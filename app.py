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
session_version = 1 if os.getenv("debug",False)=="True" else time.time() #TODO debug degistir
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,   # JS ile erişilemez
    SESSION_COOKIE_SECURE=True,      # Sadece HTTPS
    SESSION_COOKIE_SAMESITE="Lax",   # CSRF koruması
    PERMANENT_SESSION_LIFETIME=timedelta(days=30)  # 30 gün sonra sona erer
)

class TYPES:
    R = "restoran"
    E = "efendi"
    K = "kurye"


def check_session_validity():
    if not session.get("logged_in"):
        return {"valid": False,"reason": "not_logged_in","message": "Not Logged"}
    if session.get("version") != session_version:
        session.clear()
        return {"valid": False,"reason": "invalid_version","message": "Invalid Session"}
    login_time = session.get("login_time", 0)
    if time.time() - login_time > 30 * 86400:
        session.clear()
        return {"valid": False,"reason": "expired","message": "Expired Session"}
    return {"valid": True,"session_id": session.get("session_id"),"remaining_days": 30 - int((time.time() - login_time) / 86400)}

def login_required(logintype=TYPES.E):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            info = check_session_validity()
            if not info["valid"]:
                return info, 403
            if session.get("as","NULL") != logintype:
                info = {"valid": False,"reason": "invalid_type","message": "wrong User Type"}
                return info, 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def login(user_id,as_):
    session.clear()
    session["logged_in"] = True
    session["version"] = session_version
    session["login_time"] = time.time()
    session["user_id"] = user_id
    session["as"] = as_


@app.context_processor
def inject_navbar_adresler():
    navbar_adresler = []
    selected_adresName = session.get("selected_adresName")

    try:
        # sadece efendi kullanıcı için adres listesini navbar'a verelim
        if session.get("as") == TYPES.E and "user_id" in session:
            rows = sql_querry(
                "SELECT adresName FROM Adres WHERE efendiID = %s ORDER BY adresName",
                (session["user_id"],)
            ) or []

            # İlk adres varsa ve daha önce seçili adres yoksa, otomatik ilk adresi seç
            if rows and not selected_adresName:
                selected_adresName = rows[0][0]
                session["selected_adresName"] = selected_adresName

            # rows = [(adresName,), (adresName2,), ...] şeklinde kalsın
            navbar_adresler = rows

    except Exception:
        # Navbar yüzünden hiçbir sayfa patlamasın diye sessiz geçiyoruz
        pass

    return dict(
        navbar_adresler=navbar_adresler,
        navbar_selected_adresName=selected_adresName
    )

@app.route("/")
def index_get():
    if check_session_validity()["valid"]:
        return redirect("/HomePage")
    return redirect("/login")

@app.route("/HomePage")
@login_required(TYPES.E)
def HomePage_Get():
    user_id = session["user_id"]

    # Restoranlar (eski davranış aynen kalsın)
    restoranlar = sql_querry("sql/RestoranListele.sql", (user_id,)) or []

    # Seçili adres
    selected_name = session.get("selected_adresName")
    selected_adres = None
    if selected_name:
        rows = sql_querry(
            "SELECT adresName, il, ilce, mah, cd, binano, daireno "
            "FROM Adres WHERE efendiID = %s AND adresName = %s",
            (user_id, selected_name)
        ) or []
        if rows:
            selected_adres = rows[0]

    return render_template(
        "HomePage.html",
        restoranlar=restoranlar,
        selected_adres=selected_adres
    )

@app.route("/RestoranHomePage")
@login_required(TYPES.R)
def RestoranHomePage_get():
    return render_template("RestoranHomePage.html")

@app.route("/HomePage-Sepetbutton", methods=["POST"])
@login_required(TYPES.E)
def homepage_button():
    return redirect("/login")

@app.route("/profilim")
@login_required(TYPES.E)
def profilim_get():
    # İleride burada efendi bilgilerini DB'den çekebiliriz.
    return render_template("Profilim.html")


