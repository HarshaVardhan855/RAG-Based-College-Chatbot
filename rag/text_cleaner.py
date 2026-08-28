import re


def clean_text(text: str) -> str:
    """
    Cleans raw extracted document text without destroying structure or important headings.
    """
    if not text:
        return ""

    # Replace null bytes
    text = text.replace("\x00", "")

    # Replace multiple horizontal whitespaces (spaces/tabs) with a single space
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize excessive newlines (more than 2 consecutive newlines to 2)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    # Clean leading/trailing whitespace per line
    lines = [line.strip() for line in text.split("\n")]
    cleaned_text = "\n".join(lines)

    return cleaned_text.strip()
