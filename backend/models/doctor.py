from . import db

class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    specialization = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    availability = db.Column(db.Text, nullable=True)
   
    appointments = db.relationship(
        "Appointment",
        backref="doctor",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Doctor {self.name} - {self.specialization}>"