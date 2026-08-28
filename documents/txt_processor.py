def extract_text_from_txt(file_path: str) -> list[dict]:
    """
    Extracts text from TXT file.
    Returns a list of dicts: [{"page": 1, "text": full_text}]
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if not content.strip():
        return []

    return [{"page": 1, "section": "Main Text", "text": content}]
