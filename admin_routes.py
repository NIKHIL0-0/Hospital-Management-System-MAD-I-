from flask import Blueprint, render_template,request,redirect,flash,url_for
from flask_login import login_required,current_user
from models import Department, User, db,Doctor,Appointment,Patient,DoctorAvailability
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime, timedelta

admin_bp=Blueprint("admin",__name__,url_prefix="/admin")

def admin_only():
    return current_user.is_authenticated and current_user.role=="admin"



@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if not admin_only():
        flash("Access denied: Admins only area.","danger")
        return redirect(url_for("auth.login"))
    
    doctor_count=Doctor.query.count()
    patient_count=Patient.query.count()
    appointment_count=Appointment.query.count()

    return render_template("admin_dashboard.html",
                          doctor_count=doctor_count,
                          patient_count=patient_count,
                          appointment_count=appointment_count)

@admin_bp.route("/analytics")
@login_required
def analytics():
    if not admin_only():
        flash("Access denied: Admins only area.","danger")
        return redirect(url_for("auth.login"))

    # Line chart: daily bookings count (last 30 days)
    today = datetime.today().date()
    days = [(today - timedelta(days=i)) for i in range(29, -1, -1)]  # oldest to newest
    day_labels = [d.isoformat() for d in days]
    daily_counts = []
    for d in days:
        cnt = Appointment.query.filter_by(date=d.isoformat()).count()
        daily_counts.append(cnt)

    # Pie chart: number of unique patients per department (based on completed or booked appointments)
    dept_data = []
    dept_labels = []
    departments = Department.query.all()
    for dept in departments:
        # unique patient IDs who have appointments with doctors in this dept
        doctor_ids = [doc.id for doc in dept.doctors]
        if not doctor_ids:
            continue
        patient_ids = db.session.query(Appointment.patient_id).filter(Appointment.doctor_id.in_(doctor_ids)).distinct().all()
        count = len(patient_ids)
        dept_labels.append(dept.name)
        dept_data.append(count)

    # Heatmap: patient volume by hour (aggregate all appointments last 7 days)
    heat_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]  # 7 days
    heat_labels_days = [d.strftime('%Y-%m-%d') for d in heat_days]
    hours = [f"{h:02d}:00" for h in range(0,24)]
    # initialize matrix rows=days, cols=hours
    heatmap = [[0 for _ in hours] for _ in heat_days]
    recent_appts = Appointment.query.filter(Appointment.date.in_([d.isoformat() for d in heat_days])).all()
    for appt in recent_appts:
        # time may be 'HH:MM' or 'HH:MM-HH:MM'
        raw = appt.time.split('-')[0]
        try:
            hour = int(raw.split(':')[0])
        except Exception:
            continue
        # find day index
        try:
            d_index = heat_labels_days.index(appt.date)
            heatmap[d_index][hour] += 1
        except ValueError:
            continue

    return render_template("admin_analytics.html",
                           day_labels=day_labels,
                           daily_counts=daily_counts,
                           dept_labels=dept_labels,
                           dept_data=dept_data,
                           heat_days=heat_labels_days,
                           hours=hours,
                           heatmap=heatmap)

