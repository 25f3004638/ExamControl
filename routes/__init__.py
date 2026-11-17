from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.examiner_routes import examiner_bp
from routes.student_routes import student_bp

__all__ = ['auth_bp', 'admin_bp', 'examiner_bp', 'student_bp']
