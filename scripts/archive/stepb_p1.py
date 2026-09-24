#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Etape B - partie 1 (page d'accueil) : promo PROMO460 sur les 3 packs.
Corrige : (1) atomicite deux fichiers, (2) edition chirurgicale de translations.json
         (aucun json.dumps global -> format conserve au byte pres).
Usage : python3 stepb_p1.py   (a lancer depuis ~/jcode-agency)
"""
import io, json, os, shutil, sys, time

HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)) or ".", "index.html")
TR_PATH   = os.path.join(os.path.dirname(os.path.abspath(__file__)) or ".", "i18n", "translations.json")

def jsquote(v):
    return json.dumps(v, ensure_ascii=False)

# (key, lang, old_valeur_complete, new_valeur_complete)
TR_EDITS = []

def tr(key, fr_o, fr_n, en_o, en_n, nl_o, nl_n):
    TR_EDITS.append((key, "fr", fr_o, fr_n))
    TR_EDITS.append((key, "en", en_o, en_n))
    TR_EDITS.append((key, "nl", nl_o, nl_n))

tr("index.meta.description",
   "JCODE Agency propulse votre commerce (commerce, restaurant, coiffeur, boulanger...) avec 8 modules IA. Vidéos, prospection, copywriting, sites web — 100% automatisé. Package Teaser à 497€.",
   "JCODE Agency propulse votre commerce (commerce, restaurant, coiffeur, boulanger...) avec 8 modules IA. Vidéos, prospection, copywriting, sites web — 100% automatisé. Package Teaser à 37€ ce mois-ci (code PROMO460, au lieu de 497€).",
   "JCODE Agency boosts your business (commerce, restaurant, hairdresser, bakery...) with 8 AI modules. Videos, prospecting, copywriting, websites — 100% automated. Teaser Package at €497.",
   "JCODE Agency boosts your business (commerce, restaurant, hairdresser, bakery...) with 8 AI modules. Videos, prospecting, copywriting, websites — 100% automated. Teaser Package at €37 this month (code PROMO460, instead of €497).",
   "JCODE Agency boost uw bedrijf (commerce, restaurant, kapper, bakker...) met 8 AI-modules. Video's, prospectie, copywriting, websites — 100% geautomatiseerd. Teaser Pakket voor €497.",
   "JCODE Agency boost uw bedrijf (commerce, restaurant, kapper, bakker...) met 8 AI-modules. Video's, prospectie, copywriting, websites — 100% geautomatiseerd. Teaser Pakket voor 37€ deze maand (code PROMO460, in plaats van €497).")

tr("index.options.tip_html",
   "💡 <strong style=\"color: #fff;\">Conseil :</strong> Commencez avec le forfait Teaser à 497€ et ajoutez les options quand vous êtes prêt. Pas d'engagement, évolution à tout moment.",
   "💡 <strong style=\"color: #fff;\">Conseil :</strong> Commencez avec le forfait Teaser à 37€ ce mois-ci (code PROMO460, au lieu de 497€) et ajoutez les options quand vous êtes prêt. Pas d'engagement, évolution à tout moment.",
   "💡 <strong style=\"color: #fff;\">Tip:</strong> Start with the Teaser plan at €497 and add options when you're ready. No commitment, upgrade anytime.",
   "💡 <strong style=\"color: #fff;\">Tip:</strong> Start with the Teaser plan at €37 this month (code PROMO460, instead of €497) and add options when you're ready. No commitment, upgrade anytime.",
   "💡 <strong style=\"color: #fff;\">Tip:</strong> Begin met het Teaser-pakket voor €497 en voeg opties toe wanneer u klaar bent. Geen verplichting, op elk moment upgraden.",
   "💡 <strong style=\"color: #fff;\">Tip:</strong> Begin met het Teaser-pakket voor 37€ deze maand (code PROMO460, in plaats van €497) en voeg opties toe wanneer u klaar bent. Geen verplichting, op elk moment upgraden.")

tr("index.how.step1.desc",
   "Choisissez le Teaser Package à 497€ et finalisez votre paiement sécurisé en 2 minutes.",
   "Choisissez le Teaser Package à 37€ ce mois-ci (code PROMO460, au lieu de 497€) et finalisez votre paiement sécurisé en 2 minutes.",
   "Choose the Teaser Package at €497 and finalize your secure payment in 2 minutes.",
   "Choose the Teaser Package at €37 this month (code PROMO460, instead of €497) and finalize your secure payment in 2 minutes.",
   "Kies het Teaser Pakket voor €497 en voltooi uw veilige betaling in 2 minuten.",
   "Kies het Teaser Pakket voor 37€ deze maand (code PROMO460, in plaats van €497) en voltooi uw veilige betaling in 2 minuten.")

tr("index.contact.form.subjectTeaser",
   "Teaser — 497€ (paiement unique)",
   "Teaser — 37€ ce mois-ci (code PROMO460, au lieu de 497€)",
   "Teaser — €497 (one-time payment)",
   "Teaser — €37 this month (code PROMO460, instead of €497)",
   "Teaser — €497 (eenmalige betaling)",
   "Teaser — 37€ deze maand (code PROMO460, in plaats van €497)")

tr("index.contact.form.subjectPro",
   "Pro — 999€/mois",
   "Pro — 539€ ce mois-ci (code PROMO460, au lieu de 999€) — paiement unique",
   "Pro — €999/month",
   "Pro — €539 this month (code PROMO460, instead of €999) — one-time payment",
   "Pro — €999/maand",
   "Pro — 539€ deze maand (code PROMO460, in plaats van €999) — eenmalige betaling")

tr("index.contact.form.subjectProMax",
   "Pro Max — 1,599€/mois",
   "Pro Max — 1 139€ ce mois-ci (code PROMO460, au lieu de 1 599€) — paiement unique",
   "Pro Max — €1,599/month",
   "Pro Max — €1,139 this month (code PROMO460, instead of €1,599) — one-time payment",
   "Pro Max — €1.599/maand",
   "Pro Max — €1.139 deze maand (code PROMO460, in plaats van €1.599) — eenmalige betaling")

# (old, new, tag)
HTML_EDITS = [
    ("Package Teaser à 497€.",
     "Package Teaser à 37€ ce mois-ci (code PROMO460, au lieu de 497€).",
     "og:description"),
    ("Packages marketing commerce automatisé par IA. Teaser (497€), Pro (999€) et Pro Max (1,599€).",
     "Packages marketing commerce automatisé par IA. Ce mois-ci avec le code PROMO460 : Teaser à 37€ (au lieu de 497€), Pro à 539€ (au lieu de 999€) et Pro Max à 1 139€ (au lieu de 1 599€), en paiement unique.",
     "JSON-LD Service.description"),
    ("Le package Teaser commence à 497€ paiement unique. Les forfaits Pro (999€/mois) et Pro Max (1599€/mois) incluent l'automatisation complète avec agents IA.",
     "Ce mois-ci avec le code PROMO460 : Teaser à 37€ (au lieu de 497€), Pro à 539€ (au lieu de 999€) et Pro Max à 1 139€ (au lieu de 1 599€), tous en paiement unique. Les forfaits Pro et Pro Max incluent l'automatisation complète avec agents IA.",
     "FAQ JSON-LD fr"),
    ("The Teaser package starts at 497€ one-time payment. Pro (999€/month) and Pro Max (1599€/month) plans include full automation with AI agents.",
     "This month with code PROMO460: Teaser at €37 (instead of €497), Pro at €539 (instead of €999) and Pro Max at €1,139 (instead of €1,599), all in one-time payments. Pro and Pro Max plans include full automation with AI agents.",
     "FAQ JSON-LD en"),
    ("Het Teaser-pakket begint bij 497€ eenmalige betaling. Pro (999€/maand) en Pro Max (1599€/maand) omvatten volledige automatisering met IA-agents.",
     "Deze maand met code PROMO460: Teaser voor €37 (in plaats van €497), Pro voor €539 (in plaats van €999) en Pro Max voor €1.139 (in plaats van €1.599), allemaal eenmalige betalingen. De Pro- en Pro Max-pakketten omvatten volledige automatisering met IA-agents.",
     "FAQ JSON-LD nl"),
    ("Commencez avec le forfait Teaser à 497€ et ajoutez les options quand vous êtes prêt.",
     "Commencez avec le forfait Teaser à 37€ ce mois-ci (code PROMO460, au lieu de 497€) et ajoutez les options quand vous êtes prêt.",
     "tip_html inline FR"),
    ("Choisissez le Teaser Package à 497€ et finalisez votre paiement sécurisé en 2 minutes.",
     "Choisissez le Teaser Package à 37€ ce mois-ci (code PROMO460, au lieu de 497€) et finalisez votre paiement sécurisé en 2 minutes.",
     "step1.desc inline FR"),
    ("Teaser — 497€ (paiement unique)",
     "Teaser — 37€ ce mois-ci (code PROMO460, au lieu de 497€)",
     "select subjectTeaser inline FR"),
    ("Pro — 999€/mois",
     "Pro — 539€ ce mois-ci (code PROMO460, au lieu de 999€) — paiement unique",
     "select subjectPro inline FR"),
    ("Pro Max — 1,599€/mois",
     "Pro Max — 1 139€ ce mois-ci (code PROMO460, au lieu de 1 599€) — paiement unique",
     "select subjectProMax inline FR"),
]

# -------------------------------------------------- PHASE 1 : validation en memoire
errors = []
applied_tr = []
html = io.open(HTML_PATH, encoding="utf-8").read()
raw_tr = io.open(TR_PATH, encoding="utf-8").read()

for key, lang, old_v, new_v in TR_EDITS:
    pat_old = '"%s": %s' % (lang, jsquote(old_v))
    pat_new = '"%s": %s' % (lang, jsquote(new_v))
    if raw_tr.count(pat_new) == 1:
        applied_tr.append((key, lang, "deja-applique"))
        continue
    if raw_tr.count(pat_old) != 1:
        errors.append("translations[%s].%s : ancienne valeur introuvable ou ambiguë" % (key, lang))
        continue
    raw_tr = raw_tr.replace(pat_old, pat_new)
    applied_tr.append((key, lang, "ok"))

applied_html = []
for old, new, tag in HTML_EDITS:
    n = html.count(old)
    if n == 0 and html.count(new) == 1:
        applied_html.append((tag, "deja-applique"))
        continue
    if n != 1:
        errors.append("index.html :: %s" % tag)
        continue
    html = html.replace(old, new)
    applied_html.append((tag, "ok"))

if not errors:
    try:
        json.loads(raw_tr)
    except Exception as e:
        errors.append("translations.json corrompu apres edition : %s" % e)

if errors:
    print("AUCUNE ECRITURE. %d probleme(s) detecte(s) :" % len(errors))
    for e in errors:
        print("  - " + e)
    sys.exit(1)

# -------------------------------------------------- PHASE 2 : ecritures
ts = time.strftime("%Y%m%d-%H%M%S")
bak_html = os.path.join("/tmp", "jcode_index_bak_stepB_%s.html" % ts)
bak_tr   = os.path.join("/tmp", "jcode_tr_bak_stepB_%s.json" % ts)
shutil.copyfile(HTML_PATH, bak_html)
shutil.copyfile(TR_PATH, bak_tr)
print("Sauvegardes : %s / %s" % (bak_html, bak_tr))

with io.open(TR_PATH, "w", encoding="utf-8") as f:
    f.write(raw_tr)
print("translations.json : maj OK (%d valeurs)" % len(applied_tr))

with io.open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)
print("index.html : maj OK (%d motifs)" % len(applied_html))

print("\n-- translations.json --")
for k, l, st in applied_tr:
    print("  %s.%s : %s" % (k, l, st))
print("-- index.html --")
for tag, st in applied_html:
    print("  %s : %s" % (tag, st))
