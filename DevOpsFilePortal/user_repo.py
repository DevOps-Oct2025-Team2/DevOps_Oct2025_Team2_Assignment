from db.db import get_conn
from werkzeug.security import generate_password_hash


def get_user_by_username(username: str):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, password_hash, role, created_at FROM users WHERE username = ?",
            (username,),
        )
        return cur.fetchone()
    finally:
        conn.close()


def list_all_users():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
              id,
              ROW_NUMBER() OVER (ORDER BY id) AS display_id,
              username,
              role,
              created_at
            FROM users
            ORDER BY id ASC
            """
        )
        return cur.fetchall()
    finally:
        conn.close()


def create_user(username: str, password: str, role: str = "user"):
    conn = get_conn()
    try:
        cur = conn.cursor()
        pwd_hash = generate_password_hash(password)
        cur.execute(
            """
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
            """,
            (username, pwd_hash, role),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def delete_user(user_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def ensure_seed_admin():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", ("admin",))
        existing = cur.fetchone()
        if existing:
            return

        pwd_hash = generate_password_hash("admin123")
        cur.execute(
            """
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
            """,
            ("admin", pwd_hash, "admin"),
        )
        conn.commit()
        print("Seeded admin user: admin / admin123")
    finally:
        conn.close()
