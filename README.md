# 🎓 RAG-Based College Chatbot

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-green)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**An AI-powered college information assistant that uses Retrieval-Augmented Generation (RAG) to provide accurate, source-backed answers from official college documents.**

[Features](#-features) • [Architecture](#-architecture) • [Setup](#-setup) • [Usage](#-usage) • [API](#-api)

</div>

---

## 🌟 Features

- ✅ **Genuine RAG Architecture**: Document extraction → cleaning → semantic chunking → vector embeddings → similarity search → grounded LLM responses
- 🔒 **Zero Hallucination Guard**: Strict system prompts and similarity threshold filtering prevent false answers
- 👥 **Dual Role System**:
  - 🎓 **Student Interface**: Chat with AI, view conversation history, click source citations
  - 👨‍💼 **Admin Dashboard**: Upload documents, manage knowledge base, analytics & insights
- 🤖 **Intelligent Retrieval**: Google Gemini embeddings with Grok fallback
- 📄 **Multi-Format Support**: PDF, DOCX, TXT documents
- 🔐 **Authentication**: JWT-based auth with role-based access control
- 🌓 **Dark/Light Theme**: Modern glassmorphism UI
- 💾 **Persistent Storage**: SQLite + ChromaDB vector database

---

## 📐 System Architecture

### **High-Level System Overview**

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERFACE LAYER                       │
│  ┌──────────────────┐                    ┌──────────────────┐   │
│  │  Student Chat UI │                    │ Admin Dashboard  │   │
│  │  - Ask Questions │                    │ - Upload Docs    │   │
│  │  - View History  │                    │ - Manage Docs    │   │
│  │  - Click Sources │                    │ - View Analytics │   │
│  └────────┬─────────┘                    └────────┬─────────┘   │
└───────────┼────────────────────────────────────────┼─────────────┘
            │                                        │
            │         REST API (FastAPI)            │
            │                                        │
┌───────────┼────────────────────────────────────────┼─────────────┐
│           │           APPLICATION LAYER           │             │
│  ┌────────▼──────────┐                  ┌─────────▼──────────┐  │
│  │ Chat Service      │                  │ Document Service   │  │
│  │ - Query Handling  │                  │ - File Upload      │  │
│  │ - Response Format │                  │ - Processing       │  │
│  └────────┬──────────┘                  │ - Deletion         │  │
│           │                             └─────────┬──────────┘  │
│  ┌────────▼──────────────────────────────────────▼──────────┐   │
│  │              RAG PIPELINE LAYER                          │   │
│  │  ┌─────────────┐  ┌──────────┐  ┌─────────────────────┐ │   │
│  │  │ Text Cleaner│→ │ Chunker  │→ │ Embeddings Service  │ │   │
│  │  └─────────────┘  └──────────┘  └─────────────────────┘ │   │
│  │           ↓                                   ↓          │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │ Retriever: Vector Search + Similarity Filtering     │ │   │
│  │  └──────────────────────────┬────────────────────────── ┘ │   │
│  │                             ↓                            │   │
│  │  ┌──────────────────────────────────────────────────────┐ │   │
│  │  │ LLM Prompt Engine (Anti-Hallucination Grounding)     │ │   │
│  │  └──────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Authentication & Authorization Layer (JWT + Roles)     │    │
│  └─────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────┘
            │                                        │
            │      DATABASE & VECTOR STORE          │
            │                                        │
┌───────────┼────────────────────────────────────────┼─────────────┐
│           │                                        │             │
│  ┌────────▼──────────────┐        ┌───────────────▼──────────┐  │
│  │ SQLite Database       │        │ ChromaDB Vector Store    │  │
│  │ - User accounts       │        │ - Document embeddings    │  │
│  │ - Documents metadata  │        │ - Chunk vectors          │  │
│  │ - Chat history        │        │ - Similarity indexing    │  │
│  └───────────────────────┘        └──────────────────────────┘  │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 🔄 User Journey & Workflow

### **Admin Upload & Processing Flow**

```
┌─────────────────────────────────────────────────────────────────┐
│                    ADMIN UPLOADS DOCUMENT                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Document Validation │
                    │ (Format check)      │
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
            ┌────────┐    ┌────────┐    ┌────────┐
            │  PDF   │    │ DOCX   │    │  TXT   │
            │Extract │    │Extract │    │Extract │
            └───┬────┘    └───┬────┘    └───┬────┘
                │              │              │
                └──────────────┼──────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Text Cleaning      │
                    │ - Remove extra      │
                    │   whitespace        │
                    │ - Normalize text    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Recursive Chunking  │
                    │ - Chunk Size: 500   │
                    │ - Overlap: 100      │
                    │ - Preserve metadata │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Generate Embeddings│
                    │  Gemini API         │
                    │  (w/ Fallback)      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Store in ChromaDB   │
                    │ Vector Index        │
                    │ + SQLite Metadata   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ ✅ Ready for Queries│
                    └─────────────────────┘
```

### **Student Query & Response Flow**

```
┌─────────────────────────────────────────────────────────────────┐
│              STUDENT TYPES QUESTION IN CHAT                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ 1. Generate Query   │
                    │    Embedding        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ 2. Vector Search    │
                    │    ChromaDB         │
                    │    (Top-K: 4 docs)  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ 3. Similarity Check │
                    │ Threshold: 0.30     │
                    └──────┬──────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     Score ≥ 0.30   Score < 0.30      │
            │              │              │
            ▼              ▼              │
      ┌──────────┐  ┌────────────┐       │
      │ Retrieve │  │ Return Out  │       │
      │ Relevant │  │ of Scope    │       │
      │ Chunks   │  │ Message:    │       │
      │with      │  │ "I couldn't │       │
      │sources   │  │ find..."    │       │
      └────┬─────┘  └────┬───────┘       │
           │             │               │
           └──────┬──────┘               │
                  │                      │
                  ▼                      │
     ┌─────────────────────┐             │
     │ Build Context for   │             │
     │ LLM Prompt:         │             │
     │ - System Prompt     │             │
     │ - Retrieved Chunks  │             │
     │ - User Question     │             │
     └──────────┬──────────┘             │
                │                        │
                ▼                        │
     ┌─────────────────────┐             │
     │ Call Gemini API     │             │
     │ Generate Response   │             │
     │ with grounding      │             │
     └──────────┬──────────┘             │
                │                        │
                └────────┬───────────────┘
                         │
                         ▼
                    ┌────────────────────┐
                    │ 4. Format Response │
                    │ + Source Citations │
                    │ (Doc, Page, Link)  │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │ 5. Send to Student │
                    │ Display with       │
                    │ clickable sources  │
                    └────────────────────┘
```

---

## 📁 Project Structure

```
RAG-Based-College-Chatbot/
│
├── 📄 main.py                          # FastAPI application entry point
├── 📄 config.py                        # Configuration & environment settings
├── 📄 requirements.txt                 # Python dependencies
├── 📄 .env.example                     # Environment variables template
├── 📄 .gitignore                       # Git ignore rules
├── 📄 README.md                        # This file
│
├── 🔐 auth/
│   ├── authentication.py               # Password hashing & JWT tokens
│   └── authorization.py                # Role-based access control
│
├── 💾 database/
│   ├── connection.py                   # SQLite session management
│   ├── models.py                       # ORM models (User, Document, Chat, etc.)
│   └── repository.py                   # Database CRUD operations
│
├── 📄 documents/
│   ├── pdf_processor.py                # PDF extraction using PyMuPDF
│   ├── docx_processor.py               # DOCX extraction using python-docx
│   └── txt_processor.py                # Plain text file processor
│
├── 🧠 rag/
│   ├── text_cleaner.py                 # Text normalization
│   ├── chunker.py                      # Recursive character chunking
│   ├── embeddings.py                   # Gemini embeddings service
│   ├── vector_store.py                 # ChromaDB integration
│   ├── retriever.py                    # Semantic search & filtering
│   ├── prompt.py                       # LLM system prompts
│   └── pipeline.py                     # Complete RAG orchestration
│
├── 🚀 services/
│   ├── user_service.py                 # User authentication & admin setup
│   ├── document_service.py             # Document upload & processing
│   └── chat_service.py                 # Chat sessions & queries
│
├── 🎨 static/
│   ├── css/
│   │   └── style.css                   # Glassmorphism UI design
│   └── js/
│       ├── app.js                      # Main app controller
│       ├── chat.js                     # Student chat interface
│       └── admin.js                    # Admin dashboard
│
├── 📋 templates/
│   └── index.html                      # Single-page application template
│
└── ✅ tests/
    ├── test_auth.py                    # Authentication tests
    ├── test_chunking.py                # Chunking logic tests
    ├── test_retrieval.py               # Vector search tests
    └── test_rag.py                     # End-to-end RAG tests
```

---

## 🚀 Quick Start

### **Prerequisites**
- Python 3.11+
- pip (Python package manager)
- Google Gemini API key (optional - has fallback)

### **1. Clone & Install**

```bash
git clone https://github.com/HarshaVardhan855/RAG-Based-College-Chatbot.git
cd RAG-Based-College-Chatbot
pip install -r requirements.txt
```

### **2. Configure Environment**

```bash
cp .env.example .env
```

Edit `.env` and add your Google Gemini API key (optional):
```env
GEMINI_API_KEY="your-api-key-here"
```

### **3. Run the Application**

```bash
python main.py
```

Or with Uvicorn directly:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### **4. Access the Application**

Open your browser and visit:
```
http://127.0.0.1:8000
```

### **5. Default Credentials**

- **Email**: `admin@college.edu`
- **Password**: `Admin@123`

---

## 📖 Usage Guide

### **For Admins: Upload Documents**

1. **Login** with admin credentials
2. **Navigate to Admin Dashboard**
3. **Click "Upload Document"**
4. **Select** PDF, DOCX, or TXT file
5. **Click "Process"** - system will:
   - Extract text from document
   - Clean and normalize content
   - Split into semantic chunks
   - Generate embeddings
   - Store in vector database
6. **View** document status and statistics

### **For Students: Ask Questions**

1. **Access Student Chat Interface**
2. **Type your question** about college information
3. **Press Enter** or click Send
4. **View AI Response** with:
   - Direct answer grounded in college documents
   - Source citations (Document name, page, section)
   - Conversation history
5. **Click Source Badges** to jump to specific document sections

### **System Behavior**

| Scenario | Behavior |
|----------|----------|
| **Question in Knowledge Base** | Returns grounded answer with source citations |
| **Question outside Scope** | Returns: *"I couldn't find this information in the college knowledge base."* |
| **After Document Deletion** | System stops answering questions related to deleted documents |

---

## 🔌 API Endpoints

### **Authentication**

```http
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
```

### **Chat Operations**

```http
POST /api/chat/query
GET /api/chat/history
POST /api/chat/session
```

### **Document Management (Admin Only)**

```http
POST /api/documents/upload
GET /api/documents/list
DELETE /api/documents/{doc_id}
POST /api/documents/reprocess/{doc_id}
```

### **Analytics (Admin Only)**

```http
GET /api/analytics/knowledge-base
GET /api/analytics/queries
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, Uvicorn, Python 3.11+ |
| **Database** | SQLite (application data) |
| **Vector Store** | ChromaDB |
| **Embeddings** | Google Gemini Embeddings |
| **LLM** | Google Gemini 2.0 Flash + Grok Fallback |
| **Document Processing** | PyMuPDF (PDF), python-docx (DOCX) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **UI/UX** | Glassmorphism, Dark/Light themes |

---

## 🧪 Testing

### **Run All Tests**

```bash
python -m pytest tests/ -v
```

### **Run Specific Test Suite**

```bash
# Authentication tests
python -m pytest tests/test_auth.py -v

# Chunking tests
python -m pytest tests/test_chunking.py -v

# Vector retrieval tests
python -m pytest tests/test_retrieval.py -v

# End-to-end RAG tests
python -m pytest tests/test_rag.py -v
```

### **Verify RAG End-to-End**

1. Log in as admin
2. Upload a test document
3. Ask a question that's in the document → verify grounded answer
4. Ask an out-of-scope question → verify rejection
5. Delete the document → ask the question again → verify no longer answerable

---

## 🔒 Security Features

- ✅ **JWT Authentication**: Secure token-based auth
- ✅ **Password Hashing**: Bcrypt password protection
- ✅ **Role-Based Access Control**: Student vs Admin permissions
- ✅ **Input Validation**: Pydantic models for all inputs
- ✅ **Anti-Hallucination**: Strict system prompts prevent false info
- ✅ **Similarity Threshold**: Only answers high-confidence queries

---

## 📊 Knowledge Base Analytics

Admins can view:
- 📈 Total documents uploaded
- 📄 Total chunks in knowledge base
- 🔍 Query statistics
- ⏱️ Processing times
- ❌ Failed processing attempts

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙋 Support & Questions

- **Report Issues**: [GitHub Issues](https://github.com/HarshaVardhan855/RAG-Based-College-Chatbot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/HarshaVardhan855/RAG-Based-College-Chatbot/discussions)

---

## 🎯 Roadmap

- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Document versioning
- [ ] Custom LLM model selection
- [ ] Export chat history as PDF
- [ ] Voice input/output support
- [ ] Mobile app
- [ ] Integration with college management systems

---

## 👤 Author

**Harsha Vardhan** - [GitHub Profile](https://github.com/HarshaVardhan855)

---

<div align="center">

**Made with ❤️ for educational institutions**

⭐ If you find this helpful, please consider giving it a star!

</div>
