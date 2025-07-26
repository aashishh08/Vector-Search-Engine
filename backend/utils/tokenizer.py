import nltk
from nltk.tokenize import word_tokenize

# Ensure 'punkt' tokenizer is downloaded
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')

def chunk_text(text: str, max_tokens: int = 500) -> list[str]:
    """
    Tokenizes text and splits it into smaller chunks, each up to max_tokens.
    This function is now responsible for breaking down larger text blocks
    (from fetcher.py) into the 500-token segments for embedding.
    """
    if not text:
        return []

    words = word_tokenize(text)
    chunks = []
    current_chunk = []
    current_chunk_len = 0

    for word in words:
        # Check if adding the next word would exceed the max_tokens limit
        # We consider word_tokenize output as tokens.
        if current_chunk_len + 1 > max_tokens and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_chunk_len = 0

        current_chunk.append(word)
        current_chunk_len += 1

    # Add any remaining tokens as the last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks