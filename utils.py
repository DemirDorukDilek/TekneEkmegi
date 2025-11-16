from config import DB_CONFIG
import mysql.connector as sql

def get_db_connection():
    return sql.connect(**DB_CONFIG)

def make_null(x):
    if x=="":return None
    
def read_file(fp):
    with open(fp, encoding="utf-8") as f:return f.read()
