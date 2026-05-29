import os, uuid
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, flash, send_from_directory, session, jsonify)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'drali-secret-key-2024')

database_url = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres:1616@localhost:5432/dr_ali_portfolio'
)

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)

# ── Models ────────────────────────────────────────────────────────────────────
class Admin(db.Model):
    __tablename__ = 'admins'
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    pw_hash  = db.Column(db.String(256), nullable=False)
    def set_password(self, pw): self.pw_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.pw_hash, pw)

class Category(db.Model):
    __tablename__ = 'categories'
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    pdfs = db.relationship('PDF', backref='category', lazy=True, cascade='all, delete-orphan')

class PDF(db.Model):
    __tablename__ = 'pdfs'
    id            = db.Column(db.Integer, primary_key=True)
    title         = db.Column(db.String(300), nullable=False)
    description   = db.Column(db.Text, default='')
    filename      = db.Column(db.String(300), nullable=False)
    original_name = db.Column(db.String(300), nullable=False)
    file_size     = db.Column(db.Integer, default=0)
    category_id   = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    uploaded_at   = db.Column(db.DateTime, default=datetime.utcnow)
    downloads     = db.Column(db.Integer, default=0)
    is_featured   = db.Column(db.Boolean, default=False)

    @property
    def size_str(self):
        if self.file_size < 1024: return f"{self.file_size} B"
        elif self.file_size < 1024**2: return f"{self.file_size/1024:.1f} KB"
        else: return f"{self.file_size/1024**2:.1f} MB"

# ── Helpers ───────────────────────────────────────────────────────────────────
def allowed_file(fn): return '.' in fn and fn.rsplit('.', 1)[1].lower() == 'pdf'

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_id'):
            flash('Please log in first.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('pages/abouts.html')

@app.route('/publications')
def publications():
    return render_template('pages/publications.html')

@app.route('/gallery')
def gallery():
    return render_template('pages/gallery.html')

@app.route('/contact')
def contact():
    return render_template('pages/contact.html')

# ══════════════════════════════════════════════════════════════════════════════
# DOWNLOADS PORTAL ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/downloads')
def downloads_index():
    search     = request.args.get('q', '').strip()
    cat_id     = request.args.get('cat', type=int)
    categories = Category.query.order_by(Category.name).all()
    query      = PDF.query
    if search:
        query = query.filter(db.or_(PDF.title.ilike(f'%{search}%'),
                                    PDF.description.ilike(f'%{search}%')))
    if cat_id:
        query = query.filter_by(category_id=cat_id)
    pdfs     = query.order_by(PDF.uploaded_at.desc()).all()
    featured = PDF.query.filter_by(is_featured=True).order_by(PDF.uploaded_at.desc()).limit(3).all()
    return render_template('downloads/index.html', pdfs=pdfs, categories=categories,
                           featured=featured, search=search, active_cat=cat_id)

@app.route('/downloads/get/<int:pdf_id>')
def download_file(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    pdf.downloads += 1
    db.session.commit()
    return send_from_directory(app.config['UPLOAD_FOLDER'], pdf.filename,
                               as_attachment=True, download_name=pdf.original_name)

# ── Admin auth ────────────────────────────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_id'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        admin = Admin.query.filter_by(username=request.form['username']).first()
        if admin and admin.check_password(request.form['password']):
            session['admin_id']   = admin.id
            session['admin_user'] = admin.username
            flash('Welcome back!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    pdfs       = PDF.query.order_by(PDF.uploaded_at.desc()).all()
    categories = Category.query.order_by(Category.name).all()
    total_dl   = db.session.query(db.func.sum(PDF.downloads)).scalar() or 0
    return render_template('admin/dashboard.html', pdfs=pdfs,
                           categories=categories, total_dl=total_dl)

@app.route('/admin/upload', methods=['POST'])
@login_required
def upload_pdf():
    file = request.files.get('pdf_file')
    if not file or file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('admin_dashboard'))
    if not allowed_file(file.filename):
        flash('Only PDF files are allowed.', 'error')
        return redirect(url_for('admin_dashboard'))
    original = secure_filename(file.filename)
    stored   = f"{uuid.uuid4().hex}_{original}"
    path     = os.path.join(app.config['UPLOAD_FOLDER'], stored)
    file.save(path)
    size     = os.path.getsize(path)
    cat_id   = request.form.get('category_id', type=int)
    new_cat  = request.form.get('new_category', '').strip()
    if new_cat:
        cat = Category.query.filter_by(name=new_cat).first()
        if not cat:
            cat = Category(name=new_cat); db.session.add(cat); db.session.flush()
        cat_id = cat.id
    pdf = PDF(title=request.form.get('title', original).strip() or original,
              description=request.form.get('description', '').strip(),
              filename=stored, original_name=original, file_size=size,
              category_id=cat_id or None,
              is_featured=bool(request.form.get('is_featured')))
    db.session.add(pdf); db.session.commit()
    flash(f'"{pdf.title}" uploaded successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/<int:pdf_id>', methods=['POST'])
@login_required
def edit_pdf(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    pdf.title       = request.form.get('title', pdf.title).strip()
    pdf.description = request.form.get('description', '').strip()
    pdf.is_featured = bool(request.form.get('is_featured'))
    cat_id  = request.form.get('category_id', type=int)
    new_cat = request.form.get('new_category', '').strip()
    if new_cat:
        cat = Category.query.filter_by(name=new_cat).first()
        if not cat:
            cat = Category(name=new_cat); db.session.add(cat); db.session.flush()
        cat_id = cat.id
    pdf.category_id = cat_id or None
    db.session.commit()
    flash('PDF updated.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:pdf_id>', methods=['POST'])
@login_required
def delete_pdf(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    try: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], pdf.filename))
    except FileNotFoundError: pass
    db.session.delete(pdf); db.session.commit()
    flash('PDF deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/category/delete/<int:cat_id>', methods=['POST'])
@login_required
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    db.session.delete(cat); db.session.commit()
    flash(f'Category "{cat.name}" deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_category', methods=['POST'])
@login_required
def add_category():
    data = request.get_json()
    name = (data or {}).get('name', '').strip()
    if not name: return jsonify({'ok': False, 'error': 'Name required'})
    if Category.query.filter_by(name=name).first():
        return jsonify({'ok': False, 'error': 'Already exists'})
    cat = Category(name=name); db.session.add(cat); db.session.commit()
    return jsonify({'ok': True, 'id': cat.id, 'name': cat.name})

# ── Init ──────────────────────────────────────────────────────────────────────
def init_db():
    db.create_all()
    if not Admin.query.first():
        a = Admin(username='admin'); a.set_password('admin123')
        db.session.add(a); db.session.commit()
        print("✓ Admin created  →  username: admin  |  password: admin123")

with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)