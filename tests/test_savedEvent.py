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
	status: str = "PUBLISHED",
) -> Event:
	db = TestingSessionLocal()
	try:
		event = Event(
			title=title,
			description="รายละเอียดกิจกรรม",
			short_description="คำอธิบายสั้น",
			location_name="SCI Building",
			latitude=15.120245,
			longitude=104.906928,
			start_time=datetime(2026, 4, 10, 9, 0, tzinfo=UTC),
			end_time=datetime(2026, 4, 10, 12, 0, tzinfo=UTC),
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


def count_event_saves(event_id: int, user_id: int) -> int:
	db = TestingSessionLocal()
	try:
		return db.query(EventSave).filter(EventSave.event_id == event_id, EventSave.user_id == user_id).count()
	finally:
		db.close()


def create_access_token_for_user(user: User) -> str:
	token, _ = create_access_token(user.id, user.role)
	return token


def test_save_event_success_for_student_returns_201_and_persists():
	client = TestClient(app)
	student = create_user("STUDENT", "student_save_success@example.com")
	organizer = create_user("ORGANIZER", "org_save_success@example.com")
	category = create_category("Workshop")
	event = create_event(
		title="Python Workshop",
		category_id=category.id,
		organizer_id=organizer.id,
		status="PUBLISHED",
	)
	token = create_access_token_for_user(student)

	response = client.post(
		"/api/v1/saved-events",
		json={"eventId": event.id},
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 201
	body = response.json()
	assert body["success"] is True
	assert body["message"] == "บันทึกกิจกรรมสำเร็จ"
	assert body["data"]["eventId"] == event.id
	assert body["data"]["saved"] is True
	assert count_event_saves(event.id, student.id) == 1


def test_save_event_without_token_returns_401():
	client = TestClient(app)
	organizer = create_user("ORGANIZER", "org_save_no_token@example.com")
	category = create_category("Seminar")
	event = create_event(
		title="Seminar",
		category_id=category.id,
		organizer_id=organizer.id,
		status="PUBLISHED",
	)

	response = client.post(
		"/api/v1/saved-events",
		json={"eventId": event.id},
	)

	assert response.status_code == 401
	body = response.json()
	assert body["success"] is False
	assert body["message"] == "ไม่ได้รับสิทธิ์การเข้าถึง"


def test_save_event_as_organizer_returns_403():
	client = TestClient(app)
	organizer = create_user("ORGANIZER", "org_save_forbidden@example.com")
	another_organizer = create_user("ORGANIZER", "org_owner@example.com")
	category = create_category("Hackathon")
	event = create_event(
		title="Hackathon",
		category_id=category.id,
		organizer_id=another_organizer.id,
		status="PUBLISHED",
	)
	token = create_access_token_for_user(organizer)

	response = client.post(
		"/api/v1/saved-events",
		json={"eventId": event.id},
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 403
	body = response.json()
	assert body["success"] is False
	assert body["message"] == "เฉพาะ STUDENT เท่านั้นที่สามารถบันทึกกิจกรรมได้"


def test_save_event_as_admin_returns_403():
	client = TestClient(app)
	admin = create_user("ADMIN", "admin_save_forbidden@example.com")
	organizer = create_user("ORGANIZER", "org_admin_case@example.com")
	category = create_category("Talk")
	event = create_event(
		title="Tech Talk",
		category_id=category.id,
		organizer_id=organizer.id,
		status="PUBLISHED",
	)
	token = create_access_token_for_user(admin)

	response = client.post(
		"/api/v1/saved-events",
		json={"eventId": event.id},
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 403
	body = response.json()
	assert body["success"] is False
	assert body["message"] == "เฉพาะ STUDENT เท่านั้นที่สามารถบันทึกกิจกรรมได้"


def test_save_event_not_found_returns_404():
	client = TestClient(app)
	student = create_user("STUDENT", "student_not_found@example.com")
	token = create_access_token_for_user(student)

	response = client.post(
		"/api/v1/saved-events",
		json={"eventId": 99999},
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 404
	body = response.json()
	assert body["success"] is False
	assert body["message"] == "ไม่พบกิจกรรม"


def test_save_event_duplicate_returns_409_and_does_not_duplicate_row():
	client = TestClient(app)
	student = create_user("STUDENT", "student_duplicate@example.com")
	organizer = create_user("ORGANIZER", "org_duplicate@example.com")
	category = create_category("Workshop")
	event = create_event(
		title="Duplicate Save Event",
		category_id=category.id,
		organizer_id=organizer.id,
		status="PUBLISHED",
	)
	create_event_save(event.id, student.id)
	token = create_access_token_for_user(student)

	response = client.post(
		"/api/v1/saved-events",
		json={"eventId": event.id},
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 409
	body = response.json()
	assert body["success"] is False
	assert body["message"] == "กิจกรรมนี้ถูกบันทึกแล้ว"
	assert count_event_saves(event.id, student.id) == 1


def test_save_event_allows_draft_event_for_student_current_behavior():
	client = TestClient(app)
	student = create_user("STUDENT", "student_draft_save@example.com")
	organizer = create_user("ORGANIZER", "org_draft_save@example.com")
	category = create_category("Internal")
	event = create_event(
		title="Draft Internal Event",
		category_id=category.id,
		organizer_id=organizer.id,
		status="DRAFT",
	)
	token = create_access_token_for_user(student)

	response = client.post(
		"/api/v1/saved-events",
		json={"eventId": event.id},
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 201
	body = response.json()
	assert body["success"] is True
	assert body["message"] == "บันทึกกิจกรรมสำเร็จ"
	assert body["data"]["eventId"] == event.id
	assert body["data"]["saved"] is True
	assert count_event_saves(event.id, student.id) == 1


def test_save_event_missing_event_id_returns_422():
	client = TestClient(app)
	student = create_user("STUDENT", "student_missing_field@example.com")
	token = create_access_token_for_user(student)

	response = client.post(
		"/api/v1/saved-events",
		json={},
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 422
	body = response.json()
	assert "detail" in body


def test_save_event_zero_event_id_returns_422():
	client = TestClient(app)
	student = create_user("STUDENT", "student_zero_event_id@example.com")
	token = create_access_token_for_user(student)

	response = client.post(
		"/api/v1/saved-events",
		json={"eventId": 0},
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 422
	body = response.json()
	assert "detail" in body


def test_save_event_negative_event_id_returns_422():
	client = TestClient(app)
	student = create_user("STUDENT", "student_negative_event_id@example.com")
	token = create_access_token_for_user(student)

	response = client.post(
		"/api/v1/saved-events",
		json={"eventId": -1},
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 422
	body = response.json()
	assert "detail" in body


# ─── GET /api/v1/saved-events ────────────────────────────────────────────────


def test_get_saved_events_success_returns_list_with_meta():
	client = TestClient(app)
	student = create_user("STUDENT", "student_get_saved@example.com")
	organizer = create_user("ORGANIZER", "org_get_saved@example.com")
	category = create_category("Workshop")
	event = create_event(
		title="Saved Workshop",
		category_id=category.id,
		organizer_id=organizer.id,
		status="PUBLISHED",
	)
	create_event_save(event.id, student.id)
	token = create_access_token_for_user(student)

	response = client.get(
		"/api/v1/saved-events",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 200
	body = response.json()
	assert body["success"] is True
	assert body["message"] == "ดึงรายการกิจกรรมที่บันทึกไว้สำเร็จ"
	assert len(body["data"]) == 1
	assert body["data"][0]["eventId"] == event.id
	assert body["data"][0]["title"] == "Saved Workshop"
	assert body["data"][0]["status"] == "PUBLISHED"
	assert "savedAt" in body["data"][0]
	assert body["meta"]["totalItems"] == 1
	assert body["meta"]["page"] == 1


def test_get_saved_events_empty_when_no_saves():
	client = TestClient(app)
	student = create_user("STUDENT", "student_get_empty@example.com")
	token = create_access_token_for_user(student)

	response = client.get(
		"/api/v1/saved-events",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 200
	body = response.json()
	assert body["success"] is True
	assert body["data"] == []
	assert body["meta"]["totalItems"] == 0


def test_get_saved_events_filter_by_status():
	client = TestClient(app)
	student = create_user("STUDENT", "student_filter_status@example.com")
	organizer = create_user("ORGANIZER", "org_filter_status@example.com")
	category = create_category("Seminar")
	published_event = create_event(
		title="Published Event",
		category_id=category.id,
		organizer_id=organizer.id,
		status="PUBLISHED",
	)
	draft_event = create_event(
		title="Draft Event",
		category_id=category.id,
		organizer_id=organizer.id,
		status="DRAFT",
	)
	create_event_save(published_event.id, student.id)
	create_event_save(draft_event.id, student.id)
	token = create_access_token_for_user(student)

	response = client.get(
		"/api/v1/saved-events?status=PUBLISHED",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 200
	body = response.json()
	assert body["meta"]["totalItems"] == 1
	assert body["data"][0]["status"] == "PUBLISHED"


def test_get_saved_events_pagination():
	client = TestClient(app)
	student = create_user("STUDENT", "student_pagination@example.com")
	organizer = create_user("ORGANIZER", "org_pagination@example.com")
	category = create_category("Talk")
	for i in range(3):
		event = create_event(
			title=f"Event {i}",
			category_id=category.id,
			organizer_id=organizer.id,
			status="PUBLISHED",
		)
		create_event_save(event.id, student.id)
	token = create_access_token_for_user(student)

	response = client.get(
		"/api/v1/saved-events?page=1&pageSize=2",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 200
	body = response.json()
	assert len(body["data"]) == 2
	assert body["meta"]["totalItems"] == 3
	assert body["meta"]["totalPages"] == 2
	assert body["meta"]["pageSize"] == 2


def test_get_saved_events_sort_by_saved_at_desc():
	client = TestClient(app)
	student = create_user("STUDENT", "student_sort_saved_at@example.com")
	organizer = create_user("ORGANIZER", "org_sort_saved_at@example.com")
	category = create_category("Hackathon")
	event_a = create_event(
		title="Event A",
		category_id=category.id,
		organizer_id=organizer.id,
		status="PUBLISHED",
	)
	event_b = create_event(
		title="Event B",
		category_id=category.id,
		organizer_id=organizer.id,
		status="PUBLISHED",
	)
	create_event_save(event_a.id, student.id)
	create_event_save(event_b.id, student.id)
	token = create_access_token_for_user(student)

	response = client.get(
		"/api/v1/saved-events?sortBy=savedAt&sortOrder=desc",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 200
	body = response.json()
	assert len(body["data"]) == 2
	# Most recently saved (event_b) should come first
	assert body["data"][0]["eventId"] == event_b.id


def test_get_saved_events_invalid_status_returns_400():
	client = TestClient(app)
	student = create_user("STUDENT", "student_bad_status@example.com")
	token = create_access_token_for_user(student)

	response = client.get(
		"/api/v1/saved-events?status=INVALID",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 400
	body = response.json()
	assert body["success"] is False


def test_get_saved_events_without_token_returns_401():
	client = TestClient(app)

	response = client.get("/api/v1/saved-events")

	assert response.status_code == 401
	body = response.json()
	assert body["success"] is False


def test_get_saved_events_as_organizer_returns_403():
	client = TestClient(app)
	organizer = create_user("ORGANIZER", "org_get_forbidden@example.com")
	token = create_access_token_for_user(organizer)

	response = client.get(
		"/api/v1/saved-events",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 403
	body = response.json()
	assert body["success"] is False
	assert body["message"] == "เฉพาะ STUDENT เท่านั้นที่สามารถดูรายการกิจกรรมที่บันทึกไว้"


def test_get_saved_events_as_admin_returns_403():
	client = TestClient(app)
	admin = create_user("ADMIN", "admin_get_forbidden@example.com")
	token = create_access_token_for_user(admin)

	response = client.get(
		"/api/v1/saved-events",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 403
	body = response.json()
	assert body["success"] is False
	assert body["message"] == "เฉพาะ STUDENT เท่านั้นที่สามารถดูรายการกิจกรรมที่บันทึกไว้"


# ─────────── DELETE /api/v1/saved-events/{eventId} ───────────

def test_unsave_event_success():
	client = TestClient(app)
	organizer = create_user("ORGANIZER", "org_unsave@example.com")
	student = create_user("STUDENT", "student_unsave@example.com")
	category = create_category()
	event = create_event("Event Unsave", category.id, organizer.id)
	create_event_save(event.id, student.id)
	token = create_access_token_for_user(student)

	response = client.delete(
		f"/api/v1/saved-events/{event.id}",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 200
	body = response.json()
	assert body["success"] is True
	assert body["message"] == "ยกเลิกบันทึกกิจกรรมสำเร็จ"
	assert body["data"]["eventId"] == event.id
	assert body["data"]["saved"] is False


def test_unsave_event_removes_from_db():
	client = TestClient(app)
	organizer = create_user("ORGANIZER", "org_unsave_db@example.com")
	student = create_user("STUDENT", "student_unsave_db@example.com")
	category = create_category()
	event = create_event("Event Unsave DB", category.id, organizer.id)
	create_event_save(event.id, student.id)
	token = create_access_token_for_user(student)

	assert count_event_saves(event.id, student.id) == 1

	client.delete(
		f"/api/v1/saved-events/{event.id}",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert count_event_saves(event.id, student.id) == 0


def test_unsave_event_without_token_returns_401():
	client = TestClient(app)

	response = client.delete("/api/v1/saved-events/1")

	assert response.status_code == 401


def test_unsave_event_as_organizer_returns_403():
	client = TestClient(app)
	organizer = create_user("ORGANIZER", "org_unsave_403@example.com")
	token = create_access_token_for_user(organizer)

	response = client.delete(
		"/api/v1/saved-events/1",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 403
	body = response.json()
	assert body["success"] is False
	assert body["message"] == "เฉพาะ STUDENT เท่านั้นที่สามารถยกเลิกบันทึกกิจกรรมได้"


def test_unsave_event_as_admin_returns_403():
	client = TestClient(app)
	admin = create_user("ADMIN", "admin_unsave_403@example.com")
	token = create_access_token_for_user(admin)

	response = client.delete(
		"/api/v1/saved-events/1",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 403
	body = response.json()
	assert body["success"] is False
	assert body["message"] == "เฉพาะ STUDENT เท่านั้นที่สามารถยกเลิกบันทึกกิจกรรมได้"


def test_unsave_event_not_saved_returns_404():
	client = TestClient(app)
	organizer = create_user("ORGANIZER", "org_unsave_404@example.com")
	student = create_user("STUDENT", "student_unsave_404@example.com")
	category = create_category()
	event = create_event("Event Not Saved", category.id, organizer.id)
	token = create_access_token_for_user(student)

	response = client.delete(
		f"/api/v1/saved-events/{event.id}",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 404
	body = response.json()
	assert body["success"] is False
	assert body["message"] == "ไม่พบกิจกรรมที่บันทึกไว้"


# ─────────── GET /api/v1/saved-events/check/{eventId} ───────────

def test_check_saved_event_is_saved_returns_true():
	client = TestClient(app)
	organizer = create_user("ORGANIZER", "org_check_saved@example.com")
	student = create_user("STUDENT", "student_check_saved@example.com")
	category = create_category()
	event = create_event("Event Check Saved", category.id, organizer.id)
	create_event_save(event.id, student.id)
	token = create_access_token_for_user(student)

	response = client.get(
		f"/api/v1/saved-events/check/{event.id}",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 200
	body = response.json()
	assert body["success"] is True
	assert body["message"] == "ตรวจสอบสถานะการบันทึกสำเร็จ"
	assert body["data"]["eventId"] == event.id
	assert body["data"]["isSaved"] is True


def test_check_saved_event_not_saved_returns_false():
	client = TestClient(app)
	organizer = create_user("ORGANIZER", "org_check_unsaved@example.com")
	student = create_user("STUDENT", "student_check_unsaved@example.com")
	category = create_category()
	event = create_event("Event Check Not Saved", category.id, organizer.id)
	token = create_access_token_for_user(student)

	response = client.get(
		f"/api/v1/saved-events/check/{event.id}",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 200
	body = response.json()
	assert body["success"] is True
	assert body["data"]["eventId"] == event.id
	assert body["data"]["isSaved"] is False


def test_check_saved_event_without_token_returns_401():
	client = TestClient(app)

	response = client.get("/api/v1/saved-events/check/1")

	assert response.status_code == 401


def test_check_saved_event_as_organizer_returns_403():
	client = TestClient(app)
	organizer = create_user("ORGANIZER", "org_check_403@example.com")
	token = create_access_token_for_user(organizer)

	response = client.get(
		"/api/v1/saved-events/check/1",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 403
	body = response.json()
	assert body["success"] is False
	assert body["message"] == "เฉพาะ STUDENT เท่านั้นที่สามารถตรวจสอบสถานะการบันทึกได้"


def test_check_saved_event_as_admin_returns_403():
	client = TestClient(app)
	admin = create_user("ADMIN", "admin_check_403@example.com")
	token = create_access_token_for_user(admin)

	response = client.get(
		"/api/v1/saved-events/check/1",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 403
	body = response.json()
	assert body["success"] is False
	assert body["message"] == "เฉพาะ STUDENT เท่านั้นที่สามารถตรวจสอบสถานะการบันทึกได้"


def test_check_saved_event_event_not_found_returns_404():
	client = TestClient(app)
	student = create_user("STUDENT", "student_check_404@example.com")
	token = create_access_token_for_user(student)

	response = client.get(
		"/api/v1/saved-events/check/99999",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 404
	body = response.json()
	assert body["success"] is False
	assert body["message"] == "ไม่พบกิจกรรม"
