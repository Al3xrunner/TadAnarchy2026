from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(expire_on_commit=False)
db_engine = None


def init_db(url):
    global db_engine
    sqlite = url.startswith("sqlite")
    db_engine = create_engine(url, connect_args={"check_same_thread": False} if sqlite else {})
    if sqlite:
        @event.listens_for(db_engine, "connect")
        def _pragmas(conn, _record):
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")       
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.execute("PRAGMA busy_timeout=5000")      
            cur.close()
    SessionLocal.configure(bind=db_engine)
    from .models import Base
    Base.metadata.create_all(db_engine)
