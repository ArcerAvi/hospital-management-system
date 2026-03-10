# Hospital Management System (HMS)

## Project Overview

The **Hospital Management System (HMS)** is a web application designed to simplify the management of hospital operations such as user authentication, appointment management, doctor and patient records, and treatment tracking.

This project is being developed as part of the **Modern Application Development II (MAD-II)** course.

The system follows a **frontend–backend architecture**, where the frontend handles the user interface and the backend manages the application logic and data.

---

## Technology Stack

### Frontend

* **Vue.js** (via CDN)
* **Bootstrap** (via CDN)
* **HTML / JavaScript**

### Backend

* **Python**
* **Flask**
* **Flask-CORS**
* **Celery** (for background tasks)
* **Redis** (message broker for Celery)

---

## Project Structure

```
hospital-management-system/
│
├── frontend/
│   ├── index.html
│   └── src/
│       ├── app.js
│       ├── api.js
│       └── components/
│           ├── login.js
│           ├── admin-dashboard.js
│           ├── doctor-dashboard.js
│           └── patient-dashboard.js
│
├── backend/
│   ├── routes/
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── doctor.py
│   │   └── patient.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── doctor.py
│   │   ├── patient.py
│   │   ├── appointment.py
│   │   └── treatment.py
│   │
│   ├── app.py
│   ├── config.py
│   ├── tasks.py
│   └── requirements.txt
│
├── README.md
└── .gitignore
```

---

## System Architecture

The application follows a **modular architecture** with clear separation between frontend and backend components.

* The **frontend** provides the user interface using Vue.js and communicates with the backend through API calls.
* The **backend** provides RESTful routes using Flask.
* **Routes** handle incoming API requests.
* **Models** represent the core data entities such as users, doctors, patients, appointments, and treatments.
* **Celery tasks** will be used for asynchronous background processing such as notifications or scheduled jobs.

---

## Features (Planned)

The following features are planned for the system:

* User authentication (admin, doctor, patient)
* Admin dashboard for system management
* Doctor dashboard for managing appointments and treatments
* Patient dashboard for viewing appointments and medical records
* Appointment scheduling
* Treatment history tracking
* Background tasks for notifications and reports

---

## Running the Backend (Development)

1. Navigate to the backend folder

```
cd backend
```

2. Install dependencies

```
pip install -r requirements.txt
```

3. Run the Flask application

```
python app.py
```

The backend server will start locally.

---

## Development Status

Current progress:

✔ Phase 1 — Project Skeleton Completed

* Folder structure created
* Backend and frontend modules organized
* Placeholder routes and models added
* Basic Flask server running

Upcoming phases will implement full application functionality.

---

## Author

Avi