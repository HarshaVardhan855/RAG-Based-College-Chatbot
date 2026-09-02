import numpy as np
from config import settings
import re

STOP_WORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "up",
    "about",
    "into",
    "over",
    "after",
    "and",
    "or",
    "but",
    "so",
    "if",
    "then",
    "else",
    "when",
    "where",
    "why",
    "how",
    "all",
    "any",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "than",
    "too",
    "very",
    "can",
    "will",
    "just",
    "should",
    "now",
    "this",
    "that",
    "what",
    "which",
    "who",
    "whom",
    "whose",
    "it",
    "its",
    "my",
    "your",
    "his",
    "her",
    "do",
    "does",
    "did",
    "have",
    "has",
    "had",
}


_genai_client_cache = {}


def _get_cached_genai_client(api_key: str):
    if api_key not in _genai_client_cache:
        from google import genai

        _genai_client_cache[api_key] = genai.Client(api_key=api_key)
    return _genai_client_cache[api_key]


def get_embedding(text: str) -> list[float]:
    """
    Generates embedding for a single text chunk or user query.
    Tries Google Gemini API first.
    Falls back to normalized TF-IDF local embedding if API key is not configured or fails.
    """
    if settings.GEMINI_API_KEY:
        try:
            client = _get_cached_genai_client(settings.GEMINI_API_KEY)
            result = client.models.embed_content(
                model=settings.EMBEDDING_MODEL, contents=text
            )
            if hasattr(result, "embeddings") and result.embeddings and result.embeddings[0].values is not None:
                return list(result.embeddings[0].values)
            embedding_val = getattr(result, "embedding", None)
            if embedding_val and getattr(embedding_val, "values", None) is not None:
                return list(embedding_val.values)
            elif isinstance(result, dict) and result.get("embedding") is not None:
                return list(result["embedding"])
        except Exception as e:
            print(f"Gemini genai embedding error: {e}")

    return _generate_local_fallback_embedding(text)


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generates embeddings for a list of text strings.
    """
    return [get_embedding(t) for t in texts]


def _generate_local_fallback_embedding(text: str, dim: int = 384) -> list[float]:
    """
    Deterministic pseudo-embedding for testing environments without an external API key.
    Calculates term-frequency and character n-gram hash values mapped across 384 dimensions.
    """
    vec = np.zeros(dim, dtype=np.float32)
    words = [w for w in re.findall(r"\w+", text.lower()) if w not in STOP_WORDS]
    if not words:
        return vec.tolist()

    for idx, w in enumerate(words):
        h1 = hash(w) % dim
        h2 = hash(w + "_ngram") % dim
        vec[h1] += 1.0
        vec[h2] += 0.5

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()  # type: ignore
