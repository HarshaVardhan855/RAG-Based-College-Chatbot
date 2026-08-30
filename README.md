# 🎓 RAG-Based College Chatbot

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-green)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**An AI-powered college information assistant using Retrieval-Augmented Generation (RAG) to answer student queries from official college documents — grounded, source-cited, and safe.**

</div>

---

🚀 Live Demo

- Frontend (Vercel): https://rag-based-college-chatbot-two.vercel.app
- Backend (Render): https://rag-based-college-chatbot-93ga.onrender.com

(If you see different behavior, the frontend may point to a different backend URL — check `static/js/app.js` and `vercel.json`.)

---

## Elevator pitch

This project makes college policy, syllabus, and admin documents searchable and interactive for students and admins. Instead of guessing, the assistant retrieves evidence from uploaded documents, [...]

## 🌟 Key Features

- ✅ Retrieval-Augmented Generation (RAG) pipeline: extraction → cleaning → chunking → embeddings → vector search → grounded LLM responses
- 🔒 Anti-hallucination mechanisms: similarity thresholding + strict system prompts
- 👥 Role-based UI: Student chat + Admin dashboard (upload/manage docs)
- 📄 Multi-format document support: PDF, DOCX, TXT
- 💾 Persistent metadata + vector store (SQLite + ChromaDB)
- ⚙️ Simple vanilla-HTML frontend (deployable on Vercel) and FastAPI backend (deployable on Render)

---

## 📊 High-level Architecture

### System Overview

```
┌────────────────────────────────────────────────────────────────�[...]
│                     RAG-Based College Chatbot                   │
├────────────────────────────────────────────────────────────────�[...]
│                                                                   │
│  🖥️  PRESENTATION LAYER                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Student/Admin Browser Interface (HTML/CSS/JS)          │   │
│  │  - Student Chat UI                                       │   │
│  │  - Admin Document Management Dashboard                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                    │
│                             │ API Calls (HTTP/REST)             │
│                             ▼                                    │
│                                                                   │
│  🔗  API & ORCHESTRATION LAYER (Render)                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastAPI Backend (uvicorn)                               │   │
│  │  - Authentication (JWT)                                  │
│  │  - Document Management                                   │
│  │  - Chat Query Handler                                    │
│  │  - RAG Pipeline Orchestration                            │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                    │
│          ┌──────────────────┼──────────────────┐                │
│          │                  │                  │                │
│          ▼                  ▼                  ▼                │
│                                                                   │
│  🧠  RAG INTELLIGENCE LAYER                                      │
│  ┌──────────┬────────────────┬──────────────────────────────┐   │
│  │ Chunker  │  Embeddings    │  LLM Reasoning              │   │
│  │          │  (Gemini/      │  (Gemini/Fallback)          │   │
│  │ • Split  │   Fallback)    │                              │   │
│  │ • Clean  │                │  • Prompt Engineering       │   │
│  │ • Chunk  │                │  • Context Assembly         │   │
│  │          │                │  • Source Citation          │   │
│  └──────────┴────────────────┴──────────────────────────────┘   │
│          │                  │                  │                │
│          └──────────────────┼──────────────────┘                │
│                             ▼                                    │
│                                                                   │
│  💾 DATA & STORAGE LAYER                                         │
│  ┌────────────────────────┬────────────────────────────────┐   │
│  │  SQLite Database       │  ChromaDB Vector Store        │   │
│  │  ────────────────────  │  ──────────────────────────    │   │
│  │  • User Accounts       │  • Document Embeddings        │   │
│  │  • Document Metadata   │  • Semantic Search Index      │   │
│  │  • Chat History        │  • Similarity Scoring         │   │
│  │  • Access Control      │                               │   │
│  └────────────────────────┴────────────────────────────────┘   │
│                                                                   │
└────────────────────────────────────────────────────────────────�[...]
```

### Student Query Flow (Step-by-Step)

