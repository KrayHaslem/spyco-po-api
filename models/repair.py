import uuid
from datetime import datetime, timezone
from db import db


class RepairStatus:
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

    @classmethod
    def all(cls):
        return [cls.DRAFT, cls.PENDING, cls.APPROVED, cls.REJECTED, cls.COMPLETED]


class Repair(db.Model):
    __tablename__ = "repairs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repair_number = db.Column(db.String(50), unique=True, nullable=False)
    unit_id = db.Column(
        db.String(36), db.ForeignKey("units.id"), nullable=False
    )
    description = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=RepairStatus.DRAFT)
    requested_by_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=False
    )
    approved_by_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=True
    )
    approved_at = db.Column(db.DateTime, nullable=True)
    rejected_by_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=True
    )
    rejected_at = db.Column(db.DateTime, nullable=True)
    rejection_comment = db.Column(db.Text, nullable=True)
    completed_by_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=True
    )
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    unit = db.relationship("Unit", back_populates="repairs")
    requested_by = db.relationship(
        "User",
        foreign_keys=[requested_by_id],
        back_populates="repairs_requested",
    )
    approved_by = db.relationship(
        "User",
        foreign_keys=[approved_by_id],
        back_populates="repairs_approved",
    )
    rejected_by = db.relationship(
        "User",
        foreign_keys=[rejected_by_id],
        back_populates="repairs_rejected",
    )
    completed_by = db.relationship(
        "User",
        foreign_keys=[completed_by_id],
        back_populates="repairs_completed",
    )
    items = db.relationship(
        "RepairItem",
        back_populates="repair",
        lazy="joined",
        cascade="all, delete-orphan",
        order_by="RepairItem.line_number",
    )

    @staticmethod
    def generate_repair_number():
        """Generate a unique repair number."""
        now = datetime.now(timezone.utc)
        prefix = now.strftime("REP-%Y%m%d")
        
        existing = Repair.query.filter(
            Repair.repair_number.like(f"{prefix}%")
        ).count()
        
        return f"{prefix}-{existing + 1:04d}"

    def to_dict(self, include_relations=False):
        data = {
            "id": self.id,
            "repair_number": self.repair_number,
            "unit_id": self.unit_id,
            "description": self.description,
            "status": self.status,
            "requested_by_id": self.requested_by_id,
            "approved_by_id": self.approved_by_id,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_by_id": self.rejected_by_id,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "rejection_comment": self.rejection_comment,
            "completed_by_id": self.completed_by_id,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_relations:
            data["unit"] = self.unit.to_dict() if self.unit else None
            data["requested_by"] = self.requested_by.to_dict() if self.requested_by else None
            data["approved_by"] = self.approved_by.to_dict() if self.approved_by else None
            data["rejected_by"] = self.rejected_by.to_dict() if self.rejected_by else None
            data["completed_by"] = self.completed_by.to_dict() if self.completed_by else None
            data["items"] = [item.to_dict() for item in self.items]
        return data
