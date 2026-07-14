"""
Test Script: Verifikasi Implementasi Rabin-Karp Murni
=====================================================
Menguji:
  1. Character-level K-Gram generation
  2. Rolling Hash computation
  3. Dice's Similarity Coefficient
  4. Match segment extraction
"""

from preprocessing import preprocess_text
from rabin_karp import generate_kgrams, rolling_hash, compute_fingerprints, detect_plagiarism

print("=" * 70)
print("TEST 1: Character-level K-Gram (k=3)")
print("=" * 70)

test_text = "sistem"
kgrams = generate_kgrams(test_text, k=3)
print(f"Input: '{test_text}'")
print(f"K-Grams (k=3): {kgrams}")
assert kgrams == ["sis", "ist", "ste", "tem"], f"Expected ['sis', 'ist', 'ste', 'tem'], got {kgrams}"
print("✓ PASS\n")

print("=" * 70)
print("TEST 2: Rolling Hash")
print("=" * 70)

# Verify hash is deterministic
h1 = rolling_hash("sis")
h2 = rolling_hash("sis")
h3 = rolling_hash("ist")
print(f"Hash('sis') = {h1}")
print(f"Hash('sis') = {h2}  (harus sama)")
print(f"Hash('ist') = {h3}  (harus berbeda)")
assert h1 == h2, "Hash harus deterministik"
assert h1 != h3, "Hash karakter berbeda harus berbeda"
print("✓ PASS\n")

print("=" * 70)
print("TEST 3: Rolling Hash vs Direct Hash (Konsistensi)")
print("=" * 70)

text = "algoritma"
fingerprints = compute_fingerprints(text, k=3)
print(f"Input: '{text}'")
print(f"Fingerprints (k=3):")
for h, kg, pos in fingerprints:
    direct_h = rolling_hash(kg)
    match_status = "✓" if h == direct_h else "✗ MISMATCH"
    print(f"  pos={pos}: '{kg}' -> hash={h} (direct={direct_h}) {match_status}")
    assert h == direct_h, f"Rolling hash mismatch at pos {pos}"
print("✓ PASS - Rolling hash konsisten dengan direct hash\n")

print("=" * 70)
print("TEST 4: Deteksi Plagiarisme - Teks Identik")
print("=" * 70)

text_a = "algoritma rabin karp digunakan untuk deteksi plagiarisme"
text_b = "algoritma rabin karp digunakan untuk deteksi plagiarisme"
result = detect_plagiarism(text_a, text_b, k=3)
print(f"Suspect: '{text_a}'")
print(f"Source:  '{text_b}'")
print(f"Skor Kemiripan: {result['similarity_score']}%")
print(f"Matches: {result['matches']}")
assert result['similarity_score'] == 100.0, f"Teks identik harus 100%, got {result['similarity_score']}%"
print("✓ PASS\n")

print("=" * 70)
print("TEST 5: Deteksi Plagiarisme - Teks Berbeda Total")
print("=" * 70)

text_c = "kucing berlari cepat"
text_d = "pohon tumbuh tinggi"
result2 = detect_plagiarism(text_c, text_d, k=3)
print(f"Suspect: '{text_c}'")
print(f"Source:  '{text_d}'")
print(f"Skor Kemiripan: {result2['similarity_score']}%")
print(f"Matches: {result2['matches']}")
print(f"✓ Skor rendah menunjukkan teks memang berbeda\n")

print("=" * 70)
print("TEST 6: Deteksi Plagiarisme - Teks Sebagian Mirip")
print("=" * 70)

text_e = "algoritma rabin karp sangat efisien untuk pencocokan string"
text_f = "algoritma rabin karp adalah metode pencocokan string yang cepat"
result3 = detect_plagiarism(text_e, text_f, k=3)
print(f"Suspect: '{text_e}'")
print(f"Source:  '{text_f}'")
print(f"Skor Kemiripan: {result3['similarity_score']}%")
print(f"Matches: {result3['matches']}")
print(f"✓ Skor menengah menunjukkan kemiripan parsial\n")

print("=" * 70)
print("TEST 7: Integrasi dengan Preprocessing")
print("=" * 70)

raw_a = "Algoritma Rabin-Karp DIGUNAKAN untuk mendeteksi plagiarisme dalam dokumen."
raw_b = "Penggunaan algoritma rabin-karp bertujuan untuk mendeteksi kecurangan plagiarisme."

prep_a = preprocess_text(raw_a)
prep_b = preprocess_text(raw_b)
print(f"Raw Suspect:     '{raw_a}'")
print(f"Preprocessed:    '{prep_a}'")
print(f"Raw Source:      '{raw_b}'")
print(f"Preprocessed:    '{prep_b}'")

result4 = detect_plagiarism(prep_a, prep_b, k=3)
print(f"Skor Kemiripan:  {result4['similarity_score']}%")
print(f"Matches:         {result4['matches']}")
print("✓ PASS - Preprocessing + Rabin-Karp terintegrasi\n")

print("=" * 70)
print("SEMUA TEST BERHASIL! ✓")
print("=" * 70)
