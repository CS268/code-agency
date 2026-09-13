import os
import re
import io
import sys
import json
import datetime
import html as htmlmod
from html.parser import HTMLParser

ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else "."
BASE = "https://jcode.store"

PAGES = ["index.html", "ai-concierge.html", "aoa-framework.html", "promo-septembre.html", "blog/index.html"]
LOCALIZED = set(PAGES)

META = {
    "index.html": {
        "fr": ("JCODE Agency — Sites Web & Marketing Automatisé par IA",
               "JCODE Agency — Création de sites web professionnels pour entrepreneurs et PME. Sites vitrines, e-commerce et applications sur mesure."),
        "en": ("JCODE Agency — Websites & AI-Powered Marketing Automation",
               "JCODE Agency — Professional websites for entrepreneurs and SMEs in Belgium. Business websites, e-commerce and custom web applications built for you."),
        "nl": ("JCODE Agency — Websites & AI-marketingautomatisering",
               "JCODE Agency — Professionele websites voor ondernemers en KMO's in België. Websites, webshops en applicaties op maat."),
    },
    "ai-concierge.html": {
        "fr": ("AI Concierge — JCODE Agency | Automatisation IA pour commerces locaux",
               "Service AI Concierge done-with-you : 2 appels/mois, Voxer illimité, Hub Notion. Automatisez votre commerce avec l'IA."),
        "en": ("AI Concierge — JCODE Agency | AI Automation for Local Businesses",
               "Done-with-you AI Concierge service: 2 calls a month, unlimited Voxer, Notion Hub. Automate your local business with AI."),
        "nl": ("AI Concierge — JCODE Agency | AI-automatisering voor lokale handelaren",
               "Done-with-you AI Concierge-dienst: 2 gesprekken per maand, onbeperkte Voxer, Notion Hub. Automatiseer uw zaak met AI."),
    },
    "aoa-framework.html": {
        "fr": ("AOA Framework — JCODE Agency",
               "Le framework AOA de JCODE Agency : la méthode pour automatiser la présence en ligne des PME et commerces locaux."),
        "en": ("AOA Framework — JCODE Agency",
               "The JCODE Agency AOA framework: a method to automate the online presence of SMEs and local businesses."),
        "nl": ("AOA Framework — JCODE Agency",
               "Het AOA-framework van JCODE Agency: een methode om de online aanwezigheid van KMO's en lokale handelaren te automatiseren."),
    },
}

TITLE_KEYS = {"promo-septembre.html": "promo.title", "blog/index.html": "blog.index.title"}
DESC_KEYS = {"promo-septembre.html": "promo.desc", "blog/index.html": "blog.index.desc"}

GRID_CARD = {
    "fr": ('\n<a class="article-card" href="/alternatives/manychat.html">\n'
           '<span class="article-category">Alternatives</span>\n'
           "<h2>Alternative ManyChat pour Instagram : pourquoi les outils no-code atteignent leurs limites en 2026</h2>\n"
           "<p>ManyChat, InstantDM, LinkDM... comparatif honnête des outils SaaS, et pourquoi une automatisation IA sur mesure convertit mieux vos DM Instagram en rendez-vous qualifiés.</p>\n"
           '<div class="article-meta">\n'
           '<span class="article-date">9 septembre 2026</span>\n'
           "<span class=\"read-more\">Lire l'article &#8594;</span>\n"
           "</div>\n</a>"),
    "en": ('\n<a class="article-card" href="/alternatives/manychat.html">\n'
           '<span class="article-category">Alternatives</span>\n'
           "<h2>ManyChat alternative for Instagram: why no-code tools hit their limits in 2026</h2>\n"
           "<p>ManyChat, InstantDM, LinkDM... an honest comparison of SaaS tools, and why a custom AI automation turns your Instagram DMs into qualified appointments.</p>\n"
           '<div class="article-meta">\n'
           '<span class="article-date">9 September 2026</span>\n'
           '<span class="read-more">Read the article &#8594;</span>\n'
           "</div>\n</a>"),
    "nl": ('\n<a class="article-card" href="/alternatives/manychat.html">\n'
           '<span class="article-category">Alternatieven</span>\n'
           "<h2>ManyChat-alternatief voor Instagram: waarom no-code tools in 2026 tegen hun limieten lopen</h2>\n"
           "<p>ManyChat, InstantDM, LinkDM... een eerlijke vergelijking van SaaS-tools, en waarom een AI-automatisering op maat je Instagram-DM's beter omzet in gekwalificeerde afspraken.</p>\n"
           '<div class="article-meta">\n'
           '<span class="article-date">9 september 2026</span>\n'
           '<span class="read-more">Lees het artikel &#8594;</span>\n'
           "</div>\n</a>"),
}

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


