import os
import sys
import json
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.abspath("."))

from config import settings
from database.connection import SessionLocal
from database.models import Document, Chunk
from documents.pdf_processor import extract_text_from_pdf
from rag.embeddings import get_embedding
from rag.vector_store import vector_store
from rag.retriever import retrieve_relevant_chunks
from rag.pipeline import run_rag_pipeline

def verify():
    db = SessionLocal()

    print("=" * 70)
    print("STEP 1: DATABASE RECORD FOR CT UNIVERSITY BROCHURE")
    print("=" * 70)
    ct_doc = db.query(Document).filter(Document.file_name.ilike("%CT%")).first()
    if not ct_doc:
        ct_doc = db.query(Document).first()

    if ct_doc:
        chunk_count = db.query(Chunk).filter(Chunk.document_id == ct_doc.id).count()
        print(f"Document ID: {ct_doc.id}")
        print(f"Filename: {ct_doc.file_name}")
        print(f"Processing Status: {ct_doc.status}")
        print(f"Number of Chunks: {chunk_count}")
        print(f"Upload Status: {ct_doc.status}")
    else:
        print("ERROR: Document not found in DB")
        return

    print("\n" + "=" * 70)
    print("STEP 2: EXTRACTED TEXT FROM CT UNIVERSITY BROCHURE")
    print("=" * 70)
    extracted = extract_text_from_pdf(str(ct_doc.file_path))
    total_text = "\n".join(p.get("text", "") for p in extracted)
    print(f"Extracted Text Length: {len(total_text)} characters")
    has_courses = any(w in total_text.lower() for w in ["b.tech", "bba", "ll.b", "course", "program", "engineering"])
    print(f"Course/Program Information Exists: {has_courses}")

    print("\n" + "=" * 70)
    print("STEP 3: CHROMADB CHECK")
    print("=" * 70)
    col = vector_store.collection
    print(f"Collection Name: {col.name if col else 'None'}")
    total_vectors = col.count() if col else 0
    print(f"Total Vector Count: {total_vectors}")
    if col and ct_doc:
        res = col.get(where={"document_id": ct_doc.id})
        doc_vectors = len(res.get("ids", []))
        print(f"Vectors belonging to CT University Brochure: {doc_vectors}")

    print("\n" + "=" * 70)
    print("STEP 4: DIRECT RETRIEVER TEST")
    print("Query: 'What are the courses available in CT University?'")
    print("=" * 70)
    q1 = "What are the courses available in CT University?"
    retrieved_chunks = retrieve_relevant_chunks(q1, db, top_k=4)

    print(f"Retrieved Chunks Count: {len(retrieved_chunks)}")
    for idx, r in enumerate(retrieved_chunks):
        meta = r.get("metadata", {})
        print(f"\n--- Result {idx + 1} ---")
        print(f"Document Name: {meta.get('document_name')}")
        print(f"Chunk ID: {r.get('chunk_id')}")
        print(f"Similarity Score: {r.get('score')}")
        print(f"Page Number: {meta.get('page')}")
        print(f"First 300 Characters: {r.get('text', '')[:300].replace(chr(10), ' ')}")

    print("\n" + "=" * 70)
    print("STEP 6 & 7: SIMILARITY THRESHOLD & RAG PIPELINE EXECUTION FOR Q1")
    print("=" * 70)
    q1_result = run_rag_pipeline(q1, db)
    print(f"\nQ1 Answer:\n{q1_result['answer']}")
    print(f"\nQ1 Sources:\n{json.dumps(q1_result['sources'], indent=2)}")

    print("\n" + "=" * 70)
    print("STEP 10: UNRELATED QUESTION TEST")
    print("Query: 'What is CT University\\'s Mars campus fee for 2035?'")
    print("=" * 70)
    q2 = "What is CT University's Mars campus fee for 2035?"
    q2_result = run_rag_pipeline(q2, db)
    print(f"\nQ2 Answer:\n{q2_result['answer']}")
    print(f"\nQ2 Sources:\n{json.dumps(q2_result['sources'], indent=2)}")

    db.close()

if __name__ == "__main__":
    verify()
