#Garence Wong Kar Kang
import os
import sys
import uuid
import time
import requests
from markupsafe import escape
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory,
    abort,
    get_flashed_messages,
)
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from db.db import init_db
from auth import login_required, admin_required
from user_repo import (
    get_user_by_username,
    list_all_users,
    create_user,
    delete_user,
    ensure_seed_admin,
)
from file_repo import (
    list_files_for_user,
    get_file_for_user,
    insert_file,
    delete_file_record_for_user,
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "DevOpsSecretKey")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_PERMANENT=False,
)

RUN_ID = os.urandom(16).hex()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
if not os.path.isabs(UPLOAD_DIR):
    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), UPLOAD_DIR)
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", "10485760"))

_ALERT_LAST_SENT = {} 


def trigger_github_login_alert(username: str):
    if os.getenv("ENABLE_GH_LOGIN_ALERTS", "0") != "1":
        return

    owner = (os.getenv("GITHUB_OWNER") or "").strip()
    repo = (os.getenv("GITHUB_REPO") or "").strip()
    pat = (os.getenv("GITHUB_PAT") or "").strip()
    if not owner or not repo or not pat:
        return

    ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "").split(",")[0].strip()
    ua = (request.headers.get("User-Agent") or "")[:120]

    # Cooldown to avoid spamming Actions
    cooldown = int(os.getenv("LOGIN_ALERT_COOLDOWN", "30"))
    key = f"{username}|{ip}"
    now = time.time()
    last = _ALERT_LAST_SENT.get(key, 0)
    if now - last < cooldown:
        return
    _ALERT_LAST_SENT[key] = now

    url = f"https://api.github.com/repos/{owner}/{repo}/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {pat}",
        "User-Agent": "devops-file-portal",
    }
    payload = {
        "event_type": "login_failed",
        "client_payload": {
            "username": username,
            "ip": ip,
            "user_agent": ua,
            "note": "Invalid username/password attempt (demo monitoring alert)",
        },
    }

    try:
        requests.post(url, headers=headers, json=payload, timeout=5)
    except Exception:
        pass


def build_message_html() -> str:
    msgs = get_flashed_messages(with_categories=True)
    if not msgs:
        return ""
    out = ['<div class="messages">']
    for cat, m in msgs:
        cls = "msg-success" if cat == "success" else "msg-error"
        out.append(f'<div class="msg {cls}">{escape(m)}</div>')
    out.append("</div>")
    return "".join(out)


def build_users_rows_html(users, current_user_id) -> str:
    rows = []
    cur_uid = int(current_user_id) if current_user_id is not None else -1

    for u in users:
        real_id = int(u["id"])
        display_id = int(u["display_id"])
        username = escape(u["username"])
        role = escape(u["role"])
        created_at = escape(u["created_at"])

        if real_id == cur_uid:
            delete_cell = '<span class="muted">—</span>'
        else:
            delete_cell = (
                f'<form method="POST" action="/admin/delete_user/{real_id}" '
                f'onsubmit="return confirm(\'Delete this user?\')">'
                f'<button class="btn btn-danger" type="submit" style="width:auto;">Delete</button>'
                f"</form>"
            )

        rows.append(
            "<tr>"
            f"<td>{display_id}</td>"
            f"<td>{username}</td>"
            f"<td>{role}</td>"
            f"<td>{created_at}</td>"
            f"<td>{delete_cell}</td>"
            "</tr>"
        )

    if not rows:
        return '<tr><td colspan="5" class="muted">No users found.</td></tr>'

    return "".join(rows)


def build_files_rows_html(files) -> str:
    def fmt_dt(s: str) -> str:
        try:
            date_part, time_part = s.split(" ")
            y, m, d = date_part.split("-")
            hh, mm, _ss = time_part.split(":")
            return f"{d}/{m}/{y} {hh}:{mm}"
        except Exception:
            return escape(s)

    rows = []
    for f in files:
        fid = int(f["id"])
        fname = escape(f["original_filename"])
        size = f["file_size"] if f["file_size"] else "-"
        uploaded_at_raw = f["uploaded_at"] or ""
        uploaded_at = fmt_dt(str(uploaded_at_raw))

        rows.append(
            "<tr>"
            f"<td>{fid}</td>"
            f"<td>{fname}</td>"
            f"<td>{size}</td>"
            f"<td>{uploaded_at}</td>"
            "<td>"
            '<div class="actions-row">'
            f'<a class="action-link" href="/dashboard/download/{fid}">Download</a>'
            f'<form method="POST" action="/dashboard/delete/{fid}" '
            f'onsubmit="return confirm(\'Delete this file?\')">'
            f'<button class="btn btn-danger delete-btn" type="submit">Delete</button>'
            f"</form>"
            "</div>"
            "</td>"
            "</tr>"
        )

    if not rows:
        return '<tr><td colspan="5" class="muted">No files uploaded yet.</td></tr>'

    return "".join(rows)



