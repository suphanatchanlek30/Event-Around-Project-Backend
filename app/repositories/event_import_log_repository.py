from sqlalchemy.orm import Session

from app.models.event_import_log import EventImportLog


class EventImportLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        organizer_id: int,
        total_records: int,
        success_records: int,
        failed_records: int,
        default_status: str | None = None,
        file_name: str | None = None,
    ) -> EventImportLog:
        log = EventImportLog(
            organizer_id=organizer_id,
            total_records=total_records,
            success_records=success_records,
            failed_records=failed_records,
            default_status=default_status,
            file_name=file_name,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
