# app/auth/routes.py

import bcrypt
from ..db import get_db_connection, release_db_connection # db.py က functions တွေကို import လုပ်ပါ
from flask import Blueprint, request, jsonify, session
from google.oauth2 import id_token # User က "Sign in with Google" ကို နှိပ်လိုက်ရင် Google ကနေ ပြန်ပို့ပေးလိုက်တဲ့ token က မှန်ကန်ရဲ့လားဆိုတာ စစ်ဆေးဖို့ Google ရဲ့ library တွေပါ။
from google.auth.transport import requests as google_requests
from flask import session #User တစ်ယောက် login ဝင်ပြီးသွားရင်၊ သူဘယ်သူလဲဆိုတာ မှတ်ထားဖို့ (logged-in state ကို ထိန်းသိမ်းဖို့) သုံးပါတယ်။
from flask_mail import Message
from .. import mail # __init__.py ထဲက mail object ကို import လုပ်ပါ
import uuid
import secrets
from datetime import datetime, timedelta
from ..db import make_dict_factory # db.py ထဲက make_dict_factory ကို import လုပ်ပါ

# 1. 'auth' ဆိုတဲ့ Blueprint object တစ်ခုကို တည်ဆောက်ခြင်း
auth_bp = Blueprint('auth', __name__)

GOOGLE_CLIENT_ID = "749824701715-rbude5i5p8qj0g35vdctmjkb3ea45n1i.apps.googleusercontent.com"
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    email = data['email']
    password = data['password'].encode('utf-8')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE username = :username OR email = :email", username=username, email=email)
        if cursor.fetchone():
            return jsonify({'message': 'Username or email already exists'}), 409

        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (:username, :email, :password)",
            username=username, email=email, password=hashed_password.decode('utf-8')
        )
        connection.commit()
        return jsonify({'message': 'User registered successfully!'})
    finally:
        cursor.close()
        release_db_connection(connection)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password'].encode('utf-8')

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE email = :email", email=email)
        cursor.rowfactory = make_dict_factory(cursor)
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(password, user['password'].encode('utf-8')):
            session['user_id'] = user['id'] 
            return jsonify({'message': 'Login successful!', 'username': user['username'], email: user['email']})
        else:
            return jsonify({'message': 'Invalid email or password'}), 401
    finally:
        cursor.close()
        release_db_connection(connection)

@auth_bp.route('/google-login', methods=['POST'])
def google_login():
    data = request.get_json()
    token = data['credential']
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)
        email = idinfo['email']
        username = idinfo.get('name', email.split('@')[0])
        
        cursor.execute("SELECT * FROM users WHERE email = :email", email=email)
        # --- FIX: Dictionary အဖြစ်ပြောင်းဖို့ rowfactory ထည့်ပါ ---
        cursor.rowfactory = make_dict_factory(cursor)
        user = cursor.fetchone()
        
        # User မရှိသေးရင် အသစ်ဆောက်ပါ
        if not user:
            random_password = str(uuid.uuid4()).encode('utf-8')
            hashed_password = bcrypt.hashpw(random_password, bcrypt.gensalt())
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (:username, :email, :password)",
                username=username, email=email, password=hashed_password.decode('utf-8')
            )
            connection.commit()
            # အသစ်ဆောက်ပြီး user ကို ပြန်ရှာပါ
            cursor.execute("SELECT * FROM users WHERE email = :email", email=email)
            cursor.rowfactory = make_dict_factory(cursor)
            user = cursor.fetchone()

        # ---> ✅ အရေးကြီး: Session ကို ဒီနေရာမှာ သတ်မှတ်ပေးရပါမယ် <---
        if user:
            session['user_id'] = user['id']
            return jsonify({'message': 'Google login successful!', 'username': user['username'], 'email': user['email']})
        else:
            return jsonify({'message': 'Failed to create or find user after Google auth.'}), 500

    except ValueError:
        return jsonify({'message': 'Invalid Google token'}), 401
    finally:
        cursor.close()
        release_db_connection(connection)

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data['email']
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE email = :email", email=email)
        if not cursor.fetchone():
            return jsonify({'message': 'If an account with that email exists, a password reset link has been sent.'})

        token = secrets.token_urlsafe(32)
        expiry = datetime.utcnow() + timedelta(hours=1)
        
        cursor.execute("UPDATE users SET reset_token = :token, reset_token_expiration = :expiry WHERE email = :email",
                       token=token, expiry=expiry, email=email)
        connection.commit()
        
        reset_url = f"http://localhost:5173/reset-password/{token}"
        msg = Message("Password Reset Request", sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f"To reset your password, please click the following link: {reset_url}"
        mail.send(msg)
        return jsonify({'message': 'If an account with that email exists, a password reset link has been sent.'})
    except Exception as e:
        print(str(e))
        return jsonify({'message': 'Could not send email. Please try again later.'}), 500
    finally:
        cursor.close()
        release_db_connection(connection)

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data['token']
    new_password = data['password'].encode('utf-8')

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE reset_token = :token", token=token)
        cursor.rowfactory = make_dict_factory(cursor)
        user = cursor.fetchone()

        if not user or user['reset_token_expiration'].replace(tzinfo=None) < datetime.utcnow():
            return jsonify({'message': 'Invalid or expired token.'}), 400
            
        hashed_password = bcrypt.hashpw(new_password, bcrypt.gensalt())
        cursor.execute(
            "UPDATE users SET password = :password, reset_token = NULL, reset_token_expiration = NULL WHERE id = :id",
            password=hashed_password.decode('utf-8'), id=user['id']
        )
        connection.commit()
        return jsonify({'message': 'Password has been reset successfully.'})
    finally:
        cursor.close()
        release_db_connection(connection)
