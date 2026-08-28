import pytest
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import Base, get_db
from database.repository import Repository
from auth.authentication import create_access_token, hash_password
from database.models import UserRole
import os

TEST_DB_URL = "sqlite:///./test_sec.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create Admin
    admin = Repository.create_user(
        db,
        "sec_admin@college.edu",
        hash_password("pass"),
        "Sec Admin",
        UserRole.ADMIN.value,
    )
    # Create Student A
    student_a = Repository.create_user(
        db,
        "student_a@college.edu",
        hash_password("pass"),
        "Student A",
        UserRole.STUDENT.value,
    )
    # Create Student B
    student_b = Repository.create_user(
        db,
        "student_b@college.edu",
        hash_password("pass"),
        "Student B",
        UserRole.STUDENT.value,
    )

    # Create session for Student B
    session_b = Repository.create_chat_session(db, student_b.id, "Student B Session")

    yield {
        "admin": admin,
        "student_a": student_a,
        "student_b": student_b,
        "session_b": session_b,
        "db": db,
    }

    db.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_sec.db"):
        try:
            os.remove("./test_sec.db")
        except Exception:
            pass


def test_student_cannot_access_admin_endpoints(setup_test_db):
    student_a = setup_test_db["student_a"]
    token = create_access_token(
        {"sub": str(student_a.id), "email": student_a.email, "role": student_a.role}
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Student -> Admin Analytics API -> DENIED (403)
    res_analytics = client.get("/api/admin/analytics", headers=headers)
    assert res_analytics.status_code == 403

    # Student -> Admin Queries API -> DENIED (403)
    res_queries = client.get("/api/admin/queries", headers=headers)
    assert res_queries.status_code == 403

    # Student -> Upload Document -> DENIED (403)
    res_upload = client.post(
        "/api/admin/documents", headers=headers, data={"title": "Test"}
    )
    assert res_upload.status_code == 403

    # Student -> Delete Document -> DENIED (403)
    res_delete = client.delete("/api/admin/documents/1", headers=headers)
    assert res_delete.status_code == 403


def test_student_cannot_access_other_student_conversations(setup_test_db):
    student_a = setup_test_db["student_a"]
    session_b = setup_test_db["session_b"]
    token_a = create_access_token(
        {"sub": str(student_a.id), "email": student_a.email, "role": student_a.role}
    )
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Student A tries to view Student B's session messages -> DENIED (404/403)
    res_get = client.get(
        f"/api/chat/sessions/{session_b.id}/messages", headers=headers_a
    )
    assert res_get.status_code == 404

    # Student A tries to send a message to Student B's session -> DENIED (404/403)
    res_send = client.post(
        f"/api/chat/sessions/{session_b.id}/messages",
        headers=headers_a,
        json={"question": "Hi?"},
    )
    assert res_send.status_code == 404

    # Student A tries to delete Student B's session -> DENIED (404/403)
    res_del = client.delete(f"/api/chat/sessions/{session_b.id}", headers=headers_a)
    assert res_del.status_code == 404


def test_admin_access_allowed(setup_test_db):
    admin = setup_test_db["admin"]
    token_admin = create_access_token(
        {"sub": str(admin.id), "email": admin.email, "role": admin.role}
    )
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # Admin -> Analytics -> ALLOWED (200)
    res_analytics = client.get("/api/admin/analytics", headers=headers_admin)
    assert res_analytics.status_code == 200

    # Admin -> Student Queries -> ALLOWED (200)
    res_queries = client.get("/api/admin/queries", headers=headers_admin)
    assert res_queries.status_code == 200

    # Admin -> Documents List -> ALLOWED (200)
    res_docs = client.get("/api/admin/documents", headers=headers_admin)
    assert res_docs.status_code == 200