# Session invalidation on restart
@app.before_request
def invalidate_sessions_on_restart():
    if request.endpoint in ("login", "static") or request.endpoint is None:
        return
    if "user_id" in session and session.get("run_id") != RUN_ID:
        session.clear()
        return redirect(url_for("login"))


# Routes
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session and session.get("run_id") == RUN_ID:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if not username or not password:
            flash("Please enter username and password.", "error")
            return render_template("login.html", message_html=build_message_html())

        user = get_user_by_username(username)
        if not user or not check_password_hash(user["password_hash"], password):
            trigger_github_login_alert(username)
            flash("Invalid username or password.", "error")
            return render_template("login.html", message_html=build_message_html())

        session.clear()
        session["user_id"] = int(user["id"])
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["run_id"] = RUN_ID
        session.permanent = False

        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("dashboard"))

    return render_template("login.html", message_html=build_message_html())


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    users = list_all_users()
    return render_template(
        "admin.html",
        username=session.get("username", ""),
        message_html=build_message_html(),
        users_rows_html=build_users_rows_html(users, session.get("user_id")),
    )


@app.route("/admin/create_user", methods=["POST"])
@admin_required
def admin_create_user():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    if not username or not password:
        flash("Username and password required.", "error")
        return redirect(url_for("admin_dashboard"))

    try:
        create_user(username, password, "user")
        flash(f"User '{username}' created.", "success")
    except Exception:
        flash("Failed to create user. Username may already exist.", "error")

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    if session.get("user_id") == user_id:
        flash("You cannot delete your own account while logged in.", "error")
        return redirect(url_for("admin_dashboard"))

    delete_user(user_id)
    flash("User deleted.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    user_id = int(session["user_id"])
    files = list_files_for_user(user_id)

    return render_template(
        "dashboard.html",
        username=session.get("username", ""),
        message_html=build_message_html(),
        files_rows_html=build_files_rows_html(files),
    )


@app.route("/dashboard/upload", methods=["POST"])
@login_required
def dashboard_upload():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    if "file" not in request.files:
        flash("No file part.", "error")
        return redirect(url_for("dashboard"))

    f = request.files["file"]
    if not f or not f.filename or f.filename.strip() == "":
        flash("No file selected.", "error")
        return redirect(url_for("dashboard"))

    user_id = int(session["user_id"])

    original_name = secure_filename(f.filename)
    unique_name = f"{uuid.uuid4().hex}_{original_name}"
    save_path = os.path.join(UPLOAD_DIR, unique_name)

    f.save(save_path)

    try:
        file_size = os.path.getsize(save_path)
    except Exception:
        file_size = None

    insert_file(
        user_id=user_id,
        original_filename=original_name,
        stored_filename=unique_name,
        content_type=f.mimetype,
        file_size=file_size,
        storage_path=save_path,
    )

    flash("File uploaded successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/dashboard/download/<int:file_id>", methods=["GET"])
@login_required
def dashboard_download(file_id: int):
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    user_id = int(session["user_id"])
    row = get_file_for_user(user_id, file_id)
    if not row:
        abort(404)

    return send_from_directory(
        UPLOAD_DIR,
        row["stored_filename"],
        as_attachment=True,
        download_name=row["original_filename"],
    )


@app.route("/dashboard/delete/<int:file_id>", methods=["POST"])
@login_required
def dashboard_delete(file_id: int):
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    user_id = int(session["user_id"])
    row = get_file_for_user(user_id, file_id)
    if not row:
        flash("File not found.", "error")
        return redirect(url_for("dashboard"))

    file_path = os.path.join(UPLOAD_DIR, row["stored_filename"])

    deleted = delete_file_record_for_user(user_id, file_id)
    if deleted:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        flash("File deleted.", "success")
    else:
        flash("Failed to delete file.", "error")

    return redirect(url_for("dashboard"))



init_db()
ensure_seed_admin()

if os.getenv("SHOW_STARTUP_BANNER", "1") == "1":
    sys.stdout.write("\n===================================\n")
    sys.stdout.write("File Portal is running!\n")
    sys.stdout.write("Open in browser: http://127.0.0.1:5000/login\n")
    sys.stdout.write("===================================\n\n")
    sys.stdout.flush()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
