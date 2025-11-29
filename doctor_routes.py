from flask import Blueprint, render_template,request,redirect,flash,url_for
from flask_login import login_required, current_user
from models import Treatment, db, Patient, Department, Doctor, Appointment, User, DoctorAvailability
from datetime import datetime, timedelta

doctor_bp = Blueprint('doctor', __name__,url_prefix='/doctor')

def doctor_only():
    return current_user.is_authenticated and current_user.role == 'doctor'

@doctor_bp.route("/dashboard")
@login_required
def dashboard():
    if not doctor_only():
        flash("Access denied: Doctors only area.", "danger")
        return redirect(url_for("auth.login"))
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    appointments = Appointment.query.filter_by(doctor_id=doctor.id, status="Booked").all()
    
    return render_template("doctor_dashboard.html", name=current_user.name, appointments=appointments)

@doctor_bp.route("/appointment/<int:appointment_id>", methods=["GET", "POST"])
@login_required
def update_appointment(appointment_id):
    if not doctor_only():
        flash("Access denied: Doctors only area.", "danger")
        return redirect(url_for("auth.login"))
    
    appointment = Appointment.query.get(appointment_id)
    if request.method == "POST":
        diagnosis = request.form.get("diagnosis")
        prescription = request.form.get("prescription")
        notes = request.form.get("notes")
        
        #save treatment 
        treatment = Treatment(
            appointment_id=appointment.id,
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes
        )
        appointment.status = "Completed"
        db.session.add(treatment)
        db.session.commit()
        flash("Appointment updated successfully!", "success")
        return redirect(url_for("doctor.dashboard"))
    
    # Get all previous treatments for this patient (across all appointments)
    patient_history = db.session.query(Treatment, Appointment, Doctor, User, Department) \
        .join(Appointment, Treatment.appointment_id == Appointment.id) \
        .join(Doctor, Appointment.doctor_id == Doctor.id) \
        .join(User, Doctor.user_id == User.id) \
        .join(Department, Doctor.department_id == Department.id) \
        .filter(
            Appointment.patient_id == appointment.patient_id,
            Appointment.status == "Completed"
        ).all()
    
    return render_template("update_treatment.html",
                           appointment=appointment,
                           history=patient_history)

@doctor_bp.route("/cancel/<int:appointment_id>")
@login_required
def cancel_appointment(appointment_id):
    if not doctor_only():
        flash("Access denied: Doctors only area.", "danger")
        return redirect(url_for("auth.login"))
    
    appointment = Appointment.query.get(appointment_id)
    appointment.status = "Cancelled"
    db.session.commit()
    flash("Appointment cancelled successfully!", "success")
    return redirect(url_for("doctor.dashboard"))

@doctor_bp.route("/availability", methods=["GET", "POST"])
@login_required
def manage_availability():
    if not doctor_only():
        flash("Access denied: Doctors only area.", "danger")
        return redirect(url_for("auth.login"))

    doctor = Doctor.query.filter_by(user_id=current_user.id).first()

    if request.method == "POST":
        date = request.form.get("date")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")

        if not date or not start_time or not end_time:
            flash("All fields are required.", "warning")
            return redirect(url_for("doctor.manage_availability"))

        try:
            # basic validation that end is after start
            st = datetime.strptime(start_time, "%H:%M")
            et = datetime.strptime(end_time, "%H:%M")
            if et <= st:
                flash("End time must be after start time.", "warning")
                return redirect(url_for("doctor.manage_availability"))
        except Exception:
            flash("Invalid time format.", "danger")
            return redirect(url_for("doctor.manage_availability"))

        # prevent duplicates
        existing = DoctorAvailability.query.filter_by(
            doctor_id=doctor.id,
            date=date,
            start_time=start_time,
            end_time=end_time
        ).first()
        if existing:
            flash("This slot already exists.", "info")
        else:
            slot = DoctorAvailability(
                doctor_id=doctor.id,
                date=date,
                start_time=start_time,
                end_time=end_time
            )
            db.session.add(slot)
            db.session.commit()
            flash("Availability slot added.", "success")

        return redirect(url_for("doctor.manage_availability"))

    # show next 7 days
    start = datetime.today().date()
    days = [(start + timedelta(days=i)).isoformat() for i in range(7)]
    slots = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.date.in_(days)
    ).all()

    # group by date
    grouped = {d: [] for d in days}
    for s in slots:
        grouped.setdefault(s.date, []).append(s)

    return render_template("doctor_availability.html", days=days, slots_by_date=grouped)

@doctor_bp.route("/availability/delete/<int:slot_id>")
@login_required
def delete_slot(slot_id):
    if not doctor_only():
        flash("Access denied: Doctors only area.", "danger")
        return redirect(url_for("auth.login"))

    slot = DoctorAvailability.query.get(slot_id)
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not slot or slot.doctor_id != doctor.id:
        flash("Slot not found.", "warning")
        return redirect(url_for("doctor.manage_availability"))

    if slot.is_booked:
        flash("Cannot delete a booked slot.", "danger")
        return redirect(url_for("doctor.manage_availability"))

    db.session.delete(slot)
    db.session.commit()
    flash("Slot deleted.", "info")
    return redirect(url_for("doctor.manage_availability"))