import bcrypt as _bcrypt
from types import SimpleNamespace
if not hasattr(_bcrypt, "__about__"):
    _bcrypt.__about__ = SimpleNamespace(__version__=_bcrypt.__version__)
from passlib.hash import bcrypt
from database import get_db_connection
from sqlalchemy import text


def migrate():
    conn = get_db_connection()
    rows = conn.execute(text("SELECT id, password FROM users")).fetchall()
    migrated = 0
    for row in rows:
        pwd = row._mapping["password"]
        if pwd and not str(pwd).startswith("$2"):
            conn.execute(
                text("UPDATE users SET password=:pwd WHERE id=:id"),
                {"pwd": bcrypt.hash(pwd), "id": row._mapping["id"]},
            )
            migrated += 1
    if migrated:
        conn.commit()
    conn.close()
    print(f"Migrated {migrated} password(s)")


if __name__ == "__main__":
    migrate()
