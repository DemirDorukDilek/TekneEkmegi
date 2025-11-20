from datetime import timedelta
from functools import wraps
import secrets
import time
from flask import Flask, render_template, request, redirect, flash,session
import mysql.connector as sql
from werkzeug.security import generate_password_hash,check_password_hash
from utils import *
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
session_version = 1 if os.getenv("debug",False) else time.time()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,   # JS ile erişilemez
    SESSION_COOKIE_SECURE=True,      # Sadece HTTPS
    SESSION_COOKIE_SAMESITE='Lax',   # CSRF koruması
    PERMANENT_SESSION_LIFETIME=timedelta(days=30)  # 30 gün sonra sona erer
)

def check_session_validity():
    if not session.get('logged_in'):
        return {"valid": False,"reason": "not_logged_in","message": "Not Logged"}
    if session.get('version') != session_version:
        session.clear()
        return {"valid": False,"reason": "invalid_version","message": "Invalid Session"}
    login_time = session.get('login_time', 0)
    if time.time() - login_time > 30 * 86400:
        session.clear()
        return {"valid": False,"reason": "expired","message": "Expired Session"}
    return {"valid": True,"session_id": session.get('session_id'),"remaining_days": 30 - int((time.time() - login_time) / 86400)}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        info = check_session_validity()
        if not info["valid"]:
            return info, 403
        return f(*args, **kwargs)
    return decorated_function

def login(user_id):
    session["logged_in"] = True
    session["version"] = session_version
    session["login_time"] = time.time()
    session["user_id"] = user_id
    





@app.route("/")
def index_get():
    return redirect("/login")

@app.route("/HomePage")
@login_required
def HomePage_Get():
    return render_template('HomePage.html')

@app.route("/HomePage-Sepetbutton", methods=["POST"])
@login_required
def homepage_button():
    return redirect("/login")


@app.route("/addAdress")
@login_required
def addAdress_get():
    return render_template('addAdress.html')

@app.route('/login')
def login_get():
    return render_template('login.html')

@app.route('/register')
def register_get():
    return render_template('register.html')

@app.route('/post/register', methods=['POST'])
def register_post():
    
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        telno = request.form['telno']
        email = request.form['email']
        print("email",email)
        print("password",request.form['password'])
        hashed_password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        print("hashed_password",hashed_password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql_query = read_file("sql/EfendiSignIn.sql")
            cursor.execute(sql_query, (name, surname, telno, make_null(email), hashed_password))
            conn.commit()
            flash('Kayıt başarıyla tamamlandı!', 'success')
            return redirect("/login")
        
        except sql.IntegrityError:
            flash('Bu e-posta veya telefon numarası zaten kayıtlı.', 'danger')
        except sql.Error as err:
            flash(f'Bir hata oluştu: {err}', 'danger')
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
            
        return redirect("/register")

@app.route('/post/login', methods=['POST'])
def login_post():
    
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql_query = read_file("sql/EfendiLogin.sql")
            cursor.execute(sql_query, (identifier, identifier))
            user_data = cursor.fetchone()
            conn.commit()
            if user_data is None:
                flash('Telno/Email yanlış', 'danger')
            elif not check_password_hash(user_data[5],password):
                flash('Şifre yanlış', 'danger')
            else:
                login(user_data[0])
                return redirect("/HomePage")
                
            
        except sql.Error as err:
            flash(f'Bir hata oluştu: {err}', 'danger')
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
            
        return redirect("/login")

@app.route('/post/efendiAddAdress', methods=['POST'])
@login_required
def efendiAddAdress_post():
    if request.method == 'POST':
        
        try:
            adres_adi = request.form['name']
            il = request.form['il']
            ilce = request.form['ilce']
            mahalle = request.form.get('Mahalle')
            cadde = request.form.get('Cadde')
            bina_no = request.form.get('binano')
            daire_no = request.form.get('daireno')
            latitude = float(request.form.get('latitude'))
            longitude = float(request.form.get('longitude'))
            user_id = session.get('user_id')

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(read_file("sql/efendiAddAdress.sql"), (user_id, adres_adi, il,ilce, mahalle, cadde, bina_no, daire_no, latitude, longitude))
            conn.commit()
            print(f"User ID: {user_id} yeni adres ekliyor:")
            print(f"Adres Adı: {adres_adi}, İl: {il}, İlçe: {ilce}")
            print(f"Enlem: {latitude}, Boylam: {longitude}")
            flash('Adres başarıyla eklendi!', 'success')
            return redirect('/HomePage')
    
        except sql.Error as err:
            flash(f'Bir hata oluştu: {err}', 'danger')
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
    
    return redirect('/addAdress')


if __name__ == '__main__':
    app.run("0.0.0.0",3131)