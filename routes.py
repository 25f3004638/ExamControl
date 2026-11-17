from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from models.models import db, User, Examiner, Student, Course, Department

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
            user_id       = new_user.id,
            employee_id   = employee_id,
            name          = name,
            phone         = phone,
            department_id = int(department_id) if department_id else None,
            status        = 'pending'   # admin must approve
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
#  ADMIN BLUEPRINT - stub routes for sidebar links
#  (these will be filled in later)
# ─────────────────────────────────────────────

@admin_bp.route('/courses')
@login_required
def courses():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('admin/courses.html')


@admin_bp.route('/examinations')
@login_required
def examinations():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('admin/examinations.html')


@admin_bp.route('/rubrics')
@login_required
def rubrics():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('admin/rubrics.html')


@admin_bp.route('/examiners')
@login_required
def examiners():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('admin/examiners.html')


@admin_bp.route('/students')
@login_required
def students():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('admin/students.html')


@admin_bp.route('/slots')
@login_required
def slots():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('admin/slots.html')


@admin_bp.route('/bookings')
@login_required
def bookings():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('admin/bookings.html')


@admin_bp.route('/timelines')
@login_required
def timelines():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('admin/timelines.html')
