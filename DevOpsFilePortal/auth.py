from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            flash("Access denied: Admins only.", "error")
            return redirect(url_for("dashboard"))

        return view_func(*args, **kwargs)
    return wrapper
