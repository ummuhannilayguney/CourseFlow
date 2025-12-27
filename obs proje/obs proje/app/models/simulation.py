"""
Simülasyon Sonuçları ve Metrikler Modeli
"""
from app import db
from datetime import datetime
import json

class SimulationResult(db.Model):
    """Kayıt simülasyonu sonuçları"""
    __tablename__ = 'simulation_results'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    simulation_id = db.Column(db.Integer, db.ForeignKey('simulation_metrics.id'), nullable=False)
    
    # Sonuçlar
    requested_courses = db.Column(db.Integer, default=0)  # Talep edilen ders sayısı
    approved_courses = db.Column(db.Integer, default=0)   # Onaylanan ders sayısı
    rejected_courses = db.Column(db.Integer, default=0)   # Reddedilen ders sayısı
    
    # Reddedilme sebepleri detayı (JSON)
    rejection_details = db.Column(db.Text)  # JSON formatında detaylar
    
    # Öğrenci öncelik puanı (simülasyon anındaki)
    priority_score_at_simulation = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_rejection_details(self, details):
        """Reddedilme detaylarını JSON olarak kaydet"""
        self.rejection_details = json.dumps(details, ensure_ascii=False)
    
    def get_rejection_details(self):
        """Reddedilme detaylarını JSON'dan oku"""
        if self.rejection_details:
            return json.loads(self.rejection_details)
        return []
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'requested_courses': self.requested_courses,
            'approved_courses': self.approved_courses,
            'rejected_courses': self.rejected_courses,
            'rejection_details': self.get_rejection_details(),
            'priority_score': self.priority_score_at_simulation
        }
    
    def __repr__(self):
        return f'<SimulationResult student={self.student_id}>'


class SimulationMetrics(db.Model):
    """Simülasyon genel metrikleri"""
    __tablename__ = 'simulation_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    semester = db.Column(db.String(20), nullable=False)
    
    # Genel Sayılar
    total_students = db.Column(db.Integer, default=0)
    total_courses = db.Column(db.Integer, default=0)
    total_requests = db.Column(db.Integer, default=0)
    
    # Onay/Red İstatistikleri
    total_approved = db.Column(db.Integer, default=0)
    total_rejected = db.Column(db.Integer, default=0)
    
    # Reddedilme Sebepleri
    rejected_quota = db.Column(db.Integer, default=0)        # Kontenjan dolduğu için
    rejected_conflict = db.Column(db.Integer, default=0)     # Çakışma nedeniyle
    rejected_prerequisite = db.Column(db.Integer, default=0) # Ön şart nedeniyle
    rejected_other = db.Column(db.Integer, default=0)        # Diğer sebepler
    
    # Ders İstatistikleri
    courses_full = db.Column(db.Integer, default=0)          # Kontenjanı dolan ders sayısı
    
    # Ortalamalar
    avg_courses_per_student = db.Column(db.Float, default=0.0)
    avg_approval_rate = db.Column(db.Float, default=0.0)     # Ortalama onay oranı %
    
    # Bekleme Listesi
    total_waitlist = db.Column(db.Integer, default=0)
    
    # Süre
    processing_time_seconds = db.Column(db.Float, default=0.0)
    
    # Tarihler
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # İlişkiler
    results = db.relationship('SimulationResult', backref='simulation', lazy='dynamic')
    
    def calculate_averages(self):
        """Ortalamaları hesapla"""
        if self.total_students > 0:
            self.avg_courses_per_student = self.total_approved / self.total_students
        
        if self.total_requests > 0:
            self.avg_approval_rate = (self.total_approved / self.total_requests) * 100
    
    def to_dict(self):
        return {
            'id': self.id,
            'semester': self.semester,
            'total_students': self.total_students,
            'total_courses': self.total_courses,
            'total_requests': self.total_requests,
            'total_approved': self.total_approved,
            'total_rejected': self.total_rejected,
            'rejected_quota': self.rejected_quota,
            'rejected_conflict': self.rejected_conflict,
            'rejected_prerequisite': self.rejected_prerequisite,
            'rejected_other': self.rejected_other,
            'courses_full': self.courses_full,
            'avg_courses_per_student': round(self.avg_courses_per_student, 2),
            'avg_approval_rate': round(self.avg_approval_rate, 2),
            'total_waitlist': self.total_waitlist,
            'processing_time_seconds': round(self.processing_time_seconds, 3),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def __repr__(self):
        return f'<SimulationMetrics {self.semester}>'
