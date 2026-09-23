#!/usr/bin/env python3
"""Publie un brouillon EN ou NL sur le blog JCODE Agency (pages en/blog/ ou nl/blog/).

Usage :
  python3 publish_article_lang.py BROUILLON.md en|nl [fr=/blog/x.html] [en=/en/blog/y.html] [nl=/nl/blog/z.html] [--check]

--check : lance seulement les controles, n'ecrit rien.
fr=, en=, nl= : chemins des versions du meme article (pour les balises hreflang).
"""
import html as htmlmod
import json
import os
import re
import sys
import unicodedata
from datetime import date

ROOT = os.path.expanduser("~/jcode-agency")
BASE = "https://jcode.store"
REFERENCE_ARTICLE = os.path.join(ROOT, "blog", "pro-max-reservation-auto-chatbot-ia.html")
GUMROAD = "https://5530461069795.gumroad.com/l/BOT_TEAM"
MARKER = '<div class="articles-grid" data-i18n-html="blog.index.grid">'

UI = {
    "en": {
        "cat": "Automation &amp; AI", "read": "min read", "more": "Read the article →",
        "back": "← Back to blog", "rights": "© 2026 JCODE Agency. All rights reserved.",
        "legal": "Legal notice", "privacy": "Privacy policy",
        "home": "Home", "services": "Services", "blog": "Blog", "start": "Get started →",
        "months": ["January", "February", "March", "April", "May", "June", "July",
                   "August", "September", "October", "November", "December"],
        "fmt": "{month} {day}, {year}",
    },
    "nl": {
        "cat": "Automatisering &amp; AI", "read": "min leestijd", "more": "Lees het artikel →",
        "back": "← Terug naar de blog", "rights": "© 2026 JCODE Agency. Alle rechten voorbehouden.",
        "legal": "Wettelijke vermeldingen", "privacy": "Privacybeleid",
        "home": "Home", "services": "Diensten", "blog": "Blog", "start": "Aan de slag →",
        "months": ["januari", "februari", "maart", "april", "mei", "juni", "juli",
                   "augustus", "september", "oktober", "november", "december"],
        "fmt": "{day} {month} {year}",
    },
}

TEMPLATE = """<!DOCTYPE html>
<html lang="@@LANG@@">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>@@TITLE@@ | JCODE Agency</title>
    <meta name="description" content="@@DESC@@">
    <meta property="og:title" content="@@TITLE@@">
    <meta property="og:description" content="@@DESC@@">
    <meta property="og:type" content="article">
    <meta property="og:url" content="@@URL@@">
    <meta property="og:image" content="https://jcode.store/blog-og.png">
    <meta property="article:published_time" content="@@TODAY@@">
    <meta property="article:author" content="JCODE Agency">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="@@TITLE@@">
    <meta name="twitter:description" content="@@DESC@@">
    <link rel="canonical" href="@@URL@@">
@@HREFLANG@@
    @@STYLE@@
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": @@JSON_TITLE@@,
        "description": @@JSON_DESC@@,
        "image": "https://jcode.store/blog-og.png",
        "datePublished": "@@TODAY@@",
        "inLanguage": "@@LANG@@",
        "author": {"@type": "Organization", "name": "JCODE Agency", "url": "https://jcode.store"},
        "publisher": {"@type": "Organization", "name": "JCODE Agency", "url": "https://jcode.store"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": "@@URL@@"}
    }
    </script>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="/@@LANG@@/" class="logo"><div class="logo-icon">J</div><span>JCODE Agency</span></a>
            <div class="nav-links">
                <a href="/@@LANG@@/">@@HOME@@</a>
                <a href="/@@LANG@@/#services">@@SERVICES@@</a>
                <a href="/@@LANG@@/blog/">@@BLOG@@</a>
                <a href="https://jcode.store/@@LANG@@/" class="btn-primary">@@START@@</a>
            </div>
        </div>
    </nav>
    <header class="article-header">
        <div class="article-container">
            <span class="article-category">@@CAT@@</span>
            <h1>@@TITLE@@</h1>
            <div class="article-meta">
                <time datetime="@@TODAY@@">@@DATE@@</time>
                <span>•</span>
                <span>@@READ@@ @@READ_LABEL@@</span>
            </div>
        </div>
    </header>
    <article class="article-content">
        @@BODY@@
    </article>
    <footer class="footer">
        <div class="footer-content">
            <p>@@RIGHTS@@</p>
            <p><a href="/@@LANG@@/blog/" style="color: var(--primary-indigo); text-decoration: none;">@@BACK@@</a></p>
        </div>
        <p style="margin-top: 1rem; font-size: 0.875rem; text-align: center; color: var(--text-secondary);">
            <a href="/mentions-legales.html" style="color: var(--text-secondary); text-decoration: underline;">@@LEGAL@@</a> •
            <a href="/privacy-policy.html" style="color: var(--text-secondary); text-decoration: underline;">@@PRIVACY@@</a>
        </p>
    </footer>
</body>
</html>
"""


