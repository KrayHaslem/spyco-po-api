import uuid
from datetime import datetime, timezone
from db import db


class RepairItem(db.Model):
    __tablename__ = "repair_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repair_id = db.Column(
        db.String(36), db.ForeignKey("repairs.id"), nullable=False
    )
    line_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    repair = db.relationship("Repair", back_populates="items")

    def to_dict(self):
        return {
            "id": self.id,
            "repair_id": self.repair_id,
            "line_number": self.line_number,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
