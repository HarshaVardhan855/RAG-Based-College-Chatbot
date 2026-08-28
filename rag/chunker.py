from config import settings
from rag.text_cleaner import clean_text
from typing import Optional


def chunk_extracted_pages(
    pages_data: list[dict],
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> list[dict]:
    """
    Chunks extracted pages into smaller text segments with overlap.
    Preserves page and section metadata on each chunk.
    Returns: list of dicts [{"text": str, "page": int, "section": str}]
    """
    size: int = chunk_size if chunk_size is not None else settings.CHUNK_SIZE
    overlap: int = (
        chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP
    )

    chunks = []

    for page_info in pages_data:
        raw_text = page_info.get("text", "")
        cleaned = clean_text(raw_text)
        if not cleaned:
            continue

        page_num = page_info.get("page", 1)
        section_name = page_info.get("section", "General")

        words = cleaned.split(" ")
        current_chunk: list[str] = []
        current_length = 0

        for word in words:
            word_len = len(word) + 1
            if current_length + word_len > size and current_chunk:
                chunk_str = " ".join(current_chunk).strip()
                if chunk_str:
                    chunks.append(
                        {"text": chunk_str, "page": page_num, "section": section_name}
                    )

                overlap_words: list[str] = []
                overlap_len = 0
                for w in reversed(current_chunk):
                    if overlap_len + len(w) + 1 <= overlap:
                        overlap_words.insert(0, w)
                        overlap_len += len(w) + 1
                    else:
                        break

                current_chunk = overlap_words + [word]
                current_length = sum(len(w) + 1 for w in current_chunk)
            else:
                current_chunk.append(word)
                current_length += word_len

        if current_chunk:
            chunk_str = " ".join(current_chunk).strip()
            if chunk_str:
                chunks.append(
                    {"text": chunk_str, "page": page_num, "section": section_name}
                )

    return chunks
