from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime

from models.models import db, Examiner, Examination, ExaminationSlot, Booking, Evaluation, EvaluationScore, Rubric

examiner_bp = Blueprint('examiner', __name__)


def get_examiner_or_abort():
    examiner = Examiner.query.filter_by(user_id=current_user.id).first()
    return examiner


# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------

@examiner_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'examiner':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    examiner = get_examiner_or_abort()
    if not examiner:
        flash('Examiner profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    exams = []
    can_create_slots = False

    for slot in examiner.slots:
        exam = slot.exam
        if exam.status == 'slot_creation':
            can_create_slots = True

    # Build the exams list — deduplicated by exam
    seen = set()
    for slot in examiner.slots:
        exam = slot.exam
        if exam.id in seen:
            continue
        seen.add(exam.id)

        slots_data = []
        for s in exam.slots:
            if s.examiner_id == examiner.id:
                slots_data.append({
                    'id': s.id,
                    'date': s.date,
                    'start_time': s.start_time,
                    'end_time': s.end_time,
                    'capacity': s.max_capacity,
                    'booked': s.max_capacity - s.available_seats,
                    'status': s.status.capitalize(),
                })

        bookings_data = []
        for s in exam.slots:
            if s.examiner_id == examiner.id:
                for b in s.bookings:
                    if b.status == 'booked':
                        bookings_data.append({'id': b.id})

        exams.append({
            'id': exam.id,
            'name': exam.name,
            'type': exam.exam_type,
            'duration': exam.duration,
            'max_marks': exam.max_marks,
            'status': exam.status.replace('_', ' ').capitalize(),
            'slots': slots_data,
            'bookings': bookings_data,
        })

    # Also check exams in slot_creation status even if no slots created yet
    # (examiner may need to create first slot)
    # We just recheck across all exams with status=slot_creation assigned via slots
    # Actually for simplicity: allow if any exam linked to this examiner is in slot_creation
    all_examiner_exam_ids = {slot.exam_id for slot in examiner.slots}
    for eid in all_examiner_exam_ids:
        exam = Examination.query.get(eid)
        if exam and exam.status == 'slot_creation':
            can_create_slots = True
            break

    exams_options = []
    for eid in all_examiner_exam_ids:
        exam = Examination.query.get(eid)
        if exam and exam.status == 'slot_creation':
            exams_options.append({'value': exam.id, 'label': exam.name})

    return render_template('examiner/dashboard.html',
        exams=exams,
        can_create_slots=can_create_slots,
        exams_options=exams_options,
        examiner=examiner,
    )


# ------------------------------------------------------------------
# Assigned Examinations
# ------------------------------------------------------------------

@examiner_bp.route('/examinations')
@login_required
def examinations():
    if current_user.role != 'examiner':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    examiner = get_examiner_or_abort()
    if not examiner:
        flash('Examiner profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    seen = set()
    assigned_exams = []

    for slot in examiner.slots:
        exam = slot.exam
        if exam.id in seen:
            continue
        seen.add(exam.id)

        slots_data = []
        for s in exam.slots:
            if s.examiner_id == examiner.id:
                slots_data.append({
                    'id': s.id,
                    'date': s.date,
                    'start_time': s.start_time,
                    'end_time': s.end_time,
                    'status': s.status.capitalize(),
                })

        bookings_data = []
        for s in exam.slots:
            if s.examiner_id == examiner.id:
                for b in s.bookings:
                    bookings_data.append({
                        'id': b.id,
                        'student_name': b.student.name,
                        'student_id': b.student.roll_no,
                    })

        assigned_exams.append({
            'id': exam.id,
            'name': exam.name,
            'type': exam.exam_type,
            'course_name': exam.course.name if exam.course else '—',
            'status': exam.status.replace('_', ' ').capitalize(),
            'slots': slots_data,
            'bookings': bookings_data,
        })

    return render_template('examiner/examinations.html',
        assigned_exams=assigned_exams,
        examiner_id=examiner.id,
    )


# ------------------------------------------------------------------
# My Slots
# ------------------------------------------------------------------

@examiner_bp.route('/slots')
@login_required
def slots():
    if current_user.role != 'examiner':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    examiner = get_examiner_or_abort()
    if not examiner:
        flash('Examiner profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    my_slots = []
    for s in examiner.slots:
        my_slots.append({
            'id': s.id,
            'exam_name': s.exam.name,
            'date': s.date,
            'start_time': s.start_time,
            'end_time': s.end_time,
            'capacity': s.max_capacity,
            'booked': s.max_capacity - s.available_seats,
            'status': s.status.capitalize(),
        })

    return render_template('examiner/slots.html', my_slots=my_slots)


# ------------------------------------------------------------------
# Create Slot (POST)
# ------------------------------------------------------------------

@examiner_bp.route('/slots/create', methods=['POST'])
@login_required
def slot_create():
    if current_user.role != 'examiner':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    examiner = get_examiner_or_abort()
    if not examiner:
        flash('Examiner profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    exam_id = request.form.get('exam_id', type=int)
    date_str = request.form.get('date', '').strip()
    start_str = request.form.get('start_time', '').strip()
    end_str = request.form.get('end_time', '').strip()
    capacity = request.form.get('capacity', type=int)

    exam = Examination.query.get(exam_id)
    if not exam or exam.status != 'slot_creation':
        flash('Slot creation is not currently open for this examination.', 'warning')
        return redirect(url_for('examiner.dashboard'))

    if not all([date_str, start_str, end_str, capacity]):
        flash('All fields are required.', 'warning')
        return redirect(url_for('examiner.dashboard'))

    try:
        slot_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
    except ValueError:
        flash('Invalid date or time format.', 'danger')
        return redirect(url_for('examiner.dashboard'))

    new_slot = ExaminationSlot(
        exam_id=exam.id,
        examiner_id=examiner.id,
        date=slot_date,
        start_time=start_time,
        end_time=end_time,
        max_capacity=capacity,
        available_seats=capacity,
        status='available',
    )
    db.session.add(new_slot)
    db.session.commit()

    flash('Slot created successfully.', 'success')
    return redirect(url_for('examiner.slots'))


# ------------------------------------------------------------------
# Edit Slot (GET/POST)
# ------------------------------------------------------------------

@examiner_bp.route('/slots/edit/<int:slot_id>', methods=['GET', 'POST'])
@login_required
def slot_edit(slot_id):
    if current_user.role != 'examiner':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    examiner = get_examiner_or_abort()
    slot = ExaminationSlot.query.get_or_404(slot_id)

    if slot.examiner_id != examiner.id:
        flash('Not your slot.', 'danger')
        return redirect(url_for('examiner.slots'))

    if slot.exam.status != 'slot_creation':
        flash('Slots can only be edited during slot creation period.', 'warning')
        return redirect(url_for('examiner.slots'))

    if request.method == 'POST':
        date_str = request.form.get('date', '').strip()
        start_str = request.form.get('start_time', '').strip()
        end_str = request.form.get('end_time', '').strip()
        capacity = request.form.get('capacity', type=int)

        try:
            slot.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            slot.start_time = datetime.strptime(start_str, '%H:%M').time()
            slot.end_time = datetime.strptime(end_str, '%H:%M').time()
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            return redirect(url_for('examiner.slot_edit', slot_id=slot_id))

        if capacity and capacity >= (slot.max_capacity - slot.available_seats):
            # Can't shrink below already-booked count
            booked_count = slot.max_capacity - slot.available_seats
            slot.available_seats = capacity - booked_count
            slot.max_capacity = capacity
        db.session.commit()
        flash('Slot updated.', 'success')
        return redirect(url_for('examiner.slots'))

    return render_template('examiner/slots.html', edit_slot=slot, my_slots=[])


# ------------------------------------------------------------------
# Evaluations — list pending evaluations
# ------------------------------------------------------------------

@examiner_bp.route('/evaluations')
@login_required
def evaluations():
    if current_user.role != 'examiner':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    examiner = get_examiner_or_abort()
    if not examiner:
        flash('Examiner profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    evals = []
    for slot in examiner.slots:
        for booking in slot.bookings:
            if booking.status != 'booked':
                continue

            existing = booking.evaluation
            rubrics_data = []
            for rubric in slot.exam.rubrics:
                score_obj = None
                if existing:
                    score_obj = next((s for s in existing.scores if s.rubric_id == rubric.id), None)
                rubrics_data.append({
                    'rubric_id': rubric.id,
                    'criterion_name': rubric.criterion_name,
                    'weightage': rubric.weightage,
                    'max_marks': rubric.max_marks,
                    'marks': score_obj.marks if score_obj else '',
                })

            evals.append({
                'booking_id': booking.id,
                'exam_id': slot.exam_id,
                'student_name': booking.student.name,
                'slot_exam_name': slot.exam.name,
                'rubrics': rubrics_data,
                'remarks': existing.remarks if existing else '',
            })

    return render_template('examiner/evaluation.html',
        evaluations=evals,
        examiner_id=examiner.id,
    )


# ------------------------------------------------------------------
# Submit Evaluation (POST)
# ------------------------------------------------------------------

@examiner_bp.route('/evaluate/<int:booking_id>', methods=['POST'])
@login_required
def submit_evaluation(booking_id):
    if current_user.role != 'examiner':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    examiner = get_examiner_or_abort()
    booking = Booking.query.get_or_404(booking_id)

    # Confirm this booking is under this examiner's slot
    if booking.slot.examiner_id != examiner.id:
        flash('Not authorized to evaluate this booking.', 'danger')
        return redirect(url_for('examiner.evaluations'))

    remarks = request.form.get('remarks', '').strip()
    rubrics = booking.slot.exam.rubrics

    # Find or create evaluation record
    evaluation = booking.evaluation
    if not evaluation:
        evaluation = Evaluation(
            booking_id=booking.id,
            examiner_id=examiner.id,
            remarks=remarks,
            status='submitted',
            submitted_at=datetime.utcnow(),
        )
        db.session.add(evaluation)
        db.session.flush()
    else:
        evaluation.remarks = remarks
        evaluation.status = 'submitted'
        evaluation.submitted_at = datetime.utcnow()

    total = 0.0
    for rubric in rubrics:
        field_name = f'marks_{rubric.id}'
        raw = request.form.get(field_name, '')
        try:
            mark = float(raw)
        except (ValueError, TypeError):
            mark = 0.0

        mark = min(mark, rubric.max_marks)  # clamp to max

        existing_score = next((s for s in evaluation.scores if s.rubric_id == rubric.id), None)
        if existing_score:
            existing_score.marks = mark
        else:
            score = EvaluationScore(evaluation_id=evaluation.id, rubric_id=rubric.id, marks=mark)
            db.session.add(score)

        total += mark

    evaluation.total_marks = total
    db.session.commit()

    flash('Evaluation submitted.', 'success')
    return redirect(url_for('examiner.results'))


# ------------------------------------------------------------------
# Results — submitted/published evaluations for this examiner
# ------------------------------------------------------------------

@examiner_bp.route('/results')
@login_required
def results():
    if current_user.role != 'examiner':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    examiner = get_examiner_or_abort()
    if not examiner:
        flash('Examiner profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    results_data = []
    for ev in examiner.evaluations:
        if ev.status not in ('submitted', 'published'):
            continue
        booking = ev.booking
        results_data.append({
            'booking_id': booking.id,
            'student_name': booking.student.name,
            'slot_date': booking.slot.date,
            'total_marks': ev.total_marks,
            'status': ev.status.capitalize(),
        })

    return render_template('examiner/results.html', results=results_data)
