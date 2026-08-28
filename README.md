# RAG-Based College Chatbot

Production-quality, full-stack **RAG-Based College Chatbot** designed to answer student questions strictly using official college documents uploaded by administrators.

Built strictly according to specifications in [`spec.md-file`](file:///c:/Users/Harsha%20Vardhan/RAG-BOT/spec.md-file).

---

## Key Features

- **Genuine RAG Architecture**: Document Extraction → Cleaning → Recursive Chunking → Vector Embeddings → Similarity Search → Grounded LLM Answer + Sources.
- **Zero Hallucination Guard**: Strict system prompt and similarity threshold filtering. Out-of-scope questions return explicit: *"I couldn't find this information in the college knowledge base."*
- **Role-Based System**:
  - **Student View**: Interactive chat UI with conversation history, sample questions, and clickable source reference badges (Document Name, Page, Section).
  - **Admin Dashboard**: Document upload (PDF, DOCX, TXT), searchable document table, re-processing, cascading deletion, and knowledge base analytics.
- **Technology Stack**:
  - **Backend**: Python 3.11, FastAPI, Uvicorn, Pydantic, SQLAlchemy
  - **Database & Vectors**: SQLite (application data) + ChromaDB / Cosine Similarity Vector Index
  - **Embeddings & LLM**: Google Gemini API (`text-embedding-004` & `gemini-2.0-flash`) via `google.genai` SDK with offline fallback
  - **Document Processors**: PyMuPDF (`fitz`), `python-docx`, plain text processor
  - **Frontend**: Modern glassmorphism UI with dark/light themes, responsive layout, and async REST API integration.

---

## Directory Structure

```
college-rag-chatbot/
├── config.py                 # App configuration & settings
├── main.py                   # FastAPI server & route handlers
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── README.md                 # Project documentation
│
├── auth/
│   ├── authentication.py     # Password hashing & JWT token issuing
│   └── authorization.py      # Dependency guards for Student & Admin roles
│
├── database/
│   ├── connection.py         # SQLite engine & session management
│   ├── models.py             # User, Document, Chunk, ChatSession, ChatMessage ORM models
│   └── repository.py         # Database CRUD queries
│
├── documents/
│   ├── pdf_processor.py      # PDF text & page extraction (PyMuPDF)
│   ├── docx_processor.py     # DOCX paragraph extraction (python-docx)
│   └── txt_processor.py      # Plain text file processor
│
├── rag/
│   ├── text_cleaner.py       # Whitespace & newline normalization
│   ├── chunker.py            # Recursive character chunking preserving metadata
│   ├── embeddings.py         # Gemini text-embedding-004 service with fallback
│   ├── vector_store.py       # ChromaDB vector store & similarity search
│   ├── retriever.py          # Top-K relevance retrieval & threshold filtering
│   ├── prompt.py             # Strict anti-hallucination grounded system prompt
│   └── pipeline.py           # End-to-end RAG workflow orchestrator
│
├── services/
│   ├── user_service.py       # User auth & admin seeding
│   ├── document_service.py   # Upload, chunking, vector storage, delete, reprocess
│   └── chat_service.py       # Chat sessions, query execution, & sources formatting
│
├── static/
│   ├── css/style.css         # Glassmorphism dark/light visual design system
│   └── js/
│       ├── app.js            # Auth state, theme, view switcher
│       ├── chat.js           # Student chat UI controller
│       └── admin.js          # Admin dashboard controller
│
├── templates/
│   └── index.html            # Main single-page web app template
│
└── tests/
    ├── test_auth.py          # Unit tests for JWT & password hashing
    ├── test_chunking.py      # Unit tests for chunking & metadata
    ├── test_retrieval.py     # Unit tests for vector search
    └── test_rag.py            # End-to-end RAG test suite
```

---

## Local Setup & Installation

### 1. Clone repository & Install dependencies
```bash
cd RAG-BOT
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
(Optional) Set your `GEMINI_API_KEY` in `.env` to connect to Google Gemini API:
```env
GEMINI_API_KEY="your-google-gemini-api-key"
```
*Note: If no API key is provided, the application automatically uses local vector embeddings and deterministic fallback response generation for offline testing.*

### 3. Default Admin Credentials
When launching the application for the first time, default administrator credentials are automatically initialized:
- **Email**: `admin@college.edu`
- **Password**: `Admin@123`

---

## Running the Application

Start the FastAPI server using Uvicorn:

```bash
python main.py
```
or
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open your browser and navigate to:
**`http://127.0.0.1:8000`**

---

## Running Automated Tests

Run the complete test suite including the mandatory RAG end-to-end known/unknown question verification:

```bash
python -m pytest tests/ -v
```

---

## RAG End-to-End Verification Process

1. **Log in as Administrator** (`admin@college.edu` / `Admin@123`).
2. Upload a college document (e.g. PDF/DOCX/TXT notice).
3. Switch to **Student Chat** view.
4. Ask a question regarding the uploaded document -> Receive exact grounded answer with source citations.
5. Ask an out-of-scope question (e.g. *"What is the 2030 international policy?"*) -> Receive refusal: *"I couldn't find this information in the college knowledge base."*
6. Delete the document from the Admin Dashboard -> Ask the question again -> System refrains from answering as information is no longer available.
