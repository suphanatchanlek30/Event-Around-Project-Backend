from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.event_category import EventCategory
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


def setup_function():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_function():
    app.dependency_overrides.clear()


def create_user(role: str, email: str) -> User:
    db = TestingSessionLocal()
    try:
        user = User(
            full_name=f"{role} User",
            email=email,
            password_hash="hashed_pw",
            role=role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def create_category(name: str, description: str | None = None, is_active: bool = True) -> EventCategory:
    db = TestingSessionLocal()
    try:
        category = EventCategory(name=name, description=description, is_active=is_active)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    finally:
        db.close()


def auth_header_for(user: User) -> dict[str, str]:
    token, _ = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


def test_list_categories_only_active_by_default():
    client = TestClient(app)
    create_category("Academic", "กิจกรรมเชิงวิชาการ", is_active=True)
    create_category("Legacy", "หมวดเก่า", is_active=False)

    response = client.get("/api/v1/categories")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "Academic"


def test_list_categories_include_inactive_true():
    client = TestClient(app)
    create_category("Academic", is_active=True)
    create_category("Legacy", is_active=False)

    response = client.get("/api/v1/categories?includeInactive=true")

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 2


def test_list_categories_invalid_query_returns_400():
    client = TestClient(app)

    response = client.get("/api/v1/categories?includeInactive=maybe")

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False


def test_create_category_organizer_success():
    client = TestClient(app)
    organizer = create_user(role="ORGANIZER", email="org@category.com")

    response = client.post(
        "/api/v1/categories",
        json={"name": "Hackathon", "description": "กิจกรรมการแข่งขันพัฒนาโปรแกรม"},
        headers=auth_header_for(organizer),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Hackathon"
    assert body["data"]["isActive"] is True


def test_create_category_requires_permission():
    client = TestClient(app)
    student = create_user(role="STUDENT", email="student@category.com")

    response = client.post(
        "/api/v1/categories",
        json={"name": "Hackathon", "description": "กิจกรรมการแข่งขันพัฒนาโปรแกรม"},
        headers=auth_header_for(student),
    )

    assert response.status_code == 403


def test_create_category_duplicate_name_returns_409():
    client = TestClient(app)
    admin = create_user(role="ADMIN", email="admin@category.com")
    create_category("Hackathon", "เดิม")

    response = client.post(
        "/api/v1/categories",
        json={"name": " hackathon ", "description": "ใหม่"},
        headers=auth_header_for(admin),
    )

    assert response.status_code == 409


def test_get_category_detail_success_and_not_found():
    client = TestClient(app)
    category = create_category("Academic", "กิจกรรมเชิงวิชาการ")

    ok_response = client.get(f"/api/v1/categories/{category.id}")
    assert ok_response.status_code == 200
    assert ok_response.json()["data"]["categoryId"] == category.id

    not_found_response = client.get("/api/v1/categories/9999")
    assert not_found_response.status_code == 404


def test_update_category_success_and_duplicate_name():
    client = TestClient(app)
    organizer = create_user(role="ORGANIZER", email="org-update@category.com")
    category = create_category("Workshop", "เดิม")
    create_category("Seminar", "มีอยู่แล้ว")

    success_response = client.patch(
        f"/api/v1/categories/{category.id}",
        json={"name": "Workshop Updated", "description": "กิจกรรมฝึกปฏิบัติแบบลงมือทำ"},
        headers=auth_header_for(organizer),
    )
    assert success_response.status_code == 200
    assert success_response.json()["data"]["name"] == "Workshop Updated"

    duplicate_response = client.patch(
        f"/api/v1/categories/{category.id}",
        json={"name": "seminar"},
        headers=auth_header_for(organizer),
    )
    assert duplicate_response.status_code == 409


def test_deactivate_category_success_and_not_found():
    client = TestClient(app)
    admin = create_user(role="ADMIN", email="admin-delete@category.com")
    category = create_category("Meetup", "กิจกรรมพบปะ")

    response = client.delete(
        f"/api/v1/categories/{category.id}",
        headers=auth_header_for(admin),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["categoryId"] == category.id
    assert body["data"]["isActive"] is False

    not_found_response = client.delete(
        "/api/v1/categories/9999",
        headers=auth_header_for(admin),
    )
    assert not_found_response.status_code == 404
