import requests  # type: ignore
from sqlalchemy.orm import Session
from config import settings
from rag.retriever import retrieve_relevant_chunks
from rag.prompt import build_rag_prompt
from typing import Optional


from rag.embeddings import _get_cached_genai_client
import time


def _call_gemini_llm(prompt: str) -> Optional[str]:
    """Attempts to generate content using Google Gemini API."""
    if not settings.GEMINI_API_KEY:
        return None

    # De-duplicate models and filter out non-existent model names
    primary_model = settings.LLM_MODEL
    if "3.6" in primary_model or not primary_model:
        primary_model = "gemini-2.5-flash"

    models_to_try = [primary_model]
    if "gemini-2.5-flash" not in models_to_try:
        models_to_try.append("gemini-2.5-flash")
    if "gemini-1.5-flash" not in models_to_try:
        models_to_try.append("gemini-1.5-flash")

    try:
        client = _get_cached_genai_client(settings.GEMINI_API_KEY)
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name, contents=prompt
                )
                if hasattr(response, "text") and response.text:
                    return response.text.strip()
            except Exception as e:
                print(f"Gemini genai LLM error ({model_name}): {e}")
    except Exception as e:
                print(f"Gemini genai client init error: {e}")

    return None


def _call_grok_llm(prompt: str) -> Optional[str]:
    """Attempts to generate content using xAI Grok API as a fallback."""
    if not settings.GROK_API_KEY:
        return None

    try:
        url = f"{settings.GROK_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROK_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.GROK_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "").strip()
        else:
            print(f"Grok API HTTP error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Grok LLM generation error: {e}")

    return None


def run_rag_pipeline(
    question: str, db: Session, chat_history: Optional[list[dict]] = None
) -> dict:
    """
    Executes complete mandatory RAG pipeline with high-precision timing breakdown:
    Question -> Query Embedding -> Vector Similarity Search -> Relevant Chunks -> Threshold Filter -> Grounded LLM Prompt -> Answer + Sources
    """
    t_start = time.perf_counter()

    # 1. Retrieve relevant document chunks
    t_ret_start = time.perf_counter()
    retrieved_chunks = retrieve_relevant_chunks(question, db)
    t_ret_end = time.perf_counter()

    # 2. Check if relevant context is available
    if not retrieved_chunks:
        t_total = (time.perf_counter() - t_start) * 1000
        print(f"[RAG Perf] Retrieval: {(t_ret_end - t_ret_start)*1000:.2f}ms | Total: {t_total:.2f}ms (No context found)")
        return {
            "answer": "I couldn't find this information in the college knowledge base. Please contact the appropriate college department or administrator for official updates.",
            "sources": [],
        }

    # 3. Format source references
    sources = []
    seen_sources = set()
    for chunk in retrieved_chunks:
        meta = chunk.get("metadata", {})
        doc_name = meta.get("document_name", "Official Document")
        page = meta.get("page", 1)
        section = meta.get("section", "General")

        source_key = f"{doc_name}_p{page}_{section}"
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            sources.append(
                {
                    "document_name": doc_name,
                    "page": page,
                    "section": section,
                    "snippet": chunk.get("text", "")[:150] + "...",
                }
            )

    # 4. Build strict grounded RAG prompt
    t_prompt_start = time.perf_counter()
    prompt = build_rag_prompt(question, retrieved_chunks, chat_history)
    t_prompt_end = time.perf_counter()

    # 5. Call LLM with fallback mechanism (Gemini -> Grok -> Offline)
    t_llm_start = time.perf_counter()
    answer_text = _call_gemini_llm(prompt)
    if not answer_text and settings.GROK_API_KEY:
        print("Gemini unavailable/rate-limited. Triggering Grok API fallback...")
        answer_text = _call_grok_llm(prompt)

    # 6. Fallback to local extractor if all external LLM APIs fail or are unconfigured
    if not answer_text:
        answer_text = _generate_offline_grounded_answer(question, retrieved_chunks)
    t_llm_end = time.perf_counter()

    t_total = (time.perf_counter() - t_start) * 1000
    ret_ms = (t_ret_end - t_ret_start) * 1000
    prompt_ms = (t_prompt_end - t_prompt_start) * 1000
    llm_ms = (t_llm_end - t_llm_start) * 1000

    print(
        f"[RAG Perf] Retrieval: {ret_ms:.2f}ms | Prompt: {prompt_ms:.2f}ms | LLM: {llm_ms:.2f}ms | Total RAG: {t_total:.2f}ms"
    )

    if answer_text and "couldn't find this information in the college knowledge base" in answer_text.lower():
        return {"answer": answer_text, "sources": []}

    return {"answer": answer_text, "sources": sources}


def _generate_offline_grounded_answer(
    question: str, retrieved_chunks: list[dict]
) -> str:
    """
    Offline fallback grounded response generator when external LLM API key is not present.
    Extracts sentences matching the student's query from top retrieved chunks.
    """
    top_chunk = retrieved_chunks[0]
    doc_name = top_chunk.get("metadata", {}).get("document_name", "college document")
    text = top_chunk.get("text", "")

    return f"According to {doc_name}:\n\n{text}"
