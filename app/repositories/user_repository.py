# app/repositories/user_repository.py

from app.models.user import User
from sqlalchemy.orm import Session


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def create_student(self, full_name: str, email: str, password_hash: str) -> User:
        return self.create_user(
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            role="STUDENT",
        )

    def create_organizer(self, full_name: str, email: str, password_hash: str) -> User:
        return self.create_user(
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            role="ORGANIZER",
        )

    def create_user(self, full_name: str, email: str, password_hash: str, role: str) -> User:
        user = User(
            full_name=full_name,
            email=email.lower(),
            password_hash=password_hash,
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_profile(self, user: User, full_name: str | None = None, profile_image_url: str | None = None) -> User:
        if full_name is not None:
            user.full_name = full_name
        if profile_image_url is not None:
            user.profile_image_url = profile_image_url

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_password(self, user: User, password_hash: str) -> User:
        user.password_hash = password_hash
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user