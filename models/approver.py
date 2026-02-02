import uuid
from datetime import datetime, timezone
from db import db


class Approver(db.Model):
    __tablename__ = "approvers"

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
        "User", foreign_keys=[user_id], back_populates="approver"
    )
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    approver_departments = db.relationship(
        "ApproverDepartment",
        back_populates="approver",
        lazy="joined",
        cascade="all, delete-orphan",
    )

    @property
    def departments(self):
        """Get list of departments this approver is assigned to."""
        return [ad.department for ad in self.approver_departments if ad.department]

    @property
    def department_ids(self):
        """Get list of department IDs this approver is assigned to."""
        return [ad.department_id for ad in self.approver_departments]

    @property
    def is_global_approver(self):
        """Returns True if approver has no specific department assignments (approves all)."""
        return len(self.approver_departments) == 0

    def can_approve_for_department(self, department_id):
        """Check if this approver can approve POs from a specific department."""
        if self.is_global_approver:
            return True
        return department_id in self.department_ids

    def to_dict(self, include_user=False, include_departments=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "is_active": self.is_active,
            "is_global_approver": self.is_global_approver,
            "created_by_id": self.created_by_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_user and self.user:
            data["user"] = self.user.to_dict()
        if include_departments:
            data["departments"] = [d.to_dict() for d in self.departments]
            data["department_ids"] = self.department_ids
        return data
