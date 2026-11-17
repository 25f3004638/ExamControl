from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

student_bp = Blueprint('student', __name__)


@student_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('student/dashboard.html')
