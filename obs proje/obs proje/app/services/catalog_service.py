"""
Ders Kataloğu Servisi
Ders ekleme, silme, arama ve yönetim işlemleri
"""
from app import db
from app.models.course import Course, CourseSchedule, Prerequisite
from sqlalchemy import or_

class CatalogService:
    """Ders kataloğu yönetim servisi"""
    
    @staticmethod
    def get_course_by_code(code):
        """Ders koduna göre ders getir - O(1) performans (index sayesinde)"""
        return Course.query.filter_by(code=code.upper()).first()
    
    @staticmethod
    def get_course_by_id(course_id):
        """ID'ye göre ders getir"""
        return Course.query.get(course_id)
    
    @staticmethod
    def get_all_courses(active_only=True):
        """Tüm dersleri getir"""
        query = Course.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(Course.code).all()
    
    @staticmethod
    def get_open_courses():
        """Kayıta açık dersleri getir"""
        return Course.query.filter_by(is_active=True, is_open=True).order_by(Course.code).all()
    
    @staticmethod
    def search_courses(keyword, department=None, course_type=None):
        """Ders arama - kod veya isim ile"""
        query = Course.query.filter_by(is_active=True)
        
        if keyword:
            keyword = f"%{keyword}%"
            query = query.filter(
                or_(
                    Course.code.ilike(keyword),
                    Course.name.ilike(keyword)
                )
            )
        
        if department:
            query = query.filter_by(department=department)
        
        if course_type:
            query = query.filter_by(course_type=course_type)
        
        return query.order_by(Course.code).all()
    
    @staticmethod
    def get_courses_by_department(department):
        """Bölüme göre ders getir"""
        return Course.query.filter_by(
            department=department, 
            is_active=True
        ).order_by(Course.code).all()
    
    @staticmethod
    def create_course(data):
        """Yeni ders oluştur"""
        course = Course(
            code=data['code'].upper(),
            name=data['name'],
            description=data.get('description', ''),
            credit=data.get('credit', 3),
            ects=data.get('ects', 5),
            department=data['department'],
            faculty=data['faculty'],
            quota=data.get('quota', 50),
            course_type=data.get('course_type', 'elective'),
            semester_type=data.get('semester_type', 'both'),
            target_class=data.get('target_class', 0)
        )
        
        db.session.add(course)
        db.session.flush()  # ID almak için
        
        # Ders programı ekle
        if 'schedules' in data:
            for sched_data in data['schedules']:
                schedule = CourseSchedule(
                    course_id=course.id,
                    day=sched_data['day'],
                    start_time=sched_data['start_time'],
                    end_time=sched_data['end_time'],
                    classroom=sched_data.get('classroom', '')
                )
                db.session.add(schedule)
        
        # Ön şartları ekle
        if 'prerequisites' in data:
            for prereq_code in data['prerequisites']:
                prereq = Prerequisite(
                    course_id=course.id,
                    prerequisite_code=prereq_code.upper()
                )
                db.session.add(prereq)
        
        db.session.commit()
        return course
    
    @staticmethod
    def update_course(course_id, data):
        """Ders güncelle"""
        course = Course.query.get(course_id)
        if not course:
            return None
        
        # Temel bilgileri güncelle
        if 'name' in data:
            course.name = data['name']
        if 'description' in data:
            course.description = data['description']
        if 'credit' in data:
            course.credit = data['credit']
        if 'quota' in data:
            course.quota = data['quota']
        if 'course_type' in data:
            course.course_type = data['course_type']
        if 'is_open' in data:
            course.is_open = data['is_open']
        
        # Ders programını güncelle
        if 'schedules' in data:
            # Mevcut programları sil
            CourseSchedule.query.filter_by(course_id=course.id).delete()
            
            # Yeni programları ekle
            for sched_data in data['schedules']:
                schedule = CourseSchedule(
                    course_id=course.id,
                    day=sched_data['day'],
                    start_time=sched_data['start_time'],
                    end_time=sched_data['end_time'],
                    classroom=sched_data.get('classroom', '')
                )
                db.session.add(schedule)
        
        # Ön şartları güncelle
        if 'prerequisites' in data:
            Prerequisite.query.filter_by(course_id=course.id).delete()
            
            for prereq_code in data['prerequisites']:
                prereq = Prerequisite(
                    course_id=course.id,
                    prerequisite_code=prereq_code.upper()
                )
                db.session.add(prereq)
        
        db.session.commit()
        return course
    
    @staticmethod
    def delete_course(course_id):
        """Ders sil (soft delete)"""
        course = Course.query.get(course_id)
        if course:
            course.is_active = False
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def hard_delete_course(course_id):
        """Dersi tamamen sil"""
        course = Course.query.get(course_id)
        if course:
            db.session.delete(course)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def update_quota(course_id, new_quota):
        """Kontenjan güncelle"""
        course = Course.query.get(course_id)
        if course:
            course.quota = new_quota
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def increment_enrolled_count(course_id):
        """Kayıtlı öğrenci sayısını artır"""
        course = Course.query.get(course_id)
        if course:
            course.enrolled_count += 1
            if course.enrolled_count >= course.quota:
                course.is_open = False
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def decrement_enrolled_count(course_id):
        """Kayıtlı öğrenci sayısını azalt"""
        course = Course.query.get(course_id)
        if course and course.enrolled_count > 0:
            course.enrolled_count -= 1
            if course.enrolled_count < course.quota:
                course.is_open = True
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_full_courses():
        """Kontenjanı dolan dersleri getir"""
        courses = Course.query.filter_by(is_active=True).all()
        return [c for c in courses if c.is_full]
    
    @staticmethod
    def get_available_courses():
        """Kontenjanı dolmamış dersleri getir"""
        courses = Course.query.filter_by(is_active=True, is_open=True).all()
        return [c for c in courses if not c.is_full]
    
    @staticmethod
    def get_departments():
        """Tüm bölümleri getir"""
        result = db.session.query(Course.department).distinct().all()
        return [r[0] for r in result]
    
    @staticmethod
    def get_faculties():
        """Tüm fakülteleri getir"""
        result = db.session.query(Course.faculty).distinct().all()
        return [r[0] for r in result]
    
    @staticmethod
    def reset_all_enrollments():
        """Tüm derslerin kayıt sayılarını sıfırla (dönem başı)"""
        Course.query.update({Course.enrolled_count: 0, Course.is_open: True})
        db.session.commit()
