from datetime import timedelta
from functools import wraps
import secrets
import time
import traceback
import threading
from flask import Flask, render_template, request, redirect, flash, session,abort
import pyodbc
from werkzeug.security import generate_password_hash, check_password_hash
from utils import *
import os
import numpy as np

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
session_version = 1 if os.getenv("debug", False) == "True" else time.time()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,  # Development için False, HTTPS kullanıyorsan True yap
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=30)
)

REF_LAT = 39.92500
REF_LON = 32.83694


class TYPES:
    R = "restoran"
    E = "efendi"
    K = "kurye"


def banka_islemi_gerceklestir(*args):
    time.sleep(2)
    return True


def otomatik_siparis_iptal(sparisNo, efendiID):
    time.sleep(60)

    try:
        durum_result = sql_querry(
            "SELECT durum FROM sparis WHERE sparisNo = ?",
            (sparisNo,)
        )

        if durum_result and durum_result[0][0] == "Get":
            sql_querry(
                "UPDATE sparis SET durum = ? WHERE sparisNo = ?",
                ("Cancelled", sparisNo)
            )
            print(f"Sipariş {sparisNo} 60 saniye içinde kabul edilmediği için iptal edildi.")

            sql_querry(
                "UPDATE nakitOdeme SET ParaTeslimAlindi = 0 WHERE sparisNo = ?",
                (sparisNo,)
            )
            sql_querry(
                "UPDATE krediKartiOdeme SET ParaTeslimAlindi = 0 WHERE sparisNo = ?",
                (sparisNo,)
            )

    except Exception as e:
        print(f"Otomatik iptal hatası (Sipariş {sparisNo}): {e}")
        traceback.print_exc()


def check_session_validity():
    if not session.get("logged_in"):
        return {"valid": False, "reason": "not_logged_in", "message": "Not Logged"}
    if session.get("version") != session_version:
        session.clear()
        return {"valid": False, "reason": "invalid_version", "message": "Invalid Session"}
    login_time = session.get("login_time", 0)
    if time.time() - login_time > 30 * 86400:
        session.clear()
        return {"valid": False, "reason": "expired", "message": "Expired Session"}
    return {"valid": True, "session_id": session.get("session_id"), 
            "remaining_days": 30 - int((time.time() - login_time) / 86400)}


def login_required(logintype=TYPES.E):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            info = check_session_validity()
            if not info["valid"]:
                return abort(403, info)
            if session.get("as", "NULL") != logintype:
                info = {"valid": False, "reason": "invalid_type", "message": "wrong User Type"}
                return abort(403, info)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def login(user_id, as_):
    session.clear()
    session["logged_in"] = True
    session["version"] = session_version
    session["login_time"] = time.time()
    session["user_id"] = user_id
    session["as"] = as_
    rows = sql_querry("SELECT adresName FROM Adres WHERE efendiID = ? ORDER BY adresName",(session["user_id"],)) or []
    if rows and not session.get("selected_adresName",None):
        selected_adresName = rows[0][0]
        session["selected_adresName"] = selected_adresName


@app.context_processor
def inject_navbar_adresler():
    navbar_adresler = []
    selected_adresName = session.get("selected_adresName")

    try:
        if session.get("as") == TYPES.E and "user_id" in session:
            rows = sql_querry(
                "SELECT adresName FROM Adres WHERE efendiID = ? ORDER BY adresName",
                (session["user_id"],)
            ) or []

            if rows and not selected_adresName:
                selected_adresName = rows[0][0]
                session["selected_adresName"] = selected_adresName

            navbar_adresler = rows

    except Exception:
        pass

    return dict(
        navbar_adresler=navbar_adresler,
        navbar_selected_adresName=selected_adresName
    )


# ============================================
# ANA SAYFA VE YÖNLENDİRMELER
# ============================================

INDEX_MAP = {TYPES.E:["/login","/HomePage"],TYPES.R:["restoranLogin","/RestoranHomePage"], TYPES.K:["/kuryeLogin","/KuryeHomePage"]}
@app.route("/")
def index_get():
    as_ = session.get("as",TYPES.E)
    valid = 1 if check_session_validity()["valid"] else 0
    return redirect(INDEX_MAP[as_][valid])
    
    


