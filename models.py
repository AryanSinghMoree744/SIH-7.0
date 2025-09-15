from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(64), unique=True, nullable=False)  # roll number
    name = db.Column(db.String(128), nullable=False)
    student_class = db.Column(db.String(64))
    photo_path = db.Column(db.String(256))  # store image path
    face_encoding = db.Column(db.LargeBinary)  # store face encoding as pickle

class Teacher(db.Model):
    __tablename__ = "teachers"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    name = db.Column(db.String(128))
    password_hash = db.Column(db.String(256))

class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(16), nullable=False)  # Present/Absent/Late
    marked_by = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    method = db.Column(db.String(32), default="Face")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
