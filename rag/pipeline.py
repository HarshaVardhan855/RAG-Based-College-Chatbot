import requests  # type: ignore
from sqlalchemy.orm import Session
from config import settings
from rag.retriever import retrieve_relevant_chunks
from rag.prompt import build_rag_prompt
from typing import Optional


def _call_gemini_llm(prompt: str) -> Optional[str]:
    """Attempts to generate content using Google Gemini API."""
    if not settings.GEMINI_API_KEY:
        return None

    models_to_try = [settings.LLM_MODEL, "gemini-2.5-flash"]
    try:
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
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
    Executes complete mandatory RAG pipeline:
    Question -> Query Embedding -> Vector Similarity Search -> Relevant Chunks -> Threshold Filter -> Grounded LLM Prompt -> Answer + Sources
    LLM Generation uses multi-tiered fallback: Gemini API -> Grok API -> Offline Extractor
    """
    # 1. Retrieve relevant document chunks
    retrieved_chunks = retrieve_relevant_chunks(question, db)

    # 2. Check if relevant context is available
    if not retrieved_chunks:
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
    prompt = build_rag_prompt(question, retrieved_chunks, chat_history)

    # 5. Call LLM with fallback mechanism (Gemini -> Grok -> Offline)
    answer_text = _call_gemini_llm(prompt)
    if not answer_text and settings.GROK_API_KEY:
        print("Gemini unavailable/rate-limited. Triggering Grok API fallback...")
        answer_text = _call_grok_llm(prompt)

    # 6. Fallback to local extractor if all external LLM APIs fail or are unconfigured
    if not answer_text:
        answer_text = _generate_offline_grounded_answer(question, retrieved_chunks)

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
