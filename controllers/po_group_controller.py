from flask import request, jsonify
from db import db
from models.po_group import POGroup
from models.order import Order, OrderStatus


def get_po_groups(current_user):
    """Get all PO Groups (admin only)."""
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403

    po_groups = POGroup.query.order_by(POGroup.created_at.desc()).all()
    return jsonify([pg.to_dict() for pg in po_groups])


def get_po_group(po_group_id, current_user):
    """Get a single PO Group with its orders."""
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403

    po_group = POGroup.query.get(po_group_id)
    if not po_group:
        return jsonify({"error": "PO Group not found"}), 404

    return jsonify(po_group.to_dict(include_orders=True))


def create_po_group(current_user):
    """Create a new PO Group."""
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if not data.get("po_number"):
        return jsonify({"error": "PO number is required"}), 400

    # Check if PO number already exists
    existing = POGroup.query.filter_by(po_number=data["po_number"]).first()
    if existing:
        return jsonify({"error": "PO number already exists"}), 400

    po_group = POGroup(
        po_number=data["po_number"],
        created_by_id=current_user.id,
    )

    db.session.add(po_group)
    db.session.commit()

    return jsonify(po_group.to_dict()), 201


def update_po_group(po_group_id, current_user):
    """Update a PO Group's PO number."""
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403

    po_group = POGroup.query.get(po_group_id)
    if not po_group:
        return jsonify({"error": "PO Group not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "po_number" in data:
        if not data["po_number"]:
            return jsonify({"error": "PO number is required"}), 400

        # Check if new PO number already exists (excluding current)
        existing = POGroup.query.filter(
            POGroup.po_number == data["po_number"],
            POGroup.id != po_group_id
        ).first()
        if existing:
            return jsonify({"error": "PO number already exists"}), 400

        po_group.po_number = data["po_number"]

    db.session.commit()

    return jsonify(po_group.to_dict())


def delete_po_group(po_group_id, current_user):
    """Delete a PO Group (only if no orders are assigned)."""
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403

    po_group = POGroup.query.get(po_group_id)
    if not po_group:
        return jsonify({"error": "PO Group not found"}), 404

    # Check if any orders are assigned
    if po_group.order_count > 0:
        return jsonify({"error": "Cannot delete PO Group with assigned orders. Remove orders first."}), 400

    db.session.delete(po_group)
    db.session.commit()

    return jsonify({"message": "PO Group deleted"})


def add_orders_to_po_group(po_group_id, current_user):
    """Add orders to a PO Group."""
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403

    po_group = POGroup.query.get(po_group_id)
    if not po_group:
        return jsonify({"error": "PO Group not found"}), 404

    data = request.get_json()
    if not data or not data.get("order_ids"):
        return jsonify({"error": "Order IDs are required"}), 400

    order_ids = data["order_ids"]
    if not isinstance(order_ids, list):
        order_ids = [order_ids]

    added = []
    errors = []

    for order_id in order_ids:
        order = Order.query.get(order_id)
        if not order:
            errors.append(f"Order {order_id} not found")
            continue

        if order.status not in (OrderStatus.APPROVED, OrderStatus.PAID):
            errors.append(f"Order {order.order_number} is not approved or paid")
            continue

        if order.po_group_id and order.po_group_id != po_group_id:
            errors.append(f"Order {order.order_number} is already in another PO Group")
            continue

        if order.po_group_id == po_group_id:
            errors.append(f"Order {order.order_number} is already in this PO Group")
            continue

        order.po_group_id = po_group_id
        added.append(order.order_number)

    db.session.commit()

    result = {
        "message": f"Added {len(added)} order(s) to PO Group",
        "added": added,
        "po_group": po_group.to_dict(),
    }

    if errors:
        result["errors"] = errors

    return jsonify(result)


def remove_order_from_po_group(po_group_id, order_id, current_user):
    """Remove an order from a PO Group."""
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403

    po_group = POGroup.query.get(po_group_id)
    if not po_group:
        return jsonify({"error": "PO Group not found"}), 404

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.po_group_id != po_group_id:
        return jsonify({"error": "Order is not in this PO Group"}), 400

    order.po_group_id = None
    db.session.commit()

    return jsonify({
        "message": f"Order {order.order_number} removed from PO Group",
        "po_group": po_group.to_dict(),
    })


def get_available_orders_for_po_group(current_user):
    """Get approved or paid orders that are not yet assigned to any PO Group."""
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403

    orders = Order.query.filter(
        Order.status.in_([OrderStatus.APPROVED, OrderStatus.PAID]),
        Order.po_group_id.is_(None)
    ).order_by(Order.approved_at.desc()).all()

    return jsonify([order.to_dict(include_relations=True) for order in orders])
