from flask import request, jsonify
from db import db
from models.department import Department
from models.user import User
from models.vendor import Vendor
from models.unit import Unit, UnitType
from models.approver import Approver
from models.approver_department import ApproverDepartment
from models.technician import Technician


# ============== DEPARTMENTS ==============

def get_departments():
    """Get all departments."""
    departments = Department.query.order_by(Department.name).all()
    return jsonify([d.to_dict() for d in departments])


def get_department(department_id):
    """Get a single department."""
    department = Department.query.get(department_id)
    if not department:
        return jsonify({"error": "Department not found"}), 404
    return jsonify(department.to_dict())


def create_department(current_user):
    """Create a new department."""
    data = request.get_json()

    if not data or not data.get("name"):
        return jsonify({"error": "Name is required"}), 400

    existing = Department.query.filter_by(name=data["name"]).first()
    if existing:
        return jsonify({"error": "Department with this name already exists"}), 400

    department = Department(
        name=data["name"],
        description=data.get("description"),
        is_active=data.get("is_active", True),
    )

    db.session.add(department)
    db.session.commit()

    return jsonify(department.to_dict()), 201


def update_department(department_id, current_user):
    """Update a department."""
    department = Department.query.get(department_id)
    if not department:
        return jsonify({"error": "Department not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "name" in data:
        existing = Department.query.filter(
            Department.name == data["name"],
            Department.id != department_id
        ).first()
        if existing:
            return jsonify({"error": "Department with this name already exists"}), 400
        department.name = data["name"]

    if "description" in data:
        department.description = data["description"]
    if "is_active" in data:
        department.is_active = data["is_active"]

    db.session.commit()
    return jsonify(department.to_dict())


def delete_department(department_id, current_user):
    """Delete a department."""
    department = Department.query.get(department_id)
    if not department:
        return jsonify({"error": "Department not found"}), 404

    db.session.delete(department)
    db.session.commit()

    return jsonify({"message": "Department deleted"})


# ============== USERS ==============

def get_users():
    """Get all users."""
    users = User.query.order_by(User.last_name, User.first_name).all()
    return jsonify([u.to_dict(include_department=True) for u in users])


def get_user(user_id):
    """Get a single user."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict(include_department=True))


def create_user(current_user):
    """Create a new user."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    required = ["email", "password", "first_name", "last_name"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    email = data["email"].lower().strip()
    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "User with this email already exists"}), 400

    if len(data["password"]) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    user = User(
        email=email,
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data.get("phone"),
        department_id=data.get("department_id") or None,
        job_title=data.get("job_title") or None,
        is_admin=data.get("is_admin", False),
        is_active=data.get("is_active", True),
    )
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict(include_department=True)), 201


def update_user(user_id, current_user):
    """Update a user."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "email" in data:
        email = data["email"].lower().strip()
        existing = User.query.filter(
            User.email == email,
            User.id != user_id
        ).first()
        if existing:
            return jsonify({"error": "User with this email already exists"}), 400
        user.email = email

    if "first_name" in data:
        user.first_name = data["first_name"]
    if "last_name" in data:
        user.last_name = data["last_name"]
    if "phone" in data:
        user.phone = data["phone"]
    if "department_id" in data:
        user.department_id = data["department_id"] or None
    if "job_title" in data:
        user.job_title = data["job_title"]
    if "is_admin" in data:
        user.is_admin = data["is_admin"]
    if "is_active" in data:
        user.is_active = data["is_active"]
    if "password" in data and data["password"]:
        if len(data["password"]) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400
        user.set_password(data["password"])

    db.session.commit()
    return jsonify(user.to_dict(include_department=True))


def delete_user(user_id, current_user):
    """Delete a user (soft delete by setting inactive)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.id == current_user.id:
        return jsonify({"error": "Cannot delete your own account"}), 400

    user.is_active = False
    db.session.commit()

    return jsonify({"message": "User deactivated"})


# ============== VENDORS ==============

