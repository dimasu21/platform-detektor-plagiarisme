    Preprocess image to improve OCR accuracy.
    - Convert to grayscale
    - Increase contrast
    - Resize if too small
    """
    from PIL import ImageEnhance
    
    # Convert to grayscale
    if image.mode != 'L':
        image = image.convert('L')
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)  # Increase contrast
    
    # Resize if image is too small (OCR works better with larger images)
    width, height = image.size
    if width < 1000:
        scale_factor = 1000 / width
        new_size = (int(width * scale_factor), int(height * scale_factor))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    return image

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
        print(f"Error extracting text from {filename}: {e}")
        return ""

def extract_text_and_images_from_file(file_storage):
    """
    Extracts both text and images from a FileStorage object.
    Used for visual plagiarism highlighting.
    
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
        'filename': filename
    }
    
    try:
        if ext == 'pdf':
            # Extract text and images from PDF
            pdf_result = _extract_from_pdf_with_images(file_storage)
            result['text'] = pdf_result['text']
            result['images'] = pdf_result['images']
        elif ext in ['png', 'jpg', 'jpeg']:
            # For image files, extract text and keep the image
            image = Image.open(file_storage)
            processed_image = _preprocess_image_for_ocr(image)
            custom_config = r'--oem 3 --psm 1'
            text = pytesseract.image_to_string(processed_image, lang='ind+eng', config=custom_config)
            result['text'] = text
            result['images'] = [image]  # Keep original image, not preprocessed
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
        print(f"Error extracting from {filename}: {e}")
    
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
        
        # If text is found and substantial, return it
        if len(extracted_text) > 50: 
            return extracted_text
            
        print("DEBUG: Standard PDF extraction yielded little/no text. Trying OCR...")
    except Exception as e:
        print(f"DEBUG: Standard PDF extraction failed: {e}")

    # 2. Fallback to OCR (pdf2image -> pytesseract)
    try:
        # Reset file pointer to beginning
        file_storage.seek(0)
        file_bytes = file_storage.read()
        
        # Convert PDF to images
        images = convert_from_bytes(file_bytes, poppler_path=POPPLER_PATH)
        
        ocr_text = []
        for i, image in enumerate(images):
            print(f"DEBUG: OCR Processing page {i+1}...")
            # Preprocess image for better OCR
            processed_image = _preprocess_image_for_ocr(image)
            # Use PSM 1 (Automatic page segmentation with OSD)
            custom_config = r'--oem 3 --psm 1'
            text = pytesseract.image_to_string(processed_image, lang='ind+eng', config=custom_config)
            ocr_text.append(text)
            
        return '\\n'.join(ocr_text)
    except Exception as e:
        print(f"DEBUG: PDF OCR failed: {e}")
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
        print(f"DEBUG: Converted PDF to {len(images)} page images")
        
        ocr_text = []
        for i, image in enumerate(images):
            print(f"DEBUG: OCR Processing page {i+1}...")
            # Preprocess image for better OCR
            processed_image = _preprocess_image_for_ocr(image)
            # Use PSM 1 (Automatic page segmentation with OSD)
            custom_config = r'--oem 3 --psm 1'
            text = pytesseract.image_to_string(processed_image, lang='ind+eng', config=custom_config)
            ocr_text.append(text)
        
        return {
            'text': '\\n'.join(ocr_text),
            'images': images  # Return original images, not preprocessed ones
        }
    except Exception as e:
        print(f"DEBUG: PDF extraction with images failed: {e}")
        return {
            'text': '',
            'images': []
        }

def _extract_from_image(file_storage):
    image = Image.open(file_storage)
    # Preprocess image for better OCR
    processed_image = _preprocess_image_for_ocr(image)
    # Use PSM 1 (Automatic page segmentation with OSD)
    custom_config = r'--oem 3 --psm 1'
    text = pytesseract.image_to_string(processed_image, lang='ind+eng', config=custom_config)
    return text