@app.route("/HomePage")
@login_required(TYPES.E)
def HomePage_Get():
    user_id = session["user_id"]
    selected_adres = session.get("selected_adresName")
    restoranlar = sql_querry("sql/RestoranListele.sql", (user_id,selected_adres)) or []
    restoranlar = list(map(lambda x: [x[0], x[1], x[2]**0.5, x[3]], restoranlar))

    selected_name = session.get("selected_adresName")
    selected_adres = None
    if selected_name:
        rows = sql_querry(
            "SELECT adresName, il, ilce, mah, cd, binano, daireno "
            "FROM Adres WHERE efendiID = ? AND adresName = ?",
            (user_id, selected_name)
        ) or []
        if rows:
            selected_adres = rows[0]

    # İptal edilen siparişleri kontrol et
    iptal_siparisler = sql_querry(
        "SELECT sparisNo FROM sparis WHERE efendiID = ? AND durum = 'Cancelled' ORDER BY sparisNo DESC LIMIT 1",
        (user_id,)
    )
    if iptal_siparisler:
        flash(f"Siparişiniz (No: {iptal_siparisler[0][0]}) 60 saniye içinde kurye tarafından kabul edilmediği için iptal edildi. Para iadesi yapılacaktır.", "warning")
        # İptal durumunu görüldü olarak işaretle (tekrar göstermemek için)
        sql_querry(
            "UPDATE sparis SET durum = 'CancelledSeen' WHERE sparisNo = ?",
            (iptal_siparisler[0][0],)
        )

    return render_template("HomePage.html",restoranlar=restoranlar,selected_adres=selected_adres)

@app.route('/restoranFiltre', methods=['POST'])
def restoran_filtre():
    user_id = session["user_id"]
    data = request.get_json()
    filitre = (data.get('filitre',"")).strip()
    selected_adres = session.get("selected_adresName")
    if filitre:
        restoranlar = sql_querry("sql/RestoranListele2.sql", (user_id,selected_adres,f"%{filitre}%")) or []
    else:
        restoranlar = sql_querry("sql/RestoranListele.sql", (user_id,selected_adres)) or []
    restoranlar = list(map(lambda x: [x[0], x[1], x[2]**0.5, x[3]], restoranlar))

    return render_template("partials/restoran_list.html", restoranlar=restoranlar)

@app.route("/RestoranHomePage")
@login_required(TYPES.R)
def RestoranHomePage_get():
    restoranID = session.get("user_id")
    yemekler = sql_querry("sql/restoran/YemekleriListele.sql", (restoranID,))
    return render_template("RestoranHomePage.html", yemekler=yemekler)

@app.route("/restoranProfil", methods=["GET", "POST"])
@login_required(TYPES.R)
def restoran_profil():
    restoran_id = session.get("user_id")

    conn = get_db_connection()
    cur = conn.cursor()

    # PROFIL GÜNCELLEME
    if request.method == "POST":
        name = request.form.get("name")
        telno = request.form.get("telno")
        adress_form = request.form.get("adress")  # formdaki ismi aynen okuyoruz
        Minsepet = request.form.get("Minsepet")

        cur.execute(
            """
            UPDATE restoran
            SET name=?,
                telno=?,
                adres=?,
                minsepettutari=?
            WHERE ID=?
            """,
            (name, telno, adress_form, Minsepet, restoran_id),
        )
        conn.commit()
        flash("Restoran profilin güncellendi.", "success")

    # MEVCUT BILGILER
    cur.execute(
        """
        SELECT ID, name, telno, adres, minsepettutari
        FROM restoran
        WHERE ID=?
        """,
        (restoran_id,),
    )
    restoran = cur.fetchone()

    conn.close()
    return render_template("restoranProfil.html", restoran=restoran)




@app.route("/restoranSiparisler")
@login_required(TYPES.R)
def restoran_siparisler():
    restoranID = session.get("user_id")
    siparisler = sql_querry("sql/restoran/SiparisleriGetir.sql", (restoranID,)) or []

    # Her sipariş için detayları al
    siparisler_detayli = []
    for siparis in siparisler:
        siparis_no = siparis[0]
        detaylar = sql_querry("sql/restoran/SiparisDetayGetir.sql", (siparis_no, restoranID)) or []
        siparisler_detayli.append({
            "siparis": siparis,
            "detaylar": detaylar
        })

    return render_template("RestoranSiparisler.html", siparisler=siparisler_detayli)


