from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.user import User, AlertLog
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    week_ago = datetime.utcnow() - timedelta(days=7)

    if current_user.role == 'admin':
        # Admin: system-wide stats
        total_logs   = AlertLog.query.count()
        drowsy_logs  = AlertLog.query.filter_by(alert_type='DROWSY').count()
        yawn_logs    = AlertLog.query.filter_by(alert_type='YAWN').count()
        recent_logs  = AlertLog.query.order_by(AlertLog.timestamp.desc()).limit(10).all()
        all_users_count  = User.query.count()
        all_alerts_count = total_logs
        all_drowsy_count = drowsy_logs
        students_count   = User.query.filter_by(role='student').count()

        rows = db.session.query(
            func.date(AlertLog.timestamp).label('date'),
            func.count(AlertLog.id).label('count')
        ).filter(AlertLog.timestamp >= week_ago)\
         .group_by(func.date(AlertLog.timestamp)).all()

        users = User.query.all()
        user_stats = []
        for u in users:
            user_stats.append({
                'user':   u,
                'total':  AlertLog.query.filter_by(user_id=u.id).count(),
                'drowsy': AlertLog.query.filter_by(user_id=u.id, alert_type='DROWSY').count(),
                'yawn':   AlertLog.query.filter_by(user_id=u.id, alert_type='YAWN').count(),
            })
    else:
        # Student: own stats only
        total_logs   = AlertLog.query.filter_by(user_id=current_user.id).count()
        drowsy_logs  = AlertLog.query.filter_by(user_id=current_user.id, alert_type='DROWSY').count()
        yawn_logs    = AlertLog.query.filter_by(user_id=current_user.id, alert_type='YAWN').count()
        recent_logs  = AlertLog.query.filter_by(user_id=current_user.id)\
                         .order_by(AlertLog.timestamp.desc()).limit(10).all()
        all_users_count  = 0
        all_alerts_count = 0
        all_drowsy_count = 0
        students_count   = 0
        user_stats       = []

        rows = db.session.query(
            func.date(AlertLog.timestamp).label('date'),
            func.count(AlertLog.id).label('count')
        ).filter(
            AlertLog.user_id == current_user.id,
            AlertLog.timestamp >= week_ago
        ).group_by(func.date(AlertLog.timestamp)).all()

    weekly = [{'date': str(r.date), 'count': int(r.count)} for r in rows]

    return render_template('dashboard.html',
        total_logs=total_logs,
        drowsy_logs=drowsy_logs,
        yawn_logs=yawn_logs,
        recent_logs=recent_logs,
        weekly=weekly,
        all_users_count=all_users_count,
        all_alerts_count=all_alerts_count,
        all_drowsy_count=all_drowsy_count,
        students_count=students_count,
        user_stats=user_stats
    )

@main_bp.route('/webcam')
@login_required
def webcam():
    # Admin cannot access webcam monitor
    if current_user.role == 'admin':
        flash('Admins do not have webcam monitoring access.', 'error')
        return redirect(url_for('main.dashboard'))
    return render_template('webcam.html')

@main_bp.route('/upload')
@login_required
def upload():
    # Admin cannot access upload analysis
    if current_user.role == 'admin':
        flash('Admins do not have file analysis access.', 'error')
        return redirect(url_for('main.dashboard'))
    return render_template('upload.html')

@main_bp.route('/history')
@login_required
def history():
    # Student sees only own history
    if current_user.role == 'admin':
        return redirect(url_for('main.all_history'))
    logs = AlertLog.query.filter_by(user_id=current_user.id)\
            .order_by(AlertLog.timestamp.desc()).all()
    return render_template('history.html', logs=logs)

@main_bp.route('/all_history')
@login_required
def all_history():
    # Admin only — sees ALL users' history
    if current_user.role != 'admin':
        return redirect(url_for('main.history'))
    logs = AlertLog.query.order_by(AlertLog.timestamp.desc()).all()
    return render_template('all_history.html', logs=logs)

@main_bp.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    users        = User.query.all()
    all_logs     = AlertLog.query.order_by(AlertLog.timestamp.desc()).limit(50).all()
    total_users  = User.query.count()
    total_alerts = AlertLog.query.count()
    drowsy_total = AlertLog.query.filter_by(alert_type='DROWSY').count()
    yawn_total   = AlertLog.query.filter_by(alert_type='YAWN').count()
    user_stats   = []
    for u in users:
        user_stats.append({
            'user':   u,
            'total':  AlertLog.query.filter_by(user_id=u.id).count(),
            'drowsy': AlertLog.query.filter_by(user_id=u.id, alert_type='DROWSY').count(),
            'yawn':   AlertLog.query.filter_by(user_id=u.id, alert_type='YAWN').count(),
        })
    return render_template('admin.html',
        users=users, all_logs=all_logs,
        total_users=total_users, total_alerts=total_alerts,
        drowsy_total=drowsy_total, yawn_total=yawn_total,
        user_stats=user_stats
    )

@main_bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    if current_user.id == user_id:
        flash('Cannot delete yourself!', 'error')
        return redirect(url_for('main.admin'))
    user = User.query.get_or_404(user_id)
    # Delete all logs first
    AlertLog.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.name} deleted successfully.', 'success')
    return redirect(url_for('main.admin'))

@main_bp.route('/admin/clear_logs/<int:user_id>', methods=['POST'])
@login_required
def clear_logs(user_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    AlertLog.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    flash('User logs cleared.', 'success')
    return redirect(url_for('main.admin'))