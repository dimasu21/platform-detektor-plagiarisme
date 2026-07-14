"""
Test: Image Structural Similarity (SSIM) on handwritten exam images.
This tests the new hybrid approach - comparing images visually instead of
relying solely on Tesseract OCR text extraction.
"""
import sys
sys.path.insert(0, r'd:\projectpribadi\platform-plagiarisme')

from PIL import Image
from file_parser import compute_image_similarity

# Test all pairs
images = {
    "Dimas": r"d:\projectpribadi\platform-plagiarisme\Data Citra\Dimas - Computer Vision.jpeg",
    "Dea": r"d:\projectpribadi\platform-plagiarisme\Data Citra\Dea - Computer Vision.jpg",
    "Nabila": r"d:\projectpribadi\platform-plagiarisme\Data Citra\Nabila - Computer Vision.jpg",
    "Ziamul": r"d:\projectpribadi\platform-plagiarisme\Data Citra\Ziamul - Computer Vision.jpeg",
}

names = list(images.keys())

print(f"\n{'='*60}")
print("IMAGE STRUCTURAL SIMILARITY RESULTS")
print(f"{'='*60}\n")

for i in range(len(names)):
    for j in range(i+1, len(names)):
        n1, n2 = names[i], names[j]
        img1 = Image.open(images[n1])
        img2 = Image.open(images[n2])
        
        score = compute_image_similarity(img1, img2)
        print(f"\n  {n1} vs {n2}: {score}%\n")

print(f"\n{'='*60}")
print("TEST COMPLETE")
print(f"{'='*60}")
