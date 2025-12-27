"""
Ön Şart Zinciri Kontrolü Servisi
Recursive ön şart kontrolü yapar
"""
from app import db
from app.models.course import Course, Prerequisite
from app.models.student import Student, CompletedCourse

class PrerequisiteService:
    """Ön şart kontrolü servisi"""
    
    # Grade değerleri (geçme kontrolü için)
    PASSING_GRADES = ['AA', 'BA', 'BB', 'CB', 'CC', 'DC', 'DD']
    GRADE_VALUES = {
        'AA': 4.0, 'BA': 3.5, 'BB': 3.0, 'CB': 2.5,
        'CC': 2.0, 'DC': 1.5, 'DD': 1.0, 'FF': 0.0
    }
    
    @staticmethod
    def get_prerequisite_chain(course_code, visited=None):
        """
        Bir dersin tüm ön şart zincirini recursive olarak getir
        Döngüsel bağımlılıkları engellemek için visited set kullanılır
        """
        if visited is None:
            visited = set()
        
        if course_code in visited:
            return []  # Döngüsel bağımlılık önleme
        
        visited.add(course_code)
        
        course = Course.query.filter_by(code=course_code).first()
        if not course:
            return []
        
        chain = []
        prerequisites = Prerequisite.query.filter_by(course_id=course.id).all()
        
        for prereq in prerequisites:
            prereq_code = prereq.prerequisite_code
            chain.append({
                'code': prereq_code,
                'min_grade': prereq.min_grade,
                'type': prereq.prereq_type,
                'level': 1
            })
            
            # Recursive olarak alt ön şartları getir
            sub_chain = PrerequisiteService.get_prerequisite_chain(prereq_code, visited.copy())
            for item in sub_chain:
                item['level'] += 1
                chain.append(item)
        
        return chain
    
    @staticmethod
    def check_prerequisites(student_id, course_code):
        """
        Öğrencinin bir dersi alabilmesi için gerekli ön şartları kontrol et
        
        Returns:
            dict: {
                'can_enroll': bool,
                'missing_prerequisites': list,
                'completed_prerequisites': list,
                'chain_details': list
            }
        """
        student = Student.query.get(student_id)
        if not student:
            return {
                'can_enroll': False,
                'error': 'Öğrenci bulunamadı',
                'missing_prerequisites': [],
                'completed_prerequisites': []
            }
        
        course = Course.query.filter_by(code=course_code).first()
        if not course:
            return {
                'can_enroll': False,
                'error': 'Ders bulunamadı',
                'missing_prerequisites': [],
                'completed_prerequisites': []
            }
        
        # Öğrencinin tamamladığı dersleri al
        completed = CompletedCourse.query.filter_by(student_id=student_id).all()
        completed_dict = {c.course_code: c.grade for c in completed}
        
        # Ön şart zincirini al
        chain = PrerequisiteService.get_prerequisite_chain(course_code)
        
        missing = []
        completed_prereqs = []
        
        for prereq in chain:
            prereq_code = prereq['code']
            min_grade = prereq['min_grade']
            
            if prereq_code in completed_dict:
                student_grade = completed_dict[prereq_code]
                
                # Not karşılaştırması
                if PrerequisiteService._is_grade_sufficient(student_grade, min_grade):
                    completed_prereqs.append({
                        'code': prereq_code,
                        'grade': student_grade,
                        'level': prereq['level']
                    })
                else:
                    missing.append({
                        'code': prereq_code,
                        'reason': f'Yetersiz not ({student_grade}, minimum {min_grade} gerekli)',
                        'level': prereq['level']
                    })
            else:
                missing.append({
                    'code': prereq_code,
                    'reason': 'Ders alınmamış',
                    'level': prereq['level']
                })
        
        return {
            'can_enroll': len(missing) == 0,
            'missing_prerequisites': missing,
            'completed_prerequisites': completed_prereqs,
            'chain_details': chain
        }
    
    @staticmethod
    def _is_grade_sufficient(student_grade, min_grade):
        """Not karşılaştırması"""
        grade_values = PrerequisiteService.GRADE_VALUES
        student_value = grade_values.get(student_grade, 0)
        min_value = grade_values.get(min_grade, 0)
        return student_value >= min_value
    
    @staticmethod
    def get_missing_prerequisites_message(missing_list):
        """Eksik ön şartlar için kullanıcı dostu mesaj oluştur"""
        if not missing_list:
            return "Tüm ön şartlar sağlanmış."
        
        messages = []
        for item in missing_list:
            level_text = "Doğrudan ön şart" if item['level'] == 1 else f"{item['level']}. seviye ön şart"
            messages.append(f"- {item['code']}: {item['reason']} ({level_text})")
        
        return "Eksik ön şartlar:\n" + "\n".join(messages)
    
    @staticmethod
    def add_prerequisite(course_code, prereq_code, min_grade='DD', prereq_type='required'):
        """Derse ön şart ekle"""
        course = Course.query.filter_by(code=course_code).first()
        if not course:
            return False, "Ders bulunamadı"
        
        # Döngüsel bağımlılık kontrolü
        if PrerequisiteService._would_create_cycle(course_code, prereq_code):
            return False, "Bu ön şart döngüsel bağımlılık oluşturur"
        
        # Mevcut kontrol
        existing = Prerequisite.query.filter_by(
            course_id=course.id,
            prerequisite_code=prereq_code
        ).first()
        
        if existing:
            return False, "Bu ön şart zaten ekli"
        
        prereq = Prerequisite(
            course_id=course.id,
            prerequisite_code=prereq_code.upper(),
            min_grade=min_grade,
            prereq_type=prereq_type
        )
        
        db.session.add(prereq)
        db.session.commit()
        return True, "Ön şart eklendi"
    
    @staticmethod
    def remove_prerequisite(course_code, prereq_code):
        """Dersten ön şart kaldır"""
        course = Course.query.filter_by(code=course_code).first()
        if not course:
            return False, "Ders bulunamadı"
        
        prereq = Prerequisite.query.filter_by(
            course_id=course.id,
            prerequisite_code=prereq_code
        ).first()
        
        if not prereq:
            return False, "Ön şart bulunamadı"
        
        db.session.delete(prereq)
        db.session.commit()
        return True, "Ön şart kaldırıldı"
    
    @staticmethod
    def _would_create_cycle(course_code, new_prereq_code):
        """Yeni ön şart eklemenin döngüsel bağımlılık oluşturup oluşturmayacağını kontrol et"""
        # new_prereq_code'un ön şartlarında course_code var mı?
        chain = PrerequisiteService.get_prerequisite_chain(new_prereq_code)
        for item in chain:
            if item['code'] == course_code:
                return True
        return False
    
    @staticmethod
    def visualize_prerequisite_tree(course_code):
        """Ön şart ağacını görselleştir (text formatında)"""
        chain = PrerequisiteService.get_prerequisite_chain(course_code)
        
        if not chain:
            return f"{course_code}: Ön şart yok"
        
        lines = [f"{course_code}"]
        
        # Level'a göre grupla
        max_level = max(item['level'] for item in chain)
        
        for item in sorted(chain, key=lambda x: (x['level'], x['code'])):
            indent = "  " * item['level']
            lines.append(f"{indent}└─ {item['code']} (min: {item['min_grade']})")
        
        return "\n".join(lines)
