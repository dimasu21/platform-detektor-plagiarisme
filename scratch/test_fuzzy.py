import difflib
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

def get_fuzzy_matches(suspect_text, source_text):
    seq_matcher = difflib.SequenceMatcher(None, suspect_text, source_text)
    seq_score = seq_matcher.ratio() * 100
    
    matches = []
    # get_matching_blocks returns (i, j, n)
    for i, j, n in seq_matcher.get_matching_blocks():
        if n > 4: # match length in characters
            match_str = suspect_text[i:i+n].strip()
            if len(match_str.split()) >= 1 and len(match_str) > 3:
                matches.append(match_str)
                
    return seq_score, matches

s1 = "klasifikai citra vs deteksi objek. klasifikasi menentukan jenis objek dalam gambar"
s2 = "klasifikasi menentukan jenis objek dalam gambar tanpa lokasi deteksi objek menentukan jenis dan lokasi"

score, matches = get_fuzzy_matches(s1, s2)
print(f"Score: {score}")
print(f"Matches: {matches}")
