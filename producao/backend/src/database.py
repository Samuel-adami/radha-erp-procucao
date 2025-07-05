import os
from sqlalchemy import create_engine
from dotenv import load_dotenv, find_dotenv
from models import Base, Chapa, Lote, Nesting

load_dotenv(find_dotenv())

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not configured")

schema = os.environ.get("DATABASE_SCHEMA")
connect_args = {"options": f"-c search_path={schema}"} if schema else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)


def get_db_connection():
    return engine.connect()


def init_db():
    """Create all tables defined in models.py."""
    Base.metadata.create_all(engine)

