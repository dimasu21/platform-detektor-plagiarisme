import logging
import docx
from pypdf import PdfReader
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
import os
import re
import numpy as np
import cv2

logger = logging.getLogger(__name__)

# Configure Tesseract path from environment variable
# Windows: set TESSERACT_CMD=D:\path\to\tesseract.exe
# Linux:   typically /usr/bin/tesseract (default)
tesseract_cmd = os.environ.get('TESSERACT_CMD', '')
if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

logger.info("Tesseract OCR engine initialized as primary text extraction method.")

# Configure Poppler path from environment variable
# Windows: set POPPLER_PATH=D:\path\to\poppler\Library\bin
# Linux:   leave empty (uses system PATH)
POPPLER_PATH = os.environ.get('POPPLER_PATH', '') or None

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'png', 'jpg', 'jpeg'}


# ==============================================================================
# ADVANCED IMAGE PREPROCESSING PIPELINE (Photo -> Clean Document -> OCR)
# ==============================================================================

def _pil_to_cv2(pil_image):
    """Convert PIL Image to OpenCV format (numpy array)."""
    if pil_image.mode == 'RGBA':
        pil_image = pil_image.convert('RGB')
    img_array = np.array(pil_image)
    if len(img_array.shape) == 3:
        # Convert RGB to BGR for OpenCV
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    return img_array


def _cv2_to_pil(cv2_image):
    """Convert OpenCV format (numpy array) back to PIL Image."""
    if len(cv2_image.shape) == 2:
        # Grayscale
        return Image.fromarray(cv2_image)
    else:
        # BGR to RGB
        rgb = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)


def _upscale_image(gray, target_width=2400):
    """
    Upscale image to simulate high DPI (300+).
    Handwriting needs higher resolution for Tesseract to work well.
    """
    h, w = gray.shape[:2]
    if w < target_width:
        scale = target_width / w
        new_w = int(w * scale)
        new_h = int(h * scale)
        gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        logger.debug(f"  DEBUG [Upscale]: {w}x{h} -> {new_w}x{new_h} (scale {scale:.1f}x)")
    return gray


def _denoise_image(gray):
    """
    Remove camera noise and paper texture.
    fastNlMeansDenoising works well for document photos.
    """
    denoised = cv2.fastNlMeansDenoising(gray, h=12, templateWindowSize=7, searchWindowSize=21)
    logger.debug("  DEBUG [Denoise]: Applied Non-Local Means denoising")
    return denoised


def _remove_notebook_lines(binary):
    """
    Remove horizontal lines (notebook paper lines) that confuse OCR.
    Uses morphological operations to detect and remove horizontal lines.
    
    IMPORTANT: Uses a wide kernel (80px) to only catch long continuous
    horizontal lines, not short strokes from handwriting. Also caps the
    removal at 15% of image pixels to prevent destroying text.
    """
    # Detect ONLY long horizontal lines (wide kernel avoids catching text strokes)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (80, 1))
    detected_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    
    # Create a mask of lines (invert because lines are black in binary)
    line_mask = cv2.bitwise_not(detected_lines)
    
    # Count how many line pixels were found
    line_pixels = np.sum(line_mask == 0)
    total_pixels = binary.shape[0] * binary.shape[1]
    line_ratio = line_pixels / total_pixels
    
    # Only remove if lines are detected but NOT too many (> 15% means 
    # we're likely removing text too, which destroys OCR accuracy)
    if 0.001 < line_ratio < 0.15:
        # Remove lines by setting them to white (background)
        result = cv2.bitwise_or(binary, cv2.bitwise_not(line_mask))
        logger.debug(f"  DEBUG [LineRemoval]: Removed notebook lines (ratio: {line_ratio:.4f})")
        return result
    elif line_ratio >= 0.15:
        logger.debug(f"  DEBUG [LineRemoval]: Ratio too high ({line_ratio:.4f}), skipping to preserve text")
        return binary
    else:
        logger.debug("  DEBUG [LineRemoval]: No significant lines detected, skipping")
        return binary


