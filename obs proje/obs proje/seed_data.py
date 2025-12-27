"""
Örnek Veri Oluşturma Scripti
Üniversite Ders Kayıt Sistemi için test verileri oluşturur.
"""

import sys
import os

# Add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    Student, Course, CourseSchedule, Prerequisite,
    RegistrationPeriod, CompletedCourse
)
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random


def create_sample_data():
    """Ana veri oluşturma fonksiyonu"""
    
    app = create_app()
    
    with app.app_context():
        # Mevcut verileri temizle
        print("Mevcut veriler temizleniyor...")
        db.drop_all()
        db.create_all()
        
        # Kayıt dönemi oluştur
        print("Kayıt dönemi oluşturuluyor...")
        registration_period = RegistrationPeriod(
            name='2024-2025 Güz Dönemi',
            semester='2024-Güz',
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=14),
            status='active'
        )
        db.session.add(registration_period)
        
        # Dersler oluştur
        print("Dersler oluşturuluyor...")
        courses = create_courses()
        
        # Ön şartlar oluştur
        print("Ön şartlar oluşturuluyor...")
        create_prerequisites(courses)
        
        # Ders programları oluştur
        print("Ders programları oluşturuluyor...")
        create_schedules(courses)
        
        # Öğrenciler oluştur
        print("Öğrenciler oluşturuluyor...")
        students = create_students()
        
        # Tamamlanan dersler oluştur
        print("Tamamlanan dersler oluşturuluyor...")
        create_completed_courses(students, courses)
        
        # Admin kullanıcı oluştur
        print("Admin kullanıcı oluşturuluyor...")
        create_admin()
        
        db.session.commit()
        print("\n✅ Örnek veriler başarıyla oluşturuldu!")
        print(f"   - {len(courses)} ders")
        print(f"   - {len(students)} öğrenci")
        print("   - 1 admin kullanıcı")
        print("\nGiriş bilgileri:")
        print("   Admin: admin / admin123")
        print("   Öğrenci: 20200001 / student123")


