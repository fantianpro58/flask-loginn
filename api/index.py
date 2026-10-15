"""
Template Flask Login -> Dashboard
Deploy: Vercel | Database: Supabase (PostgreSQL)
"""
import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.pool import NullPool
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ganti-secret-key-ini")

# DATABASE_URL diambil dari Environment Variable (Vercel / file .env lokal).
# Gunakan connection string "Transaction pooler" Supabase (port 6543).
db_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")
# Paksa pakai driver psycopg (versi 3) supaya cocok dengan requirements.txt
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# NullPool: tidak menahan koneksi, cocok untuk serverless (Vercel)
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": NullPool}

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nama = db.Column(db.String(100))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def index():
    return redirect(url_for("dashboard" if "user_id" in session else "login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            session["nama"] = user.nama or user.username
            return redirect(url_for("dashboard"))

        flash("Username atau password salah.", "danger")
    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    total_user = User.query.count()
    return render_template("dashboard.html", nama=session["nama"], total_user=total_user)


@app.route("/logout")
def logout():
    session.clear()
    flash("Anda telah logout.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
