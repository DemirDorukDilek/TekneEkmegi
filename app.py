from flask import Flask, render_template, request, redirect, flash
import mysql.connector as sql
from werkzeug.security import generate_password_hash
from utils import *

app = Flask(__name__)
app.secret_key = '!@#$%^&*IJHGFr34hbtjyornkhofij4q39rfa$ojgk$ogvkmW<OP4gvjmpomdsj'

@app.route('/')
def index_get():
    return render_template('register.html')

@app.route('/post/sql/efendi_sign_in', methods=['POST'])
def signin_post():
    
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        telno = request.form['telno']
        email = request.form['email']
        hashed_password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql_query = read_file("sql/EfendiSignIn.sql")
            cursor.execute(sql_query, (name, surname, telno, make_null(email), hashed_password))
            conn.commit()
            flash('Kayıt başarıyla tamamlandı!', 'success')
        
        except sql.IntegrityError:
            flash('Bu e-posta veya telefon numarası zaten kayıtlı.', 'danger')
        except sql.Error as err:
            flash(f'Bir hata oluştu: {err}', 'danger')
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
            
        return redirect("/")

if __name__ == '__main__':
    app.run("0.0.0.0",3131)