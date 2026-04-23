from datetime import UTC, datetime, timedelta

from app.core.database import Base, get_db
from app.core.security import create_access_token
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
    latitude: float = 14.87,
    longitude: float = 102.01,
) -> Event:
    db = TestingSessionLocal()
    try:
        event = Event(
            title=title,
            description=description,
            short_description=short_description,
            location_name=location_name,
            latitude=latitude,
            longitude=longitude,
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


def create_import_log(
    organizer_id: int,
    total_records: int,
    success_records: int,
    failed_records: int,
    default_status: str | None = None,
    file_name: str | None = None,
) -> EventImportLog:
    db = TestingSessionLocal()
    try:
        import_log = EventImportLog(
            organizer_id=organizer_id,
            total_records=total_records,
            success_records=success_records,
            failed_records=failed_records,
            default_status=default_status,
            file_name=file_name,
        )
        db.add(import_log)
        db.commit()
        db.refresh(import_log)
        return import_log
    finally:
        db.close()


def create_access_token_for_user(user: User) -> str:
    token, _ = create_access_token(user.id, user.role)
    return token


def test_list_events_returns_published_only_and_meta():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org@events.com")
    category = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")

    start_time = datetime(2026, 4, 10, 9, 0, tzinfo=UTC)
    end_time = datetime(2026, 4, 10, 12, 0, tzinfo=UTC)
    create_event(
        title="Python Workshop",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=start_time,
        end_time=end_time,
        status="PUBLISHED",
        cover_image_url="https://example.com/python-workshop.jpg",
        short_description="เรียน Python แบบลงมือทำ",
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
    assert body["data"][0]["description"] == ""
    assert body["data"][0]["coverImageUrl"] == "https://example.com/python-workshop.jpg"
    assert body["data"][0]["shortDescription"] == "เรียน Python แบบลงมือทำ"


def test_get_event_detail_published_event_returns_detail():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_detail@events.com")
    category = create_category("Seminar", "กิจกรรมสัมมนา")
    start_time = datetime(2026, 5, 10, 9, 0, tzinfo=UTC)
    end_time = datetime(2026, 5, 10, 12, 0, tzinfo=UTC)
    event = create_event(
        title="Data Science Seminar",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=start_time,
        end_time=end_time,
        status="PUBLISHED",
        description="A seminar about data science.",
        cover_image_url="https://example.com/data-science.jpg",
    )

    response = client.get(f"/api/v1/events/{event.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["eventId"] == event.id
    assert body["data"]["title"] == "Data Science Seminar"
    assert body["data"]["coverImageUrl"] == "https://example.com/data-science.jpg"
    assert body["data"]["cancelReason"] is None
    assert body["data"]["savedCount"] == 0
    assert body["data"]["isSaved"] is False


def test_get_my_events_includes_cover_image_url():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "myevents_org@example.com")
    category = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")
    create_event(
        title="Owner Event",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 4, 15, 9, 0, tzinfo=UTC),
        end_time=datetime(2026, 4, 15, 12, 0, tzinfo=UTC),
        status="PUBLISHED",
        cover_image_url="https://example.com/owner-event.jpg",
    )
    token = create_access_token_for_user(organizer)

    response = client.get(
        "/api/v1/events/my-events",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"][0]["coverImageUrl"] == "https://example.com/owner-event.jpg"
    assert body["data"][0]["locationName"] == "SCI Building Room 501"
    assert body["data"][0]["category"]["name"] == "Workshop"
    assert body["data"][0]["organizer"]["userId"] == organizer.id


def test_get_upcoming_events_includes_cover_image_url():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "upcoming_org@example.com")
    category = create_category("Hackathon", "กิจกรรมแข่งขัน")
    now = datetime.now(UTC)
    create_event(
        title="Upcoming Hackathon",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=now + timedelta(days=5),
        end_time=now + timedelta(days=5, hours=3),
        status="PUBLISHED",
        cover_image_url="https://example.com/upcoming.jpg",
    )

    response = client.get("/api/v1/events/upcoming")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"][0]["coverImageUrl"] == "https://example.com/upcoming.jpg"
    assert body["data"][0]["category"]["name"] == "Hackathon"
    assert body["data"][0]["organizer"]["userId"] == organizer.id
    assert "savedCount" in body["data"][0]


def test_get_active_events_includes_cover_image_url():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "active_org@example.com")
    category = create_category("Seminar", "กิจกรรมสัมมนา")
    now = datetime.now(UTC)
    create_event(
        title="Active Seminar",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=2),
        status="PUBLISHED",
        cover_image_url="https://example.com/active.jpg",
    )

    response = client.get("/api/v1/events/active")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"][0]["coverImageUrl"] == "https://example.com/active.jpg"
    assert body["data"][0]["category"]["name"] == "Seminar"
    assert body["data"][0]["organizer"]["userId"] == organizer.id
    assert "savedCount" in body["data"][0]


