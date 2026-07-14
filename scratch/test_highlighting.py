"""Test highlighting with the new aggressive matching logic."""
import sys
sys.path.insert(0, r'd:\projectpribadi\platform-plagiarisme')

from PIL import Image
from file_parser import _advanced_preprocess_for_handwriting, _multi_pass_ocr, _clean_ocr_text
from preprocessing import preprocess_text
from rabin_karp import detect_plagiarism
from highlight_visualizer import highlight_plagiarism_in_images

img1_path = r"d:\projectpribadi\platform-plagiarisme\Data Citra\Dimas - Computer Vision.jpeg"
img2_path = r"d:\projectpribadi\platform-plagiarisme\Data Citra\Dea - Computer Vision.jpg"

def ocr_image(path):
    img = Image.open(path)
    clean_doc = _advanced_preprocess_for_handwriting(img)
    raw_text = _multi_pass_ocr(clean_doc, lang='ind+eng')
    return _clean_ocr_text(raw_text)

print("Processing images and getting text...")
text1 = ocr_image(img1_path)
text2 = ocr_image(img2_path)

p1 = preprocess_text(text1)
p2 = preprocess_text(text2)

result = detect_plagiarism(p1, p2, k=3)

print(f"\nTotal matches found: {len(result['matches'])}")
print("Matches:", result['matches'])

print("\nGenerating highlights for Image 1...")
img1 = Image.open(img1_path)
highlighted_img1 = highlight_plagiarism_in_images([img1], result['matches'])[0]
highlighted_img1.save(r"d:\projectpribadi\platform-plagiarisme\scratch\highlight_test_1.png")

print("\nGenerating highlights for Image 2...")
img2 = Image.open(img2_path)
highlighted_img2 = highlight_plagiarism_in_images([img2], result['matches'])[0]
highlighted_img2.save(r"d:\projectpribadi\platform-plagiarisme\scratch\highlight_test_2.png")

print("\nHighlights saved to scratch directory.")
