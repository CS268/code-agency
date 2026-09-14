import json, re, sys, os
from datetime import date

REFERENCE_ARTICLE = os.path.expanduser("~/jcode-agency/blog/pro-max-reservation-auto-chatbot-ia.html")

def extract_style_block(path):
    with open(path, encoding='utf-8') as f:
        html = f.read()
    m = re.search(r'<style>.*?</style>', html, re.S)
    if not m:
        raise SystemExit(f"ERREUR: aucun bloc <style> trouvé dans {path}")
    return m.group(0)

STYLE_BLOCK = extract_style_block(REFERENCE_ARTICLE)

DRAFT_PATH = sys.argv[1] if len(sys.argv) > 1 else None
if not DRAFT_PATH:
    print("Usage: python3 publish_article.py <chemin_vers_brouillon.md>")
    sys.exit(1)

with open(DRAFT_PATH, encoding='utf-8') as f:
    raw = f.read()

raw = re.sub(r'\n---\n\*\[Note pour l.humain.*?\]\*\s*$', '', raw, flags=re.S)

lines = raw.strip().split('\n')
title = lines[0].lstrip('#').strip()
body_md = '\n'.join(lines[1:]).strip()

def slugify(s):
    s = s.lower()
    s = re.sub(r'[àâä]', 'a', s); s = re.sub(r'[éèêë]', 'e', s)
    s = re.sub(r'[îï]', 'i', s); s = re.sub(r'[ôö]', 'o', s)
    s = re.sub(r'[ûüù]', 'u', s); s = re.sub(r'ç', 'c', s)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    if len(s) <= 60:
        return s
    truncated = s[:60]
    last_dash = truncated.rfind('-')
    return truncated[:last_dash] if last_dash > 20 else truncated

slug = slugify(title)
filename = f"{slug}.html"

paras = [p.strip() for p in body_md.split('\n\n') if p.strip() and not p.startswith('#')]
first_para = re.sub(r'\*\*(.*?)\*\*', r'\1', paras[0]) if paras else title
description = (first_para[:155] + '…') if len(first_para) > 155 else first_para

def md_to_html(md):
    md = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', md)
    blocks = md.split('\n\n')
    html = []
    in_list = False
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith('## '):
            if in_list:
                html.append('</ul>'); in_list = False
            html.append(f'<h2>{block[3:].strip()}</h2>')
        elif block.startswith('# '):
            continue
        elif block.startswith('- '):
            if not in_list:
                html.append('<ul>'); in_list = True
            for item in block.split('\n'):
                if item.startswith('- '):
                    html.append(f'<li>{item[2:].strip()}</li>')
        else:
            if in_list:
                html.append('</ul>'); in_list = False
            html.append(f'<p>{block}</p>')
    if in_list:
        html.append('</ul>')
    return '\n        '.join(html)

article_html = md_to_html(body_md)
today = date.today().isoformat()
today_fr = date.today().strftime('%-d %B %Y')
words = len(body_md.split())
read_min = max(1, round(words / 200))

TEMPLATE = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | JCODE Agency</title>
    <meta name="description" content="{description}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://jcode.store/blog/{filename}">
    <meta property="og:image" content="https://jcode.store/blog-og.png">
    <meta property="article:published_time" content="{today}">
    <meta property="article:author" content="JCODE Agency">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <link rel="canonical" href="https://jcode.store/blog/{filename}">
    {style_block}
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "{title}",
        "description": "{description}",
        "image": "https://jcode.store/blog-og.png",
        "datePublished": "{today}",
        "author": {{"@type": "Organization", "name": "JCODE Agency", "url": "https://jcode.store"}},
        "publisher": {{"@type": "Organization", "name": "JCODE Agency", "url": "https://jcode.store"}},
        "mainEntityOfPage": {{"@type": "WebPage", "@id": "https://jcode.store/blog/{filename}"}}
    }}
    </script>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="/" class="logo"><div class="logo-icon">J</div><span>JCODE Agency</span></a>
            <div class="nav-links">
                <a href="/">Accueil</a>
                <a href="/#services">Services</a>
                <a href="/blog">Blog</a>
                <a href="https://jcode.store" class="btn-primary">Démarrer →</a>
            </div>
        </div>
    </nav>
    <header class="article-header">
        <div class="article-container">
            <span class="article-category">Automatisation &amp; IA</span>
            <h1>{title}</h1>
            <div class="article-meta">
                <time datetime="{today}">{today_fr}</time>
                <span>•</span>
                <span>{read_min} min de lecture</span>
            </div>
        </div>
    </header>
    <article class="article-content">
        {article_html}
    </article>
    <footer class="footer">
        <div class="footer-content">
            <p>© 2026 JCODE Agency. Tous droits réservés.</p>
            <p><a href="/blog" style="color: var(--primary-indigo); text-decoration: none;">← Retour au blog</a></p>
        </div>
        <p style="margin-top: 1rem; font-size: 0.875rem; text-align: center; color: var(--text-secondary);">
            <a href="/mentions-legales.html" style="color: var(--text-secondary); text-decoration: underline;">Mentions légales</a> •
            <a href="/privacy-policy.html" style="color: var(--text-secondary); text-decoration: underline;">Politique de confidentialité</a>
        </p>
    </footer>
