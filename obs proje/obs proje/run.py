"""
Uygulama başlatma dosyası
"""
from app import create_app, db
from app.models import Student, Course, Enrollment, Schedule

app = create_app('development')

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Student': Student,
        'Course': Course,
        'Enrollment': Enrollment,
        'Schedule': Schedule
    }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