def patch_grid_translations():
    path = os.path.join(ROOT, "i18n", "translations.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    grid = data.get("blog.index.grid")
    if not grid:
        return
    changed = False
    for lang in ("fr", "en", "nl"):
        if "/alternatives/manychat.html" not in grid.get(lang, ""):
            grid[lang] = grid.get(lang, "") + GRID_CARD[lang]
            changed = True
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("translations.json : carte ManyChat ajoutee a blog.index.grid")


def load_translations():
    with open(os.path.join(ROOT, "i18n", "translations.json"), encoding="utf-8") as f:
        return json.load(f)


def public_path(page):
    if page == "index.html":
        return ""
    if page.endswith("/index.html"):
        return page[: -len("index.html")]
    return page


def canonical(page, lang):
    pref = "" if lang == "fr" else lang + "/"
    return BASE + "/" + pref + public_path(page)


def page_url(page, lang):
    pref = "" if lang == "fr" else lang + "/"
    p = public_path(page)
    if p == "":
        return "/" + pref
    return "/" + pref + p


def hreflang_block(page):
    lines = []
    for lang in ("fr", "en", "nl"):
        lines.append('<link rel="alternate" hreflang="%s" href="%s">' % (lang, canonical(page, lang)))
    lines.append('<link rel="alternate" hreflang="x-default" href="%s">' % canonical(page, "fr"))
    return "\n    " + "\n    ".join(lines) + "\n"


def set_attr(raw, name, value):
    esc = htmlmod.escape(value, quote=True)
    pat = re.compile(r'(\s' + re.escape(name) + r'\s*=\s*)("[^"]*"|\'[^\']*\'|[^\s>]+)', re.I)
    if pat.search(raw):
        return pat.sub(lambda m: m.group(1) + '"' + esc + '"', raw, count=1)
    m = re.search(r'(\s*/?>)\s*$', raw)
    if not m:
        return raw
    return raw[: m.start()] + ' ' + name + '="' + esc + '"' + m.group(1)


def get_attr(attrs, name):
    for k, v in attrs:
        if k == name:
            return v
    return None


def remove_attr(raw, name):
    pat = re.compile(r'\s' + re.escape(name) + r'\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)', re.I)
    return pat.sub('', raw)


def rewrite_href(href, page, lang):
    h = href.strip()
    low = h.lower()
    if not h or low.startswith(("#", "mailto:", "tel:", "javascript:", "data:", "http://", "https://", "//")):
        return h
    frag = ""
    query = ""
    if "#" in h:
        h, frag = h.split("#", 1)
        frag = "#" + frag
    if "?" in h:
        h, query = h.split("?", 1)
        query = "?" + query
    h = h.strip()
    if h in ("", "./", "/"):
        target = "index.html"
    elif h.rstrip("/") == "/blog" or h.rstrip("/") == "blog":
        target = "blog/index.html"
    else:
        target = h.lstrip("./")
        if target.startswith("/"):
            target = target.lstrip("/")
    if target in LOCALIZED:
        return page_url(target, lang) + query + frag
    return "/" + target + query + frag


class Renderer(HTMLParser):
    def __init__(self, translations, page, lang, translate_body):
        super().__init__(convert_charrefs=False)
        self.T = translations
        self.page = page
        self.lang = lang
        self.translate_body = translate_body
        self.out = io.StringIO()
        self.suppress = None
        self.in_title = False
        self.title_buf = []
        self.skip_script = False
        self.hreflang_done = False

    def tr(self, key):
        v = self.T.get(key)
        if not v:
            return None
        return v.get(self.lang) or v.get("fr")

    def handle_decl(self, decl):
        self.out.write("<!" + decl + ">")

    def handle_comment(self, data):
        if self.suppress or self.skip_script:
            return
        self.out.write("<!--" + data + "-->")

    def handle_pi(self, data):
        self.out.write("<?" + data + ">")

    def handle_entityref(self, name):
        if self.suppress or self.skip_script:
            return
        if self.in_title:
            self.title_buf.append("&" + name + ";")
            return
        self.out.write("&" + name + ";")

    def handle_charref(self, name):
        if self.suppress or self.skip_script:
            return
        if self.in_title:
            self.title_buf.append("&#" + name + ";")
            return
        self.out.write("&#" + name + ";")

    def handle_data(self, data):
        if self.suppress or self.skip_script:
            return
        if self.in_title:
            self.title_buf.append(data)
            return
        self.out.write(data)

    def handle_startendtag(self, tag, attrs):
        if self.suppress or self.skip_script:
            return
        raw = self.get_starttag_text()
        if tag == "script":
            self.out.write(raw)
            return
        if get_attr(attrs, "data-i18n-attr"):
            raw = self.apply_attr_keys(raw, attrs)
        self.out.write(raw)

    def handle_starttag(self, tag, attrs):
        if self.skip_script:
            return
        raw = self.get_starttag_text()
        if self.suppress:
            if tag == self.suppress[0]:
                self.suppress[1] += 1
            return

        if tag == "script":
            src = get_attr(attrs, "src") or ""
            if "i18n.js" in src:
                self.skip_script = True
                return
            self.out.write(raw)
            return

        if tag == "html":
            raw = set_attr(raw, "lang", self.lang)
            self.out.write(raw)
            return

        if tag == "head":
            self.out.write(raw)
            if self.lang != "fr":
                self.out.write('<base href="/">')
            self.out.write('<style>.lang-btn[data-lang-active]{background:rgba(99,102,241,0.15);border-color:rgba(99,102,241,0.3);color:var(--primary-light);}</style>')
            return

        if tag == "title":
            self.in_title = True
            self.title_buf = []
            self.out.write(raw)
            return

        if tag == "meta":
            raw = self.rewrite_meta(raw, attrs)
            self.out.write(raw)
            return

        if tag == "link":
            rel = (get_attr(attrs, "rel") or "").lower()
            if "canonical" in rel:
                raw = set_attr(raw, "href", canonical(self.page, self.lang))
                self.out.write(raw)
                if not self.hreflang_done:
                    self.out.write(hreflang_block(self.page))
                    self.hreflang_done = True
                return
            if "alternate" in rel and get_attr(attrs, "hreflang"):
                return
            self.out.write(raw)
            return

        i18n_key = get_attr(attrs, "data-i18n")
        i18n_html_key = get_attr(attrs, "data-i18n-html")

        if get_attr(attrs, "data-lang"):
            raw = self.rewrite_switcher(raw, attrs)
            self.out.write(raw)
            return

        if tag == "a":
            href = get_attr(attrs, "href")
            if href is not None:
                raw = set_attr(raw, "href", rewrite_href(href, self.page, self.lang))

        if i18n_key or i18n_html_key:
            key = i18n_key or i18n_html_key
            val = self.tr(key) if self.translate_body else None
            if get_attr(attrs, "data-i18n-attr"):
                raw = self.apply_attr_keys(raw, attrs)
            self.out.write(raw)
            if val is not None and tag not in VOID:
                if i18n_html_key:
                    self.out.write(val)
                else:
                    self.out.write(htmlmod.escape(val, quote=False))
                self.suppress = [tag, 1]
            return

        if get_attr(attrs, "data-i18n-attr"):
            raw = self.apply_attr_keys(raw, attrs)
        self.out.write(raw)

    def handle_endtag(self, tag):
        if self.skip_script:
            if tag == "script":
                self.skip_script = False
            return
        if self.suppress:
            if tag == self.suppress[0]:
                self.suppress[1] -= 1
                if self.suppress[1] == 0:
                    self.out.write("</" + tag + ">")
                    self.suppress = None
            return
        if tag == "title" and self.in_title:
            self.in_title = False
            if self.lang == "fr":
                self.out.write("".join(self.title_buf))
            else:
                self.out.write(htmlmod.escape(self.get_title(), quote=False))
            self.out.write("</title>")
            return
        if tag == "head" and not self.hreflang_done:
            self.out.write(hreflang_block(self.page))
            self.hreflang_done = True
        self.out.write("</" + tag + ">")

    def apply_attr_keys(self, raw, attrs):
        spec = get_attr(attrs, "data-i18n-attr")
        for pair in spec.split(","):
            segs = pair.strip().split(":")
            if len(segs) == 2:
                val = self.tr(segs[1].strip())
                if val is not None and self.translate_body:
                    raw = set_attr(raw, segs[0].strip(), val)
        return raw

    def rewrite_meta(self, raw, attrs):
        name = (get_attr(attrs, "name") or "").lower()
        prop = (get_attr(attrs, "property") or "").lower()
        if name == "description":
            if self.lang != "fr":
                raw = set_attr(raw, "content", self.get_desc())
        elif prop == "og:title":
            if self.lang != "fr":
                raw = set_attr(raw, "content", self.get_title())
        elif prop == "og:description":
            if self.lang != "fr":
                raw = set_attr(raw, "content", self.get_desc())
        elif prop == "og:url":
            raw = set_attr(raw, "content", canonical(self.page, self.lang))
        elif prop == "og:locale":
            loc = {"fr": "fr_BE", "en": "en_GB", "nl": "nl_BE"}[self.lang]
            raw = set_attr(raw, "content", loc)
        return raw

    def rewrite_switcher(self, raw, attrs):
        dl = (get_attr(attrs, "data-lang") or "").lower()
        raw = remove_attr(raw, "onclick")
        raw = set_attr(raw, "href", page_url(self.page, dl))
        if dl == self.lang:
            raw = set_attr(raw, "data-lang-active", dl)
            raw = set_attr(raw, "aria-current", "true")
        return raw

    def get_title(self):
        if self.page in META:
            return META[self.page][self.lang][0]
        if self.page in TITLE_KEYS:
            v = self.tr(TITLE_KEYS[self.page])
            if v:
                return v
        return ""

    def get_desc(self):
        if self.page in META:
            return META[self.page][self.lang][1]
        if self.page in DESC_KEYS:
            v = self.tr(DESC_KEYS[self.page])
            if v:
                return v
        return ""

    def result(self):
        return self.out.getvalue()


def render(page, lang, translations):
    with open(os.path.join(ROOT, page), encoding="utf-8") as f:
        src = f.read()
    src = re.sub(r'[ \t]*<link[^>]*hreflang[^>]*>\s*\n?', '', src)
    src = re.sub(r'<base href="/">', '', src)
    src = re.sub(r'<style>\.lang-btn\[data-lang-active\][^<]*</style>', '', src)
    r = Renderer(translations, page, lang, translate_body=(lang != "fr"))
    r.feed(src)
    r.close()
    return r.result()


def update_sitemap():
    path = os.path.join(ROOT, "sitemap.xml")
    if not os.path.exists(path):
        print("ATTENTION : sitemap.xml introuvable a la racine, sitemap non mis a jour.")
        return
    with open(path, encoding="utf-8") as f:
        s = f.read()
    s = re.sub(r'\s*<xhtml:link[^>]*/>', '', s)
    if "xmlns:xhtml" not in s:
        def add_ns(m):
            return m.group(0)[:-1] + ' xmlns:xhtml="http://www.w3.org/1999/xhtml">'
        s, n = re.subn(r'<urlset\b[^>]*>', add_ns, s, count=1)
        if n == 0:
            print("ATTENTION : balise <urlset> introuvable, namespace xhtml non ajoute.")
    today = datetime.date.today().isoformat()
    for page in PAGES:
        fr = canonical(page, "fr")
        links = ""
        for lang in ("fr", "en", "nl", "x-default"):
            href = canonical(page, "fr") if lang == "x-default" else canonical(page, lang)
            links += '\n    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (lang, href)
        pat = re.compile(r'(<loc>' + re.escape(fr) + r'</loc>(?:\s*<lastmod>[^<]*</lastmod>)?)')
        if pat.search(s):
            s = pat.sub(lambda m: m.group(1) + links, s, count=1)
        for lang in ("en", "nl"):
            loc = canonical(page, lang)
            if "<loc>" + loc + "</loc>" not in s:
                entry = '\n  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.7</priority>%s\n  </url>' % (loc, today, links)
                s = s.replace("</urlset>", entry + "\n</urlset>", 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


def main():
    missing = [p for p in PAGES if not os.path.exists(os.path.join(ROOT, p))]
    if missing:
        print("AUCUNE ECRITURE. Fichier(s) introuvable(s) :")
        for m in missing:
            print("  - " + m)
        sys.exit(1)

    patch_grid_translations()
    translations = load_translations()
    changed = []

    for page in PAGES:
        fr_new = render(page, "fr", translations)
        with open(os.path.join(ROOT, page), "w", encoding="utf-8") as f:
            f.write(fr_new)
        changed.append(page)

        for lang in ("en", "nl"):
            out = render(page, lang, translations)
            dest = os.path.join(ROOT, lang, page)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(out)
            changed.append(lang + "/" + page)

    print("Pages generees/modifiees :")
    for c in changed:
        print("  " + c)

    update_sitemap()
    print("\nSitemap mis a jour avec les alternates hreflang.")


main()
