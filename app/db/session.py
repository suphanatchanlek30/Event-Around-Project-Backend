from app.core.settings import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()