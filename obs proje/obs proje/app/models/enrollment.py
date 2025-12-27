"""
Kayıt ve Talep Modelleri
"""
from app import db
from datetime import datetime

class CourseRequest(db.Model):
    """Öğrenci ders talepleri (Sepet) modeli"""
    __tablename__ = 'course_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Talep Bilgileri
    priority_order = db.Column(db.Integer, default=0)  # Öğrencinin belirlediği öncelik sırası
    is_mandatory = db.Column(db.Boolean, default=False)  # Zorunlu ders mi (çakışmada öncelikli)
    
    # Durum
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    rejection_reason = db.Column(db.String(200))  # Reddedilme sebebi
    
    # Tarihler
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Unique constraint - bir öğrenci aynı dersi birden fazla kez talep edemez
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='unique_student_course_request'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'course_id': self.course_id,
            'course': self.course.to_dict() if self.course else None,
            'priority_order': self.priority_order,
            'is_mandatory': self.is_mandatory,
            'status': self.status,
            'rejection_reason': self.rejection_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<CourseRequest student={self.student_id} course={self.course_id}>'


class Enrollment(db.Model):
    """Kesinleşmiş ders kayıtları modeli"""
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Kayıt Bilgileri
    status = db.Column(db.String(20), default='approved')  # approved, dropped, completed
    semester = db.Column(db.String(20), nullable=False)  # 2024-Güz
    
    # Tarihler
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    dropped_at = db.Column(db.DateTime)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', 'semester', name='unique_enrollment'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'course_id': self.course_id,
            'course': self.course.to_dict() if self.course else None,
            'status': self.status,
            'semester': self.semester,
            'enrolled_at': self.enrolled_at.isoformat() if self.enrolled_at else None
        }
    
    def __repr__(self):
        return f'<Enrollment student={self.student_id} course={self.course_id}>'


class WaitList(db.Model):
    """Bekleme listesi modeli"""
    __tablename__ = 'waitlists'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Bekleme sırası
    position = db.Column(db.Integer, nullable=False)
    
    # Durum
    status = db.Column(db.String(20), default='waiting')  # waiting, notified, enrolled, expired
    
    # Tarihler
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    notified_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='unique_waitlist_entry'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'course_id': self.course_id,
            'course': self.course.to_dict() if self.course else None,
            'position': self.position,
            'status': self.status,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }
    
    def __repr__(self):
        return f'<WaitList student={self.student_id} course={self.course_id} pos={self.position}>'