def _deskew_image(gray):
    """
    Correct rotation/skew in photographed documents.
    Uses Hough Line Transform to detect text angle and rotate.
    """
    # Edge detection
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    
    # Detect lines using Hough Transform
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100,
                            minLineLength=100, maxLineGap=10)
    
    if lines is not None and len(lines) > 0:
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line.flatten()
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            # Only consider near-horizontal lines (text lines)
            if abs(angle) < 15:
                angles.append(angle)
        
        if angles:
            median_angle = np.median(angles)
            
            # Only deskew if the angle is significant but not too extreme
            if 0.5 < abs(median_angle) < 10:
                h, w = gray.shape[:2]
                center = (w // 2, h // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                
                # Use white background for rotation
                rotated = cv2.warpAffine(gray, rotation_matrix, (w, h),
                                        flags=cv2.INTER_CUBIC,
                                        borderMode=cv2.BORDER_CONSTANT,
                                        borderValue=255)
                logger.debug(f"  DEBUG [Deskew]: Corrected rotation by {median_angle:.2f} degrees")
                return rotated
            else:
                logger.debug(f"  DEBUG [Deskew]: Angle {median_angle:.2f} degrees too small/large, skipping")
        else:
            logger.debug("  DEBUG [Deskew]: No valid text lines detected")
    else:
        logger.debug("  DEBUG [Deskew]: No lines detected for deskew")
    
    return gray


def _adaptive_threshold(gray):
    """
    Apply adaptive thresholding to handle uneven lighting.
    This is MUCH better than global thresholding for phone photos
    where lighting varies across the image.
    """
    # Adaptive Gaussian thresholding
    # blockSize=31: area size for local threshold calculation
    # C=15: constant subtracted from mean (controls sensitivity)
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=15
    )
    logger.debug("  DEBUG [Threshold]: Applied adaptive Gaussian thresholding")
    return binary


def _morphological_cleanup(binary):
    """
    Use morphological operations to:
    1. Connect broken characters (common in handwriting)
    2. Remove small noise specks
    """
    # Close small gaps in characters (connect broken strokes)
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, close_kernel, iterations=1)
    
    # Remove small noise specks (opening removes small white noise on black,
    # but we need to remove small black noise on white background)
    # Invert -> open -> invert back
    inverted = cv2.bitwise_not(cleaned)
    open_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    opened = cv2.morphologyEx(inverted, cv2.MORPH_OPEN, open_kernel, iterations=1)
    result = cv2.bitwise_not(opened)
    
    logger.debug("  DEBUG [Morphology]: Applied close + noise removal")
    return result


def _apply_clahe(gray):
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization).
    Much better than simple autocontrast for images with uneven lighting
    (e.g., photos taken under desk lamps, shadows, etc.).
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    logger.debug("  DEBUG [CLAHE]: Applied adaptive histogram equalization")
    return enhanced


def _bilateral_denoise(gray):
    """
    Bilateral filter: smooths flat areas (noise) while preserving
    sharp edges (text strokes). Better than Gaussian for OCR because
    it doesn't blur the text edges.
    """
    denoised = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
    logger.debug("  DEBUG [BilateralFilter]: Applied edge-preserving denoise")
    return denoised


def _advanced_preprocess_for_handwriting(pil_image):
    """
    ADVANCED preprocessing pipeline that converts a photo of handwritten/printed text
    into a clean, document-quality image - equivalent to what a PDF scanner produces.
    
    Pipeline steps:
    1. Upscale   - Simulate high DPI for Tesseract
    2. Deskew    - Correct camera rotation
    3. CLAHE     - Fix uneven lighting
    4. Bilateral - Denoise while keeping text edges sharp
    5. Threshold - Binarize with adaptive local thresholds
    6. Line Rem. - Remove notebook ruled lines
    7. Morphology- Connect broken strokes, remove speckle noise
    """
    logger.debug("DEBUG [Pipeline]: Starting advanced Tesseract preprocessing...")
    
    # Step 0: Convert PIL -> OpenCV grayscale
    cv2_img = _pil_to_cv2(pil_image)
    if len(cv2_img.shape) == 3:
        gray = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = cv2_img
    
    # Step 1: Upscale for better OCR resolution (target ~300 DPI equivalent)
    gray = _upscale_image(gray, target_width=2400)
    
    # Step 2: Deskew (correct rotation from camera angle)
    gray = _deskew_image(gray)
    
    # Step 3: CLAHE - fix uneven lighting (replaces simple autocontrast)
    gray = _apply_clahe(gray)
    
    # Step 4: Bilateral filter - denoise while preserving text edges
    gray = _bilateral_denoise(gray)
    
    # Step 5: Adaptive thresholding (critical for phone photos)
    binary = _adaptive_threshold(gray)
    
    # Step 6: Remove notebook/ruled paper lines
    binary = _remove_notebook_lines(binary)
    
    # Step 7: Morphological cleanup
    binary = _morphological_cleanup(binary)
    
    logger.debug("DEBUG [Pipeline]: Preprocessing complete - image is now document-quality")
    
    # Convert back to PIL
    return _cv2_to_pil(binary)


