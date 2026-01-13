from werkzeug.security import generate_password_hash
from db.db import get_conn


def get_user_by_username(username: str):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username,)
        )
        return cur.fetchone()
    finally:
        conn.close()


def list_all_users():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, username, role, created_at FROM users ORDER BY id ASC")
        return cur.fetchall()
    finally:
        conn.close()


def create_user(username: str, password: str, role: str = "user"):
    pw_hash = generate_password_hash(password)
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, pw_hash, role)
        )
        conn.commit()
    finally:
        conn.close()


def delete_user(user_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def ensure_seed_admin():
    """
    Creates a default admin if none exists.
    Change credentials after first login.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM users WHERE role = 'admin'")
        count = cur.fetchone()["c"]

        if count == 0:
            create_user("admin", "admin123", "admin")
            print("Seeded admin user: admin / admin123")
    finally:
        conn.close()
