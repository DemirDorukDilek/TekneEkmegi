import os
if os.name != "posix":
    from dotenv import load_dotenv;load_dotenv()
print("******* .env dosyasi gerekmektedir ve db root sifresi ROOT_PASSWORD olarak girilmelidir bkz:config.py *******")
# ODBC Connection String
def get_connection_string():
    password = os.getenv("ROOT_PASSWORD")
    return (
        f"DRIVER={{MySQL ODBC 9.5 Unicode Driver}};"
        f"SERVER=localhost;"
        f"DATABASE=ekmekteknesi;"
        f"USER=root;"
        f"PASSWORD={password};"
        f"CHARSET=utf8mb4;"
    )