def get_vendors():
    """Get all vendors."""
    vendors = Vendor.query.order_by(Vendor.name).all()
    return jsonify([v.to_dict() for v in vendors])


def get_vendor(vendor_id):
    """Get a single vendor."""
    vendor = Vendor.query.get(vendor_id)
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404
    return jsonify(vendor.to_dict())


def create_vendor(current_user):
    """Create a new vendor."""
    data = request.get_json()

    if not data or not data.get("name"):
        return jsonify({"error": "Name is required"}), 400

    vendor = Vendor(
        name=data["name"],
        contact_info=data.get("contact_info"),
        is_active=data.get("is_active", True),
    )

    db.session.add(vendor)
    db.session.commit()

    return jsonify(vendor.to_dict()), 201


def update_vendor(vendor_id, current_user):
    """Update a vendor."""
    vendor = Vendor.query.get(vendor_id)
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "name" in data:
        vendor.name = data["name"]
    if "contact_info" in data:
        vendor.contact_info = data["contact_info"]
    if "is_active" in data:
        vendor.is_active = data["is_active"]

    db.session.commit()
    return jsonify(vendor.to_dict())


def delete_vendor(vendor_id, current_user):
    """Delete a vendor."""
    vendor = Vendor.query.get(vendor_id)
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404

    vendor.is_active = False
    db.session.commit()

    return jsonify({"message": "Vendor deactivated"})


# ============== UNITS ==============

def get_units():
    """Get all units."""
    units = Unit.query.order_by(Unit.unit_number).all()
    return jsonify([u.to_dict(include_department=True) for u in units])


def get_unit(unit_id):
    """Get a single unit."""
    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({"error": "Unit not found"}), 404
    return jsonify(unit.to_dict(include_department=True))


def get_unit_types():
    """Get all unit types."""
    return jsonify(UnitType.all())


def create_unit(current_user):
    """Create a new unit."""
    data = request.get_json()

    if not data or not data.get("unit_number"):
        return jsonify({"error": "Unit number is required"}), 400

    existing = Unit.query.filter_by(unit_number=data["unit_number"]).first()
    if existing:
        return jsonify({"error": "Unit with this number already exists"}), 400

    unit_type = data.get("unit_type", UnitType.OTHER)
    if unit_type not in UnitType.all():
        return jsonify({"error": f"Invalid unit type. Must be one of: {UnitType.all()}"}), 400

    unit = Unit(
        unit_number=data["unit_number"],
        description=data.get("description"),
        unit_type=unit_type,
        department_id=data.get("department_id"),
        is_active=data.get("is_active", True),
        created_by_id=current_user.id,
    )

    db.session.add(unit)
    db.session.commit()

    return jsonify(unit.to_dict(include_department=True)), 201


