from datetime import datetime, timezone
from flask import request, jsonify
from db import db
from models.repair import Repair, RepairStatus
from models.repair_item import RepairItem
from models.approver import Approver
from models.technician import Technician
from models.unit import Unit
from app import REPAIRS_DEPARTMENT_ID
from lib.sms_service import notify_repair_pending, notify_repair_approved, notify_repair_completed


def get_repairs(current_user):
    """Get repairs for current user (their own or ones they can approve/complete)."""
    # Get repairs created by the user
    user_repairs = Repair.query.filter_by(requested_by_id=current_user.id).all()

    # If user is an approver, also get pending repairs they can approve
    approver_repairs = []
    if current_user.is_approver:
        approver = Approver.query.filter_by(user_id=current_user.id).first()
        if approver:
            pending_repairs = Repair.query.filter_by(status=RepairStatus.PENDING).all()
            for repair in pending_repairs:
                # Check if approver can approve repairs (via Repairs department)
                if approver.can_approve_for_department(REPAIRS_DEPARTMENT_ID):
                    if repair not in user_repairs:
                        approver_repairs.append(repair)

    # If user is a technician, also get approved repairs they can complete
    technician_repairs = []
    if current_user.is_technician:
        approved_repairs = Repair.query.filter_by(status=RepairStatus.APPROVED).all()
        for repair in approved_repairs:
            if repair not in user_repairs and repair not in approver_repairs:
                technician_repairs.append(repair)

    all_repairs = user_repairs + approver_repairs + technician_repairs
    return jsonify([repair.to_dict(include_relations=True) for repair in all_repairs])


def get_all_repairs(current_user):
    """Get all repairs (admin sees all, approvers/technicians see relevant ones)."""
    # Build base query
    query = Repair.query

    # Apply filters from query params
    status = request.args.get("status")
    if status and status in RepairStatus.all():
        query = query.filter_by(status=status)

    owner_id = request.args.get("owner_id")
    if owner_id:
        query = query.filter_by(requested_by_id=owner_id)

    unit_id = request.args.get("unit_id")
    if unit_id:
        query = query.filter_by(unit_id=unit_id)

    # If admin, return all matching repairs
    if current_user.is_admin:
        repairs = query.order_by(Repair.created_at.desc()).all()
        return jsonify([repair.to_dict(include_relations=True) for repair in repairs])

    # If approver assigned to Repairs department, return all
    if current_user.is_approver:
        approver = Approver.query.filter_by(user_id=current_user.id).first()
        if approver and approver.can_approve_for_department(REPAIRS_DEPARTMENT_ID):
            repairs = query.order_by(Repair.created_at.desc()).all()
            return jsonify([repair.to_dict(include_relations=True) for repair in repairs])

    # If technician, return all
    if current_user.is_technician:
        repairs = query.order_by(Repair.created_at.desc()).all()
        return jsonify([repair.to_dict(include_relations=True) for repair in repairs])

    # Not authorized
    return jsonify({"error": "Access denied"}), 403


def get_repair(repair_id, current_user):
    """Get a single repair."""
    repair = Repair.query.get(repair_id)
    if not repair:
        return jsonify({"error": "Repair not found"}), 404

    # Check access: user must be the creator, admin, approver, or technician
    can_access = (
        repair.requested_by_id == current_user.id or
        current_user.is_admin or
        current_user.is_technician
    )

    if not can_access and current_user.is_approver:
        approver = Approver.query.filter_by(user_id=current_user.id).first()
        if approver and approver.can_approve_for_department(REPAIRS_DEPARTMENT_ID):
            can_access = True

    if not can_access:
        return jsonify({"error": "Access denied"}), 403

    return jsonify(repair.to_dict(include_relations=True))


