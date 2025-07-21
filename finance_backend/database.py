import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv, find_dotenv
from .models import Base

load_dotenv(find_dotenv())

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not configured")

schema = os.environ.get("DATABASE_SCHEMA")
connect_args = {"options": f"-c search_path={schema}"} if schema else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)


def get_session() -> Session:
    return SessionLocal()


def get_db_connection():
    return engine.connect()


def insert_with_id(conn, sql: str, params: tuple):
    if engine.dialect.name == "postgresql":
        result = conn.exec_driver_sql(sql + " RETURNING id", params)
        return result.scalar()
    result = conn.exec_driver_sql(sql, params)
    return result.lastrowid


def init_db():
    Base.metadata.create_all(engine)
