import bcrypt as _bcrypt
from types import SimpleNamespace
if not hasattr(_bcrypt, "__about__"):
    _bcrypt.__about__ = SimpleNamespace(__version__=_bcrypt.__version__)
from passlib.hash import bcrypt
from database import get_db_connection


def migrate():
    conn = get_db_connection()
    cur = conn.cursor()
    rows = cur.execute("SELECT id, password FROM users").fetchall()
    migrated = 0
    for row in rows:
        pwd = row["password"]
        if pwd and not str(pwd).startswith("$2"):
            cur.execute(
                "UPDATE users SET password=? WHERE id=?",
                (bcrypt.hash(pwd), row["id"]),
            )
            migrated += 1
    if migrated:
        conn.commit()
    conn.close()
    print(f"Migrated {migrated} password(s)")


if __name__ == "__main__":
    migrate()
