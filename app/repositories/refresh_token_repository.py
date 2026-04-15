from datetime import datetime

from app.models.refresh_token import RefreshToken
from sqlalchemy.orm import Session


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, token_hash: str, expires_at: datetime) -> RefreshToken:
        row = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_active_by_hash(self, token_hash: str) -> RefreshToken | None:
        now = datetime.utcnow()
        return (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .filter(RefreshToken.revoked_at.is_(None))
            .filter(RefreshToken.expires_at > now)
            .first()
        )

    def revoke_by_hash(self, token_hash: str) -> None:
        row = self.db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if row is not None and row.revoked_at is None:
            row.revoked_at = datetime.utcnow()
            self.db.add(row)
            self.db.commit()

    def revoke_all_for_user(self, user_id: int) -> None:
        rows = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id)
            .filter(RefreshToken.revoked_at.is_(None))
            .all()
        )
        now = datetime.utcnow()
        changed = False
        for row in rows:
            row.revoked_at = now
            self.db.add(row)
            changed = True

        if changed:
            self.db.commit()
