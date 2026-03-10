from datetime import datetime, timedelta
import json

from app import create_app
from models import db
from models.user import User
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from models.treatment import Treatment


def login_session(client, user_id, role):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["role"] = role


def make_test_app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False
    return app


def seed_data():
    admin = User(
        username="admin1",
        email="admin1@example.com",
        password="admin123",
        role="admin",
        is_active=True,
        is_blacklisted=False
    )

    doctor_user = User(
        username="doc1",
        email="doc1@example.com",
        password="doc123",
        role="doctor",
        is_active=True,
        is_blacklisted=False
    )

    patient_user = User(
        username="pat1",
        email="pat1@example.com",
        password="pat123",
        role="patient",
        is_active=True,
        is_blacklisted=False
    )

    db.session.add_all([admin, doctor_user, patient_user])
    db.session.flush()

    doctor = Doctor(
        user_id=doctor_user.id,
        name="Doctor One",
        specialization="Cardiology",
        phone="1234567890",
        availability="[]"
    )

    patient = Patient(
        user_id=patient_user.id,
        name="Patient One",
        age=30,
        gender="Male",
        phone="9999999999",
        address="Rajpura"
    )

    db.session.add_all([doctor, patient])
    db.session.flush()

    slot = (datetime.utcnow() + timedelta(days=1)).replace(microsecond=0, second=0)
    doctor.availability = json.dumps([slot.isoformat()])

    appointment = Appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        appointment_date=slot,
        status="scheduled"
    )

    db.session.add(appointment)
    db.session.commit()

    return admin, doctor_user, patient_user, doctor, patient, appointment, slot


def test_patient_registration_creates_user_and_patient():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()

        client = app.test_client()

        response = client.post("/auth/register/patient", json={
            "username": "pat2",
            "email": "pat2@example.com",
            "password": "pat123",
            "name": "Pat Two",
            "age": 25,
            "gender": "Female",
            "phone": "8888888888",
            "address": "Patiala"
        })

        assert response.status_code == 201

        user = User.query.filter_by(email="pat2@example.com").first()
        assert user is not None
        assert user.role == "patient"

        patient = Patient.query.filter_by(user_id=user.id).first()
        assert patient is not None
        assert patient.name == "Pat Two"


def test_admin_dashboard():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        admin, _, _, _, _, _, _ = seed_data()

        client = app.test_client()
        login_session(client, admin.id, "admin")

        response = client.get("/admin/dashboard")
        assert response.status_code == 200

        data = response.get_json()
        assert "total_doctors" in data
        assert "total_patients" in data
        assert "total_appointments" in data


def test_admin_can_add_doctor():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        admin, _, _, _, _, _, _ = seed_data()

        client = app.test_client()
        login_session(client, admin.id, "admin")

        response = client.post("/admin/doctors", json={
            "username": "doc2",
            "email": "doc2@example.com",
            "password": "doc234",
            "specialization": "Dermatology",
            "phone": "7777777777"
        })

        assert response.status_code == 201

        user = User.query.filter_by(email="doc2@example.com").first()
        assert user is not None
        assert user.role == "doctor"

        doctor = Doctor.query.filter_by(user_id=user.id).first()
        assert doctor is not None
        assert doctor.specialization == "Dermatology"


def test_admin_can_search_doctors():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        admin, _, _, _, _, _, _ = seed_data()

        client = app.test_client()
        login_session(client, admin.id, "admin")

        response = client.get("/admin/doctors/search?q=Cardio")
        assert response.status_code == 200

        data = response.get_json()
        assert len(data) >= 1


def test_admin_can_search_patients():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        admin, _, _, _, _, _, _ = seed_data()

        client = app.test_client()
        login_session(client, admin.id, "admin")

        response = client.get("/admin/patients/search?q=pat1")
        assert response.status_code == 200

        data = response.get_json()
        assert len(data) >= 1


def test_admin_can_blacklist_user():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        admin, doctor_user, _, _, _, _, _ = seed_data()

        client = app.test_client()
        login_session(client, admin.id, "admin")

        response = client.patch(
            f"/admin/users/{doctor_user.id}/status",
            json={"is_active": False, "is_blacklisted": True}
        )

        assert response.status_code == 200

        updated_user = User.query.get(doctor_user.id)
        assert updated_user.is_active is False
        assert updated_user.is_blacklisted is True


def test_doctor_can_view_dashboard():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        _, doctor_user, _, _, _, _, _ = seed_data()

        client = app.test_client()
        login_session(client, doctor_user.id, "doctor")

        response = client.get("/doctor/dashboard")
        assert response.status_code == 200


def test_doctor_can_view_upcoming_appointments():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        _, doctor_user, _, _, _, _, _ = seed_data()

        client = app.test_client()
        login_session(client, doctor_user.id, "doctor")

        response = client.get("/doctor/appointments/upcoming")
        assert response.status_code == 200

        data = response.get_json()
        assert len(data) >= 1


