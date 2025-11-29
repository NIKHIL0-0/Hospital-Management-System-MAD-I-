# Hospital Management System

A Flask-based web application for managing hospital operations including patient registration, doctor scheduling, appointment booking, and treatment records.

## Features

- **Role-Based Access Control**: Admin, Doctor, and Patient roles with specific permissions
- **Appointment Management**: Book, reschedule, and cancel appointments with conflict prevention
- **Doctor Availability**: Weekly time slot management system
- **Treatment Records**: Diagnosis, prescriptions, and clinical notes
- **Patient Profiles**: Comprehensive medical information including allergies and vitals
- **Admin Dashboard**: Statistics, search, and management tools
- **Analytics**: Visual insights with Chart.js (booking trends, department distribution, hourly heatmap)

## Tech Stack

- **Backend**: Flask 3.0.0
- **Database**: SQLite (SQLAlchemy ORM)
- **Authentication**: Flask-Login
- **Frontend**: Jinja2, Bootstrap 5.3.0, Chart.js 4.4.0
- **Security**: Werkzeug password hashing (PBKDF2)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/23f3001617/Hospital-Management-System-MAD-I-.git
cd Hospital-Management-System-MAD-I-
```

2. Create and activate virtual environment (optional but recommended):
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Access the application at `http://127.0.0.1:5000`

## Default Credentials

- **Admin**: 
  - Email: `admin@hms.com`
  - Password: `admin123`

- **Sample Doctor**:
  - Email: `john.smith@hospital.com`
  - Password: `doctor123`

- **Patient**: Register a new account via the registration page

## Database Schema

The application uses SQLite with 7 tables:
- `users` - Authentication and role management
- `patients` - Patient medical information
- `doctors` - Doctor profiles and experience
- `departments` - Medical specializations
- `appointments` - Scheduled consultations
- `treatments` - Medical records and prescriptions
- `doctor_availability` - Time slot management

The database is created automatically on first run with sample data.

## Project Structure

```
HospitalManagementSystem/
├── app.py                 # Application entry point
├── models.py              # Database models
├── auth.py                # Authentication routes
├── admin_routes.py        # Admin functionality
├── doctor_routes.py       # Doctor workflows
├── patient_routes.py      # Patient features
├── templates/             # Jinja2 HTML templates
├── static/
│   └── css/
│       └── style.css     # Custom styling
├── requirements.txt       # Python dependencies
└── README.md
```

## Usage Guide

### Admin Workflow
1. Login with admin credentials
2. Add/manage doctors and departments
3. View all appointments and filter by status
4. Search for doctors or patients
5. Access analytics dashboard for insights
6. Manage patient accounts (edit, activate/deactivate, delete)

### Doctor Workflow
1. Login with doctor credentials
2. Manage weekly availability (publish time slots)
3. View upcoming appointments
4. Mark appointments as completed
5. Add treatment records (diagnosis, prescriptions, notes)
6. View patient history and profiles

### Patient Workflow
1. Register a new account
2. Complete profile with medical information
3. Search for doctors by name or department
4. Book appointments from available time slots
5. Reschedule or cancel appointments
6. View appointment history and treatment records
7. Edit profile information

## Database Reset

To reset the database and start fresh:

**Windows:**
```powershell
Remove-Item hms.db -ErrorAction SilentlyContinue; python app.py
```

**Linux/Mac:**
```bash
rm -f hms.db && python app.py
```

## Security Notes

- Passwords are hashed using Werkzeug's PBKDF2-SHA256
- SQL injection prevention via SQLAlchemy ORM
- Session management with Flask-Login
- Role-based access control on all routes

## License

This project is created for educational purposes as part of the Modern Application Development course.

## Author

Roll Number: 23f3001617
