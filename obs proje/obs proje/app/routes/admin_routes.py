"""
Admin Route'ları
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.student import Student
from app.models.course import Course
from app.models.enrollment import CourseRequest, Enrollment
from app.models.simulation import SimulationMetrics
from app.services.catalog_service import CatalogService
from app.services.simulation_service import SimulationService
from app.services.priority_service import PriorityService

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Admin yetkisi kontrolü decorator'ı"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Bu sayfaya erişim yetkiniz yok', 'error')
            return redirect(url_for('student.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin ana sayfası"""
    # İstatistikler
    total_students = Student.query.filter_by(is_admin=False).count()
    total_courses = Course.query.filter_by(is_active=True).count()
    total_requests = CourseRequest.query.filter_by(status='pending').count()
    total_enrollments = Enrollment.query.filter_by(status='approved').count()
    
    # Son simülasyon
    latest_simulation = SimulationService.get_latest_simulation()
    
    # Kontenjanı dolan dersler
    full_courses = CatalogService.get_full_courses()
    
    return render_template('admin/dashboard.html',
                          stats={
                              'students': total_students,
                              'courses': total_courses,
                              'pending_requests': total_requests,
                              'enrollments': total_enrollments
                          },
                          latest_simulation=latest_simulation,
                          full_courses=full_courses)

# ==================== DERS YÖNETİMİ ====================

@admin_bp.route('/courses')
@login_required
@admin_required
def courses():
    """Ders listesi"""
    keyword = request.args.get('keyword', '')
    courses = CatalogService.search_courses(keyword) if keyword else CatalogService.get_all_courses()
    return render_template('admin/courses.html', courses=courses)

@admin_bp.route('/courses/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_course():
    """Ders ekle"""
    if request.method == 'POST':
        data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'description': request.form.get('description', ''),
            'credit': int(request.form.get('credit', 3)),
            'ects': int(request.form.get('ects', 5)),
            'department': request.form.get('department'),
            'faculty': request.form.get('faculty'),
            'quota': int(request.form.get('quota', 50)),
            'course_type': request.form.get('course_type', 'elective'),
            'schedules': [],
            'prerequisites': []
        }
        
        # Ders programı
        days = request.form.getlist('day[]')
        start_times = request.form.getlist('start_time[]')
        end_times = request.form.getlist('end_time[]')
        classrooms = request.form.getlist('classroom[]')
        
        for i in range(len(days)):
            if days[i] and start_times[i] and end_times[i]:
                data['schedules'].append({
                    'day': days[i],
                    'start_time': start_times[i],
                    'end_time': end_times[i],
                    'classroom': classrooms[i] if i < len(classrooms) else ''
                })
        
        # Ön şartlar
        prereqs = request.form.get('prerequisites', '')
        if prereqs:
            data['prerequisites'] = [p.strip() for p in prereqs.split(',') if p.strip()]
        
        try:
            course = CatalogService.create_course(data)
            flash(f"'{course.code}' dersi eklendi", 'success')
            return redirect(url_for('admin.courses'))
        except Exception as e:
            flash(f'Hata: {str(e)}', 'error')
    
    departments = CatalogService.get_departments() or ['Bilgisayar Mühendisliği']
    faculties = CatalogService.get_faculties() or ['Mühendislik Fakültesi']
    
    return render_template('admin/course_form.html',
                          course=None,
                          departments=departments,
                          faculties=faculties)

@admin_bp.route('/courses/edit/<int:course_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    """Ders düzenle"""
    course = CatalogService.get_course_by_id(course_id)
    if not course:
        flash('Ders bulunamadı', 'error')
        return redirect(url_for('admin.courses'))
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'description': request.form.get('description', ''),
            'credit': int(request.form.get('credit', 3)),
            'quota': int(request.form.get('quota', 50)),
            'course_type': request.form.get('course_type', 'elective'),
            'is_open': request.form.get('is_open') == 'on',
            'schedules': [],
            'prerequisites': []
        }
        
        # Ders programı
        days = request.form.getlist('day[]')
        start_times = request.form.getlist('start_time[]')
        end_times = request.form.getlist('end_time[]')
        classrooms = request.form.getlist('classroom[]')
        
        for i in range(len(days)):
            if days[i] and start_times[i] and end_times[i]:
                data['schedules'].append({
                    'day': days[i],
                    'start_time': start_times[i],
                    'end_time': end_times[i],
                    'classroom': classrooms[i] if i < len(classrooms) else ''
                })
        
        # Ön şartlar
        prereqs = request.form.get('prerequisites', '')
        if prereqs:
            data['prerequisites'] = [p.strip() for p in prereqs.split(',') if p.strip()]
        
        CatalogService.update_course(course_id, data)
        flash(f"'{course.code}' güncellendi", 'success')
        return redirect(url_for('admin.courses'))
    
    departments = CatalogService.get_departments()
    faculties = CatalogService.get_faculties()
    
    return render_template('admin/course_form.html',
                          course=course,
                          departments=departments,
                          faculties=faculties)

