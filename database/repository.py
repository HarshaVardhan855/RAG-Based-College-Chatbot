from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from database.models import User, Document, Chunk, ChatSession, ChatMessage, UserRole
import datetime
import json
from typing import Optional, List


class Repository:
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower()).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_user(
        db: Session, email: str, hashed_password: str, full_name: str, role: str
    ) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_document(
        db: Session,
        file_name: str,
        file_type: str,
        file_path: str,
        title: str,
        department: str,
        category: str,
        uploaded_by: int,
    ) -> Document:
        doc = Document(
            file_name=file_name,
            file_type=file_type,
            file_path=file_path,
            title=title,
            department=department,
            category=category,
            uploaded_by=uploaded_by,
            version=1,
            status="PROCESSED",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def get_document_by_id(db: Session, doc_id: int) -> Optional[Document]:
        return db.query(Document).filter(Document.id == doc_id).first()

    @staticmethod
    def get_all_documents(db: Session) -> List[Document]:
        return db.query(Document).order_by(Document.upload_date.desc()).all()

    @staticmethod
    def delete_document(db: Session, doc_id: int) -> bool:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            db.delete(doc)
            db.commit()
            return True
        return False

    @staticmethod
    def create_chunks(db: Session, document_id: int, chunks_data: list) -> list[Chunk]:
        db_chunks = []
        for idx, item in enumerate(chunks_data):
            c = Chunk(
                document_id=document_id,
                chunk_index=idx,
                chunk_text=item["text"],
                page_number=item.get("page"),
                section=item.get("section"),
            )
            db.add(c)
            db_chunks.append(c)
        db.commit()
        for c in db_chunks:
            db.refresh(c)
        return db_chunks

    @staticmethod
    def get_chunks_by_document(db: Session, document_id: int) -> List[Chunk]:
        return db.query(Chunk).filter(Chunk.document_id == document_id).all()

    @staticmethod
    def delete_chunks_by_document(db: Session, document_id: int):
        db.query(Chunk).filter(Chunk.document_id == document_id).delete()
        db.commit()

    @staticmethod
    def create_chat_session(
        db: Session, user_id: int, title: str = "New Conversation"
    ) -> ChatSession:
        session = ChatSession(user_id=user_id, title=title)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_chat_sessions(db: Session, user_id: int) -> List[ChatSession]:
        return (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .all()
        )

    @staticmethod
    def get_chat_session(
        db: Session, session_id: int, user_id: int
    ) -> Optional[ChatSession]:
        return (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .first()
        )

    @staticmethod
    def create_chat_message(
        db: Session,
        session_id: int,
        sender: str,
        message: str,
        sources: Optional[list] = None,
    ) -> ChatMessage:
        sources_json = json.dumps(sources) if sources is not None else None
        msg = ChatMessage(
            session_id=session_id,
            sender=sender,
            message=message,
            sources_json=sources_json,
        )
        db.add(msg)

        # update session timestamp
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            session.updated_at = datetime.datetime.utcnow()

        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def delete_chat_session(db: Session, session_id: int, user_id: int) -> bool:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .first()
        )
        if session:
            db.delete(session)
            db.commit()
            return True
        return False

    @staticmethod
    def get_kb_stats(db: Session) -> dict:
        """Basic KB stats (legacy endpoint — kept for compatibility)."""
        total_docs = db.query(Document).count()
        total_chunks = db.query(Chunk).count()
        total_chats = db.query(ChatMessage).filter(ChatMessage.sender == "user").count()
        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "total_questions": total_chats,
        }

    @staticmethod
    def get_analytics_stats(db: Session) -> dict:
        """
        Full analytics for Admin dashboard.
        All values computed from real DB data — never hard-coded.
        """
        # Core counts
        total_students = (
            db.query(User).filter(User.role == UserRole.STUDENT.value).count()
        )
        total_documents = db.query(Document).count()
        total_chunks = db.query(Chunk).count()
        total_sessions = db.query(ChatSession).count()
        total_questions = (
            db.query(ChatMessage).filter(ChatMessage.sender == "user").count()
        )

        # Students who have used the chatbot = UNIQUE students with at least one question
        active_students = (
            db.query(func.count(distinct(ChatSession.user_id)))
            .join(ChatMessage, ChatMessage.session_id == ChatSession.id)
            .filter(ChatMessage.sender == "user")
            .scalar() or 0
        )

        # Daily question counts for last 7 days
        today = datetime.datetime.utcnow().date()
        trends = []
        for i in range(6, -1, -1):  # 6 days ago ... today
            day = today - datetime.timedelta(days=i)
            day_start = datetime.datetime.combine(day, datetime.time.min)
            day_end = datetime.datetime.combine(day, datetime.time.max)
            count = (
                db.query(ChatMessage)
                .filter(
                    ChatMessage.sender == "user",
                    ChatMessage.timestamp >= day_start,
                    ChatMessage.timestamp <= day_end,
                )
                .count()
            )
            trends.append({"date": day.strftime("%b %d"), "count": count})

        # Top 10 most frequent questions (by exact message text)
        top_raw = (
            db.query(ChatMessage.message, func.count(ChatMessage.message).label("freq"))
            .filter(ChatMessage.sender == "user")
            .group_by(ChatMessage.message)
            .order_by(func.count(ChatMessage.message).desc())
            .limit(10)
            .all()
        )
        top_questions = [
            {"question": row.message[:100], "count": row.freq} for row in top_raw
        ]

        # Recent activity: last 20 student questions with student email and timestamp
        recent_msgs = (
            db.query(ChatMessage, ChatSession, User)
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .join(User, ChatSession.user_id == User.id)
            .filter(ChatMessage.sender == "user")
            .order_by(ChatMessage.timestamp.desc())
            .limit(20)
            .all()
        )

        recent_activity = []
        for msg, session, user in recent_msgs:
            recent_activity.append(
                {
                    "student_email": user.email,
                    "student_name": user.full_name,
                    "question": msg.message[:120],
                    "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M"),
                }
            )

        return {
            "total_students": total_students,
            "active_students": int(active_students),
            "total_questions": total_questions,
            "total_sessions": total_sessions,
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "question_trends": trends,
            "top_questions": top_questions,
            "recent_activity": recent_activity,
        }

    @staticmethod
    def get_all_student_queries(db: Session, limit: int = 50) -> list:
        """
        Admin-only: returns all student questions paired with the AI answer that followed.
        SECURITY: This endpoint must only be called via require_admin dependency.
        Students must NEVER access this data.
        """
        # Get user messages (questions) with their session and user info
        user_messages = (
            db.query(ChatMessage, ChatSession, User)
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .join(User, ChatSession.user_id == User.id)
            .filter(ChatMessage.sender == "user")
            .order_by(ChatMessage.timestamp.desc())
            .limit(limit)
            .all()
        )

        result = []
        for user_msg, session, user in user_messages:
            # Find the AI reply that immediately follows this user message
            ai_reply = (
                db.query(ChatMessage)
                .filter(
                    ChatMessage.session_id == user_msg.session_id,
                    ChatMessage.sender == "ai",
                    ChatMessage.id > user_msg.id,
                )
                .order_by(ChatMessage.id.asc())
                .first()
            )

            sources = []
            if ai_reply and ai_reply.sources_json:
                try:
                    sources = json.loads(str(ai_reply.sources_json))
                except Exception:
                    sources = []

            result.append(
                {
                    "student_email": user.email,
                    "student_name": user.full_name,
                    "session_title": session.title,
                    "question": user_msg.message,
                    "answer": ai_reply.message if ai_reply else "(No answer recorded)",
                    "sources": sources,
                    "timestamp": user_msg.timestamp.strftime("%Y-%m-%d %H:%M"),
                }
            )

        return result