def _preprocess_image_for_ocr(image):
    """
    Basic preprocessing for PDF page images (which are already clean).
    - Convert to grayscale
    - Upscale for better DPI
    - Autocontrast & enhance contrast
    - Sharpen edges
    """
    from PIL import ImageEnhance, ImageOps, ImageFilter
    
    # Convert to grayscale
    if image.mode != 'L':
        image = image.convert('L')
    
    # Resize: upscale if the image is too small (Tesseract needs ~300 DPI)
    # Handwriting often needs a larger scale
    width, height = image.size
    target_width = 1500
    if width < target_width:
        scale_factor = target_width / width
        new_size = (int(width * scale_factor), int(height * scale_factor))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # Auto contrast to balance uneven lighting (common in phone photos)
    image = ImageOps.autocontrast(image, cutoff=1)
    
    # Enhance contrast
    enhancer_contrast = ImageEnhance.Contrast(image)
    image = enhancer_contrast.enhance(2.0)
    
    # Enhance sharpness to make text edges crisper
    enhancer_sharpness = ImageEnhance.Sharpness(image)
    image = enhancer_sharpness.enhance(2.0)
    
    return image


# ==============================================================================
# POST-OCR TEXT CLEANUP
# ==============================================================================

def _clean_ocr_text(raw_text):
    """
    Clean up raw OCR output to produce readable, structured text.
    Removes garbage characters, fixes spacing, and normalizes the text
    to match the quality of text extracted from a proper PDF.
    """
    if not raw_text:
        return ""
    
    text = raw_text
    
    # 1. Remove common OCR garbage characters
    # Remove isolated special characters that aren't real punctuation
    text = re.sub(r'[|\\~`^{}[\]<>]', '', text)
    
    # 2. Fix common OCR substitution errors
    # Replace sequences of repeated punctuation (OCR noise)
    text = re.sub(r'[.]{3,}', '...', text)
    text = re.sub(r'[-]{3,}', ' ', text)
    text = re.sub(r'[_]{2,}', ' ', text)
    
    # 3. Remove lines that are mostly non-alphabetic (likely noise/headers)
    cleaned_lines = []
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        
        # Count alphabetic characters
        alpha_count = sum(1 for c in stripped if c.isalpha())
        total_count = len(stripped)
        
        # Keep lines that are at least 15% alphabetic and have 2+ alpha chars
        if total_count > 0 and alpha_count >= 2 and (alpha_count / total_count) >= 0.15:
            cleaned_lines.append(stripped)
    
    text = ' '.join(cleaned_lines)
    
    # 4. Fix spacing issues
    # Remove spaces before punctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    # Add space after punctuation if missing
    text = re.sub(r'([.,;:!?])([A-Za-z])', r'\1 \2', text)
    
    # 5. Join hyphenated words split across lines
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
    
    # 6. Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 7. Remove single-character "words" that are OCR noise
    # RELAXED: We shouldn't aggressively drop them because it destroys words in noisy OCR output.
    words = text.split()
    filtered_words = []
    for word in words:
        # Keep the word unless it's a completely invalid standalone symbol
        if len(word) > 1 or word.isalpha() or word.isdigit():
            filtered_words.append(word)
    text = ' '.join(filtered_words)
    
    logger.debug(f"  DEBUG [TextCleanup]: Cleaned text length: {len(text)} chars")
    return text


