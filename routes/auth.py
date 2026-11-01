from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash
)
from flask_login import (
    login_user, logout_user, login_required, current_user
)
from models import User

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):

            if user.is_suspended:
                flash("Your account has been suspended.", "danger")
                return redirect(url_for("auth.login"))

            login_user(user)
            flash("Welcome to AccessLoop!", "success")

            return redirect(url_for("auth.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():

    logout_user()
    flash("You have been logged out.", "success")

    return redirect(url_for("auth.login"))