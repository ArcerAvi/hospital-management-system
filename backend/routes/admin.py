from flask import Blueprint, request, jsonify
from models import db
from models.user import User
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from routes.utils import login_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard", methods=["GET"])
@login_required(role="admin")
def dashboard():
    return jsonify({
        "total_doctors": Doctor.query.count(),
        "total_patients": Patient.query.count(),
        "total_appointments": Appointment.query.count(),
        "active_doctors": User.query.filter_by(role="doctor", is_active=True).count(),
        "active_patients": User.query.filter_by(role="patient", is_active=True).count(),
    }), 200


@admin_bp.route("/doctors", methods=["POST"])
@login_required(role="admin")
def add_doctor():
    data = request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    specialization = data.get("specialization")
    phone = data.get("phone")

    if not all([username, email, password, specialization]):
        return jsonify({"error": "Missing required fields"}), 400

    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()
    if existing_user:
        return jsonify({"error": "Username or email already exists"}), 409

    user = User(
        username=username,
        email=email,
        role="doctor",
        is_active=True,
        is_blacklisted=False
    )
    #user.set_password(password)
    user.password = password

    db.session.add(user)
    db.session.flush()

    doctor = Doctor(
        user_id=user.id,
        name=username,
        specialization=specialization,
        phone=phone,
        availability="[]"
    )
    db.session.add(doctor)
    db.session.commit()

    return jsonify({"message": "Doctor added successfully", "doctor_id": doctor.id}), 201


@admin_bp.route("/doctors/<int:doctor_id>", methods=["PUT"])
@login_required(role="admin")
def edit_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    user = User.query.get(doctor.user_id)

    data = request.get_json()

    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]
    if "specialization" in data:
        doctor.specialization = data["specialization"]
    if "phone" in data:
        doctor.phone = data["phone"]

    db.session.commit()
    return jsonify({"message": "Doctor updated successfully"}), 200


@admin_bp.route("/doctors/<int:doctor_id>", methods=["DELETE"])
@login_required(role="admin")
def delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    user = User.query.get(doctor.user_id)

    Appointment.query.filter_by(doctor_id=doctor.id).delete()
    db.session.delete(doctor)
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "Doctor deleted successfully"}), 200


@admin_bp.route("/doctors/search", methods=["GET"])
@login_required(role="admin")
def search_doctors():
    q = request.args.get("q", "").strip()

    doctors = (
        db.session.query(Doctor, User)
        .join(User, Doctor.user_id == User.id)
        .filter(
            (User.username.ilike(f"%{q}%")) |
            (User.email.ilike(f"%{q}%")) |
            (Doctor.specialization.ilike(f"%{q}%"))
        )
        .all()
    )

    result = []
    for doctor, user in doctors:
        result.append({
            "doctor_id": doctor.id,
            "username": user.username,
            "email": user.email,
            "specialization": doctor.specialization,
            "phone": doctor.phone,
            "is_active": user.is_active,
            "is_blacklisted": user.is_blacklisted,
        })

    return jsonify(result), 200


@admin_bp.route("/patients/search", methods=["GET"])
@login_required(role="admin")
def search_patients():
    q = request.args.get("q", "").strip()

    patients = (
        db.session.query(Patient, User)
        .join(User, Patient.user_id == User.id)
        .filter(
            (User.username.ilike(f"%{q}%")) |
            (User.email.ilike(f"%{q}%")) |
            (Patient.phone.ilike(f"%{q}%"))
        )
        .all()
    )

    result = []
    for patient, user in patients:
        result.append({
            "patient_id": patient.id,
            "username": user.username,
            "email": user.email,
            "phone": patient.phone,
            "age": patient.age,
            "gender": patient.gender,
            "is_active": user.is_active,
            "is_blacklisted": user.is_blacklisted,
        })

    return jsonify(result), 200


@admin_bp.route("/appointments", methods=["GET"])
@login_required(role="admin")
def all_appointments():
    appointments = Appointment.query.all()

    result = []
    for appt in appointments:
        doctor = Doctor.query.get(appt.doctor_id)
        patient = Patient.query.get(appt.patient_id)

        doctor_user = User.query.get(doctor.user_id) if doctor else None
        patient_user = User.query.get(patient.user_id) if patient else None

        result.append({
            "appointment_id": appt.id,
            "doctor_name": doctor_user.username if doctor_user else None,
            "patient_name": patient_user.username if patient_user else None,
            "appointment_date": appt.appointment_date.isoformat(),
            "status": appt.status,
        })

    return jsonify(result), 200

@admin_bp.route("/users/<int:user_id>/status", methods=["PATCH"])
@login_required(role="admin")
def update_user_status(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if "is_active" in data:
        user.is_active = data["is_active"]
    if "is_blacklisted" in data:
        user.is_blacklisted = data["is_blacklisted"]

    db.session.commit()
    return jsonify({"message": "User status updated successfully"}), 200