```
STEP 1: User Input
   Student types a question in chat UI
                │
                ▼
STEP 2: Frontend Request
   POST /api/chat/query → Send question to backend
                │
                ▼
STEP 3: Query Embedding
   Backend converts question to embeddings (Gemini API / fallback)
                │
                ▼
STEP 4: Vector Search
   ChromaDB searches embeddings (Top-K results, K=4 by default)
                │
                ▼
STEP 5: Similarity Check
   ┌─ If similarity score ≥ 0.30 (threshold)  →  PROCEED
   │
   └─ If similarity score < 0.30               →  Return "Out of scope" message
                │
                ▼
STEP 6: Context Building
   Retrieve matching document chunks + metadata
                │
                ▼
STEP 7: LLM Generation
   Call Gemini API with:
   • System prompt (strict grounding rules)
   • User question
   • Retrieved chunks (context)
                │
                ▼
STEP 8: Response with Sources
   Backend returns:
   • Grounded answer
   • Source citations (clickable badges)
   • Metadata (document ID, chunk reference)
                │
                ▼
STEP 9: Frontend Display
   Show answer + interactive source links in chat UI
```

### Admin Upload & Document Processing Flow

```
STEP 1: Document Upload
   Admin uploads file (PDF / DOCX / TXT) via dashboard
                │
                ▼
STEP 2: File Type Detection
   Backend identifies format and routes to appropriate parser
                │
   ┌───────────┼───────────┐
   │           │           │
   ▼           ▼           ▼
  PDF       DOCX         TXT
 (PyMuPDF)  (python-      (plain
           docx)        read)
   │           │           │
   └───────────┼───────────┘
               ▼
STEP 3: Text Extraction
   Extract raw text from document
               │
               ▼
STEP 4: Text Cleaning
   • Remove extra whitespace
   • Fix encoding issues
   • Remove metadata
               │
               ▼
STEP 5: Chunking
   Split into overlapping chunks (~500 tokens, ~100 token overlap)
               │
               ▼
STEP 6: Generate Embeddings
   Convert chunks to vector embeddings (Gemini / fallback)
               │
               ▼
STEP 7: Store Results
   ├─ ChromaDB: Save vectors + chunk text
   └─ SQLite: Save metadata (doc_id, filename, upload_date, etc.)
               │
               ▼
STEP 8: Index Complete ✅
   Document ready for semantic queries
```

---

## 📁 Project Structure (Concise)

```
RAG-Based-College-Chatbot/
├── main.py                # FastAPI app
├── config.py              # env & settings
├── requirements.txt
├── static/                # Frontend (HTML, CSS, JS) — deployed to Vercel
├── templates/             # index.html SPA
├── rag/                   # RAG pipeline: chunker, embeddings, retriever, prompt
├── documents/             # file processors (pdf/docx/txt)
├── services/              # domain logic (user, document, chat)
├── database/              # SQLite models & repo
├── auth/                  # JWT & role access
└── tests/                 # pytest suites
```

Note: The frontend is a simple single-page app (vanilla JS) under `static/` and `templates/` and can be hosted on Vercel. The backend is FastAPI (main.py) and can be hosted on Render / other Pyth[...]

---

## 🔧 Quick Start (Local)

Prereqs: Python 3.11+, pip

1. Clone & install

```bash
git clone https://github.com/HarshaVardhan855/RAG-Based-College-Chatbot.git
cd RAG-Based-College-Chatbot
pip install -r requirements.txt
```

2. Configure environment

```bash
cp .env.example .env
# Edit .env (GEMINI_API_KEY if available)
```

Required / common env vars (see `.env.example`):
- GEMINI_API_KEY (optional)
- GROK_API_KEY (optional, used as fallback when Gemini rate limits or fails)
- DATABASE_URL (if changed)
- SECRET_KEY / JWT settings

3. Run backend (development)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. Serve frontend (open templates/index.html or configure static hosting)

