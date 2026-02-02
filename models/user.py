import uuid
from datetime import datetime, timezone
import bcrypt
from db import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    department_id = db.Column(
        db.String(36), db.ForeignKey("departments.id"), nullable=True
    )
    job_title = db.Column(db.String(100), nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
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

    department = db.relationship("Department", back_populates="users")
    approver = db.relationship(
        "Approver",
        back_populates="user",
        uselist=False,
        lazy="joined",
        foreign_keys="Approver.user_id",
    )
    technician = db.relationship(
        "Technician",
        back_populates="user",
        uselist=False,
        lazy="joined",
        foreign_keys="Technician.user_id",
    )
    orders_ordered = db.relationship(
        "Order",
        foreign_keys="Order.ordered_by_id",
        back_populates="ordered_by",
        lazy="dynamic",
    )
    orders_approved = db.relationship(
        "Order",
        foreign_keys="Order.approved_by_id",
        back_populates="approved_by",
        lazy="dynamic",
    )
    orders_rejected = db.relationship(
        "Order",
        foreign_keys="Order.rejected_by_id",
        back_populates="rejected_by",
        lazy="dynamic",
    )
    repairs_requested = db.relationship(
        "Repair",
        foreign_keys="Repair.requested_by_id",
        back_populates="requested_by",
        lazy="dynamic",
    )
    repairs_approved = db.relationship(
        "Repair",
        foreign_keys="Repair.approved_by_id",
        back_populates="approved_by",
        lazy="dynamic",
    )
    repairs_rejected = db.relationship(
        "Repair",
        foreign_keys="Repair.rejected_by_id",
        back_populates="rejected_by",
        lazy="dynamic",
    )
    repairs_completed = db.relationship(
        "Repair",
        foreign_keys="Repair.completed_by_id",
        back_populates="completed_by",
        lazy="dynamic",
    )

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    @property
    def is_approver(self):
        return self.approver is not None and self.approver.is_active

    @property
    def is_technician(self):
        return self.technician is not None and self.technician.is_active

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self, include_department=False):
        data = {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "phone": self.phone,
            "department_id": self.department_id,
            "job_title": self.job_title,
            "is_admin": self.is_admin,
            "is_approver": self.is_approver,
            "is_technician": self.is_technician,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_department and self.department:
            data["department"] = self.department.to_dict()
        return data