def _multi_pass_ocr(processed_image, lang='ind+eng'):
    """
    Run OCR with multiple configurations and pick the best result.
    Different PSM modes work better for different layouts.
    
    Returns the best OCR text result.
    """
    configs = [
        # PSM 6: Assume a single uniform block of text (best for clean documents)
        ('--oem 1 --psm 6', 'PSM6-LSTM'),
        # PSM 4: Assume a single column of text of variable sizes
        ('--oem 1 --psm 4', 'PSM4-LSTM'),
        # PSM 3: Fully automatic page segmentation (Tesseract default)
        ('--oem 1 --psm 3', 'PSM3-LSTM'),
    ]
    
    best_text = ""
    best_score = 0
    best_config_name = ""
    
    for config, name in configs:
        try:
            text = pytesseract.image_to_string(processed_image, lang=lang, config=config)
            text = str(text).strip()
            
            # Score: prefer longer text with more alphabetic characters
            alpha_count = sum(1 for c in text if c.isalpha())
            word_count = len(text.split())
            # Score formula: alphabetic chars + bonus for word count
            score = alpha_count + (word_count * 2)
            
            logger.debug(f"  DEBUG [MultiOCR] {name}: {len(text)} chars, {word_count} words, score={score}")
            
            if score > best_score:
                best_score = score
                best_text = text
                best_config_name = name
        except Exception as e:
            logger.error(f"  ERROR [MultiOCR] {name} failed: {e}", exc_info=True)
    
    logger.debug(f"  DEBUG [MultiOCR]: Best config = {best_config_name} (score={best_score})")
    return best_text


# ==============================================================================
# FILE EXTRACTION FUNCTIONS
# ==============================================================================

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_file(file_storage):
    """
    Extracts text from a FileStorage object (Flask upload).
    Determines type by filename extension.
    """
    filename = file_storage.filename
    ext = filename.rsplit('.', 1)[1].lower()
    
    try:
        if ext == 'docx':
            return _extract_from_docx(file_storage)
        elif ext == 'pdf':
            return _extract_from_pdf(file_storage)
        elif ext in ['png', 'jpg', 'jpeg']:
            return _extract_from_image(file_storage)
        elif ext == 'txt':
            return file_storage.read().decode('utf-8')
        else:
            return ""
    except Exception as e:
        logger.debug(f"Error extracting text from {filename}: {e}")
        return ""


def extract_text_and_images_from_file(file_storage):
    """
    Extracts both text and images from a FileStorage object.
    Used for visual plagiarism highlighting.
    
    For image files (PNG/JPEG), uses the advanced handwriting pipeline:
    1. Advanced preprocessing (photo -> clean document quality)
    2. Multi-pass OCR with best configuration
    3. Post-OCR text cleanup
    4. Original image kept for visual highlighting
    
    Returns:
        dict: {
            'text': str,
            'images': list of PIL Images (for PDF/images),
            'filename': str
        }
    """
    filename = file_storage.filename
    ext = filename.rsplit('.', 1)[1].lower()
    
    result = {
        'text': '',
        'images': [],
        'filename': filename,
        'error': None
    }
    
    try:
        if ext == 'pdf':
            # Extract text and images from PDF
            pdf_result = _extract_from_pdf_with_images(file_storage)
            result['text'] = str(pdf_result['text'])
            result['images'] = list(pdf_result['images'])
        elif ext in ['png', 'jpg', 'jpeg']:
            # ============================================
            # TESSERACT OCR PIPELINE
            # Photo -> Preprocessing -> Multi-Pass OCR -> Clean Text
            # ============================================
            logger.debug(f"\n{'='*60}")
            logger.debug(f"TESSERACT OCR PIPELINE: Processing {filename}")
            logger.debug(f"{'='*60}")
            
            # Load original image
            image = Image.open(file_storage)
            original_image = image.copy()  # Keep original for highlighting
            
            # Step 1: Advanced preprocessing (convert photo to clean document)
            logger.debug("\n[STEP 1] Advanced Preprocessing (Photo -> Document Quality)...")
            clean_document = _advanced_preprocess_for_handwriting(image)
            
            # Step 2: Multi-pass OCR on the clean document
            logger.debug("\n[STEP 2] Multi-Pass OCR on clean document...")
            raw_text = _multi_pass_ocr(clean_document, lang='ind+eng')
            
            # Step 3: Post-OCR text cleanup
            logger.debug("\n[STEP 3] Post-OCR Text Cleanup...")
            clean_text = _clean_ocr_text(raw_text)
            
            if not clean_text and raw_text:
                result['error'] = f"Filter dropped all text. Raw: {raw_text[:50]}..."
            elif not clean_text and not raw_text:
                result['error'] = "Tesseract OCR found 0 words."
                
            logger.debug(f"\n[RESULT] Final clean text ({len(clean_text)} chars):")
            logger.debug(f"  Preview: {clean_text[:200]}...")
            logger.debug(f"{'='*60}\n")
            
            result['text'] = clean_text
            result['images'] = [original_image]  # Keep original image for highlighting
            
        elif ext == 'docx':
            # DOCX doesn't have images to highlight
            result['text'] = _extract_from_docx(file_storage)
            result['images'] = []
        elif ext == 'txt':
            result['text'] = file_storage.read().decode('utf-8')
            result['images'] = []
        else:
            result['text'] = ""
            result['images'] = []
            
    except Exception as e:
        logger.error(f"Error extracting from {filename}: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        result['error'] = f"{type(e).__name__}: {str(e)}"
    
    return result


def _extract_from_docx(file_storage):
    doc = docx.Document(file_storage)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)


