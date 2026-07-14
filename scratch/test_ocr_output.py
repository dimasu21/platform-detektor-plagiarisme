"""
Debug script: See what Tesseract actually reads from each handwriting image.
Compare OCR output side-by-side to understand the low similarity score.
"""
import sys
sys.path.insert(0, r'd:\projectpribadi\platform-plagiarisme')

from PIL import Image
from file_parser import _advanced_preprocess_for_handwriting, _multi_pass_ocr, _clean_ocr_text
from preprocessing import preprocess_text
from rabin_karp import detect_plagiarism

# Pick two images that should be similar
img1_path = r"d:\projectpribadi\platform-plagiarisme\Data Citra\Dimas - Computer Vision.jpeg"
img2_path = r"d:\projectpribadi\platform-plagiarisme\Data Citra\Dea - Computer Vision.jpg"

def process_image(path):
    print(f"\n{'='*70}")
    print(f"Processing: {path}")
    print(f"{'='*70}")
    img = Image.open(path)
    clean_doc = _advanced_preprocess_for_handwriting(img)
    raw_text = _multi_pass_ocr(clean_doc, lang='ind+eng')
    clean_text = _clean_ocr_text(raw_text)
    return raw_text, clean_text

# Process both images
raw1, clean1 = process_image(img1_path)
raw2, clean2 = process_image(img2_path)

print(f"\n{'='*70}")
print("RAW OCR OUTPUT COMPARISON")
print(f"{'='*70}")

print(f"\n--- Image 1 RAW ({len(raw1)} chars) ---")
print(raw1[:1000])
print(f"\n--- Image 2 RAW ({len(raw2)} chars) ---")
print(raw2[:1000])

print(f"\n--- Image 1 CLEANED ({len(clean1)} chars) ---")
print(clean1[:500])
print(f"\n--- Image 2 CLEANED ({len(clean2)} chars) ---")
print(clean2[:500])

# Now preprocess for Rabin-Karp
preprocessed1 = preprocess_text(clean1)
preprocessed2 = preprocess_text(clean2)

print(f"\n--- Image 1 PREPROCESSED ({len(preprocessed1)} chars) ---")
print(preprocessed1[:500])
print(f"\n--- Image 2 PREPROCESSED ({len(preprocessed2)} chars) ---")
print(preprocessed2[:500])

# Run Rabin-Karp
result = detect_plagiarism(preprocessed1, preprocessed2, k=5)
print(f"\n{'='*70}")
print(f"PLAGIARISM RESULT: {result['similarity_score']}%")
print(f"Matches found: {len(result['matches'])}")
if result['matches']:
    print("Sample matches:")
    for m in result['matches'][:10]:
        print(f"  - '{m}'")
print(f"{'='*70}")
