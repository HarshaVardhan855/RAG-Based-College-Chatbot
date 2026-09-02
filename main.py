import os
from fastapi import FastAPI, Depends, UploadFile, File, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from config import settings
from database.connection import engine, Base, get_db
from database.repository import Repository
from auth.authorization import get_current_user, require_admin, require_student
from services.user_service import UserService
from services.document_service import DocumentService
from services.chat_service import ChatService

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

# Seed Admin User
db_gen = get_db()
db_session = next(db_gen)
try:
    UserService.seed_admin_if_needed(db_session)
finally:
    db_session.close()

app = FastAPI(
    title=settings.APP_NAME,
    description="Full-stack RAG-Based College Information Chatbot",
    version="1.0.0",
)

# Enable CORS
parsed_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
is_wildcard = "*" in parsed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=parsed_origins if parsed_origins else ["*"],
    allow_credentials=not is_wildcard,  # Spec compliant: cannot allow_credentials with wildcard '*'
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static & Templates setup
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Pydantic Request Schemas
class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    # NOTE: role is intentionally excluded from public registration.
    # All self-registrations are forced to STUDENT by UserService.register_user.


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class ChatMessageRequest(BaseModel):
    question: str


class ChatSessionCreateRequest(BaseModel):
    title: str = "New Conversation"


# ================= HEALTH CHECK =================
@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


# ================= AUTH ENDPOINTS =================
@app.post("/api/auth/register")
def register(user_data: RegisterSchema, db: Session = Depends(get_db)):
    user = UserService.register_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        # role intentionally not passed — always STUDENT for self-registration
    )
    return {
        "message": "User registered successfully",
        "user": {"id": user.id, "email": user.email, "role": user.role},
    }


@app.post("/api/auth/login")
def login(credentials: LoginSchema, db: Session = Depends(get_db)):
    return UserService.authenticate_user(db, credentials.email, credentials.password)


@app.get("/api/auth/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
    }


# ================= ADMIN DOCUMENT MANAGEMENT ENDPOINTS =================
@app.post("/api/admin/documents")
def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    department: str = Form("General"),
    category: str = Form("General"),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    doc = DocumentService.process_and_store_document(
        db=db,
        file=file,
        title=title,
        department=department,
        category=category,
        admin_id=admin.id,
    )
    return {
        "message": "Document uploaded and processed successfully",
        "document_id": doc.id,
        "title": doc.title,
    }


@app.get("/api/admin/documents")
def list_documents(admin=Depends(require_admin), db: Session = Depends(get_db)):
    return DocumentService.get_all_documents(db)


@app.delete("/api/admin/documents/{doc_id}")
def delete_document(
    doc_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)
):
    return DocumentService.delete_document(db, doc_id)


@app.post("/api/admin/documents/{doc_id}/reprocess")
def reprocess_document(
    doc_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)
):
    return DocumentService.reprocess_document(db, doc_id)


@app.get("/api/admin/stats")
def get_admin_stats(admin=Depends(require_admin), db: Session = Depends(get_db)):
    return Repository.get_kb_stats(db)


@app.get("/api/admin/analytics")
def get_admin_analytics(admin=Depends(require_admin), db: Session = Depends(get_db)):
    """Extended analytics: students, active users, sessions, trends, top questions, recent activity."""
    return Repository.get_analytics_stats(db)


@app.get("/api/admin/queries")
def get_student_queries(
    limit: int = 50, admin=Depends(require_admin), db: Session = Depends(get_db)
):
    """Admin-only: view all student questions with answers and sources."""
    return Repository.get_all_student_queries(db, limit=limit)


# ================= STUDENT CHAT ENDPOINTS =================
@app.get("/api/chat/sessions")
def get_sessions(current_user=Depends(require_student), db: Session = Depends(get_db)):
    return ChatService.get_user_sessions(db, current_user.id)


@app.post("/api/chat/sessions")
def create_session(
    req: ChatSessionCreateRequest,
    current_user=Depends(require_student),
    db: Session = Depends(get_db),
):
    return ChatService.create_session(db, current_user.id, req.title)


@app.get("/api/chat/sessions/{session_id}/messages")
def get_session_messages(
    session_id: int,
    current_user=Depends(require_student),
    db: Session = Depends(get_db),
):
    return ChatService.get_session_messages(db, session_id, current_user.id)


@app.post("/api/chat/sessions/{session_id}/messages")
def send_chat_message(
    session_id: int,
    req: ChatMessageRequest,
    current_user=Depends(require_student),
    db: Session = Depends(get_db),
):
    return ChatService.process_chat_message(
        db, session_id, current_user.id, req.question
    )


@app.delete("/api/chat/sessions/{session_id}")
def delete_session(
    session_id: int,
    current_user=Depends(require_student),
    db: Session = Depends(get_db),
):
    return ChatService.delete_session(db, session_id, current_user.id)


# ================= MAIN UI ROUTE =================
@app.get("/")
def serve_index(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "app_name": settings.APP_NAME}
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
