import pytesseract
from PIL import Image, ImageDraw, ImageFont
import os

def extract_text_with_boxes(image, lang='ind+eng'):
    """
    Extract text and bounding box coordinates from image using Tesseract.
    
    Args:
        image: PIL Image object
        lang: Language for OCR (default: 'ind+eng')
    
    Returns:
        dict: OCR data with text, coordinates, and confidence levels
    """
    # PSM 6: Assume a single uniform block of text (works better for handwriting)
    # OEM 1: LSTM engine (most accurate)
    custom_config = r'--oem 1 --psm 6'
    
    # Get detailed data with bounding boxes
    data = pytesseract.image_to_data(
        image, 
        lang=lang, 
        config=custom_config,
        output_type=pytesseract.Output.DICT
    )
    
    return data

def build_word_to_box_mapping(ocr_data):
    """
    Build a mapping from words to their bounding boxes.
    
    Uses a very low confidence threshold to capture as many words as possible
    from handwritten text (where Tesseract confidence is naturally low).
    
    Args:
        ocr_data: Dictionary from pytesseract.image_to_data
    
    Returns:
        list: List of tuples (word, (x, y, w, h))
    """
    word_boxes = []
    
    n_boxes = len(ocr_data['text'])
    for i in range(n_boxes):
        # Use very low confidence threshold - handwriting OCR has low confidence
        # but the bounding boxes are still useful for highlighting
        conf = int(ocr_data['conf'][i])
        if conf > 0:  # Accept any positive confidence
            text = ocr_data['text'][i].strip()
            if text and len(text) >= 2:  # At least 2 characters
                x = ocr_data['left'][i]
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]
                
                word_boxes.append((text, (x, y, w, h)))
    
    return word_boxes

def normalize_word(word):
    """
    Normalize word by removing punctuation and converting to lowercase.
    """
    import re
    # Remove all non-alphanumeric characters except spaces
    normalized = re.sub(r'[^a-z0-9\s]', '', word.lower())
    return normalized.strip()

def find_matched_boxes(word_boxes, matched_phrases):
    """
    Find bounding boxes for matched phrases with aggressive fuzzy matching.
    
    Uses multiple strategies:
    1. Multi-word phrase matching with fuzzy comparison
    2. Individual word matching for single-word matches
    3. Loose window scanning to handle OCR word insertion/deletion
    """
    from difflib import SequenceMatcher
    matched_boxes = []
    used_indices = set()  # Track which OCR words we've already highlighted
    
    # Normalize word_boxes for better matching
    normalized_word_boxes = []
    for word, box in word_boxes:
        normalized_word_boxes.append((normalize_word(word), box, word))
    
    # Separate single-word and multi-word phrases
    single_words = set()
    multi_phrases = []
    
    for phrase in matched_phrases:
        phrase_words = [normalize_word(w) for w in phrase.split() if normalize_word(w)]
        if not phrase_words:
            continue
        if len(phrase_words) == 1:
            single_words.add(phrase_words[0])
        else:
            multi_phrases.append(phrase_words)
    
    # === STRATEGY 1: Multi-word phrase matching ===
    for phrase_words in multi_phrases:
        phrase_len = len(phrase_words)
        
        i = 0
        while i < len(normalized_word_boxes):
            ocr_w = normalized_word_boxes[i][0]
            p_w = phrase_words[0]
            
            is_match = False
            if len(ocr_w) >= 2 and len(p_w) >= 2:
                ratio = SequenceMatcher(None, ocr_w, p_w).ratio()
                if ratio > 0.55 or p_w in ocr_w or ocr_w in p_w:
                    is_match = True
            elif ocr_w == p_w:
                is_match = True
                
            if is_match:
                matched_ocr_indices = [i]
                phrase_idx = 1
                search_idx = i + 1
                window_limit = i + phrase_len + 6  # wider window for handwriting
                
                while phrase_idx < phrase_len and search_idx < min(len(normalized_word_boxes), window_limit):
                    curr_ocr_w = normalized_word_boxes[search_idx][0]
                    curr_p_w = phrase_words[phrase_idx]
                    
                    curr_match = False
                    if len(curr_ocr_w) >= 2 and len(curr_p_w) >= 2:
                        r = SequenceMatcher(None, curr_ocr_w, curr_p_w).ratio()
                        if r > 0.55 or curr_p_w in curr_ocr_w or curr_ocr_w in curr_p_w:
                            curr_match = True
                    elif curr_ocr_w == curr_p_w:
                        curr_match = True
                        
                    if curr_match:
                        matched_ocr_indices.append(search_idx)
                        phrase_idx += 1
                    
                    search_idx += 1
                
                # Accept if we found at least 50% of phrase words (more lenient for OCR)
                if len(matched_ocr_indices) >= max(1, int(phrase_len * 0.50)):
                    boxes = [normalized_word_boxes[idx][1] for idx in matched_ocr_indices]
                    if boxes:
                        min_x = min(box[0] for box in boxes)
                        min_y = min(box[1] for box in boxes)
                        max_x = max(box[0] + box[2] for box in boxes)
                        max_y = max(box[1] + box[3] for box in boxes)
                        matched_boxes.append((min_x, min_y, max_x, max_y))
                        used_indices.update(matched_ocr_indices)
                    
                    i = search_idx - 1
            i += 1
    
    # === STRATEGY 2: Individual word matching ===
    # For single-word matches, highlight each occurrence in the image
    for i, (ocr_norm, box, ocr_orig) in enumerate(normalized_word_boxes):
        if i in used_indices:
            continue  # Skip words already highlighted by phrase matching
        if len(ocr_norm) < 3:
            continue  # Skip very short OCR words (likely noise)
            
        for match_word in single_words:
            if len(match_word) < 3:
                continue
            
            # Fuzzy match the OCR word against the match word
            ratio = SequenceMatcher(None, ocr_norm, match_word).ratio()
            if ratio > 0.60 or match_word in ocr_norm or ocr_norm in match_word:
                x, y, w, h = box
                matched_boxes.append((x, y, x + w, y + h))
                used_indices.add(i)
                break  # One match per OCR word is enough
            
    return matched_boxes

