"""
Text Highlighter Module

Provides functions to highlight matching text phrases in HTML format
for visual plagiarism comparison.
"""

import re
from html import escape


def highlight_text_matches(original_text, matches):
    """
    Highlight matched phrases in text by wrapping them with HTML mark tags.
    
    Since K-gram matches are preprocessed (lowercase, stemmed, no stopwords),
    we need to find and highlight the individual words from matches in the original text.
    
    Args:
        original_text (str): The original text to highlight
        matches (list): List of matched phrases (k-grams) from preprocessed text
        
    Returns:
        str: HTML string with matched words wrapped in <mark> tags
    """
    if not original_text or not matches:
        return escape(original_text) if original_text else ""
    
    # Extract all unique words from matches
    matched_words = set()
    for match in matches:
        words = match.lower().split()
        matched_words.update(words)
    
    print(f"DEBUG: Words to highlight: {matched_words}")
    
    # Build regex pattern to find these words in original text
    # Match whole words only, case-insensitive
    if not matched_words:
        return escape(original_text)
    
    # Create pattern that matches any of the words
    # We use word boundaries for better matching
    pattern_words = '|'.join(re.escape(word) for word in matched_words)
    pattern = rf'\b({pattern_words})\b'
    
    # Find all matches and their positions
    highlights = []
    for m in re.finditer(pattern, original_text, re.IGNORECASE):
        highlights.append((m.start(), m.end()))
    
    print(f"DEBUG: Found {len(highlights)} highlight positions")
    
    # Merge overlapping highlights
    highlights = merge_overlapping_ranges(highlights)
    
    # Build the highlighted HTML string
    result = []
    last_end = 0
    
    for start, end in sorted(highlights):
        # Add non-highlighted text before this match
        if start > last_end:
            result.append(escape(original_text[last_end:start]))
        # Add highlighted match
        result.append(f'<mark class="plagiarism-highlight">{escape(original_text[start:end])}</mark>')
        last_end = end
    
    # Add remaining text after last match
    if last_end < len(original_text):
        result.append(escape(original_text[last_end:]))
    
    return ''.join(result)


def merge_overlapping_ranges(ranges):
    """
    Merge overlapping or adjacent ranges.
    
    Args:
        ranges: List of (start, end) tuples
        
    Returns:
        list: Merged list of non-overlapping ranges
    """
    if not ranges:
        return []
    
    # Sort by start position
    sorted_ranges = sorted(ranges, key=lambda x: x[0])
    merged = [sorted_ranges[0]]
    
    for start, end in sorted_ranges[1:]:
        last_start, last_end = merged[-1]
        
        # If this range overlaps or is adjacent to the last one, merge them
        if start <= last_end + 1:  # +1 to merge adjacent words too
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    
    return merged


def prepare_text_for_display(text, max_length=None):
    """
    Prepare text for display by cleaning up whitespace and optionally truncating.
    
    Args:
        text (str): Text to prepare
        max_length (int, optional): Maximum length before truncation
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    if max_length and len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text
