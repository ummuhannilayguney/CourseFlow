"""
Ders Kayıt Servisi
Sepet yönetimi, kayıt işlemleri ve bekleme listesi
"""
from app import db
from app.models.student import Student
from app.models.course import Course
from app.models.enrollment import Enrollment, CourseRequest, WaitList
from app.services.conflict_service import ConflictService
from app.services.prerequisite_service import PrerequisiteService
from config import Config
from datetime import datetime

class EnrollmentService:
    """Ders kayıt yönetim servisi"""
    
    # ==================== SEPET YÖNETİMİ ====================
    
    @staticmethod
    def add_to_cart(student_id, course_id, is_mandatory=False):
        """
        Sepete ders ekle
        
        Returns:
            dict: {success, message, request}
        """
        student = Student.query.get(student_id)
        course = Course.query.get(course_id)
        
        if not student:
            return {'success': False, 'message': 'Öğrenci bulunamadı'}
        if not course:
            return {'success': False, 'message': 'Ders bulunamadı'}
        if not course.is_active:
            return {'success': False, 'message': 'Ders aktif değil'}
        if not course.is_open:
            return {'success': False, 'message': 'Ders kayıta kapalı'}
        
        # Zaten sepette mi kontrol
        existing = CourseRequest.query.filter_by(
            student_id=student_id,
            course_id=course_id
        ).first()
        
        if existing:
            return {'success': False, 'message': 'Ders zaten sepetinizde'}
        
        # Zaten kayıtlı mı kontrol
        enrolled = Enrollment.query.filter_by(
            student_id=student_id,
            course_id=course_id,
            status='approved'
        ).first()
        
        if enrolled:
            return {'success': False, 'message': 'Bu derse zaten kayıtlısınız'}
        
        # Maksimum ders sayısı kontrolü
        current_requests = CourseRequest.query.filter_by(
            student_id=student_id,
            status='pending'
        ).count()
        
        if current_requests >= Config.MAX_COURSES_PER_STUDENT:
            return {'success': False, 'message': f'Maksimum {Config.MAX_COURSES_PER_STUDENT} ders seçebilirsiniz'}
        
        # Öncelik sırası belirle (en sona ekle)
        max_priority = db.session.query(db.func.max(CourseRequest.priority_order)).filter_by(
            student_id=student_id,
            status='pending'
        ).scalar() or 0
        
        request = CourseRequest(
            student_id=student_id,
            course_id=course_id,
            priority_order=max_priority + 1,
            is_mandatory=is_mandatory
        )
        
        db.session.add(request)
        db.session.commit()
        
        return {
            'success': True,
            'message': f"'{course.code}' sepete eklendi",
            'request': request.to_dict()
        }
    
    @staticmethod
    def remove_from_cart(student_id, course_id):
        """Sepetten ders çıkar"""
        request = CourseRequest.query.filter_by(
            student_id=student_id,
            course_id=course_id,
            status='pending'
        ).first()
        
        if not request:
            return {'success': False, 'message': 'Ders sepetinizde bulunamadı'}
        
        course_code = request.course.code
        db.session.delete(request)
        db.session.commit()
        
        # Öncelik sıralarını yeniden düzenle
        EnrollmentService._reorder_cart(student_id)
        
        return {'success': True, 'message': f"'{course_code}' sepetten çıkarıldı"}
    
    @staticmethod
    def update_cart_order(student_id, course_ids):
        """
        Sepet sırasını güncelle
        
        Args:
            course_ids: Yeni sıralama (course_id listesi)
        """
        for index, course_id in enumerate(course_ids):
            request = CourseRequest.query.filter_by(
                student_id=student_id,
                course_id=course_id,
                status='pending'
            ).first()
            
            if request:
                request.priority_order = index + 1
        
        db.session.commit()
        return {'success': True, 'message': 'Sıralama güncellendi'}
    
    @staticmethod
    def set_mandatory(student_id, course_id, is_mandatory):
        """Dersi zorunlu olarak işaretle/kaldır"""
        request = CourseRequest.query.filter_by(
            student_id=student_id,
            course_id=course_id,
            status='pending'
        ).first()
        
        if not request:
            return {'success': False, 'message': 'Ders sepetinizde bulunamadı'}
        
        request.is_mandatory = is_mandatory
        db.session.commit()
        
        status = "zorunlu olarak işaretlendi" if is_mandatory else "zorunlu işareti kaldırıldı"
        return {'success': True, 'message': f"'{request.course.code}' {status}"}
    
    @staticmethod
    def get_cart(student_id):
        """Öğrencinin sepetini getir"""
        requests = CourseRequest.query.filter_by(
            student_id=student_id,
            status='pending'
        ).order_by(CourseRequest.priority_order).all()
        
        return [req.to_dict() for req in requests]
    
    @staticmethod
    def clear_cart(student_id):
        """Sepeti temizle"""
        CourseRequest.query.filter_by(
            student_id=student_id,
            status='pending'
        ).delete()
        
        db.session.commit()
        return {'success': True, 'message': 'Sepet temizlendi'}
    
    @staticmethod
    def _reorder_cart(student_id):
        """Sepet sıralamasını düzenle"""
        requests = CourseRequest.query.filter_by(
            student_id=student_id,
            status='pending'
        ).order_by(CourseRequest.priority_order).all()
        
        for index, request in enumerate(requests):
            request.priority_order = index + 1
        
        db.session.commit()
    
    # ==================== KAYIT İŞLEMLERİ ====================
    
    @staticmethod
    def process_student_requests(student_id, semester):
        """
        Öğrencinin ders taleplerini işle
        
        Returns:
            dict: {
                'approved': list,
                'rejected': list,
                'waitlisted': list
            }
        """
        student = Student.query.get(student_id)
        if not student:
            return {'error': 'Öğrenci bulunamadı'}
        
        requests = CourseRequest.query.filter_by(
            student_id=student_id,
            status='pending'
        ).order_by(CourseRequest.priority_order).all()
        
        approved = []
        rejected = []
        waitlisted = []
        approved_course_ids = []
        
        for request in requests:
            course = request.course
            result = EnrollmentService._evaluate_request(
                student, course, approved_course_ids
            )
            
            if result['can_enroll']:
                # Kayıt oluştur
                enrollment = Enrollment(
                    student_id=student_id,
                    course_id=course.id,
                    semester=semester,
                    status='approved'
                )
                db.session.add(enrollment)
                
                # Kontenjan güncelle
                course.enrolled_count += 1
                if course.enrolled_count >= course.quota:
                    course.is_open = False
                
                # Talep durumunu güncelle
                request.status = 'approved'
                request.processed_at = datetime.utcnow()
                
                approved.append({
                    'course': course.to_dict(),
                    'message': 'Kayıt başarılı'
                })
                approved_course_ids.append(course.id)
                
            elif result['reason'] == 'quota_full' and Config.WAITLIST_ENABLED:
                # Bekleme listesine ekle
                waitlist_result = EnrollmentService._add_to_waitlist(student_id, course.id)
                if waitlist_result['success']:
                    request.status = 'rejected'
                    request.rejection_reason = 'Kontenjan doldu - Bekleme listesine alındı'
                    request.processed_at = datetime.utcnow()
                    
                    waitlisted.append({
                        'course': course.to_dict(),
                        'position': waitlist_result['position']
                    })
                else:
                    request.status = 'rejected'
                    request.rejection_reason = result['message']
                    request.processed_at = datetime.utcnow()
                    rejected.append({
                        'course': course.to_dict(),
                        'reason': result['message']
                    })
            else:
                request.status = 'rejected'
                request.rejection_reason = result['message']
                request.processed_at = datetime.utcnow()
                
                rejected.append({
                    'course': course.to_dict(),
                    'reason': result['message']
                })
        
        db.session.commit()
        
        return {
            'approved': approved,
            'rejected': rejected,
            'waitlisted': waitlisted
        }
    
    @staticmethod
    def _evaluate_request(student, course, approved_course_ids):
        """
        Tek bir ders talebini değerlendir
        
        Kontroller:
        1. Kontenjan
        2. Ön şart
        3. Çakışma
        """
        # 1. Kontenjan kontrolü
        if course.is_full:
            return {
                'can_enroll': False,
                'reason': 'quota_full',
                'message': f"'{course.code}' kontenjanı dolu"
            }
        
        # 2. Ön şart kontrolü
        prereq_result = PrerequisiteService.check_prerequisites(student.id, course.code)
        if not prereq_result['can_enroll']:
            missing = [m['code'] for m in prereq_result['missing_prerequisites']]
            return {
                'can_enroll': False,
                'reason': 'prerequisite',
                'message': f"Ön şart eksik: {', '.join(missing)}"
            }
        
        # 3. Çakışma kontrolü (mevcut onaylı dersler + bu turda onaylananlar)
        # Mevcut kayıtlar
        conflict_result = ConflictService.check_conflicts_for_student(student.id, course.id)
        if conflict_result['has_conflict']:
            conflicting = conflict_result['conflicting_courses'][0]
            return {
                'can_enroll': False,
                'reason': 'conflict',
                'message': f"'{conflicting.code}' ile saat çakışması"
            }
        
        # Bu turda onaylanan derslerle çakışma
        for approved_id in approved_course_ids:
            result = ConflictService.check_conflict_between_courses(approved_id, course.id)
            if result['has_conflict']:
                approved_course = Course.query.get(approved_id)
                return {
                    'can_enroll': False,
                    'reason': 'conflict',
                    'message': f"'{approved_course.code}' ile saat çakışması"
                }
        
        return {'can_enroll': True}
    
    # ==================== BEKLEME LİSTESİ ====================
    
    @staticmethod
    def _add_to_waitlist(student_id, course_id):
        """Bekleme listesine ekle"""
        # Mevcut kontrol
        existing = WaitList.query.filter_by(
            student_id=student_id,
            course_id=course_id
        ).first()
        
        if existing:
            return {'success': False, 'message': 'Zaten bekleme listesinde'}
        
        # Mevcut pozisyon sayısı
        current_count = WaitList.query.filter_by(
            course_id=course_id,
            status='waiting'
        ).count()
        
        if current_count >= Config.WAITLIST_MAX_SIZE:
            return {'success': False, 'message': 'Bekleme listesi dolu'}
        
        waitlist = WaitList(
            student_id=student_id,
            course_id=course_id,
            position=current_count + 1
        )
        
        db.session.add(waitlist)
        db.session.commit()
        
        return {'success': True, 'position': current_count + 1}
    
    @staticmethod
    def get_waitlist(course_id):
        """Dersin bekleme listesini getir"""
        entries = WaitList.query.filter_by(
            course_id=course_id,
            status='waiting'
        ).order_by(WaitList.position).all()
        
        return [entry.to_dict() for entry in entries]
    
    @staticmethod
    def get_student_waitlist(student_id):
        """Öğrencinin bekleme listelerini getir"""
        entries = WaitList.query.filter_by(
            student_id=student_id,
            status='waiting'
        ).all()
        
        return [entry.to_dict() for entry in entries]
    
    # ==================== KAYIT SORGULARI ====================
    
    @staticmethod
    def get_student_enrollments(student_id, semester=None):
        """Öğrencinin kayıtlarını getir"""
        query = Enrollment.query.filter_by(
            student_id=student_id,
            status='approved'
        )
        
        if semester:
            query = query.filter_by(semester=semester)
        
        return [e.to_dict() for e in query.all()]
    
    @staticmethod
    def get_course_enrollments(course_id):
        """Derse kayıtlı öğrencileri getir"""
        enrollments = Enrollment.query.filter_by(
            course_id=course_id,
            status='approved'
        ).all()
        
        return enrollments
    
    @staticmethod
    def drop_course(student_id, course_id):
        """Dersten çekil"""
        enrollment = Enrollment.query.filter_by(
            student_id=student_id,
            course_id=course_id,
            status='approved'
        ).first()
        
        if not enrollment:
            return {'success': False, 'message': 'Kayıt bulunamadı'}
        
        course = Course.query.get(course_id)
        
        # Kaydı güncelle
        enrollment.status = 'dropped'
        enrollment.dropped_at = datetime.utcnow()
        
        # Kontenjanı güncelle
        if course:
            course.enrolled_count = max(0, course.enrolled_count - 1)
            course.is_open = True
        
        db.session.commit()
        
        return {'success': True, 'message': f"'{course.code}' dersinden çekildiniz"}
    
    @staticmethod
    def validate_cart(student_id):
        """
        Sepet doğrulama - kayıt öncesi kontrol
        
        Returns:
            dict: {
                'valid': bool,
                'issues': list,
                'warnings': list
            }
        """
        requests = CourseRequest.query.filter_by(
            student_id=student_id,
            status='pending'
        ).order_by(CourseRequest.priority_order).all()
        
        issues = []
        warnings = []
        
        if len(requests) < Config.MIN_COURSES_PER_STUDENT:
            issues.append(f'Minimum {Config.MIN_COURSES_PER_STUDENT} ders seçmelisiniz')
        
        # Her ders için kontrol
        for request in requests:
            course = request.course
            
            # Kontenjan uyarısı
            if course.fill_percentage > 80:
                warnings.append(f"'{course.code}' kontenjanı %{course.fill_percentage} dolu")
            
            # Ön şart kontrolü
            prereq_result = PrerequisiteService.check_prerequisites(
                student_id, course.code
            )
            if not prereq_result['can_enroll']:
                issues.append(f"'{course.code}' için ön şart eksik")
        
        # Çakışma kontrolü
        conflict_result = ConflictService.check_conflicts_in_request_list(student_id)
        if conflict_result['has_conflicts']:
            for pair in conflict_result['conflict_pairs']:
                warnings.append(
                    f"'{pair['course1'].code}' ve '{pair['course2'].code}' çakışıyor"
                )
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
