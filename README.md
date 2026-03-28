# 🛡️ NAF Encyclopedia System — Deployment Guide

## Demo Login Credentials

| Service Number   | Role        | Access Level              |
|-----------------|-------------|---------------------------|
| EAU/ADMIN/001   | Super Admin | Full access + Admin Panel |
| NAF/00/00/1247  | Officer     | General + Restricted       |
| NAF/09/03/2219  | NCO         | General content only       |
| GUEST/00/0001   | Guest       | Read-only, unclassified    |

---

## Option 1 — Deploy to Render (FREE, 5 minutes)

1. Create a free account at https://render.com
2. Click **New → Web Service**
3. Upload this folder OR connect a GitHub repo
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn server:app`
   - **Environment:** Python 3
5. Click **Deploy**
6. Your app is live at `https://your-app.onrender.com`

---

## Option 2 — Deploy to Railway (FREE, 3 minutes)

1. Create account at https://railway.app
2. Click **New Project → Deploy from GitHub** or drag-drop folder
3. Railway auto-detects Python + Procfile
4. Click **Deploy** — live in ~2 minutes

---

## Option 3 — Run Locally

```bash
# Install Python 3.8+
pip install -r requirements.txt
python server.py
# Open http://localhost:5000
```

---

## What's Working

- ✅ Service number authentication + JWT sessions
- ✅ Role-based access (Super Admin / Officer / NCO / Guest)
- ✅ Article browsing with real SQLite database
- ✅ Full-text search across all articles
- ✅ Admin panel — add/edit/deactivate users
- ✅ Admin panel — add/edit/delete articles
- ✅ Audit log — every login, view, search, admin action logged
- ✅ Content classification (Unclassified / Restricted / Confidential)
- ✅ Watermark display on all article views
- ✅ 10 pre-loaded articles across all categories
- ✅ 8 pre-loaded personnel accounts

## Notes

- Database is SQLite stored in `naf_encyclopedia.db` (auto-created on first run)
- On Render/Railway free tier, the DB resets on each deployment — use a persistent volume or PostgreSQL addon for production
- For production NAF deployment, replace SQLite with PostgreSQL and set `SECRET` as an environment variable
