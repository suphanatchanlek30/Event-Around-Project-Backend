from datetime import UTC, datetime

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.event import Event
from app.models.event_category import EventCategory
from app.models.event_save import EventSave
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


def create_category(name: str = "Workshop") -> EventCategory:
    db = TestingSessionLocal()
    try:
        category = EventCategory(name=name, description="test", is_active=True)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    finally:
        db.close()


def create_event(
    category_id: int,
    organizer_id: int,
    status: str = "PUBLISHED",
    title: str = "Test Event",
) -> Event:
    db = TestingSessionLocal()
    try:
        event = Event(
            title=title,
            description="desc",
            short_description=None,
            location_name="Room 501",
            latitude=14.87,
            longitude=102.01,
            start_time=datetime(2026, 5, 1, 9, 0, tzinfo=UTC),
            end_time=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
            status=status,
            category_id=category_id,
            organizer_id=organizer_id,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    finally:
        db.close()


def create_event_save(event_id: int, user_id: int) -> EventSave:
    db = TestingSessionLocal()
    try:
        es = EventSave(event_id=event_id, user_id=user_id)
        db.add(es)
        db.commit()
        db.refresh(es)
        return es
    finally:
        db.close()


def token_for(user: User) -> str:
    t, _ = create_access_token(user.id, user.role)
    return t


# ---------- success ----------

def test_dashboard_returns_correct_counts():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org@test.com")
    student = create_user("STUDENT", "stu@test.com")
    cat = create_category()

    # 2 DRAFT, 3 PUBLISHED, 1 CANCELLED = 6 total
    create_event(cat.id, organizer.id, status="DRAFT")
    create_event(cat.id, organizer.id, status="DRAFT")
    pub1 = create_event(cat.id, organizer.id, status="PUBLISHED", title="Pub1")
    pub2 = create_event(cat.id, organizer.id, status="PUBLISHED", title="Pub2")
    create_event(cat.id, organizer.id, status="PUBLISHED", title="Pub3")
    create_event(cat.id, organizer.id, status="CANCELLED")

    # student saves 2 published events
    create_event_save(pub1.id, student.id)
    create_event_save(pub2.id, student.id)

    token = token_for(organizer)
    resp = client.get(
        "/api/v1/organizer/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "ดึง dashboard สำเร็จ"
    data = body["data"]
    assert data["totalEvents"] == 6
    assert data["draftEvents"] == 2
    assert data["publishedEvents"] == 3
    assert data["cancelledEvents"] == 1
    assert data["totalSavedCount"] == 2


def test_dashboard_zero_events():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_zero@test.com")
    token = token_for(organizer)

    resp = client.get(
        "/api/v1/organizer/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["totalEvents"] == 0
    assert data["draftEvents"] == 0
    assert data["publishedEvents"] == 0
    assert data["cancelledEvents"] == 0
    assert data["totalSavedCount"] == 0


def test_dashboard_does_not_count_other_organizer_events():
    client = TestClient(app)
    org1 = create_user("ORGANIZER", "org1@test.com")
    org2 = create_user("ORGANIZER", "org2@test.com")
    cat = create_category()

    create_event(cat.id, org1.id, status="PUBLISHED")
    create_event(cat.id, org2.id, status="PUBLISHED")

    token = token_for(org1)
    resp = client.get(
        "/api/v1/organizer/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert resp.json()["data"]["totalEvents"] == 1


# ---------- error cases ----------

def test_dashboard_unauthorized_no_token():
    client = TestClient(app)
    resp = client.get("/api/v1/organizer/dashboard")
    assert resp.status_code == 401


def test_dashboard_forbidden_student():
    client = TestClient(app)
    student = create_user("STUDENT", "stu_forbidden@test.com")
    token = token_for(student)

    resp = client.get(
        "/api/v1/organizer/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403


def test_dashboard_forbidden_admin():
    client = TestClient(app)
    admin = create_user("ADMIN", "admin@test.com")
    token = token_for(admin)

    resp = client.get(
        "/api/v1/organizer/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403


# ========== GET /api/v1/organizer/events/{eventId}/stats ==========

# ---------- success ----------

def test_event_stats_returns_correct_data():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_stats@test.com")
    student1 = create_user("STUDENT", "stu1_stats@test.com")
    student2 = create_user("STUDENT", "stu2_stats@test.com")
    cat = create_category()

    event = create_event(cat.id, organizer.id, status="PUBLISHED", title="Python Workshop")
    create_event_save(event.id, student1.id)
    create_event_save(event.id, student2.id)

    token = token_for(organizer)
    resp = client.get(
        f"/api/v1/organizer/events/{event.id}/stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "ดึงสถิติกิจกรรมสำเร็จ"
    data = body["data"]
    assert data["eventId"] == event.id
    assert data["title"] == "Python Workshop"
    assert data["status"] == "PUBLISHED"
    assert data["savedCount"] == 2
    assert "startTime" in data
    assert "endTime" in data


def test_event_stats_zero_saves():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_zero_stats@test.com")
    cat = create_category()
    event = create_event(cat.id, organizer.id, status="DRAFT", title="Draft Event")

    token = token_for(organizer)
    resp = client.get(
        f"/api/v1/organizer/events/{event.id}/stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["savedCount"] == 0
    assert data["status"] == "DRAFT"


# ---------- error cases ----------

def test_event_stats_unauthorized_no_token():
    client = TestClient(app)
    resp = client.get("/api/v1/organizer/events/1/stats")
    assert resp.status_code == 401


def test_event_stats_forbidden_student():
    client = TestClient(app)
    student = create_user("STUDENT", "stu_stats_forbid@test.com")
    token = token_for(student)

    resp = client.get(
        "/api/v1/organizer/events/1/stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403


def test_event_stats_not_found():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_notfound@test.com")
    token = token_for(organizer)

    resp = client.get(
        "/api/v1/organizer/events/9999/stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 404


def test_event_stats_forbidden_not_owner():
    client = TestClient(app)
    org1 = create_user("ORGANIZER", "org1_stats@test.com")
    org2 = create_user("ORGANIZER", "org2_stats@test.com")
    cat = create_category()
    event = create_event(cat.id, org1.id, status="PUBLISHED")

    token = token_for(org2)
    resp = client.get(
        f"/api/v1/organizer/events/{event.id}/stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403