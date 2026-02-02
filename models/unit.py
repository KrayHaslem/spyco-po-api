import uuid
from datetime import datetime, timezone
from db import db


class UnitType:
    VEHICLE = "vehicle"
    TRAILER = "trailer"
    EQUIPMENT = "equipment"
    LOCATION = "location"
    OTHER = "other"

    @classmethod
    def all(cls):
        return [cls.VEHICLE, cls.TRAILER, cls.EQUIPMENT, cls.LOCATION, cls.OTHER]


class Unit(db.Model):
    __tablename__ = "units"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    unit_number = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    unit_type = db.Column(db.String(20), nullable=False, default=UnitType.OTHER)
    department_id = db.Column(
        db.String(36), db.ForeignKey("departments.id"), nullable=True
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

    department = db.relationship("Department", back_populates="units")
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    orders = db.relationship(
        "Order", back_populates="unit", lazy="dynamic"
    )
    repairs = db.relationship(
        "Repair", back_populates="unit", lazy="dynamic"
    )

    def to_dict(self, include_department=False):
        data = {
            "id": self.id,
            "unit_number": self.unit_number,
            "description": self.description,
            "unit_type": self.unit_type,
            "department_id": self.department_id,
            "is_active": self.is_active,
            "created_by_id": self.created_by_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_department and self.department:
            data["department"] = self.department.to_dict()
        return data
