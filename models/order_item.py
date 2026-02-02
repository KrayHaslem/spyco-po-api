import uuid
from datetime import datetime, timezone
from db import db


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = db.Column(
        db.String(36), db.ForeignKey("orders.id"), nullable=False
    )
    line_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=True)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    order = db.relationship("Order", back_populates="items")

    @property
    def total(self):
        """Calculate line item total if quantity and unit_cost are provided."""
        if self.quantity is not None and self.unit_cost is not None:
            return float(self.quantity) * float(self.unit_cost)
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "line_number": self.line_number,
            "description": self.description,
            "quantity": float(self.quantity) if self.quantity is not None else None,
            "unit_cost": float(self.unit_cost) if self.unit_cost is not None else None,
            "total": self.total,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
