import uuid
from datetime import datetime, timezone
from db import db


class Technician(db.Model):
    __tablename__ = "technicians"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), unique=True, nullable=False
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_by_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=True
    )
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship(
        "User", foreign_keys=[user_id], back_populates="technician"
    )
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    def to_dict(self, include_user=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "is_active": self.is_active,
            "created_by_id": self.created_by_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_user and self.user:
            data["user"] = self.user.to_dict()
        return data
