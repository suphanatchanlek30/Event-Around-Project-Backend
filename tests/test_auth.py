from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_register_student_success(monkeypatch):
    monkeypatch.setattr("app.services.auth_service.get_password_hash", lambda _: "hashed_pw")

    payload = {
        "fullName": "Test User",
        "email": "test1@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
    }

    response = client.post("/api/v1/auth/register/student", json=payload)
    assert response.status_code == 201

    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "test1@example.com"
    assert body["data"]["role"] == "STUDENT"


def test_register_student_duplicate_email(monkeypatch):
    monkeypatch.setattr("app.services.auth_service.get_password_hash", lambda _: "hashed_pw")

    db = TestingSessionLocal()
    try:
        db.add(
            User(
                full_name="Existing User",
                email="dup@example.com",
                password_hash="hashed_pw",
                role="STUDENT",
            )
        )
        db.commit()
    finally:
        db.close()

    payload = {
        "fullName": "New User",
        "email": "dup@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
    }

    response = client.post("/api/v1/auth/register/student", json=payload)
    assert response.status_code == 409

    body = response.json()
    assert body["success"] is False
    assert body["errors"][0]["code"] == "EMAIL_ALREADY_EXISTS"


def test_register_student_password_mismatch(monkeypatch):
    monkeypatch.setattr("app.services.auth_service.get_password_hash", lambda _: "hashed_pw")

    payload = {
        "fullName": "Test User",
        "email": "test2@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123",
    }

    response = client.post("/api/v1/auth/register/student", json=payload)
    assert response.status_code == 400

    body = response.json()
    assert body["success"] is False
    assert body["errors"][0]["code"] == "PASSWORD_MISMATCH"
