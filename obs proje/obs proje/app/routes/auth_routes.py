"""
Kimlik Doğrulama Route'ları
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.student import Student

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Giriş sayfası"""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
    
    if request.method == 'POST':
        student_number = request.form.get('student_number')
        password = request.form.get('password')
        
        user = Student.query.filter_by(student_number=student_number).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            
            if user.is_admin:
                return redirect(next_page or url_for('admin.dashboard'))
            return redirect(next_page or url_for('student.dashboard'))
        
        flash('Geçersiz öğrenci numarası veya şifre', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Çıkış"""
    logout_user()
    flash('Başarıyla çıkış yaptınız', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Kayıt sayfası (Demo amaçlı)"""
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))
    
    if request.method == 'POST':
        student_number = request.form.get('student_number')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        department = request.form.get('department', 'Bilgisayar Mühendisliği')
        faculty = request.form.get('faculty', 'Mühendislik Fakültesi')
        
        # Kontroller
        if Student.query.filter_by(student_number=student_number).first():
            flash('Bu öğrenci numarası zaten kayıtlı', 'error')
            return render_template('auth/register.html')
        
        if Student.query.filter_by(email=email).first():
            flash('Bu e-posta zaten kayıtlı', 'error')
            return render_template('auth/register.html')
        
        # Yeni öğrenci oluştur
        student = Student(
            student_number=student_number,
            email=email,
            first_name=first_name,
            last_name=last_name,
            department=department,
            faculty=faculty,
            class_level=1,
            gpa=0.0,
            remaining_courses=40
        )
        student.set_password(password)
        
        db.session.add(student)
        db.session.commit()
        
        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')
