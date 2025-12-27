"""
Ders Çakışması Kontrolü ve Çözümleme Servisi
"""
from app import db
from app.models.course import Course, CourseSchedule
from app.models.enrollment import Enrollment, CourseRequest

class ConflictService:
    """Ders çakışması kontrolü ve çözümleme servisi"""
    
    @staticmethod
    def check_conflict_between_courses(course1_id, course2_id):
        """
        İki ders arasında çakışma kontrolü
        
        Returns:
            dict: {
                'has_conflict': bool,
                'conflicts': list of conflict details
            }
        """
        course1 = Course.query.get(course1_id)
        course2 = Course.query.get(course2_id)
        
        if not course1 or not course2:
            return {'has_conflict': False, 'conflicts': [], 'error': 'Ders bulunamadı'}
        
        schedules1 = course1.schedules.all()
        schedules2 = course2.schedules.all()
        
        conflicts = []
        
        for sched1 in schedules1:
            for sched2 in schedules2:
                if sched1.conflicts_with(sched2):
                    conflicts.append({
                        'course1': {
                            'code': course1.code,
                            'name': course1.name,
                            'schedule': sched1.display_text
                        },
                        'course2': {
                            'code': course2.code,
                            'name': course2.name,
                            'schedule': sched2.display_text
                        },
                        'day': sched1.day,
                        'time_overlap': f"{max(sched1.start_time, sched2.start_time)} - {min(sched1.end_time, sched2.end_time)}"
                    })
        
        return {
            'has_conflict': len(conflicts) > 0,
            'conflicts': conflicts
        }
    
    @staticmethod
    def check_conflicts_for_student(student_id, new_course_id):
        """
        Öğrencinin mevcut programıyla yeni dersin çakışma kontrolü
        
        Returns:
            dict: {
                'has_conflict': bool,
                'conflicting_courses': list,
                'conflict_details': list
            }
        """
        # Öğrencinin onaylı kayıtları
        enrollments = Enrollment.query.filter_by(
            student_id=student_id,
            status='approved'
        ).all()
        
        all_conflicts = []
        conflicting_courses = []
        
        for enrollment in enrollments:
            result = ConflictService.check_conflict_between_courses(
                enrollment.course_id, 
                new_course_id
            )
            
            if result['has_conflict']:
                conflicting_courses.append(enrollment.course)
                all_conflicts.extend(result['conflicts'])
        
        return {
            'has_conflict': len(all_conflicts) > 0,
            'conflicting_courses': conflicting_courses,
            'conflict_details': all_conflicts
        }
    
    @staticmethod
    def check_conflicts_in_request_list(student_id):
        """
        Öğrencinin talep listesindeki dersler arasında çakışma kontrolü
        
        Returns:
            dict: {
                'has_conflicts': bool,
                'conflict_pairs': list of (course1, course2, details)
            }
        """
        requests = CourseRequest.query.filter_by(
            student_id=student_id,
            status='pending'
        ).order_by(CourseRequest.priority_order).all()
        
        conflict_pairs = []
        
        for i in range(len(requests)):
            for j in range(i + 1, len(requests)):
                result = ConflictService.check_conflict_between_courses(
                    requests[i].course_id,
                    requests[j].course_id
                )
                
                if result['has_conflict']:
                    conflict_pairs.append({
                        'course1': requests[i].course,
                        'course2': requests[j].course,
                        'details': result['conflicts'],
                        'request1_priority': requests[i].priority_order,
                        'request2_priority': requests[j].priority_order,
                        'request1_mandatory': requests[i].is_mandatory,
                        'request2_mandatory': requests[j].is_mandatory
                    })
        
        return {
            'has_conflicts': len(conflict_pairs) > 0,
            'conflict_pairs': conflict_pairs
        }
    
    @staticmethod
    def resolve_conflict(conflict_pair):
        """
        Çakışma çözümleme politikası uygula
        
        Kurallar (öncelik sırasına göre):
        1. Zorunlu ders her zaman öncelikli
        2. Düşük priority_order (yüksek öncelik) tercih edilir
        3. Eşitlik durumunda ilk eklenen kalır
        
        Returns:
            dict: {
                'keep_course': Course,
                'drop_course': Course,
                'reason': str
            }
        """
        course1 = conflict_pair['course1']
        course2 = conflict_pair['course2']
        req1_mandatory = conflict_pair['request1_mandatory']
        req2_mandatory = conflict_pair['request2_mandatory']
        req1_priority = conflict_pair['request1_priority']
        req2_priority = conflict_pair['request2_priority']
        
        # Kural 1: Zorunlu ders kontrolü
        if req1_mandatory and not req2_mandatory:
            return {
                'keep_course': course1,
                'drop_course': course2,
                'reason': f"'{course1.code}' zorunlu ders olarak işaretlenmiş"
            }
        elif req2_mandatory and not req1_mandatory:
            return {
                'keep_course': course2,
                'drop_course': course1,
                'reason': f"'{course2.code}' zorunlu ders olarak işaretlenmiş"
            }
        
        # Kural 2: Öncelik sırası kontrolü (düşük değer = yüksek öncelik)
        if req1_priority < req2_priority:
            return {
                'keep_course': course1,
                'drop_course': course2,
                'reason': f"'{course1.code}' daha yüksek önceliğe sahip (sıra: {req1_priority})"
            }
        elif req2_priority < req1_priority:
            return {
                'keep_course': course2,
                'drop_course': course1,
                'reason': f"'{course2.code}' daha yüksek önceliğe sahip (sıra: {req2_priority})"
            }
        
        # Kural 3: Eşitlik - ders türüne göre (zorunlu > seçmeli)
        type_priority = {'required': 1, 'technical_elective': 2, 'elective': 3}
        type1 = type_priority.get(course1.course_type, 3)
        type2 = type_priority.get(course2.course_type, 3)
        
        if type1 < type2:
            return {
                'keep_course': course1,
                'drop_course': course2,
                'reason': f"'{course1.code}' zorunlu/teknik seçmeli ders"
            }
        else:
            return {
                'keep_course': course2,
                'drop_course': course1,
                'reason': f"'{course2.code}' zorunlu/teknik seçmeli ders"
            }
    
    @staticmethod
    def get_conflict_free_schedule(requests):
        """
        Talep listesinden çakışmasız bir program oluştur
        
        Args:
            requests: CourseRequest listesi (öncelik sırasına göre)
        
        Returns:
            dict: {
                'approved': list of courses,
                'rejected': list of {course, reason}
            }
        """
        approved = []
        rejected = []
        approved_schedules = []  # Onaylanan derslerin programları
        
        for request in requests:
            course = request.course
            course_schedules = course.schedules.all()
            
            has_conflict = False
            conflict_with = None
            
            # Mevcut onaylı derslerle çakışma kontrolü
            for approved_course in approved:
                result = ConflictService.check_conflict_between_courses(
                    approved_course.id,
                    course.id
                )
                if result['has_conflict']:
                    has_conflict = True
                    conflict_with = approved_course
                    break
            
            if has_conflict:
                rejected.append({
                    'course': course,
                    'reason': f"'{conflict_with.code}' dersiyle saat çakışması",
                    'conflict_type': 'time_conflict'
                })
            else:
                approved.append(course)
                approved_schedules.extend(course_schedules)
        
        return {
            'approved': approved,
            'rejected': rejected
        }
    
    @staticmethod
    def get_conflict_report(student_id):
        """Öğrencinin tüm çakışma raporunu oluştur"""
        # Bekleyen talepler
        pending_result = ConflictService.check_conflicts_in_request_list(student_id)
        
        # Onaylı kayıtlar
        enrollments = Enrollment.query.filter_by(
            student_id=student_id,
            status='approved'
        ).all()
        
        enrolled_conflicts = []
        for i in range(len(enrollments)):
            for j in range(i + 1, len(enrollments)):
                result = ConflictService.check_conflict_between_courses(
                    enrollments[i].course_id,
                    enrollments[j].course_id
                )
                if result['has_conflict']:
                    enrolled_conflicts.append({
                        'course1': enrollments[i].course,
                        'course2': enrollments[j].course,
                        'details': result['conflicts']
                    })
        
        return {
            'pending_conflicts': pending_result['conflict_pairs'],
            'enrolled_conflicts': enrolled_conflicts,
            'total_pending_conflicts': len(pending_result['conflict_pairs']),
            'total_enrolled_conflicts': len(enrolled_conflicts)
        }