def _extract_from_pdf(file_storage):
    # 1. Try standard text extraction first (faster)
    try:
        reader = PdfReader(file_storage)
        full_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
        
        extracted_text = '\n'.join(full_text).strip()
        
        # CLEANUP: Fix common PDF line break issues
        # 1. Join hyphenated words split across lines (e.g. "per- nyataan" -> "pernyataan")
        extracted_text = extracted_text.replace('-\n', '')
        # 2. Convert newlines to spaces to treat paragraphs as continuous blocks
        extracted_text = extracted_text.replace('\n', ' ')
        # 3. Collapse multiple spaces
        extracted_text = re.sub(r'\s+', ' ', extracted_text)
        
        # If text is found and substantial, return it
        if len(extracted_text) > 50: 
            return extracted_text
            
        logger.debug("DEBUG: Standard PDF extraction yielded little/no text. Trying OCR...")
    except Exception as e:
        logger.debug(f"DEBUG: Standard PDF extraction failed: {e}")

    # 2. Fallback to OCR (pdf2image -> pytesseract)
    try:
        # Reset file pointer to beginning
        file_storage.seek(0)
        file_bytes = file_storage.read()
        
        # Convert PDF to images
        images = convert_from_bytes(file_bytes, poppler_path=POPPLER_PATH)
        
        ocr_text = []
        for i, image in enumerate(images):
            logger.debug(f"DEBUG: OCR Processing page {i+1}...")
            # Preprocess image for better OCR
            processed_image = _preprocess_image_for_ocr(image)
            # Use PSM 4 (Assume a single column of text of variable sizes) which works better for mixed handwritten layouts
            custom_config = r'--oem 3 --psm 4'
            text = pytesseract.image_to_string(processed_image, lang='ind+eng', config=custom_config)
            ocr_text.append(str(text))
            
        return '\n'.join(ocr_text)
    except Exception as e:
        logger.debug(f"DEBUG: PDF OCR failed: {e}")
        return ""