def update_unit(unit_id, current_user):
    """Update a unit."""
    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({"error": "Unit not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "unit_number" in data:
        existing = Unit.query.filter(
            Unit.unit_number == data["unit_number"],
            Unit.id != unit_id
        ).first()
        if existing:
            return jsonify({"error": "Unit with this number already exists"}), 400
        unit.unit_number = data["unit_number"]

    if "description" in data:
        unit.description = data["description"]
    if "unit_type" in data:
        if data["unit_type"] not in UnitType.all():
            return jsonify({"error": f"Invalid unit type. Must be one of: {UnitType.all()}"}), 400
        unit.unit_type = data["unit_type"]
    if "department_id" in data:
        unit.department_id = data["department_id"] or None
    if "is_active" in data:
        unit.is_active = data["is_active"]

    db.session.commit()
    return jsonify(unit.to_dict(include_department=True))


def delete_unit(unit_id, current_user):
    """Delete a unit."""
    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({"error": "Unit not found"}), 404

    unit.is_active = False
    db.session.commit()

    return jsonify({"message": "Unit deactivated"})


# ============== APPROVERS ==============

def get_approvers():
    """Get all approvers."""
    approvers = Approver.query.all()
    return jsonify([a.to_dict(include_user=True, include_departments=True) for a in approvers])


def get_approver(approver_id):
    """Get a single approver."""
    approver = Approver.query.get(approver_id)
    if not approver:
        return jsonify({"error": "Approver not found"}), 404
    return jsonify(approver.to_dict(include_user=True, include_departments=True))


def create_approver(current_user):
    """Create a new approver."""
    data = request.get_json()

    if not data or not data.get("user_id"):
        return jsonify({"error": "User ID is required"}), 400

    user = User.query.get(data["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    existing = Approver.query.filter_by(user_id=data["user_id"]).first()
    if existing:
        return jsonify({"error": "This user is already an approver"}), 400

    approver = Approver(
        user_id=data["user_id"],
        is_active=data.get("is_active", True),
        created_by_id=current_user.id,
    )

    db.session.add(approver)
    db.session.flush()

    # Add department assignments if provided
    department_ids = data.get("department_ids", [])
    for dept_id in department_ids:
        dept = Department.query.get(dept_id)
        if dept:
            approver_dept = ApproverDepartment(
                approver_id=approver.id,
                department_id=dept_id,
            )
            db.session.add(approver_dept)

    db.session.commit()

    return jsonify(approver.to_dict(include_user=True, include_departments=True)), 201


def update_approver(approver_id, current_user):
    """Update an approver."""
    approver = Approver.query.get(approver_id)
    if not approver:
        return jsonify({"error": "Approver not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "is_active" in data:
        approver.is_active = data["is_active"]

    # Update department assignments if provided
    if "department_ids" in data:
        # Remove existing assignments
        ApproverDepartment.query.filter_by(approver_id=approver.id).delete()

        # Add new assignments
        for dept_id in data["department_ids"]:
            dept = Department.query.get(dept_id)
            if dept:
                approver_dept = ApproverDepartment(
                    approver_id=approver.id,
                    department_id=dept_id,
                )
                db.session.add(approver_dept)

    db.session.commit()
    return jsonify(approver.to_dict(include_user=True, include_departments=True))


def delete_approver(approver_id, current_user):
    """Delete an approver."""
    approver = Approver.query.get(approver_id)
    if not approver:
        return jsonify({"error": "Approver not found"}), 404

    db.session.delete(approver)
    db.session.commit()

    return jsonify({"message": "Approver removed"})


# ============== TECHNICIANS ==============

def get_technicians():
    """Get all technicians."""
    technicians = Technician.query.all()
    return jsonify([t.to_dict(include_user=True) for t in technicians])


def get_technician(technician_id):
    """Get a single technician."""
    technician = Technician.query.get(technician_id)
    if not technician:
        return jsonify({"error": "Technician not found"}), 404
    return jsonify(technician.to_dict(include_user=True))


def create_technician(current_user):
    """Create a new technician."""
    data = request.get_json()

    if not data or not data.get("user_id"):
        return jsonify({"error": "User ID is required"}), 400

    user = User.query.get(data["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    existing = Technician.query.filter_by(user_id=data["user_id"]).first()
    if existing:
        return jsonify({"error": "This user is already a technician"}), 400

    technician = Technician(
        user_id=data["user_id"],
        is_active=data.get("is_active", True),
        created_by_id=current_user.id,
    )

    db.session.add(technician)
    db.session.commit()

    return jsonify(technician.to_dict(include_user=True)), 201


def update_technician(technician_id, current_user):
    """Update a technician."""
    technician = Technician.query.get(technician_id)
    if not technician:
        return jsonify({"error": "Technician not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "is_active" in data:
        technician.is_active = data["is_active"]

    db.session.commit()
    return jsonify(technician.to_dict(include_user=True))


def delete_technician(technician_id, current_user):
    """Delete a technician."""
    technician = Technician.query.get(technician_id)
    if not technician:
        return jsonify({"error": "Technician not found"}), 404

    db.session.delete(technician)
    db.session.commit()

    return jsonify({"message": "Technician removed"})
