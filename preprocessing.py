import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

# Initialize Sastrawi factories once to avoid overhead
stemmer_factory = StemmerFactory()
stemmer = stemmer_factory.create_stemmer()

stopword_factory = StopWordRemoverFactory()
stopword_remover = stopword_factory.create_stop_word_remover()

def preprocess_text(text):
    """
    Preprocesses the input text by:
    1. Case folding (lowercasing)
    2. Removing punctuation and special characters
    3. Removing stopwords (Indonesian)
    4. Stemming (Indonesian)
    """
    if not text:
        return ""

    # Custom Stopwords: Abaikan kata-kata di kop surat ujian
    # Ini mencegah header terdeteksi sebagai plagiarisme
    header_keywords = [
        r'\bfakultas\b', r'\bteknik\b', r'\bilmu\b', r'\bkomputer\b', 
        r'\buniversitas\b', r'\bpancasakti\b', r'\btegal\b',
        r'\bujian\b', r'\bakhir\b', r'\bsemester\b', r'\bta\b',
        r'\bnama\b', r'\bmata\b', r'\bkuliah\b', r'\bhari\b', r'\btgl\b', r'\btanggal\b',
        r'\bpresensi\b', r'\bsks\b', r'\bkls\b', r'\bkelas\b', r'\btangan\b', r'\bno\b'
    ]
    
    # Hapus kata-kata header dari teks mentah (case-insensitive)
    for keyword in header_keywords:
        text = re.sub(keyword, '', text, flags=re.IGNORECASE)

    # 1. Case Folding
    text = text.lower()

    # 2. Remove Punctuation and Special Characters
    # Keep only alphanumeric and whitespace
    text = re.sub(r'[^a-z0-9\s]', '', text)

    # 3. Stopword Removal
    text = stopword_remover.remove(text)

    # 4. Stemming
    text = stemmer.stem(text)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text
