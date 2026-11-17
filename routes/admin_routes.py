from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from models.models import (
    db, Examiner, Student, Course, Department,
    Examination, Rubric, ExaminationSlot, Booking, Evaluation
)

admin_bp = Blueprint('admin', __name__)


def admin_only():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return False
    return True


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not admin_only():
        return redirect(url_for('auth.login'))

    stats = {
        'courses': Course.query.count(),
        'examinations': Examination.query.count(),
        'examiners': Examiner.query.count(),
        'students': Student.query.count(),
        'slots': ExaminationSlot.query.count(),
        'bookings': Booking.query.count(),
    }

    slot_creation_open = Examination.query.filter_by(status='slot_creation').first() is not None
    booking_open = Examination.query.filter_by(status='booking_open').first() is not None

    return render_template('admin/dashboard.html',
                           stats=stats,
                           slot_creation_open=slot_creation_open,
                           booking_open=booking_open)


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------

@admin_bp.route('/courses', methods=['GET', 'POST'])
@login_required
def courses():
    if not admin_only():
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        action = request.form.get('action')
        code = request.form.get('code', '').strip()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'Active').strip()

        if action == 'edit':
            c = Course.query.get(request.form.get('course_id'))
            if c:
                c.code, c.name, c.description, c.status = code, name, description, status
                db.session.commit()
                flash('Course updated.', 'success')
        else:
            if Course.query.filter_by(code=code).first():
                flash('Course code already exists.', 'danger')
            else:
                db.session.add(Course(code=code, name=name, description=description, status=status))
                db.session.commit()
                flash('Course created.', 'success')

        return redirect(url_for('admin.courses'))

    q = request.args.get('q', '').strip()
    course_query = Course.query
    if q:
        course_query = course_query.filter((Course.name.ilike(f'%{q}%')) | (Course.code.ilike(f'%{q}%')))

    return render_template('admin/courses.html', courses=course_query.all(), edit=None, q=q)


@admin_bp.route('/courses/edit/<int:course_id>')
@login_required
def course_edit(course_id):
    if not admin_only():
        return redirect(url_for('auth.login'))

    return render_template('admin/courses.html',
                           courses=Course.query.all(),
                           edit=Course.query.get_or_404(course_id),
                           q='')


@admin_bp.route('/courses/delete/<int:course_id>', methods=['POST'])
@login_required
def course_delete(course_id):
    if not admin_only():
        return redirect(url_for('auth.login'))

    c = Course.query.get(course_id)
    if c:
        db.session.delete(c)
        db.session.commit()
        flash('Course deleted.', 'success')

    return redirect(url_for('admin.courses'))


# ---------------------------------------------------------------------------
# Examinations
# ---------------------------------------------------------------------------

