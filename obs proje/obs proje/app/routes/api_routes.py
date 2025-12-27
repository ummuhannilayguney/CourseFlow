"""
API Route'ları (AJAX istekleri için)
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.catalog_service import CatalogService
from app.services.enrollment_service import EnrollmentService
from app.services.conflict_service import ConflictService
from app.services.prerequisite_service import PrerequisiteService
from app.services.priority_service import PriorityService
from app.services.simulation_service import SimulationService

api_bp = Blueprint('api', __name__)

# ==================== DERS API ====================

@api_bp.route('/courses', methods=['GET'])
def get_courses():
    """Ders listesi API"""
    keyword = request.args.get('keyword', '')
    department = request.args.get('department')
    course_type = request.args.get('course_type')
    
    courses = CatalogService.search_courses(keyword, department, course_type)
    return jsonify([c.to_dict() for c in courses])

@api_bp.route('/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """Ders detayı API"""
    course = CatalogService.get_course_by_id(course_id)
    if not course:
        return jsonify({'error': 'Ders bulunamadı'}), 404
    return jsonify(course.to_dict())

@api_bp.route('/courses/code/<code>', methods=['GET'])
def get_course_by_code(code):
    """Ders koduna göre API"""
    course = CatalogService.get_course_by_code(code)
    if not course:
        return jsonify({'error': 'Ders bulunamadı'}), 404
    return jsonify(course.to_dict())

# ==================== SEPET API ====================

@api_bp.route('/cart', methods=['GET'])
@login_required
def get_cart():
    """Sepet API"""
    cart = EnrollmentService.get_cart(current_user.id)
    return jsonify(cart)

@api_bp.route('/cart/add', methods=['POST'])
@login_required
def api_add_to_cart():
    """Sepete ekle API"""
    data = request.get_json()
    course_id = data.get('course_id')
    is_mandatory = data.get('is_mandatory', False)
    
    if not course_id:
        return jsonify({'success': False, 'message': 'Ders ID gerekli'}), 400
    
    result = EnrollmentService.add_to_cart(current_user.id, course_id, is_mandatory)
    return jsonify(result)

@api_bp.route('/cart/remove', methods=['POST'])
@login_required
def api_remove_from_cart():
    """Sepetten çıkar API"""
    data = request.get_json()
    course_id = data.get('course_id')
    
    if not course_id:
        return jsonify({'success': False, 'message': 'Ders ID gerekli'}), 400
    
    result = EnrollmentService.remove_from_cart(current_user.id, course_id)
    return jsonify(result)

@api_bp.route('/cart/reorder', methods=['POST'])
@login_required
def api_reorder_cart():
    """Sepet sıralaması API"""
    data = request.get_json()
    course_ids = data.get('course_ids', [])
    
    result = EnrollmentService.update_cart_order(current_user.id, course_ids)
    return jsonify(result)

@api_bp.route('/cart/validate', methods=['GET'])
@login_required
def api_validate_cart():
    """Sepet doğrulama API"""
    result = EnrollmentService.validate_cart(current_user.id)
    return jsonify(result)

# ==================== ÇAKIŞMA API ====================

@api_bp.route('/conflicts/check', methods=['POST'])
@login_required
def check_conflicts():
    """Çakışma kontrolü API"""
    data = request.get_json()
    course_id = data.get('course_id')
    
    if not course_id:
        return jsonify({'error': 'Ders ID gerekli'}), 400
    
    result = ConflictService.check_conflicts_for_student(current_user.id, course_id)
    
    # Çakışan dersleri serialize et
    conflicting = []
    for course in result['conflicting_courses']:
        conflicting.append(course.to_dict())
    
    return jsonify({
        'has_conflict': result['has_conflict'],
        'conflicting_courses': conflicting,
        'details': result['conflict_details']
    })

@api_bp.route('/conflicts/report', methods=['GET'])
@login_required
def get_conflict_report():
    """Çakışma raporu API"""
    report = ConflictService.get_conflict_report(current_user.id)
    return jsonify(report)

# ==================== ÖN ŞART API ====================

@api_bp.route('/prerequisites/<course_code>', methods=['GET'])
@login_required
def check_prerequisites(course_code):
    """Ön şart kontrolü API"""
    result = PrerequisiteService.check_prerequisites(current_user.id, course_code)
    return jsonify(result)

@api_bp.route('/prerequisites/chain/<course_code>', methods=['GET'])
def get_prerequisite_chain(course_code):
    """Ön şart zinciri API"""
    chain = PrerequisiteService.get_prerequisite_chain(course_code)
    return jsonify(chain)

@api_bp.route('/prerequisites/tree/<course_code>', methods=['GET'])
def get_prerequisite_tree(course_code):
    """Ön şart ağacı (text) API"""
    tree = PrerequisiteService.visualize_prerequisite_tree(course_code)
    return jsonify({'tree': tree})

# ==================== ÖNCELİK API ====================

@api_bp.route('/priority', methods=['GET'])
@login_required
def get_priority():
    """Öncelik bilgisi API"""
    breakdown = PriorityService.get_priority_breakdown(current_user)
    return jsonify(breakdown)

@api_bp.route('/priority/ranking', methods=['GET'])
@login_required
def get_priority_ranking():
    """Öncelik sıralaması API (Admin)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Yetki yok'}), 403
    
    students = PriorityService.get_students_by_priority()
    return jsonify([{
        'id': s.id,
        'student_number': s.student_number,
        'name': s.full_name,
        'priority_score': s.priority_score
    } for s in students[:50]])

