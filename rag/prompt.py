from typing import Optional


def build_rag_prompt(
    question: str,
    retrieved_chunks: list[dict],
    chat_history: Optional[list[dict]] = None,
) -> str:
    """
    Builds a strict anti-hallucination prompt separating System Instructions,
    Retrieved Context, Conversation History, and User Question.
    """

    system_instructions = """SYSTEM INSTRUCTIONS:
You are the official College Information Assistant.
Your primary role is to provide factual, accurate answers to student questions based STRICTLY on the official college documents provided in the RETRIEVED CONTEXT below.

CRITICAL RULES:
1. Answer the student's question using ONLY the factual information provided in the RETRIEVED CONTEXT.
2. DO NOT invent, assume, or extrapolate college policies, dates, deadlines, fee amounts, department details, hostel rules, course details, or examination schedules.
3. IF THE RETRIEVED CONTEXT IS EMPTY OR DOES NOT CONTAIN ENOUGH INFORMATION TO ANSWER THE QUESTION ACCURATELY, YOU MUST RESPOND EXACTLY WITH:
   "I couldn't find this information in the college knowledge base. Please contact the appropriate college department or administrator for official updates."
4. Do not pretend that unsupported information is official college policy.
5. Keep your answer clear, polite, and directly student-focused.
"""

    context_str = ""
    if retrieved_chunks:
        context_str = "RETRIEVED COLLEGE KNOWLEDGE BASE CONTEXT:\n"
        for idx, chunk in enumerate(retrieved_chunks, 1):
            meta = chunk.get("metadata", {})
            doc_name = meta.get("document_name", "Official Document")
            page = meta.get("page", 1)
            section = meta.get("section", "General")
            context_str += f"\n--- Context Document {idx}: {doc_name} (Page {page}, Section: {section}) ---\n"
            context_str += chunk.get("text", "").strip() + "\n"
    else:
        context_str = "RETRIEVED COLLEGE KNOWLEDGE BASE CONTEXT:\n[No relevant documents retrieved from the knowledge base]\n"

    history_str = ""
    if chat_history:
        history_str = "RECENT CONVERSATION HISTORY:\n"
        for msg in chat_history[-6:]:
            role = "Student" if msg.get("sender") == "user" else "AI Assistant"
            history_str += f"{role}: {msg.get('message')}\n"

    prompt = f"""{system_instructions}

{context_str}

{history_str}

STUDENT QUESTION:
{question}

FINAL ANSWER:"""

    return prompt
