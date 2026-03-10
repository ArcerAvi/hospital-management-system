from functools import wraps
from flask import session, jsonify

def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return jsonify({"error": "Login required"}), 401

            if role and session.get("role") != role:
                return jsonify({"error": "Unauthorized"}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator