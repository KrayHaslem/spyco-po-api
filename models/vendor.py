import uuid
from datetime import datetime, timezone
from db import db


class Vendor(db.Model):
    __tablename__ = "vendors"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    contact_info = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    orders = db.relationship(
        "Order", back_populates="vendor", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "contact_info": self.contact_info,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
