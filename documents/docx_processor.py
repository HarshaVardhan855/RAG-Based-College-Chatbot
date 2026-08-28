import docx
from typing import Any


def extract_text_from_docx(file_path: str) -> list[dict]:
    """
    Extracts text from DOCX file by paragraph / section.
    Returns a list of dicts: [{"page": page_num, "section": section_title, "text": text}]
    """
    doc: Any = docx.Document(file_path)
    paragraphs_data = []

    current_heading = "General"
    current_buffer: list[str] = []
    page_counter = 1

    for p in doc.paragraphs:
        text = str(p.text).strip()
        if not text:
            continue

        # Check if paragraph is a heading
        style_name = (
            str(p.style.name)
            if p.style and hasattr(p.style, "name") and p.style.name
            else ""
        )
        if style_name.startswith("Heading"):
            if current_buffer:
                paragraphs_data.append(
                    {
                        "page": page_counter,
                        "section": current_heading,
                        "text": "\n".join(current_buffer),
                    }
                )
                current_buffer = []
            current_heading = text
        else:
            current_buffer.append(text)

    if current_buffer:
        paragraphs_data.append(
            {
                "page": page_counter,
                "section": current_heading,
                "text": "\n".join(current_buffer),
            }
        )

    return paragraphs_data
