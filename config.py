import os
if os.name != "posix":
    from dotenv import load_dotenv;load_dotenv()


DB_CONFIG = {
    'host': "localhost",
    'user': "root",
    'password': os.getenv("ROOT_PASSWORD"),
    'database': "ekmekteknesi"
}