import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import Base
from database.repository import Repository
from rag.pipeline import run_rag_pipeline
from services.document_service import DocumentService
from fastapi import UploadFile
import io
from typing import Any

TEST_DB_URL = "sqlite:///./test_rag.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def db_session():
    if os.path.exists("./test_rag.db"):
        try:
            os.remove("./test_rag.db")
        except Exception:
            pass
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create test admin user if not already present
    user = Repository.get_user_by_email(db, "admin_test@college.edu")
    if not user:
        user = Repository.create_user(
            db, "admin_test@college.edu", "hashed_pwd", "Admin Test", "ADMIN"
        )

    yield db, user.id

    db.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_rag.db"):
        try:
            os.remove("./test_rag.db")
        except Exception:
            pass


def test_rag_end_to_end_known_and_unknown_questions(db_session: Any):
    db, admin_id = db_session

    # 1. Upload Test Document
    notice_content = "Official Examination Notice 2026.\n\nThe last date for examination registration is September 15, 2026. No late fees will be accepted after September 20."
    file_bytes = notice_content.encode("utf-8")
    upload_file = UploadFile(
        filename="Examination_Notice_2026.txt", file=io.BytesIO(file_bytes)
    )

    doc = DocumentService.process_and_store_document(
        db=db,
        file=upload_file,
        title="Examination Notice 2026",
        department="Examinations",
        category="Examinations",
        admin_id=admin_id,
    )

    assert doc is not None
    doc_id = int(str(doc.id))
    assert doc_id > 0

    # 2. Test Known Question
    known_question = "What is the last date for examination registration?"
    result_known = run_rag_pipeline(known_question, db)

    assert "September 15, 2026" in result_known["answer"]
    assert len(result_known["sources"]) > 0
    assert result_known["sources"][0]["document_name"] == "Examination_Notice_2026.txt"

    # 3. Test Unknown Out-of-Scope Question
    unknown_question = "What is the college's international exchange policy for 2030?"
    result_unknown = run_rag_pipeline(unknown_question, db)

    assert (
        "I couldn't find this information in the college knowledge base."
        in result_unknown["answer"]
    )
    assert len(result_unknown["sources"]) == 0

    # 4. Test Deletion -> Fact should disappear from retrieval
    DocumentService.delete_document(db, doc_id)

    result_after_delete = run_rag_pipeline(known_question, db)
    assert (
        "I couldn't find this information in the college knowledge base."
        in result_after_delete["answer"]
    )
    assert len(result_after_delete["sources"]) == 0
