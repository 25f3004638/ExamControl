from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

from models.models import db, User, Examiner, Student, Course, Department, Examination, Rubric, ExaminationSlot, Booking

auth_bp     = Blueprint('auth', __name__)
admin_bp    = Blueprint('admin', __name__) 

examiner_bp = Blueprint('examiner', __name__)
student_bp  = Blueprint('student', __name__)

@auth_bp.route('/')
def home():
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_to_dashboard(current_user)
    

    if request.method == 'POST':
        email    = request.form.get('username')   # input is named "username" in the template
        password = request.form.get('password')


        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Wrong email or password.', 'danger')
            return render_template('auth/login.html')



        if not user.is_active:

            flash('Your account has been deactivated. Contact the admin.', 'danger')
            return render_template('auth/login.html')

        
        if user.role == 'examiner':
            examiner = Examiner.query.filter_by(user_id=user.id).first()

            if examiner.status == 'pending': 

                flash('Your account is pending admin approval.', 'warning')
                return render_template('auth/login.html')

            
            if examiner.status in ('rejected', 'inactive'):

                flash('Your examiner account has been rejected or deactivated.', 'danger')
                return render_template('auth/login.html')

        login_user(user)
        return redirect_to_dashboard(user)

    return render_template('auth/login.html')



@auth_bp.route('/logout')
@login_required
def logout():

    logout_user()

    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/student/register', methods=['GET', 'POST'])
def register_student():
    courses = Course.query.filter_by(status='active').all()

    if request.method == 'POST':
        first_name    = request.form.get('first_name', '').strip()
        last_name  = request.form.get('last_name', '').strip()
        email   = request.form.get('email', '').strip()


        phone   = request.form.get('phone', '').strip()
        student_id  =request.form.get('student_id', '').strip()
        course_id  = request.form.get('course_id', '').strip()

        year= request.form.get('year', '').strip()
        password= request.form.get('password', '')

        confirm_password = request.form.get('confirm_password', '')



        if not first_name or not last_name:
            flash('Please enter your full name.', 'danger')
            return render_template('auth/register_student.html', courses=courses)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register_student.html', courses=courses)

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/register_student.html', courses=courses)

        if User.query.filter_by(email=email).first():
            flash('That email is already registered.', 'danger')
            return render_template('auth/register_student.html', courses=courses)

        if Student.query.filter_by(roll_no=student_id).first():
            flash('That Student ID is already taken.', 'danger')
            return render_template('auth/register_student.html', courses=courses)

        new_user = User(email=email, role='student', is_active=True)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()      # get new_user.id before commit

        new_student = Student(
            user_id   = new_user.id,
            roll_no   = student_id,
            name      = first_name + ' ' + last_name,
            phone     = phone,
            course_id = int(course_id) if course_id else None,
            year      = year,
            status    = 'active'
        )
        db.session.add(new_student)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_student.html', courses=courses)


@auth_bp.route('/examiner/register', methods=['GET', 'POST'])
def register_examiner():
    departments = Department.query.all()

    if request.method == 'POST':
        name             = request.form.get('name', '').strip()
        email            = request.form.get('email', '').strip()
        phone            = request.form.get('phone', '').strip()
        employee_id      = request.form.get('employee_id', '').strip()
        department_id    = request.form.get('department_id', '').strip()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not name:
            flash('Name is required.', 'danger')
            return render_template('auth/register_examiner.html', departments=departments)

        if not employee_id:
            flash('Employee ID is required.', 'danger')
            return render_template('auth/register_examiner.html', departments=departments)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register_examiner.html', departments=departments)

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/register_examiner.html', departments=departments)

        if User.query.filter_by(email=email).first():
            flash('That email is already registered.', 'danger')
            return render_template('auth/register_examiner.html', departments=departments)

        if Examiner.query.filter_by(employee_id=employee_id).first():
            flash('That Employee ID is already taken.', 'danger')
            return render_template('auth/register_examiner.html', departments=departments)

        new_user = User(email=email, role='examiner', is_active=True)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()      # get new_user.id before commit

        new_examiner = Examiner(
            user_id   = new_user.id,
            employee_id  = employee_id,
            name = name,
            phone = phone,
            department_id= int(department_id) if department_id else None,
            status = 'pending'   # admin must approve
        )
        db.session.add(new_examiner)
        db.session.commit()

        flash('Registered! Please wait for admin approval before logging in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_examiner.html', departments=departments)