@admin_bp.route("/manage_doctors")
@login_required
def manage_doctors():
    if not admin_only():
        flash("Access denied: Admins only area.","danger")
        return redirect(url_for("auth.login"))
    
    doctors = Doctor.query.all()
    
    doctors_table = ""
    for doctor in doctors:
        doctors_table += f"""
        <tr>
            <td>{doctor.id}</td>
            <td>{doctor.user.name}</td>
            <td>{doctor.user.email}</td>
            <td>{doctor.department.name}</td>
            <td>{doctor.experience} years</td>
            <td>{doctor.availability}</td>
            <td>
                <a href="/admin/edit_doctor/{doctor.id}" class="btn btn-sm btn-warning">Edit</a>
                <a href="/admin/delete_doctor/{doctor.id}" class="btn btn-sm btn-danger" 
                   onclick="return confirm('Are you sure you want to delete this doctor?')">Delete</a>
            </td>
        </tr>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage Doctors</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
            <div class="container-fluid">
                <a class="navbar-brand" href="/">Hospital Management System</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link btn btn-outline-light" href="/logout">Logout</a>
                </div>
            </div>
        </nav>
        
        <div class="container">
            <h2>Manage Doctors</h2>
            
            <div class="mb-3">
                <a href="/admin/dashboard" class="btn btn-secondary">Back to Dashboard</a>
                <a href="/admin/add_doctor" class="btn btn-success">Add New Doctor</a>
            </div>
            
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Department</th>
                            <th>Experience</th>
                            <th>Availability</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {doctors_table}
                    </tbody>
                </table>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

@admin_bp.route("/add_doctor",methods=["GET","POST"])
@login_required
def add_doctor():
    if not admin_only():
        flash("Access denied: Admins only area.","danger")
        return redirect(url_for("auth.login"))
    departments=Department.query.all()

    if request.method=="POST":
        name=request.form.get("name")
        email=request.form.get("email")
        password=generate_password_hash(request.form.get("password"))
        department_id=request.form.get("department_id")
        experience=request.form.get("experience")

        user=User(
            name=name,
            email=email,
            password=password,
            role="doctor"
            )
        db.session.add(user)
        db.session.commit()
        doctor=Doctor(
            user_id=user.id,
            department_id=department_id,
            experience=experience,
            availability="NOT SET"
        )
        db.session.add(doctor)
        db.session.commit()
        flash("Doctor added successfully!","success")
        return redirect(url_for("admin.dashboard"))
    # Create department options for select dropdown
    department_options = "".join([f'<option value="{d.id}">{d.name}</option>' for d in departments])
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Add Doctor</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
            <div class="container-fluid">
                <a class="navbar-brand" href="/">Hospital Management System</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link btn btn-outline-light" href="/logout">Logout</a>
                </div>
            </div>
        </nav>
        
        <div class="container">
            <h3>Add Doctor</h3>
            <form method="POST" class="mt-4">
                <div class="mb-3">
                    <input name="name" class="form-control" placeholder="Doctor Name" required>
                </div>
                <div class="mb-3">
                    <input name="email" class="form-control" placeholder="Email" required>
                </div>
                <div class="mb-3">
                    <input type="password" name="password" class="form-control" placeholder="Password" required>
                </div>
                <div class="mb-3">
                    <input name="experience" class="form-control" placeholder="Experience (years)" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Department</label>
                    <select name="department_id" class="form-select" required>
                        <option value="">Select Department</option>
                        {department_options}
                    </select>
                </div>
                <button type="submit" class="btn btn-success">Add Doctor</button>
                <a href="/admin/dashboard" class="btn btn-secondary ms-2">Cancel</a>
            </form>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

@admin_bp.route("/edit_doctor/<int:doctor_id>",methods=["GET","POST"])
@login_required
def edit_doctor(doctor_id):
    if not admin_only():
        flash("Access denied: Admins only area.","danger")
        return redirect(url_for("auth.login"))
    
    doctor=Doctor.query.get(doctor_id)
    departments=Department.query.all()

    if request.method=="POST":
        doctor.user.name=request.form.get("name")
        doctor.user.email=request.form.get("email")
        doctor.experience=request.form.get("experience")
        doctor.department_id=request.form.get("department_id")
        
        # Handle availability - use custom text if "Custom" is selected
        availability = request.form.get("availability")
        if availability == "Custom":
            doctor.availability = request.form.get("custom_availability")
        else:
            doctor.availability = availability
            
        db.session.commit()
        return f"""
        <script>
            alert("Doctor updated successfully!");
            window.location.href = "/admin/manage_doctors";
        </script>
        """
    
    # Create department options with current selection
    department_options = ""
    for d in departments:
        selected = "selected" if d.id == doctor.department_id else ""
        department_options += f'<option value="{d.id}" {selected}>{d.name}</option>'
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit Doctor</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
            <div class="container-fluid">
                <a class="navbar-brand" href="/">Hospital Management System</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link btn btn-outline-light" href="/logout">Logout</a>
                </div>
            </div>
        </nav>
        
        <div class="container">
            <h3>Edit Doctor</h3>
            <form method="POST" class="mt-4">
                <div class="mb-3">
                    <label class="form-label">Doctor Name</label>
                    <input name="name" class="form-control" value="{doctor.user.name}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Email</label>
                    <input name="email" class="form-control" value="{doctor.user.email}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Experience (years)</label>
                    <input name="experience" class="form-control" value="{doctor.experience}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Department</label>
                    <select name="department_id" class="form-select" required>
                        {department_options}
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Availability</label>
                    <select name="availability" class="form-select" required id="availabilitySelect" onchange="toggleCustomInput()">
                        <option value="Available" {"selected" if doctor.availability == "Available" else ""}>Available</option>
                        <option value="Busy" {"selected" if doctor.availability == "Busy" else ""}>Busy</option>
                        <option value="On Leave" {"selected" if doctor.availability == "On Leave" else ""}>On Leave</option>
                        <option value="NOT SET" {"selected" if doctor.availability == "NOT SET" else ""}>Not Set</option>
                        <option value="Custom" {"selected" if doctor.availability not in ["Available", "Busy", "On Leave", "NOT SET"] else ""}>Custom</option>
                    </select>
                </div>
                <div class="mb-3" id="customAvailabilityDiv" style="display: {'block' if doctor.availability not in ["Available", "Busy", "On Leave", "NOT SET"] else 'none'};">
                    <label class="form-label">Custom Availability Status</label>
                    <input name="custom_availability" class="form-control" id="customAvailabilityInput" 
                           placeholder="Enter custom availability status" 
                           value="{'_' if doctor.availability in ["Available", "Busy", "On Leave", "NOT SET"] else doctor.availability}">
                </div>
                
                <script>
                function toggleCustomInput() {{
                    var select = document.getElementById('availabilitySelect');
                    var customDiv = document.getElementById('customAvailabilityDiv');
                    var customInput = document.getElementById('customAvailabilityInput');
                    
                    if (select.value === 'Custom') {{
                        customDiv.style.display = 'block';
                        customInput.required = true;
                        customInput.focus();
                    }} else {{
                        customDiv.style.display = 'none';
                        customInput.required = false;
                        customInput.value = '';
                    }}
                }}
                </script>
                <button type="submit" class="btn btn-success">Update Doctor</button>
                <a href="/admin/manage_doctors" class="btn btn-secondary ms-2">Cancel</a>
            </form>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

@admin_bp.route("/delete_doctor/<int:doctor_id>")
@login_required
def delete_doctor(doctor_id):
    if not admin_only():
        flash("Access denied: Admins only area.","danger")
        return redirect(url_for("auth.login"))
    
    try:
        doctor=Doctor.query.get(doctor_id)
        if not doctor:
            return f"""
            <script>
                alert("Doctor not found!");
                window.location.href = "/admin/manage_doctors";
            </script>
            """
        
        user=User.query.get(doctor.user_id)
        
        # Get all appointments for this doctor (both past and future)
        all_appointments = Appointment.query.filter_by(doctor_id=doctor_id).all()
        appointment_count = len(all_appointments)
        
        # First, delete all treatments related to this doctor's appointments
        from models import Treatment
        for appointment in all_appointments:
            treatments = Treatment.query.filter_by(appointment_id=appointment.id).all()
            for treatment in treatments:
                db.session.delete(treatment)
        
        # Then delete all appointments for this doctor
        for appointment in all_appointments:
            db.session.delete(appointment)
        
        # Now delete the doctor record
        db.session.delete(doctor)
        # Finally delete the user record
        db.session.delete(user)
        
        db.session.commit()
        
        return f"""
        <script>
            alert("Doctor deleted successfully! {appointment_count} appointments and related treatments were also removed.");
            window.location.href = "/admin/manage_doctors";
        </script>
        """
        
    except Exception as e:
        db.session.rollback()
        return f"""
        <script>
            alert("Error deleting doctor: {str(e)}. Please try again.");
            window.location.href = "/admin/manage_doctors";
        </script>
        """

@admin_bp.route("/appointments")
@login_required
def view_appointments():
    if not admin_only():
        flash("Access denied: Admins only area.","danger")
        return redirect(url_for("auth.login"))
    
    appointments=Appointment.query.all()
    # filters
    status = request.args.get("status")
    when = request.args.get("when")  # upcoming|past|all
    q = Appointment.query
    if status and status != "all":
        q = q.filter_by(status=status)

    # naive split by date relative to today
    from datetime import date
    today = date.today().isoformat()
    if when == "upcoming":
        q = q.filter(Appointment.date >= today)
    elif when == "past":
        q = q.filter(Appointment.date < today)

    appointments = q.all()
    return render_template("admin_appointments.html",appointments=appointments)

@admin_bp.route("/cancel_appointment/<int:appointment_id>")
@login_required
def cancel_appointment(appointment_id):
    if not admin_only():
        flash("Access denied: Admins only area.","danger")
        return redirect(url_for("auth.login"))
    appt = Appointment.query.get(appointment_id)
    if not appt:
        flash("Appointment not found.","warning")
        return redirect(url_for("admin.view_appointments"))
    appt.status = "Cancelled"
    slot = DoctorAvailability.query.filter_by(appointment_id=appt.id).first()
    if slot:
        slot.is_booked = False
        slot.appointment_id = None
    db.session.commit()
    flash("Appointment cancelled.","info")
    return redirect(url_for("admin.view_appointments"))

@admin_bp.route("/manage_patients")
@login_required
def manage_patients():
    if not admin_only():
        flash("Access denied: Admins only area.","danger")
        return redirect(url_for("auth.login"))
    patients = Patient.query.all()
    return render_template("admin_manage_patients.html", patients=patients)

@admin_bp.route("/toggle_user/<int:user_id>")
@login_required
def toggle_user(user_id):
    if not admin_only():
        flash("Access denied: Admins only area.","danger")
        return redirect(url_for("auth.login"))
    user = User.query.get(user_id)
    if not user:
        flash("User not found.","warning")
        return redirect(url_for("admin.manage_patients"))
    user.is_active = not bool(user.is_active)
    db.session.commit()
    flash(("Activated" if user.is_active else "Deactivated") + " user.","success")
    return redirect(url_for("admin.manage_patients"))

@admin_bp.route("/edit_patient/<int:patient_id>", methods=["GET","POST"])
@login_required
def edit_patient(patient_id):
    if not admin_only():
        flash("Access denied: Admins only area.","danger")
        return redirect(url_for("auth.login"))
    patient = Patient.query.get(patient_id)
    if request.method == "POST":
        patient.age = int(request.form.get("age") or patient.age or 0)
        patient.address = request.form.get("address")
        patient.blood_group = request.form.get("blood_group")
        patient.phone = request.form.get("phone")
        patient.height = request.form.get("height")
        patient.weight = request.form.get("weight")
        patient.special_notes = request.form.get("special_notes")
        db.session.commit()
        flash("Patient updated.","success")
        return redirect(url_for("admin.manage_patients"))
    return render_template("edit_patient.html", patient=patient)

@admin_bp.route("/delete_patient/<int:patient_id>")
@login_required
def delete_patient(patient_id):
    if not admin_only():
        flash("Access denied: Admins only area.","danger")
        return redirect(url_for("auth.login"))
    patient = Patient.query.get(patient_id)
    if not patient:
        flash("Patient not found.","warning")
        return redirect(url_for("admin.manage_patients"))
    user = User.query.get(patient.user_id)
    # delete related appointments and treatments
    from models import Treatment
    for appt in list(patient.appointments):
        for t in Treatment.query.filter_by(appointment_id=appt.id).all():
            db.session.delete(t)
        slot = DoctorAvailability.query.filter_by(appointment_id=appt.id).first()
        if slot:
            slot.is_booked = False
            slot.appointment_id = None
        db.session.delete(appt)
    db.session.delete(patient)
    if user:
        db.session.delete(user)
    db.session.commit()
    flash("Patient deleted.","info")
    return redirect(url_for("admin.manage_patients"))

@admin_bp.route("/search", methods=["GET","POST"])
@login_required
def search():
    if not admin_only():
        flash("Access denied: Admins only area.","danger")
        return redirect(url_for("auth.login"))
    results = {"doctors": [], "patients": []}
    q = ""
    target = "doctors"
    if request.method == "POST":
        q = request.form.get("q", "").strip()
        target = request.form.get("target", "doctors")
        if target == "doctors":
            results["doctors"] = db.session.query(Doctor).join(User, Doctor.user_id==User.id).join(Department, Doctor.department_id==Department.id).filter((User.name.ilike(f"%{q}%")) | (Department.name.ilike(f"%{q}%"))).all()
        else:
            results["patients"] = db.session.query(Patient).join(User, Patient.user_id==User.id).filter((User.name.ilike(f"%{q}%")) | (Patient.phone.ilike(f"%{q}%")) | (User.id.cast(db.String).ilike(f"%{q}%"))).all()
    return render_template("admin_search.html", results=results, q=q, target=target)