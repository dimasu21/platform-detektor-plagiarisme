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
            
    # Calculate similarity score
    # Formula: (Matches / Total Suspect N-grams) * 100
    similarity_score = (match_count / len(suspect_ngrams)) * 100 if suspect_ngrams else 0.0
    
    return {
        "similarity_score": round(similarity_score, 2),
        "matches": list(set(matches)) # Return unique matches
    }
