"""
Kayıt Simülasyonu Servisi
Toplu kayıt işlemi ve metrik hesaplama
"""
from app import db
from app.models.student import Student
from app.models.course import Course
from app.models.enrollment import CourseRequest, Enrollment
from app.models.simulation import SimulationResult, SimulationMetrics
from app.services.priority_service import PriorityService
from app.services.enrollment_service import EnrollmentService
from app.services.catalog_service import CatalogService
from datetime import datetime
import time

class SimulationService:
    """Kayıt simülasyonu servisi"""
    
    @staticmethod
    def run_simulation(semester):
        """
        Tam kayıt simülasyonu çalıştır
        
        Akış:
        1. Tüm öncelik puanlarını hesapla
        2. Öğrencileri önceliğe göre sırala
        3. Her öğrenci için kayıt işlemlerini sırayla yap
        4. Metrikleri hesapla ve kaydet
        
        Returns:
            SimulationMetrics: Simülasyon sonuç metrikleri
        """
        start_time = time.time()
        
        # Metrik kaydı oluştur
        metrics = SimulationMetrics(semester=semester)
        db.session.add(metrics)
        db.session.flush()
        
        # 1. Öncelik puanlarını hesapla
        PriorityService.calculate_all_priorities()
        
        # 2. Öğrencileri önceliğe göre sırala
        students = PriorityService.get_students_by_priority()
        metrics.total_students = len(students)
        
        # 3. Aktif dersleri say
        courses = CatalogService.get_all_courses(active_only=True)
        metrics.total_courses = len(courses)
        
        # İstatistikler
        total_requests = 0
        total_approved = 0
        total_rejected = 0
        rejected_quota = 0
        rejected_conflict = 0
        rejected_prerequisite = 0
        rejected_other = 0
        total_waitlist = 0
        
        # 4. Her öğrenci için kayıt işlemi
        for student in students:
            # Bekleyen talepleri kontrol
            pending_requests = CourseRequest.query.filter_by(
                student_id=student.id,
                status='pending'
            ).count()
            
            if pending_requests == 0:
                continue
            
            total_requests += pending_requests
            
            # Kayıt işlemini yap
            result = EnrollmentService.process_student_requests(student.id, semester)
            
            # Sonuçları kaydet
            sim_result = SimulationResult(
                student_id=student.id,
                simulation_id=metrics.id,
                requested_courses=pending_requests,
                approved_courses=len(result['approved']),
                rejected_courses=len(result['rejected']),
                priority_score_at_simulation=student.priority_score
            )
            
            # Reddedilme detayları
            rejection_details = []
            for rejected in result['rejected']:
                reason = rejected['reason']
                rejection_details.append({
                    'course_code': rejected['course']['code'],
                    'reason': reason
                })
                
                # Sebebe göre sayaç artır
                if 'kontenjan' in reason.lower():
                    rejected_quota += 1
                elif 'çakışma' in reason.lower():
                    rejected_conflict += 1
                elif 'ön şart' in reason.lower():
                    rejected_prerequisite += 1
                else:
                    rejected_other += 1
            
            sim_result.set_rejection_details(rejection_details)
            db.session.add(sim_result)
            
            total_approved += len(result['approved'])
            total_rejected += len(result['rejected'])
            total_waitlist += len(result.get('waitlisted', []))
        
        # 5. Metrikleri güncelle
        metrics.total_requests = total_requests
        metrics.total_approved = total_approved
        metrics.total_rejected = total_rejected
        metrics.rejected_quota = rejected_quota
        metrics.rejected_conflict = rejected_conflict
        metrics.rejected_prerequisite = rejected_prerequisite
        metrics.rejected_other = rejected_other
        metrics.total_waitlist = total_waitlist
        
        # Kontenjanı dolan dersler
        metrics.courses_full = len(CatalogService.get_full_courses())
        
        # Ortalamaları hesapla
        metrics.calculate_averages()
        
        # İşlem süresi
        metrics.processing_time_seconds = time.time() - start_time
        metrics.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return metrics
    
    @staticmethod
    def get_simulation_results(simulation_id):
        """Simülasyon sonuçlarını getir"""
        metrics = SimulationMetrics.query.get(simulation_id)
        if not metrics:
            return None
        
        results = SimulationResult.query.filter_by(simulation_id=simulation_id).all()
        
        return {
            'metrics': metrics.to_dict(),
            'student_results': [r.to_dict() for r in results]
        }
    
    @staticmethod
    def get_latest_simulation(semester=None):
        """En son simülasyonu getir"""
        query = SimulationMetrics.query
        
        if semester:
            query = query.filter_by(semester=semester)
        
        return query.order_by(SimulationMetrics.completed_at.desc()).first()
    
    @staticmethod
    def get_all_simulations():
        """Tüm simülasyonları getir"""
        return SimulationMetrics.query.order_by(
            SimulationMetrics.completed_at.desc()
        ).all()
    
    @staticmethod
    def get_student_simulation_result(simulation_id, student_id):
        """Belirli bir öğrencinin simülasyon sonucunu getir"""
        return SimulationResult.query.filter_by(
            simulation_id=simulation_id,
            student_id=student_id
        ).first()
    
    @staticmethod
    def generate_detailed_report(simulation_id):
        """
        Detaylı simülasyon raporu oluştur
        """
        metrics = SimulationMetrics.query.get(simulation_id)
        if not metrics:
            return None
        
        results = SimulationResult.query.filter_by(simulation_id=simulation_id).all()
        
        # Öğrenci bazlı analiz
        students_full_enrollment = 0  # Tüm derslerini alan öğrenciler
        students_partial_enrollment = 0  # Kısmi kayıt
        students_no_enrollment = 0  # Hiç ders alamayan
        
        for result in results:
            if result.rejected_courses == 0 and result.approved_courses > 0:
                students_full_enrollment += 1
            elif result.approved_courses > 0:
                students_partial_enrollment += 1
            else:
                students_no_enrollment += 1
        
        # Ders bazlı analiz
        courses = Course.query.filter_by(is_active=True).all()
        course_stats = []
        
        for course in courses:
            enrollments = Enrollment.query.filter_by(
                course_id=course.id,
                status='approved'
            ).count()
            
            course_stats.append({
                'code': course.code,
                'name': course.name,
                'quota': course.quota,
                'enrolled': enrollments,
                'fill_rate': round((enrollments / course.quota) * 100, 1) if course.quota > 0 else 0,
                'is_full': enrollments >= course.quota
            })
        
        # En çok talep edilen dersler
        most_requested = sorted(course_stats, key=lambda x: x['enrolled'], reverse=True)[:10]
        
        # En az talep edilen dersler
        least_requested = sorted(course_stats, key=lambda x: x['enrolled'])[:10]
        
        return {
            'metrics': metrics.to_dict(),
            'student_analysis': {
                'full_enrollment': students_full_enrollment,
                'partial_enrollment': students_partial_enrollment,
                'no_enrollment': students_no_enrollment,
                'success_rate': round(
                    (students_full_enrollment / len(results)) * 100, 1
                ) if results else 0
            },
            'course_analysis': {
                'total_courses': len(courses),
                'full_courses': len([c for c in course_stats if c['is_full']]),
                'empty_courses': len([c for c in course_stats if c['enrolled'] == 0]),
                'most_requested': most_requested,
                'least_requested': least_requested
            },
            'rejection_breakdown': {
                'quota': metrics.rejected_quota,
                'conflict': metrics.rejected_conflict,
                'prerequisite': metrics.rejected_prerequisite,
                'other': metrics.rejected_other,
                'quota_percentage': round(
                    (metrics.rejected_quota / metrics.total_rejected) * 100, 1
                ) if metrics.total_rejected > 0 else 0,
                'conflict_percentage': round(
                    (metrics.rejected_conflict / metrics.total_rejected) * 100, 1
                ) if metrics.total_rejected > 0 else 0,
                'prerequisite_percentage': round(
                    (metrics.rejected_prerequisite / metrics.total_rejected) * 100, 1
                ) if metrics.total_rejected > 0 else 0
            }
        }
    
    @staticmethod
    def reset_simulation(semester):
        """
        Simülasyonu sıfırla (test amaçlı)
        - Tüm kayıtları sil
        - Kontenjanları sıfırla
        - Talepleri pending'e çevir
        """
        # Kayıtları sil
        Enrollment.query.filter_by(semester=semester).delete()
        
        # Bekleme listelerini temizle
        from app.models.enrollment import WaitList
        WaitList.query.delete()
        
        # Kontenjanları sıfırla
        CatalogService.reset_all_enrollments()
        
        # Talepleri pending'e çevir
        requests = CourseRequest.query.filter(
            CourseRequest.status.in_(['approved', 'rejected'])
        ).all()
        
        for req in requests:
            req.status = 'pending'
            req.rejection_reason = None
            req.processed_at = None
        
        db.session.commit()
        
        return {'success': True, 'message': 'Simülasyon sıfırlandı'}
    
    @staticmethod
    def preview_simulation(semester):
        """
        Simülasyon önizleme (değişiklik yapmadan)
        Sonuçları tahmin et
        """
        students = PriorityService.get_students_by_priority()
        
        # Geçici kontenjan takibi
        temp_quotas = {}
        courses = Course.query.filter_by(is_active=True).all()
        for course in courses:
            temp_quotas[course.id] = course.quota - course.enrolled_count
        
        preview_results = []
        
        for student in students:
            requests = CourseRequest.query.filter_by(
                student_id=student.id,
                status='pending'
            ).order_by(CourseRequest.priority_order).all()
            
            if not requests:
                continue
            
            student_preview = {
                'student_id': student.id,
                'student_name': student.full_name,
                'priority_score': student.priority_score,
                'requested': len(requests),
                'likely_approved': 0,
                'likely_rejected': 0,
                'issues': []
            }
            
            for req in requests:
                course = req.course
                
                # Basit önizleme kontrolü
                if temp_quotas.get(course.id, 0) <= 0:
                    student_preview['likely_rejected'] += 1
                    student_preview['issues'].append(f"{course.code}: Kontenjan dolu olabilir")
                else:
                    student_preview['likely_approved'] += 1
                    temp_quotas[course.id] -= 1
            
            preview_results.append(student_preview)
        
        return {
            'total_students': len(preview_results),
            'results': preview_results[:50]  # İlk 50 öğrenci
        }