@admin_bp.route('/courses/delete/<int:course_id>', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    """Ders sil"""
    course = CatalogService.get_course_by_id(course_id)
    if course:
        CatalogService.delete_course(course_id)
        flash(f"'{course.code}' silindi", 'success')
    return redirect(url_for('admin.courses'))

# ==================== ÖĞRENCİ YÖNETİMİ ====================

@admin_bp.route('/students')
@login_required
@admin_required
def students():
    """Öğrenci listesi"""
    students = Student.query.filter_by(is_admin=False).order_by(Student.student_number).all()
    return render_template('admin/students.html', students=students)

@admin_bp.route('/students/<int:student_id>')
@login_required
@admin_required
def student_detail(student_id):
    """Öğrenci detayı"""
    student = Student.query.get_or_404(student_id)
    
    # Öncelik detayı
    priority = PriorityService.get_priority_breakdown(student)
    
    # Sepet
    from app.services.enrollment_service import EnrollmentService
    cart = EnrollmentService.get_cart(student_id)
    
    # Kayıtlar
    enrollments = EnrollmentService.get_student_enrollments(student_id)
    
    return render_template('admin/student_detail.html',
                          student=student,
                          priority=priority,
                          cart=cart,
                          enrollments=enrollments)

@admin_bp.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_student(student_id):
    """Öğrenci düzenle"""
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        student.first_name = request.form.get('first_name')
        student.last_name = request.form.get('last_name')
        student.class_level = int(request.form.get('class_level', 1))
        student.gpa = float(request.form.get('gpa', 0))
        student.remaining_courses = int(request.form.get('remaining_courses', 40))
        student.special_status = request.form.get('special_status', 'none')
        
        # Öncelik puanını yeniden hesapla
        student.calculate_priority_score()
        
        db.session.commit()
        flash('Öğrenci bilgileri güncellendi', 'success')
        return redirect(url_for('admin.student_detail', student_id=student_id))
    
    return render_template('admin/student_form.html', student=student)

# ==================== SİMÜLASYON ====================

@admin_bp.route('/simulation')
@login_required
@admin_required
def simulation():
    """Simülasyon sayfası"""
    simulations = SimulationService.get_all_simulations()
    return render_template('admin/simulation.html', simulations=simulations)

@admin_bp.route('/simulation/run', methods=['POST'])
@login_required
@admin_required
def run_simulation():
    """Simülasyon çalıştır"""
    semester = request.form.get('semester', '2024-Güz')
    
    try:
        metrics = SimulationService.run_simulation(semester)
        flash(f'Simülasyon tamamlandı! {metrics.total_approved} kayıt onaylandı.', 'success')
        return redirect(url_for('admin.simulation_result', simulation_id=metrics.id))
    except Exception as e:
        flash(f'Simülasyon hatası: {str(e)}', 'error')
        return redirect(url_for('admin.simulation'))

@admin_bp.route('/simulation/reset', methods=['POST'])
@login_required
@admin_required
def reset_simulation():
    """Simülasyonu sıfırla"""
    semester = request.form.get('semester', '2024-Güz')
    result = SimulationService.reset_simulation(semester)
    flash(result['message'], 'success')
    return redirect(url_for('admin.simulation'))

@admin_bp.route('/simulation/<int:simulation_id>')
@login_required
@admin_required
def simulation_result(simulation_id):
    """Simülasyon sonucu"""
    report = SimulationService.generate_detailed_report(simulation_id)
    if not report:
        flash('Simülasyon bulunamadı', 'error')
        return redirect(url_for('admin.simulation'))
    
    return render_template('admin/simulation_result.html', report=report)

@admin_bp.route('/simulation/preview', methods=['POST'])
@login_required
@admin_required
def preview_simulation():
    """Simülasyon önizleme"""
    semester = request.form.get('semester', '2024-Güz')
    preview = SimulationService.preview_simulation(semester)
    return render_template('admin/simulation_preview.html', preview=preview)

# ==================== RAPORLAR ====================

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Raporlar sayfası"""
    # Ders doluluk oranları
    courses = Course.query.filter_by(is_active=True).all()
    course_stats = []
    
    for course in courses:
        course_stats.append({
            'course': course,
            'fill_rate': course.fill_percentage
        })
    
    # En dolu dersler
    most_filled = sorted(course_stats, key=lambda x: x['fill_rate'], reverse=True)[:10]
    
    # Öncelik dağılımı
    students = Student.query.filter_by(is_admin=False).all()
    priority_distribution = {
        'high': len([s for s in students if s.priority_score >= 70]),
        'medium': len([s for s in students if 40 <= s.priority_score < 70]),
        'low': len([s for s in students if s.priority_score < 40])
    }
    
    return render_template('admin/reports.html',
                          most_filled=most_filled,
                          priority_distribution=priority_distribution)
