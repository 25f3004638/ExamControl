from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime

from models.models import db, Student, Examination, ExaminationSlot, Booking, Evaluation, EvaluationScore, User

student_bp = Blueprint('student', __name__)


def get_student_or_abort():
    return Student.query.filter_by(user_id=current_user.id).first()


def booking_period_open():
    # True if at least one exam has status booking_open
    return Examination.query.filter_by(status='booking_open').count() > 0


# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------

@student_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    student = get_student_or_abort()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    # Exams open for booking with available slots
    open_exams = Examination.query.filter_by(status='booking_open').all()

    # Student's existing bookings — to avoid showing already-booked exams
    booked_exam_ids = set()
    for b in student.bookings:
        if b.status == 'booked':
            booked_exam_ids.add(b.slot.exam_id)

    examinations = []
    for exam in open_exams:
        if exam.id in booked_exam_ids:
            continue
        avail_slots = [s for s in exam.slots if s.available_seats > 0 and s.status == 'available']
        examinations.append({
            'id': exam.id,
            'name': exam.name,
            'course_name': exam.course.name if exam.course else '—',
            'type': exam.exam_type,
            'max_marks': exam.max_marks,
            'status': exam.status.replace('_', ' ').capitalize(),
            'slots': [{'id': s.id, 'date': s.date, 'start_time': s.start_time} for s in avail_slots],
        })

    upcoming = sum(1 for b in student.bookings if b.status == 'booked')
    results_count = sum(1 for b in student.bookings if b.evaluation and b.evaluation.status == 'published')
    past = sum(1 for b in student.bookings if b.status == 'completed')

    stats = {
        'examinations': len(open_exams),
        'slots': sum(len(e['slots']) for e in examinations),
        'upcoming': upcoming,
        'booked': upcoming,
        'results': results_count,
        'past': past,
    }

    return render_template('student/dashboard.html',
        stats=stats,
        examinations=examinations,
        student_id=student.id,
    )


# ------------------------------------------------------------------
# Available Examinations (full page)
# ------------------------------------------------------------------

@student_bp.route('/examinations')
@login_required
def examinations():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    student = get_student_or_abort()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    booked_exam_ids = set()
    for b in student.bookings:
        if b.status == 'booked':
            booked_exam_ids.add(b.slot.exam_id)

    open_exams = Examination.query.filter_by(status='booking_open').all()

    examinations = []
    for exam in open_exams:
        avail_slots = [s for s in exam.slots if s.available_seats > 0 and s.status == 'available']
        already_booked = exam.id in booked_exam_ids
        examinations.append({
            'id': exam.id,
            'name': exam.name,
            'course_name': exam.course.name if exam.course else '—',
            'type': exam.exam_type,
            'max_marks': exam.max_marks,
            'status': exam.status.replace('_', ' ').capitalize(),
            'slots': [] if already_booked else [{'id': s.id, 'date': s.date, 'start_time': s.start_time} for s in avail_slots],
        })

    return render_template('student/examinations.html',
        examinations=examinations,
        student_id=student.id,
    )


# ------------------------------------------------------------------
# Book a Slot (POST)
# ------------------------------------------------------------------

@student_bp.route('/book/<int:slot_id>', methods=['POST'])
@login_required
def book(slot_id):
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    student = get_student_or_abort()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    slot = ExaminationSlot.query.get_or_404(slot_id)
    exam = slot.exam

    if exam.status != 'booking_open':
        flash('Booking is not currently open for this examination.', 'warning')
        return redirect(url_for('student.examinations'))

    if slot.status != 'available' or slot.available_seats <= 0:
        flash('This slot is full or unavailable.', 'warning')
        return redirect(url_for('student.examinations'))

    # Check duplicate booking for this exam
    for b in student.bookings:
        if b.status == 'booked' and b.slot.exam_id == exam.id:
            flash('You already have a booking for this examination.', 'warning')
            return redirect(url_for('student.examinations'))

    new_booking = Booking(
        student_id=student.id,
        slot_id=slot.id,
        status='booked',
        booking_date=datetime.utcnow(),
    )
    db.session.add(new_booking)

    slot.available_seats -= 1
    if slot.available_seats <= 0:
        slot.status = 'full'

    db.session.commit()
    flash('Slot booked successfully!', 'success')
    return redirect(url_for('student.bookings'))


# ------------------------------------------------------------------
# My Slots
# ------------------------------------------------------------------

