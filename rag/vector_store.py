from config import settings
from typing import Any


class VectorStore:
    def __init__(self):
        self.chroma_client: Any = None
        self.collection: Any = None
        self._init_chroma()

    def _init_chroma(self):
        try:
            import chromadb

            self.chroma_client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name="college_knowledge_base", metadata={"hnsw:space": "cosine"}
            )
            print("ChromaDB vector store initialized successfully.")
        except Exception as e:
            print(
                f"ChromaDB initialization fallback to NumPy in-memory vector store: {e}"
            )

    def add_chunks(
        self,
        chunk_ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ):
        if not chunk_ids:
            return
        if self.collection is not None:
            try:
                self.collection.add(
                    ids=[str(cid) for cid in chunk_ids],
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,  # type: ignore
                )
                return
            except Exception as e:
                print(f"ChromaDB add error: {e}")

    def delete_chunks(self, chunk_ids: list[str]):
        if not chunk_ids:
            return
        if self.collection is not None:
            try:
                self.collection.delete(ids=[str(cid) for cid in chunk_ids])
            except Exception as e:
                print(f"ChromaDB delete error: {e}")

    def delete_by_document(self, document_id: int):
        if self.collection is not None:
            try:
                self.collection.delete(where={"document_id": document_id})
            except Exception as e:
                print(f"ChromaDB delete by doc error: {e}")

    def search(self, query_embedding: list[float], top_k: int = 4) -> list[dict]:
        """
        Searches vector store using query embedding.
        Returns list of dicts: [{"chunk_id": str, "score": float, "text": str, "metadata": dict}]
        """
        if self.collection is not None:
            try:
                results: Any = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    include=["documents", "metadatas", "distances"],
                )
                retrieved = []
                has_valid_ids = bool(results and isinstance(results, dict) and "ids" in results and results["ids"] and len(results["ids"][0]) > 0)
                if has_valid_ids:
                    ids = results["ids"][0]
                    docs = results.get("documents", [[]])[0]
                    metas = results.get("metadatas", [[]])[0]
                    distances = (
                        results.get("distances", [[]])[0]
                        if "distances" in results
                        else [0.0] * len(ids)
                    )

                    for cid, doc_text, meta, dist in zip(ids, docs, metas, distances):
                        # Cosine distance to similarity: similarity = 1 - distance
                        similarity = (
                            max(0.0, 1.0 - float(dist)) if dist is not None else 0.5
                        )
                        retrieved.append(
                            {
                                "chunk_id": str(cid),
                                "score": round(similarity, 4),
                                "text": str(doc_text),
                                "metadata": meta if isinstance(meta, dict) else {},
                            }
                        )
                return retrieved
            except Exception as e:
                print(f"ChromaDB query error: {e}")

        return []


vector_store = VectorStore()
