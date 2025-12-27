"""
Flask Uygulama Fabrikası
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app(config_name='default'):
    """Uygulama fabrikası"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Blueprints
    from app.routes.main_routes import main_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.student_routes import student_bp
    from app.routes.api_routes import api_bp
    from app.routes.auth_routes import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    return app
