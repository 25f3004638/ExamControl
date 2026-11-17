from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

examiner_bp = Blueprint('examiner', __name__)


@examiner_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'examiner':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('examiner/dashboard.html')