def fail(msg):
    print("❌ " + msg)
    sys.exit(1)


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) <= 60:
        return s
    cut = s[:60]
    d = cut.rfind("-")
    return cut[:d] if d > 20 else cut


def local_exists(path):
    path = path.split("#")[0].split("?")[0]
    full = os.path.join(ROOT, path.lstrip("/"))
    if path == "" or path.endswith("/") or os.path.isdir(full):
        return os.path.exists(os.path.join(full, "index.html"))
    return os.path.exists(full)


def md_inline(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\(((?:https?://|/)[^)\s]+)\)",
               r'<a href="\2" style="color: var(--primary-indigo);">\1</a>', s)
    s = re.sub(r"\*([^*\n]+)\*", r"<em>\1</em>", s)
    return s


def md_to_html(md):
    blocks = md.split("\n\n")
    out = []
    in_list = False
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith("## "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<h2>%s</h2>" % md_inline(block[3:].strip()))
        elif block.startswith("# "):
            continue
        elif block == "---":
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<hr>")
        elif block.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            for item in block.split("\n"):
                if item.startswith("- "):
                    out.append("<li>%s</li>" % md_inline(item[2:].strip()))
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            m = re.fullmatch(r"\[([^\]]+)\]\(((?:https?://|/)[^)\s]+)\)", block)
            if m:
                out.append('<p><a href="%s" style="display: inline-block; padding: 14px 28px; '
                           'background: var(--primary-indigo); color: #ffffff; border-radius: 10px; '
                           'text-decoration: none; font-weight: 600;">%s</a></p>' % (m.group(2), m.group(1)))
            else:
                out.append("<p>%s</p>" % md_inline(block))
    if in_list:
        out.append("</ul>")
    return "\n        ".join(out)


# ---------- arguments ----------
args = [a for a in sys.argv[1:] if not a.startswith("--")]
check_only = "--check" in sys.argv
if len(args) < 2 or args[1] not in UI:
    print(__doc__)
    sys.exit(1)
draft_path, lang = os.path.expanduser(args[0]), args[1]
alts = {}
for a in args[2:]:
    if "=" in a:
        k, v = a.split("=", 1)
        if k in ("fr", "en", "nl"):
            alts[k] = v
ui = UI[lang]

# ---------- lecture du brouillon ----------
with open(draft_path, encoding="utf-8") as f:
    raw = f.read()
meta = {}
m = re.match(r"\s*---\n(.*?)\n---\s*\n", raw, re.S)
if m:
    for line in m.group(1).split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    raw = raw[m.end():]
raw = re.sub(r"\n---\n\*\[[^\]]*\]\*\s*$", "", raw, flags=re.S)  # note finale entre crochets pour l'humain
raw = raw.strip()
if not raw.startswith("# ") and meta.get("title"):
    raw = "# " + meta["title"] + "\n\n" + raw
lines = raw.split("\n")
title = lines[0].lstrip("#").strip()
body_md = "\n".join(lines[1:]).strip()
slug = slugify(meta["slug"]) if meta.get("slug") else slugify(title)

# ---------- controles bloquants ----------
problems = []
if not raw.startswith("# "):
    problems.append("le brouillon ne commence pas par un titre « # … »")
if not title or not slug:
    problems.append("titre ou slug vide")
for ph in re.findall(r"\[[^\]\n]+\](?!\()", body_md):
    problems.append("crochet non rempli : " + ph[:60])
if re.search(r"calendly", raw, re.I):
    problems.append("mention de Calendly (cet outil n'existe pas)")
for e in sorted(set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", raw))):
    problems.append("adresse e-mail : " + e)
targets = set(re.findall(r"\]\(([^)\s]+)\)", raw))
targets |= set(t.rstrip(".,;:!?") for t in re.findall(r"https?://[^\s)\]\"<>]+", raw))
targets |= set(re.findall(r"mailto:[^\s)\]\"<>]+", raw))
for t in sorted(targets):
    if t.startswith("mailto:"):
        problems.append("lien mailto : " + t)
    elif t == GUMROAD:
        continue
    else:
        mm = re.match(r"^https://jcode\.store(/.*)?$", t)
        if mm:
            path = mm.group(1) or ""
        elif t.startswith("/"):
            path = t
        else:
            problems.append("lien non autorisé : " + t)
            continue
        if not local_exists(path):
            problems.append("page introuvable sur le site : " + t)
if problems:
    print("❌ Publication bloquée, %d problème(s) :" % len(problems))
    for p in problems:
        print("   - " + p)
    sys.exit(1)

filename = slug + ".html"
print("✅ Contrôles OK — langue : %s | slug : %s" % (lang, slug))
print("   titre : " + title)
if check_only:
    sys.exit(0)

# ---------- construction de la page ----------
today_d = date.today()
today = today_d.isoformat()
today_fmt = ui["fmt"].format(month=ui["months"][today_d.month - 1], day=today_d.day, year=today_d.year)
read_min = max(1, round(len(body_md.split()) / 200))
paras = [p.strip() for p in body_md.split("\n\n") if p.strip() and not p.strip().startswith("#")]
first = re.sub(r"\*\*(.*?)\*\*", r"\1", paras[0]) if paras else title
first = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", first)
description = (first[:155] + "…") if len(first) > 155 else first

with open(REFERENCE_ARTICLE, encoding="utf-8") as f:
    ref_html = f.read()
sm_style = re.search(r"<style>.*?</style>", ref_html, re.S)
if not sm_style:
    fail("aucun bloc <style> dans l'article de référence")

url = "%s/%s/blog/%s" % (BASE, lang, filename)
alts.setdefault(lang, "/%s/blog/%s" % (lang, filename))
hreflang_lines = []
for code in ("fr", "en", "nl"):
    if code in alts:
        hreflang_lines.append('    <link rel="alternate" hreflang="%s" href="%s%s">' % (code, BASE, alts[code]))
if "fr" in alts:
    hreflang_lines.append('    <link rel="alternate" hreflang="x-default" href="%s%s">' % (BASE, alts["fr"]))

tokens = {
    "LANG": lang, "TITLE": htmlmod.escape(title), "DESC": htmlmod.escape(description, quote=True),
    "URL": url, "TODAY": today, "HREFLANG": "\n".join(hreflang_lines), "STYLE": sm_style.group(0),
    "JSON_TITLE": json.dumps(title, ensure_ascii=False), "JSON_DESC": json.dumps(description, ensure_ascii=False),
    "HOME": ui["home"], "SERVICES": ui["services"], "BLOG": ui["blog"], "START": ui["start"],
    "CAT": ui["cat"], "DATE": today_fmt, "READ": str(read_min), "READ_LABEL": ui["read"],
    "BODY": md_to_html(body_md), "RIGHTS": ui["rights"], "BACK": ui["back"],
    "LEGAL": ui["legal"], "PRIVACY": ui["privacy"],
}
page = TEMPLATE
for k, v in tokens.items():
    page = page.replace("@@%s@@" % k, v)

page_dir = os.path.join(ROOT, lang, "blog")
os.makedirs(page_dir, exist_ok=True)
page_path = os.path.join(page_dir, filename)
if os.path.exists(page_path):
    fail("%s existe déjà — arrêt pour éviter d'écraser." % page_path)
with open(page_path, "w", encoding="utf-8") as f:
    f.write(page)
print("✅ Page écrite : " + page_path)

card_html = ('<a class="article-card" href="/%s/blog/%s">' % (lang, filename) +
             '<span class="article-category">%s</span>' % ui["cat"] +
             "<h2>%s</h2>" % htmlmod.escape(title) +
             "<p>%s</p>" % htmlmod.escape(description) +
             '<div class="article-meta"><span class="article-date">%s</span>' % today_fmt +
             '<span class="read-more">%s</span></div></a>' % ui["more"])

# 1) index statique en/blog ou nl/blog
idx_path = os.path.join(ROOT, lang, "blog", "index.html")
with open(idx_path, encoding="utf-8") as f:
    idx = f.read()
if filename in idx:
    print("⚠️  Déjà présent dans %s/blog/index.html, ignoré" % lang)
elif MARKER in idx:
    with open(idx_path, "w", encoding="utf-8") as f:
        f.write(idx.replace(MARKER, MARKER + "\n" + card_html, 1))
    with open(idx_path, encoding="utf-8") as f:
        if filename not in f.read():
            fail("insertion non vérifiée dans %s/blog/index.html" % lang)
    print("✅ Carte ajoutée dans %s/blog/index.html (vérifié)" % lang)
else:
    fail("marqueur introuvable dans %s/blog/index.html — rien écrit." % lang)

# 2) translations.json (source vivante de la grille)
tr_path = os.path.join(ROOT, "i18n", "translations.json")
with open(tr_path, encoding="utf-8") as f:
    data = json.load(f)
grid = data.setdefault("blog.index.grid", {})
if filename in grid.get(lang, ""):
    print("⚠️  Déjà présent dans translations.json (%s), ignoré" % lang)
else:
    grid[lang] = card_html + grid.get(lang, "")
    with open(tr_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(tr_path, encoding="utf-8") as f:
        if filename not in json.load(f)["blog.index.grid"][lang]:
            fail("insertion non vérifiée dans translations.json (%s)" % lang)
    print("✅ Carte ajoutée dans translations.json (%s, vérifié)" % lang)

# 3) sitemap.xml
sm_path = os.path.join(ROOT, "sitemap.xml")
with open(sm_path, encoding="utf-8") as f:
    sm = f.read()
if url in sm:
    print("⚠️  Déjà présent dans sitemap.xml, ignoré")
else:
    entry = ("  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n"
             "    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n" % (url, today))
    with open(sm_path, "w", encoding="utf-8") as f:
        f.write(sm.replace("</urlset>", entry + "</urlset>"))
    with open(sm_path, encoding="utf-8") as f:
        if url not in f.read():
            fail("insertion non vérifiée dans sitemap.xml")
    print("✅ Ajouté au sitemap.xml (vérifié)")

print("\nSlug: " + slug)