@app.route("/odemeYontemlerim")
@login_required(TYPES.E)
def odeme_yontemlerim_get():
    return render_template("OdemeYontemlerim.html")


@app.route("/gecmisSiparislerim")
@login_required(TYPES.E)
def gecmis_siparislerim_get():
    # İleride gerçek siparişleri buraya bağlarız
    return render_template("GecmisSiparislerim.html")


@app.route("/kuponlarim")
@login_required(TYPES.E)
def kuponlarim_get():
    # Sonra DB'den kupon listesi çekilebilir
    return render_template("Kuponlarim.html")


@app.route("/yardim")
@login_required(TYPES.E)
def yardim_get():
    return render_template("Yardim.html")


@app.route("/logout")
def logout_get():
    session.clear()
    flash("Çıkış yapıldı.", "success")
    return redirect("/login")

@app.route("/addAdress")
@login_required(TYPES.E)
def addAdress_get():
    return render_template("addAdress.html")

@app.route("/adreslerim")
@login_required(TYPES.E)
def adreslerim_get():
    user_id = session["user_id"]

    adresler = sql_querry(
        "SELECT adresName, il, ilce, mah, cd, binano, daireno FROM Adres WHERE efendiID = %s",
        (user_id,)
    ) or []

    selected_name = session.get("selected_adresName")

    return render_template("Adreslerim.html", adresler=adresler, selected_name=selected_name)

@app.route("/adres/sec", methods=["POST"])
@login_required(TYPES.E)
def adres_sec_post():
    user_id = session["user_id"]
    adres_name = request.form["adresName"]

    rows = sql_querry(
        "SELECT adresName FROM Adres WHERE efendiID = %s AND adresName = %s",
        (user_id, adres_name)
    ) or []

    if not rows:
        flash("Adres bulunamadı.", "danger")
    else:
        session["selected_adresName"] = adres_name
        flash(f"Seçili adres güncellendi: {adres_name}", "success")

    return redirect("/adreslerim")

@app.route("/adres/sil", methods=["POST"])
@login_required(TYPES.E)
def adres_sil_post():
    user_id = session["user_id"]
    adres_name = request.form["adresName"]

    try:
        sql_querry(
            "DELETE FROM Adres WHERE efendiID = %s AND adresName = %s",
            (user_id, adres_name)
        )
        flash("Adres silindi.", "success")
    except sql.Error as err:
        flash(f"Adres silinirken bir hata oluştu: {err}", "danger")

    return redirect("/adreslerim")

@app.route("/adres/duzenle", methods=["GET"])
@login_required(TYPES.E)
def adres_duzenle_get():
    user_id = session["user_id"]
    adres_name = request.args.get("adresName")

    rows = sql_querry(
        "SELECT adresName, il, ilce, mah, cd, binano, daireno FROM Adres WHERE efendiID = %s AND adresName = %s",
        (user_id, adres_name)
    ) or []

    if not rows:
        flash("Adres bulunamadı.", "danger")
        return redirect("/adreslerim")

    adres = rows[0]  # tuple

    return render_template("AdresDuzenle.html", adres=adres)

@app.route("/adres/duzenle", methods=["POST"])
@login_required(TYPES.E)
def adres_duzenle_post():
    user_id = session["user_id"]
    old_name = request.form["old_adresName"]

    def temizle(s):
        if s is None:
            return None
        return s.strip().strip("'").strip('"')

    new_name = temizle(request.form["name"])
    il = temizle(request.form["il"])
    ilce = temizle(request.form["ilce"])
    mahalle = temizle(request.form.get("Mahalle"))
    cadde = temizle(request.form.get("Cadde"))
    bina_no = temizle(request.form.get("binano"))
    daire_no = temizle(request.form.get("daireno"))

    try:
        sql_querry(
            "UPDATE Adres SET adresName=%s, il=%s, ilce=%s, mah=%s, cd=%s, binano=%s, daireno=%s "
            "WHERE efendiID=%s AND adresName=%s",
            (new_name, il, ilce, mahalle, cadde, bina_no, daire_no, user_id, old_name)
        )
        flash("Adres güncellendi.", "success")
    except sql.IntegrityError:
        flash("Bu isimde zaten bir adresiniz var. Lütfen farklı bir isim kullanın.", "danger")
    except sql.Error as err:
        flash(f"Adres güncellenirken bir hata oluştu: {err}", "danger")

    return redirect("/adreslerim")