@student_bp.route('/slots')
@login_required
def slots():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    student = get_student_or_abort()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    my_slots = []
    for b in student.bookings:
        s = b.slot
        my_slots.append({
            'id': s.id,
            'exam_name': s.exam.name,
            'date': s.date,
            'start_time': s.start_time,
            'end_time': s.end_time,
            'status': s.status.capitalize(),
            'booking_status': b.status.capitalize(),
        })

    return render_template('student/slots.html', my_slots=my_slots)


# ------------------------------------------------------------------
# Booking History
# ------------------------------------------------------------------

@student_bp.route('/bookings')
@login_required
def bookings():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    student = get_student_or_abort()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    bookings_list = []
    for b in student.bookings:
        s = b.slot
        has_result = b.evaluation and b.evaluation.status == 'published'
        bookings_list.append({
            'id': b.id,
            'exam_id': s.exam_id,
            'exam_name': s.exam.name,
            'slot_date': s.date,
            'status': b.status.capitalize(),
            'results': has_result,
        })

    is_open = booking_period_open()

    return render_template('student/bookings.html',
        bookings=bookings_list,
        student_id=student.id,
        booking_open=is_open,
    )


# ------------------------------------------------------------------
# Cancel Booking (POST)
# ------------------------------------------------------------------

@student_bp.route('/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel(booking_id):
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    student = get_student_or_abort()
    booking = Booking.query.get_or_404(booking_id)

    if booking.student_id != student.id:
        flash('Not your booking.', 'danger')
        return redirect(url_for('student.bookings'))

    if booking.status != 'booked':
        flash('Only active bookings can be cancelled.', 'warning')
        return redirect(url_for('student.bookings'))

    if booking.slot.exam.status != 'booking_open':
        flash('Cancellation is only allowed while booking is open.', 'warning')
        return redirect(url_for('student.bookings'))

    booking.status = 'cancelled'

    slot = booking.slot
    slot.available_seats += 1
    if slot.status == 'full':
        slot.status = 'available'

    db.session.commit()
    flash('Booking cancelled.', 'info')
    return redirect(url_for('student.bookings'))


# ------------------------------------------------------------------
# Published Results
# ------------------------------------------------------------------

@student_bp.route('/results')
@login_required
def results():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    student = get_student_or_abort()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    results_data = []
    for b in student.bookings:
        ev = b.evaluation
        if not ev or ev.status != 'published':
            continue

        rubric_breakdown = []
        for score in ev.scores:
            rubric_breakdown.append((score.rubric.criterion_name, score.marks))

        results_data.append({
            'exam_name': b.slot.exam.name,
            'total_marks': ev.total_marks,
            'rubric_breakdown': rubric_breakdown,
            'remarks': ev.remarks,
        })

    return render_template('student/results.html', results=results_data)


# ------------------------------------------------------------------
# Single booking result detail
# ------------------------------------------------------------------

@student_bp.route('/result/<int:booking_id>')
@login_required
def result(booking_id):
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    student = get_student_or_abort()
    booking = Booking.query.get_or_404(booking_id)

    if booking.student_id != student.id:
        flash('Not your booking.', 'danger')
        return redirect(url_for('student.results'))

    ev = booking.evaluation
    if not ev or ev.status != 'published':
        flash('Result is not published yet.', 'info')
        return redirect(url_for('student.bookings'))

    rubric_breakdown = [(s.rubric.criterion_name, s.marks) for s in ev.scores]

    r = {
        'exam_name': booking.slot.exam.name,
        'total_marks': ev.total_marks,
        'rubric_breakdown': rubric_breakdown,
        'remarks': ev.remarks,
    }
    return render_template('student/results.html', results=[r])


# ------------------------------------------------------------------
# Profile (GET / POST)
# ------------------------------------------------------------------

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    student = get_student_or_abort()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        student.name = name or student.name
        student.phone = phone

        user = User.query.get(student.user_id)
        if email and email != user.email:
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != user.id:
                flash('Email already in use.', 'danger')
                return redirect(url_for('student.profile'))
            user.email = email

        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('student.profile'))

    user = User.query.get(student.user_id)
    edit = {
        'name': student.name,
        'email': user.email,
        'phone': student.phone or '',
        'student_id': student.roll_no,
        'status': student.status.capitalize() if student.status else 'Active',
    }

    return render_template('student/profile.html',
        edit=edit,
        student_id=student.id,
    )