# ============================================
# PROFİL VE AYARLAR
# ============================================

@app.route("/profilim", methods=["GET", "POST"])
@login_required(TYPES.E)
def profilim_get():
    user_id = session["user_id"]

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        surname = (request.form.get("surname") or "").strip()
        telno = (request.form.get("telno") or "").strip()
        email = (request.form.get("email") or "").strip() or None  # email null olabilir

        if not name or not surname or not telno:
            flash("Ad, soyad ve telefon alanları boş bırakılamaz.", "danger")
            return redirect("/profilim")

        try:
            sql_querry(
                "UPDATE efendi SET name=?, surname=?, telno=?, email=? WHERE ID=?",
                (name, surname, telno, email, user_id)
            )
            flash("Profil bilgilerin güncellendi!", "success")
            return redirect("/profilim")

        except pyodbc.IntegrityError:
            # telno veya email unique constraint patlarsa
            flash("Bu telefon numarası veya e-posta zaten başka bir hesapta kayıtlı.", "danger")
            return redirect("/profilim")

        except pyodbc.Error as err:
            flash(f"Profil güncellenirken bir hata oluştu: {err}", "danger")
            return redirect("/profilim")

    # GET isteği: veriyi DB'den çekip formu doldur
    rows = sql_querry(
        "SELECT name, surname, telno, email FROM efendi WHERE ID = ?",
        (user_id,)
    ) or []
    user = rows[0] if rows else None  # (name, surname, telno, email)

    return render_template("Profilim.html", user=user)



@app.route("/gecmisSiparislerim")
@login_required(TYPES.E)
def gecmis_siparislerim_get():
    efendiID = session.get("user_id")
    siparisler = sql_querry("sql/SiparisVerme/siparislerimlistele.sql", (efendiID,)) or []
    return render_template("GecmisSiparislerim.html", siparisler=siparisler)



@app.route("/logout")
def logout_get():
    session.clear()
    flash("Çıkış yapıldı.", "success")
    return redirect("/login")


# ============================================
# ADRES YÖNETİMİ
# ============================================

@app.route("/addAdress")
@login_required(TYPES.E)
def addAdress_get():
    return render_template("addAdress.html")


@app.route("/adreslerim")
@login_required(TYPES.E)
def adreslerim_get():
    user_id = session["user_id"]
    adresler = sql_querry(
        "SELECT adresName, il, ilce, mah, cd, binano, daireno FROM Adres WHERE efendiID = ?",
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
        "SELECT adresName FROM Adres WHERE efendiID = ? AND adresName = ?",
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
            "DELETE FROM Adres WHERE efendiID = ? AND adresName = ?",
            (user_id, adres_name)
        )
        flash("Adres silindi.", "success")
    except pyodbc.Error as err:
        flash(f"Adres silinirken bir hata oluştu: {err}", "danger")

    return redirect("/adreslerim")


@app.route("/adres/duzenle", methods=["GET"])
@login_required(TYPES.E)
def adres_duzenle_get():
    user_id = session["user_id"]
    adres_name = request.args.get("adresName")

    rows = sql_querry(
        "SELECT adresName, il, ilce, mah, cd, binano, daireno FROM Adres WHERE efendiID = ? AND adresName = ?",
        (user_id, adres_name)
    ) or []

    if not rows:
        flash("Adres bulunamadı.", "danger")
        return redirect("/adreslerim")

    adres = rows[0]
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
            "UPDATE Adres SET adresName=?, il=?, ilce=?, mah=?, cd=?, binano=?, daireno=? "
            "WHERE efendiID=? AND adresName=?",
            (new_name, il, ilce, mahalle, cadde, bina_no, daire_no, user_id, old_name)
        )
        flash("Adres güncellendi.", "success")
    except pyodbc.IntegrityError:
        flash("Bu isimde zaten bir adresiniz var. Lütfen farklı bir isim kullanın.", "danger")
    except pyodbc.Error as err:
        flash(f"Adres güncellenirken bir hata oluştu: {err}", "danger")

    return redirect("/adreslerim")


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
            latitude = (float(request.form.get("latitude")) - REF_LAT) * 111320
            longitude = (float(request.form.get("longitude")) - REF_LON) * 111320 * np.cos(REF_LAT*np.pi/180)
            user_id = session.get("user_id")

            sql_querry("sql/efendiAddAdress.sql", 
                      (user_id, adres_adi, il, ilce, mahalle, cadde, bina_no, daire_no, latitude, longitude))

            if not session.get("selected_adresName"):
                session["selected_adresName"] = adres_adi
            
            flash("Adres başarıyla eklendi!", "success")
            return redirect("/HomePage")

        except pyodbc.IntegrityError:
            flash("Bu isimde bir adres zaten kayıtlı. Lütfen farklı bir adres adı girin.", "danger")
            return redirect("/addAdress")

        except pyodbc.Error as err:
            flash(f"Bir hata oluştu: {err}", "danger")
            return redirect("/addAdress")

    return redirect("/addAdress")