#-------------------------------------------Admin Routes---------------------------------------
@admin_bp.route('/dashboard')
@login_required

def dashboard():
    if current_user.role != 'admin':

        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    from models.models import Course, Examination, Examiner, Student, ExaminationSlot, Booking
    stats = {
        'courses': Course.query.count(),
        'examinations': Examination.query.count(),
        'examiners':    Examiner.query.count(),
        'students':     Student.query.count(),
        'slots':        ExaminationSlot.query.count(),
        'bookings':     Booking.query.count(),
    }

    slot_creation_open = Examination.query.filter_by(status='slot_creation').first() is not None
    booking_open       = Examination.query.filter_by(status='booking_open').first() is not None

    return render_template('admin/dashboard.html',
                           stats=stats,
                           slot_creation_open=slot_creation_open,
                           booking_open=booking_open)



@examiner_bp.route('/dashboard')
@login_required
def dashboard():

    if current_user.role != 'examiner':
        flash('Access denied.', 'danger')

        return redirect(url_for('auth.login'))
    return render_template('examiner/dashboard.html')




@student_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'student':


        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    
    return render_template('student/dashboard.html')




def redirect_to_dashboard(user):
    if user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif user.role == 'examiner':
        return redirect(url_for('examiner.dashboard'))
    else:
        return redirect(url_for('student.dashboard'))


# ─────────────────────────────────────────────
#  ADMIN BLUEPRINT ROUTES
# ─────────────────────────────────────────────

# --- Courses ---

@admin_bp.route('/courses', methods=['GET', 'POST'])
@login_required
def courses():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        action = request.form.get('action')
        code = request.form.get('code', '').strip()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'Active').strip()

        if action == 'edit':
            cid = request.form.get('course_id')
            c = Course.query.get(cid)
            if c:
                c.code = code
                c.name = name
                c.description = description
                c.status = status
                db.session.commit()
                flash('Course updated successfully.', 'success')
        else:
            if Course.query.filter_by(code=code).first():
                flash('Course code already exists.', 'danger')
            else:
                new_c = Course(code=code, name=name, description=description, status=status)
                db.session.add(new_c)
                db.session.commit()
                flash('Course created successfully.', 'success')

        return redirect(url_for('admin.courses'))

    q = request.args.get('q', '').strip()
    if q:
        all_courses = Course.query.filter((Course.name.ilike(f'%{q}%')) | (Course.code.ilike(f'%{q}%'))).all()
    else:
        all_courses = Course.query.all()

    return render_template('admin/courses.html', courses=all_courses, edit=None, q=q)


