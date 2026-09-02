import numpy as np
from config import settings
from rag.embeddings import get_embedding, _generate_local_fallback_embedding
from rag.vector_store import vector_store
from sqlalchemy.orm import Session
from database.models import Chunk, Document
from typing import Optional, Any


def retrieve_relevant_chunks(
    question: str,
    db: Session,
    top_k: Optional[int] = None,
    threshold: Optional[float] = None,
) -> list[dict]:
    """
    1. Embed user question.
    2. Perform similarity search against vector store.
    3. If vector store returns results, filter by similarity threshold (or return top results).
    4. Fall back to database chunks with local fast vector similarity if vector store is unavailable.
    """
    k: int = top_k if top_k is not None else settings.TOP_K
    thresh: float = (
        threshold if threshold is not None else settings.SIMILARITY_THRESHOLD
    )

    query_vec = get_embedding(question)

    # Try vector store first
    results = vector_store.search(query_vec, top_k=k)

    # Filter by threshold
    filtered_results = [r for r in results if r["score"] >= thresh]

    if filtered_results:
        return filtered_results
    elif results:
        # Vector store returned items slightly below threshold — return top results to avoid expensive fallback
        return results

    # Fallback to direct DB chunks search with fast local TF-IDF embeddings (zero API overhead)
    db_chunks: Any = db.query(Chunk).all()
    if not db_chunks:
        return []

    local_q_vec = _generate_local_fallback_embedding(question)
    q_arr = np.array(local_q_vec, dtype=np.float32)
    q_norm = np.linalg.norm(q_arr)

    scored_chunks = []
    for chunk in db_chunks:
        c_text = str(chunk.chunk_text)
        c_vec = _generate_local_fallback_embedding(c_text)
        c_arr = np.array(c_vec, dtype=np.float32)
        c_norm = np.linalg.norm(c_arr)

        if q_norm > 0 and c_norm > 0:
            sim = float(np.dot(q_arr, c_arr) / (q_norm * c_norm))
        else:
            sim = 0.0

        doc: Any = (
            db.query(Document).filter(Document.id == chunk.document_id).first()
        )
        doc_name = str(doc.file_name) if doc else f"Document_{chunk.document_id}"
        doc_title = str(doc.title) if doc else doc_name

        scored_chunks.append(
            {
                "chunk_id": str(chunk.id),
                "score": round(sim, 4),
                "text": c_text,
                "metadata": {
                    "document_id": chunk.document_id,
                    "document_name": doc_name,
                    "document_title": doc_title,
                    "page": chunk.page_number or 1,
                    "section": chunk.section or "General",
                },
            }
        )

    scored_chunks.sort(key=lambda x: float(str(x["score"])), reverse=True)
    return scored_chunks[:k]
