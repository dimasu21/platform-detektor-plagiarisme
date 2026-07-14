"""Quick test: how many match words does the improved Rabin-Karp produce?"""
import sys
sys.path.insert(0, r'd:\projectpribadi\platform-plagiarisme')

from PIL import Image
from file_parser import _advanced_preprocess_for_handwriting, _multi_pass_ocr, _clean_ocr_text
from preprocessing import preprocess_text
from rabin_karp import detect_plagiarism

img1_path = r"d:\projectpribadi\platform-plagiarisme\Data Citra\Dimas - Computer Vision.jpeg"
img2_path = r"d:\projectpribadi\platform-plagiarisme\Data Citra\Dea - Computer Vision.jpg"

def ocr_image(path):
    img = Image.open(path)
    clean_doc = _advanced_preprocess_for_handwriting(img)
    raw_text = _multi_pass_ocr(clean_doc, lang='ind+eng')
    return _clean_ocr_text(raw_text)

print("Processing images...")
text1 = ocr_image(img1_path)
text2 = ocr_image(img2_path)

p1 = preprocess_text(text1)
p2 = preprocess_text(text2)

result = detect_plagiarism(p1, p2, k=3)

print(f"\nScore: {result['similarity_score']}%")
print(f"Total matches: {len(result['matches'])}")
print(f"\nAll matches:")
for m in sorted(result['matches']):
    print(f"  - '{m}'")
