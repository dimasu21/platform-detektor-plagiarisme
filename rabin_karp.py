import logging

logger = logging.getLogger(__name__)
"""
Modul Algoritma Rabin-Karp

Implementasi murni algoritma Rabin-Karp untuk deteksi plagiarisme teks
menggunakan teknik:
  1. Character-level K-Gram (k=3)
  2. Rolling Hash (Polynomial Hashing)
  3. Dice's Similarity Coefficient

Referensi:
  - Rabin, M.O. & Karp, R.M. (1987). Efficient Randomized Pattern-Matching Algorithms.
"""


def generate_kgrams(text, k=3):
    """
    Menghasilkan k-gram pada level karakter dari teks.

    K-Gram adalah teknik pemotongan teks menjadi potongan karakter
    sepanjang k secara kontinyu dari awal hingga akhir dokumen.

    Contoh (k=3): "sistem" -> ["sis", "ist", "ste", "tem"]

    Args:
        text (str): Teks input (sudah dipreprocessing).
        k (int): Panjang k-gram dalam karakter (default: 3).

    Returns:
        list: Daftar string k-gram.
    """
    if not text or len(text) < k:
        return []

    kgrams = []
    for i in range(len(text) - k + 1):
        kgrams.append(text[i:i + k])
    return kgrams


def rolling_hash(text, base=257, mod=1000000007):
    """
    Menghitung nilai hash menggunakan Polynomial Rolling Hash.

    Rumus:
        H(s[0..k-1]) = s[0] * d^(k-1) + s[1] * d^(k-2) + ... + s[k-1] * d^0
        Semua operasi dilakukan modulo `mod`.

    Di mana:
        - d (base) = bilangan prima sebagai basis (257)
        - mod       = bilangan prima besar untuk mencegah overflow (10^9 + 7)
        - s[i]      = nilai ASCII dari karakter ke-i

    Args:
        text (str): String yang akan dihitung hash-nya.
        base (int): Basis untuk polynomial hash (default: 257).
        mod (int): Modulus prima besar (default: 10^9 + 7).

    Returns:
        int: Nilai hash dari string input.
    """
    h = 0
    for char in text:
        h = (h * base + ord(char)) % mod
    return h


def compute_fingerprints(text, k=3, base=257, mod=1000000007):
    """
    Menghitung hash fingerprint untuk seluruh k-gram menggunakan
    teknik Rolling Hash.

    Rolling Hash memungkinkan perhitungan hash k-gram berikutnya
    dilakukan secara efisien dengan cara:
        H(s[i+1..i+k]) = (H(s[i..i+k-1]) - s[i] * d^(k-1)) * d + s[i+k]

    Teknik ini jauh lebih efisien dibanding menghitung ulang hash
    dari nol untuk setiap k-gram.

    Args:
        text (str): Teks input (sudah dipreprocessing).
        k (int): Panjang k-gram dalam karakter.
        base (int): Basis polynomial hash.
        mod (int): Modulus prima.

    Returns:
        list of tuple: [(hash_value, kgram_string, position), ...]
    """
    n = len(text)
    if n < k:
        return []

    results = []

    # Precompute d^(k-1) % mod (digunakan untuk menghapus karakter terdepan)
    h_power = pow(base, k - 1, mod)

    # Hitung hash untuk k-gram pertama (window pertama)
    current_hash = 0
    for i in range(k):
        current_hash = (current_hash * base + ord(text[i])) % mod

    results.append((current_hash, text[0:k], 0))

    # Geser window (rolling) untuk k-gram berikutnya
    for i in range(1, n - k + 1):
        # Rolling hash formula:
        # 1. Hapus kontribusi karakter paling kiri: - s[i-1] * d^(k-1)
        # 2. Geser (kalikan dengan d): * d
        # 3. Tambahkan karakter baru di kanan: + s[i+k-1]
        current_hash = (
            (current_hash - ord(text[i - 1]) * h_power) * base + ord(text[i + k - 1])
        ) % mod

        # Pastikan hash positif (Python bisa menghasilkan mod negatif)
        current_hash = (current_hash + mod) % mod

        results.append((current_hash, text[i:i + k], i))

    return results


