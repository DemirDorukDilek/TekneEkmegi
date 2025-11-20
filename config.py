import os
print(os.getenv("ROOT_PASSWORD"))
DB_CONFIG = {
    'host': "localhost",
    'user': "root",
    'password': os.getenv("ROOT_PASSWORD"),
    'database': "ekmekteknesi"
}