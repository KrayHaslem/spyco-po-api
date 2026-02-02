from flask import Blueprint
from controllers.order_controller import (
    get_orders,
    get_all_orders,
    get_order,
    create_order,
    update_order,
    delete_order,
    submit_order,
    approve_order,
    reject_order,
    get_order_approvers,
    admin_update_order_items,
    mark_order_paid,
)
from lib.authenticate import authenticate

order_bp = Blueprint("order", __name__)


@order_bp.route("/", methods=["GET"])
@authenticate
def get_orders_route(current_user):
    return get_orders(current_user)


@order_bp.route("/all", methods=["GET"])
@authenticate
def get_all_orders_route(current_user):
    return get_all_orders(current_user)


@order_bp.route("/<order_id>", methods=["GET"])
@authenticate
def get_order_route(order_id, current_user):
    return get_order(order_id, current_user)


@order_bp.route("/", methods=["POST"])
@authenticate
def create_order_route(current_user):
    return create_order(current_user)


@order_bp.route("/<order_id>", methods=["PUT"])
@authenticate
def update_order_route(order_id, current_user):
    return update_order(order_id, current_user)


@order_bp.route("/<order_id>", methods=["DELETE"])
@authenticate
def delete_order_route(order_id, current_user):
    return delete_order(order_id, current_user)


@order_bp.route("/<order_id>/submit", methods=["POST"])
@authenticate
def submit_order_route(order_id, current_user):
    return submit_order(order_id, current_user)


@order_bp.route("/<order_id>/approve", methods=["POST"])
@authenticate
def approve_order_route(order_id, current_user):
    return approve_order(order_id, current_user)


@order_bp.route("/<order_id>/reject", methods=["POST"])
@authenticate
def reject_order_route(order_id, current_user):
    return reject_order(order_id, current_user)


@order_bp.route("/<order_id>/approvers", methods=["GET"])
@authenticate
def get_order_approvers_route(order_id, current_user):
    return get_order_approvers(order_id, current_user)


@order_bp.route("/<order_id>/admin-items", methods=["PUT"])
@authenticate
def admin_update_order_items_route(order_id, current_user):
    return admin_update_order_items(order_id, current_user)


@order_bp.route("/<order_id>/mark-paid", methods=["POST"])
@authenticate
def mark_order_paid_route(order_id, current_user):
    return mark_order_paid(order_id, current_user)