def detect_plagiarism(suspect_text, source_text, k=3):
    """
    Mendeteksi plagiarisme menggunakan algoritma Rabin-Karp murni.

    Alur proses:
        1. Hasilkan k-gram karakter dari kedua dokumen.
        2. Hitung rolling hash untuk setiap k-gram.
        3. Bandingkan fingerprint hash antara suspect dan source.
        4. Hitung persentase kemiripan menggunakan Dice's Coefficient.

    Rumus Dice's Similarity Coefficient:
        S = (2 × C) / (A + B) × 100%

    Di mana:
        - A = jumlah fingerprint unik pada dokumen suspect
        - B = jumlah fingerprint unik pada dokumen source
        - C = jumlah fingerprint yang sama (irisan / intersection)

    Args:
        suspect_text (str): Teks yang dicurigai plagiat (sudah dipreprocessing).
        source_text (str): Teks sumber/asli (sudah dipreprocessing).
        k (int): Panjang k-gram dalam karakter (default: 3).

    Returns:
        dict: Dictionary berisi:
            - similarity_score (float): Persentase kemiripan (0-100).
            - matches (list): Daftar segmen teks yang terdeteksi mirip.
    """
    # Langkah 1 & 2: Hasilkan fingerprint (hash k-gram) untuk kedua dokumen
    suspect_fingerprints = compute_fingerprints(suspect_text, k)
    source_fingerprints = compute_fingerprints(source_text, k)

    if not suspect_fingerprints or not source_fingerprints:
        return {"similarity_score": 0.0, "matches": []}

    # Kumpulkan hash unik dari masing-masing dokumen
    suspect_hash_set = set(h for h, _, _ in suspect_fingerprints)
    source_hash_set = set(h for h, _, _ in source_fingerprints)

    # Langkah 3: Temukan fingerprint yang cocok (irisan)
    common_hashes = suspect_hash_set.intersection(source_hash_set)

    # Langkah 4: Hitung Dice's Similarity Coefficient
    A = len(suspect_hash_set)   # Jumlah fingerprint unik suspect
    B = len(source_hash_set)    # Jumlah fingerprint unik source
    C = len(common_hashes)      # Jumlah fingerprint yang sama

    similarity_score = (2 * C) / (A + B) * 100 if (A + B) > 0 else 0.0

    logger.debug(f"DEBUG Rabin-Karp: K-Gram={k}, Suspect={A}, Source={B}, Match={C}")
    logger.debug(f"DEBUG Rabin-Karp: Dice = (2×{C}) / ({A}+{B}) × 100 = {similarity_score:.2f}%")

    # Ekstrak segmen teks yang cocok untuk keperluan highlighting
    matching_positions = []
    for h, kgram, pos in suspect_fingerprints:
        if h in common_hashes:
            matching_positions.append(pos)

    matches = _extract_match_segments(suspect_text, matching_positions, k)

    return {
        "similarity_score": round(similarity_score, 2),
        "matches": matches
    }


def _extract_match_segments(text, matching_positions, k):
    """
    Mengonversi posisi k-gram karakter yang cocok menjadi segmen kata
    untuk keperluan highlighting pada teks asli.

    Proses:
        1. Buat mask boolean untuk setiap karakter yang termasuk k-gram cocok.
        2. Gabungkan posisi yang bersebelahan menjadi segmen kontinu.
        3. Ekstrak kata-kata dari segmen tersebut.

    Args:
        text (str): Teks yang dipreprocessing.
        matching_positions (list): Daftar posisi awal k-gram yang cocok.
        k (int): Panjang k-gram.

    Returns:
        list: Daftar kata/segmen unik yang terdeteksi mirip.
    """
    if not matching_positions or not text:
        return []

    # Buat mask karakter yang termasuk dalam k-gram yang cocok
    char_mask = [False] * len(text)
    for pos in matching_positions:
        for i in range(pos, min(pos + k, len(text))):
            char_mask[i] = True

    # Gabungkan karakter bersebelahan yang cocok menjadi segmen kontinu
    segments = []
    in_segment = False
    start = 0

    for i, matched in enumerate(char_mask):
        if matched and not in_segment:
            start = i
            in_segment = True
        elif not matched and in_segment:
            segments.append((start, i))
            in_segment = False

    if in_segment:
        segments.append((start, len(text)))

    # Ekstrak kata-kata dari setiap segmen untuk highlighting
    matched_words = set()
    for seg_start, seg_end in segments:
        segment_text = text[seg_start:seg_end]
        words = segment_text.split()
        for word in words:
            # Hanya ambil kata dengan panjang >= 2 karakter
            clean_word = word.strip()
            if len(clean_word) >= 2:
                matched_words.add(clean_word)

    return list(matched_words)
