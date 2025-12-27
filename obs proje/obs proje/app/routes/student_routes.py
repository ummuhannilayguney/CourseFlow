"""
Öğrenci Route'ları
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.course import Course
from app.models.enrollment import CourseRequest, Enrollment
from app.services.catalog_service import CatalogService
from app.services.enrollment_service import EnrollmentService
from app.services.conflict_service import ConflictService
from app.services.prerequisite_service import PrerequisiteService
from app.services.priority_service import PriorityService

student_bp = Blueprint('student', __name__)

def student_required(f):
    """Öğrenci yetkisi kontrolü decorator'ı"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.is_admin:
            flash('Bu sayfa sadece öğrenciler içindir', 'warning')
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    """Öğrenci ana sayfası"""
    # Öncelik puanını güncelle
    current_user.calculate_priority_score()
    db.session.commit()
    
    # Sepetteki dersler
    cart = EnrollmentService.get_cart(current_user.id)
    
    # Kayıtlı dersler
    enrollments = EnrollmentService.get_student_enrollments(current_user.id)
    
    # Bekleme listeleri
    waitlist = EnrollmentService.get_student_waitlist(current_user.id)
    
    # Öncelik detayı
    priority_breakdown = PriorityService.get_priority_breakdown(current_user)
    
    return render_template('student/dashboard.html',
                          cart=cart,
                          enrollments=enrollments,
                          waitlist=waitlist,
                          priority=priority_breakdown)

@student_bp.route('/courses')
@login_required
@student_required
def course_catalog():
    """Ders kataloğu"""
    keyword = request.args.get('keyword', '')
    department = request.args.get('department', '')
    course_type = request.args.get('course_type', '')
    
    if keyword or department or course_type:
        courses = CatalogService.search_courses(keyword, department or None, course_type or None)
    else:
        courses = CatalogService.get_open_courses()
    
    departments = CatalogService.get_departments()
    
    return render_template('student/courses.html',
                          courses=courses,
                          departments=departments,
                          filters={'keyword': keyword, 'department': department, 'course_type': course_type})

@student_bp.route('/course/<int:course_id>')
@login_required
@student_required
def course_detail(course_id):
    """Ders detayı"""
    course = CatalogService.get_course_by_id(course_id)
    if not course:
        flash('Ders bulunamadı', 'error')
        return redirect(url_for('student.course_catalog'))
    
    # Ön şart kontrolü
    prereq_result = PrerequisiteService.check_prerequisites(current_user.id, course.code)
    
    # Çakışma kontrolü
    conflict_result = ConflictService.check_conflicts_for_student(current_user.id, course.id)
    
    # Sepette mi?
    in_cart = CourseRequest.query.filter_by(
        student_id=current_user.id,
        course_id=course_id,
        status='pending'
    ).first() is not None
    
    # Kayıtlı mı?
    enrolled = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=course_id,
        status='approved'
    ).first() is not None
    
    return render_template('student/course_detail.html',
                          course=course,
                          prereq_result=prereq_result,
                          conflict_result=conflict_result,
                          in_cart=in_cart,
                          enrolled=enrolled)

@student_bp.route('/cart')
@login_required
@student_required
def cart():
    """Sepet sayfası"""
    cart_items = EnrollmentService.get_cart(current_user.id)
    
    # Sepet doğrulama
    validation = EnrollmentService.validate_cart(current_user.id)
    
    # Çakışma raporu
    conflict_report = ConflictService.get_conflict_report(current_user.id)
    
    return render_template('student/cart.html',
                          cart=cart_items,
                          validation=validation,
                          conflicts=conflict_report)

@student_bp.route('/cart/add/<int:course_id>', methods=['POST'])
@login_required
@student_required
def add_to_cart(course_id):
    """Sepete ders ekle"""
    is_mandatory = request.form.get('is_mandatory', 'false') == 'true'
    result = EnrollmentService.add_to_cart(current_user.id, course_id, is_mandatory)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'error')
    
    return redirect(request.referrer or url_for('student.course_catalog'))

@student_bp.route('/cart/remove/<int:course_id>', methods=['POST'])
@login_required
@student_required
def remove_from_cart(course_id):
    """Sepetten ders çıkar"""
    result = EnrollmentService.remove_from_cart(current_user.id, course_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'error')
    
    return redirect(url_for('student.cart'))

@student_bp.route('/cart/toggle-mandatory/<int:course_id>', methods=['POST'])
@login_required
@student_required
def toggle_mandatory(course_id):
    """Zorunlu işaretini değiştir"""
    req = CourseRequest.query.filter_by(
        student_id=current_user.id,
        course_id=course_id,
        status='pending'
    ).first()
    
    if req:
        result = EnrollmentService.set_mandatory(current_user.id, course_id, not req.is_mandatory)
        flash(result['message'], 'success')
    
    return redirect(url_for('student.cart'))

@student_bp.route('/cart/clear', methods=['POST'])
@login_required
@student_required
def clear_cart():
    """Sepeti temizle"""
    result = EnrollmentService.clear_cart(current_user.id)
    flash(result['message'], 'success')
    return redirect(url_for('student.cart'))

@student_bp.route('/schedule')
@login_required
@student_required
def schedule():
    """Ders programı"""
    enrollments = Enrollment.query.filter_by(
        student_id=current_user.id,
        status='approved'
    ).all()
    
    # Haftalık program oluştur
    weekly_schedule = {
        'Pazartesi': [], 'Salı': [], 'Çarşamba': [],
        'Perşembe': [], 'Cuma': [], 'Cumartesi': []
    }
    
    for enrollment in enrollments:
        course = enrollment.course
        for sched in course.schedules:
            if sched.day in weekly_schedule:
                weekly_schedule[sched.day].append({
                    'course': course,
                    'schedule': sched
                })
    
    # Her günü saate göre sırala
    for day in weekly_schedule:
        weekly_schedule[day].sort(key=lambda x: x['schedule'].start_time)
    
    return render_template('student/schedule.html',
                          weekly_schedule=weekly_schedule,
                          enrollments=enrollments)

@student_bp.route('/transcript')
@login_required
@student_required
def transcript():
    """Transkript"""
    from app.models.student import CompletedCourse
    
    completed = CompletedCourse.query.filter_by(
        student_id=current_user.id
    ).order_by(CompletedCourse.semester.desc()).all()
    
    return render_template('student/transcript.html', completed=completed)

@student_bp.route('/priority')
@login_required
@student_required
def priority_info():
    """Öncelik bilgisi"""
    breakdown = PriorityService.get_priority_breakdown(current_user)
    return render_template('student/priority.html', priority=breakdown)
