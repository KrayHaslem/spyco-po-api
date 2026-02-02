from flask import request, jsonify, make_response
from db import db
from models.user import User
from lib.authenticate import generate_token


def login():
    """Handle user login."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is inactive"}), 401

    token = generate_token(user.id)

    response = make_response(jsonify({
        "message": "Login successful",
        "user": user.to_dict(include_department=True),
    }))

    response.set_cookie(
        "token",
        token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="Lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )

    return response


def logout():
    """Handle user logout."""
    response = make_response(jsonify({"message": "Logout successful"}))
    response.delete_cookie("token")
    return response


def check_login(current_user):
    """Check if user is logged in and return user info."""
    return jsonify({
        "authenticated": True,
        "user": current_user.to_dict(include_department=True),
    })


def change_password(current_user):
    """Change user's password."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        return jsonify({"error": "Current password and new password are required"}), 400

    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters"}), 400

    if not current_user.check_password(current_password):
        return jsonify({"error": "Current password is incorrect"}), 401

    current_user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Password changed successfully"})
