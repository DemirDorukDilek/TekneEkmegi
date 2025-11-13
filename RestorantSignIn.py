import mysql.connector as sql

def read_file(fp):
    with open(fp,encoding="utf-8") as f:return f.read()

db = sql.connect(host="localhost",user="root",password="112358",database="ekmekteknesi")
cursor = db.cursor()


name = input("name: ")
telno = input("telno: ")
adres = input("adres: ")
cursor.execute(read_file("RestorantSignIn.sql"),(name,telno,adres))
db.commit()