def create_courses():
    """Örnek dersler oluştur"""
    courses_data = [
        # 1. Sınıf Dersleri
        {'code': 'MAT101', 'name': 'Matematik I', 'credit': 4, 'department': 'Matematik', 'faculty': 'Fen Fakültesi',
         'course_type': 'required', 'target_class': 1, 'quota': 60},
        {'code': 'FIZ101', 'name': 'Fizik I', 'credit': 4, 'department': 'Fizik', 'faculty': 'Fen Fakültesi',
         'course_type': 'required', 'target_class': 1, 'quota': 60},
        {'code': 'BIL101', 'name': 'Bilgisayara Giriş', 'credit': 3, 'department': 'Bilgisayar', 'faculty': 'Mühendislik Fakültesi',
         'course_type': 'required', 'target_class': 1, 'quota': 50},
        {'code': 'ING101', 'name': 'İngilizce I', 'credit': 2, 'department': 'Yabancı Diller', 'faculty': 'Yabancı Diller Yüksekokulu',
         'course_type': 'required', 'target_class': 1, 'quota': 40},
        {'code': 'TRK101', 'name': 'Türk Dili I', 'credit': 2, 'department': 'Türk Dili', 'faculty': 'Edebiyat Fakültesi',
         'course_type': 'required', 'target_class': 1, 'quota': 80},
        
        # 2. Sınıf Dersleri
        {'code': 'MAT201', 'name': 'Matematik II', 'credit': 4, 'department': 'Matematik', 'faculty': 'Fen Fakültesi',
         'course_type': 'required', 'target_class': 2, 'quota': 55},
        {'code': 'FIZ201', 'name': 'Fizik II', 'credit': 4, 'department': 'Fizik', 'faculty': 'Fen Fakültesi',
         'course_type': 'required', 'target_class': 2, 'quota': 55},
        {'code': 'BIL201', 'name': 'Programlama I', 'credit': 4, 'department': 'Bilgisayar', 'faculty': 'Mühendislik Fakültesi',
         'course_type': 'required', 'target_class': 2, 'quota': 45},
        {'code': 'BIL202', 'name': 'Veri Yapıları', 'credit': 4, 'department': 'Bilgisayar', 'faculty': 'Mühendislik Fakültesi',
         'course_type': 'required', 'target_class': 2, 'quota': 45},
        {'code': 'ING201', 'name': 'İngilizce II', 'credit': 2, 'department': 'Yabancı Diller', 'faculty': 'Yabancı Diller Yüksekokulu',
         'course_type': 'required', 'target_class': 2, 'quota': 40},
        
        # 3. Sınıf Dersleri
        {'code': 'BIL301', 'name': 'Algoritmalar', 'credit': 4, 'department': 'Bilgisayar', 'faculty': 'Mühendislik Fakültesi',
         'course_type': 'required', 'target_class': 3, 'quota': 40},
        {'code': 'BIL302', 'name': 'Veritabanı Sistemleri', 'credit': 4, 'department': 'Bilgisayar', 'faculty': 'Mühendislik Fakültesi',
         'course_type': 'required', 'target_class': 3, 'quota': 40},
        {'code': 'BIL303', 'name': 'İşletim Sistemleri', 'credit': 4, 'department': 'Bilgisayar', 'faculty': 'Mühendislik Fakültesi',
         'course_type': 'required', 'target_class': 3, 'quota': 40},
        {'code': 'BIL304', 'name': 'Yazılım Mühendisliği', 'credit': 3, 'department': 'Bilgisayar', 'faculty': 'Mühendislik Fakültesi',
         'course_type': 'required', 'target_class': 3, 'quota': 40},
        {'code': 'BIL305', 'name': 'Bilgisayar Ağları', 'credit': 3, 'department': 'Bilgisayar', 'faculty': 'Mühendislik Fakültesi',
         'course_type': 'elective', 'target_class': 3, 'quota': 35},
        
        # 4. Sınıf Dersleri
        {'code': 'BIL401', 'name': 'Yapay Zeka', 'credit': 4, 'department': 'Bilgisayar', 'faculty': 'Mühendislik Fakültesi',
         'course_type': 'elective', 'target_class': 4, 'quota': 30},
        {'code': 'BIL402', 'name': 'Makine Öğrenmesi', 'credit': 4, 'department': 'Bilgisayar', 'faculty': 'Mühendislik Fakültesi',
         'course_type': 'elective', 'target_class': 4, 'quota': 30},
        {'code': 'BIL403', 'name': 'Web Programlama', 'credit': 3, 'department': 'Bilgisayar', 'faculty': 'Mühendislik Fakültesi',
         'course_type': 'elective', 'target_class': 4, 'quota': 35},
        {'code': 'BIL404', 'name': 'Mobil Programlama', 'credit': 3, 'department': 'Bilgisayar', 'faculty': 'Mühendislik Fakültesi',
         'course_type': 'elective', 'target_class': 4, 'quota': 35},
        {'code': 'BIL405', 'name': 'Bitirme Projesi', 'credit': 6, 'department': 'Bilgisayar', 'faculty': 'Mühendislik Fakültesi',
         'course_type': 'required', 'target_class': 4, 'quota': 50},
    ]
    
    courses = []
    for data in courses_data:
        course = Course(**data)
        db.session.add(course)
        courses.append(course)
    
    db.session.flush()
    return courses


def create_prerequisites(courses):
    """Ön şartları oluştur"""
    course_dict = {c.code: c for c in courses}
    
    prerequisites = [
        ('MAT201', 'MAT101'),  # Mat II için Mat I gerekli
        ('FIZ201', 'FIZ101'),  # Fizik II için Fizik I gerekli
        ('FIZ201', 'MAT101'),  # Fizik II için Mat I de gerekli
        ('BIL201', 'BIL101'),  # Programlama için Bilgisayara Giriş
        ('BIL202', 'BIL201'),  # Veri Yapıları için Programlama
        ('ING201', 'ING101'),  # İngilizce II için İngilizce I
        ('BIL301', 'BIL202'),  # Algoritmalar için Veri Yapıları
        ('BIL302', 'BIL201'),  # Veritabanı için Programlama
        ('BIL303', 'BIL201'),  # İşletim Sistemleri için Programlama
        ('BIL304', 'BIL202'),  # Yazılım Müh. için Veri Yapıları
        ('BIL305', 'BIL201'),  # Ağlar için Programlama
        ('BIL401', 'BIL301'),  # Yapay Zeka için Algoritmalar
        ('BIL402', 'BIL401'),  # Makine Öğr. için Yapay Zeka
        ('BIL403', 'BIL302'),  # Web için Veritabanı
        ('BIL404', 'BIL201'),  # Mobil için Programlama
        ('BIL405', 'BIL304'),  # Bitirme için Yazılım Müh.
    ]
    
    for course_code, prereq_code in prerequisites:
        if course_code in course_dict and prereq_code in course_dict:
            prereq = Prerequisite(
                course_id=course_dict[course_code].id,
                prerequisite_code=prereq_code
            )
            db.session.add(prereq)