# ============================================
# RESTORAN YÖNETİMİ (Restoran hesabı için)
# ============================================

@app.route("/addYemek")
@login_required(TYPES.R)
def addyemek_get():
    return render_template("addYemek.html")


@app.route("/post/restoranAddYemek", methods=["POST"])
@login_required(TYPES.R)
def addYemek_post():
    if request.method == "POST":
        try:
            name = request.form["name"]
            price = float(request.form["price"])
            sql_querry("sql/restoran/addYemek.sql", (name, price, session.get("user_id")))
            flash("Yemek başarıyla eklendi!", "success")
            return redirect("/RestoranHomePage")
        except pyodbc.Error as err:
            flash(f"Bir hata oluştu: {err}", "danger")

    return redirect("/addYemek")


# ============================================
# SEPET SİSTEMİ
# ============================================

@app.route("/restoranSec", methods=["POST"])
@login_required(TYPES.E)
def restoran_sec():
    restoranID = request.form.get("restoranID")
    
    restoran = sql_querry(
        "SELECT ID, name, telno, adres, minsepettutari FROM restoran WHERE ID = ?",
        (restoranID,)
    )
    
    if not restoran:
        flash("Restoran bulunamadı.", "danger")
        return redirect("/HomePage")
    
    yemekler = sql_querry("sql/restoran/YemekleriListele.sql", (restoranID,))
    
    return render_template("RestoranMenu.html", restoran=restoran[0], yemekler=yemekler)


@app.route("/restoranSec", methods=["GET"])
@login_required(TYPES.E)
def restoran_sec_get():
    restoranID = request.args.get("restoranID")
    
    if not restoranID:
        flash("Restoran ID bulunamadı.", "danger")
        return redirect("/HomePage")
    
    restoran = sql_querry(
        "SELECT ID, name, telno, adres, minsepettutari FROM restoran WHERE ID = ?",
        (restoranID,)
    )
    
    if not restoran:
        flash("Restoran bulunamadı.", "danger")
        return redirect("/HomePage")
    
    yemekler = sql_querry("sql/restoran/YemekleriListele.sql", (restoranID,))
    
    return render_template("RestoranMenu.html", restoran=restoran[0], yemekler=yemekler)


