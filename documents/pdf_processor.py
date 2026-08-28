def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Extracts text from PDF file page by page.
    Returns a list of dicts: [{"page": page_num, "text": page_text}]
    """
    pages_data = []

    # Primary: PyMuPDF (fitz)
    try:
        import fitz  # type: ignore

        doc = fitz.open(file_path)
        for page_idx in range(len(doc)):
            page = doc.load_page(page_idx)
            text = str(page.get_text("text"))
            if text.strip():
                pages_data.append({"page": page_idx + 1, "text": text})
        doc.close()
        if pages_data:
            return pages_data
    except Exception as e:
        print(f"fitz extraction failed, falling back to PyPDF2: {e}")

    # Fallback: PyPDF2
    try:
        import PyPDF2

        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    pages_data.append({"page": page_idx + 1, "text": text})
    except Exception as e:
        print(f"PyPDF2 extraction failed: {e}")

    return pages_data
