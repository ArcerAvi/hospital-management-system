import json
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from models import db
from models.user import User
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from models.treatment import Treatment
from routes.utils import login_required

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")

@patient_bp.route("/dashboard", methods=["GET"])
def patient_dashboard():
    return {"message": "Patient dashboard route placeholder."}

def get_logged_in_patient():
    user_id = session.get("user_id")
    return Patient.query.filter_by(user_id=user_id).first()

@patient_bp.route("/profile", methods=["GET"])
@login_required(role="patient")
def get_profile():
    patient = get_logged_in_patient()
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404

    user = User.query.get(patient.user_id)

    return jsonify({
        "patient_id": patient.id,
        "username": user.username,
        "email": user.email,
        "age": patient.age,
        "gender": patient.gender,
        "phone": patient.phone,
        "address": patient.address,
    }), 200


@patient_bp.route("/profile", methods=["PUT"])
@login_required(role="patient")
def update_profile():
    patient = get_logged_in_patient()
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404

    user = User.query.get(patient.user_id)
    data = request.get_json()

    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]
    if "age" in data:
        patient.age = data["age"]
    if "gender" in data:
        patient.gender = data["gender"]
    if "phone" in data:
        patient.phone = data["phone"]
    if "address" in data:
        patient.address = data["address"]

    db.session.commit()
    return jsonify({"message": "Profile updated successfully"}), 200


@patient_bp.route("/doctors", methods=["GET"])
@login_required(role="patient")
def browse_doctors():
    specialization = request.args.get("specialization", "").strip()

    query = db.session.query(Doctor, User).join(User, Doctor.user_id == User.id)
    query = query.filter(User.is_active == True, User.is_blacklisted == False)

    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))

    doctors = query.all()

    result = []
    for doctor, user in doctors:
        result.append({
            "doctor_id": doctor.id,
            "name": user.username,
            "email": user.email,
            "specialization": doctor.specialization,
            "phone": doctor.phone,
        })

    return jsonify(result), 200


@patient_bp.route("/doctors/<int:doctor_id>/availability", methods=["GET"])
@login_required(role="patient")
def view_availability(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)

    try:
        availability = json.loads(doctor.availability) if doctor.availability else []
    except Exception:
        availability = []

    return jsonify({
        "doctor_id": doctor.id,
        "availability": availability
    }), 200


@patient_bp.route("/appointments", methods=["POST"])
@login_required(role="patient")
def book_appointment():
    patient = get_logged_in_patient()
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404

    data = request.get_json()
    doctor_id = data.get("doctor_id")
    appointment_date = data.get("appointment_date")

    if not doctor_id or not appointment_date:
        return jsonify({"error": "doctor_id and appointment_date are required"}), 400

    doctor = Doctor.query.get_or_404(doctor_id)
    doctor_user = User.query.get(doctor.user_id)

    if not doctor_user.is_active or doctor_user.is_blacklisted:
        return jsonify({"error": "Doctor is not available for booking"}), 400

    try:
        appointment_dt = datetime.fromisoformat(appointment_date)
    except ValueError:
        return jsonify({"error": "Invalid appointment_date format"}), 400

    try:
        availability = json.loads(doctor.availability) if doctor.availability else []
    except Exception:
        availability = []

    if appointment_dt.isoformat() not in availability:
        return jsonify({"error": "Selected slot is not available"}), 400

    existing = Appointment.query.filter_by(
        doctor_id=doctor.id,
        appointment_date=appointment_dt,
        status="scheduled"
    ).first()

    if existing:
        return jsonify({"error": "Slot already booked"}), 409

    appointment = Appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        appointment_date=appointment_dt,
        status="scheduled"
    )

    db.session.add(appointment)
    db.session.commit()

    return jsonify({"message": "Appointment booked successfully", "appointment_id": appointment.id}), 201


@patient_bp.route("/appointments/<int:appointment_id>/cancel", methods=["PATCH"])
@login_required(role="patient")
def cancel_appointment(appointment_id):
    patient = get_logged_in_patient()
    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.patient_id != patient.id:
        return jsonify({"error": "Unauthorized appointment access"}), 403

    appointment.status = "cancelled"
    db.session.commit()

    return jsonify({"message": "Appointment cancelled successfully"}), 200


@patient_bp.route("/appointments/<int:appointment_id>/reschedule", methods=["PATCH"])
@login_required(role="patient")
def reschedule_appointment(appointment_id):
    patient = get_logged_in_patient()
    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.patient_id != patient.id:
        return jsonify({"error": "Unauthorized appointment access"}), 403

    data = request.get_json()
    new_date = data.get("appointment_date")
    if not new_date:
        return jsonify({"error": "appointment_date is required"}), 400

    try:
        new_dt = datetime.fromisoformat(new_date)
    except ValueError:
        return jsonify({"error": "Invalid appointment_date format"}), 400

    doctor = Doctor.query.get(appointment.doctor_id)
    try:
        availability = json.loads(doctor.availability) if doctor.availability else []
    except Exception:
        availability = []

    if new_dt.isoformat() not in availability:
        return jsonify({"error": "New slot is not available"}), 400

    clash = Appointment.query.filter_by(
        doctor_id=doctor.id,
        appointment_date=new_dt,
        status="scheduled"
    ).first()

    if clash and clash.id != appointment.id:
        return jsonify({"error": "New slot already booked"}), 409

    appointment.appointment_date = new_dt
    appointment.status = "scheduled"
    db.session.commit()

    return jsonify({"message": "Appointment rescheduled successfully"}), 200


@patient_bp.route("/treatments", methods=["GET"])
@login_required(role="patient")
def treatment_history():
    patient = get_logged_in_patient()
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404

    appointments = Appointment.query.filter_by(patient_id=patient.id).all()
    appointment_ids = [appt.id for appt in appointments]

    treatments = Treatment.query.filter(Treatment.appointment_id.in_(appointment_ids)).all() if appointment_ids else []

    result = []
    for treatment in treatments:
        appointment = Appointment.query.get(treatment.appointment_id)
        doctor = Doctor.query.get(appointment.doctor_id) if appointment else None
        doctor_user = User.query.get(doctor.user_id) if doctor else None

        result.append({
            "treatment_id": treatment.id,
            "appointment_id": treatment.appointment_id,
            "doctor_name": doctor_user.username if doctor_user else None,
            "diagnosis": treatment.diagnosis,
            "prescription": treatment.prescription,
            "notes": treatment.notes,
        })

    return jsonify(result), 200