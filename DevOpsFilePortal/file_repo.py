# DevOpsApp/file_repo.py
from db.db import get_conn


def _reset_files_sequence_if_empty(cur):
    cur.execute("SELECT COUNT(*) AS c FROM files")
    row = cur.fetchone()
    if row and row["c"] == 0:
        cur.execute("DELETE FROM sqlite_sequence WHERE name='files'")


def list_files_for_user(user_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, original_filename, stored_filename, content_type, file_size, uploaded_at
            FROM files
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        )
        return cur.fetchall()
    finally:
        conn.close()


def get_file_for_user(user_id: int, file_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, user_id, original_filename, stored_filename, content_type, file_size, storage_path, uploaded_at
            FROM files
            WHERE id = ? AND user_id = ?
            """,
            (file_id, user_id),
        )
        return cur.fetchone()
    finally:
        conn.close()


def insert_file(
    user_id: int,
    original_filename: str,
    stored_filename: str,
    content_type,
    file_size,
    storage_path: str,
):
    conn = get_conn()
    try:
        cur = conn.cursor()

        _reset_files_sequence_if_empty(cur)

        cur.execute(
            """
            INSERT INTO files (user_id, original_filename, stored_filename, content_type, file_size, storage_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, original_filename, stored_filename, content_type, file_size, storage_path),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def delete_file_record_for_user(user_id: int, file_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM files WHERE id = ? AND user_id = ?", (file_id, user_id))
        deleted = cur.rowcount
        conn.commit()

        if deleted:
            _reset_files_sequence_if_empty(cur)
            conn.commit()

        return deleted
    finally:
        conn.close()
