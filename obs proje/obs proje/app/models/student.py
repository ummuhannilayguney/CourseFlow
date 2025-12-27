"""
Öğrenci Modeli
"""
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Student(UserMixin, db.Model):
    """Öğrenci modeli - Öncelik sistemi dahil"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Kişisel Bilgiler
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    
    # Akademik Bilgiler
    department = db.Column(db.String(100), nullable=False)
    faculty = db.Column(db.String(100), nullable=False)
    class_level = db.Column(db.Integer, nullable=False, default=1)  # 1-4 sınıf
    gpa = db.Column(db.Float, default=0.0)  # Not ortalaması (0-4)
    total_credits = db.Column(db.Integer, default=0)  # Toplam alınan kredi
    remaining_courses = db.Column(db.Integer, default=40)  # Mezuniyete kalan ders
    
    # Özel Durum
    special_status = db.Column(db.String(50), default='none')  # scholarship, double_major, honor_student, exchange
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Hesaplanan Öncelik Puanı
    priority_score = db.Column(db.Float, default=0.0)
    
    # Tarihler
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    course_requests = db.relationship('CourseRequest', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    completed_courses = db.relationship('CompletedCourse', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    waitlist_entries = db.relationship('WaitList', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Şifre hash'le"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Şifre doğrula"""
        return check_password_hash(self.password_hash, password)
    
    def calculate_priority_score(self):
        """
        Öncelik puanı hesapla
        Faktörler:
        - Sınıf seviyesi (4. sınıf en yüksek)
        - Mezuniyete kalan ders sayısı (az kalan yüksek)
        - Not ortalaması
        - Özel durum bonusu
        """
        from config import Config
        
        weights = Config.PRIORITY_WEIGHTS
        bonus = Config.SPECIAL_STATUS_BONUS
        
        # Sınıf seviyesi puanı (1-4 -> 25-100)
        class_score = (self.class_level / 4) * weights['class_level']
        
        # Mezuniyete kalan ders puanı (az kalan yüksek puan alır)
        # 0 ders kaldı -> max puan, 40+ ders kaldı -> min puan
        remaining_score = max(0, (1 - self.remaining_courses / 40)) * weights['remaining_courses']
        
        # GPA puanı (0-4 -> 0-100 normalize)
        gpa_score = (self.gpa / 4) * weights['gpa']
        
        # Özel durum bonusu
        special_score = bonus.get(self.special_status, 0)
        
        self.priority_score = class_score + remaining_score + gpa_score + special_score
        return self.priority_score
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_completed_course_codes(self):
        """Tamamlanan ders kodlarını getir"""
        return [cc.course_code for cc in self.completed_courses]
    
    def get_current_schedule(self):
        """Mevcut ders programını getir"""
        return self.enrollments.filter_by(status='approved').all()
    
    def get_pending_requests(self):
        """Bekleyen ders taleplerini getir"""
        return self.course_requests.filter_by(status='pending').order_by(CourseRequest.priority_order).all()
    
    def to_dict(self):
        """Model'i dictionary'e çevir"""
        return {
            'id': self.id,
            'student_number': self.student_number,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'department': self.department,
            'faculty': self.faculty,
            'class_level': self.class_level,
            'gpa': self.gpa,
            'remaining_courses': self.remaining_courses,
            'special_status': self.special_status,
            'priority_score': self.priority_score,
            'is_admin': self.is_admin
        }
    
    def __repr__(self):
        return f'<Student {self.student_number}: {self.full_name}>'


class CompletedCourse(db.Model):
    """Öğrencinin tamamladığı dersler (Transkript)"""
    __tablename__ = 'completed_courses'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_code = db.Column(db.String(20), nullable=False)
    course_name = db.Column(db.String(200), nullable=False)
    grade = db.Column(db.String(2), nullable=False)  # AA, BA, BB, CB, CC, DC, DD, FF
    credit = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.String(20), nullable=False)  # 2023-Güz, 2024-Bahar
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CompletedCourse {self.course_code}: {self.grade}>'


@login_manager.user_loader
def load_user(id):
    return Student.query.get(int(id))
