import os
DB_CONFIG = {
    'host': "localhost",
    'user': "root",
    'password': os.getenv("ROOT_PASSWORD"),
    'database': "ekmekteknesi"
}