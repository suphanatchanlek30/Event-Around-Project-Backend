# app/repositories/user_repository.py

from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def create_student(self, full_name: str, email: str, password_hash: str) -> User:
        user = User(
            full_name=full_name,
            email=email.lower(),
            password_hash=password_hash,
            role="STUDENT",
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user