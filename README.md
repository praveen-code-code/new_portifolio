# Dr. Mohammed Ali Hussain — Downloads Portal
### Flask + PostgreSQL PDF Management System

---

## 📁 Project Structure

```
dr_ali_downloads/
├── app.py                  # Flask application (routes, models, logic)
├── requirements.txt        # Python dependencies
├── setup.sh                # Quick-start script
├── README.md
├── uploads/                # Uploaded PDF files (auto-created)
└── templates/
    ├── index.html           # Public downloads page
    ├── admin_login.html     # Admin login
    └── admin_dashboard.html # Admin panel
```

---

## 🚀 Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create PostgreSQL database
```bash
psql -U postgres
CREATE DATABASE dr_ali_downloads;
\q
```

### 3. Configure database (optional)
```bash
export DATABASE_URL="postgresql://your_user:your_pass@localhost:5432/dr_ali_downloads"
```
Default (no env var): `postgresql://postgres:postgres@localhost:5432/dr_ali_downloads`

### 4. Run
```bash
python app.py
```

Tables are created automatically on first run.  
Default admin is seeded: **username: `admin`** / **password: `admin123`**

---

## 🌐 URLs

| URL | Description |
|-----|-------------|
| `http://localhost:5000/` | Public downloads page |
| `http://localhost:5000/admin` | Admin dashboard |
| `http://localhost:5000/admin/login` | Admin login |
| `http://localhost:5000/download/<id>` | Download a PDF |

---

## 🔐 Admin Features
- Upload PDFs (drag & drop or browse)
- Set title, description, category
- Mark PDFs as **Featured** (appear at top of public page)
- Edit or delete any PDF
- Manage categories (add / delete)
- View download counts

## 👥 Public Features
- Browse all PDFs in a card grid
- Filter by category
- Full-text search (title + description)
- Featured section at top
- One-click PDF download
- Download count per document

---

## 🔒 Production Notes
- Change `SECRET_KEY` in `app.py` or set `SECRET_KEY` env var
- Change the default admin password after first login (add a change-password route)
- Use `gunicorn` or `uWSGI` instead of Flask's dev server
- Store uploads on S3 / cloud storage for production
- Enable HTTPS