def create_schedules(courses):
    """Ders programlarını oluştur"""
    days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
    time_slots = [
        ('09:00', '10:50'),
        ('11:00', '12:50'),
        ('13:00', '14:50'),
        ('15:00', '16:50'),
    ]
    rooms = ['A101', 'A102', 'A201', 'A202', 'B101', 'B102', 'B201', 'B202', 'LAB1', 'LAB2']
    
    for course in courses:
        # Her ders için 1-2 oturum
        num_sessions = 2 if course.credit >= 4 else 1
        used_slots = set()
        
        for _ in range(num_sessions):
            attempts = 0
            while attempts < 20:
                day = random.choice(days)
                time_slot = random.choice(time_slots)
                slot_key = (day, time_slot[0])
                
                if slot_key not in used_slots:
                    used_slots.add(slot_key)
                    schedule = CourseSchedule(
                        course_id=course.id,
                        day=day,
                        start_time=time_slot[0],
                        end_time=time_slot[1],
                        classroom=random.choice(rooms)
                    )
                    db.session.add(schedule)
                    break
                attempts += 1


def create_students():
    """Örnek öğrenciler oluştur"""
    students_data = []
    
    special_statuses = [None, None, None, None, None, 'disabled', 'scholarship', 'athlete', 'honor']
    
    # Her sınıf için öğrenci oluştur
    for year in range(1, 5):
        base_year = 2024 - year
        student_count = 15 if year <= 2 else 10
        
        for i in range(student_count):
            student_num = f"{base_year}000{i+1:02d}"
            
            # GPA - sınıf seviyesine göre biraz değişkenlik
            base_gpa = random.uniform(1.5, 4.0)
            
            # Kalan ders sayısı - üst sınıflar için daha az
            total_courses = 40
            completed = min(int((year - 1) * 10 + random.randint(0, 5)), total_courses - 5)
            remaining = total_courses - completed
            
            student = Student(
                student_number=student_num,
                email=f"{student_num}@ogrenci.edu.tr",
                first_name=random.choice(['Ahmet', 'Mehmet', 'Ali', 'Ayşe', 'Fatma', 'Zeynep', 'Mustafa', 'Elif', 'Emre', 'Selin']),
                last_name=random.choice(['Yılmaz', 'Kaya', 'Demir', 'Çelik', 'Şahin', 'Öztürk', 'Yıldız', 'Aydın', 'Arslan', 'Doğan']),
                department='Bilgisayar Mühendisliği',
                faculty='Mühendislik Fakültesi',
                class_level=year,
                gpa=round(base_gpa, 2),
                remaining_courses=remaining,
                special_status=random.choice(special_statuses),
                is_active=True
            )
            student.set_password('student123')
            db.session.add(student)
            students_data.append(student)
    
    db.session.flush()
    return students_data


def create_completed_courses(students, courses):
    """Öğrencilerin tamamladığı dersleri oluştur"""
    course_by_year = {}
    for course in courses:
        if course.target_class not in course_by_year:
            course_by_year[course.target_class] = []
        course_by_year[course.target_class].append(course)
    
    for student in students:
        # Öğrencinin sınıf seviyesine göre geçmiş dersleri belirle
        for year in range(1, student.class_level):
            if year in course_by_year:
                for course in course_by_year[year]:
                    # %80 ihtimalle dersi geçmiş
                    if random.random() < 0.8:
                        grade_options = ['AA', 'BA', 'BB', 'CB', 'CC', 'DC', 'DD']
                        weights = [0.1, 0.15, 0.25, 0.2, 0.15, 0.1, 0.05]
                        
                        completed = CompletedCourse(
                            student_id=student.id,
                            course_code=course.code,
                            course_name=course.name,
                            credit=course.credit,
                            grade=random.choices(grade_options, weights)[0],
                            semester=f"{2020 + year - 1}-{2020 + year} {'Güz' if random.random() < 0.5 else 'Bahar'}"
                        )
                        db.session.add(completed)


def create_admin():
    """Admin kullanıcı oluştur"""
    admin = Student(
        student_number='admin',
        email='admin@ogrenci.edu.tr',
        first_name='Sistem',
        last_name='Yöneticisi',
        department='Bilgi İşlem',
        faculty='Rektörlük',
        class_level=4,
        gpa=4.0,
        remaining_courses=0,
        is_admin=True,
        is_active=True
    )
    admin.set_password('admin123')
    db.session.add(admin)


if __name__ == '__main__':
    create_sample_data()
