"""
Batch Cross-Comparison Module

Provides functions to compare multiple documents against each other
and generate a similarity matrix.
"""

from itertools import combinations
from rabin_karp import detect_plagiarism
from preprocessing import preprocess_text


def compare_all_pairs(documents):
    """
    Compare all pairs of documents and return similarity results.
    
    Args:
        documents: List of dicts with 'name', 'text', and optional 'images' keys
        
    Returns:
        dict with:
            - 'matrix': 2D dict of similarity scores
            - 'pairs': List of all pair comparisons with details
            - 'suspicious': List of pairs with similarity > threshold
    """
    n = len(documents)
    
    # Initialize matrix
    matrix = {}
    for doc in documents:
        matrix[doc['name']] = {}
        for doc2 in documents:
            if doc['name'] == doc2['name']:
                matrix[doc['name']][doc2['name']] = None  # Self comparison
            else:
                matrix[doc['name']][doc2['name']] = 0
    
    # Compare all unique pairs
    pairs = []
    for doc1, doc2 in combinations(documents, 2):
        # Preprocess texts
        text1_processed = preprocess_text(doc1['text'])
        text2_processed = preprocess_text(doc2['text'])
        
        # Run plagiarism detection
        result = detect_plagiarism(text1_processed, text2_processed, k=5)
        
        pair_result = {
            'doc1_name': doc1['name'],
            'doc2_name': doc2['name'],
            'doc1_text': doc1['text'],
            'doc2_text': doc2['text'],
            'doc1_images': doc1.get('images', []),
            'doc2_images': doc2.get('images', []),
            'similarity': result['similarity_score'],
            'matches': result['matches']
        }
        pairs.append(pair_result)
        
        # Update matrix (symmetric)
        matrix[doc1['name']][doc2['name']] = result['similarity_score']
        matrix[doc2['name']][doc1['name']] = result['similarity_score']
    
    return {
        'matrix': matrix,
        'pairs': pairs,
        'document_names': [doc['name'] for doc in documents]
    }


def get_suspicious_pairs(pairs, threshold=50):
    """
    Filter pairs with similarity above threshold.
    
    Args:
        pairs: List of pair comparison results
        threshold: Minimum similarity score to flag as suspicious
        
    Returns:
        List of suspicious pairs sorted by similarity (highest first)
    """
    suspicious = [p for p in pairs if p['similarity'] >= threshold]
    return sorted(suspicious, key=lambda x: x['similarity'], reverse=True)


def get_comparison_stats(pairs):
    """
    Calculate statistics from comparison results.
    
    Args:
        pairs: List of pair comparison results
        
    Returns:
        dict with statistics
    """
    if not pairs:
        return {
            'total_comparisons': 0,
            'avg_similarity': 0,
            'max_similarity': 0,
            'min_similarity': 0,
            'high_risk_count': 0,
            'medium_risk_count': 0,
            'low_risk_count': 0
        }
    
    similarities = [p['similarity'] for p in pairs]
    
    return {
        'total_comparisons': len(pairs),
        'avg_similarity': round(sum(similarities) / len(similarities), 1),
        'max_similarity': max(similarities),
        'min_similarity': min(similarities),
        'high_risk_count': len([s for s in similarities if s > 50]),
        'medium_risk_count': len([s for s in similarities if 20 < s <= 50]),
        'low_risk_count': len([s for s in similarities if s <= 20])
    }
