from flask import g
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load .env if running locally
load_dotenv()

# DATABASE_URL from Render (external Postgres URL)
DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://sahjanandmart_user:ihI9VpcN6wflSh97D3JAnc7ORzAbZBnN@dpg-d15qgjodl3ps7382ldu0-a.oregon-postgres.render.com/sahjanandmart"

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
        # Corrected path: schema.sql must be in same folder as app.py (backend/)
        with app.open_resource('schema.sql', mode='r') as f:
            db.execute(text(f.read()))
        db.close()

def query_db(query, args=(), one=False):
    db = get_db()
    result = db.execute(text(query), args)
    rows = result.fetchall()
    return (rows[0] if rows else None) if one else rows
