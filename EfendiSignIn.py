import mysql.connector as sql
from basics.file_work import read_file

db = sql.connect(host="localhost",user="root",password="",database="ekmekteknesi")
cursor = db.cursor()


name = input("name: ")
surname = input("surname: ")
telno = input("telno: ")
email = input("email: ")
password = input("password: ")
cursor.execute(read_file("SignIn.sql"),(name,surname,telno,email,password))
db.commit()