# ==================== SİMÜLASYON API ====================

@api_bp.route('/simulation/latest', methods=['GET'])
@login_required
def get_latest_simulation():
    """Son simülasyon API"""
    if not current_user.is_admin:
        return jsonify({'error': 'Yetki yok'}), 403
    
    simulation = SimulationService.get_latest_simulation()
    if not simulation:
        return jsonify({'error': 'Simülasyon bulunamadı'}), 404
    
    return jsonify(simulation.to_dict())

@api_bp.route('/simulation/<int:simulation_id>/report', methods=['GET'])
@login_required
def get_simulation_report(simulation_id):
    """Simülasyon raporu API"""
    if not current_user.is_admin:
        return jsonify({'error': 'Yetki yok'}), 403
    
    report = SimulationService.generate_detailed_report(simulation_id)
    if not report:
        return jsonify({'error': 'Simülasyon bulunamadı'}), 404
    
    return jsonify(report)

# ==================== KAYIT API ====================

@api_bp.route('/enrollments', methods=['GET'])
@login_required
def get_enrollments():
    """Kayıtlar API"""
    semester = request.args.get('semester')
    enrollments = EnrollmentService.get_student_enrollments(current_user.id, semester)
    return jsonify(enrollments)

@api_bp.route('/enrollments/drop', methods=['POST'])
@login_required
def drop_enrollment():
    """Dersten çekilme API"""
    data = request.get_json()
    course_id = data.get('course_id')
    
    if not course_id:
        return jsonify({'success': False, 'message': 'Ders ID gerekli'}), 400
    
    result = EnrollmentService.drop_course(current_user.id, course_id)
    return jsonify(result)

@api_bp.route('/waitlist', methods=['GET'])
@login_required
def get_waitlist():
    """Bekleme listesi API"""
    waitlist = EnrollmentService.get_student_waitlist(current_user.id)
    return jsonify(waitlist)

# ==================== İSTATİSTİK API ====================

@api_bp.route('/stats/courses', methods=['GET'])
def get_course_stats():
    """Ders istatistikleri API"""
    courses = CatalogService.get_all_courses()
    
    stats = {
        'total': len(courses),
        'open': len([c for c in courses if c.is_open]),
        'full': len([c for c in courses if c.is_full]),
        'by_type': {}
    }
    
    for course in courses:
        ctype = course.course_type
        if ctype not in stats['by_type']:
            stats['by_type'][ctype] = 0
        stats['by_type'][ctype] += 1
    
    return jsonify(stats)