@app.route("/addYemek")
@login_required(TYPES.R)
def addyemek_get():
    return render_template("addYemek.html")

@app.route("/login")
def login_get():
    return render_template("efendiLogin.html")

@app.route("/restoranLogin")
def restoranLogin_get():
    return render_template("RestoranLogin.html")

@app.route("/restoranRegister")
def restoranRegister_get():
    return render_template("RestoranRegister.html")

@app.route("/register")
def register_get():
    return render_template("register.html")

@app.route("/kuryeLogin")
def kuryelogin_get():
    return render_template("KuryeLogin.html")

@app.route("/kuryeRegister")
def kuryeregister_get():
    return render_template("kuryeRegister.html")

@app.route("/post/register", methods=["POST"])
def register_post():
    
    if request.method == "POST":
        name = request.form["name"]
        surname = request.form["surname"]
        telno = request.form["telno"]
        email = request.form["email"]
        hashed_password = generate_password_hash(request.form["password"], method="pbkdf2:sha256")

        try:
            sql_querry("sql/Login_Register/EfendiSignIn.sql",(name, surname, telno, make_null(email), hashed_password))
            flash("Kayıt başarıyla tamamlandı!", "success")
            return redirect("/login")

        except sql.IntegrityError:
            flash("Bu e-posta veya telefon numarası zaten kayıtlı.", "danger")
        except sql.Error as err:
            flash(f"Bir hata oluştu: {err}", "danger")
            
        return redirect("/register")

@app.route("/post/login", methods=["POST"])
def login_post():
    
    if request.method == "POST":
        identifier = request.form["identifier"]
        password = request.form["password"]

        try:
            user_data = sql_querry("sql/Login_Register/EfendiLogin.sql",(identifier, identifier))[0]
            if user_data is None:
                flash("Telno/Email yanlış", "danger")
            elif not check_password_hash(user_data[5],password):
                flash("Şifre yanlış", "danger")
            else:
                login(user_data[0],"efendi")
                return redirect("/HomePage")

        except sql.Error as err:
            flash(f"Bir hata oluştu: {err}", "danger")
            
        return redirect("/login")

@app.route("/post/RestoranLogin", methods=["POST"])
def RestoranLogin_post():

    if request.method == "POST":
        identifier = request.form["identifier"]
        password = request.form["password"]

        try:
            user_data = sql_querry("sql/Login_Register/RestoranLogin.sql",(identifier,))[0]
            if user_data is None:
                flash("Telno yanlış", "danger")
            elif not check_password_hash(user_data[5],password):
                flash("Şifre yanlış", "danger")
            else:
                login(user_data[0],"restoran")
                return redirect("/RestoranHomePage") # TODO
        except sql.Error as err:
            flash(f"Bir hata oluştu: {err}", "danger")

        return redirect("/restoranLogin")

@app.route("/post/RestoranRegister", methods=["POST"])
def RestoranRegister_post():
    
    if request.method == "POST":
        name = request.form["name"]
        telno = request.form["telno"]
        adres = request.form["adress"]
        minsepet = request.form["Minsepet"]
        latitude = request.form["latitude"]
        longitude = request.form["longitude"]
        hashed_password = generate_password_hash(request.form["password"], method="pbkdf2:sha256")

        try:
            sql_querry("sql/Login_Register/RestoranRegister.sql",(name, telno, adres, minsepet,hashed_password, latitude,longitude))
            flash("Kayıt başarıyla tamamlandı!", "success")
            return redirect("/restoranLogin")
        
        except sql.IntegrityError:
            flash("Bu e-posta veya telefon numarası zaten kayıtlı.", "danger")
        except sql.Error as err:
            flash(f"Bir hata oluştu: {err}", "danger")

        return redirect("/restoranRegister")

