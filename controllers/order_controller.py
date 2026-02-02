from datetime import datetime, timezone
from flask import request, jsonify
from db import db
from models.order import Order, OrderStatus
from models.order_item import OrderItem
from models.approver import Approver
from models.vendor import Vendor
from models.unit import Unit


def get_orders(current_user):
    """Get orders for current user (their own or ones they can approve)."""
    # Get orders created by the user
    user_orders = Order.query.filter_by(ordered_by_id=current_user.id).all()

    # If user is an approver, also get pending orders they can approve
    approver_orders = []
    if current_user.is_approver:
        approver = Approver.query.filter_by(user_id=current_user.id).first()
        if approver:
            pending_orders = Order.query.filter_by(status=OrderStatus.PENDING).all()
            for order in pending_orders:
                # Check if approver can approve based on department
                if order.ordered_by and approver.can_approve_for_department(order.ordered_by.department_id):
                    if order not in user_orders:
                        approver_orders.append(order)

    all_orders = user_orders + approver_orders
    return jsonify([order.to_dict(include_relations=True) for order in all_orders])


def get_all_orders(current_user):
    """Get all orders (admin sees all, approvers see their departments)."""
    from models.user import User

    # Build base query
    query = Order.query

    # Apply filters from query params
    status = request.args.get("status")
    if status and status in OrderStatus.all():
        query = query.filter_by(status=status)

    owner_id = request.args.get("owner_id")
    if owner_id:
        query = query.filter_by(ordered_by_id=owner_id)

    vendor_id = request.args.get("vendor_id")
    if vendor_id:
        query = query.filter_by(vendor_id=vendor_id)

    # If admin, return all matching orders
    if current_user.is_admin:
        orders = query.order_by(Order.created_at.desc()).all()
        return jsonify([order.to_dict(include_relations=True) for order in orders])

    # If approver, filter by departments they can approve
    if current_user.is_approver:
        approver = Approver.query.filter_by(user_id=current_user.id).first()
        if approver:
            # Global approvers see all
            if approver.is_global_approver:
                orders = query.order_by(Order.created_at.desc()).all()
                return jsonify([order.to_dict(include_relations=True) for order in orders])

            # Department-scoped approvers see only their departments
            department_ids = approver.department_ids
            if department_ids:
                # Join with User to filter by department
                query = query.join(User, Order.ordered_by_id == User.id)
                query = query.filter(User.department_id.in_(department_ids))
                orders = query.order_by(Order.created_at.desc()).all()
                return jsonify([order.to_dict(include_relations=True) for order in orders])

    # Not authorized
    return jsonify({"error": "Access denied"}), 403


def get_order(order_id, current_user):
    """Get a single order."""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    # Check access: user must be the creator or an approver who can approve it
    can_access = (
        order.ordered_by_id == current_user.id or
        current_user.is_admin
    )

    if not can_access and current_user.is_approver:
        approver = Approver.query.filter_by(user_id=current_user.id).first()
        if approver and approver.can_approve_for_department(order.ordered_by.department_id):
            can_access = True

    if not can_access:
        return jsonify({"error": "Access denied"}), 403

    return jsonify(order.to_dict(include_relations=True))


