import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Student, Teacher, Attendance
from helpers import decode_base64_image, get_face_encoding_from_pil, serialize_encoding, deserialize_encoding, compare_encodings
from datetime import date


from flask import Flask
from models import db, Teacher
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key'

db.init_app(app)

# Create tables and add default teacher
with app.app_context():
    db.create_all()
    if not Teacher.query.first():
        teacher = Teacher(
            email='teacher@example.com',
            name='Admin Teacher',
            password_hash=generate_password_hash('password')
        )
        db.session.add(teacher)
        db.session.commit()
    print("✅ Database initialized with default teacher")




BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'attendance.db')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-change-me'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.before_first_request
def create_db():
    db.create_all()
    if not Teacher.query.first():
        t = Teacher(email='teacher@example.com', name='Default Teacher', password_hash=generate_password_hash('password'))
        db.session.add(t)
        db.session.commit()

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']

        if role == 'teacher':
            t = Teacher.query.filter_by(email=username).first()
            if t and check_password_hash(t.password_hash, password):
                session['teacher'] = t.id
                return redirect(url_for('teacher_dashboard'))
        else:
            s = Student.query.filter_by(student_id=username).first()
            if s:
                session['student'] = s.id
                return redirect(url_for('student_dashboard', student_id=s.student_id))
        return "Invalid credentials", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ----------- Teacher Routes ------------

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'teacher' not in session:
        return redirect(url_for('login'))
    students = Student.query.all()
    return render_template('teacher.html', students=students)

@app.route('/teacher/add_student', methods=['GET', 'POST'])
def add_student():
    if 'teacher' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        student_id = request.form['student_id']
        photo = request.files['photo']
        photo_path = os.path.join(BASE_DIR, 'static/known_faces', photo.filename)
        photo.save(photo_path)

        pil = decode_base64_image("data:image/jpeg;base64," + base64.b64encode(photo.read()).decode())
        enc = get_face_encoding_from_pil(pil)

        s = Student(name=name, student_id=student_id, photo_path=photo_path)
        if enc:
            s.face_encoding = serialize_encoding(enc)
        db.session.add(s)
        db.session.commit()
        return redirect(url_for('teacher_dashboard'))
    return render_template('add_student.html')

@app.route('/teacher/mark_present', methods=['POST'])
def mark_present():
    if 'teacher' not in session:
        return redirect(url_for('login'))
    student_id = request.form['student_id']
    s = Student.query.get(student_id)
    if s:
        today = date.today()
        att = Attendance.query.filter_by(student_id=s.id, date=today).first()
        if not att:
            att = Attendance(student_id=s.id)
            db.session.add(att)
            db.session.commit()
    return redirect(url_for('teacher_dashboard'))

# ----------- Student Routes ------------

@app.route('/student/<student_id>')
def student_dashboard(student_id):
    s = Student.query.filter_by(student_id=student_id).first_or_404()
    return render_template('student.html', student=s)

# ----------- API for Face Attendance ------------

@app.route('/api/face_login', methods=['POST'])
def api_face_login():
    data = request.json
    img_data = data.get('image')
    if not img_data:
        return jsonify({'success': False, 'msg': 'No image provided'}), 400

    pil = decode_base64_image(img_data)
    enc = get_face_encoding_from_pil(pil)
    if enc is None:
        return jsonify({'success': False, 'msg': 'Face not detected'}), 400

    for s in Student.query.all():
        if s.face_encoding:
            stored = deserialize_encoding(s.face_encoding)
            if compare_encodings(enc, stored):
                today = date.today()
                att = Attendance.query.filter_by(student_id=s.id, date=today).first()
                if not att:
                    att = Attendance(student_id=s.id)
                    db.session.add(att)
                    db.session.commit()
                return jsonify({'success': True, 'student_id': s.student_id, 'name': s.name})
    return jsonify({'success': False, 'msg': 'No match found'}), 404

# ----------- API: Attendance Summary ------------

@app.route('/api/attendance_summary/<student_id>')
def attendance_summary(student_id):
    s = Student.query.filter_by(student_id=student_id).first_or_404()
    records = Attendance.query.filter_by(student_id=s.id).all()
    present_count = sum(1 for r in records if r.status=="Present")
    absent_count = len(records) - present_count
    labels = ["Present", "Absent"]
    values = [present_count, absent_count]
    return jsonify({'labels': labels, 'values': values, 'present': present_count, 'absent': absent_count})

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
