# patient_routes.py

from flask import Blueprint, render_template, redirect, request, flash, url_for
from flask_login import login_required, current_user
from models import db, User, Patient, Doctor, Department, Appointment, Treatment, DoctorAvailability
from datetime import datetime, timedelta

# All patient-related URLs start with /patient
patient_bp = Blueprint("patient", __name__, url_prefix="/patient")







# Allow only patient role to access patient pages
def patient_only():
    return current_user.is_authenticated and current_user.role == "patient"


@patient_bp.route("/dashboard")
@login_required
def dashboard():
    print(f"Dashboard accessed by user: {current_user.name} (ID: {current_user.id}, Role: {current_user.role})")
    
    if not patient_only():
        print("Access denied: not a patient")
        return "<h1>Unauthorized Access</h1><p>You must be logged in as a patient to access this page.</p><p><a href='/login'>Login</a> | <a href='/register'>Register as Patient</a></p>"

    print("Patient access granted")
    
    # Get all departments for selection
    departments = Department.query.all()
    print(f"Found {len(departments)} departments")

    # Find this patient row via logged-in user_id
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    print(f"Patient record: {'Found' if patient else 'Not found'}")
    
    # If no patient record exists, create one
    if not patient:
        print("Creating new patient record")
        patient = Patient(
            user_id=current_user.id,
            age=25,  # Default age
            address="Not provided",
            blood_group="Unknown"
        )
        db.session.add(patient)
        db.session.commit()
        flash("Patient profile created. Please update your details.", "info")
        print("Patient record created")

    # Upcoming appointments
    upcoming = Appointment.query.filter_by(patient_id=patient.id, status="Booked").all()
    print(f"Upcoming appointments: {len(upcoming)}")

    # Appointment history
    history = Appointment.query.filter(Appointment.patient_id == patient.id,
                                       Appointment.status != "Booked").all()
    print(f"Appointment history: {len(history)}")
    
    # Full medical history (completed appointments with treatment)
    full_history = db.session.query(Treatment, Appointment, Doctor, User, Department) \
        .join(Appointment, Treatment.appointment_id == Appointment.id) \
        .join(Doctor, Appointment.doctor_id == Doctor.id) \
        .join(User, Doctor.user_id == User.id) \
        .join(Department, Doctor.department_id == Department.id) \
        .filter(
            Appointment.patient_id == patient.id,
            Appointment.status == "Completed"
        ).all()
    print(f"Full medical history records: {len(full_history)}")
    
    print("Rendering patient_dashboard.html template")
    return render_template("patient_dashboard.html",
                           name=current_user.name,
                           departments=departments,
                           upcoming=upcoming,
                           history=history,
                           full_history=full_history)


# After selecting a department → list doctors
@patient_bp.route("/doctors", methods=["GET", "POST"])
@login_required
def list_doctors():
    if request.method == "POST":
        department_id = request.form.get("department_id")
        if not department_id:
            flash("Please select a department.", "warning")
            return redirect(url_for("patient.dashboard"))
    else:
        # GET request - show all doctors or redirect to dashboard
        return redirect(url_for("patient.dashboard"))
    
    print(f"Searching for doctors in department ID: {department_id}")
    doctors = Doctor.query.filter_by(department_id=department_id).all()
    department = Department.query.get(department_id)
    # Compute next 7 days availability counts per doctor
    start = datetime.today().date()
    days = [(start + timedelta(days=i)).isoformat() for i in range(7)]
    availability_by_doctor = {}
    for d in doctors:
        count = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == d.id,
            DoctorAvailability.date.in_(days),
            DoctorAvailability.is_booked == False
        ).count()
        availability_by_doctor[d.id] = count
    
    print(f"Found {len(doctors)} doctors in {department.name if department else 'Unknown'} department")
    
    return render_template("doctor_list.html", 
                         doctors=doctors, 
                         department=department,
                         availability_by_doctor=availability_by_doctor)


