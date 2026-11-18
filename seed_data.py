import os
import sys
from datetime import datetime, date, time

from app import app
from models.models import (
    db, User, Admin, Department, Examiner, Student,
    Course, Examination, Rubric, ExaminationSlot,
    Booking, Evaluation, EvaluationScore
)

def seed():
    with app.app_context():
        print("Starting seed...")

        # -------------------------------------------------------------
        # 1. Departments
        # -------------------------------------------------------------
        dept_cse = Department.query.filter_by(name="Computer Science & Engineering").first()
        if not dept_cse:
            dept_cse = Department(name="Computer Science & Engineering")
            db.session.add(dept_cse)

        dept_ds = Department.query.filter_by(name="Data Science & Applications").first()
        if not dept_ds:
            dept_ds = Department(name="Data Science & Applications")
            db.session.add(dept_ds)

        dept_math = Department.query.filter_by(name="Mathematics & Statistics").first()
        if not dept_math:
            dept_math = Department(name="Mathematics & Statistics")
            db.session.add(dept_math)

        db.session.flush()

        # -------------------------------------------------------------
        # 2. Courses
        # -------------------------------------------------------------
        c_mad = Course.query.filter_by(code="CS101").first()
        if not c_mad:
            c_mad = Course(code="CS101", name="Modern Application Development I", description="Web dev with Flask, Jinja2, SQLite")
            db.session.add(c_mad)

        c_tds = Course.query.filter_by(code="DS201").first()
        if not c_tds:
            c_tds = Course(code="DS201", name="Tools in Data Science", description="Data processing, analysis, and scripting")
            db.session.add(c_tds)

        c_la = Course.query.filter_by(code="MA102").first()
        if not c_la:
            c_la = Course(code="MA102", name="Linear Algebra & Numerical Methods", description="Vectors, matrices, eigenvalues")
            db.session.add(c_la)

        db.session.flush()

        # -------------------------------------------------------------
        # 3. Users & Examiners
        # -------------------------------------------------------------
        # Examiner 1: Dr. Arvind Kumar (approved)
        u_ex1 = User.query.filter_by(email="examiner@emp.com").first()
        if not u_ex1:
            u_ex1 = User(email="examiner@emp.com", role="examiner", is_active=True)
            u_ex1.set_password("examiner123")
            db.session.add(u_ex1)
            db.session.flush()

        ex1 = Examiner.query.filter_by(user_id=u_ex1.id).first()
        if not ex1:
            ex1 = Examiner(
                user_id=u_ex1.id,
                employee_id="FAC101",
                name="Dr. Arvind Kumar",
                phone="9876543210",
                department_id=dept_cse.id,
                status="approved"
            )
            db.session.add(ex1)

        # Examiner 2: Dr. Priya Sharma (approved)
        u_ex2 = User.query.filter_by(email="priya@emp.com").first()
        if not u_ex2:
            u_ex2 = User(email="priya@emp.com", role="examiner", is_active=True)
            u_ex2.set_password("examiner123")
            db.session.add(u_ex2)
            db.session.flush()

        ex2 = Examiner.query.filter_by(user_id=u_ex2.id).first()
        if not ex2:
            ex2 = Examiner(
                user_id=u_ex2.id,
                employee_id="FAC102",
                name="Dr. Priya Sharma",
                phone="9876543211",
                department_id=dept_ds.id,
                status="approved"
            )
            db.session.add(ex2)

        # Examiner 3: Prof. Rajesh Verma (pending - demo approval workflow)
        u_ex3 = User.query.filter_by(email="rajesh@emp.com").first()
        if not u_ex3:
            u_ex3 = User(email="rajesh@emp.com", role="examiner", is_active=True)
            u_ex3.set_password("examiner123")
            db.session.add(u_ex3)
            db.session.flush()

        ex3 = Examiner.query.filter_by(user_id=u_ex3.id).first()
        if not ex3:
            ex3 = Examiner(
                user_id=u_ex3.id,
                employee_id="FAC103",
                name="Prof. Rajesh Verma",
                phone="9876543212",
                department_id=dept_math.id,
                status="pending"
            )
            db.session.add(ex3)

        # -------------------------------------------------------------
        # 4. Users & Students
        # -------------------------------------------------------------
        # Student 1: Primary student (Rahul Mehta)
        u_st1 = User.query.filter_by(email="student@emp.com").first()
        if not u_st1:
            u_st1 = User(email="student@emp.com", role="student", is_active=True)
            u_st1.set_password("student123")
            db.session.add(u_st1)
            db.session.flush()

        st1 = Student.query.filter_by(user_id=u_st1.id).first()
        if not st1:
            st1 = Student(
                user_id=u_st1.id,
                roll_no="25f3004638",
                name="Rahul Mehta",
                phone="9123456780",
                course_id=c_mad.id,
                year="Year 2",
                status="active"
            )
            db.session.add(st1)

        # Student 2: Sneha Patel
        u_st2 = User.query.filter_by(email="sneha@emp.com").first()
        if not u_st2:
            u_st2 = User(email="sneha@emp.com", role="student", is_active=True)
            u_st2.set_password("student123")
            db.session.add(u_st2)
            db.session.flush()

        st2 = Student.query.filter_by(user_id=u_st2.id).first()
        if not st2:
            st2 = Student(
                user_id=u_st2.id,
                roll_no="25f3001024",
                name="Sneha Patel",
                phone="9123456781",
                course_id=c_mad.id,
                year="Year 2",
                status="active"
            )
            db.session.add(st2)

        # Student 3: Amit Sharma
        u_st3 = User.query.filter_by(email="amit@emp.com").first()
        if not u_st3:
            u_st3 = User(email="amit@emp.com", role="student", is_active=True)
            u_st3.set_password("student123")
            db.session.add(u_st3)
            db.session.flush()

        st3 = Student.query.filter_by(user_id=u_st3.id).first()
        if not st3:
            st3 = Student(
                user_id=u_st3.id,
                roll_no="25f3002048",
                name="Amit Sharma",
                phone="9123456782",
                course_id=c_tds.id,
                year="Year 1",
                status="active"
            )
            db.session.add(st3)

        db.session.flush()

        # -------------------------------------------------------------
        # 5. Examinations & Rubrics
        # -------------------------------------------------------------
        exam_mad = Examination.query.filter_by(name="MAD-I Term Project Viva").first()
        if not exam_mad:
            exam_mad = Examination(
                course_id=c_mad.id,
                name="MAD-I Term Project Viva",
                exam_type="Viva",
                duration=30,
                max_marks=100,
                status="booking_open",
                slot_creation_start=datetime(2026, 11, 15, 9, 0),
                slot_creation_end=datetime(2026, 11, 18, 18, 0),
                slot_booking_start=datetime(2026, 11, 18, 9, 0),
                slot_booking_end=datetime(2026, 11, 25, 23, 59),
            )
            db.session.add(exam_mad)
            db.session.flush()

            # Rubrics for MAD-I
            rubrics_data = [
                ("Architecture & Blueprint Modularity", 30, 30.0, "Evaluation of MVC/Blueprint separation, models, and clean codebase."),
                ("Feature Completeness & Functionality", 40, 40.0, "All 3 roles work end-to-end, validation rules, capacity handling."),
                ("Viva Defense & Q&A Response", 30, 30.0, "Ability to explain design patterns, db flush, and security flow.")
            ]
            for c_name, max_m, weight, desc in rubrics_data:
                r = Rubric(
                    exam_id=exam_mad.id,
                    criterion_name=c_name,
                    max_marks=max_m,
                    weightage=weight,
                    description=desc
                )
                db.session.add(r)

        exam_tds = Examination.query.filter_by(name="Tools in Data Science Practical").first()
        if not exam_tds:
            exam_tds = Examination(
                course_id=c_tds.id,
                name="Tools in Data Science Practical",
                exam_type="Practical",
                duration=45,
                max_marks=50,
                status="slot_creation",
                slot_creation_start=datetime(2026, 11, 18, 9, 0),
                slot_creation_end=datetime(2026, 11, 22, 18, 0),
                slot_booking_start=datetime(2026, 11, 22, 18, 0),
                slot_booking_end=datetime(2026, 11, 28, 23, 59),
            )
            db.session.add(exam_tds)
            db.session.flush()

            r_tds = Rubric(
                exam_id=exam_tds.id,
                criterion_name="Code Execution & Outputs",
                max_marks=50,
                weightage=100.0,
                description="Practical test on numpy, pandas, and bash scripting."
            )
            db.session.add(r_tds)

        db.session.flush()

        # -------------------------------------------------------------
        # 6. Examination Slots
        # -------------------------------------------------------------
        # Slot 1: MAD-I with Dr. Arvind Kumar
        slot1 = ExaminationSlot.query.filter_by(exam_id=exam_mad.id, examiner_id=ex1.id).first()
        if not slot1:
            slot1 = ExaminationSlot(
                exam_id=exam_mad.id,
                examiner_id=ex1.id,
                date=date(2026, 11, 20),
                start_time=time(10, 0),
                end_time=time(10, 30),
                max_capacity=3,
                available_seats=1,  # 2 will be booked below
                status="available"
            )
            db.session.add(slot1)

        # Slot 2: MAD-I with Dr. Priya Sharma
        slot2 = ExaminationSlot.query.filter_by(exam_id=exam_mad.id, examiner_id=ex2.id).first()
        if not slot2:
            slot2 = ExaminationSlot(
                exam_id=exam_mad.id,
                examiner_id=ex2.id,
                date=date(2026, 11, 21),
                start_time=time(14, 0),
                end_time=time(14, 30),
                max_capacity=2,
                available_seats=2,
                status="available"
            )
            db.session.add(slot2)

        # Slot 3: TDS with Dr. Arvind Kumar
        slot3 = ExaminationSlot.query.filter_by(exam_id=exam_tds.id, examiner_id=ex1.id).first()
        if not slot3:
            slot3 = ExaminationSlot(
                exam_id=exam_tds.id,
                examiner_id=ex1.id,
                date=date(2026, 11, 22),
                start_time=time(11, 0),
                end_time=time(11, 45),
                max_capacity=4,
                available_seats=4,
                status="available"
            )
            db.session.add(slot3)

        db.session.flush()

        # -------------------------------------------------------------
        # 7. Bookings & Evaluations
        # -------------------------------------------------------------
        # Booking 1: Rahul Mehta on Slot 1
        b1 = Booking.query.filter_by(student_id=st1.id, slot_id=slot1.id).first()
        if not b1:
            b1 = Booking(
                student_id=st1.id,
                slot_id=slot1.id,
                status="booked",
                booking_date=datetime(2026, 11, 18, 10, 15)
            )
            db.session.add(b1)
            db.session.flush()

            # Evaluation for Rahul (PUBLISHED: so student can view results!)
            ev1 = Evaluation(
                booking_id=b1.id,
                examiner_id=ex1.id,
                total_marks=88.0,
                remarks="Superb modular structure, well-defined blueprints, and strong viva answers.",
                status="published",
                submitted_at=datetime(2026, 11, 18, 11, 30)
            )
            db.session.add(ev1)
            db.session.flush()

            rubrics = Rubric.query.filter_by(exam_id=exam_mad.id).all()
            scores1 = [27.0, 36.0, 25.0]
            for r, score_val in zip(rubrics, scores1):
                es = EvaluationScore(evaluation_id=ev1.id, rubric_id=r.id, marks=score_val)
                db.session.add(es)

        # Booking 2: Sneha Patel on Slot 1
        b2 = Booking.query.filter_by(student_id=st2.id, slot_id=slot1.id).first()
        if not b2:
            b2 = Booking(
                student_id=st2.id,
                slot_id=slot1.id,
                status="booked",
                booking_date=datetime(2026, 11, 18, 11, 0)
            )
            db.session.add(b2)
            db.session.flush()

            # Evaluation for Sneha (SUBMITTED: ready for Admin to click "Publish" during demo!)
            ev2 = Evaluation(
                booking_id=b2.id,
                examiner_id=ex1.id,
                total_marks=78.5,
                remarks="Solid implementation. Check edge cases on cancellation capacity.",
                status="submitted",
                submitted_at=datetime(2026, 11, 18, 12, 0)
            )
            db.session.add(ev2)
            db.session.flush()

            rubrics = Rubric.query.filter_by(exam_id=exam_mad.id).all()
            scores2 = [24.0, 31.5, 23.0]
            for r, score_val in zip(rubrics, scores2):
                es = EvaluationScore(evaluation_id=ev2.id, rubric_id=r.id, marks=score_val)
                db.session.add(es)

        db.session.commit()
        print("✅ Database successfully seeded with realistic sample data!")

if __name__ == "__main__":
    seed()
