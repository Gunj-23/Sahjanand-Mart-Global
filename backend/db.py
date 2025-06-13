from flask import g, current_app
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load .env if running locally
load_dotenv()

# Load connection string securely
DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://postgres:GDPatel$2310@db.zvjuzgrqpusezzosmtsz.supabase.co:5432/postgres"

# Setup SQLAlchemy Engine and Session
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    if 'db' not in g:
        g.db = SessionLocal()
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    with app.app_context():
        db = engine.connect()
        with app.open_resource('backend/schema.sql', mode='r') as f:
            db.execute(text(f.read()))
        db.close()

def query_db(query, args=(), one=False):
    db = get_db()
    result = db.execute(text(query), args)
    rows = result.fetchall()
    return (rows[0] if rows else None) if one else rows
