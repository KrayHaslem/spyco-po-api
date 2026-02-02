import uuid
from datetime import datetime, timezone
from db import db


class OrderStatus:
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"

    @classmethod
    def all(cls):
        return [cls.DRAFT, cls.PENDING, cls.APPROVED, cls.REJECTED, cls.PAID]


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    vendor_id = db.Column(
        db.String(36), db.ForeignKey("vendors.id"), nullable=False
    )
    unit_id = db.Column(
        db.String(36), db.ForeignKey("units.id"), nullable=True
    )
    po_group_id = db.Column(
        db.String(36), db.ForeignKey("po_groups.id"), nullable=True
    )
    description = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=OrderStatus.DRAFT)
    ordered_by_id = db.Column(
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

    vendor = db.relationship("Vendor", back_populates="orders")
    unit = db.relationship("Unit", back_populates="orders")
    po_group = db.relationship("POGroup", back_populates="orders")
    ordered_by = db.relationship(
        "User",
        foreign_keys=[ordered_by_id],
        back_populates="orders_ordered",
    )
    approved_by = db.relationship(
        "User",
        foreign_keys=[approved_by_id],
        back_populates="orders_approved",
    )
    rejected_by = db.relationship(
        "User",
        foreign_keys=[rejected_by_id],
        back_populates="orders_rejected",
    )
    items = db.relationship(
        "OrderItem",
        back_populates="order",
        lazy="joined",
        cascade="all, delete-orphan",
        order_by="OrderItem.line_number",
    )

    @staticmethod
    def generate_order_number():
        """Generate a unique order number."""
        now = datetime.now(timezone.utc)
        prefix = now.strftime("ORD-%Y%m%d")
        
        existing = Order.query.filter(
            Order.order_number.like(f"{prefix}%")
        ).count()
        
        return f"{prefix}-{existing + 1:04d}"

    @property
    def total(self):
        """Calculate total from items that have pricing."""
        total = 0
        for item in self.items:
            if item.quantity is not None and item.unit_cost is not None:
                total += item.quantity * item.unit_cost
        return total

    def to_dict(self, include_relations=False):
        data = {
            "id": self.id,
            "order_number": self.order_number,
            "vendor_id": self.vendor_id,
            "unit_id": self.unit_id,
            "po_group_id": self.po_group_id,
            "description": self.description,
            "status": self.status,
            "ordered_by_id": self.ordered_by_id,
            "approved_by_id": self.approved_by_id,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_by_id": self.rejected_by_id,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "rejection_comment": self.rejection_comment,
            "notes": self.notes,
            "total": self.total,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_relations:
            data["vendor"] = self.vendor.to_dict() if self.vendor else None
            data["unit"] = self.unit.to_dict() if self.unit else None
            data["po_group"] = self.po_group.to_dict() if self.po_group else None
            data["ordered_by"] = self.ordered_by.to_dict() if self.ordered_by else None
            data["approved_by"] = self.approved_by.to_dict() if self.approved_by else None
            data["rejected_by"] = self.rejected_by.to_dict() if self.rejected_by else None
            data["items"] = [item.to_dict() for item in self.items]
        return data
