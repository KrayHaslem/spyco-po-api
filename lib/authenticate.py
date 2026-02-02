import os
from functools import wraps
from flask import request, jsonify, current_app
import jwt
from models.user import User


def authenticate(f):
    """Decorator to require authentication for a route."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("token")

        if not token:
            return jsonify({"error": "Authentication required"}), 401

        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET_KEY"],
                algorithms=[current_app.config["JWT_ALGORITHM"]],
            )
            user_id = payload.get("user_id")
            user = User.query.get(user_id)

            if not user or not user.is_active:
                return jsonify({"error": "User not found or inactive"}), 401

            kwargs["current_user"] = user
            return f(*args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

    return decorated_function


def require_admin(f):
    """Decorator to require admin privileges for a route."""

    @wraps(f)
    @authenticate
    def decorated_function(*args, **kwargs):
        current_user = kwargs.get("current_user")
        if not current_user.is_admin:
            return jsonify({"error": "Admin privileges required"}), 403
        return f(*args, **kwargs)

    return decorated_function


def require_approver(f):
    """Decorator to require approver privileges for a route."""

    @wraps(f)
    @authenticate
    def decorated_function(*args, **kwargs):
        current_user = kwargs.get("current_user")
        if not current_user.is_approver:
            return jsonify({"error": "Approver privileges required"}), 403
        return f(*args, **kwargs)

    return decorated_function


def generate_token(user_id):
    """Generate a JWT token for a user."""
    import datetime

    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(days=7),
        "iat": datetime.datetime.now(datetime.timezone.utc),
    }
    return jwt.encode(
        payload,
        os.getenv("JWT_SECRET_KEY", "dev-secret-key"),
        algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
    )
