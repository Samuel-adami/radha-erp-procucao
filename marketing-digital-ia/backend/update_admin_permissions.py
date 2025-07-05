import json
from database import get_db_connection, DEFAULT_ADMIN_PERMISSIONS
from sqlalchemy import text
import os


def ensure_cadastros_permissions(username: str = None) -> None:
    """Grant all Cadastros permissions to the given admin user."""
    conn = get_db_connection()
    if username:
        rows = conn.execute(
            text("SELECT id, permissoes FROM users WHERE username=:u AND cargo='admin'"),
            {"u": username},
        ).fetchall()
    else:
        rows = conn.execute(
            text("SELECT id, permissoes FROM users WHERE cargo='admin'")
        ).fetchall()
    updated = 0
    for row in rows:
        perms = json.loads(row._mapping["permissoes"] or "[]")
        changed = False
        for perm in DEFAULT_ADMIN_PERMISSIONS:
            if perm.startswith("cadastros") and perm not in perms:
                perms.append(perm)
                changed = True
        if changed:
            conn.execute(
                text("UPDATE users SET permissoes=:p WHERE id=:id"),
                {"p": json.dumps(perms), "id": row._mapping["id"]},
            )
            updated += 1
    if updated:
        conn.commit()
    conn.close()
    print(f"Updated {updated} admin user(s)")


if __name__ == "__main__":
    ensure_cadastros_permissions(os.getenv("RADHA_ADMIN_USER"))
