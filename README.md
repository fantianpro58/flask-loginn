# Template Flask Login → Dashboard (Vercel + Supabase)

Aplikasi sederhana: halaman login → dashboard. Data user disimpan di database online **Supabase (PostgreSQL)**, aplikasi di-hosting di **Vercel**.

## Struktur Folder
```
api/
  index.py            ← aplikasi Flask (routes, model, koneksi DB)
  templates/
    base.html         ← layout & CSS
    login.html        ← halaman login
    dashboard.html    ← halaman setelah login
schema.sql            ← SQL pembuat tabel + user demo
buat_user.py          ← script menambah user (password di-hash)
requirements.txt
pyproject.toml        ← konfigurasi Vercel (lokasi app Flask)
.env.example
```

## Langkah 1 — Siapkan Database di Supabase
1. Daftar di https://supabase.com → **New project** (simpan password database!).
2. Buka **SQL Editor** → paste isi `schema.sql` → **Run**.
3. Buka **Connect** → pilih **Transaction pooler** → salin connection string (port **6543**).
   Ganti `[YOUR-PASSWORD]` dengan password database Anda.

## Langkah 2 — Coba di Komputer Sendiri (opsional)
```bash
python -m venv venv
venv\Scripts\activate          # Windows  (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # lalu isi DATABASE_URL & SECRET_KEY
python -c "from dotenv import load_dotenv; load_dotenv(); from api.index import app; app.run(debug=True)"
```
Buka http://127.0.0.1:5000 → login `admin` / `admin123`.

## Langkah 3 — Deploy ke Vercel
1. Upload project ke **GitHub** (file `.env` otomatis diabaikan oleh `.gitignore`).
2. Di https://vercel.com → **Add New → Project** → import repo.
3. Sebelum Deploy, buka **Environment Variables**, isi:
   | Name | Value |
   |---|---|
   | `DATABASE_URL` | connection string Transaction pooler Supabase |
   | `SECRET_KEY` | string acak panjang |
4. Klik **Deploy**. Setelah selesai, buka URL `*.vercel.app` dan login.

## Menambah User
```bash
python buat_user.py
```
Password otomatis di-hash. **Jangan pernah** insert password asli langsung ke tabel.

## Troubleshooting
| Masalah | Penyebab umum |
|---|---|
| `too many connections` / timeout | Memakai port 5432 (direct). Gunakan **Transaction pooler port 6543**. |
| Error 500 di Vercel | `DATABASE_URL` belum diisi → cek *Settings → Environment Variables*, lalu **Redeploy**. Lihat detail di tab **Logs**. |
| Login selalu gagal | Tabel/user belum dibuat → jalankan `schema.sql`. |
| Tiba-tiba tidak bisa connect | Project Supabase free ter-*pause* karena tidak aktif → buka dashboard Supabase, klik **Restore**. |

## Aturan Keamanan
- Jangan commit file `.env` atau connection string ke GitHub.
- Password selalu di-hash (`werkzeug.security`).
- Ganti/hapus user demo `admin` setelah testing.