def _extract_from_pdf_with_images(file_storage):
    """
    Extract both text and images from PDF.
    Returns dict with 'text' and 'images' keys.
    """
    # Always convert PDF to images for visual highlighting
    try:
        file_storage.seek(0)
        file_bytes = file_storage.read()
        
        # Convert PDF to images (higher DPI for better quality)
        images = convert_from_bytes(file_bytes, poppler_path=POPPLER_PATH, dpi=200)
        logger.debug(f"DEBUG: Converted PDF to {len(images)} page images")
        
        ocr_text = []
        for i, image in enumerate(images):
            logger.debug(f"DEBUG: OCR Processing page {i+1}...")
            # Preprocess image for better OCR
            processed_image = _preprocess_image_for_ocr(image)
            # Use PSM 4
            custom_config = r'--oem 3 --psm 4'
            text = pytesseract.image_to_string(processed_image, lang='ind+eng', config=custom_config)
            ocr_text.append(str(text))
        
        return {
            'text': '\n'.join(ocr_text),
            'images': images  # Return original images, not preprocessed ones
        }
    except Exception as e:
        logger.debug(f"DEBUG: PDF extraction with images failed: {e}")
        return {
            'text': '',
            'images': []
        }


def _extract_from_image(file_storage):
    """
    Extract text from a standalone image file using the advanced pipeline.
    """
    image = Image.open(file_storage)
    
    # Use advanced preprocessing for handwriting
    logger.debug("DEBUG: Using advanced handwriting pipeline for standalone image...")
    clean_document = _advanced_preprocess_for_handwriting(image)
    
    # Multi-pass OCR
    raw_text = _multi_pass_ocr(clean_document, lang='ind+eng')
    
    # Clean up
    clean_text = _clean_ocr_text(raw_text)
    
    return clean_text


# ==============================================================================
# IMAGE-BASED STRUCTURAL SIMILARITY (SSIM) FOR HANDWRITING COMPARISON
# ==============================================================================

