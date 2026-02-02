from flask import request, jsonify
from db import db
from models.vendor import Vendor
from models.unit import Unit
from models.department import Department


def search_vendors(current_user):
    """Search vendors by name."""
    query = request.args.get("q", "").strip()
    
    vendors = Vendor.query.filter(
        Vendor.is_active == True
    )
    
    if query:
        vendors = vendors.filter(Vendor.name.ilike(f"%{query}%"))
    
    vendors = vendors.order_by(Vendor.name).limit(50).all()
    
    return jsonify([v.to_dict() for v in vendors])


def search_units(current_user):
    """Search units by number or description."""
    query = request.args.get("q", "").strip()
    
    units = Unit.query.filter(
        Unit.is_active == True
    )
    
    if query:
        units = units.filter(
            db.or_(
                Unit.unit_number.ilike(f"%{query}%"),
                Unit.description.ilike(f"%{query}%"),
            )
        )
    
    units = units.order_by(Unit.unit_number).limit(50).all()
    
    return jsonify([u.to_dict(include_department=True) for u in units])


def get_departments_list(current_user):
    """Get all active departments for dropdowns."""
    departments = Department.query.filter(
        Department.is_active == True
    ).order_by(Department.name).all()
    
    return jsonify([d.to_dict() for d in departments])


def create_vendor_quick(current_user):
    """Quick create a vendor from the combo box."""
    data = request.get_json()
    
    if not data or not data.get("name"):
        return jsonify({"error": "Name is required"}), 400
    
    vendor = Vendor(
        name=data["name"],
        contact_info=data.get("contact_info"),
        is_active=True,
    )
    
    db.session.add(vendor)
    db.session.commit()
    
    return jsonify(vendor.to_dict()), 201


def create_unit_quick(current_user):
    """Quick create a unit from the combo box."""
    data = request.get_json()
    
    if not data or not data.get("unit_number"):
        return jsonify({"error": "Unit number is required"}), 400
    
    existing = Unit.query.filter_by(unit_number=data["unit_number"]).first()
    if existing:
        return jsonify({"error": "Unit with this number already exists"}), 400
    
    unit = Unit(
        unit_number=data["unit_number"],
        description=data.get("description"),
        unit_type=data.get("unit_type", "other"),
        department_id=data.get("department_id"),
        is_active=True,
        created_by_id=current_user.id,
    )
    
    db.session.add(unit)
    db.session.commit()
    
    return jsonify(unit.to_dict(include_department=True)), 201