@admin_bp.route('/courses/edit/<int:course_id>')
@login_required
def course_edit(course_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    edit_course = Course.query.get_or_404(course_id)
    all_courses = Course.query.all()
    return render_template('admin/courses.html', courses=all_courses, edit=edit_course, q='')


@admin_bp.route('/courses/delete/<int:course_id>', methods=['POST'])
@login_required
def course_delete(course_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    c = Course.query.get(course_id)
    if c:
        db.session.delete(c)
        db.session.commit()
        flash('Course deleted.', 'success')

    return redirect(url_for('admin.courses'))


# --- Examinations ---

@admin_bp.route('/examinations', methods=['GET', 'POST'])
@login_required
def examinations():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    courses_list = Course.query.all()
    courses_options = [{'value': c.id, 'label': f"{c.code} - {c.name}"} for c in courses_list]

    if request.method == 'POST':
        action = request.form.get('action')
        course_id = request.form.get('course_id')
        name = request.form.get('name', '').strip()
        exam_type = request.form.get('type', '').strip()
        duration = request.form.get('duration', 0)
        max_marks = request.form.get('max_marks', 0)
        status = request.form.get('status', 'Draft').strip()

        slot_start_str = request.form.get('slot_start')
        slot_end_str = request.form.get('slot_end')
        booking_start_str = request.form.get('booking_start')
        booking_end_str = request.form.get('booking_end')

        def parse_dt(s):
            if not s:
                return None
            try:
                return datetime.strptime(s, '%Y-%m-%dT%H:%M')
            except Exception:
                return None

        slot_start = parse_dt(slot_start_str)
        slot_end = parse_dt(slot_end_str)
        booking_start = parse_dt(booking_start_str)
        booking_end = parse_dt(booking_end_str)

        if action == 'edit':
            eid = request.form.get('exam_id')
            e = Examination.query.get(eid)
            if e:
                e.course_id = int(course_id)
                e.name = name
                e.exam_type = exam_type
                e.duration = int(duration)
                e.max_marks = int(max_marks)
                e.status = status
                e.slot_creation_start = slot_start
                e.slot_creation_end = slot_end
                e.slot_booking_start = booking_start
                e.slot_booking_end = booking_end
                db.session.commit()
                flash('Examination updated successfully.', 'success')
        else:
            new_e = Examination(
                course_id=int(course_id),
                name=name,
                exam_type=exam_type,
                duration=int(duration),
                max_marks=int(max_marks),
                status=status,
                slot_creation_start=slot_start,
                slot_creation_end=slot_end,
                slot_booking_start=booking_start,
                slot_booking_end=booking_end
            )
            db.session.add(new_e)
            db.session.commit()
            flash('Examination created successfully.', 'success')

        return redirect(url_for('admin.examinations'))

    q = request.args.get('q', '').strip()
    if q:
        all_exams = Examination.query.filter(Examination.name.ilike(f'%{q}%')).all()
    else:
        all_exams = Examination.query.all()

    # prepare display list with helper properties
    exam_items = []
    for e in all_exams:
        exam_items.append({
            'id': e.id,
            'course_name': e.course.name if e.course else 'N/A',
            'name': e.name,
            'type': e.exam_type,
            'max_marks': e.max_marks,
            'status': e.status
        })

    return render_template('admin/examinations.html',
                           examinations=exam_items,
                           courses_options=courses_options,
                           edit=None,
                           q=q)


@admin_bp.route('/examinations/edit/<int:exam_id>')
@login_required
def exam_edit(exam_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    e = Examination.query.get_or_404(exam_id)
    courses_list = Course.query.all()
    courses_options = [{'value': c.id, 'label': f"{c.code} - {c.name}"} for c in courses_list]

    all_exams = Examination.query.all()
    exam_items = []
    for ex in all_exams:
        exam_items.append({
            'id': ex.id,
            'course_name': ex.course.name if ex.course else 'N/A',
            'name': ex.name,
            'type': ex.exam_type,
            'max_marks': ex.max_marks,
            'status': ex.status
        })

    edit_data = {
        'id': e.id,

        "course_id": e.course_id,
        'name': e.name,
        'type': e.exam_type,

        "duration": e.duration,
        'max_marks': e.max_marks,

        'status': e.status,

        'slot_start': e.slot_creation_start.strftime('%Y-%m-%dT%H:%M') if e.slot_creation_start else '',
        'slot_end': e.slot_creation_end.strftime('%Y-%m-%dT%H:%M') if e.slot_creation_end else '',
        'booking_start': e.slot_booking_start.strftime('%Y-%m-%dT%H:%M') if e.slot_booking_start else '',
        'booking_end': e.slot_booking_end.strftime('%Y-%m-%dT%H:%M') if e.slot_booking_end else ''
    }

    return render_template('admin/examinations.html',
                           examinations=exam_items,
                           courses_options=courses_options,
                           edit=edit_data,
                           q='')


@admin_bp.route('/examinations/delete/<int:exam_id>', methods=['POST'])
@login_required
def exam_delete(exam_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    e = Examination.query.get(exam_id)
    if e:
        db.session.delete(e)
        db.session.commit()
        flash('Examination deleted.', 'success')

    return redirect(url_for('admin.examinations'))



@admin_bp.route('/rubrics', methods=['GET', 'POST'])
@login_required
def rubrics():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    exams_list = Examination.query.all()
    exams_options = [{'value': ex.id, 'label': ex.name} for ex in exams_list]

    if request.method == 'POST':
        action = request.form.get('action')
        exam_id = request.form.get('exam_id')
        criterion_name = request.form.get('criterion_name', '').strip()
        max_marks = request.form.get('max_marks', 0)
        weightage = request.form.get('weightage', 0)
        description = request.form.get('description', '').strip()

        if action == 'edit':
            rid = request.form.get('rubric_id')
            r = Rubric.query.get(rid)
            if r:
                r.exam_id = int(exam_id)
                r.criterion_name = criterion_name
                r.max_marks = int(max_marks)
                r.weightage = float(weightage)
                r.description = description
                db.session.commit()
                flash('Rubric updated successfully.', 'success')
        else:
            new_r = Rubric(
                exam_id=int(exam_id),
                criterion_name=criterion_name,
                max_marks=int(max_marks),
                weightage=float(weightage),
                description=description
            )
            db.session.add(new_r)
            db.session.commit()
            flash('Rubric created successfully.', 'success')

        return redirect(url_for('admin.rubrics'))

    q = request.args.get('q', '').strip()
    if q:
        all_rubrics = Rubric.query.filter(Rubric.criterion_name.ilike(f'%{q}%')).all()
    else:
        all_rubrics = Rubric.query.all()

    rubric_items = []
    for r in all_rubrics:
        rubric_items.append({
            'id': r.id,
            'exam_name': r.exam.name if r.exam else 'N/A',
            'criterion_name': r.criterion_name,
            'max_marks': r.max_marks,
            'weightage': r.weightage
        })

    return render_template('admin/rubrics.html',
                           rubrics=rubric_items,
                           exams_options=exams_options,
                           edit=None,
                           q=q)


@admin_bp.route('/rubrics/edit/<int:rubric_id>')
@login_required
def rubric_edit(rubric_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    r = Rubric.query.get_or_404(rubric_id)
    exams_list = Examination.query.all()
    exams_options = [{'value': ex.id, 'label': ex.name} for ex in exams_list]

    all_rubrics = Rubric.query.all()
    rubric_items = []
    for item in all_rubrics:
        rubric_items.append({
            'id': item.id,
            'exam_name': item.exam.name if item.exam else 'N/A',
            'criterion_name': item.criterion_name,
            'max_marks': item.max_marks,
            'weightage': item.weightage
        })

    return render_template('admin/rubrics.html',
                           rubrics=rubric_items,
                           exams_options=exams_options,
                           edit=r,
                           q='')


@admin_bp.route('/rubrics/delete/<int:rubric_id>', methods=['POST'])
@login_required
def rubric_delete(rubric_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    r = Rubric.query.get(rubric_id)
    if r:
        db.session.delete(r)
        db.session.commit()
        flash('Rubric deleted.', 'success')

    return redirect(url_for('admin.rubrics'))


# --- Examiners ---

@admin_bp.route('/examiners', methods=['GET', 'POST'])
@login_required
def examiners():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    departments_list = Department.query.all()
    departments_options = [{'value': d.id, 'label': d.name} for d in departments_list]

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'edit':
            ex_id = request.form.get('examiner_id')
            examiner = Examiner.query.get(ex_id)
            if examiner:
                examiner.name = request.form.get('name', '').strip()
                examiner.phone = request.form.get('phone', '').strip()
                dept_id = request.form.get('department_id')
                examiner.department_id = int(dept_id) if dept_id else None
                status = request.form.get('status', 'Pending').strip()
                examiner.status = status.lower()

                email = request.form.get('email', '').strip()
                if email and examiner.user:
                    examiner.user.email = email

                db.session.commit()
                flash('Examiner updated successfully.', 'success')

        return redirect(url_for('admin.examiners'))

    q = request.args.get('q', '').strip()
    if q:
        all_examiners = Examiner.query.filter(
            (Examiner.name.ilike(f'%{q}%')) | (Examiner.employee_id.ilike(f'%{q}%'))
        ).all()
    else:
        all_examiners = Examiner.query.all()

    examiner_items = []
    for ex in all_examiners:
        examiner_items.append({
            'id': ex.id,
            'name': ex.name,
            'email': ex.user.email if ex.user else '',
            'department': ex.department.name if ex.department else 'N/A',
            'status': ex.status.capitalize()
        })

    return render_template('admin/examiners.html',
                           examiners=examiner_items,
                           departments_options=departments_options,
                           edit=None,
                           q=q)


@admin_bp.route('/examiners/edit/<int:examiner_id>')
@login_required
def examiner_edit(examiner_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    ex = Examiner.query.get_or_404(examiner_id)
    departments_list = Department.query.all()
    departments_options = [{'value': d.id, 'label': d.name} for d in departments_list]

    all_examiners = Examiner.query.all()
    examiner_items = []
    for item in all_examiners:
        examiner_items.append({
            'id': item.id,
            'name': item.name,
            'email': item.user.email if item.user else '',
            'department': item.department.name if item.department else 'N/A',
            'status': item.status.capitalize()
        })

    edit_data = {
        'id': ex.id,
        'name': ex.name,
        'email': ex.user.email if ex.user else '',
        'phone': ex.phone,
        'department_id': ex.department_id,
        'status': ex.status.capitalize()
    }

    return render_template('admin/examiners.html',
           examiners=examiner_items,
        departments_options=departments_options,
        edit=edit_data,
        q='')


@admin_bp.route('/examiners/approve/<int:examiner_id>', methods=['POST'])
@login_required
def examiner_approve(examiner_id):

    if current_user.role != 'admin':

        flash('Access denied.', 'danger')

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

    if current_user.role != 'admin':
        flash('Access denied.', 'danger')

        return redirect(url_for('auth.login'))

    ex = Examiner.query.get(examiner_id)
    if ex:

        ex.status = 'inactive'
        if ex.user:

            ex.user.is_active = False
        db.session.commit()

        flash(f'Examiner {ex.name} deactivated.', 'info')


    return redirect(url_for('admin.examiners'))


# --- Students ---

@admin_bp.route('/students', methods=['GET', 'POST'])
@login_required
def students():

    if current_user.role != 'admin':

        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'edit':
            st_id = request.form.get('student_id')
            student = Student.query.get(st_id)

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
                flash('Student updated successfully.', 'success')

        return redirect(url_for('admin.students'))

    q = request.args.get('q', '').strip()
    if q:

        all_students = Student.query.filter(

            (Student.name.ilike(f'%{q}%')) | (Student.roll_no.ilike(f'%{q}%'))
        ).all()

    else:
        all_students = Student.query.all()

    student_items = []

    for s in all_students:
        student_items.append({
        'id': s.id,

            'name': s.name,

            'email': s.user.email if s.user else '',
            'student_id': s.roll_no,
            'status': s.status.capitalize()


        })

    return render_template('admin/students.html', students=student_items, edit=None, q=q)


@admin_bp.route('/students/edit/<int:student_id>')
@login_required
def student_edit(student_id):

    if current_user.role != 'admin':

        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    

    st = Student.query.get_or_404(student_id)

    all_students = Student.query.all()

    student_items = []
    for item in all_students:

        student_items.append({

            'id': item.id,

            'name': item.name,
            'email': item.user.email if item.user else '',


            'student_id': item.roll_no,
            'status': item.status.capitalize()
        })



    edit_data = {
        'id': st.id,
        'name': st.name,

        'email': st.user.email if st.user else '',
        'phone': st.phone,

        'student_id': st.roll_no,
        'status': st.status.capitalize()
    }

    return render_template('admin/students.html', students=student_items, edit=edit_data, q='')


# --- Examination Slots ---

@admin_bp.route('/slots')
@login_required
def slots():
    if current_user.role != 'admin':

        flash('Access denied.', 'danger')

        return redirect(url_for('auth.login'))

    q = request.args.get('q', '').strip()

    query = ExaminationSlot.query
    if q:
        query = query.join(Examination).filter(Examination.name.ilike(f'%{q}%'))


    all_slots = query.all()
    slot_items = []
    for s in all_slots:

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
    if current_user.role != 'admin':

        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    s = ExaminationSlot.query.get_or_404(slot_id)
    return redirect(url_for('admin.slots'))


@admin_bp.route('/slots/reschedule/<int:slot_id>', methods=['POST'])
@login_required
def slot_reschedule(slot_id):

    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
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

    if current_user.role != 'admin':

        flash('Access denied.', 'danger')

        return redirect(url_for('auth.login'))

    s = ExaminationSlot.query.get(slot_id)

    if s:
        new_examiner_id = request.form.get('examiner_id')

        if new_examiner_id:
            s.examiner_id = int(new_examiner_id)

            db.session.commit()
            flash('Examiner changed for this slot.', 'success')

        else:
            other_examiner = Examiner.query.filter(Examiner.id != s.examiner_id, Examiner.status == 'approved').first()

            if other_examiner:

                s.examiner_id = other_examiner.id

                db.session.commit()

                flash(f'Examiner reassigned to {other_examiner.name}.', 'success')

            else:

                flash('No alternate approved examiner found.', 'warning')


    return redirect(url_for('admin.slots'))


# --- Bookings ---

@admin_bp.route('/bookings')
@login_required
def bookings():

    if current_user.role != 'admin':

        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    

    q = request.args.get('q', '').strip()
    query = Booking.query


    if q:
        query = query.join(Student).filter(Student.name.ilike(f'%{q}%'))

    all_bookings = query.all()
    booking_items = []
    for b in all_bookings:
        booking_items.append({
            'id': b.id,

            'student_name': b.student.name if b.student else 'N/A',
            'slot_exam_name': b.slot.exam.name if (b.slot and b.slot.exam) else 'N/A',

            'slot_date': b.slot.date.strftime('%Y-%m-%d') if (b.slot and b.slot.date) else 'N/A',
            'booking_date': b.booking_date.strftime('%Y-%m-%d %H:%M') if b.booking_date else '',
            'status': b.status.capitalize()
        })

    total_bookings = Booking.query.count()

    booked_slots = Booking.query.filter_by(status='booked').count()

    cancelled = Booking.query.filter_by(status='cancelled').count()
    completed = Booking.query.filter_by(status='completed').count()

    stats = {
        'total_bookings': total_bookings,

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
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')

 
        return redirect(url_for('auth.login'))

    b = Booking.query.get(booking_id)
    if b:
        b.status = 'cancelled'

        if b.slot:
            b.slot.available_seats  += 1
            if b.slot.status   =='full':      
                b.slot.status = 'available'

        db.session.commit()
        flash('Booking cancelled successfully.', 'info')

    return redirect(url_for('admin.bookings'))


# --- Timelines ---

@admin_bp.route('/timelines')
@login_required
def timelines():

    if current_user.role != 'admin':
        flash('Access denied.', 'danger')

        return redirect(url_for('auth.login'))

    slot_creation_open = Examination.query.filter_by(status='slot_creation').first() is not None

    booking_open = Examination.query.filter_by(status='booking_open').first() is not None

    exams = Examination.query.all()

    exams_timeline = [] 

    for e in exams:
        exams_timeline.append({
            'name': e.name,

            'slot_start': e.slot_creation_start.strftime('%Y-%m-%d %H:%M') if e.slot_creation_start else '—',
            'slot_end': e.slot_creation_end.strftime('%Y-%m-%d %H:%M') if e.slot_creation_end else '—',

            'booking_start': e.slot_booking_start.strftime('%Y-%m-%d %H:%M') if e.slot_booking_start else '—',
            'booking_end': e.slot_booking_end.strftime('%Y-%m-%d %H:%M') if e.slot_booking_end else '—'
        })

    return render_template('admin/timelines.html',
        slot_creation_open = slot_creation_open,
         booking_open = booking_open,
        slot_start_date = '',
        slot_end_date='',
         booking_start_date='',
        booking_end_date='',
        exams_timeline=exams_timeline)




@admin_bp.route('/timelines/slot_creation', methods=['POST'])
@login_required
def slot_creation():

    if current_user.role != 'admin': 

        flash('Access denied.', 'danger')  
        return redirect(url_for('auth.login'))

    is_open = Examination.query.filter_by(status='slot_creation').first() is not None
    if is_open:
        for e in Examination.query.filter_by(status='slot_creation').all():
            e.status = 'draft'
        flash('Slot creation closed for all active exams.', 'info')

    else:
        for e in Examination.query.all():


            if e.status in ('draft',  'closed'):
                e.status  = 'slot_creation'

        flash('Slot creation opened for examinations.', 'success')



    db.session.commit()
    return redirect(url_for('admin.timelines'))







@admin_bp.route('/timelines/booking_period', methods=['POST'])
@login_required
def booking_period():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')


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
