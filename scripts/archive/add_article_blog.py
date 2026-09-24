import json, sys

SLUG = "5-occasions-manquees-site-pme.html"

def card(cat, title, p, date):
    return ('<!-- Article: 5 missed opportunities -->\n'
            '<a class="article-card" href="/blog/%s">'
            '<span class="article-category">%s</span>'
            '<h2>%s</h2>'
            '<p>%s</p>'
            '<div class="article-meta">'
            '<span class="article-date">%s</span>'
            '<span class="read-more">%s</span>'
            '</div></a>') % (SLUG, cat, title, p, date, 'Lire l\'article →')

card_fr = card("Guide pratique",
    "Les 5 occasions manquées sur votre site actuel",
    "Votre site est-il fait pour vendre ? Chatbot IA, réservation automatique, QR code, tableau de bord de performance et contenu : les 5 fonctionnalités que la plupart des sites de PME n'exploitent pas.",
    "9 septembre 2026")

card_en = card("Practical guide",
    "The 5 missed opportunities on your current website",
    "Is your website built to sell? AI chatbot, auto-booking, QR code, performance dashboard and content: the 5 features most SME websites don't use.",
    "9 September 2026").replace("Lire l'article →", "Read the article →")

card_nl = card("Praktische gids",
    "De 5 gemiste kansen op uw huidige website",
    "Is uw website gemaakt om te verkopen? AI-chatbot, automatisch reserveren, QR-code, prestatiedashboard en content: de 5 functies die de meeste KMO-websites niet benutten.",
    "9 september 2026").replace("Lire l'article →", "Lees het artikel →")

# 1) translations.json -> blog.index.grid (insérer en tête de la grille)
path = 'i18n/translations.json'
raw = open(path, encoding='utf-8').read()
data = json.loads(raw)
grid = data['blog.index.grid']
for lang, c in (('fr', card_fr), ('en', card_en), ('nl', card_nl)):
    val = grid[lang]
    if SLUG in val:
        raise SystemExit('deja present en %s : rien a faire' % lang)
    marker = '<!-- Article 0: Pro Max -->'
    if marker in val:
        val = val.replace(marker, c + marker, 1)
    else:
        val = c + val
    grid[lang] = val
data['blog.index.grid'] = grid
open(path, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=2))

# 2) blog/index.html (fallback FR, même structure)
p = 'blog/index.html'
idx = open(p, encoding='utf-8').read()
if SLUG in idx:
    raise SystemExit('deja present dans blog/index.html')
marker = '<!-- Article 0: Pro Max -->'
idx = idx.replace(marker, card_fr + marker, 1)
open(p, 'w', encoding='utf-8').write(idx)

print('OK : carte ajoutee en fr/en/nl (translations.json + blog/index.html)')
