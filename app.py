from flask import Flask
from flask_login import LoginManager
from models import db, init_db
from auth import auth_bp

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///hms.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Attach sqlalchemy to app
    db.init_app(app)
    
    # Attach login manager to app    
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    
    # Import user_loader function
    from auth import load_user
    login_manager.user_loader(load_user)
    
    # Register blueprint
    app.register_blueprint(auth_bp)

    # Try to import patient routes with error handling
    try:
        from patient_routes import patient_bp
        app.register_blueprint(patient_bp)

    except Exception as e:
        print(f"Error importing patient_routes: {e}")
        import traceback
        traceback.print_exc()
    # Register doctor routes blueprint
    try:
        from doctor_routes import doctor_bp
        app.register_blueprint(doctor_bp)

    except Exception as e:
        print(f"Error importing doctor_routes: {e}")
        import traceback
        traceback.print_exc()

    # Register admin routes blueprint
    try:
        from admin_routes import admin_bp
        app.register_blueprint(admin_bp)

    except Exception as e:
        print(f"Error importing admin_routes: {e}")
        import traceback
        traceback.print_exc()

    # Initialize database
    with app.app_context():
        init_db()
    
    return app

app = create_app()

if __name__ == "__main__":

    app.run(debug=True, host='0.0.0.0', port=5000)