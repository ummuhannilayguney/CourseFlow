"""
Ders Programı ve Kayıt Dönemi Modelleri
"""
from app import db
from datetime import datetime

class Schedule(db.Model):
    """Öğrenci haftalık ders programı görünümü"""
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    
    # Program özeti
    total_credits = db.Column(db.Integer, default=0)
    total_courses = db.Column(db.Integer, default=0)
    
    # Tarihler
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Schedule student={self.student_id} semester={self.semester}>'


class RegistrationPeriod(db.Model):
    """Kayıt dönemi modeli"""
    __tablename__ = 'registration_periods'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(20), nullable=False)  # 2024-Güz
    
    # Dönem tarihleri
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    
    # Durum
    status = db.Column(db.String(20), default='upcoming')  # upcoming, active, processing, completed
    
    # Ayarlar
    is_simulation_complete = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_active(self):
        """Dönem aktif mi"""
        now = datetime.utcnow()
        return self.start_date <= now <= self.end_date and self.status == 'active'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'semester': self.semester,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<RegistrationPeriod {self.semester}: {self.status}>'
