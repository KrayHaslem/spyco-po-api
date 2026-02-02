from flask import Blueprint
from controllers.auth_controller import login, logout, check_login, change_password
from lib.authenticate import authenticate

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login_route():
    return login()


@auth_bp.route("/logout", methods=["POST"])
def logout_route():
    return logout()


@auth_bp.route("/check-login", methods=["GET"])
@authenticate
def check_login_route(current_user):
    return check_login(current_user)


@auth_bp.route("/change-password", methods=["POST"])
@authenticate
def change_password_route(current_user):
    return change_password(current_user)
