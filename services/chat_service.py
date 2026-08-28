import json
from sqlalchemy.orm import Session
from fastapi import HTTPException
from database.repository import Repository
from rag.pipeline import run_rag_pipeline


class ChatService:
    @staticmethod
    def create_session(db: Session, user_id: int, title: str = "New Conversation"):
        session = Repository.create_chat_session(db, user_id, title)
        return {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at.strftime("%Y-%m-%d %H:%M"),
        }

    @staticmethod
    def get_user_sessions(db: Session, user_id: int):
        sessions = Repository.get_chat_sessions(db, user_id)
        return [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.strftime("%Y-%m-%d %H:%M"),
                "message_count": len(s.messages),
            }
            for s in sessions
        ]

    @staticmethod
    def get_session_messages(db: Session, session_id: int, user_id: int):
        session = Repository.get_chat_session(db, session_id, user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found.")

        messages = []
        for m in session.messages:
            sources = json.loads(m.sources_json) if m.sources_json else []
            messages.append(
                {
                    "id": m.id,
                    "sender": m.sender,
                    "message": m.message,
                    "sources": sources,
                    "timestamp": m.timestamp.strftime("%H:%M"),
                }
            )
        return {"session_id": session.id, "title": session.title, "messages": messages}

    @staticmethod
    def process_chat_message(db: Session, session_id: int, user_id: int, question: str):
        session = Repository.get_chat_session(db, session_id, user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found.")

        if not question or not question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty.")

        # Set title from first question if default
        session_title = str(session.title)
        if session_title == "New Conversation":
            session.title = str(
                question.strip()[:35] + ("..." if len(question) > 35 else "")
            )  # type: ignore

        # 1. Save student question message
        user_msg = Repository.create_chat_message(db, session_id, "user", question)

        # 2. Get past chat history for context
        history = []
        for m in session.messages:
            history.append({"sender": str(m.sender), "message": str(m.message)})

        # 3. Execute RAG Pipeline
        rag_output = run_rag_pipeline(question, db, history)

        # 4. Save AI Answer message
        ai_msg = Repository.create_chat_message(
            db=db,
            session_id=session_id,
            sender="ai",
            message=rag_output["answer"],
            sources=rag_output["sources"],
        )

        return {
            "user_message": {
                "id": user_msg.id,
                "sender": user_msg.sender,
                "message": user_msg.message,
                "timestamp": user_msg.timestamp.strftime("%H:%M"),
            },
            "ai_message": {
                "id": ai_msg.id,
                "sender": ai_msg.sender,
                "message": ai_msg.message,
                "sources": rag_output["sources"],
                "timestamp": ai_msg.timestamp.strftime("%H:%M"),
            },
        }

    @staticmethod
    def delete_session(db: Session, session_id: int, user_id: int):
        success = Repository.delete_chat_session(db, session_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found.")
        return {"message": "Chat session deleted."}
