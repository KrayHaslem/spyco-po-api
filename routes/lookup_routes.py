from flask import Blueprint
from controllers.lookup_controller import (
    search_vendors,
    search_units,
    get_departments_list,
    create_vendor_quick,
    create_unit_quick,
)
from lib.authenticate import authenticate

lookup_bp = Blueprint("lookup", __name__)


@lookup_bp.route("/vendors/search", methods=["GET"])
@authenticate
def search_vendors_route(current_user):
    return search_vendors(current_user)


@lookup_bp.route("/vendors", methods=["POST"])
@authenticate
def create_vendor_quick_route(current_user):
    return create_vendor_quick(current_user)


@lookup_bp.route("/units/search", methods=["GET"])
@authenticate
def search_units_route(current_user):
    return search_units(current_user)


@lookup_bp.route("/units", methods=["POST"])
@authenticate
def create_unit_quick_route(current_user):
    return create_unit_quick(current_user)


@lookup_bp.route("/departments", methods=["GET"])
@authenticate
def get_departments_route(current_user):
    return get_departments_list(current_user)