def compute_image_similarity(pil_image1, pil_image2):
    """
    Compare two images of exam answers using multiple visual analysis techniques.
    
    Strategy: Instead of comparing raw photos (different lighting/angles),
    we normalize both images through binarization first, then compare the
    text structure and layout patterns.
    
    Techniques used:
    1. SSIM on preprocessed (binarized) images - compares text structure
    2. Zone-based text density - divides image into grid, compares text amount per zone
    3. Histogram comparison on binarized images - overall ink distribution
    4. ORB feature matching - visual keypoint similarity
    
    Returns:
        float: Similarity score 0-100 (percentage)
    """
    logger.debug("DEBUG [ImageSim]: Computing image structural similarity...")
    
    # Convert PIL images to OpenCV grayscale
    img1 = _pil_to_cv2(pil_image1)
    img2 = _pil_to_cv2(pil_image2)
    
    if len(img1.shape) == 3:
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    if len(img2.shape) == 3:
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # Resize both to same dimensions
    target_size = (800, 1000)
    img1_resized = cv2.resize(img1, target_size, interpolation=cv2.INTER_AREA)
    img2_resized = cv2.resize(img2, target_size, interpolation=cv2.INTER_AREA)
    
    # === STEP 1: Binarize both images (normalize lighting differences) ===
    bin1 = cv2.adaptiveThreshold(img1_resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 31, 15)
    bin2 = cv2.adaptiveThreshold(img2_resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 31, 15)
    
    # === METHOD 1: SSIM on binarized images ===
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    
    img1_f = bin1.astype(np.float64)
    img2_f = bin2.astype(np.float64)
    
    mu1 = cv2.GaussianBlur(img1_f, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(img2_f, (11, 11), 1.5)
    
    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2
    
    sigma1_sq = cv2.GaussianBlur(img1_f ** 2, (11, 11), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(img2_f ** 2, (11, 11), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(img1_f * img2_f, (11, 11), 1.5) - mu1_mu2
    
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
               ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    
    ssim_score = float(np.mean(ssim_map)) * 100
    ssim_score = max(0, ssim_score)
    logger.debug(f"  DEBUG [SSIM-Binary]: Score = {ssim_score:.2f}%")
    
    # === METHOD 2: Zone-based text density comparison ===
    # Divide image into grid zones and compare text density per zone
    # This detects if two answers cover the same topics in the same order
    rows, cols = 10, 5  # 10 rows x 5 cols = 50 zones
    zone_h = target_size[1] // rows
    zone_w = target_size[0] // cols
    
    density1 = []
    density2 = []
    
    for r in range(rows):
        for c in range(cols):
            y1, y2 = r * zone_h, (r + 1) * zone_h
            x1, x2 = c * zone_w, (c + 1) * zone_w
            
            zone1 = bin1[y1:y2, x1:x2]
            zone2 = bin2[y1:y2, x1:x2]
            
            # Text density = ratio of dark pixels (text = 0 in binary)
            d1 = np.sum(zone1 == 0) / zone1.size
            d2 = np.sum(zone2 == 0) / zone2.size
            
            density1.append(d1)
            density2.append(d2)
    
    density1 = np.array(density1)
    density2 = np.array(density2)
    
    # Cosine similarity between density vectors
    dot_product = np.dot(density1, density2)
    norm1 = np.linalg.norm(density1)
    norm2 = np.linalg.norm(density2)
    
    if norm1 > 0 and norm2 > 0:
        zone_score = (dot_product / (norm1 * norm2)) * 100
    else:
        zone_score = 0.0
    zone_score = max(0, zone_score)
    logger.debug(f"  DEBUG [ZoneDensity]: Score = {zone_score:.2f}%")
    
    # === METHOD 3: Row-level horizontal projection profile ===
    # Creates a 1D "profile" of text density per row (how much text on each line)
    # Two answers that cover the same content will have similar line-by-line patterns
    # (e.g., same paragraph breaks, same numbering, same amount of text per answer)
    num_rows_profile = 100  # Sample 100 rows across the image height
    row_step = target_size[1] // num_rows_profile
    
    profile1 = []
    profile2 = []
    
    for r in range(num_rows_profile):
        y = r * row_step
        y_end = min(y + row_step, target_size[1])
        
        row1 = bin1[y:y_end, :]
        row2 = bin2[y:y_end, :]
        
        # Calculate text density for this row strip
        p1 = np.sum(row1 == 0) / row1.size if row1.size > 0 else 0
        p2 = np.sum(row2 == 0) / row2.size if row2.size > 0 else 0
        
        profile1.append(p1)
        profile2.append(p2)
    
    profile1 = np.array(profile1)
    profile2 = np.array(profile2)
    
    # Pearson correlation between profiles
    if np.std(profile1) > 0 and np.std(profile2) > 0:
        correlation = np.corrcoef(profile1, profile2)[0, 1]
        profile_score = max(0, correlation * 100)
    else:
        profile_score = 0.0
    logger.debug(f"  DEBUG [RowProfile]: Score = {profile_score:.2f}%")
    
    # === METHOD 4: Histogram comparison on binarized images ===
    hist1 = cv2.calcHist([bin1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([bin2], [0], None, [256], [0, 256])
    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)
    
    hist_score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL) * 100
    hist_score = max(0, hist_score)
    logger.debug(f"  DEBUG [Histogram-Binary]: Score = {hist_score:.2f}%")
    
    # === METHOD 5: ORB Feature Matching on binarized images ===
    orb = cv2.ORB_create(nfeatures=1000)
    kp1, des1 = orb.detectAndCompute(bin1, None)
    kp2, des2 = orb.detectAndCompute(bin2, None)
    
    orb_score = 0.0
    if des1 is not None and des2 is not None and len(des1) > 0 and len(des2) > 0:
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        
        if matches:
            good_matches = [m for m in matches if m.distance < 60]
            total_kp = max(len(kp1), len(kp2))
            orb_score = (len(good_matches) / total_kp) * 100
            orb_score = min(100, orb_score)
    logger.debug(f"  DEBUG [ORB-Binary]: Score = {orb_score:.2f}%")
    
    # === COMBINE SCORES ===
    # Adjusted weights to create more diverse and realistic scores:
    # - profile_score (35%): Highly sensitive to line spacing and paragraph breaks
    # - zone_score (25%): Detects overall layout but can be too generic
    # - ssim_score (20%): Pixel-level structural overlap
    # - hist_score (10%): Binary text/background ratio (usually very similar, so weight is low)
    # - orb_score (10%): Local feature matching
    final_score = (profile_score * 0.35) + (zone_score * 0.25) + (ssim_score * 0.20) + (hist_score * 0.10) + (orb_score * 0.10)
    final_score = round(min(100, max(0, final_score)), 2)
    
    logger.debug(f"  DEBUG [ImageSim]: Final combined score = {final_score:.2f}%")
    return final_score