def draw_highlights(image, boxes, color=(255, 70, 70, 90)):
    """
    Draw semi-transparent highlighter blocks on image to highlight matched text (Turnitin style).
    
    Args:
        image: PIL Image object
        boxes: List of bounding boxes (x1, y1, x2, y2)
        color: RGBA Color of highlight fill (default: semi-transparent red)
    
    Returns:
        PIL Image: Image with highlights drawn
    """
    # Convert base image to RGBA to support transparency
    base = image.convert('RGBA')
    # Create a blank transparent overlay image
    overlay = Image.new('RGBA', base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    for box in boxes:
        x1, y1, x2, y2 = box
        # Expand the box slightly to cover the word fully like a real marker
        pad = 3
        # Draw filled rectangle with transparency
        draw.rectangle([x1-pad, y1-pad, x2+pad, y2+pad], fill=color)
    
    # Combine the base image and the highlighter overlay
    highlighted = Image.alpha_composite(base, overlay)
    
    # Convert back to RGB
    return highlighted.convert('RGB')

def save_highlighted_image(image, output_path):
    """
    Save highlighted image to file.
    
    Args:
        image: PIL Image object
        output_path: Path where to save the image
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save image
    image.save(output_path, 'PNG')
    print(f"DEBUG: Saved highlighted image to {output_path}")

def highlight_plagiarism_in_images(images, matched_phrases):
    """
    Process multiple images and highlight plagiarized text.
    
    For image files, applies advanced preprocessing before OCR to get
    accurate bounding boxes, then draws highlights on the ORIGINAL image.
    
    Args:
        images: List of PIL Image objects (PDF pages or photos)
        matched_phrases: List of matched n-gram strings
    
    Returns:
        list: List of highlighted PIL Images
    """
    highlighted_images = []
    
    for page_num, image in enumerate(images, 1):
        print(f"DEBUG: Processing highlights for page {page_num}...")
        
        # Preprocess image for better OCR box detection
        preprocessed = image  # fallback to original
        try:
            from file_parser import _advanced_preprocess_for_handwriting
            preprocessed = _advanced_preprocess_for_handwriting(image)
            # Get OCR data from preprocessed image for accurate boxes
            ocr_data = extract_text_with_boxes(preprocessed)
        except Exception as e:
            print(f"DEBUG: Advanced preprocessing failed for highlighting, using original: {e}")
            preprocessed = image
            ocr_data = extract_text_with_boxes(image)
        
        # Build word-to-box mapping
        word_boxes = build_word_to_box_mapping(ocr_data)
        
        # Find boxes for matched phrases
        matched_boxes = find_matched_boxes(word_boxes, matched_phrases)
        
        # Scale boxes back to original image dimensions if preprocessed image was resized
        if image.size != preprocessed.size:
            scale_x = image.size[0] / preprocessed.size[0]
            scale_y = image.size[1] / preprocessed.size[1]
            scaled_boxes = []
            for (x1, y1, x2, y2) in matched_boxes:
                scaled_boxes.append((
                    int(x1 * scale_x), int(y1 * scale_y),
                    int(x2 * scale_x), int(y2 * scale_y)
                ))
            matched_boxes = scaled_boxes
            
        # --- SAFEGUARD: Abaikan kotak merah di area Kop Surat (18% bagian atas gambar) ---
        img_width, img_height = image.size
        header_threshold = img_height * 0.18  # Threshold 18% dari atas
        
        filtered_boxes = []
        for box in matched_boxes:
            x1, y1, x2, y2 = box
            # Hanya gambar kotak jika posisinya berada di bawah batas header
            if y1 > header_threshold:
                filtered_boxes.append(box)
        
        print(f"DEBUG: Found {len(filtered_boxes)} highlight regions on page {page_num} (after header filtering)")
        
        # Draw highlights on the ORIGINAL image (not preprocessed)
        highlighted_img = draw_highlights(image, filtered_boxes)
        highlighted_images.append(highlighted_img)
    
    return highlighted_images

