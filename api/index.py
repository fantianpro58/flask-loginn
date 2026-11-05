"""
Template Flask Login -> Dashboard
Deploy: Vercel | Database: Supabase (PostgreSQL)
"""
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

try:
    from zoneinfo import ZoneInfo
    WIB = ZoneInfo("Asia/Jakarta")
except Exception:
    WIB = timezone(timedelta(hours=7))

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.pool import NullPool
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ganti-secret-key-ini")

# DATABASE_URL diambil dari Environment Variable (Vercel / file .env lokal).
# Gunakan connection string "Transaction pooler" Supabase (port 6543).
db_url = os.environ.get("DATABASE_URL") or "sqlite:///local.db"
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
    created_at = db.Column(db.DateTime(timezone=True), default=db.func.now())


BULAN_ID = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]
HARI_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def to_wib(dt):
    """Konversi objek datetime ke zona waktu WIB (Asia/Jakarta, UTC+7)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Jika naive datetime dari database, asumsikan UTC lalu ubah ke WIB
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(WIB)


def format_tanggal_indonesia(dt, with_time=False):
    """Format tanggal ke bahasa Indonesia dalam zona waktu WIB."""
    if dt is None:
        return "-"
    dt_wib = to_wib(dt)
    hari = HARI_ID[dt_wib.weekday()]
    bulan = BULAN_ID[dt_wib.month]
    if with_time:
        return f"{dt_wib.day} {bulan} {dt_wib.year}, {dt_wib.strftime('%H:%M')} WIB"
    return f"{hari}, {dt_wib.day} {bulan} {dt_wib.year}"


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
    # Menggunakan zona waktu WIB (Asia/Jakarta, UTC+7)
    now_wib = datetime.now(WIB)
    today_wib_start = datetime(now_wib.year, now_wib.month, now_wib.day, tzinfo=WIB)
    seven_days_ago_wib = now_wib - timedelta(days=7)

    total_user = User.query.count()
    user_hari_ini = User.query.filter(User.created_at >= today_wib_start).count()
    user_7_hari = User.query.filter(User.created_at >= seven_days_ago_wib).count()
    tanggal_hari_ini = format_tanggal_indonesia(now_wib)

    # 1. Grafik garis: User baru per hari selama 7 hari terakhir dalam WIB
    line_labels = []
    line_data = []
    for i in range(6, -1, -1):
        target_day = (now_wib - timedelta(days=i)).date()
        day_wib_start = datetime(target_day.year, target_day.month, target_day.day, tzinfo=WIB)
        day_wib_end = day_wib_start + timedelta(days=1)
        count = User.query.filter(
            User.created_at >= day_wib_start,
            User.created_at < day_wib_end
        ).count()
        line_labels.append(f"{target_day.day} {BULAN_ID[target_day.month][:3]}")
        line_data.append(count)

    # 2. Grafik donut: Komposisi user baru 7 hari vs user lama
    user_lama = max(0, total_user - user_7_hari)
    donut_labels = ["User Baru (7 Hari)", "User Lama"]
    donut_data = [user_7_hari, user_lama]

    # 3. Tabel user terbaru: 5 user terakhir (tanggal dalam zona waktu WIB)
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()
    user_terbaru = []
    for u in recent_users:
        nama_tampil = u.nama or u.username
        initial = (nama_tampil[0] if nama_tampil else "U").upper()
        tgl_daftar = format_tanggal_indonesia(u.created_at, with_time=True)
        user_terbaru.append({
            "id": u.id,
            "nama": nama_tampil,
            "username": u.username,
            "initial": initial,
            "tanggal_daftar": tgl_daftar,
            "status": "Aktif"
        })

    return render_template(
        "dashboard.html",
        nama=session.get("nama", "User"),
        total_user=total_user,
        user_hari_ini=user_hari_ini,
        user_7_hari=user_7_hari,
        tanggal_hari_ini=tanggal_hari_ini,
        line_labels=line_labels,
        line_data=line_data,
        donut_labels=donut_labels,
        donut_data=donut_data,
        user_terbaru=user_terbaru,
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("Anda telah logout.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