@app.route("/sepeteEkle", methods=["POST"])
@login_required(TYPES.E)
def sepete_ekle():
    efendiID = session.get("user_id")
    yemekID = request.form.get("yemekID")
    restoranID = request.form.get("restoranID")
    adet = int(request.form.get("adet", 1))
    
    print(f"DEBUG - Sepete ekleme başlıyor:")
    print(f"  efendiID: {efendiID}, type: {type(efendiID)}")
    print(f"  yemekID: {yemekID}, type: {type(yemekID)}")
    print(f"  adet: {adet}, type: {type(adet)}")
    print(f"  restoranID: {restoranID}, type: {type(restoranID)}")
    
    try:
        if adet < 0:
            # Mevcut adeti kontrol et
            mevcut = sql_querry("SELECT adet FROM sepetUrunler WHERE efendiID = ? AND yemekID = ?", (efendiID, yemekID))
            if mevcut[0][0] + adet <= 0:
                sql_querry("DELETE FROM sepetUrunler WHERE efendiID = ? AND yemekID = ?", (efendiID, yemekID))
                flash("Ürün sepetten tamamen kaldırıldı!", "success")
                if (restoranID == "sepet"):
                    return redirect("/sepetim")
                return redirect(f"/restoranSec?restoranID={restoranID}")
            sql_querry("UPDATE sepetUrunler SET adet=? WHERE efendiID = ? AND yemekID = ?", (mevcut[0][0] - 1, efendiID, yemekID))
        else:
            result = sql_querry("sql/Siparis/sepeteEkle.sql", (efendiID, yemekID, adet, adet))
            print(f"DEBUG - SQL result: {result}")
        if adet<0:
            flash(f"{-adet} adet ürün sepetten azaltıldı!", "success")
        else:
            flash(f"{adet} adet ürün sepete eklendi!", "success")
        print("DEBUG - Flash mesajı başarılı eklendi")
        
    except Exception as e:
        print(f"DEBUG - HATA YAKALANDI: {e}")
        print(f"DEBUG - Hata tipi: {type(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Sepete eklenirken hata oluştu: {e}", "danger")

    if (restoranID == "sepet"):
        return redirect("/sepetim")
    print(f"DEBUG - Redirect ediliyor: /restoranSec?restoranID={restoranID}")
    return redirect(f"/restoranSec?restoranID={restoranID}")


@app.route("/sepetim")
@login_required(TYPES.E)
def sepetim_get():
    efendiID = session.get("user_id")
    sepet_urunler = sql_querry("sql/Siparis/sepetiGetir.sql", (efendiID,))
    print(sepet_urunler)
    return render_template("Sepet.html", sepet_urunler=sepet_urunler)


@app.route("/sepettenSil", methods=["POST"])
@login_required(TYPES.E)
def sepetten_sil():
    try:
        efendiID = session.get("user_id")
        yemekID = request.form.get("yemekID")
        
        sql_querry("sql/Siparis/sepettenSil.sql", (efendiID, yemekID))
        
        flash("Ürün sepetten silindi.", "success")
        
    except Exception as e:
        flash(f"Silinirken hata oluştu: {e}", "danger")
    
    return redirect("/sepetim")


@app.route("/siparisOlustur", methods=["POST"])
@login_required(TYPES.E)
def siparis_olustur():
    conn = None
    cursor = None
    try:
        efendiID = session.get("user_id")
        odeme_yontemi = request.form.get('odemeYontemi')
        if odeme_yontemi == 'krediKarti':
            kart_no = request.form.get('kartNo').replace(" ","")
            kart_sahibi = request.form.get('kartSahibi')
            son_kullanma = request.form.get('sonKullanma').replace("/","")
            cvv = request.form.get('cvv')
            exist = sql_querry("SELECT kartno from krediKarti where kartno=?",(kart_no,))

        sepet_urunler = sql_querry("sql/Siparis/Sepetigetir.sql", (efendiID,))
        
        if not sepet_urunler:
            flash("Sepetiniz boş!", "danger")
            return redirect("/sepetim")
        
        selected_adres = session.get("selected_adresName")
        if not selected_adres:
            flash("Lütfen önce bir teslimat adresi seçin!", "danger")
            return redirect("/adreslerim")
        
        toplam_fiyat = sum(urun[2] * urun[3] for urun in sepet_urunler)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(read_file("sql/SiparisVerme/siparisOlustur.sql"), (efendiID, selected_adres))
        cursor.execute("SELECT LAST_INSERT_ID()")
        sparisNo = cursor.fetchone()[0]
        
        for urun in sepet_urunler:
            yemekID = urun[0]
            adet = urun[3]
            cursor.execute(read_file("sql/SiparisVerme/siparisUrunEkle.sql"),(sparisNo, yemekID, adet))
        
        if odeme_yontemi == "krediKarti":
            if banka_islemi_gerceklestir(cvv, kart_sahibi, kart_no, son_kullanma, toplam_fiyat):
                if not exist:
                    cursor.execute(read_file("sql/odeme/kartolusturma.sql"),(kart_no, cvv, kart_sahibi, son_kullanma))
                cursor.execute(read_file("sql/odeme/kredikarti.sql"),(sparisNo, toplam_fiyat, kart_no))
        else:
            cursor.execute(read_file("sql/odeme/nakitOdemeEkle.sql"),(sparisNo, toplam_fiyat))

        print(f"Sipariş {sparisNo} oluşturuldu, kuryeler tarafından kabul edilmesi bekleniyor...")

        sql_querry("sql/Siparis/Sepetitemizle.sql", (efendiID,))

        conn.commit()

        iptal_thread = threading.Thread(
            target=otomatik_siparis_iptal,
            args=(sparisNo, efendiID),
            daemon=True
        )
        iptal_thread.start()

        flash(f"Siparişiniz başarıyla oluşturuldu! Sipariş No: {sparisNo}", "success")
        flash(f"Toplam tutar: {toplam_fiyat:.2f} ₺", "success")
        flash("Siparişiniz 60 saniye içinde bir kurye tarafından kabul edilmelidir.", "info")

        return redirect("/HomePage")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Sipariş oluşturma hatası: {e}")
        traceback.print_exc()
        flash(f"Sipariş oluşturulurken hata oluştu: {e}", "danger")
        return redirect("/sepetim")
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================
# GİRİŞ VE KAYIT İŞLEMLERİ
# ============================================

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
            sql_querry("sql/Login_Register/EfendiSignIn.sql", (name, surname, telno, make_null(email), hashed_password))
            flash("Kayıt başarıyla tamamlandı!", "success")
            return redirect("/login")

        except pyodbc.IntegrityError:
            flash("Bu e-posta veya telefon numarası zaten kayıtlı.", "danger")
        except pyodbc.Error as err:
            flash(f"Bir hata oluştu: {err}", "danger")

        return redirect("/register")


