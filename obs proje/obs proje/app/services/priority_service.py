"""
Öncelik Hesaplama Servisi
"""
from app import db
from app.models.student import Student
from config import Config

class PriorityService:
    """Öğrenci öncelik hesaplama servisi"""
    
    @staticmethod
    def calculate_priority(student):
        """
        Öğrenci öncelik puanı hesapla
        
        Faktörler ve ağırlıkları:
        - Sınıf seviyesi: %30 (4. sınıf en yüksek)
        - Mezuniyete kalan ders: %25 (az kalan yüksek)
        - Not ortalaması: %20
        - Özel durum bonusu: %25
        """
        weights = Config.PRIORITY_WEIGHTS
        bonus = Config.SPECIAL_STATUS_BONUS
        
        # Sınıf seviyesi puanı (1-4 -> 25-100)
        class_score = (student.class_level / 4) * weights['class_level']
        
        # Mezuniyete kalan ders puanı
        # 0 ders kaldı -> max puan, 40+ ders kaldı -> min puan
        remaining_factor = max(0, 1 - (student.remaining_courses / 40))
        remaining_score = remaining_factor * weights['remaining_courses']
        
        # GPA puanı (0-4 -> normalize)
        gpa_score = (student.gpa / 4) * weights['gpa']
        
        # Özel durum bonusu
        special_score = bonus.get(student.special_status, 0)
        
        total_score = class_score + remaining_score + gpa_score + special_score
        
        return round(total_score, 2)
    
    @staticmethod
    def calculate_all_priorities():
        """Tüm öğrencilerin öncelik puanlarını hesapla ve kaydet"""
        students = Student.query.filter_by(is_admin=False, is_active=True).all()
        
        for student in students:
            student.priority_score = PriorityService.calculate_priority(student)
        
        db.session.commit()
        return len(students)
    
    @staticmethod
    def get_students_by_priority():
        """Öğrencileri öncelik puanına göre sıralı getir (yüksekten düşüğe)"""
        return Student.query.filter_by(
            is_admin=False, 
            is_active=True
        ).order_by(Student.priority_score.desc()).all()
    
    @staticmethod
    def get_priority_breakdown(student):
        """Öğrencinin öncelik puanı detayını getir"""
        weights = Config.PRIORITY_WEIGHTS
        bonus = Config.SPECIAL_STATUS_BONUS
        
        class_score = (student.class_level / 4) * weights['class_level']
        remaining_factor = max(0, 1 - (student.remaining_courses / 40))
        remaining_score = remaining_factor * weights['remaining_courses']
        gpa_score = (student.gpa / 4) * weights['gpa']
        special_score = bonus.get(student.special_status, 0)
        
        return {
            'student_id': student.id,
            'student_name': student.full_name,
            'total_score': round(class_score + remaining_score + gpa_score + special_score, 2),
            'breakdown': {
                'class_level': {
                    'value': student.class_level,
                    'weight': weights['class_level'],
                    'score': round(class_score, 2),
                    'description': f'{student.class_level}. sınıf'
                },
                'remaining_courses': {
                    'value': student.remaining_courses,
                    'weight': weights['remaining_courses'],
                    'score': round(remaining_score, 2),
                    'description': f'Mezuniyete {student.remaining_courses} ders kaldı'
                },
                'gpa': {
                    'value': student.gpa,
                    'weight': weights['gpa'],
                    'score': round(gpa_score, 2),
                    'description': f'Not ortalaması: {student.gpa:.2f}'
                },
                'special_status': {
                    'value': student.special_status,
                    'weight': weights['special_status'],
                    'score': round(special_score, 2),
                    'description': PriorityService._get_status_description(student.special_status)
                }
            }
        }
    
    @staticmethod
    def _get_status_description(status):
        """Özel durum açıklaması"""
        descriptions = {
            'none': 'Standart öğrenci',
            'scholarship': 'Burslu öğrenci',
            'double_major': 'Çift anadal öğrencisi',
            'honor_student': 'Onur öğrencisi',
            'exchange': 'Değişim öğrencisi'
        }
        return descriptions.get(status, 'Bilinmiyor')
    
    @staticmethod
    def compare_students(student1_id, student2_id):
        """İki öğrenciyi öncelik açısından karşılaştır"""
        student1 = Student.query.get(student1_id)
        student2 = Student.query.get(student2_id)
        
        if not student1 or not student2:
            return None
        
        breakdown1 = PriorityService.get_priority_breakdown(student1)
        breakdown2 = PriorityService.get_priority_breakdown(student2)
        
        return {
            'student1': breakdown1,
            'student2': breakdown2,
            'winner': student1_id if breakdown1['total_score'] > breakdown2['total_score'] else student2_id,
            'difference': abs(breakdown1['total_score'] - breakdown2['total_score'])
        }
