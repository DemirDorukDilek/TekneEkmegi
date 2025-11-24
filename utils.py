from config import DB_CONFIG
import mysql.connector as sql
import os

def get_db_connection():
    return sql.connect(**DB_CONFIG)

def make_null(x):
    if x=="":return None
    return x
    
def read_file(fp):
    with open(fp, encoding="utf-8") as f:return f.read()


def make_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    for l in read_file("sql/CreateTable.sql").split(";"):
        if len(l.strip()) > 0:
            cursor.execute(l.strip()+";")
    conn.commit()

def sql_query(querry,args):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        code = read_file(querry) if os.path.isfile(querry) else querry
        cursor.execute(code, args)
        data = None
        if code.lower().startswith("select"):
            data = cursor.fetchone()
        conn.commit()
        return data
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()