@app.route("/post/login", methods=["POST"])
def login_post():
    if request.method == "POST":
        identifier = request.form["identifier"]
        password = request.form["password"]

        try:
            user_data = sql_querry("sql/Login_Register/EfendiLogin.sql", (identifier, identifier))
            if user_data == []:
                flash("Telno/Email yanlış", "danger")
            elif not check_password_hash(user_data[0][5], password):
                flash("Şifre yanlış", "danger")
            else:
                login(user_data[0][0], "efendi")
                return redirect("/HomePage")

        except pyodbc.Error as err:
            flash(f"Bir hata oluştu: {err}", "danger")

        return redirect("/login")


@app.route("/post/RestoranLogin", methods=["POST"])
def RestoranLogin_post():
    if request.method == "POST":
        identifier = request.form["identifier"]
        password = request.form["password"]

        try:
            user_data = sql_querry("sql/Login_Register/RestoranLogin.sql", (identifier,))
            if user_data == []:
                flash("Telno yanlış", "danger")
            elif not check_password_hash(user_data[0][5], password):
                flash("Şifre yanlış", "danger")
            else:
                login(user_data[0][0], "restoran")
                return redirect("/RestoranHomePage")
        except pyodbc.Error as err:
            flash(f"Bir hata oluştu: {err}", "danger")

        return redirect("/restoranLogin")


@app.route("/post/RestoranRegister", methods=["POST"])
def RestoranRegister_post():
    if request.method == "POST":
        name = request.form["name"]
        telno = request.form["telno"]
        adres = request.form["adress"]
        minsepet = request.form["Minsepet"]
        latitude = (float(request.form.get("latitude")) - REF_LAT) * 111320
        longitude = (float(request.form.get("longitude")) - REF_LON) * 111320 * np.cos(REF_LAT*np.pi/180)

        hashed_password = generate_password_hash(request.form["password"], method="pbkdf2:sha256")

        try:
            sql_querry("sql/Login_Register/RestoranRegister.sql", (name, telno, adres, minsepet, hashed_password, latitude, longitude))
            flash("Kayıt başarıyla tamamlandı!", "success")
            return redirect("/restoranLogin")

        except pyodbc.IntegrityError:
            flash("Bu e-posta veya telefon numarası zaten kayıtlı.", "danger")
        except pyodbc.Error as err:
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
            sql_querry("sql/Login_Register/KuryeRegister.sql", (name, surname, telno, make_null(email), hashed_password))
            flash("Kayıt başarıyla tamamlandı!", "success")
            return redirect("/kuryeLogin")

        except pyodbc.IntegrityError:
            flash("Bu e-posta veya telefon numarası zaten kayıtlı.", "danger")
        except pyodbc.Error as err:
            flash(f"Bir hata oluştu: {err}", "danger")

        return redirect("/kuryeRegister")