# Book appointment with selected doctor
@patient_bp.route("/book/<int:doctor_id>", methods=["GET", "POST"])
@login_required
def book_appointment(doctor_id):
    patient = Patient.query.filter_by(user_id=current_user.id).first()

    # Show next 7 days of available slots for this doctor
    start = datetime.today().date()
    days = [(start + timedelta(days=i)).isoformat() for i in range(7)]
    slots = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.date.in_(days),
        DoctorAvailability.is_booked == False
    ).order_by(DoctorAvailability.date, DoctorAvailability.start_time).all()

    # Fallback manual booking via POST (for legacy template support)
    if request.method == "POST":
        date = request.form.get("date")
        time = request.form.get("time")

        conflict = Appointment.query.filter_by(
            doctor_id=doctor_id,
            date=date,
            time=time,
            status="Booked"
        ).first()
        if conflict:
            flash("This time slot is already booked.", "danger")
        else:
            appt = Appointment(patient_id=patient.id, doctor_id=doctor_id, date=date, time=time)
            db.session.add(appt)
            db.session.commit()
            flash("Appointment booked successfully!", "success")
            return redirect(url_for("patient.dashboard"))

    return render_template("book_appointment.html", doctor_id=doctor_id, slots=slots)


@patient_bp.route("/book_slot/<int:availability_id>")
@login_required
def book_slot(availability_id):
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    slot = DoctorAvailability.query.get(availability_id)
    if not slot or slot.is_booked:
        flash("Slot is no longer available.", "danger")
        return redirect(url_for("patient.dashboard"))

    # Create appointment from slot
    appt = Appointment(
        patient_id=patient.id,
        doctor_id=slot.doctor_id,
        date=slot.date,
        time=f"{slot.start_time}-{slot.end_time}"
    )
    db.session.add(appt)
    db.session.flush()
    slot.is_booked = True
    slot.appointment_id = appt.id
    db.session.commit()
    flash("Appointment booked.", "success")
    return redirect(url_for("patient.dashboard"))


# Cancel appointment
@patient_bp.route("/cancel/<int:appointment_id>")
@login_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    appointment.status = "Cancelled"
    # Free linked availability slot if any
    slot = DoctorAvailability.query.filter_by(appointment_id=appointment.id).first()
    if slot:
        slot.is_booked = False
        slot.appointment_id = None
    db.session.commit()
    flash("Appointment cancelled.", "info")
    return redirect(url_for("patient.dashboard"))


@patient_bp.route("/reschedule/<int:appointment_id>", methods=["GET", "POST"])
@login_required
def reschedule_appointment(appointment_id):
    appt = Appointment.query.get(appointment_id)
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not appt or appt.patient_id != patient.id:
        flash("Not authorized to reschedule this appointment.", "danger")
        return redirect(url_for("patient.dashboard"))

    # available slots for same doctor next 7 days
    start = datetime.today().date()
    days = [(start + timedelta(days=i)).isoformat() for i in range(7)]
    available = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == appt.doctor_id,
        DoctorAvailability.date.in_(days),
        DoctorAvailability.is_booked == False
    ).order_by(DoctorAvailability.date, DoctorAvailability.start_time).all()

    if request.method == "POST":
        new_slot_id = request.form.get("availability_id")
        slot = DoctorAvailability.query.get(int(new_slot_id))
        if not slot or slot.is_booked:
            flash("Selected slot is not available.", "danger")
            return redirect(url_for("patient.reschedule_appointment", appointment_id=appointment_id))

        # free old slot if linked
        old_slot = DoctorAvailability.query.filter_by(appointment_id=appt.id).first()
        if old_slot:
            old_slot.is_booked = False
            old_slot.appointment_id = None

        # assign new slot
        appt.date = slot.date
        appt.time = f"{slot.start_time}-{slot.end_time}"
        slot.is_booked = True
        slot.appointment_id = appt.id
        db.session.commit()
        flash("Appointment rescheduled.", "success")
        return redirect(url_for("patient.dashboard"))

    return render_template("reschedule.html", appointment=appt, slots=available)


# Patient profile management
@patient_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if request.method == "POST":
        patient.age = int(request.form.get("age") or patient.age or 0)
        patient.address = request.form.get("address")
        patient.blood_group = request.form.get("blood_group")
        patient.phone = request.form.get("phone")
        patient.height = request.form.get("height")
        patient.weight = request.form.get("weight")
        patient.special_notes = request.form.get("special_notes")
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("patient.profile"))
    return render_template("patient_profile.html", patient=patient)


# Patient search doctors by name
@patient_bp.route("/search_doctors")
@login_required
def search_doctors():
    q = request.args.get("q", "").strip()
    if not q:
        return redirect(url_for("patient.dashboard"))
    doctors = db.session.query(Doctor).join(User, Doctor.user_id == User.id).filter(User.name.ilike(f"%{q}%")).all()
    return render_template("doctor_list.html", doctors=doctors, department=None)
