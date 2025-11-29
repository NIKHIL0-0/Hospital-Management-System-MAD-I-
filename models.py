# models.py

# This file is responsible for:
# 1. Creating a connection to SQLite using SQLAlchemy
# 2. Defining our database tables (right now: only "User")
# 3. Creating the tables and a default admin user the first time the app runs

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from sqlalchemy import UniqueConstraint

# db is our main database object.
# Other files will import this "db" to define tables or run queries.
db = SQLAlchemy()


class User(db.Model, UserMixin):
    """
    User table stores ALL users:
    - Admin
    - Doctors
    - Patients

    We use a 'role' column to differentiate.
    """
    __tablename__ = "users"  # optional, just sets the table name

    # Primary key (unique id for each user)
    id = db.Column(db.Integer, primary_key=True)

    # Basic info
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

    # Hashed password (never store plain password)
    password = db.Column(db.String(255), nullable=False)

    # "admin", "doctor", "patient"
    role = db.Column(db.String(20), nullable=False, default="patient")

    # If we want to "blacklist" someone, we can set this to False
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        # This is just for debugging prints
        return f"<User {self.id} {self.email} {self.role}>"


def init_db():
    """
    This function will be called from app.py once,
    when the application starts.

    It will:
    1. Create all tables (if not already there)
    2. Create one default admin user (if not present)
    3. Create sample departments (if not present)
    """
    # Create tables using SQLAlchemy models
    db.create_all()
    
    # Migration: Add missing columns to patients table if needed (for existing DBs)
    try:
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('patients')]
        with db.engine.connect() as conn:
            if 'phone' not in columns:
                conn.execute(db.text("ALTER TABLE patients ADD COLUMN phone VARCHAR(20)"))
                print("Migration: Added 'phone' column")
            if 'height' not in columns:
                conn.execute(db.text("ALTER TABLE patients ADD COLUMN height VARCHAR(20)"))
                print("Migration: Added 'height' column")
            if 'weight' not in columns:
                conn.execute(db.text("ALTER TABLE patients ADD COLUMN weight VARCHAR(20)"))
                print("Migration: Added 'weight' column")
            if 'special_notes' not in columns:
                conn.execute(db.text("ALTER TABLE patients ADD COLUMN special_notes TEXT"))
                print("Migration: Added 'special_notes' column")
            conn.commit()
    except Exception as e:
        print(f"Migration check failed or not needed: {e}")

    # Check if any admin user already exists
    existing_admin = User.query.filter_by(role="admin").first()

    if not existing_admin:
        # No admin — create one with default email & password
        admin = User(
            name="Admin",
            email="admin@hms.com",
            # "admin123" will be the login password for this admin
            password=generate_password_hash("admin123"),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()
    
    # Create sample departments if they don't exist
    dept_count = Department.query.count()
    
    if dept_count == 0:
        print("Creating sample departments...")
        departments = [
            Department(name="Cardiology", description="Heart and cardiovascular system"),
            Department(name="Neurology", description="Brain and nervous system"), 
            Department(name="Orthopedics", description="Bones, joints, and muscles"),
            Department(name="Pediatrics", description="Children's health"),
            Department(name="General Medicine", description="General medical care")
        ]
        for dept in departments:
            db.session.add(dept)
        db.session.commit()
        print("Sample departments created.")
        print(f"New department count: {Department.query.count()}")
        
        # Create sample doctors for each department
        print("Creating sample doctors...")
        sample_doctors_data = [
            ("Dr. John Smith", "john.smith@hospital.com", 1, 10, "Mon-Fri 9AM-5PM"),  # Cardiology
            ("Dr. Sarah Johnson", "sarah.johnson@hospital.com", 2, 8, "Mon-Wed-Fri 10AM-4PM"),  # Neurology
            ("Dr. Mike Wilson", "mike.wilson@hospital.com", 3, 12, "Tue-Thu-Sat 8AM-6PM"),  # Orthopedics
            ("Dr. Emily Davis", "emily.davis@hospital.com", 4, 6, "Mon-Fri 8AM-3PM"),  # Pediatrics
            ("Dr. Robert Brown", "robert.brown@hospital.com", 5, 15, "Daily 9AM-5PM"),  # General Medicine
        ]
        
        for name, email, dept_id, experience, availability in sample_doctors_data:
            # Create User record for doctor
            doctor_user = User(
                name=name,
                email=email,
                password=generate_password_hash("doctor123"),
                role="doctor"
            )
            db.session.add(doctor_user)
            db.session.flush()  # Get the user ID
            
            # Create Doctor record
            doctor = Doctor(
                user_id=doctor_user.id,
                department_id=dept_id,
                experience=experience,
                availability=availability
            )
            db.session.add(doctor)
        
        db.session.commit()
    
    # Create sample doctors if they don't exist (separate from departments)  
    doctor_count = Doctor.query.count()
    
    if doctor_count == 0:
        print("Creating sample doctors...")
        sample_doctors_data = [
            ("Dr. John Smith", "john.smith@hospital.com", 1, 10, "Mon-Fri 9AM-5PM"),  # Cardiology
            ("Dr. Sarah Johnson", "sarah.johnson@hospital.com", 2, 8, "Mon-Wed-Fri 10AM-4PM"),  # Neurology
            ("Dr. Mike Wilson", "mike.wilson@hospital.com", 3, 12, "Tue-Thu-Sat 8AM-6PM"),  # Orthopedics
            ("Dr. Emily Davis", "emily.davis@hospital.com", 4, 6, "Mon-Fri 8AM-3PM"),  # Pediatrics
            ("Dr. Robert Brown", "robert.brown@hospital.com", 5, 15, "Daily 9AM-5PM"),  # General Medicine
        ]
        
        for name, email, dept_id, experience, availability in sample_doctors_data:
            # Check if doctor user already exists
            existing_doctor_user = User.query.filter_by(email=email).first()
            if not existing_doctor_user:
                # Create User record for doctor
                doctor_user = User(
                    name=name,
                    email=email,
                    password=generate_password_hash("doctor123"),
                    role="doctor"
                )
                db.session.add(doctor_user)
                db.session.flush()  # Get the user ID
                
                # Create Doctor record
                doctor = Doctor(
                    user_id=doctor_user.id,
                    department_id=dept_id,
                    experience=experience,
                    availability=availability
                )
                db.session.add(doctor)
        
        db.session.commit()

class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

class Doctor(db.Model):
    __tablename__ = "doctors"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    experience = db.Column(db.Integer, nullable=False) 
    availability = db.Column(db.String(100), nullable=True)
    
    # Relationships
    user = db.relationship("User", backref="doctor_profile")
    department = db.relationship("Department", backref="doctors")

class Patient(db.Model):
    __tablename__ = "patients"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(255))
    blood_group = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    height = db.Column(db.String(20))
    weight = db.Column(db.String(20))
    special_notes = db.Column(db.Text)
    
    # Relationship
    user = db.relationship("User", backref="patient_profile")

class Appointment(db.Model):
    __tablename__ = "appointments"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="Booked")
    
    # Relationships
    patient = db.relationship("Patient", backref="appointments")
    doctor = db.relationship("Doctor", backref="appointments") 

class Treatment(db.Model):
    __tablename__ = "treatments"
    id = db.Column(db.Integer, primary_key=True)
    appointment_id=db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    diagnosis=db.Column(db.String(255))
    prescription=db.Column(db.String(255), nullable=True)
    notes=db.Column(db.String(500), nullable=True)

class DoctorAvailability(db.Model):
    __tablename__ = "doctor_availability"
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    # Store as ISO strings to stay consistent with current Appointment schema
    date = db.Column(db.String(20), nullable=False)  # YYYY-MM-DD
    start_time = db.Column(db.String(10), nullable=False)  # HH:MM
    end_time = db.Column(db.String(10), nullable=False)    # HH:MM
    is_booked = db.Column(db.Boolean, default=False, nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)

    doctor = db.relationship("Doctor", backref="availabilities")
    appointment = db.relationship("Appointment", backref="availability", uselist=False)

    __table_args__ = (
        UniqueConstraint('doctor_id', 'date', 'start_time', 'end_time', name='uq_doctor_slot'),
    )