</body>
</html>
'''

html_out = TEMPLATE.format(title=title, description=description, filename=filename,
                            today=today, today_fr=today_fr, article_html=article_html, read_min=read_min,
                            style_block=STYLE_BLOCK)

blog_path = os.path.expanduser(f"~/jcode-agency/blog/{filename}")
if os.path.exists(blog_path):
    print(f"⚠️  {filename} existe déjà — arrêt pour éviter d'écraser.")
    sys.exit(1)
with open(blog_path, 'w', encoding='utf-8') as f:
    f.write(html_out)
print(f"✅ Article écrit : {blog_path}")

card_html = (f'<a class="article-card" href="/blog/{filename}">'
             f'<span class="article-category">Automatisation &amp; IA</span>'
             f'<h2>{title}</h2>'
             f'<p>{description}</p>'
             f'<div class="article-meta"><span class="article-date">{today_fr}</span>'
             f'<span class="read-more">Lire l\'article →</span></div></a>')

# 1) blog/index.html (fallback statique)
idx_path = os.path.expanduser("~/jcode-agency/blog/index.html")
with open(idx_path, encoding='utf-8') as f:
    idx = f.read()
marker = '<div class="articles-grid" data-i18n-html="blog.index.grid">'
if filename in idx:
    print("⚠️  Déjà présent dans blog/index.html, ignoré")
elif marker in idx:
    new_idx = idx.replace(marker, marker + '\n' + card_html, 1)
    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(new_idx)
    with open(idx_path, encoding='utf-8') as f:
        verify = f.read()
    if filename not in verify:
        print("❌ ÉCHEC: l'insertion dans blog/index.html n'a pas été vérifiée après écriture.")
        sys.exit(1)
    print("✅ Carte ajoutée dans blog/index.html (vérifié)")
else:
    print("❌ ÉCHEC: marqueur introuvable dans blog/index.html — rien écrit.")
    sys.exit(1)

# 2) translations.json (source vivante, langue fr uniquement pour l'instant)
tr_path = os.path.expanduser("~/jcode-agency/i18n/translations.json")
with open(tr_path, encoding='utf-8') as f:
    data = json.load(f)
grid_fr = data.get('blog.index.grid', {}).get('fr', '')
if filename in grid_fr:
    print("⚠️  Déjà présent dans translations.json (fr), ignoré")
else:
    data['blog.index.grid']['fr'] = card_html + grid_fr
    with open(tr_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(tr_path, encoding='utf-8') as f:
        verify_data = json.load(f)
    if filename not in verify_data['blog.index.grid']['fr']:
        print("❌ ÉCHEC: l'insertion dans translations.json n'a pas été vérifiée après écriture.")
        sys.exit(1)
    print("✅ Carte ajoutée dans translations.json (fr, vérifié)")

# 3) sitemap.xml
sm_path = os.path.expanduser("~/jcode-agency/sitemap.xml")
with open(sm_path, encoding='utf-8') as f:
    sm = f.read()
if filename in sm:
    print("⚠️  Déjà présent dans sitemap.xml, ignoré")
else:
    entry = (f'  <url>\n    <loc>https://jcode.store/blog/{filename}</loc>\n'
             f'    <lastmod>{today}</lastmod>\n    <changefreq>monthly</changefreq>\n'
             f'    <priority>0.7</priority>\n  </url>\n')
    sm = sm.replace('</urlset>', entry + '</urlset>')
    with open(sm_path, 'w', encoding='utf-8') as f:
        f.write(sm)
    with open(sm_path, encoding='utf-8') as f:
        verify_sm = f.read()
    if filename not in verify_sm:
        print("❌ ÉCHEC: l'insertion dans sitemap.xml n'a pas été vérifiée après écriture.")
        sys.exit(1)
    print("✅ Ajouté au sitemap.xml (vérifié)")

print(f"\nSlug: {slug}")
