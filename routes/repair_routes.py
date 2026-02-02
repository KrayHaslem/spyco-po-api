from flask import Blueprint
from controllers.repair_controller import (
    get_repairs,
    get_all_repairs,
    get_repair,
    create_repair,
    update_repair,
    delete_repair,
    submit_repair,
    approve_repair,
    reject_repair,
    get_repair_approvers,
    complete_repair,
)
from lib.authenticate import authenticate

repair_bp = Blueprint("repair", __name__)


@repair_bp.route("/", methods=["GET"])
@authenticate
def get_repairs_route(current_user):
    return get_repairs(current_user)


@repair_bp.route("/all", methods=["GET"])
@authenticate
def get_all_repairs_route(current_user):
    return get_all_repairs(current_user)


@repair_bp.route("/<repair_id>", methods=["GET"])
@authenticate
def get_repair_route(repair_id, current_user):
    return get_repair(repair_id, current_user)


@repair_bp.route("/", methods=["POST"])
@authenticate
def create_repair_route(current_user):
    return create_repair(current_user)


@repair_bp.route("/<repair_id>", methods=["PUT"])
@authenticate
def update_repair_route(repair_id, current_user):
    return update_repair(repair_id, current_user)


@repair_bp.route("/<repair_id>", methods=["DELETE"])
@authenticate
def delete_repair_route(repair_id, current_user):
    return delete_repair(repair_id, current_user)


@repair_bp.route("/<repair_id>/submit", methods=["POST"])
@authenticate
def submit_repair_route(repair_id, current_user):
    return submit_repair(repair_id, current_user)


@repair_bp.route("/<repair_id>/approve", methods=["POST"])
@authenticate
def approve_repair_route(repair_id, current_user):
    return approve_repair(repair_id, current_user)


@repair_bp.route("/<repair_id>/reject", methods=["POST"])
@authenticate
def reject_repair_route(repair_id, current_user):
    return reject_repair(repair_id, current_user)


@repair_bp.route("/<repair_id>/approvers", methods=["GET"])
@authenticate
def get_repair_approvers_route(repair_id, current_user):
    return get_repair_approvers(repair_id, current_user)


@repair_bp.route("/<repair_id>/complete", methods=["POST"])
@authenticate
def complete_repair_route(repair_id, current_user):
    return complete_repair(repair_id, current_user)
