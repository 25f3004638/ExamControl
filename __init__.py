import os
from flask import Flask, redirect, url_for, request, session, flash
from .models import db, User, Admin

DEFAULT_ADMIN_EMAIL = os.environ.get("EMP_ADMIN_EMAIL", "admin@emp.local")
DEFAULT_ADMIN_PASSWORD = os.environ.get("EMP_ADMIN_PASSWORD", "admin123")
DEFAULT_ADMIN_NAME = os.environ.get("EMP_ADMIN_NAME", "Super Admin")


def create_app():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    instance_dir = os.path.join(base_dir, "instance")
    os.makedirs(instance_dir, exist_ok=True)
    db_path = os.path.join(instance_dir, "examcontrol.sqlite")

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    db.init_app(app)

    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    """Ensure a pre-existing superuser admin exists (no admin registration)."""
    if User.query.filter_by(email=DEFAULT_ADMIN_EMAIL).first():
        return

    user = User(email=DEFAULT_ADMIN_EMAIL, role="admin", is_active=True)
    user.set_password(DEFAULT_ADMIN_PASSWORD)
    db.session.add(user)
    db.session.flush()
    db.session.add(Admin(user_id=user.id, name=DEFAULT_ADMIN_NAME))
    db.session.commit()


def main():
    app = create_app()
    app.run(debug=True, port=5000)


# expose for `flask --app examcontrol run`
app = create_app()