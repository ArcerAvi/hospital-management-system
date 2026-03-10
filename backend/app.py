from flask import Flask
from flask_login import LoginManager
from config import Config

from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.doctor import doctor_bp
from routes.patient import patient_bp

from models import db
from models.user import User
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from models.treatment import Treatment

login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_admin(app):
    with app.app_context():
        admin = User.query.filter_by(role="admin").first()

        if not admin:
            admin = User(
                username=app.config["ADMIN_USERNAME"],
                email=app.config["ADMIN_EMAIL"],
                password=app.config["ADMIN_PASSWORD"],
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created successfully.")
        else:
            print("Admin user already exists.")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp) #, url_prefix="/admin"
    app.register_blueprint(doctor_bp) #, url_prefix="/doctor"
    app.register_blueprint(patient_bp) #, url_prefix="/patient"

    @app.route("/")
    def home():
        return {"message": "HMS backend is running successfully"}

    with app.app_context():
        db.create_all()
        create_admin(app)

    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)