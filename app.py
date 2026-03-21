from flask import Flask
from extensions import db, login_manager
from routes.auth_routes import auth_bp
from routes.main_routes import main_bp
from routes.ai_routes import ai_bp
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'drowzyai-secret-key-2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(ai_bp, url_prefix='/ai')

    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, threaded=True)