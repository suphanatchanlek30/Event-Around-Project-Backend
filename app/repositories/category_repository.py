from app.models.event_category import EventCategory
from sqlalchemy import func
from sqlalchemy.orm import Session


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_categories(self, include_inactive: bool = False) -> list[EventCategory]:
        query = self.db.query(EventCategory)
        if not include_inactive:
            query = query.filter(EventCategory.is_active.is_(True))

        return query.order_by(EventCategory.name.asc()).all()

    def get_by_id(self, category_id: int) -> EventCategory | None:
        return self.db.query(EventCategory).filter(EventCategory.id == category_id).first()

    def get_by_name(self, name: str) -> EventCategory | None:
        return (
            self.db.query(EventCategory)
            .filter(func.lower(EventCategory.name) == name.strip().lower())
            .first()
        )

    def create(self, name: str, description: str | None = None) -> EventCategory:
        category = EventCategory(name=name, description=description, is_active=True)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category: EventCategory, name: str | None = None, description: str | None = None) -> EventCategory:
        if name is not None:
            category.name = name
        if description is not None:
            category.description = description

        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def deactivate(self, category: EventCategory) -> EventCategory:
        category.is_active = False
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
