def generate_ngrams(text, k):
    """Generates k-grams (substrings of length k words) from the text."""
    words = text.split()
    if len(words) < k:
        return []
    
    ngrams = []
    for i in range(len(words) - k + 1):
        ngram = " ".join(words[i:i+k])
        ngrams.append(ngram)
    return ngrams

def calculate_hash(text):
    """
    Calculates a simple hash for a string.
    In a real-world scenario, a rolling hash is more efficient,
    but for this demo with word-level k-grams, Python's built-in hash is sufficient and robust.
    """
    return hash(text)

def detect_plagiarism(suspect_text, source_text, k=5):
    """
    Detects plagiarism using the Rabin-Karp algorithm concept (hashing k-grams).
    
    Args:
        suspect_text (str): The text to check (preprocessed).
        source_text (str): The original source text (preprocessed).
        k (int): The length of the k-gram (in words).
        
    Returns:
        dict: A dictionary containing:
            - similarity_score (float): Percentage of matching k-grams.
            - matches (list): List of matching k-grams.
    """
    suspect_ngrams = generate_ngrams(suspect_text, k)
    source_ngrams = generate_ngrams(source_text, k)
    
    if not suspect_ngrams:
        return {"similarity_score": 0.0, "matches": []}

    # Create a set of hashes for the source n-grams for O(1) lookups
    source_hashes = set(calculate_hash(ngram) for ngram in source_ngrams)
    
    matches = []
    match_count = 0
    
    for ngram in suspect_ngrams:
        ngram_hash = calculate_hash(ngram)
        if ngram_hash in source_hashes:
            matches.append(ngram)
            match_count += 1
            
    # Calculate similarity score (Rabin-Karp)
    # Formula: (Matches / Total Suspect N-grams) * 100
    rk_score = (match_count / len(suspect_ngrams)) * 100 if suspect_ngrams else 0.0
    
    # --- HYBRID IMPROVEMENT: JACCARD SIMILARITY ---
    # Calculates word overlap to detect paraphrasing
    suspect_words = set(suspect_text.split())
    source_words = set(source_text.split())
    
    # Filter short words to avoid noise in highlighting
    intersection = {w for w in suspect_words.intersection(source_words) if len(w) > 3}
    union = suspect_words.union(source_words)
    
    jaccard_score = (len(intersection) / len(union)) * 100 if union else 0.0
    
    print(f"DEBUG: RK Score: {rk_score:.2f}%, Jaccard Score: {jaccard_score:.2f}%")
    
    # Use the higher of the two scores
    final_score = max(rk_score, jaccard_score)
    
    # If Jaccard is significantly helpful, add individual words to matches for highlighting
    if jaccard_score > rk_score:
        matches.extend(list(intersection))
    
    return {
        "similarity_score": round(final_score, 2),
        "matches": list(set(matches)) # Return unique matches
    }
