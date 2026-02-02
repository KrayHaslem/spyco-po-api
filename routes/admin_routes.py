from flask import Blueprint
from controllers.admin_controller import (
    get_departments, get_department, create_department, update_department, delete_department,
    get_users, get_user, create_user, update_user, delete_user,
    get_vendors, get_vendor, create_vendor, update_vendor, delete_vendor,
    get_units, get_unit, get_unit_types, create_unit, update_unit, delete_unit,
    get_approvers, get_approver, create_approver, update_approver, delete_approver,
    get_technicians, get_technician, create_technician, update_technician, delete_technician,
)
from lib.authenticate import require_admin

admin_bp = Blueprint("admin", __name__)


# ============== DEPARTMENTS ==============

@admin_bp.route("/departments", methods=["GET"])
@require_admin
def get_departments_route(current_user):
    return get_departments()


@admin_bp.route("/departments/<department_id>", methods=["GET"])
@require_admin
def get_department_route(department_id, current_user):
    return get_department(department_id)


@admin_bp.route("/departments", methods=["POST"])
@require_admin
def create_department_route(current_user):
    return create_department(current_user)


@admin_bp.route("/departments/<department_id>", methods=["PUT"])
@require_admin
def update_department_route(department_id, current_user):
    return update_department(department_id, current_user)


@admin_bp.route("/departments/<department_id>", methods=["DELETE"])
@require_admin
def delete_department_route(department_id, current_user):
    return delete_department(department_id, current_user)


# ============== USERS ==============

@admin_bp.route("/users", methods=["GET"])
@require_admin
def get_users_route(current_user):
    return get_users()


@admin_bp.route("/users/<user_id>", methods=["GET"])
@require_admin
def get_user_route(user_id, current_user):
    return get_user(user_id)


@admin_bp.route("/users", methods=["POST"])
@require_admin
def create_user_route(current_user):
    return create_user(current_user)


@admin_bp.route("/users/<user_id>", methods=["PUT"])
@require_admin
def update_user_route(user_id, current_user):
    return update_user(user_id, current_user)


@admin_bp.route("/users/<user_id>", methods=["DELETE"])
@require_admin
def delete_user_route(user_id, current_user):
    return delete_user(user_id, current_user)


# ============== VENDORS ==============

@admin_bp.route("/vendors", methods=["GET"])
@require_admin
def get_vendors_route(current_user):
    return get_vendors()


@admin_bp.route("/vendors/<vendor_id>", methods=["GET"])
@require_admin
def get_vendor_route(vendor_id, current_user):
    return get_vendor(vendor_id)


@admin_bp.route("/vendors", methods=["POST"])
@require_admin
def create_vendor_route(current_user):
    return create_vendor(current_user)


@admin_bp.route("/vendors/<vendor_id>", methods=["PUT"])
@require_admin
def update_vendor_route(vendor_id, current_user):
    return update_vendor(vendor_id, current_user)


@admin_bp.route("/vendors/<vendor_id>", methods=["DELETE"])
@require_admin
def delete_vendor_route(vendor_id, current_user):
    return delete_vendor(vendor_id, current_user)


# ============== UNITS ==============

@admin_bp.route("/units", methods=["GET"])
@require_admin
def get_units_route(current_user):
    return get_units()


@admin_bp.route("/units/<unit_id>", methods=["GET"])
@require_admin
def get_unit_route(unit_id, current_user):
    return get_unit(unit_id)


@admin_bp.route("/unit-types", methods=["GET"])
@require_admin
def get_unit_types_route(current_user):
    return get_unit_types()


@admin_bp.route("/units", methods=["POST"])
@require_admin
def create_unit_route(current_user):
    return create_unit(current_user)


@admin_bp.route("/units/<unit_id>", methods=["PUT"])
@require_admin
def update_unit_route(unit_id, current_user):
    return update_unit(unit_id, current_user)


@admin_bp.route("/units/<unit_id>", methods=["DELETE"])
@require_admin
def delete_unit_route(unit_id, current_user):
    return delete_unit(unit_id, current_user)


# ============== APPROVERS ==============

@admin_bp.route("/approvers", methods=["GET"])
@require_admin
def get_approvers_route(current_user):
    return get_approvers()


@admin_bp.route("/approvers/<approver_id>", methods=["GET"])
@require_admin
def get_approver_route(approver_id, current_user):
    return get_approver(approver_id)


@admin_bp.route("/approvers", methods=["POST"])
@require_admin
def create_approver_route(current_user):
    return create_approver(current_user)


@admin_bp.route("/approvers/<approver_id>", methods=["PUT"])
@require_admin
def update_approver_route(approver_id, current_user):
    return update_approver(approver_id, current_user)


@admin_bp.route("/approvers/<approver_id>", methods=["DELETE"])
@require_admin
def delete_approver_route(approver_id, current_user):
    return delete_approver(approver_id, current_user)


# ============== TECHNICIANS ==============

@admin_bp.route("/technicians", methods=["GET"])
@require_admin
def get_technicians_route(current_user):
    return get_technicians()


@admin_bp.route("/technicians/<technician_id>", methods=["GET"])
@require_admin
def get_technician_route(technician_id, current_user):
    return get_technician(technician_id)


@admin_bp.route("/technicians", methods=["POST"])
@require_admin
def create_technician_route(current_user):
    return create_technician(current_user)


@admin_bp.route("/technicians/<technician_id>", methods=["PUT"])
@require_admin
def update_technician_route(technician_id, current_user):
    return update_technician(technician_id, current_user)


@admin_bp.route("/technicians/<technician_id>", methods=["DELETE"])
@require_admin
def delete_technician_route(technician_id, current_user):
    return delete_technician(technician_id, current_user)
