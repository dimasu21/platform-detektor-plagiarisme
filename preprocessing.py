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
