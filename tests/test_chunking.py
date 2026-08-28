from rag.text_cleaner import clean_text
from rag.chunker import chunk_extracted_pages


def test_text_cleaner():
    raw_text = "  Hello   World!\n\n\n\nThis is   a test.\x00 "
    cleaned = clean_text(raw_text)
    assert "\x00" not in cleaned
    assert "   " not in cleaned
    assert "Hello World!" in cleaned


def test_chunk_extracted_pages_preserves_metadata():
    pages_data = [
        {
            "page": 1,
            "section": "Admissions",
            "text": "The last date for admission fee payment is August 30, 2026. All candidates must bring original certificates for physical verification at room 102.",
        },
        {
            "page": 2,
            "section": "Hostel",
            "text": "Hostel registrations open on September 1, 2026. Students must submit a medical fitness certificate.",
        },
    ]

    chunks = chunk_extracted_pages(pages_data, chunk_size=50, chunk_overlap=10)
    assert len(chunks) > 0
    assert chunks[0]["page"] == 1
    assert chunks[0]["section"] == "Admissions"
    assert "text" in chunks[0]
