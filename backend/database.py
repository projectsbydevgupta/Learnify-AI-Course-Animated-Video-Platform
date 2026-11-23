import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/aicourse_db")

# Attempt PostgreSQL connection; if unavailable, fallback cleanly to SQLite
connect_args = {}
try:
    if DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        engine = create_engine(DATABASE_URL, connect_args=connect_args)
    else:
        test_engine = create_engine(DATABASE_URL)
        with test_engine.connect() as conn:
            pass
        engine = test_engine
        print("[DATABASE] Connected successfully to PostgreSQL database.")
except Exception as ex:
    print(f"[DATABASE WARNING] PostgreSQL connection failed ({ex}). Falling back to local SQLite database: courses.db")
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "courses.db"))
    DATABASE_URL = f"sqlite:///{db_path}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()