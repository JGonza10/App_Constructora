from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from .extensions import limiter
from .forms import LoginForm
from .models import Usuario

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("8 per 15 minutes", methods=["POST"])
def login():
    if current_user.is_authenticated and current_user.tipo == "usuario":
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data.lower().strip(), activo=True).first()
        if usuario and usuario.check_password(form.password.data):
            login_user(usuario)
            return redirect(request.args.get("next") or url_for("main.dashboard"))
        flash("Credenciales inválidas.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
