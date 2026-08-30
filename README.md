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

This project makes college policy, syllabus, and admin documents searchable and interactive for students and admins. Instead of guessing, the assistant retrieves evidence from uploaded documents, builds grounded answers with source citations, and avoids hallucination using similarity thresholds and guarded prompts. Perfect for universities, departments, or campus portals. 🎯

## 🌟 Key Features

- ✅ Retrieval-Augmented Generation (RAG) pipeline: extraction → cleaning → chunking → embeddings → vector search → grounded LLM responses
- 🔒 Anti-hallucination mechanisms: similarity thresholding + strict system prompts
- 👥 Role-based UI: Student chat + Admin dashboard (upload/manage docs)
- 📄 Multi-format document support: PDF, DOCX, TXT
- 💾 Persistent metadata + vector store (SQLite + ChromaDB)
- ⚙️ Simple vanilla-HTML frontend (deployable on Vercel) and FastAPI backend (deployable on Render)

---

## 📊 High-level Architecture (visual)

User interacts with frontend → Frontend calls backend (FastAPI) → Backend coordinates RAG pipeline and data stores

Simple flow:

```
Student/Admin (browser)  🖱️
        │
        ▼
Frontend (Vercel)  ───► Backend API (Render)  ──► RAG Pipeline
                        (FastAPI / uvicorn)           │
                                                   ▼
                                     ┌──────────────┬──────────────┐
                                     │ SQLite (metadata)        │
                                     │ ChromaDB (vectors)       │
                                     └──────────────┴──────────────┘
```

More detailed step-by-step flow for a student question:

1. Student types a question in the chat UI.
2. Frontend sends POST /api/chat/query to backend.
3. Backend generates an embedding for the query (Gemini / fallback).
4. Backend performs vector search in ChromaDB (Top-K, default 4).
5. If highest similarity >= threshold (default ~0.30) → retrieve chunks and build context; else return "out of scope" message.
6. Backend calls LLM (Gemini / fallback) with system prompt + retrieved chunks to generate grounded answer.
7. Backend returns answer + source citations to frontend; frontend shows clickable source badges.

---

## 🧭 Admin upload & processing (visual)

```
Admin uploads document (PDF/DOCX/TXT)
          │
          ▼
Document extraction (PyMuPDF / python-docx / plain)
          │
          ▼
Text cleaner → Chunker (size ~500, overlap ~100)
          │
          ▼
Embeddings (Gemini API or fallback) → Store vectors in ChromaDB + metadata in SQLite
          │
          ▼
Ready for queries ✅
```

---

## 📁 Project structure (concise)

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

Note: The frontend is a simple single-page app (vanilla JS) under `static/` and `templates/` and can be hosted on Vercel. The backend is FastAPI (main.py) and can be hosted on Render / other Python hosts.

---

## 🔧 Quick start (local)

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
- DATABASE_URL (if changed)
- SECRET_KEY / JWT settings

3. Run backend (development)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. Serve frontend (open templates/index.html or configure static hosting)

Open http://127.0.0.1:8000 in your browser or serve static folder with any static host.

---

## 🧪 Tests

Run tests:

```bash
python -m pytest tests/ -v
```

---

## 🔌 API (high-level)

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

## 📦 Deployment notes

You've deployed this repo with a split deployment (frontend + backend):

- Frontend: Vercel (static SPA) — https://rag-based-college-chatbot-two.vercel.app
- Backend: Render (FastAPI) — https://rag-based-college-chatbot-93ga.onrender.com

Tips:
- Ensure the frontend's API base URL points to the Render backend. Look for `API_BASE_URL` or similar in `static/js/app.js` or environment configs.
- For production, store secrets in Vercel & Render environment settings (do not commit `.env` with secrets).

---

## ✅ Interviewer-ready summary (elevator + architecture)

Quick talking points:

- "This project is a RAG-based assistant for college docs. It ingests PDFs/DOCX/TXT, chunks & embeds them, and uses vector similarity to retrieve evidence before asking an LLM to answer — preventing hallucinations."
- "Frontend is a lightweight SPA (HTML/CSS/Vanilla JS) deployed on Vercel; backend is FastAPI on Render. We separate concerns: UI, API, RAG pipeline, and vector store."
- "Key safety: similarity thresholding (default 0.30) and system prompts ensure the model only answers when we have evidence."

Bring these bullets and the flow chart above to interviews — they're concise and demonstrate end-to-end design thinking. ✨

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
