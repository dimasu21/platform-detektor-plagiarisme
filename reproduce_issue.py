from preprocessing import preprocess_text
from rabin_karp import detect_plagiarism

# Teks dari User Screenshot
suspect_raw = "Game Development adalah proses perancangan, pembuatan, dan pengujian game. Scratch berperan sbg tools pembelajaran karena menyediakan pemrograman visual berbasis blok."
source_raw = "Game Development adalah proses merancang, membuat, dan menguji game. Scratch berperan sebagai tools edukatif untuk belajar logika dan konsep dasar pembuatan game secara visual."

print(f"--- Raw Texts ---")
print(f"Suspect: {suspect_raw}")
print(f"Source:  {source_raw}")
print("-" * 30)

# Preprocess
suspect_proc = preprocess_text(suspect_raw)
source_proc = preprocess_text(source_raw)

print(f"--- Processed Texts ---")
print(f"Suspect: {suspect_raw}") # Showing raw again for context, assuming preprocess_text doesn't change much
print("-" * 30)

# Test with K=5 (Current Default)
print(f"--- Testing match with K=5 ---")
result_k5 = detect_plagiarism(suspect_proc, source_proc, k=5)
print(f"Score: {result_k5['similarity_score']}%")
print(f"Matches: {result_k5['matches']}")

# Test with K=3 (More lenient)
print(f"\n--- Testing match with K=3 ---")
result_k3 = detect_plagiarism(suspect_proc, source_proc, k=3)
print(f"Score: {result_k3['similarity_score']}%")
print(f"Matches: {result_k3['matches']}")

# Test with K=4
print(f"\n--- Testing match with K=4 ---")
result_k4 = detect_plagiarism(suspect_proc, source_proc, k=4)
print(f"Score: {result_k4['similarity_score']}%")
print(f"Matches: {result_k4['matches']}")