def create_order(current_user):
    """Create a new order."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate required fields
    if not data.get("vendor_id"):
        return jsonify({"error": "Vendor is required"}), 400
    if not data.get("description"):
        return jsonify({"error": "Description is required"}), 400

    # Validate vendor exists
    vendor = Vendor.query.get(data["vendor_id"])
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404

    # Validate unit if provided
    if data.get("unit_id"):
        unit = Unit.query.get(data["unit_id"])
        if not unit:
            return jsonify({"error": "Unit not found"}), 404

    # Create order
    order = Order(
        order_number=Order.generate_order_number(),
        vendor_id=data["vendor_id"],
        unit_id=data.get("unit_id"),
        description=data["description"],
        status=OrderStatus.DRAFT,
        ordered_by_id=current_user.id,
        notes=data.get("notes"),
    )

    db.session.add(order)
    db.session.flush()

    # Add line items
    items = data.get("items", [])
    for idx, item_data in enumerate(items):
        if not item_data.get("description"):
            continue

        item = OrderItem(
            order_id=order.id,
            line_number=idx + 1,
            description=item_data["description"],
            quantity=item_data.get("quantity"),
            unit_cost=item_data.get("unit_cost"),
        )
        db.session.add(item)

    db.session.commit()

    return jsonify(order.to_dict(include_relations=True)), 201


def update_order(order_id, current_user):
    """Update an order (drafts and rejected orders can be updated by creator)."""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.ordered_by_id != current_user.id:
        return jsonify({"error": "Only the creator can edit this order"}), 403

    if order.status not in (OrderStatus.DRAFT, OrderStatus.REJECTED):
        return jsonify({"error": "Only draft or rejected orders can be edited"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update basic fields
    if "vendor_id" in data:
        vendor = Vendor.query.get(data["vendor_id"])
        if not vendor:
            return jsonify({"error": "Vendor not found"}), 404
        order.vendor_id = data["vendor_id"]

    if "unit_id" in data:
        if data["unit_id"]:
            unit = Unit.query.get(data["unit_id"])
            if not unit:
                return jsonify({"error": "Unit not found"}), 404
        order.unit_id = data["unit_id"]

    if "description" in data:
        order.description = data["description"]
    if "notes" in data:
        order.notes = data["notes"]

    # Update items if provided
    if "items" in data:
        # Remove existing items
        OrderItem.query.filter_by(order_id=order.id).delete()

        # Add new items
        for idx, item_data in enumerate(data["items"]):
            if not item_data.get("description"):
                continue

            item = OrderItem(
                order_id=order.id,
                line_number=idx + 1,
                description=item_data["description"],
                quantity=item_data.get("quantity"),
                unit_cost=item_data.get("unit_cost"),
            )
            db.session.add(item)

    db.session.commit()

    return jsonify(order.to_dict(include_relations=True))


def delete_order(order_id, current_user):
    """Delete an order (only drafts can be deleted)."""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.ordered_by_id != current_user.id and not current_user.is_admin:
        return jsonify({"error": "Only the creator or admin can delete this order"}), 403

    if order.status != OrderStatus.DRAFT:
        return jsonify({"error": "Only draft orders can be deleted"}), 400

    db.session.delete(order)
    db.session.commit()

    return jsonify({"message": "Order deleted"})


def submit_order(order_id, current_user):
    """Submit an order for approval (draft or re-submit after rejection)."""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.ordered_by_id != current_user.id:
        return jsonify({"error": "Only the creator can submit this order"}), 403

    if order.status not in (OrderStatus.DRAFT, OrderStatus.REJECTED):
        return jsonify({"error": "Only draft or rejected orders can be submitted"}), 400

    if len(order.items) == 0:
        return jsonify({"error": "Order must have at least one item"}), 400

    # Find approvers who can approve this order
    approvers = get_approvers_for_order(order)
    if not approvers:
        return jsonify({"error": "No approvers configured for your department"}), 400

    order.status = OrderStatus.PENDING
    db.session.commit()

    return jsonify({
        "message": "Order submitted for approval",
        "order": order.to_dict(include_relations=True),
        "approvers": [a.to_dict(include_user=True) for a in approvers],
    })


def approve_order(order_id, current_user):
    """Approve an order."""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.status != OrderStatus.PENDING:
        return jsonify({"error": "Only pending orders can be approved"}), 400

    # Check if user is an approver who can approve this order
    if not current_user.is_approver:
        return jsonify({"error": "You are not an approver"}), 403

    approver = Approver.query.filter_by(user_id=current_user.id).first()
    if not approver or not approver.can_approve_for_department(order.ordered_by.department_id):
        return jsonify({"error": "You cannot approve orders from this department"}), 403

    order.status = OrderStatus.APPROVED
    order.approved_by_id = current_user.id
    order.approved_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "message": "Order approved",
        "order": order.to_dict(include_relations=True),
    })


def reject_order(order_id, current_user):
    """Reject an order."""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.status != OrderStatus.PENDING:
        return jsonify({"error": "Only pending orders can be rejected"}), 400

    # Check if user is an approver who can reject this order
    if not current_user.is_approver:
        return jsonify({"error": "You are not an approver"}), 403

    approver = Approver.query.filter_by(user_id=current_user.id).first()
    if not approver or not approver.can_approve_for_department(order.ordered_by.department_id):
        return jsonify({"error": "You cannot reject orders from this department"}), 403

    data = request.get_json() or {}

    order.status = OrderStatus.REJECTED
    order.rejected_by_id = current_user.id
    order.rejected_at = datetime.now(timezone.utc)
    order.rejection_comment = data.get("comment", "")
    db.session.commit()

    return jsonify({
        "message": "Order rejected",
        "order": order.to_dict(include_relations=True),
    })


def get_approvers_for_order(order):
    """Get list of approvers who can approve a specific order."""
    submitter_dept_id = order.ordered_by.department_id if order.ordered_by else None

    approvers = Approver.query.filter_by(is_active=True).all()
    eligible = []

    for approver in approvers:
        if approver.can_approve_for_department(submitter_dept_id):
            eligible.append(approver)

    return eligible


def get_order_approvers(order_id, current_user):
    """Get list of approvers for a specific order."""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    approvers = get_approvers_for_order(order)
    return jsonify([a.to_dict(include_user=True) for a in approvers])


def admin_update_order_items(order_id, current_user):
    """Admin can update line items on approved orders (for accurate pricing from vendor)."""
    if not current_user.is_admin:
        return jsonify({"error": "Only admins can update approved order items"}), 403

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.status not in (OrderStatus.APPROVED, OrderStatus.PAID):
        return jsonify({"error": "Only approved or paid orders can have items updated by admin"}), 400

    data = request.get_json()
    if not data or "items" not in data:
        return jsonify({"error": "Items data is required"}), 400

    # Remove existing items
    OrderItem.query.filter_by(order_id=order.id).delete()

    # Add new items
    for idx, item_data in enumerate(data["items"]):
        if not item_data.get("description"):
            continue

        item = OrderItem(
            order_id=order.id,
            line_number=idx + 1,
            description=item_data["description"],
            quantity=item_data.get("quantity"),
            unit_cost=item_data.get("unit_cost"),
        )
        db.session.add(item)

    db.session.commit()

    return jsonify({
        "message": "Order items updated",
        "order": order.to_dict(include_relations=True),
    })


def mark_order_paid(order_id, current_user):
    """Admin can mark an approved order as paid."""
    if not current_user.is_admin:
        return jsonify({"error": "Only admins can mark orders as paid"}), 403

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.status != OrderStatus.APPROVED:
        return jsonify({"error": "Only approved orders can be marked as paid"}), 400

    order.status = OrderStatus.PAID
    db.session.commit()

    return jsonify({
        "message": "Order marked as paid",
        "order": order.to_dict(include_relations=True),
    })
