import pytest
import os
import io
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import Base
from database.repository import Repository
from auth.authentication import hash_password
from database.models import UserRole
from services.document_service import DocumentService
from fastapi import UploadFile

TEST_DB_URL = "sqlite:///./test_doc_lifecycle.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def doc_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    admin = Repository.create_user(
        db,
        "doc_admin@college.edu",
        hash_password("pass"),
        "Doc Admin",
        UserRole.ADMIN.value,
    )

    yield db, admin.id

    db.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_doc_lifecycle.db"):
        try:
            os.remove("./test_doc_lifecycle.db")
        except Exception:
            pass


def test_document_upload_reprocess_and_delete(doc_db):
    db, admin_id = doc_db

    # 1. Upload TXT Document
    content = "College Placement Cell Guidelines 2026.\n\nOver 95% of eligible students placed in top firms."
    file_obj = UploadFile(
        filename="Placements_2026.txt", file=io.BytesIO(content.encode("utf-8"))
    )

    doc = DocumentService.process_and_store_document(
        db=db,
        file=file_obj,
        title="Placement Guidelines 2026",
        department="Placements",
        category="Placements",
        admin_id=admin_id,
    )

    assert doc.id is not None
    doc_id = int(doc.id)
    assert doc.title == "Placement Guidelines 2026"
    assert doc.version == 1
    assert doc.status == "PROCESSED"

    # Verify chunks created
    chunks = Repository.get_chunks_by_document(db, doc_id)
    assert len(chunks) > 0

    # 2. Reprocess Document
    reprocess_res = DocumentService.reprocess_document(db, doc_id)
    assert reprocess_res["version"] == 2

    reprocessed_doc = Repository.get_document_by_id(db, doc_id)
    assert reprocessed_doc is not None
    assert reprocessed_doc.version == 2

    # 3. Delete Document
    del_res = DocumentService.delete_document(db, doc_id)
    assert "deleted successfully" in del_res["message"]

    # Verify document & chunks deleted from DB
    deleted_doc = Repository.get_document_by_id(db, doc_id)
    assert deleted_doc is None

    deleted_chunks = Repository.get_chunks_by_document(db, doc_id)
    assert len(deleted_chunks) == 0
