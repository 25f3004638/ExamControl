from datetime import datetime 

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash



db = SQLAlchemy()
 

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email   = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)   # admin | examiner | student
    is_active = db.Column(db.Boolean, default=True)

    created_at= db.Column(db.DateTime, default=datetime.utcnow)

    examiner=db.relationship("Examiner", backref="user", uselist=False)
    student  = db.relationship("Student", backref="user", uselist=False)
    admin  =db.relationship("Admin", backref="user", uselist=False)

    def set_password(self, pwd: str):

        self.password_hash=generate_password_hash(pwd)



    def check_password(self, pwd: str) -> bool:

        return check_password_hash(self.password_hash, pwd)




class Admin(db.Model):
    __tablename__ = "admins"
    id  = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer , db.ForeignKey("users.id"), unique=True, nullable=False)

    name= db.Column(db.String(120), nullable=False)



class Department(db.Model):
    __tablename__ = "departments"


    id  = db.Column(db.Integer, primary_key=True)
    name   = db.Column(db.String(120), unique=True, nullable=False)

    code= db.Column(db.String(20), unique=True)


    examiners = db.relationship("Examiner", backref="department")



class Examiner(db.Model):

    __tablename__ = "examiners"

    id  = db.Column(db.Integer, primary_key=True)

    user_id      =db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    employee_id   = db.Column(db.String(50), unique=True, nullable=False)


    name   = db.Column(db.String(120), nullable=False)

    phone  = db.Column(db.String(30))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    status= db.Column(db.String(20), default="pending")  # pending|approved|rejected|inactive
    slots = db.relationship("ExaminationSlot", backref="examiner")

    evaluations = db.relationship("Evaluation", backref="examiner")






class Student(db.Model):
    __tablename__ = "students"

    id= db.Column(db.Integer, primary_key=True)
    user_id =db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    name= db.Column(db.String(120), nullable=False)

    phone=db.Column(db.String(30))
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"))
    year  =  db.Column(db.String(20))
    status =  db.Column(db.String(20), default="active")       # active|inactive

    course= db.relationship("Course", backref="students")
    bookings=db.relationship("Booking", backref="student")


class Course(db.Model):

    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(db.String(30), unique=True, nullable=False)

    name    = db.Column(db.String(150), nullable=False)
    description  = db.Column(db.Text)
    status=   db.Column(db.String(20), default="active")    # active|inactive

    examinations = db.relationship("Examination", backref="course")


class Examination(db.Model):
    __tablename__ = "examinations"

    id   = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)

    name     = db.Column(db.String(150), nullable=False)
    exam_type= db.Column(db.String(30), nullable=False)   # Viva|Practical|Project Demo|Assessment

    duration = db.Column(db.Integer, nullable=False)       # in minutes ig?
    max_marks = db.Column(db.Integer, nullable=False)

    slot_creation_start = db.Column(db.DateTime)
    slot_creation_end=db.Column(db.DateTime)
    slot_booking_start  = db.Column(db.DateTime)

    slot_booking_end  = db.Column(db.DateTime)
    status = db.Column(db.String(20), default="draft")  # draft|slot_creation|booking_open|closed|completed perhaps
    rubrics = db.relationship("Rubric", backref="exam")
    slots  = db.relationship("ExaminationSlot", backref="exam")


class Rubric(db.Model):
    __tablename__ = "rubrics"

    id  = db.Column(db.Integer, primary_key=True)
    exam_id= db.Column(db.Integer, db.ForeignKey("examinations.id"), nullable=False)
    criterion_name = db.Column(db.String(120), nullable=False)

    max_marks= db.Column(db.Integer, nullable=False)

    weightage   =db.Column(db.Float, nullable=False)             # percentage
    description    = db.Column(db.Text)

    scores  = db.relationship("EvaluationScore", backref="rubric")


class ExaminationSlot(db.Model):
    __tablename__ = "examination_slots"
    id  = db.Column(db.Integer, primary_key=True)
    exam_id  = db.Column(db.Integer, db.ForeignKey("examinations.id"), nullable=False)

    examiner_id=db.Column(db.Integer, db.ForeignKey("examiners.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)

    start_time= db.Column(db.Time, nullable=False)
    end_time       = db.Column(db.Time, nullable=False)
    max_capacity   = db.Column(db.Integer, nullable=False)

    available_seats = db.Column(db.Integer, nullable=False)

    status         = db.Column(db.String(20), default="available")  # available|full|cancelled|completed
    
    bookings  = db.relationship("Booking", backref="slot")


class Booking(db.Model):
    __tablename__ = "bookings"
    
    id    = db.Column(db.Integer, primary_key=True)
    student_id  = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    slot_id  = db.Column(db.Integer, db.ForeignKey("examination_slots.id"), nullable=False)
    
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)

    status  =db.Column(db.String(20), default="booked")       # booked|cancelled|completed
    evaluation   =db.relationship("Evaluation", backref="booking", uselist=False)

    __table_args__= (db.UniqueConstraint("student_id", "slot_id", name="uq_student_slot"),)


class Evaluation(db.Model):

    __tablename__ = "evaluations"


    id      = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), unique=True, nullable=False)

    examiner_id  =db.Column(db.Integer, db.ForeignKey("examiners.id"), nullable=False)
    total_marks = db.Column(db.Float)

    remarks  =db.Column(db.Text)
    status= db.Column(db.String(20), default="draft")        # draft|submitted|published


    submitted_at = db.Column(db.DateTime)
    scores       = db.relationship("EvaluationScore", backref="evaluation",
                                   cascade="all, delete-orphan")





class EvaluationScore(db.Model):

    __tablename__ = "evaluation_scores"

    id  = db.Column(db.Integer, primary_key=True)
    evaluation_id =db.Column(db.Integer,  db.ForeignKey("evaluations.id"), nullable=False )
    rubric_id  = db.Column(db.Integer, db.ForeignKey("rubrics.id"), nullable=False)

    marks= db.Column(db.Float, nullable=False)


class Setting(db.Model):
    __tablename__ = "settings"
    key   = db.Column(db.String(60), primary_key=True)

    value = db.Column(db.String(255))     



