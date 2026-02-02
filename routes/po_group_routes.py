from flask import Blueprint
from controllers.po_group_controller import (
    get_po_groups,
    get_po_group,
    create_po_group,
    update_po_group,
    delete_po_group,
    add_orders_to_po_group,
    remove_order_from_po_group,
    get_available_orders_for_po_group,
)
from lib.authenticate import authenticate

po_group_bp = Blueprint("po_group", __name__)


@po_group_bp.route("/", methods=["GET"])
@authenticate
def get_po_groups_route(current_user):
    return get_po_groups(current_user)


@po_group_bp.route("/available-orders", methods=["GET"])
@authenticate
def get_available_orders_route(current_user):
    return get_available_orders_for_po_group(current_user)


@po_group_bp.route("/<po_group_id>", methods=["GET"])
@authenticate
def get_po_group_route(po_group_id, current_user):
    return get_po_group(po_group_id, current_user)


@po_group_bp.route("/", methods=["POST"])
@authenticate
def create_po_group_route(current_user):
    return create_po_group(current_user)


@po_group_bp.route("/<po_group_id>", methods=["PUT"])
@authenticate
def update_po_group_route(po_group_id, current_user):
    return update_po_group(po_group_id, current_user)


@po_group_bp.route("/<po_group_id>", methods=["DELETE"])
@authenticate
def delete_po_group_route(po_group_id, current_user):
    return delete_po_group(po_group_id, current_user)


@po_group_bp.route("/<po_group_id>/orders", methods=["POST"])
@authenticate
def add_orders_route(po_group_id, current_user):
    return add_orders_to_po_group(po_group_id, current_user)


@po_group_bp.route("/<po_group_id>/orders/<order_id>", methods=["DELETE"])
@authenticate
def remove_order_route(po_group_id, order_id, current_user):
    return remove_order_from_po_group(po_group_id, order_id, current_user)
