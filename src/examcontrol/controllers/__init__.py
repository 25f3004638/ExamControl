from .auth import auth_bp
from .admin import admin_bp
from .examiner import examiner_bp
from .student import student_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(examiner_bp, url_prefix="/examiner")
    app.register_blueprint(student_bp, url_prefix="/student")