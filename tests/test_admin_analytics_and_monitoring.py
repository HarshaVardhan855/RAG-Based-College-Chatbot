import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import Base
from database.repository import Repository
from auth.authentication import hash_password
from database.models import UserRole
import os

TEST_DB_URL = "sqlite:///./test_analytics.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def analytics_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create Admin
    Repository.create_user(
        db,
        "analytics_admin@college.edu",
        hash_password("pass"),
        "Analytics Admin",
        UserRole.ADMIN.value,
    )

    # 1. Create 5 registered students (Section 31 requirement)
    s_a = Repository.create_user(
        db,
        "student_a_analytics@college.edu",
        hash_password("pass"),
        "Student A",
        UserRole.STUDENT.value,
    )
    s_b = Repository.create_user(
        db,
        "student_b_analytics@college.edu",
        hash_password("pass"),
        "Student B",
        UserRole.STUDENT.value,
    )
    s_c = Repository.create_user(
        db,
        "student_c_analytics@college.edu",
        hash_password("pass"),
        "Student C",
        UserRole.STUDENT.value,
    )
    Repository.create_user(
        db,
        "student_d_analytics@college.edu",
        hash_password("pass"),
        "Student D",
        UserRole.STUDENT.value,
    )
    Repository.create_user(
        db,
        "student_e_analytics@college.edu",
        hash_password("pass"),
        "Student E",
        UserRole.STUDENT.value,
    )

    # 2. Student A asks 3 questions
    sess_a = Repository.create_chat_session(db, s_a.id, "Session A")
    Repository.create_chat_message(db, sess_a.id, "user", "Question A1")
    Repository.create_chat_message(
        db,
        sess_a.id,
        "ai",
        "Answer A1",
        sources=[{"document_name": "Doc1.pdf", "page": 1}],
    )
    Repository.create_chat_message(db, sess_a.id, "user", "Question A2")
    Repository.create_chat_message(
        db,
        sess_a.id,
        "ai",
        "Answer A2",
        sources=[{"document_name": "Doc1.pdf", "page": 2}],
    )
    Repository.create_chat_message(db, sess_a.id, "user", "Question A3")
    Repository.create_chat_message(db, sess_a.id, "ai", "Answer A3")

    # 3. Student B asks 2 questions
    sess_b = Repository.create_chat_session(db, s_b.id, "Session B")
    Repository.create_chat_message(db, sess_b.id, "user", "Question B1")
    Repository.create_chat_message(db, sess_b.id, "ai", "Answer B1")
    Repository.create_chat_message(db, sess_b.id, "user", "Question B2")
    Repository.create_chat_message(db, sess_b.id, "ai", "Answer B2")

    # 4. Student C asks 1 question
    sess_c = Repository.create_chat_session(db, s_c.id, "Session C")
    Repository.create_chat_message(db, sess_c.id, "user", "Question C1")
    Repository.create_chat_message(db, sess_c.id, "ai", "Answer C1")

    # Students D and E ask 0 questions

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_analytics.db"):
        try:
            os.remove("./test_analytics.db")
        except Exception:
            pass


def test_admin_analytics_calculations(analytics_db):
    stats = Repository.get_analytics_stats(analytics_db)

    # Mandatory Section 31 Verification:
    # Total registered students = 5
    assert stats["total_students"] == 5

    # Students using chatbot (UNIQUE students who submitted questions) = 3
    assert stats["active_students"] == 3

    # Total questions = 6 (3 from A + 2 from B + 1 from C)
    assert stats["total_questions"] == 6

    # Total sessions = 3
    assert stats["total_sessions"] == 3


def test_admin_query_monitoring(analytics_db):
    queries = Repository.get_all_student_queries(analytics_db, limit=50)

    # Should record all 6 student questions
    assert len(queries) == 6

    # Verify query detail fields
    q1 = queries[0]  # Most recent question
    assert "student_email" in q1
    assert "student_name" in q1
    assert "question" in q1
    assert "answer" in q1
    assert "sources" in q1
    assert "timestamp" in q1
