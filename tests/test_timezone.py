from datetime import UTC, datetime, timedelta

from app.core.database import Base, get_db
from app.core.security import create_access_token, create_refresh_token
from app.core.timezone import (
    convert_bangkok_to_utc,
    convert_utc_to_bangkok,
    format_datetime_for_api,
    get_now_bangkok,
)
from app.main import app
from app.models.event import Event
from app.models.event_category import EventCategory
from app.models.event_import_log import EventImportLog
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
        category = EventCategory(name=name, description="กิจกรรมทดสอบ", is_active=True)
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
) -> Event:
    db = TestingSessionLocal()
    try:
        event = Event(
            title=title,
            description="รายละเอียดกิจกรรม",
            short_description="สรุปสั้น",
            location_name="SCI Building",
            latitude=15.120245,
            longitude=104.906928,
            start_time=start_time,
            end_time=end_time,
            status=status,
            category_id=category_id,
            organizer_id=organizer_id,
            cover_image_url="https://example.com/event.jpg",
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


def create_import_log(organizer_id: int) -> EventImportLog:
    db = TestingSessionLocal()
    try:
        log = EventImportLog(
            organizer_id=organizer_id,
            total_records=3,
            success_records=2,
            failed_records=1,
            default_status="DRAFT",
            file_name="events.csv",
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    finally:
        db.close()


def token_for(user: User) -> str:
    token, _ = create_access_token(user.id, user.role)
    return token


def test_timezone_utilities_use_bangkok_and_round_trip_utc():
    bangkok_now = get_now_bangkok()
    assert bangkok_now.utcoffset() == timedelta(hours=7)

    bangkok_time = datetime(2026, 4, 10, 9, 0)
    utc_time = convert_bangkok_to_utc(bangkok_time)
    assert utc_time.isoformat() == "2026-04-10T02:00:00+00:00"

    converted_back = convert_utc_to_bangkok(utc_time)
    assert converted_back.isoformat() == "2026-04-10T09:00:00+07:00"
    assert format_datetime_for_api(utc_time) == "2026-04-10T09:00:00+07:00"


def test_refresh_token_expiration_stays_utc_aware():
    _, expires_at = create_refresh_token(user_id=1, role="STUDENT")
    assert expires_at.tzinfo is not None
    assert expires_at.utcoffset() == timedelta(0)


def test_health_and_auth_responses_use_bangkok_timezone():
    client = TestClient(app)
    student = create_user("STUDENT", "timezone-auth@example.com")
    token = token_for(student)

    health_response = client.get("/api/v1/health")
    assert health_response.status_code == 200
    assert health_response.json()["data"]["serverTime"].endswith("+07:00")

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()["data"]
    assert me_data["createdAt"].endswith("+07:00")
    assert me_data["updatedAt"].endswith("+07:00")


def test_event_related_endpoints_respond_with_bangkok_time_and_naive_input_stores_utc():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "timezone-organizer@example.com")
    student = create_user("STUDENT", "timezone-student@example.com")
    category = create_category()
    event = create_event(
        title="Bangkok Event",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 4, 10, 2, 0, tzinfo=UTC),
        end_time=datetime(2026, 4, 10, 5, 0, tzinfo=UTC),
    )
    create_event_save(event.id, student.id)

    organizer_token = token_for(organizer)
    student_token = token_for(student)

    list_response = client.get("/api/v1/events")
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["startTime"] == "2026-04-10T09:00:00+07:00"
    assert list_response.json()["data"][0]["endTime"] == "2026-04-10T12:00:00+07:00"

    detail_response = client.get(f"/api/v1/events/{event.id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["startTime"] == "2026-04-10T09:00:00+07:00"
    assert detail_response.json()["data"]["endTime"] == "2026-04-10T12:00:00+07:00"

    my_events_response = client.get(
        "/api/v1/events/my-events",
        headers={"Authorization": f"Bearer {organizer_token}"},
    )
    assert my_events_response.status_code == 200
    assert my_events_response.json()["data"][0]["startTime"] == "2026-04-10T09:00:00+07:00"

    nearby_response = client.get(
        "/api/v1/events/nearby?latitude=15.120100&longitude=104.905800&radiusKm=5"
    )
    assert nearby_response.status_code == 200
    assert nearby_response.json()["data"][0]["startTime"] == "2026-04-10T09:00:00+07:00"

    map_response = client.get(
        "/api/v1/events/map?latitude=15.120100&longitude=104.905800&radiusKm=5"
    )
    assert map_response.status_code == 200
    assert map_response.json()["data"][0]["startTime"] == "2026-04-10T09:00:00+07:00"

    saved_response = client.get(
        "/api/v1/saved-events",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert saved_response.status_code == 200
    saved_item = saved_response.json()["data"][0]
    assert saved_item["startTime"] == "2026-04-10T09:00:00+07:00"
    assert saved_item["endTime"] == "2026-04-10T12:00:00+07:00"
    assert saved_item["savedAt"].endswith("+07:00")

    organizer_stats_response = client.get(
        f"/api/v1/organizer/events/{event.id}/stats",
        headers={"Authorization": f"Bearer {organizer_token}"},
    )
    assert organizer_stats_response.status_code == 200
    assert organizer_stats_response.json()["data"]["startTime"] == "2026-04-10T09:00:00+07:00"

    create_response = client.post(
        "/api/v1/events",
        json={
            "title": "Naive Bangkok Input",
            "description": "created from naive bangkok time",
            "locationName": "SCI Building Room 501",
            "latitude": 15.120245,
            "longitude": 104.906928,
            "startTime": "2026-04-11T09:00:00",
            "endTime": "2026-04-11T12:00:00",
            "categoryId": category.id,
            "status": "DRAFT",
        },
        headers={"Authorization": f"Bearer {organizer_token}"},
    )
    assert create_response.status_code == 201

    db = TestingSessionLocal()
    try:
        created_event = db.query(Event).filter(Event.title == "Naive Bangkok Input").one()
        assert created_event.start_time.isoformat() == "2026-04-11T02:00:00+00:00"
        assert created_event.end_time.isoformat() == "2026-04-11T05:00:00+00:00"
    finally:
        db.close()


def test_category_and_import_history_responses_use_bangkok_timezone():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "timezone-category@example.com")
    create_import_log(organizer.id)
    token = token_for(organizer)

    category_response = client.get("/api/v1/categories")
    assert category_response.status_code == 200
    category_data = category_response.json()["data"]
    assert category_data == []

    created_category_response = client.post(
        "/api/v1/categories",
        json={"name": "Timezone Category", "description": "tz"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert created_category_response.status_code == 201
    created_category_data = created_category_response.json()["data"]
    assert created_category_data["createdAt"].endswith("+07:00")
    assert created_category_data["updatedAt"].endswith("+07:00")

    history_response = client.get(
        "/api/v1/import/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert history_response.status_code == 200
    assert history_response.json()["data"][0]["createdAt"].endswith("+07:00")