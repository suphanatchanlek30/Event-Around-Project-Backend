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
    short_description: str | None = None,
    cover_image_url: str | None = None,
) -> Event:
    db = TestingSessionLocal()
    try:
        event = Event(
            title=title,
            description=description,
            short_description=short_description,
            location_name=location_name,
            latitude=14.87,
            longitude=102.01,
            start_time=start_time,
            end_time=end_time,
            status=status,
            category_id=category_id,
            organizer_id=organizer_id,
            cover_image_url=cover_image_url,
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


def test_create_event_as_organizer_saves_as_draft():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_create@events.com")
    category = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")

    payload = {
        "title": "Python Workshop",
        "description": "เวิร์กชอป Python เบื้องต้น",
        "shortDescription": "ลงมือทำจริง",
        "locationName": "SCI Building Room 501",
        "latitude": 15.120245,
        "longitude": 104.906928,
        "startTime": "2026-04-10T09:00:00+07:00",
        "endTime": "2026-04-10T12:00:00+07:00",
        "categoryId": category.id,
        "coverImageUrl": "https://example.com/python.jpg",
        "status": "DRAFT",
    }
    token = create_access_token_for_user(organizer)

    response = client.post(
        "/api/v1/events",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "DRAFT"
    assert body["data"]["categoryId"] == category.id


def test_organizer_owner_can_update_event():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_update@events.com")
    category = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")
    event = create_event(
        title="Python Workshop",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 4, 10, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 4, 10, 12, 0, tzinfo=timezone.utc),
        status="DRAFT",
    )
    token = create_access_token_for_user(organizer)

    response = client.patch(
        f"/api/v1/events/{event.id}",
        json={
            "title": "Python Workshop Updated",
            "locationName": "SCI Building Room 502",
            "latitude": 15.120300,
            "longitude": 104.907000,
            "startTime": "2026-04-10T10:00:00+07:00",
            "endTime": "2026-04-10T13:00:00+07:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["eventId"] == event.id
    assert body["data"]["title"] == "Python Workshop Updated"
    assert body["data"]["locationName"] == "SCI Building Room 502"
    assert body["data"]["status"] == "DRAFT"


def test_admin_can_update_any_event():
    client = TestClient(app)
    admin = create_user("ADMIN", "admin_update@events.com")
    organizer = create_user("ORGANIZER", "org_update2@events.com")
    category = create_category("Seminar", "กิจกรรมสัมมนา")
    event = create_event(
        title="Organizer Event",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 5, 10, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc),
        status="DRAFT",
    )
    token = create_access_token_for_user(admin)

    response = client.patch(
        f"/api/v1/events/{event.id}",
        json={
            "title": "Admin Updated Title",
            "locationName": "Main Hall",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["eventId"] == event.id
    assert body["data"]["title"] == "Admin Updated Title"
    assert body["data"]["locationName"] == "Main Hall"
    assert body["data"]["status"] == "DRAFT"


def test_organizer_cannot_create_published_event():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_publish_denied@events.com")
    category = create_category("Seminar", "กิจกรรมสัมมนา")

    payload = {
        "title": "Restricted Publish",
        "locationName": "SCI Building Room 501",
        "latitude": 15.120245,
        "longitude": 104.906928,
        "startTime": "2026-04-10T09:00:00+07:00",
        "endTime": "2026-04-10T12:00:00+07:00",
        "categoryId": category.id,
        "status": "PUBLISHED",
    }
    token = create_access_token_for_user(organizer)

    response = client.post(
        "/api/v1/events",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_admin_can_publish_draft_event():
    client = TestClient(app)
    admin = create_user("ADMIN", "admin_publish@events.com")
    organizer = create_user("ORGANIZER", "org_publish@events.com")
    category = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")

    event = create_event(
        title="Draft Workshop",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc),
        status="DRAFT",
    )
    token = create_access_token_for_user(admin)

    response = client.post(
        f"/api/v1/events/{event.id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "PUBLISHED"


def test_admin_can_cancel_event_with_reason():
    client = TestClient(app)
    admin = create_user("ADMIN", "admin_cancel@events.com")
    organizer = create_user("ORGANIZER", "org_cancel@events.com")
    category = create_category("Seminar", "กิจกรรมสัมมนา")

    event = create_event(
        title="Cancelable Event",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc),
        status="PUBLISHED",
    )
    token = create_access_token_for_user(admin)

    response = client.post(
        f"/api/v1/events/{event.id}/cancel",
        json={"reason": "เลื่อนสถานที่จัดงาน"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "CANCELLED"
    assert body["data"]["reason"] == "เลื่อนสถานที่จัดงาน"


def test_get_my_events_as_organizer():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_my_events@events.com")
    category = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")

    # Create events for the organizer
    event1 = create_event(
        title="My Workshop 1",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 4, 10, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 4, 10, 12, 0, tzinfo=timezone.utc),
        status="PUBLISHED",
    )
    event2 = create_event(
        title="My Workshop 2",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 4, 15, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc),
        status="DRAFT",
    )

    # Create event for another organizer
    other_organizer = create_user("ORGANIZER", "other_org@events.com")
    create_event(
        title="Other Workshop",
        category_id=category.id,
        organizer_id=other_organizer.id,
        start_time=datetime(2026, 4, 20, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc),
        status="PUBLISHED",
    )

    token = create_access_token_for_user(organizer)

    response = client.get(
        "/api/v1/events/my-events",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "ดึงรายการกิจกรรมของผู้จัดสำเร็จ"
    assert body["meta"]["totalItems"] == 2
    assert len(body["data"]) == 2
    assert body["data"][0]["title"] in ["My Workshop 1", "My Workshop 2"]
    assert body["data"][1]["title"] in ["My Workshop 1", "My Workshop 2"]


def test_get_my_events_non_organizer_forbidden():
    client = TestClient(app)
    student = create_user("STUDENT", "student_my_events@events.com")
    token = create_access_token_for_user(student)

    response = client.get(
        "/api/v1/events/my-events",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["success"] is False


def test_get_upcoming_events():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_upcoming@events.com")
    category = create_category("Seminar", "กิจกรรมสัมมนา")

    # Create upcoming event (future start time)
    future_time = datetime.now(timezone.utc) + timedelta(days=7)
    upcoming_event = create_event(
        title="Future Seminar",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=future_time,
        end_time=future_time + timedelta(hours=3),
        status="PUBLISHED",
    )

    # Create past event (should not appear)
    past_time = datetime.now(timezone.utc) - timedelta(days=1)
    create_event(
        title="Past Seminar",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=past_time,
        end_time=past_time + timedelta(hours=3),
        status="PUBLISHED",
    )

    response = client.get("/api/v1/events/upcoming")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "ดึงกิจกรรมที่กำลังจะมาถึงสำเร็จ"
    assert body["meta"]["totalItems"] == 1
    assert len(body["data"]) == 1
    assert body["data"][0]["eventId"] == upcoming_event.id
    assert body["data"][0]["title"] == "Future Seminar"


def test_get_active_events():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_active@events.com")
    category = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")

    # Create active event (ongoing)
    now = datetime.now(timezone.utc)
    active_event = create_event(
        title="Ongoing Workshop",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=2),
        status="PUBLISHED",
    )

    # Create ended event (should not appear)
    ended_event = create_event(
        title="Ended Workshop",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=now - timedelta(hours=3),
        end_time=now - timedelta(hours=1),
        status="PUBLISHED",
    )

    response = client.get("/api/v1/events/active")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "ดึงกิจกรรมที่ยัง active สำเร็จ"
    assert body["meta"]["totalItems"] == 1
    assert len(body["data"]) == 1
    assert body["data"][0]["eventId"] == active_event.id
    assert body["data"][0]["title"] == "Ongoing Workshop"


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
