from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from backend.database import get_db


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = get_db().execute(
            "SELECT * FROM admins WHERE username = ?",
            (username,),
        ).fetchone()

        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session.permanent = True
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            flash("Login successful.", "success")
            return redirect(url_for("dashboard.dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