@app.route("/post/kuryeLogin", methods=["POST"])
def kuryelogin_post():
    if request.method == "POST":
        identifier = request.form["identifier"]
        password = request.form["password"]

        try:
            user_data = sql_querry("sql/Login_Register/KuryeLogin.sql", (identifier, identifier))
            if user_data == []:
                flash("Telno/Email yanlış", "danger")
            elif not check_password_hash(user_data[0][5], password):
                flash("Şifre yanlış", "danger")
            else:
                login(user_data[0][0], "kurye")
                return redirect("/KuryeHomePage")

        except pyodbc.Error as err:
            flash(f"Bir hata oluştu: {err}", "danger")

        return redirect("/kuryeLogin")


@app.errorhandler(403)
def no403(e):
    flash(f"Unvalid accses due to {e.description["message"]}", "danger")
    return redirect("/")
@app.route("/KuryeHomePage")
@login_required(TYPES.K)
def KuryeHomePage_get():
    kuryeID = session.get("user_id")
    kurye_bilgileri = sql_querry("sql/kurye/KuryeBilgileriGetir.sql", (kuryeID,))
    aktif_siparis = sql_querry("sql/kurye/AktifSiparisGetir.sql", (kuryeID,))

    kurye = kurye_bilgileri[0] if kurye_bilgileri else None
    siparis = aktif_siparis[0] if aktif_siparis else None

    return render_template("KuryeHomePage.html", kurye=kurye, siparis=siparis)

@app.route("/kuryeProfil", methods=["GET", "POST"])
@login_required(TYPES.K)
def kurye_profil():
    kurye_id = session.get("user_id")

    conn = get_db_connection()
    cur = conn.cursor()

    # ========== PROFIL GÜNCELLEME ==========
    if request.method == "POST":
        ad = request.form.get("name")
        soyad = request.form.get("surname")
        telno = request.form.get("telno")   # ← dikkat: telno
        email = request.form.get("email")   # ← ister eklersin ister çıkartırsın

        cur.execute(
            "UPDATE kurye SET name=?, surname=?, telno=?, email=? WHERE ID=?",
            (ad, soyad, telno, email, kurye_id),
        )
        conn.commit()
        flash("Profil bilgilerin güncellendi.", "success")

    # ========== MEVCUT BILGILER ==========
    cur.execute(
        "SELECT ID, name, surname, telno, email FROM kurye WHERE ID=?",
        (kurye_id,),
    )
    kurye = cur.fetchone()

    conn.close()

    return render_template("kuryeProfil.html", kurye=kurye)


@app.route("/kurye/iseBasla", methods=["POST"])
@login_required(TYPES.K)
def kurye_ise_basla():
    kuryeID = session.get("user_id")
    yeni_durum = request.form.get("durum")

    if yeni_durum not in ["0", "1"]:
        return {"success": False, "message": "Geçersiz durum"}, 400

    try:
        sql_querry("sql/kurye/IsWorkingGuncelle.sql", (int(yeni_durum), kuryeID))
        return {"success": True, "isWorking": int(yeni_durum) == 1}
    except Exception as e:
        print(f"İşe başla hatası: {e}")
        return {"success": False, "message": str(e)}, 500


@app.route("/kurye/koordinatGuncelle", methods=["POST"])
@login_required(TYPES.K)
def kurye_koordinat_guncelle():
    kuryeID = session.get("user_id")
    try:
        x = (float(request.form.get("latitude")) - REF_LAT) * 111320
        y = (float(request.form.get("longitude")) - REF_LON) * 111320 * np.cos(REF_LAT*np.pi/180)
        sql_querry("sql/kurye/KoordinatGuncelle.sql", (x, y, kuryeID))
        return {"success": True}
    except Exception as e:
        print(f"Koordinat güncelleme hatası: {e}")
        return {"success": False, "message": str(e)}, 500


