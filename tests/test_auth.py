from app.core.database import Base, get_db
from app.main import app
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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


def setup_function():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_function():
    app.dependency_overrides.clear()


def create_student_user(
    email: str = "student@example.com",
    password_hash: str = "hashed_pw",
    profile_image_url: str | None = None,
) -> int:
    db = TestingSessionLocal()
    try:
        user = User(
            full_name="Student User",
            email=email,
            password_hash=password_hash,
            role="STUDENT",
            is_active=True,
            profile_image_url=profile_image_url,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    finally:
        db.close()


def test_register_student_success(monkeypatch):
    monkeypatch.setattr("app.services.auth_service.get_password_hash", lambda _: "hashed_pw")
    client = TestClient(app)

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
    assert body["data"]["role"] == "STUDENT"


def test_register_organizer_success(monkeypatch):
    monkeypatch.setattr("app.services.auth_service.get_password_hash", lambda _: "hashed_pw")
    client = TestClient(app)

    payload = {
        "fullName": "Organizer User",
        "email": "org1@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
    }

    response = client.post("/api/v1/auth/register/organizer", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["role"] == "ORGANIZER"


def test_register_student_duplicate_email(monkeypatch):
    monkeypatch.setattr("app.services.auth_service.get_password_hash", lambda _: "hashed_pw")
    client = TestClient(app)

    create_student_user(email="dup@example.com")

    payload = {
        "fullName": "New User",
        "email": "dup@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
    }

    response = client.post("/api/v1/auth/register/student", json=payload)
    assert response.status_code == 409


def test_login_and_me_flow(monkeypatch):
    monkeypatch.setattr("app.services.auth_service.verify_password", lambda plain, hashed: plain == "Password123!")
    client = TestClient(app)

    create_student_user(
        email="student@login.com",
        password_hash="any_hash",
        profile_image_url="https://example.com/profile.jpg",
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "student@login.com", "password": "Password123!"},
    )
    assert login_response.status_code == 200

    login_body = login_response.json()
    access_token = login_body["data"]["accessToken"]
    refresh_token = login_body["data"]["refreshToken"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()["data"]
    assert me_data["email"] == "student@login.com"
    assert me_data["isActive"] is True
    assert me_data["profileImageUrl"] == "https://example.com/profile.jpg"

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": refresh_token},
    )
    assert refresh_response.status_code == 200
    assert refresh_response.json()["success"] is True


def test_patch_me_and_change_password(monkeypatch):
    monkeypatch.setattr("app.services.auth_service.verify_password", lambda plain, hashed: plain == "Password123!")
    monkeypatch.setattr("app.services.auth_service.get_password_hash", lambda _: "new_hash")
    client = TestClient(app)

    create_student_user(email="student@patch.com", password_hash="old_hash")

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "student@patch.com", "password": "Password123!"},
    )
    tokens = login_response.json()["data"]
    access_token = tokens["accessToken"]
    refresh_token = tokens["refreshToken"]

    patch_response = client.patch(
        "/api/v1/auth/me",
        json={"fullName": "Updated Name", "profileImageUrl": "https://example.com/avatar.jpg"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert patch_response.status_code == 200
    patch_data = patch_response.json()["data"]
    assert patch_data["fullName"] == "Updated Name"
    assert patch_data["profileImageUrl"] == "https://example.com/avatar.jpg"

    me_after_patch = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_after_patch.status_code == 200
    assert me_after_patch.json()["data"]["profileImageUrl"] == "https://example.com/avatar.jpg"

    change_pass_response = client.post(
        "/api/v1/auth/change-password",
        json={
            "oldPassword": "Password123!",
            "newPassword": "NewPassword123!",
            "confirmNewPassword": "NewPassword123!",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert change_pass_response.status_code == 200

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refreshToken": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_response.status_code == 200


def test_patch_me_rejects_invalid_profile_image_url(monkeypatch):
    monkeypatch.setattr("app.services.auth_service.verify_password", lambda plain, hashed: plain == "Password123!")
    client = TestClient(app)

    create_student_user(email="student@invalid-url.com", password_hash="any_hash")

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "student@invalid-url.com", "password": "Password123!"},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["data"]["accessToken"]

    patch_response = client.patch(
        "/api/v1/auth/me",
        json={"profileImageUrl": "not-a-valid-url"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert patch_response.status_code == 422
