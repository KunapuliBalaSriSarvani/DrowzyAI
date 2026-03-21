from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models.user import User, AlertLog
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        total_logs   = AlertLog.query.count()
        drowsy_logs  = AlertLog.query.filter_by(alert_type='DROWSY').count()
        yawn_logs    = AlertLog.query.filter_by(alert_type='YAWN').count()
        normal_logs  = AlertLog.query.filter_by(alert_type='NORMAL').count()
        recent_logs  = AlertLog.query.order_by(AlertLog.timestamp.desc()).limit(10).all()
        total_users  = User.query.count()
        week_ago     = datetime.utcnow() - timedelta(days=7)
        weekly = db.session.query(
            func.date(AlertLog.timestamp).label('date'),
            func.count(AlertLog.id).label('count')
        ).filter(AlertLog.timestamp >= week_ago)\
         .group_by(func.date(AlertLog.timestamp)).all()
        return render_template('dashboard.html',
            total_logs=total_logs, drowsy_logs=drowsy_logs,
            yawn_logs=yawn_logs, normal_logs=normal_logs,
            recent_logs=recent_logs, total_users=total_users,
            weekly=weekly, is_admin=True)
    else:
        total_logs   = AlertLog.query.filter_by(user_id=current_user.id).count()
        drowsy_logs  = AlertLog.query.filter_by(user_id=current_user.id, alert_type='DROWSY').count()
        yawn_logs    = AlertLog.query.filter_by(user_id=current_user.id, alert_type='YAWN').count()
        normal_logs  = AlertLog.query.filter_by(user_id=current_user.id, alert_type='NORMAL').count()
        recent_logs  = AlertLog.query.filter_by(user_id=current_user.id)\
                        .order_by(AlertLog.timestamp.desc()).limit(10).all()
        week_ago     = datetime.utcnow() - timedelta(days=7)
        weekly = db.session.query(
            func.date(AlertLog.timestamp).label('date'),
            func.count(AlertLog.id).label('count')
        ).filter(
            AlertLog.user_id == current_user.id,
            AlertLog.timestamp >= week_ago
        ).group_by(func.date(AlertLog.timestamp)).all()
        return render_template('dashboard.html',
            total_logs=total_logs, drowsy_logs=drowsy_logs,
            yawn_logs=yawn_logs, normal_logs=normal_logs,
            recent_logs=recent_logs, total_users=None,
            weekly=weekly, is_admin=False)


@main_bp.route('/webcam')
@login_required
def webcam():
    return render_template('webcam.html')


@main_bp.route('/upload')
@login_required
def upload():
    return render_template('upload.html')


@main_bp.route('/history')
@login_required
def history():
    if current_user.role == 'admin':
        logs = AlertLog.query.order_by(AlertLog.timestamp.desc()).all()
    else:
        logs = AlertLog.query.filter_by(user_id=current_user.id)\
                .order_by(AlertLog.timestamp.desc()).all()
    return render_template('history.html', logs=logs)


@main_bp.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        return redirect(url_for('main.dashboard'))
    users        = User.query.all()
    all_logs     = AlertLog.query.order_by(AlertLog.timestamp.desc()).limit(50).all()
    total_users  = User.query.count()
    total_alerts = AlertLog.query.count()
    drowsy_total = AlertLog.query.filter_by(alert_type='DROWSY').count()
    return render_template('admin.html',
        users=users, all_logs=all_logs,
        total_users=total_users, total_alerts=total_alerts,
        drowsy_total=drowsy_total)