@app.route("/kurye/aktifSiparis", methods=["GET"])
@login_required(TYPES.K)
def kurye_aktif_siparis():
    kuryeID = session.get("user_id")
    try:
        aktif_siparis = sql_querry("sql/kurye/AktifSiparisGetir.sql", (kuryeID,))
        if aktif_siparis:
            siparis = aktif_siparis[0]
            return {
                "success": True,
                "siparis": {
                    "sparisNo": siparis[0],
                    "durum": siparis[1],
                    "teslimAdres": siparis[2],
                    "efendiName": siparis[3],
                    "efendiSurname": siparis[4],
                    "efendiTelno": siparis[5],
                    "il": siparis[6],
                    "ilce": siparis[7],
                    "mah": siparis[8],
                    "cd": siparis[9],
                    "binano": siparis[10],
                    "daireno": siparis[11],
                    "teslimX": siparis[12],
                    "teslimY": siparis[13],
                    "restoranName": siparis[14],
                    "restoranTelno": siparis[15],
                    "restoranAdres": siparis[16],
                    "restoranX": siparis[17],
                    "restoranY": siparis[18]
                }
            }
        return {"success": True, "siparis": None}
    except Exception as e:
        print(f"Aktif sipariş getirme hatası: {e}")
        traceback.print_exc()
        return {"success": False, "message": str(e)}, 500


@app.route("/kurye/bekleyenSiparisler", methods=["GET"])
@login_required(TYPES.K)
def kurye_bekleyen_siparisler():
    kuryeID = session.get("user_id")
    try:
        bekleyen_siparisler = sql_querry("sql/kurye/BekleyenSiparislerGetir.sql", (kuryeID,))
        if bekleyen_siparisler:
            siparisler = []
            for siparis in bekleyen_siparisler:
                siparisler.append({
                    "sparisNo": siparis[0],
                    "teslimAdres": siparis[1],
                    "efendiName": siparis[2],
                    "efendiSurname": siparis[3],
                    "restoranName": siparis[4],
                    "restoranAdres": siparis[5],
                    "mesafe": round(siparis[8], 2) if len(siparis) > 8 else 0
                })
            return {"success": True, "siparisler": siparisler}
        return {"success": True, "siparisler": []}
    except Exception as e:
        print(f"Bekleyen siparişler getirme hatası: {e}")
        traceback.print_exc()
        return {"success": False, "message": str(e)}, 500


@app.route("/kurye/siparisKabulEt", methods=["POST"])
@login_required(TYPES.K)
def kurye_siparis_kabul_et():
    kuryeID = session.get("user_id")
    sparisNo = request.form.get("sparisNo")

    try:
        sql_querry("sql/kurye/SiparisKabulEt.sql", (kuryeID, sparisNo))
        flash("Sipariş kabul edildi!", "success")
        return redirect("/KuryeHomePage")
    except Exception as e:
        print(f"Sipariş kabul etme hatası: {e}")
        flash(f"Sipariş kabul edilirken hata oluştu: {e}", "danger")
        return redirect("/KuryeHomePage")


@app.route("/kurye/siparisOnayla", methods=["POST"])
@login_required(TYPES.K)
def kurye_siparis_onayla():
    kuryeID = session.get("user_id")
    sparisNo = request.form.get("sparisNo")

    try:
        sql_querry("sql/kurye/SiparisOnayla.sql", (kuryeID, sparisNo))
        flash("Sipariş kabul edildi!", "success")
        return redirect("/KuryeHomePage")
    except Exception as e:
        print(f"Sipariş onaylama hatası: {e}")
        flash(f"Sipariş kabul edilirken hata oluştu: {e}", "danger")
        return redirect("/KuryeHomePage")


@app.route("/kurye/siparisTamamla", methods=["POST"])
@login_required(TYPES.K)
def kurye_siparis_tamamla():
    kuryeID = session.get("user_id")
    sparisNo = request.form.get("sparisNo")

    try:
        sql_querry("sql/kurye/SiparisTamamla.sql", (sparisNo, kuryeID))
        flash("Sipariş teslim edildi!", "success")
        return redirect("/KuryeHomePage")
    except Exception as e:
        print(f"Sipariş tamamlama hatası: {e}")
        flash(f"Sipariş tamamlanırken hata oluştu: {e}", "danger")
        return redirect("/KuryeHomePage")

# ============================================
# UYGULAMA BAŞLATMA
# ============================================

if __name__ == "__main__":
    app.run("0.0.0.0", 3131)