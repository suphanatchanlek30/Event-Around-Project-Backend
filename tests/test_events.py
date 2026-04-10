from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.event import Event
from app.models.event_category import EventCategory
from app.models.event_save import EventSave
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


def create_event(
    title: str,
    category_id: int,
    organizer_id: int,
    start_time: datetime,
    end_time: datetime,
    status: str = "PUBLISHED",
    location_name: str = "SCI Building Room 501",
    description: str | None = None,
) -> Event:
    db = TestingSessionLocal()
    try:
        event = Event(
            title=title,
            description=description,
            location_name=location_name,
            latitude=14.87,
            longitude=102.01,
            start_time=start_time,
            end_time=end_time,
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
        event_save = EventSave(event_id=event_id, user_id=user_id)
        db.add(event_save)
        db.commit()
        db.refresh(event_save)
        return event_save
    finally:
        db.close()


def create_access_token_for_user(user: User) -> str:
    token, _ = create_access_token(user.id, user.role)
    return token


def test_list_events_returns_published_only_and_meta():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org@events.com")
    category = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")

    start_time = datetime(2026, 4, 10, 9, 0, tzinfo=timezone.utc)
    end_time = datetime(2026, 4, 10, 12, 0, tzinfo=timezone.utc)
    create_event(
        title="Python Workshop",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=start_time,
        end_time=end_time,
        status="PUBLISHED",
    )
    create_event(
        title="Draft Event",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=start_time,
        end_time=end_time,
        status="DRAFT",
    )

    response = client.get("/api/v1/events")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["meta"]["totalItems"] == 1
    assert body["meta"]["page"] == 1
    assert body["data"][0]["title"] == "Python Workshop"


def test_get_event_detail_published_event_returns_detail():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_detail@events.com")
    category = create_category("Seminar", "กิจกรรมสัมมนา")
    start_time = datetime(2026, 5, 10, 9, 0, tzinfo=timezone.utc)
    end_time = datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc)
    event = create_event(
        title="Data Science Seminar",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=start_time,
        end_time=end_time,
        status="PUBLISHED",
        description="A seminar about data science.",
    )

    response = client.get(f"/api/v1/events/{event.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["eventId"] == event.id
    assert body["data"]["title"] == "Data Science Seminar"
    assert body["data"]["savedCount"] == 0
    assert body["data"]["isSaved"] is False


def test_get_event_detail_returns_is_saved_for_student():
    client = TestClient(app)
    student = create_user("STUDENT", "student@example.com")
    organizer = create_user("ORGANIZER", "org_event@events.com")
    category = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")
    start_time = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
    end_time = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    event = create_event(
        title="AI Workshop",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=start_time,
        end_time=end_time,
        status="PUBLISHED",
    )
    create_event_save(event.id, student.id)
    token = create_access_token_for_user(student)

    response = client.get(
        f"/api/v1/events/{event.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["savedCount"] == 1
    assert body["data"]["isSaved"] is True


def test_get_event_detail_unpublished_returns_404_for_anonymous():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_draft@events.com")
    category = create_category("Seminar", "กิจกรรมสัมมนา")
    start_time = datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc)
    end_time = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)
    event = create_event(
        title="Secret Event",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=start_time,
        end_time=end_time,
        status="DRAFT",
    )

    response = client.get(f"/api/v1/events/{event.id}")

    assert response.status_code == 404
    assert response.json()["success"] is False


def test_list_events_filters_search_category_date_and_sort():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org2@events.com")
    workshop = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")
    seminar = create_category("Seminar", "กิจกรรมสัมมนา")

    now = datetime(2026, 4, 1, 0, 0, tzinfo=timezone.utc)
    later = now + timedelta(days=9)
    create_event(
        title="Python Workshop",
        category_id=workshop.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 4, 10, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 4, 10, 12, 0, tzinfo=timezone.utc),
        status="PUBLISHED",
    )
    create_event(
        title="Java Seminar",
        category_id=seminar.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 4, 15, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 4, 15, 11, 0, tzinfo=timezone.utc),
        status="PUBLISHED",
    )

    response = client.get(
        "/api/v1/events?search=python&categoryId=%s&status=PUBLISHED&startFrom=2026-04-01T00:00:00Z&endTo=2026-04-30T23:59:59Z&sortBy=startTime&sortOrder=asc"
        % workshop.id,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["meta"]["totalItems"] == 1
    assert body["data"][0]["category"]["categoryId"] == workshop.id
    assert body["data"][0]["organizer"]["fullName"] == organizer.full_name


def test_list_events_invalid_sort_by_returns_400():
    client = TestClient(app)
    response = client.get("/api/v1/events?sortBy=invalid")
    assert response.status_code == 400
    assert response.json()["success"] is False