def test_doctor_can_mark_appointment_completed():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        _, doctor_user, _, _, _, appointment, _ = seed_data()

        client = app.test_client()
        login_session(client, doctor_user.id, "doctor")

        response = client.patch(
            f"/doctor/appointments/{appointment.id}/status",
            json={"status": "completed"}
        )

        assert response.status_code == 200

        updated = Appointment.query.get(appointment.id)
        assert updated.status == "completed"


def test_doctor_can_add_treatment():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        _, doctor_user, _, _, _, appointment, _ = seed_data()

        client = app.test_client()
        login_session(client, doctor_user.id, "doctor")

        response = client.post(
            f"/doctor/appointments/{appointment.id}/treatment",
            json={
                "diagnosis": "Viral fever",
                "prescription": "Paracetamol",
                "notes": "Rest for 3 days"
            }
        )

        assert response.status_code == 200

        treatment = Treatment.query.filter_by(appointment_id=appointment.id).first()
        assert treatment is not None
        assert treatment.diagnosis == "Viral fever"


def test_doctor_can_set_availability():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        _, doctor_user, _, _, _, _, _ = seed_data()

        client = app.test_client()
        login_session(client, doctor_user.id, "doctor")

        slot1 = (datetime.utcnow() + timedelta(days=1)).replace(microsecond=0, second=0).isoformat()
        slot2 = (datetime.utcnow() + timedelta(days=2)).replace(microsecond=0, second=0).isoformat()

        response = client.post("/doctor/availability", json={
            "availability": [slot1, slot2]
        })

        assert response.status_code == 200


def test_patient_can_view_profile():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        _, _, patient_user, _, _, _, _ = seed_data()

        client = app.test_client()
        login_session(client, patient_user.id, "patient")

        response = client.get("/patient/profile")
        assert response.status_code == 200


def test_patient_can_browse_doctors():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        _, _, patient_user, _, _, _, _ = seed_data()

        client = app.test_client()
        login_session(client, patient_user.id, "patient")

        response = client.get("/patient/doctors?specialization=Cardio")
        assert response.status_code == 200

        data = response.get_json()
        assert len(data) >= 1


def test_patient_can_view_doctor_availability():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        _, _, patient_user, doctor, _, _, slot = seed_data()

        client = app.test_client()
        login_session(client, patient_user.id, "patient")

        response = client.get(f"/patient/doctors/{doctor.id}/availability")
        assert response.status_code == 200

        data = response.get_json()
        assert slot.isoformat() in data["availability"]


def test_patient_can_book_appointment():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()

        _, doctor_user, patient_user, doctor, patient, _, _ = seed_data()

        client = app.test_client()
        login_session(client, patient_user.id, "patient")

        new_slot = (datetime.utcnow() + timedelta(days=2)).replace(microsecond=0, second=0)
        doctor.availability = json.dumps([new_slot.isoformat()])
        db.session.commit()

        response = client.post("/patient/appointments", json={
            "doctor_id": doctor.id,
            "appointment_date": new_slot.isoformat()
        })

        assert response.status_code == 201

        appointment = Appointment.query.filter_by(
            doctor_id=doctor.id,
            patient_id=patient.id,
            appointment_date=new_slot
        ).first()

        assert appointment is not None
        assert appointment.status == "scheduled"


def test_patient_can_cancel_appointment():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        _, _, patient_user, _, _, appointment, _ = seed_data()

        client = app.test_client()
        login_session(client, patient_user.id, "patient")

        response = client.patch(f"/patient/appointments/{appointment.id}/cancel")
        assert response.status_code == 200

        updated = Appointment.query.get(appointment.id)
        assert updated.status == "cancelled"


def test_patient_can_reschedule_appointment():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        _, _, patient_user, doctor, _, appointment, _ = seed_data()

        client = app.test_client()
        login_session(client, patient_user.id, "patient")

        new_slot = (datetime.utcnow() + timedelta(days=3)).replace(microsecond=0, second=0)
        doctor.availability = json.dumps([new_slot.isoformat()])
        db.session.commit()

        response = client.patch(
            f"/patient/appointments/{appointment.id}/reschedule",
            json={"appointment_date": new_slot.isoformat()}
        )

        assert response.status_code == 200

        updated = Appointment.query.get(appointment.id)
        assert updated.appointment_date == new_slot


def test_patient_can_view_treatment_history():
    app = make_test_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        _, _, patient_user, _, patient, appointment, _ = seed_data()

        treatment = Treatment(
            appointment_id=appointment.id,
            diagnosis="Migraine",
            prescription="Painkiller",
            notes="Avoid stress"
        )
        db.session.add(treatment)
        db.session.commit()

        client = app.test_client()
        login_session(client, patient_user.id, "patient")

        response = client.get("/patient/treatments")
        assert response.status_code == 200

        data = response.get_json()
        assert len(data) >= 1
        assert data[0]["diagnosis"] == "Migraine"