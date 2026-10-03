import os

HERE = os.path.dirname(os.path.abspath(__file__))


class Config:
    DATA_DIR = os.path.abspath(os.environ.get("DATA_DIR", os.path.join(HERE, "..", "frontend", "public", "data")))
    EXTRA_SCENARIOS = os.path.join(HERE, "scenarios")
    DB_URL = os.environ.get("DB_URL", "sqlite:///" + os.path.join(HERE, "city.db"))
    MOCK = os.environ.get("MOCK", "").strip() == "1"       # strip: cmd's `set X=1 && ...` adds a space
    DIRECTOR_TOKEN = os.environ.get("DIRECTOR_TOKEN", "1357908642").strip()
    DEFAULT_SCENARIO = os.environ.get("SCENARIO", "heating_azory").strip()
    DEFAULT_USERS = int(os.environ.get("USERS", "20000"))
    DEFAULT_SPEED = float(os.environ.get("SPEED", "60"))
