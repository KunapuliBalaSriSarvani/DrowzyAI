from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from extensions import db
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student')

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')

        user = User(name=name, email=email, role=role)
        user.set_password(password)

        face_file = request.files.get('face_image')
        if face_file and face_file.filename:
            upload_dir = os.path.join(current_app.root_path, 'uploads', 'faces')
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"{email.replace('@','_').replace('.','_')}_face.jpg"
            filepath = os.path.join(upload_dir, filename)
            face_file.save(filepath)
            user.face_image = f"uploads/faces/{filename}"

        db.session.add(user)
        db.session.commit()

        try:
            from ai.face_recognition import train_faces
            train_faces()
            user.face_trained = True
            db.session.commit()
        except Exception as e:
            print(f"Training warning: {e}")

        flash('Account created! Please login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))