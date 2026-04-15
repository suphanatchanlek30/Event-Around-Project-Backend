from app.core.exceptions import bad_request, conflict, forbidden, not_found
from app.domain.event_category import EventCategory as DomainEventCategory
from app.models.event_category import EventCategory
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreateRequest, CategoryUpdateRequest
from sqlalchemy.orm import Session


class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.category_repo = CategoryRepository(db)

    def _ensure_manage_permission(self, current_user: User) -> None:
        if current_user.role not in {"ADMIN", "ORGANIZER"}:
            raise forbidden("ไม่มีสิทธิ์จัดการหมวดหมู่")

    def _to_domain_category(self, category: EventCategory) -> DomainEventCategory:
        return DomainEventCategory(
            category_id=category.id,
            name=category.name,
            description=category.description,
            is_active=category.is_active,
        )

    def _to_response_data(self, category: EventCategory) -> dict:
        return {
            "categoryId": category.id,
            "name": category.name,
            "description": category.description,
            "isActive": category.is_active,
        }

    def _parse_include_inactive(self, include_inactive: str | None) -> bool:
        if include_inactive is None:
            return False

        normalized = include_inactive.strip().lower()
        if normalized in {"true", "1"}:
            return True
        if normalized in {"false", "0"}:
            return False

        raise bad_request(
            message="ข้อมูล query ไม่ถูกต้อง",
            errors=[
                {
                    "field": "includeInactive",
                    "code": "INVALID_QUERY",
                    "detail": "includeInactive ต้องเป็น true/false หรือ 1/0",
                }
            ],
        )

    def _ensure_name_unique(self, name: str, excluded_category_id: int | None = None) -> None:
        existed = self.category_repo.get_by_name(name)
        if existed is None:
            return
        if excluded_category_id is not None and existed.id == excluded_category_id:
            return

        raise conflict(
            message="ชื่อหมวดหมู่นี้ถูกใช้งานแล้ว",
            errors=[
                {
                    "field": "name",
                    "code": "CATEGORY_NAME_DUPLICATE",
                    "detail": "กรุณาใช้ชื่อหมวดหมู่อื่น",
                }
            ],
        )

    def list_categories(self, include_inactive: str | None):
        include_inactive_bool = self._parse_include_inactive(include_inactive)
        categories = self.category_repo.list_categories(include_inactive=include_inactive_bool)

        return {
            "success": True,
            "message": "ดึงหมวดหมู่สำเร็จ",
            "data": [self._to_response_data(category) for category in categories],
        }

    def create_category(self, payload: CategoryCreateRequest, current_user: User):
        self._ensure_manage_permission(current_user)

        domain_category = DomainEventCategory(category_id=0, name=payload.name)
        domain_category.set_name(payload.name)

        self._ensure_name_unique(domain_category.get_name())

        created = self.category_repo.create(
            name=domain_category.get_name(),
            description=payload.description,
        )

        return {
            "success": True,
            "message": "สร้างหมวดหมู่สำเร็จ",
            "data": self._to_response_data(created),
        }

    def get_category_detail(self, category_id: int):
        category = self.category_repo.get_by_id(category_id)
        if category is None:
            raise not_found("ไม่พบหมวดหมู่ที่ต้องการ")

        return {
            "success": True,
            "message": "ดึงรายละเอียดหมวดหมู่สำเร็จ",
            "data": self._to_response_data(category),
        }

    def update_category(self, category_id: int, payload: CategoryUpdateRequest, current_user: User):
        self._ensure_manage_permission(current_user)

        if payload.name is None and payload.description is None:
            raise bad_request(
                message="ข้อมูลไม่ถูกต้อง",
                errors=[
                    {
                        "field": "body",
                        "code": "EMPTY_UPDATE_PAYLOAD",
                        "detail": "ต้องระบุ name หรือ description อย่างน้อย 1 ฟิลด์",
                    }
                ],
            )

        category = self.category_repo.get_by_id(category_id)
        if category is None:
            raise not_found("ไม่พบหมวดหมู่ที่ต้องการ")

        domain_category = self._to_domain_category(category)
        next_name = category.name
        if payload.name is not None:
            domain_category.set_name(payload.name)
            next_name = domain_category.get_name()
            self._ensure_name_unique(next_name, excluded_category_id=category.id)

        updated = self.category_repo.update(
            category=category,
            name=next_name if payload.name is not None else None,
            description=payload.description,
        )

        return {
            "success": True,
            "message": "แก้ไขหมวดหมู่สำเร็จ",
            "data": self._to_response_data(updated),
        }

    def deactivate_category(self, category_id: int, current_user: User):
        self._ensure_manage_permission(current_user)

        category = self.category_repo.get_by_id(category_id)
        if category is None:
            raise not_found("ไม่พบหมวดหมู่ที่ต้องการ")

        domain_category = self._to_domain_category(category)
        domain_category.deactivate()

        if category.is_active:
            category = self.category_repo.deactivate(category)

        return {
            "success": True,
            "message": "ปิดใช้งานหมวดหมู่สำเร็จ",
            "data": {
                "categoryId": category.id,
                "isActive": category.is_active,
            },
        }
