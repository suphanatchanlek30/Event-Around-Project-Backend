# app/seed/seed_data.py

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash


def seed_users(db: Session):
    demo_users = [
        {
            "full_name": "Organizer Demo",
            "email": "organizer@example.com",
            "password_hash": get_password_hash("Password123!"),
            "role": "ORGANIZER",
        }
    ]

    for user_data in demo_users:
        exists = db.query(User).filter(User.email == user_data["email"]).first()
        if not exists:
            db.add(User(**user_data))

    db.commit()


def main():
    db = SessionLocal()
    try:
        seed_users(db)
        print("Seed completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()