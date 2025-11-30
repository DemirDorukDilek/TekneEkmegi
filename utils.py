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
    make_table()
    make_index()

def execute_delimiter(code,cursor):
    # // ile ayrılmış trigger/procedure kodlarını çalıştır
    statements = code.split("//")
    for statement in statements:
        statement = statement.strip()
        if len(statement) > 0:
            cursor.execute(statement)

def make_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    sql_content = read_file("sql/CreateTable.sql")

    # --DELIMITER// ile başlayan kısım varsa ayır
    if "--DELIMITER//" in sql_content:
        normal_sql, delimiter_sql = sql_content.split("--DELIMITER//", 1)

        # Normal SQL'leri çalıştır
        for l in normal_sql.split(";"):
            code = l.strip()
            if len(code) > 0:
                cursor.execute(code+";")

        # Trigger'ları çalıştır
        execute_delimiter(delimiter_sql, cursor)
    else:
        # Eski format
        for l in sql_content.split(";"):
            code = l.strip()
            if len(code) > 0:
                cursor.execute(code+";")

    conn.commit()

def make_index():
    conn = get_db_connection()
    cursor = conn.cursor()
    for l in read_file("sql/AddIndex.sql").split(";"):
        if len(l.strip()) > 0 and l.startswith("CREATE INDEX"):
            cursor.execute(l.strip()+";")
    conn.commit()

def sql_querry(querry,args):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        code = read_file(querry) if os.path.isfile(querry) else querry
        with open("sql_querry_log","a",encoding="utf-8") as f:
            f.write(code+"\n")
            f.write(str(args)+"\n")
            f.write(str(type(args))+"\n")
            f.write("\n\n")
        cursor.execute(code, args)
        data = None
        if code.lower().startswith("select"):
            data = cursor.fetchall()
        conn.commit()
        return data
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()