def _parse_dt(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%dT%H:%M')
    except Exception:
        return None


def _exam_view_data(exams):
    return [{
        'id': e.id,
        'course_name': e.course.name if e.course else 'N/A',
        'name': e.name,
        'type': e.exam_type,
        'max_marks': e.max_marks,
        'status': e.status
    } for e in exams]


@admin_bp.route('/examinations', methods=['GET', 'POST'])
@login_required
def examinations():
    if not admin_only():
        return redirect(url_for('auth.login'))

    courses_options = [{'value': c.id, 'label': f"{c.code} - {c.name}"} for c in Course.query.all()]

    if request.method == 'POST':
        action = request.form.get('action')
        data = {
            'course_id': int(request.form.get('course_id')),
            'name': request.form.get('name', '').strip(),
            'exam_type': request.form.get('type', '').strip(),
            'duration': int(request.form.get('duration', 0)),
            'max_marks': int(request.form.get('max_marks', 0)),
            'status': request.form.get('status', 'Draft').strip(),
            'slot_creation_start': _parse_dt(request.form.get('slot_start')),
            'slot_creation_end': _parse_dt(request.form.get('slot_end')),
            'slot_booking_start': _parse_dt(request.form.get('booking_start')),
            'slot_booking_end': _parse_dt(request.form.get('booking_end'))
        }

        if action == 'edit':
            e = Examination.query.get(request.form.get('exam_id'))
            if e:
                for k, v in data.items():
                    setattr(e, k, v)
                db.session.commit()
                flash('Examination updated.', 'success')
        else:
            db.session.add(Examination(**data))
            db.session.commit()
            flash('Examination created.', 'success')

        return redirect(url_for('admin.examinations'))

    q = request.args.get('q', '').strip()
    exams = Examination.query.filter(Examination.name.ilike(f'%{q}%')).all() if q else Examination.query.all()

    return render_template('admin/examinations.html',
                           examinations=_exam_view_data(exams),
                           courses_options=courses_options,
                           edit=None,
                           q=q)


@admin_bp.route('/examinations/edit/<int:exam_id>')
@login_required
def exam_edit(exam_id):
    if not admin_only():
        return redirect(url_for('auth.login'))

    e = Examination.query.get_or_404(exam_id)
    courses_options = [{'value': c.id, 'label': f"{c.code} - {c.name}"} for c in Course.query.all()]

    edit_data = {
        'id': e.id,
        'course_id': e.course_id,
        'name': e.name,
        'type': e.exam_type,
        'duration': e.duration,
        'max_marks': e.max_marks,
        'status': e.status,
        'slot_start': e.slot_creation_start.strftime('%Y-%m-%dT%H:%M') if e.slot_creation_start else '',
        'slot_end': e.slot_creation_end.strftime('%Y-%m-%dT%H:%M') if e.slot_creation_end else '',
        'booking_start': e.slot_booking_start.strftime('%Y-%m-%dT%H:%M') if e.slot_booking_start else '',
        'booking_end': e.slot_booking_end.strftime('%Y-%m-%dT%H:%M') if e.slot_booking_end else ''
    }

    return render_template('admin/examinations.html',
                           examinations=_exam_view_data(Examination.query.all()),
                           courses_options=courses_options,
                           edit=edit_data,
                           q='')


@admin_bp.route('/examinations/delete/<int:exam_id>', methods=['POST'])
@login_required
def exam_delete(exam_id):
    if not admin_only():
        return redirect(url_for('auth.login'))

    e = Examination.query.get(exam_id)
    if e:
        db.session.delete(e)
        db.session.commit()
        flash('Examination deleted.', 'success')

    return redirect(url_for('admin.examinations'))


# ---------------------------------------------------------------------------
# Rubrics
# ---------------------------------------------------------------------------

def _rubric_view_data(rubrics):
    return [{
        'id': r.id,
        'exam_name': r.exam.name if r.exam else 'N/A',
        'criterion_name': r.criterion_name,
        'max_marks': r.max_marks,
        'weightage': r.weightage
    } for r in rubrics]


@admin_bp.route('/rubrics', methods=['GET', 'POST'])
@login_required
def rubrics():
    if not admin_only():
        return redirect(url_for('auth.login'))

    exams_options = [{'value': ex.id, 'label': ex.name} for ex in Examination.query.all()]

    if request.method == 'POST':
        action = request.form.get('action')
        data = {
            'exam_id': int(request.form.get('exam_id')),
            'criterion_name': request.form.get('criterion_name', '').strip(),
            'max_marks': int(request.form.get('max_marks', 0)),
            'weightage': float(request.form.get('weightage', 0)),
            'description': request.form.get('description', '').strip()
        }

        if action == 'edit':
            r = Rubric.query.get(request.form.get('rubric_id'))
            if r:
                for k, v in data.items():
                    setattr(r, k, v)
                db.session.commit()
                flash('Rubric updated.', 'success')
        else:
            db.session.add(Rubric(**data))
            db.session.commit()
            flash('Rubric created.', 'success')

        return redirect(url_for('admin.rubrics'))

    q = request.args.get('q', '').strip()
    items = Rubric.query.filter(Rubric.criterion_name.ilike(f'%{q}%')).all() if q else Rubric.query.all()

    return render_template('admin/rubrics.html',
                           rubrics=_rubric_view_data(items),
                           exams_options=exams_options,
                           edit=None,
                           q=q)


@admin_bp.route('/rubrics/edit/<int:rubric_id>')
@login_required
def rubric_edit(rubric_id):
    if not admin_only():
        return redirect(url_for('auth.login'))

    r = Rubric.query.get_or_404(rubric_id)
    exams_options = [{'value': ex.id, 'label': ex.name} for ex in Examination.query.all()]

    return render_template('admin/rubrics.html',
                           rubrics=_rubric_view_data(Rubric.query.all()),
                           exams_options=exams_options,
                           edit=r,
                           q='')


@admin_bp.route('/rubrics/delete/<int:rubric_id>', methods=['POST'])
@login_required
def rubric_delete(rubric_id):
    if not admin_only():
        return redirect(url_for('auth.login'))

    r = Rubric.query.get(rubric_id)
    if r:
        db.session.delete(r)
        db.session.commit()
        flash('Rubric deleted.', 'success')

    return redirect(url_for('admin.rubrics'))


# ---------------------------------------------------------------------------
# Examiners
# ---------------------------------------------------------------------------

def _examiner_view_data(examiners):
    return [{
        'id': ex.id,
        'name': ex.name,
        'email': ex.user.email if ex.user else '',
        'department': ex.department.name if ex.department else 'N/A',
        'status': ex.status.capitalize()
    } for ex in examiners]


@admin_bp.route('/examiners', methods=['GET', 'POST'])
@login_required
def examiners():
    if not admin_only():
        return redirect(url_for('auth.login'))

    departments_options = [{'value': d.id, 'label': d.name} for d in Department.query.all()]

    if request.method == 'POST':
        examiner = Examiner.query.get(request.form.get('examiner_id'))
        if examiner:
            examiner.name = request.form.get('name', '').strip()
            examiner.phone = request.form.get('phone', '').strip()
            dept_id = request.form.get('department_id')
            examiner.department_id = int(dept_id) if dept_id else None
            examiner.status = request.form.get('status', 'Pending').strip().lower()

            email = request.form.get('email', '').strip()
            if email and examiner.user:
                examiner.user.email = email

            db.session.commit()
            flash('Examiner updated.', 'success')

        return redirect(url_for('admin.examiners'))

    q = request.args.get('q', '').strip()
    query = Examiner.query
    if q:
        query = query.filter((Examiner.name.ilike(f'%{q}%')) | (Examiner.employee_id.ilike(f'%{q}%')))

    return render_template('admin/examiners.html',
                           examiners=_examiner_view_data(query.all()),
                           departments_options=departments_options,
                           edit=None,
                           q=q)


@admin_bp.route('/examiners/edit/<int:examiner_id>')
@login_required
def examiner_edit(examiner_id):
    if not admin_only():
        return redirect(url_for('auth.login'))

    ex = Examiner.query.get_or_404(examiner_id)
    departments_options = [{'value': d.id, 'label': d.name} for d in Department.query.all()]

    edit_data = {
        'id': ex.id,
        'name': ex.name,
        'email': ex.user.email if ex.user else '',
        'phone': ex.phone,
        'department_id': ex.department_id,
        'status': ex.status.capitalize()
    }

    return render_template('admin/examiners.html',
                           examiners=_examiner_view_data(Examiner.query.all()),
                           departments_options=departments_options,
                           edit=edit_data,
                           q='')


@admin_bp.route('/examiners/approve/<int:examiner_id>', methods=['POST'])
@login_required
def examiner_approve(examiner_id):
    if not admin_only():
        return redirect(url_for('auth.login'))

    ex = Examiner.query.get(examiner_id)
    if ex:
        ex.status = 'approved'
        db.session.commit()
        flash(f'Examiner {ex.name} approved.', 'success')

    return redirect(url_for('admin.examiners'))


@admin_bp.route('/examiners/deactivate/<int:examiner_id>', methods=['POST'])
@login_required
def examiner_deactivate(examiner_id):
    if not admin_only():
        return redirect(url_for('auth.login'))

    ex = Examiner.query.get(examiner_id)
    if ex:
        ex.status = 'inactive'
        if ex.user:
            ex.user.is_active = False
        db.session.commit()
        flash(f'Examiner {ex.name} deactivated.', 'info')

    return redirect(url_for('admin.examiners'))


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------

def _student_view_data(students):
    return [{
        'id': s.id,
        'name': s.name,
        'email': s.user.email if s.user else '',
        'student_id': s.roll_no,
        'status': s.status.capitalize()
    } for s in students]


@admin_bp.route('/students', methods=['GET', 'POST'])
@login_required
def students():
    if not admin_only():
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        student = Student.query.get(request.form.get('student_id'))
        if student:
            student.name = request.form.get('name', '').strip()
            student.phone = request.form.get('phone', '').strip()
            student.roll_no = request.form.get('student_id', '').strip()
            status = request.form.get('status', 'Active').strip()
            student.status = status.lower()

            email = request.form.get('email', '').strip()
            if email and student.user:
                student.user.email = email
                student.user.is_active = (status.lower() == 'active')

            db.session.commit()
            flash('Student updated.', 'success')

        return redirect(url_for('admin.students'))

    q = request.args.get('q', '').strip()
    query = Student.query
    if q:
        query = query.filter((Student.name.ilike(f'%{q}%')) | (Student.roll_no.ilike(f'%{q}%')))

    return render_template('admin/students.html',
                           students=_student_view_data(query.all()),
                           edit=None,
                           q=q)


@admin_bp.route('/students/edit/<int:student_id>')
@login_required
def student_edit(student_id):
    if not admin_only():
        return redirect(url_for('auth.login'))

    st = Student.query.get_or_404(student_id)
    edit_data = {
        'id': st.id,
        'name': st.name,
        'email': st.user.email if st.user else '',
        'phone': st.phone,
        'student_id': st.roll_no,
        'status': st.status.capitalize()
    }

    return render_template('admin/students.html',
                           students=_student_view_data(Student.query.all()),
                           edit=edit_data,
                           q='')


# ---------------------------------------------------------------------------
# Examination Slots
# ---------------------------------------------------------------------------

@admin_bp.route('/slots')
@login_required
def slots():
    if not admin_only():
        return redirect(url_for('auth.login'))

    q = request.args.get('q', '').strip()
    query = ExaminationSlot.query
    if q:
        query = query.join(Examination).filter(Examination.name.ilike(f'%{q}%'))

    slot_items = []
    for s in query.all():
        booked_count = Booking.query.filter_by(slot_id=s.id, status='booked').count()
        slot_items.append({
            'id': s.id,
            'exam_name': s.exam.name if s.exam else 'N/A',
            'examiner_name': s.examiner.name if s.examiner else 'N/A',
            'date': s.date.strftime('%Y-%m-%d') if s.date else '',
            'start_time': s.start_time.strftime('%H:%M') if s.start_time else '',
            'end_time': s.end_time.strftime('%H:%M') if s.end_time else '',
            'capacity': s.max_capacity,
            'booked': booked_count,
            'status': s.status.capitalize()
        })

    return render_template('admin/slots.html', slots=slot_items, q=q)


@admin_bp.route('/slots/edit/<int:slot_id>', methods=['GET', 'POST'])
@login_required
def slot_edit(slot_id):
    if not admin_only():
        return redirect(url_for('auth.login'))

    ExaminationSlot.query.get_or_404(slot_id)
    return redirect(url_for('admin.slots'))


@admin_bp.route('/slots/reschedule/<int:slot_id>', methods=['POST'])
@login_required
def slot_reschedule(slot_id):
    if not admin_only():
        return redirect(url_for('auth.login'))

    s = ExaminationSlot.query.get(slot_id)
    if s:
        new_date = request.form.get('date')
        if new_date:
            try:
                s.date = datetime.strptime(new_date, '%Y-%m-%d').date()
            except Exception:
                pass
        s.status = 'available'
        db.session.commit()
        flash('Slot rescheduled.', 'info')

    return redirect(url_for('admin.slots'))


@admin_bp.route('/slots/change_examiner/<int:slot_id>', methods=['POST'])
@login_required
def slot_change_examiner(slot_id):
    if not admin_only():
        return redirect(url_for('auth.login'))

    s = ExaminationSlot.query.get(slot_id)
    if s:
        new_examiner_id = request.form.get('examiner_id')
        if new_examiner_id:
            s.examiner_id = int(new_examiner_id)
            db.session.commit()
            flash('Examiner changed for this slot.', 'success')
        else:
            other = Examiner.query.filter(Examiner.id != s.examiner_id, Examiner.status == 'approved').first()
            if other:
                s.examiner_id = other.id
                db.session.commit()
                flash(f'Examiner reassigned to {other.name}.', 'success')
            else:
                flash('No alternate approved examiner found.', 'warning')

    return redirect(url_for('admin.slots'))


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------

@admin_bp.route('/bookings')
@login_required
def bookings():
    if not admin_only():
        return redirect(url_for('auth.login'))

    q = request.args.get('q', '').strip()
    query = Booking.query
    if q:
        query = query.join(Student).filter(Student.name.ilike(f'%{q}%'))

    booking_items = [{
        'id': b.id,
        'student_name': b.student.name if b.student else 'N/A',
        'slot_exam_name': b.slot.exam.name if (b.slot and b.slot.exam) else 'N/A',
        'slot_date': b.slot.date.strftime('%Y-%m-%d') if (b.slot and b.slot.date) else 'N/A',
        'booking_date': b.booking_date.strftime('%Y-%m-%d %H:%M') if b.booking_date else '',
        'status': b.status.capitalize()
    } for b in query.all()]

    booked_slots = Booking.query.filter_by(status='booked').count()
    cancelled = Booking.query.filter_by(status='cancelled').count()
    completed = Booking.query.filter_by(status='completed').count()

    stats = {
        'total_bookings': Booking.query.count(),
        'booked_slots': booked_slots,
        'cancelled': cancelled,
        'completed': completed
    }

    status_stats = [
        {'name': 'Booked', 'count': booked_slots, 'color': 'primary'},
        {'name': 'Cancelled', 'count': cancelled, 'color': 'dark'},
        {'name': 'Completed', 'count': completed, 'color': 'success'},
    ]

    return render_template('admin/bookings.html',
                           bookings=booking_items,
                           stats=stats,
                           status_stats=status_stats,
                           q=q)


@admin_bp.route('/bookings/cancel/<int:booking_id>', methods=['POST'])
@login_required
def booking_cancel(booking_id):
    if not admin_only():
        return redirect(url_for('auth.login'))

    b = Booking.query.get(booking_id)
    if b:
        b.status = 'cancelled'
        if b.slot:
            b.slot.available_seats += 1
            if b.slot.status == 'full':
                b.slot.status = 'available'
        db.session.commit()
        flash('Booking cancelled.', 'info')

    return redirect(url_for('admin.bookings'))


# ---------------------------------------------------------------------------
# Timelines
# ---------------------------------------------------------------------------

@admin_bp.route('/timelines')
@login_required
def timelines():
    if not admin_only():
        return redirect(url_for('auth.login'))

    slot_creation_open = Examination.query.filter_by(status='slot_creation').first() is not None
    booking_open = Examination.query.filter_by(status='booking_open').first() is not None

    exams_timeline = [{
        'name': e.name,
        'slot_start': e.slot_creation_start.strftime('%Y-%m-%d %H:%M') if e.slot_creation_start else '—',
        'slot_end': e.slot_creation_end.strftime('%Y-%m-%d %H:%M') if e.slot_creation_end else '—',
        'booking_start': e.slot_booking_start.strftime('%Y-%m-%d %H:%M') if e.slot_booking_start else '—',
        'booking_end': e.slot_booking_end.strftime('%Y-%m-%d %H:%M') if e.slot_booking_end else '—'
    } for e in Examination.query.all()]

    return render_template('admin/timelines.html',
                           slot_creation_open=slot_creation_open,
                           booking_open=booking_open,
                           slot_start_date='',
                           slot_end_date='',
                           booking_start_date='',
                           booking_end_date='',
                           exams_timeline=exams_timeline)


@admin_bp.route('/timelines/slot_creation', methods=['POST'])
@login_required
def slot_creation():
    if not admin_only():
        return redirect(url_for('auth.login'))

    is_open = Examination.query.filter_by(status='slot_creation').first() is not None
    if is_open:
        for e in Examination.query.filter_by(status='slot_creation').all():
            e.status = 'draft'
        flash('Slot creation closed for all active exams.', 'info')
    else:
        for e in Examination.query.all():
            if e.status in ('draft', 'closed'):
                e.status = 'slot_creation'
        flash('Slot creation opened for examinations.', 'success')

    db.session.commit()
    return redirect(url_for('admin.timelines'))


@admin_bp.route('/timelines/booking_period', methods=['POST'])
@login_required
def booking_period():
    if not admin_only():
        return redirect(url_for('auth.login'))

    is_open = Examination.query.filter_by(status='booking_open').first() is not None
    if is_open:
        for e in Examination.query.filter_by(status='booking_open').all():
            e.status = 'closed'
        flash('Student slot booking closed for examinations.', 'info')
    else:
        for e in Examination.query.all():
            if e.status in ('draft', 'slot_creation', 'closed'):
                e.status = 'booking_open'
        flash('Student slot booking opened for examinations.', 'success')

    db.session.commit()
    return redirect(url_for('admin.timelines'))


# ---------------------------------------------------------------------------
# Results — view all submitted/published evaluations and publish them
# ---------------------------------------------------------------------------

@admin_bp.route('/results')
@login_required
def results():
    if not admin_only():
        return redirect(url_for('auth.login'))

    all_bookings = Booking.query.all()
    results_data = []

    for b in all_bookings:
        ev = b.evaluation
        # only show bookings that have an evaluation record
        if not ev:
            continue

        results_data.append({
            'booking_id': b.id,
            'evaluation_id': ev.id,
            'student_name': b.student.name,
            'exam_name': b.slot.exam.name,
            'slot_date': b.slot.date,
            'total_marks': ev.total_marks if ev.total_marks is not None else '—',
            'eval_status': ev.status.capitalize(),
        })

    return render_template('admin/results.html', results=results_data)


@admin_bp.route('/results/publish/<int:evaluation_id>', methods=['POST'])
@login_required
def publish_result(evaluation_id):
    if not admin_only():
        return redirect(url_for('auth.login'))

    ev = Evaluation.query.get_or_404(evaluation_id)

    if ev.status != 'submitted':
        flash('Only submitted evaluations can be published.', 'warning')
        return redirect(url_for('admin.results'))

    ev.status = 'published'
    db.session.commit()
    flash('Result published — student can now see it.', 'success')
    return redirect(url_for('admin.results'))
