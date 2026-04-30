from app.core.settings import settings
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def _set_postgres_timezone(dbapi_connection, connection_record) -> None:
    if engine.dialect.name != "postgresql":
        return

    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SET TIME ZONE 'UTC'")
    finally:
        cursor.close()


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