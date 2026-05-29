#!/usr/bin/env python3
"""
run_migration.py
────────────────
Drop this script in your POTIFOLIO/ root folder and run it once.
It will:
  1. Create the Flask folder structure
  2. Copy & patch all your HTML files (fix paths to url_for)
  3. Copy all CSS and images into static/
  4. Print a summary

Usage:
    python run_migration.py
"""

import os, shutil, re

# ── Config: adjust BASE if your project root is elsewhere ─────────────────────
BASE    = os.path.dirname(os.path.abspath(__file__))   # folder this script lives in
OUT     = os.path.join(BASE, 'flask_output')           # where to write the result

# ── Folder map ────────────────────────────────────────────────────────────────
DIRS = [
    'templates/pages',
    'templates/downloads',
    'templates/admin',
    'static/css',
    'static/images/icons',
    'static/images/achievements',
    'uploads',
]

# ── Route map:  old href  →  Flask url_for call ───────────────────────────────
ROUTE_MAP = {
    'index.html':           "{{ url_for('index') }}",
    '../index.html':        "{{ url_for('index') }}",
    'pages/abouts.html':    "{{ url_for('about') }}",
    'abouts.html':          "{{ url_for('about') }}",
    '../pages/abouts.html': "{{ url_for('about') }}",
    'pages/publications.html':    "{{ url_for('publications') }}",
    'publications.html':          "{{ url_for('publications') }}",
    '../pages/publications.html': "{{ url_for('publications') }}",
    'pages/gallery.html':    "{{ url_for('gallery') }}",
    'gallery.html':          "{{ url_for('gallery') }}",
    '../pages/gallery.html': "{{ url_for('gallery') }}",
    'pages/contact.html':    "{{ url_for('contact') }}",
    'contact.html':          "{{ url_for('contact') }}",
    '../pages/contact.html': "{{ url_for('contact') }}",
}

# ── CSS path map ──────────────────────────────────────────────────────────────
CSS_MAP = {
    'styles/style.css':           'css/style.css',
    '../styles/style.css':        'css/style.css',
    'styles/abouts.css':          'css/abouts.css',
    '../styles/abouts.css':       'css/abouts.css',
    'styles/contact.css':         'css/contact.css',
    '../styles/contact.css':      'css/contact.css',
    'styles/gallery.css':         'css/gallery.css',
    '../styles/gallery.css':      'css/gallery.css',
    'styles/publications.css':    'css/publications.css',
    '../styles/publications.css': 'css/publications.css',
}

def url_for_static(path):
    return "{{ url_for('static', filename='" + path + "') }}"

def patch_html(content, is_subpage=False):
    """Fix all paths in an HTML file."""

    # 1. CSS links:  href="styles/style.css"  →  href="{{ url_for(...) }}"
    def replace_css(m):
        quote = m.group(1)
        path  = m.group(2)
        for old, new in CSS_MAP.items():
            if path == old:
                return f'href={quote}{url_for_static(new)}{quote}'
        return m.group(0)
    content = re.sub(r'href=(["\'])(.*?\.css)\1', replace_css, content)

    # 2. Nav href links
    def replace_href(m):
        quote = m.group(1)
        path  = m.group(2)
        for old, new in ROUTE_MAP.items():
            if path == old:
                return f'href={quote}{new}{quote}'
        return m.group(0)
    content = re.sub(r'href=(["\'])([^"\'#\s]+\.html)\1', replace_href, content)

    # 3. Image src:  src="images/..."  or  src="../images/..."
    def replace_img(m):
        quote    = m.group(1)
        src_path = m.group(2)
        # Normalise prefix
        clean = src_path.lstrip('.').lstrip('/')
        # Map   images/xxx  →  static filename
        if clean.startswith('images/'):
            return f'src={quote}{url_for_static(clean)}{quote}'
        return m.group(0)
    content = re.sub(r'src=(["\'])((?:\.\.\/)?images\/[^"\']+)\1', replace_img, content)

    return content


def main():
    print("=" * 60)
    print("  Flask Migration Script — Dr. MAH Portfolio")
    print("=" * 60)

    # Create output dirs
    for d in DIRS:
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    print(f"\n✓ Created folder structure in: {OUT}/\n")

    # ── Patch HTML files ──────────────────────────────────────────
    html_jobs = [
        (os.path.join(BASE, 'index.html'),             os.path.join(OUT, 'templates/index.html'),             False),
        (os.path.join(BASE, 'pages/abouts.html'),      os.path.join(OUT, 'templates/pages/abouts.html'),      True),
        (os.path.join(BASE, 'pages/publications.html'),os.path.join(OUT, 'templates/pages/publications.html'),True),
        (os.path.join(BASE, 'pages/gallery.html'),     os.path.join(OUT, 'templates/pages/gallery.html'),     True),
        (os.path.join(BASE, 'pages/contact.html'),     os.path.join(OUT, 'templates/pages/contact.html'),     True),
    ]

    for src, dst, is_sub in html_jobs:
        if os.path.exists(src):
            with open(src, 'r', encoding='utf-8') as f:
                content = f.read()
            patched = patch_html(content, is_sub)
            with open(dst, 'w', encoding='utf-8') as f:
                f.write(patched)
            print(f"  ✓ Patched  {os.path.relpath(src, BASE)}  →  templates/{os.path.relpath(dst, os.path.join(OUT,'templates'))}")
        else:
            print(f"  ⚠ Not found (skip): {os.path.relpath(src, BASE)}")

    # ── Copy CSS ──────────────────────────────────────────────────
    print()
    styles_dir = os.path.join(BASE, 'styles')
    if os.path.isdir(styles_dir):
        for fn in os.listdir(styles_dir):
            if fn.endswith('.css'):
                shutil.copy2(os.path.join(styles_dir, fn),
                             os.path.join(OUT, 'static/css', fn))
                print(f"  ✓ CSS  styles/{fn}  →  static/css/{fn}")
    else:
        print("  ⚠ styles/ folder not found")

    # ── Copy images ───────────────────────────────────────────────
    print()
    images_dir = os.path.join(BASE, 'images')
    if os.path.isdir(images_dir):
        for root, dirs, files in os.walk(images_dir):
            for fn in files:
                src_path = os.path.join(root, fn)
                rel      = os.path.relpath(src_path, images_dir)
                dst_path = os.path.join(OUT, 'static/images', rel)
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)
                print(f"  ✓ Image  images/{rel}  →  static/images/{rel}")
    else:
        print("  ⚠ images/ folder not found (copy manually later)")

    # ── Copy app.py + requirements if present ─────────────────────
    print()
    for fn in ['app.py', 'requirements.txt']:
        src = os.path.join(BASE, fn)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(OUT, fn))
            print(f"  ✓ Copied  {fn}")

    # ── Summary ───────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  DONE! Your Flask project is ready in:  flask_output/")
    print("=" * 60)
    print("""
NEXT STEPS:
  1. cd flask_output/
  2. pip install -r requirements.txt
  3. Create DB:  psql -U postgres -c "CREATE DATABASE dr_ali_portfolio;"
  4. python app.py
  5. Open  http://localhost:5000

  Admin panel:   http://localhost:5000/admin
  Downloads:     http://localhost:5000/downloads
  Login:         admin / admin123
""")


if __name__ == '__main__':
    main()
