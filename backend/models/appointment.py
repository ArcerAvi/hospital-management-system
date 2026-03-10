from . import db

class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    #appointment_date = db.Column(db.String(50), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="scheduled")

    treatments = db.relationship(
        "Treatment",
        backref="appointment",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Appointment Doctor {self.doctor_id} - Patient {self.patient_id}>"