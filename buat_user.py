"""
Script untuk membuat user baru (password otomatis di-hash).
Jalankan lokal:  python buat_user.py
Pastikan file .env sudah berisi DATABASE_URL Supabase.
"""
from getpass import getpass

from dotenv import load_dotenv
load_dotenv()

from werkzeug.security import generate_password_hash  # noqa: E402
from api.index import app, db, User  # noqa: E402

with app.app_context():
    db.create_all()  # membuat tabel users jika belum ada
    username = input("Username: ").strip()
    nama = input("Nama lengkap: ").strip()
    password = getpass("Password: ")

    if User.query.filter_by(username=username).first():
        print("Username sudah dipakai.")
    else:
        db.session.add(User(username=username, nama=nama,
                            password_hash=generate_password_hash(password)))
        db.session.commit()
        print(f"User '{username}' berhasil dibuat.")
