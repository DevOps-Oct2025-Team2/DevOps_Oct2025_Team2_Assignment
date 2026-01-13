import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from dotenv import load_dotenv

from db.db import init_db
from auth import login_required, admin_required
from user_repo import (
    get_user_by_username,
    list_all_users,
    create_user,
    delete_user,
    ensure_seed_admin
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")


@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if not username or not password:
            flash("Please enter username and password.", "error")
            return render_template("login.html")

        user = get_user_by_username(username)
        if not user:
            flash("Invalid username or password.", "error")
            return render_template("login.html")

        if not check_password_hash(user["password_hash"], password):
            flash("Invalid username or password.", "error")
            return render_template("login.html")

        session["user_id"] = int(user["id"])
        session["username"] = user["username"]
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("dashboard"))

    return render_template("login.html")


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
    return render_template("admin.html", users=users)


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
    return render_template("dashboard.html")


if __name__ == "__main__":
    init_db()
    ensure_seed_admin()
    app.run(debug=True, host="0.0.0.0", port=5000)
