import os
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))


class Config:
    DATA_DIR = os.path.abspath(os.environ.get("DATA_DIR", os.path.join(HERE, "..", "frontend", "public", "data")))
    EXTRA_SCENARIOS = os.path.join(HERE, "scenarios")
    DB_URL = os.environ.get("DB_URL", "sqlite:///" + os.path.join(HERE, "city.db"))
    MOCK = os.environ.get("MOCK", "").strip() == "1"     
    DIRECTOR_TOKEN = os.environ.get("DIRECTOR_TOKEN", "1234554321").strip()
    DEFAULT_SCENARIO = os.environ.get("SCENARIO", "live_city").strip()
    DEFAULT_USERS = int(os.environ.get("USERS", "20000"))
    DEFAULT_SPEED = float(os.environ.get("SPEED", "60"))

    odbc_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=127.0.0.1,1433;"
        "DATABASE=master;"
        "UID=sa;"
        "PWD=YourStrongPassword123!;"
        "TrustServerCertificate=yes;"
    )
    
    params = urllib.parse.quote_plus(odbc_str)
    
    SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={params}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False