"""
Route Modülleri
"""
from app.routes.main_routes import main_bp
from app.routes.admin_routes import admin_bp
from app.routes.student_routes import student_bp
from app.routes.api_routes import api_bp
from app.routes.auth_routes import auth_bp

__all__ = ['main_bp', 'admin_bp', 'student_bp', 'api_bp', 'auth_bp']
