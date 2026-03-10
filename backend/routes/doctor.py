import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from models import db
from models.user import User
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from models.treatment import Treatment
from routes.utils import login_required

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")


def get_logged_in_doctor():
    user_id = session.get("user_id")
    return Doctor.query.filter_by(user_id=user_id).first()


@doctor_bp.route("/dashboard", methods=["GET"])
@login_required(role="doctor")
def dashboard():
    doctor = get_logged_in_doctor()
    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    upcoming_count = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status == "scheduled",
        Appointment.appointment_date >= datetime.utcnow()
    ).count()

    completed_count = Appointment.query.filter_by(
        doctor_id=doctor.id,
        status="completed"
    ).count()

    cancelled_count = Appointment.query.filter_by(
        doctor_id=doctor.id,
        status="cancelled"
    ).count()

    return jsonify({
        "doctor_id": doctor.id,
        "upcoming_appointments": upcoming_count,
        "completed_appointments": completed_count,
        "cancelled_appointments": cancelled_count
    }), 200


@doctor_bp.route("/appointments/upcoming", methods=["GET"])
@login_required(role="doctor")
def upcoming_appointments():
    doctor = get_logged_in_doctor()
    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status == "scheduled",
        Appointment.appointment_date >= datetime.utcnow()
    ).order_by(Appointment.appointment_date.asc()).all()

    result = []
    for appt in appointments:
        patient = Patient.query.get(appt.patient_id)
        patient_user = User.query.get(patient.user_id) if patient else None

        result.append({
            "appointment_id": appt.id,
            "patient_name": patient_user.username if patient_user else None,
            "appointment_date": appt.appointment_date.isoformat(),
            "status": appt.status
        })

    return jsonify(result), 200


@doctor_bp.route("/appointments/<int:appointment_id>/status", methods=["PATCH"])
@login_required(role="doctor")
def update_appointment_status(appointment_id):
    doctor = get_logged_in_doctor()
    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.doctor_id != doctor.id:
        return jsonify({"error": "Unauthorized appointment access"}), 403

    data = request.get_json()
    new_status = data.get("status")

    if new_status not in ["completed", "cancelled"]:
        return jsonify({"error": "Invalid status"}), 400

    appointment.status = new_status
    db.session.commit()

    return jsonify({"message": "Appointment status updated"}), 200


@doctor_bp.route("/appointments/<int:appointment_id>/treatment", methods=["POST"])
@login_required(role="doctor")
def add_treatment(appointment_id):
    doctor = get_logged_in_doctor()
    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.doctor_id != doctor.id:
        return jsonify({"error": "Unauthorized appointment access"}), 403

    data = request.get_json()
    diagnosis = data.get("diagnosis")
    prescription = data.get("prescription")
    notes = data.get("notes")

    treatment = Treatment.query.filter_by(appointment_id=appointment.id).first()
    if treatment:
        treatment.diagnosis = diagnosis
        treatment.prescription = prescription
        treatment.notes = notes
    else:
        treatment = Treatment(
            appointment_id=appointment.id,
            #doctor_id=doctor.id,
            #patient_id=appointment.patient_id,
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes
        )
        db.session.add(treatment)

    db.session.commit()
    return jsonify({"message": "Treatment saved successfully"}), 200


@doctor_bp.route("/availability", methods=["POST"])
@login_required(role="doctor")
def set_availability():
    doctor = get_logged_in_doctor()
    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    data = request.get_json()
    availability = data.get("availability")

    if not isinstance(availability, list):
        return jsonify({"error": "Availability must be a list"}), 400

    today = datetime.utcnow().date()
    max_date = today + timedelta(days=7)

    validated = []
    for slot in availability:
        try:
            slot_dt = datetime.fromisoformat(slot)
            if not (today <= slot_dt.date() <= max_date):
                return jsonify({"error": "Availability must be within next 7 days"}), 400
            validated.append(slot_dt.isoformat())
        except ValueError:
            return jsonify({"error": f"Invalid datetime format: {slot}"}), 400

    doctor.availability = json.dumps(validated)
    db.session.commit()

    return jsonify({"message": "Availability updated", "availability": validated}), 200


@doctor_bp.route("/availability", methods=["GET"])
@login_required(role="doctor")
def get_availability():
    doctor = get_logged_in_doctor()
    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    try:
        availability = json.loads(doctor.availability) if doctor.availability else []
    except Exception:
        availability = []

    return jsonify({"doctor_id": doctor.id, "availability": availability}), 200