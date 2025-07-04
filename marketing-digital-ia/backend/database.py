import os
from sqlalchemy import create_engine, text
from passlib.hash import bcrypt
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    data_dir = os.environ.get("RADHA_DATA_DIR", os.path.dirname(__file__))
    os.makedirs(data_dir, exist_ok=True)
    DATABASE_URL = f"sqlite:///{os.path.join(data_dir, 'marketing_ia.db')}"

engine = create_engine(DATABASE_URL)


def get_db_connection():
    return engine.connect()


def init_db():
    with engine.begin() as conn:
        conn.execute(text(
            """CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                email TEXT,
                nome TEXT,
                cargo TEXT,
                permissoes TEXT
            )"""
        ))

