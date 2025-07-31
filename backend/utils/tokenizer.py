import nltk
from nltk.tokenize import word_tokenize

# Download punkt tokenizer if needed
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')

def chunk_text(text: str, max_tokens: int = 500) -> list[str]:
    """Split text into chunks of max_tokens length."""
    if not text:
        return []

    words = word_tokenize(text)
    chunks = []
    current_chunk = []
    current_len = 0

    for word in words:
        if current_len + 1 > max_tokens and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_len = 0

        current_chunk.append(word)
        current_len += 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks