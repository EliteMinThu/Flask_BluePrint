# app/__init__.py

from flask import Flask
from flask_cors import CORS
from flask_mail import Mail
from .db import init_pool 


mail = Mail()

def create_app():
    app = Flask(__name__)
    
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True
    app.secret_key = 'minthuyein007'
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = 'your_gmail_address@gmail.com'
    app.config['MAIL_PASSWORD'] = 'your_16_digit_app_password' 
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    
    CORS(app, supports_credentials=True, resources={r"/*": {"origins": ["http://localhost:5173"]}})
    mail.init_app(app)
    init_pool() 
    
    from .auth.routes import auth_bp
    from .notes.routes import notes_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(notes_bp, url_prefix='/api/notes')

    return app