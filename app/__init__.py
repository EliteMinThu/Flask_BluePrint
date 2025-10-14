# app/__init__.py

from flask import Flask
from flask_cors import CORS
from flask_mail import Mail
from .db import init_pool # db.py ထဲက pool ကို import လုပ်မယ်


mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # --- SECTION 2: APP CONFIGURATION ---
    # app.py ထဲက config အားလုံးကို ဒီကိုရွှေ့လာပါ
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True
    app.secret_key = 'minthuyein007'
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = 'your_gmail_address@gmail.com'
    app.config['MAIL_PASSWORD'] = 'your_16_digit_app_password' 
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    
    # Initialize extensions
    CORS(app, supports_credentials=True, resources={r"/*": {"origins": ["http://localhost:5173"]}})
    mail.init_app(app)
    init_pool() # Database pool ကို စတင်ပါ
    
    # --- Blueprints တွေကို Register လုပ်ခြင်း ---
    from .auth.routes import auth_bp
    from .notes.routes import notes_bp
    
    # url_prefix နဲ့ API endpoint တွေကို ပိုရှင်းအောင်လုပ်နိုင်ပါတယ်
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(notes_bp, url_prefix='/api/notes')

    return app