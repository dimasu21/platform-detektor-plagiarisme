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
    custom_config = r'--oem 3 --psm 1'
    
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
    
    Args:
        ocr_data: Dictionary from pytesseract.image_to_data
    
    Returns:
        list: List of tuples (word, (x, y, w, h))
    """
    word_boxes = []
    
    n_boxes = len(ocr_data['text'])
    for i in range(n_boxes):
        # Filter out empty text and low confidence
        if int(ocr_data['conf'][i]) > 0:  # Only include recognized text
            text = ocr_data['text'][i].strip()
            if text:  # Not empty
                x = ocr_data['left'][i]
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]
                
                # Keep original case for debugging
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
    Find bounding boxes for matched phrases with fuzzy matching.
    
    Args:
        word_boxes: List of (word, box) tuples
        matched_phrases: List of matched n-gram strings
    
    Returns:
        list: List of bounding boxes (x, y, x2, y2) for matched text
    """
    matched_boxes = []
    
    # Normalize word_boxes for better matching
    normalized_word_boxes = []
    for word, box in word_boxes:
        normalized_word_boxes.append((normalize_word(word), box, word))  # keep original word for debug
    
    for phrase in matched_phrases:
        # Normalize and split phrase into words
        phrase_words = [normalize_word(w) for w in phrase.split() if normalize_word(w)]
        if not phrase_words:
            continue
        
        # Print for debugging
        print(f"DEBUG: Looking for phrase: {phrase_words}")
        
        # Find consecutive words in word_boxes
        for i in range(len(normalized_word_boxes) - len(phrase_words) + 1):
            # Check if words match (allowing for minor differences)
            words_match = True
            for j in range(len(phrase_words)):
                ocr_word = normalized_word_boxes[i + j][0]
                phrase_word = phrase_words[j]
                
                # Exact match or substring match (to handle OCR errors)
                if not (ocr_word == phrase_word or 
                        phrase_word in ocr_word or 
                        ocr_word in phrase_word):
                    words_match = False
                    break
            
            if words_match:
                # Get bounding boxes for all words in phrase
                boxes = [normalized_word_boxes[i + j][1] for j in range(len(phrase_words))]
                
                # Debug: print matched words
                matched_words = [normalized_word_boxes[i + j][2] for j in range(len(phrase_words))]
                print(f"DEBUG: Matched words: {matched_words}")
                
                # Merge boxes into one bounding box
                if boxes:
                    min_x = min(box[0] for box in boxes)
                    min_y = min(box[1] for box in boxes)
                    max_x = max(box[0] + box[2] for box in boxes)
                    max_y = max(box[1] + box[3] for box in boxes)
                    
                    matched_boxes.append((min_x, min_y, max_x, max_y))
    
    return matched_boxes

def draw_highlights(image, boxes, color='red', width=3):
    """
    Draw bounding boxes on image to highlight matched text.
    
    Args:
        image: PIL Image object
        boxes: List of bounding boxes (x1, y1, x2, y2)
        color: Color of highlight boxes (default: 'red')
        width: Width of box outline (default: 3)
    
    Returns:
        PIL Image: Image with highlights drawn
    """
    # Create a copy to avoid modifying original
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    
    for box in boxes:
        x1, y1, x2, y2 = box
        # Draw rectangle with red outline
        draw.rectangle([x1, y1, x2, y2], outline=color, width=width)
    
    return img_copy

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
    
    Args:
        images: List of PIL Image objects (PDF pages)
        matched_phrases: List of matched n-gram strings
    
    Returns:
        list: List of highlighted PIL Images
    """
    highlighted_images = []
    
    for page_num, image in enumerate(images, 1):
        print(f"DEBUG: Processing highlights for page {page_num}...")
        
        # Extract text with bounding boxes
        ocr_data = extract_text_with_boxes(image)
        
        # Build word-to-box mapping
        word_boxes = build_word_to_box_mapping(ocr_data)
        
        # Find boxes for matched phrases
        matched_boxes = find_matched_boxes(word_boxes, matched_phrases)
        
        print(f"DEBUG: Found {len(matched_boxes)} highlight regions on page {page_num}")
        
        # Draw highlights
        highlighted_img = draw_highlights(image, matched_boxes)
        highlighted_images.append(highlighted_img)
    
    return highlighted_images
