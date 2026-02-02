import uuid
from datetime import datetime, timezone
from db import db


class POGroup(db.Model):
    __tablename__ = "po_groups"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    po_number = db.Column(db.String(100), unique=True, nullable=False)
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

    orders = db.relationship("Order", back_populates="po_group", lazy="dynamic")
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    @property
    def order_count(self):
        """Get the count of orders in this PO Group."""
        return self.orders.count()

    @property
    def total(self):
        """Calculate total from all orders in this PO Group."""
        total = 0
        for order in self.orders:
            total += order.total
        return total

    def to_dict(self, include_orders=False):
        data = {
            "id": self.id,
            "po_number": self.po_number,
            "created_by_id": self.created_by_id,
            "created_by": self.created_by.to_dict() if self.created_by else None,
            "order_count": self.order_count,
            "total": self.total,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_orders:
            data["orders"] = [order.to_dict(include_relations=True) for order in self.orders]
        return data
