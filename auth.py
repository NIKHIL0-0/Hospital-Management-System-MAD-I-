# This file handles /login, /register, /logout routes

from flask import Blueprint, render_template, redirect, request, flash, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, User

auth_bp = Blueprint('auth', __name__)



def load_user(user_id):
    # user_id comes as a string, so we convert to int
    return User.query.get(int(user_id))

@auth_bp.route("/")
def home():
    # we send to login page now then redirect based on role 
    if current_user.is_authenticated:
        return f"Hello, {current_user.name}! You are logged in as {current_user.role}."
    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            if not user.is_active:
                flash("Your account is deactivated. Please contact admin.", "danger")
                return redirect(url_for("auth.login"))

            # Log the user in 
            login_user(user)
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            elif user.role == "doctor":
                return redirect(url_for("doctor.dashboard"))
            elif user.role == "patient":
                return redirect(url_for("patient.dashboard"))
            flash("Logged in successfully!", "success")
        else:
            flash("Invalid email or password.", "danger")
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    #new registration
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        raw_password = request.form.get("password")

        # Simple validations 
        if not name or not email or not raw_password:
            flash("All fields are required.", "warning")
            return redirect(url_for("auth.register"))

        # Check if email already used
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("auth.login"))

        hashed_password = generate_password_hash(raw_password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            role="patient"  # default
        )
        db.session.add(new_user)
        db.session.flush()  # Get the user ID before commit
        
        # Create Patient record for new patient user
        from models import Patient
        new_patient = Patient(
            user_id=new_user.id,
            age=25,  # Default age, can be updated later
            address="Not provided",
            blood_group="Unknown"
        )
        db.session.add(new_patient)
        db.session.commit()
        
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


    

