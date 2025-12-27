"""
Uygulama Konfigürasyon Dosyası
"""
import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'obs-proje-gizli-anahtar-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///obs.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Kayıt sistemi ayarları
    MAX_COURSES_PER_STUDENT = 8  # Bir öğrencinin alabileceği maksimum ders
    MIN_COURSES_PER_STUDENT = 3  # Minimum ders sayısı
    WAITLIST_ENABLED = True      # Bekleme listesi aktif mi
    WAITLIST_MAX_SIZE = 10       # Bekleme listesi maksimum boyutu
    
    # Öncelik ağırlıkları
    PRIORITY_WEIGHTS = {
        'class_level': 30,        # Sınıf seviyesi (4. sınıf en yüksek)
        'remaining_courses': 25,  # Mezuniyete kalan ders sayısı
        'gpa': 20,                # Not ortalaması
        'special_status': 25      # Özel durum (çift anadal, burs vb.)
    }
    
    # Özel durum bonus puanları
    SPECIAL_STATUS_BONUS = {
        'none': 0,
        'scholarship': 10,        # Burslu
        'double_major': 15,       # Çift anadal
        'honor_student': 12,      # Onur öğrencisi
        'exchange': 8             # Değişim öğrencisi
    }


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