@app.route("/post/kuryeRegister", methods=["POST"])
def kuryeregister_post():
    
    if request.method == "POST":
        name = request.form["name"]
        surname = request.form["surname"]
        telno = request.form["telno"]
        email = request.form["email"]
        hashed_password = generate_password_hash(request.form["password"], method="pbkdf2:sha256")

        try:
            sql_querry("sql/Login_Register/KuryeRegister.sql",(name, surname, telno, make_null(email), hashed_password))
            flash("Kayıt başarıyla tamamlandı!", "success")
            return redirect("/kuryeLogin")

        except sql.IntegrityError:
            flash("Bu e-posta veya telefon numarası zaten kayıtlı.", "danger")
        except sql.Error as err:
            flash(f"Bir hata oluştu: {err}", "danger")
            
        return redirect("/kuryeRegister")

@app.route("/post/kuryeLogin", methods=["POST"])
def kuryelogin_post():
    
    if request.method == "POST":
        identifier = request.form["identifier"]
        password = request.form["password"]

        try:
            user_data = sql_querry("sql/Login_Register/KuryeLogin.sql",(identifier, identifier))[0]
            if user_data is None:
                flash("Telno/Email yanlış", "danger")
            elif not check_password_hash(user_data[5],password):
                flash("Şifre yanlış", "danger")
            else:
                login(user_data[0],"kurye")
                return redirect("/KuryeHomePage")

        except sql.Error as err:
            flash(f"Bir hata oluştu: {err}", "danger")
            
        return redirect("/kuryeLogin")






@app.route("/post/efendiAddAdress", methods=["POST"])
@login_required(TYPES.E)
def efendiAddAdress_post():
    if request.method == "POST":
        
        try:
            adres_adi = request.form["name"]
            il = request.form["il"]
            ilce = request.form["ilce"]
            mahalle = request.form.get("Mahalle")
            cadde = request.form.get("Cadde")
            bina_no = request.form.get("binano")
            daire_no = request.form.get("daireno")
            latitude = float(request.form.get("latitude"))
            longitude = float(request.form.get("longitude"))
            user_id = session.get("user_id")

            sql_querry("sql/efendiAddAdress.sql", (user_id, adres_adi, il, ilce, mahalle, cadde, bina_no, daire_no, latitude, longitude))

        # Eğer daha önce seçili adres yoksa, bu yeni eklenen adresi varsayılan seçili yap
            if not session.get("selected_adresName"):
                session["selected_adresName"] = adres_adi
                flash("Adres başarıyla eklendi!", "success")
                return redirect("/HomePage")

        except sql.IntergrityError:
            flash("Bu isimde bir adres zaten kayıtlı. Lütfen farklı bir adres adı girin.", "danger")
            return redirect("/addAdress");

        except sql.Error as err:
            flash(f"Bir hata oluştu: {err}", "danger")
            return redirect("/addAdress");
    
    return redirect("/addAdress")


@app.route("/post/restoranAddYemek", methods=["POST"])
@login_required(TYPES.R)
def addYemek_post():
    if request.method == "POST":
        try:
            name = request.form["name"]
            price = float(request.form["price"])
            sql_querry("sql/restoran/addYemek.sql",(name,price,session.get("user_id")))
            return redirect("/RestoranHomePage")
        except sql.Error as err:
            flash(f"Bir hata oluştu: {err}", "danger")

    return redirect("/addYemek")
    
if __name__ == "__main__":
    app.run("0.0.0.0",3131)