from rag.embeddings import get_embedding
import numpy as np


def test_embedding_generation():
    text = "The examination registration deadline is September 15, 2026."
    emb = get_embedding(text)
    assert isinstance(emb, list)
    assert len(emb) > 0


def test_cosine_similarity_ranking():
    vec_q = np.array(get_embedding("What is the exam deadline?"), dtype=np.float32)
    vec_match = np.array(
        get_embedding("The examination registration deadline is September 15, 2026."),
        dtype=np.float32,
    )
    vec_irrelevant = np.array(
        get_embedding("Cafeteria serves lunch between 12 PM and 2 PM daily."),
        dtype=np.float32,
    )

    sim_match = np.dot(vec_q, vec_match) / (
        np.linalg.norm(vec_q) * np.linalg.norm(vec_match)
    )
    sim_irrelevant = np.dot(vec_q, vec_irrelevant) / (
        np.linalg.norm(vec_q) * np.linalg.norm(vec_irrelevant)
    )

    assert sim_match > sim_irrelevant