def create_repair(current_user):
    """Create a new repair request."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate required fields
    if not data.get("unit_id"):
        return jsonify({"error": "Unit is required"}), 400
    if not data.get("description"):
        return jsonify({"error": "Description is required"}), 400

    # Validate unit exists
    unit = Unit.query.get(data["unit_id"])
    if not unit:
        return jsonify({"error": "Unit not found"}), 404

    # Create repair
    repair = Repair(
        repair_number=Repair.generate_repair_number(),
        unit_id=data["unit_id"],
        description=data["description"],
        status=RepairStatus.DRAFT,
        requested_by_id=current_user.id,
        notes=data.get("notes"),
    )

    db.session.add(repair)
    db.session.flush()

    # Add repair items
    items = data.get("items", [])
    for idx, item_data in enumerate(items):
        if not item_data.get("description"):
            continue

        item = RepairItem(
            repair_id=repair.id,
            line_number=idx + 1,
            description=item_data["description"],
        )
        db.session.add(item)

    db.session.commit()

    return jsonify(repair.to_dict(include_relations=True)), 201


def update_repair(repair_id, current_user):
    """Update a repair (drafts and rejected repairs can be updated by creator)."""
    repair = Repair.query.get(repair_id)
    if not repair:
        return jsonify({"error": "Repair not found"}), 404

    if repair.requested_by_id != current_user.id:
        return jsonify({"error": "Only the creator can edit this repair"}), 403

    if repair.status not in (RepairStatus.DRAFT, RepairStatus.REJECTED):
        return jsonify({"error": "Only draft or rejected repairs can be edited"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update basic fields
    if "unit_id" in data:
        if data["unit_id"]:
            unit = Unit.query.get(data["unit_id"])
            if not unit:
                return jsonify({"error": "Unit not found"}), 404
        repair.unit_id = data["unit_id"]

    if "description" in data:
        repair.description = data["description"]
    if "notes" in data:
        repair.notes = data["notes"]

    # Update items if provided
    if "items" in data:
        # Remove existing items
        RepairItem.query.filter_by(repair_id=repair.id).delete()

        # Add new items
        for idx, item_data in enumerate(data["items"]):
            if not item_data.get("description"):
                continue

            item = RepairItem(
                repair_id=repair.id,
                line_number=idx + 1,
                description=item_data["description"],
            )
            db.session.add(item)

    db.session.commit()

    return jsonify(repair.to_dict(include_relations=True))


def delete_repair(repair_id, current_user):
    """Delete a repair (only drafts can be deleted)."""
    repair = Repair.query.get(repair_id)
    if not repair:
        return jsonify({"error": "Repair not found"}), 404

    if repair.requested_by_id != current_user.id and not current_user.is_admin:
        return jsonify({"error": "Only the creator or admin can delete this repair"}), 403

    if repair.status != RepairStatus.DRAFT:
        return jsonify({"error": "Only draft repairs can be deleted"}), 400

    db.session.delete(repair)
    db.session.commit()

    return jsonify({"message": "Repair deleted"})


def submit_repair(repair_id, current_user):
    """Submit a repair for approval (draft or re-submit after rejection)."""
    repair = Repair.query.get(repair_id)
    if not repair:
        return jsonify({"error": "Repair not found"}), 404

    if repair.requested_by_id != current_user.id:
        return jsonify({"error": "Only the creator can submit this repair"}), 403

    if repair.status not in (RepairStatus.DRAFT, RepairStatus.REJECTED):
        return jsonify({"error": "Only draft or rejected repairs can be submitted"}), 400

    if len(repair.items) == 0:
        return jsonify({"error": "Repair must have at least one item"}), 400

    # Find approvers who can approve repairs
    approvers = get_approvers_for_repair()
    if not approvers:
        return jsonify({"error": "No approvers configured for repairs"}), 400

    repair.status = RepairStatus.PENDING
    db.session.commit()

    # Notify approvers via SMS
    notify_repair_pending(repair, approvers, current_user.full_name)

    return jsonify({
        "message": "Repair submitted for approval",
        "repair": repair.to_dict(include_relations=True),
        "approvers": [a.to_dict(include_user=True) for a in approvers],
    })


def approve_repair(repair_id, current_user):
    """Approve a repair."""
    repair = Repair.query.get(repair_id)
    if not repair:
        return jsonify({"error": "Repair not found"}), 404

    if repair.status != RepairStatus.PENDING:
        return jsonify({"error": "Only pending repairs can be approved"}), 400

    # Check if user is an approver who can approve repairs
    if not current_user.is_approver:
        return jsonify({"error": "You are not an approver"}), 403

    approver = Approver.query.filter_by(user_id=current_user.id).first()
    if not approver or not approver.can_approve_for_department(REPAIRS_DEPARTMENT_ID):
        return jsonify({"error": "You cannot approve repairs"}), 403

    repair.status = RepairStatus.APPROVED
    repair.approved_by_id = current_user.id
    repair.approved_at = datetime.now(timezone.utc)
    db.session.commit()

    # Notify all active technicians via SMS
    technicians = Technician.query.filter_by(is_active=True).all()
    notify_repair_approved(repair, technicians)

    return jsonify({
        "message": "Repair approved",
        "repair": repair.to_dict(include_relations=True),
    })


def reject_repair(repair_id, current_user):
    """Reject a repair."""
    repair = Repair.query.get(repair_id)
    if not repair:
        return jsonify({"error": "Repair not found"}), 404

    if repair.status != RepairStatus.PENDING:
        return jsonify({"error": "Only pending repairs can be rejected"}), 400

    # Check if user is an approver who can reject repairs
    if not current_user.is_approver:
        return jsonify({"error": "You are not an approver"}), 403

    approver = Approver.query.filter_by(user_id=current_user.id).first()
    if not approver or not approver.can_approve_for_department(REPAIRS_DEPARTMENT_ID):
        return jsonify({"error": "You cannot reject repairs"}), 403

    data = request.get_json() or {}

    repair.status = RepairStatus.REJECTED
    repair.rejected_by_id = current_user.id
    repair.rejected_at = datetime.now(timezone.utc)
    repair.rejection_comment = data.get("comment", "")
    db.session.commit()

    return jsonify({
        "message": "Repair rejected",
        "repair": repair.to_dict(include_relations=True),
    })


def get_approvers_for_repair():
    """Get list of approvers who can approve repairs."""
    approvers = Approver.query.filter_by(is_active=True).all()
    eligible = []

    for approver in approvers:
        if approver.can_approve_for_department(REPAIRS_DEPARTMENT_ID):
            eligible.append(approver)

    return eligible


def get_repair_approvers(repair_id, current_user):
    """Get list of approvers for repairs."""
    repair = Repair.query.get(repair_id)
    if not repair:
        return jsonify({"error": "Repair not found"}), 404

    approvers = get_approvers_for_repair()
    return jsonify([a.to_dict(include_user=True) for a in approvers])


def complete_repair(repair_id, current_user):
    """Technician can mark an approved repair as completed."""
    if not current_user.is_technician:
        return jsonify({"error": "Only technicians can mark repairs as completed"}), 403

    repair = Repair.query.get(repair_id)
    if not repair:
        return jsonify({"error": "Repair not found"}), 404

    if repair.status != RepairStatus.APPROVED:
        return jsonify({"error": "Only approved repairs can be marked as completed"}), 400

    repair.status = RepairStatus.COMPLETED
    repair.completed_by_id = current_user.id
    repair.completed_at = datetime.now(timezone.utc)
    db.session.commit()

    # Notify the original repair requester via SMS
    notify_repair_completed(repair, repair.requested_by)

    return jsonify({
        "message": "Repair marked as completed",
        "repair": repair.to_dict(include_relations=True),
    })
