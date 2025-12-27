"""
Ders Modeli ve İlişkili Tablolar
"""
from app import db
from datetime import datetime

class Course(db.Model):
    """Ders kataloğu modeli"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Akademik Bilgiler
    credit = db.Column(db.Integer, nullable=False, default=3)
    ects = db.Column(db.Integer, default=5)
    department = db.Column(db.String(100), nullable=False)
    faculty = db.Column(db.String(100), nullable=False)
    
    # Kontenjan Bilgileri
    quota = db.Column(db.Integer, nullable=False, default=50)
    enrolled_count = db.Column(db.Integer, default=0)
    
    # Ders Türü
    course_type = db.Column(db.String(20), default='elective')  # required, elective, technical_elective
    semester_type = db.Column(db.String(10), default='both')  # fall, spring, both
    target_class = db.Column(db.Integer, default=0)  # 0=tüm sınıflar, 1-4=belirli sınıf
    
    # Durum
    is_active = db.Column(db.Boolean, default=True)
    is_open = db.Column(db.Boolean, default=True)  # Kayıta açık mı
    
    # Tarihler
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    schedules = db.relationship('CourseSchedule', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    prerequisites = db.relationship('Prerequisite', backref='course', lazy='dynamic', 
                                    foreign_keys='Prerequisite.course_id', cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    requests = db.relationship('CourseRequest', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    waitlist = db.relationship('WaitList', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def available_quota(self):
        """Kalan kontenjan"""
        return max(0, self.quota - self.enrolled_count)
    
    @property
    def is_full(self):
        """Kontenjan doldu mu"""
        return self.enrolled_count >= self.quota
    
    @property
    def fill_percentage(self):
        """Doluluk yüzdesi"""
        if self.quota == 0:
            return 100
        return round((self.enrolled_count / self.quota) * 100, 1)
    
    def get_schedule_display(self):
        """Ders programı görüntüleme metni"""
        schedules = self.schedules.all()
        if not schedules:
            return "Belirtilmemiş"
        return ", ".join([s.display_text for s in schedules])
    
    def get_prerequisite_codes(self):
        """Ön şart ders kodlarını getir"""
        return [p.prerequisite_code for p in self.prerequisites]
    
    def check_time_conflict(self, other_course):
        """Başka bir dersle çakışma kontrolü"""
        my_schedules = self.schedules.all()
        other_schedules = other_course.schedules.all()
        
        for my_sched in my_schedules:
            for other_sched in other_schedules:
                if my_sched.conflicts_with(other_sched):
                    return True, my_sched, other_sched
        return False, None, None
    
    def to_dict(self):
        """Model'i dictionary'e çevir"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'credit': self.credit,
            'ects': self.ects,
            'department': self.department,
            'faculty': self.faculty,
            'quota': self.quota,
            'enrolled_count': self.enrolled_count,
            'available_quota': self.available_quota,
            'is_full': self.is_full,
            'fill_percentage': self.fill_percentage,
            'course_type': self.course_type,
            'is_open': self.is_open,
            'schedule': self.get_schedule_display(),
            'prerequisites': self.get_prerequisite_codes(),
            'schedules': [s.to_dict() for s in self.schedules]
        }
    
    def __repr__(self):
        return f'<Course {self.code}: {self.name}>'


class CourseSchedule(db.Model):
    """Ders zaman çizelgesi modeli"""
    __tablename__ = 'course_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    day = db.Column(db.String(20), nullable=False)  # Pazartesi, Salı, ...
    start_time = db.Column(db.String(5), nullable=False)  # HH:MM formatı
    end_time = db.Column(db.String(5), nullable=False)
    classroom = db.Column(db.String(50))
    
    # Gün kodu (sıralama için)
    DAY_ORDER = {
        'Pazartesi': 1, 'Salı': 2, 'Çarşamba': 3,
        'Perşembe': 4, 'Cuma': 5, 'Cumartesi': 6, 'Pazar': 7
    }
    
    @property
    def display_text(self):
        """Görüntüleme metni"""
        return f"{self.day} {self.start_time}-{self.end_time}"
    
    @property
    def day_order(self):
        """Gün sırası"""
        return self.DAY_ORDER.get(self.day, 8)
    
    def _time_to_minutes(self, time_str):
        """Zaman stringini dakikaya çevir"""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    def conflicts_with(self, other):
        """Başka bir zaman dilimiyle çakışma kontrolü"""
        if self.day != other.day:
            return False
        
        self_start = self._time_to_minutes(self.start_time)
        self_end = self._time_to_minutes(self.end_time)
        other_start = self._time_to_minutes(other.start_time)
        other_end = self._time_to_minutes(other.end_time)
        
        # Çakışma kontrolü
        return not (self_end <= other_start or other_end <= self_start)
    
    def to_dict(self):
        return {
            'id': self.id,
            'day': self.day,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'classroom': self.classroom,
            'display': self.display_text
        }
    
    def __repr__(self):
        return f'<CourseSchedule {self.display_text}>'


class Prerequisite(db.Model):
    """Ders ön şart modeli - Zincir destekli"""
    __tablename__ = 'prerequisites'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    prerequisite_code = db.Column(db.String(20), nullable=False, index=True)
    
    # Ön şart türü
    prereq_type = db.Column(db.String(20), default='required')  # required, recommended
    min_grade = db.Column(db.String(2), default='DD')  # Minimum geçme notu
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Prerequisite {self.prerequisite_code} for course_id={self.course_id}>'
