import uuid
from datetime import datetime, timezone
from db import db


class ApproverDepartment(db.Model):
    __tablename__ = "approver_departments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    approver_id = db.Column(
        db.String(36), db.ForeignKey("approvers.id"), nullable=False
    )
    department_id = db.Column(
        db.String(36), db.ForeignKey("departments.id"), nullable=False
    )
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint("approver_id", "department_id", name="uq_approver_department"),
    )

    approver = db.relationship("Approver", back_populates="approver_departments")
    department = db.relationship("Department", back_populates="approver_departments")

    def to_dict(self):
        return {
            "id": self.id,
            "approver_id": self.approver_id,
            "department_id": self.department_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