Open http://127.0.0.1:8000 in your browser or serve static folder with any static host.

---

## Fallback model behavior (Gemini → Grok)

This project implements a model-provider fallback mechanism: Gemini is the primary model provider, and when a Gemini request returns a rate-limit (or other unrecoverable) error, the backend automatically attempts the same request against Grok using the GROK_API_KEY.

Why this is documented
- So maintainers know which providers are used and in what order.
- So operators can provide the correct API keys and understand cost/rate implications.
- So developers can test and customize the fallback behavior.

Configuration
- Environment variables (examples used by this project):
  - GEMINI_API_KEY — primary provider key (optional)
  - GROK_API_KEY — fallback provider key (optional)
  - DISABLE_FALLBACK — set to `true` to disable automatic fallback (if supported by your deployment/config)

Runtime behavior (high-level)
- Attempt request to Gemini.
- If the call succeeds, return Gemini's response.
- If the call fails with a rate-limit or unrecoverable error, log a warning and call Grok.
- If Grok also fails, return a friendly error to the user and log the failure for debugging.

Example pseudocode (conceptual)
```python
def generate_answer(prompt):
    try:
        return call_gemini(prompt)
    except RateLimitError:
        logger.warning("Gemini rate limit reached; falling back to Grok")
        try:
            return call_grok(prompt)
        except Exception:
            logger.error("Both Gemini and Grok failed", exc_info=True)
            raise RuntimeError("All model providers failed; try again later")
```

Notes and recommendations
- Secure your API keys (do not commit them). Use a secrets manager or environment variables.
- Monitor usage and set alerts for approaching rate limits or unexpected failures.
- Consider exponential backoff and retries for transient errors before falling back.
- Be explicit about costs and privacy: document that queries may be sent to third-party APIs (Gemini, Grok) and include any relevant privacy/cost warnings.

Testing
- To test fallback, temporarily invalidate or revoke the Gemini key and confirm the app uses Grok.
- Check logs for the fallback warning and verify the final response source.

---

## 🧪 Tests

Run tests:

```bash
python -m pytest tests/ -v
```

---

## 🔌 API (High-level)

- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- POST /api/chat/query
- GET /api/chat/history
- POST /api/documents/upload
- GET /api/documents/list
- DELETE /api/documents/{doc_id}

Refer to code in `services/` and `main.py` for implementation details.

---

## 📦 Deployment Notes

You've deployed this repo with a split deployment (frontend + backend):

- Frontend: Vercel (static SPA) — https://rag-based-college-chatbot-two.vercel.app
- Backend: Render (FastAPI) — https://rag-based-college-chatbot-93ga.onrender.com

Tips:
- Ensure the frontend's API base URL points to the Render backend. Look for `API_BASE_URL` or similar in `static/js/app.js` or environment configs.
- For production, store secrets in Vercel & Render environment settings (do not commit `.env` with secrets).

---

## ✅ Interviewer-Ready Summary (Elevator + Architecture)

Quick talking points:

- "This project is a RAG-based assistant for college docs. It ingests PDFs/DOCX/TXT, chunks & embeds them, and uses vector similarity to retrieve evidence before asking an LLM to answer — preve[...]
- "Frontend is a lightweight SPA (HTML/CSS/Vanilla JS) deployed on Vercel; backend is FastAPI on Render. We separate concerns: UI, API, RAG pipeline, and vector store."
- "Key safety: similarity thresholding (default 0.30) and system prompts ensure the model only answers when we have evidence."

Bring these diagrams and talking points to interviews — they demonstrate end-to-end design thinking. ✨

---

## 🤝 Contributing

1. Fork
2. Create feature branch
3. Commit & PR

See tests & run them locally. For major changes, open an issue first to discuss.

---

## 📝 License

MIT — see LICENSE

---

## 👤 Author

**Harsha Vardhan** — https://github.com/HarshaVardhan855

---

Made with ❤️ & careful grounding for educational institutions.
