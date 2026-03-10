from functools import wraps
from flask import Blueprint, request, jsonify, session

from models import db
from models.user import User
from models.doctor import Doctor
from models.patient import Patient

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET"])
def login():
    return {"message": "Login route placeholder./Auth login route working"}


@auth_bp.route("/register", methods=["GET"])
def register():
    return {"message": "Register route placeholder."}

# -------------------------
# Helper decorators
# -------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                return jsonify({"error": "Authentication required"}), 401

            user_role = session.get("role")
            if user_role not in allowed_roles:
                return jsonify({"error": "Access denied"}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -------------------------
# Patient Registration
# -------------------------
@auth_bp.route("/register/patient", methods=["POST"])
def register_patient():
    data = request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")
    age = data.get("age")
    gender = data.get("gender")
    phone = data.get("phone")
    address = data.get("address")

    if not username or not email or not password or not name or age is None or not gender:
        return jsonify({
            "error": "username, email, password, name, age, and gender are required"
        }), 400

    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        return jsonify({"error": "Username or email already exists"}), 409

    try:
        age = int(age)
    except (TypeError, ValueError):
        return jsonify({"error": "Age must be a valid integer"}), 400

    user = User(
        username=username,
        email=email,
        password=password,
        role="patient",
        is_active=True,
        is_blacklisted=False
    )
    db.session.add(user)
    db.session.flush()   # gets user.id before commit

    patient = Patient(
        user_id=user.id,
        name=name,
        age=age,
        gender=gender,
        phone=phone,
        address=address
    )
    db.session.add(patient)
    db.session.commit()

    return jsonify({
        "message": "Patient registered successfully",
        "user_id": user.id,
        "patient_id": patient.id
    }), 201

# -------------------------
# Admin Login
# -------------------------
@auth_bp.route("/login/admin", methods=["POST"])
def login_admin():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email, role="admin").first()

    if not user or user.password != password:
        return jsonify({"error": "Invalid admin credentials"}), 401

    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role

    return jsonify({
        "message": "Admin login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }), 200

# -------------------------
# Doctor Login
# -------------------------
@auth_bp.route("/login/doctor", methods=["POST"])
def login_doctor():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email, role="doctor").first()

    if not user or user.password != password:
        return jsonify({"error": "Invalid doctor credentials"}), 401

    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role

    return jsonify({
        "message": "Doctor login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }), 200

# -------------------------
# Patient Login
# -------------------------
@auth_bp.route("/login/patient", methods=["POST"])
def login_patient():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email, role="patient").first()

    if not user or user.password != password:
        return jsonify({"error": "Invalid patient credentials"}), 401

    if not user.is_active:
        return jsonify({"error": "Patient account is deactivated"}), 403

    if user.is_blacklisted:
        return jsonify({"error": "Patient account is blacklisted"}), 403

    patient = Patient.query.filter_by(user_id=user.id).first()
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404

    session["user_id"] = user.id
    session["role"] = user.role

    return jsonify({
        "message": "Patient login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        },
        "patient": {
            "id": patient.id,
            "name": patient.name
        }
    }), 200

# -------------------------
# Logout
# -------------------------
@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


# -------------------------
# Session / Protected Test Routes
# -------------------------
@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    return jsonify({
        "message": "Session is active",
        "user": {
            "user_id": session.get("user_id"),
            "username": session.get("username"),
            "role": session.get("role")
        }
    }), 200


@auth_bp.route("/admin-only", methods=["GET"])
@role_required("admin")
def admin_only():
    return jsonify({
        "message": f"Welcome Admin {session.get('username')}"
    }), 200


@auth_bp.route("/doctor-only", methods=["GET"])
@role_required("doctor")
def doctor_only():
    return jsonify({
        "message": f"Welcome Doctor {session.get('username')}"
    }), 200


@auth_bp.route("/patient-only", methods=["GET"])
@role_required("patient")
def patient_only():
    return jsonify({
        "message": f"Welcome Patient {session.get('username')}"
    }), 200