def test_get_nearby_events_includes_cover_image_url():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "nearby_org@example.com")
    category = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")
    create_event(
        title="Nearby Event",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 4, 20, 9, 0, tzinfo=UTC),
        end_time=datetime(2026, 4, 20, 12, 0, tzinfo=UTC),
        status="PUBLISHED",
        cover_image_url="https://example.com/nearby.jpg",
        latitude=15.120245,
        longitude=104.906928,
    )

    response = client.get(
        "/api/v1/events/nearby?latitude=15.120100&longitude=104.905800&radiusKm=5"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"][0]["coverImageUrl"] == "https://example.com/nearby.jpg"
    assert body["data"][0]["status"] == "PUBLISHED"
    assert body["data"][0]["organizer"]["userId"] == organizer.id


def test_get_map_events_includes_cover_image_url():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "map_org@example.com")
    category = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")
    create_event(
        title="Map Event",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 4, 20, 9, 0, tzinfo=UTC),
        end_time=datetime(2026, 4, 20, 12, 0, tzinfo=UTC),
        status="PUBLISHED",
        cover_image_url="https://example.com/map.jpg",
        latitude=15.120245,
        longitude=104.906928,
    )

    response = client.get(
        "/api/v1/events/map?latitude=15.120100&longitude=104.905800&radiusKm=5"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"][0]["coverImageUrl"] == "https://example.com/map.jpg"
    assert body["data"][0]["status"] == "PUBLISHED"
    assert body["data"][0]["category"]["name"] == "Workshop"


def test_get_event_detail_returns_is_saved_for_student():
    client = TestClient(app)
    student = create_user("STUDENT", "student@example.com")
    organizer = create_user("ORGANIZER", "org_event@events.com")
    category = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")
    start_time = datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
    end_time = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
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
    start_time = datetime(2026, 7, 1, 9, 0, tzinfo=UTC)
    end_time = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
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
        start_time=datetime(2026, 4, 10, 9, 0, tzinfo=UTC),
        end_time=datetime(2026, 4, 10, 12, 0, tzinfo=UTC),
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
        start_time=datetime(2026, 5, 10, 9, 0, tzinfo=UTC),
        end_time=datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
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
        start_time=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
        end_time=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
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
        start_time=datetime(2026, 9, 1, 9, 0, tzinfo=UTC),
        end_time=datetime(2026, 9, 1, 12, 0, tzinfo=UTC),
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


def test_import_events_csv_creates_events_and_returns_import_log():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_import@events.com")
    create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")
    create_category("Seminar", "กิจกรรมสัมมนา")

    token = create_access_token_for_user(organizer)
    csv_content = (
        "title,description,shortDescription,locationName,latitude,longitude,startTime,endTime,categoryId,coverImageUrl,status\n"
        "Python Bootcamp,หลักสูตรเข้มข้น,เวิร์กชอป,Main Hall,15.0,100.0,2026-05-01T09:00:00+07:00,2026-05-01T12:00:00+07:00,1,https://example.com/image.jpg,DRAFT\n"
        "Invalid Time Event,,สั้น,Main Hall,15.0,100.0,2026-05-01T12:00:00+07:00,2026-05-01T10:00:00+07:00,1,,\n"
    )

    response = client.post(
        "/api/v1/import/events/csv",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("events.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["totalRecords"] == 2
    assert body["data"]["successRecords"] == 1
    assert body["data"]["failedRecords"] == 1
    assert body["data"]["importLogId"] > 0
    assert body["data"]["errors"][0]["row"] == 3


def test_import_events_json_creates_events_and_returns_import_log():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_import_json@events.com")
    category = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")

    token = create_access_token_for_user(organizer)
    payload = {
        "events": [
            {
                "title": "Python Workshop",
                "description": "เวิร์กชอป Python",
                "shortDescription": "ลงมือทำ",
                "locationName": "SCI 501",
                "latitude": 15.120245,
                "longitude": 104.906928,
                "startTime": "2026-04-10T09:00:00+07:00",
                "endTime": "2026-04-10T12:00:00+07:00",
                "categoryId": category.id,
                "status": "DRAFT"
            }
        ]
    }

    response = client.post(
        "/api/v1/import/events/json",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["totalRecords"] == 1
    assert body["data"]["successRecords"] == 1
    assert body["data"]["failedRecords"] == 0
    assert body["data"]["importLogId"] > 0
    assert body["data"]["errors"] == []


def test_import_events_csv_returns_failed_records_when_category_not_found():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_import_csv_invalid_category@events.com")

    token = create_access_token_for_user(organizer)
    csv_content = (
        "title,description,shortDescription,locationName,latitude,longitude,startTime,endTime,categoryId,coverImageUrl,status\n"
        "Row One,desc,short,Main Hall,15.0,100.0,2026-05-01T09:00:00+07:00,2026-05-01T12:00:00+07:00,99999,,DRAFT\n"
        "Row Two,desc,short,Main Hall,15.0,100.0,2026-05-02T09:00:00+07:00,2026-05-02T12:00:00+07:00,99998,,DRAFT\n"
    )

    response = client.post(
        "/api/v1/import/events/csv",
        headers={"Authorization": f"Bearer {token}"},
        data={"defaultStatus": "DRAFT"},
        files={"file": ("events_invalid_category.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["totalRecords"] == 2
    assert body["data"]["successRecords"] == 0
    assert body["data"]["failedRecords"] == 2
    assert body["data"]["importLogId"] > 0
    assert len(body["data"]["errors"]) == 2
    assert body["data"]["errors"][0]["row"] == 2
    assert body["data"]["errors"][0]["field"] == "categoryId"
    assert body["data"]["errors"][0]["detail"] == "ไม่พบหมวดหมู่ที่ต้องการ"
    assert body["data"]["errors"][1]["row"] == 3
    assert body["data"]["errors"][1]["field"] == "categoryId"
    assert body["data"]["errors"][1]["detail"] == "ไม่พบหมวดหมู่ที่ต้องการ"


def test_import_events_json_returns_failed_records_when_category_not_found():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_import_json_invalid_category@events.com")

    token = create_access_token_for_user(organizer)
    payload = {
        "events": [
            {
                "title": "Python Workshop",
                "description": "เวิร์กชอป Python",
                "shortDescription": "ลงมือทำ",
                "locationName": "SCI 501",
                "latitude": 15.120245,
                "longitude": 104.906928,
                "startTime": "2026-04-10T09:00:00+07:00",
                "endTime": "2026-04-10T12:00:00+07:00",
                "categoryId": 99999,
                "status": "DRAFT",
            }
        ]
    }

    response = client.post(
        "/api/v1/import/events/json",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["totalRecords"] == 1
    assert body["data"]["successRecords"] == 0
    assert body["data"]["failedRecords"] == 1
    assert body["data"]["importLogId"] > 0
    assert len(body["data"]["errors"]) == 1
    assert body["data"]["errors"][0]["row"] == 1
    assert body["data"]["errors"][0]["field"] == "categoryId"
    assert body["data"]["errors"][0]["detail"] == "ไม่พบหมวดหมู่ที่ต้องการ"


def test_get_import_history_as_organizer_returns_only_own_logs():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "organizer_history@events.com")
    other_organizer = create_user("ORGANIZER", "other_history@events.com")
    create_import_log(
        organizer_id=organizer.id,
        total_records=3,
        success_records=2,
        failed_records=1,
        default_status="DRAFT",
        file_name="my-events.csv",
    )
    create_import_log(
        organizer_id=other_organizer.id,
        total_records=4,
        success_records=4,
        failed_records=0,
        default_status="PUBLISHED",
        file_name="other-events.csv",
    )
    token = create_access_token_for_user(organizer)

    response = client.get(
        "/api/v1/import/history",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "ดึงประวัติการนำเข้าสำเร็จ"
    assert body["meta"]["totalItems"] == 1
    assert len(body["data"]) == 1
    assert body["meta"]["summary"]["type"]["csv"] == 1
    assert body["meta"]["summary"]["type"]["json"] == 0
    assert body["meta"]["summary"]["status"]["partialSuccess"] == 1
    assert body["data"][0]["fileName"] == "my-events.csv"
    assert body["data"][0]["importNo"] == f"#{body['data'][0]['importLogId']}"
    assert body["data"][0]["importType"] == "CSV"
    assert body["data"][0]["defaultStatus"] == "DRAFT"
    assert body["data"][0]["status"] == "PARTIAL_SUCCESS"
    assert body["data"][0]["statusLabel"] == "มีข้อผิดพลาด"
    assert body["data"][0]["statusTone"] == "warning"
    assert body["data"][0]["hasErrors"] is True
    assert body["data"][0]["metrics"]["processedRecords"] == 3
    assert body["data"][0]["metrics"]["pendingRecords"] == 0
    assert body["data"][0]["metrics"]["successRate"] == 66.67
    assert body["data"][0]["source"]["type"] == "CSV"
    assert body["data"][0]["display"]["importId"] == f"#{body['data'][0]['importLogId']}"
    assert body["data"][0]["importedBy"]["userId"] == organizer.id


def test_get_import_history_as_admin_returns_all_logs_latest_first():
    client = TestClient(app)
    admin = create_user("ADMIN", "admin_history@events.com")
    organizer = create_user("ORGANIZER", "organizer_history_admin@events.com")
    first_log = create_import_log(
        organizer_id=organizer.id,
        total_records=2,
        success_records=2,
        failed_records=0,
        default_status="DRAFT",
        file_name="first.csv",
    )
    second_log = create_import_log(
        organizer_id=admin.id,
        total_records=5,
        success_records=4,
        failed_records=1,
        default_status=None,
        file_name=None,
    )
    token = create_access_token_for_user(admin)

    response = client.get(
        "/api/v1/import/history",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["meta"]["totalItems"] == 2
    assert body["meta"]["summary"]["type"]["csv"] == 1
    assert body["meta"]["summary"]["type"]["json"] == 1
    assert body["meta"]["summary"]["status"]["success"] == 1
    assert body["meta"]["summary"]["status"]["partialSuccess"] == 1
    assert len(body["data"]) == 2
    assert body["data"][0]["importLogId"] == second_log.id
    assert body["data"][1]["importLogId"] == first_log.id
    assert body["data"][0]["importType"] == "JSON"
    assert body["data"][0]["status"] == "PARTIAL_SUCCESS"
    assert body["data"][0]["importedBy"]["role"] == "ADMIN"
    assert body["data"][1]["importType"] == "CSV"
    assert body["data"][1]["status"] == "SUCCESS"
    assert body["data"][1]["statusLabel"] == "สำเร็จ"
    assert body["data"][1]["statusTone"] == "success"
    assert body["data"][1]["importedBy"]["role"] == "ORGANIZER"


def test_get_import_history_student_forbidden():
    client = TestClient(app)
    student = create_user("STUDENT", "student_history@events.com")
    token = create_access_token_for_user(student)

    response = client.get(
        "/api/v1/import/history",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["success"] is False


def test_get_my_events_as_organizer():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_my_events@events.com")
    category = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")

    # Create events for the organizer
    create_event(
        title="My Workshop 1",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 4, 10, 9, 0, tzinfo=UTC),
        end_time=datetime(2026, 4, 10, 12, 0, tzinfo=UTC),
        status="PUBLISHED",
    )
    create_event(
        title="My Workshop 2",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 4, 15, 9, 0, tzinfo=UTC),
        end_time=datetime(2026, 4, 15, 12, 0, tzinfo=UTC),
        status="DRAFT",
    )

    # Create event for another organizer
    other_organizer = create_user("ORGANIZER", "other_org@events.com")
    create_event(
        title="Other Workshop",
        category_id=category.id,
        organizer_id=other_organizer.id,
        start_time=datetime(2026, 4, 20, 9, 0, tzinfo=UTC),
        end_time=datetime(2026, 4, 20, 12, 0, tzinfo=UTC),
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
    future_time = datetime.now(UTC) + timedelta(days=7)
    upcoming_event = create_event(
        title="Future Seminar",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=future_time,
        end_time=future_time + timedelta(hours=3),
        status="PUBLISHED",
    )

    # Create past event (should not appear)
    past_time = datetime.now(UTC) - timedelta(days=1)
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
    now = datetime.now(UTC)
    active_event = create_event(
        title="Ongoing Workshop",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=2),
        status="PUBLISHED",
    )

    # Create ended event (should not appear)
    create_event(
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

    create_event(
        title="Python Workshop",
        category_id=workshop.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 4, 10, 9, 0, tzinfo=UTC),
        end_time=datetime(2026, 4, 10, 12, 0, tzinfo=UTC),
        status="PUBLISHED",
    )
    create_event(
        title="Java Seminar",
        category_id=seminar.id,
        organizer_id=organizer.id,
        start_time=datetime(2026, 4, 15, 9, 0, tzinfo=UTC),
        end_time=datetime(2026, 4, 15, 11, 0, tzinfo=UTC),
        status="PUBLISHED",
    )

    response = client.get(
        f"/api/v1/events?search=python&categoryId={workshop.id}&status=PUBLISHED&startFrom=2026-04-01T00:00:00Z&endTo=2026-04-30T23:59:59Z&sortBy=startTime&sortOrder=asc",
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


def test_get_nearby_events():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_nearby@events.com")
    category = create_category("Workshop", "กิจกรรมฝึกปฏิบัติ")

    # Create event with specific location
    future_time = datetime.now(UTC) + timedelta(days=7)
    event = create_event(
        title="Nearby Workshop",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=future_time,
        end_time=future_time + timedelta(hours=3),
        status="PUBLISHED",
        latitude=15.120245,
        longitude=104.906928,
    )

    # Test nearby with location close to event
    response = client.get("/api/v1/events/nearby?latitude=15.120100&longitude=104.905800&radiusKm=5&sortBy=startTime&sortOrder=asc")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "ดึงกิจกรรมใกล้ตัวสำเร็จ"
    assert len(body["data"]) == 1
    assert body["data"][0]["eventId"] == event.id
    assert "distanceKm" in body["data"][0]
    assert body["meta"]["totalItems"] == 1


def test_get_nearby_events_invalid_coordinates():
    client = TestClient(app)
    response = client.get("/api/v1/events/nearby?latitude=100&longitude=104.905800&radiusKm=5")
    assert response.status_code == 400
    assert response.json()["success"] is False


def test_get_map_events():
    client = TestClient(app)
    organizer = create_user("ORGANIZER", "org_map@events.com")
    category = create_category("Seminar", "กิจกรรมสัมมนา")

    # Create event with specific location
    future_time = datetime.now(UTC) + timedelta(days=7)
    event = create_event(
        title="Map Seminar",
        category_id=category.id,
        organizer_id=organizer.id,
        start_time=future_time,
        end_time=future_time + timedelta(hours=3),
        status="PUBLISHED",
        latitude=15.120245,
        longitude=104.906928,
    )

    response = client.get("/api/v1/events/map?latitude=15.120100&longitude=104.905800&radiusKm=5")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "ดึงข้อมูลแผนที่สำเร็จ"
    assert len(body["data"]) == 1
    assert body["data"][0]["eventId"] == event.id
    assert "distanceKm" in body["data"][0]
