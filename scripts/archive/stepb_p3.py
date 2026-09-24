#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Etape B - partie 3 : delais de livraison + comparatif de fonctionnalites.
Meme logique atomique : validation en memoire d'abord, ecriture seulement
si tout est valide.
Usage : python3 stepb_p3.py   (a lancer depuis ~/jcode-agency)
"""
import io, json, os, shutil, sys, time

TR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)) or ".", "i18n", "translations.json")

def jsquote(v):
    return json.dumps(v, ensure_ascii=False)

TR_EDITS = []

def tr(label, lang, old_v, new_v):
    TR_EDITS.append((label, lang, old_v, new_v))

# --- Delais de livraison (Teaser) ---
tr("delai_teaser", "fr",
   "<strong style='color:#fff;'>Teaser (€497) :</strong> 24 à 48h ouvrées",
   "<strong style='color:#fff;'>Teaser (37€ ce mois-ci, code PROMO460, au lieu de €497) :</strong> 24 à 48h ouvrées")
tr("delai_teaser", "en",
   "<strong style='color:#fff;'>Teaser (€497):</strong> 24 to 48 business hours",
   "<strong style='color:#fff;'>Teaser (€37 this month, code PROMO460, instead of €497):</strong> 24 to 48 business hours")
tr("delai_teaser", "nl",
   "<strong style='color:#fff;'>Teaser (€497):</strong> 24 tot 48 werkuren",
   "<strong style='color:#fff;'>Teaser (37€ deze maand, code PROMO460, in plaats van €497):</strong> 24 tot 48 werkuren")

# --- Delais de livraison (Pro) ---
tr("delai_pro", "fr",
   "<strong style='color:#fff;'>Pro (€999/mois) :</strong> 48 à 72h ouvrées + mise en place mensuelle",
   "<strong style='color:#fff;'>Pro (539€ ce mois-ci, code PROMO460, au lieu de €999) :</strong> 48 à 72h ouvrées + mise en place mensuelle")
tr("delai_pro", "en",
   "<strong style='color:#fff;'>Pro (€999/month):</strong> 48 to 72 business hours + monthly setup",
   "<strong style='color:#fff;'>Pro (€539 this month, code PROMO460, instead of €999):</strong> 48 to 72 business hours + monthly setup")
tr("delai_pro", "nl",
   "<strong style='color:#fff;'>Pro (€999/maand):</strong> 48 tot 72 werkuren + maandelijkse opzet",
   "<strong style='color:#fff;'>Pro (539€ deze maand, code PROMO460, in plaats van €999):</strong> 48 tot 72 werkuren + maandelijkse opzet")

# --- Comparatif fonctionnalites (Teaser) ---
tr("comparatif_teaser", "fr",
   "Teaser : €497 (paiement unique) — Site web professionnel avec réservation en ligne, QR code, email de confirmation, bannière cookies RGPD et mentions légales.",
   "Teaser : 37€ ce mois-ci (code PROMO460, au lieu de €497), paiement unique — Site web professionnel avec réservation en ligne, QR code, email de confirmation, bannière cookies RGPD et mentions légales.")
tr("comparatif_teaser", "en",
   "Teaser: €497 (one-time payment) — Professional website with online booking, QR code, confirmation email, GDPR cookie banner and legal notices.",
   "Teaser: €37 this month (code PROMO460, instead of €497), one-time payment — Professional website with online booking, QR code, confirmation email, GDPR cookie banner and legal notices.")
tr("comparatif_teaser", "nl",
   "Teaser: €497 (eenmalige betaling) — Professionele website met online reservering, QR-code, bevestigingsmail, AVG-cookiebanner en wettelijke vermeldingen.",
   "Teaser: 37€ deze maand (code PROMO460, in plaats van €497), eenmalige betaling — Professionele website met online reservering, QR-code, bevestigingsmail, AVG-cookiebanner en wettelijke vermeldingen.")

# --- Comparatif fonctionnalites (Pro) ---
tr("comparatif_pro", "fr",
   "Pro : €999/mois",
   "Pro : 539€ ce mois-ci (code PROMO460, au lieu de €999)")
tr("comparatif_pro", "en",
   "Pro: €999/month",
   "Pro: €539 this month (code PROMO460, instead of €999)")
tr("comparatif_pro", "nl",
   "Pro: €999/maand",
   "Pro: 539€ deze maand (code PROMO460, in plaats van €999)")

# --- Comparatif fonctionnalites (Pro Max) ---
tr("comparatif_promax", "fr",
   "Pro Max : €1 599/mois",
   "Pro Max : 1 139€ ce mois-ci (code PROMO460, au lieu de €1 599)")
tr("comparatif_promax", "en",
   "Pro Max: €1,599/month",
   "Pro Max: €1,139 this month (code PROMO460, instead of €1,599)")
tr("comparatif_promax", "nl",
   "Pro Max: €1.599/maand",
   "Pro Max: €1.139 deze maand (code PROMO460, in plaats van €1.599)")

# -------------------------------------------------- PHASE 1 : validation en memoire
errors = []
applied = []
raw_tr = io.open(TR_PATH, encoding="utf-8").read()

for label, lang, old_v, new_v in TR_EDITS:
    pat_old = '"%s": %s' % (lang, jsquote(old_v))
    pat_new = '"%s": %s' % (lang, jsquote(new_v))
    if raw_tr.count(pat_new) == 1:
        applied.append((label, lang, "deja-applique"))
        continue
    if raw_tr.count(pat_old) != 1:
        errors.append("%s.%s : ancienne valeur introuvable ou ambiguë" % (label, lang))
        continue
    raw_tr = raw_tr.replace(pat_old, pat_new)
    applied.append((label, lang, "ok"))

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

# -------------------------------------------------- PHASE 2 : ecriture
ts = time.strftime("%Y%m%d-%H%M%S")
bak_tr = os.path.join("/tmp", "jcode_tr_bak_stepB3_%s.json" % ts)
shutil.copyfile(TR_PATH, bak_tr)
print("Sauvegarde : %s" % bak_tr)

with io.open(TR_PATH, "w", encoding="utf-8") as f:
    f.write(raw_tr)
print("translations.json : maj OK (%d valeurs)" % len(applied))

print("\n-- translations.json --")
for label, lang, st in applied:
    print("  %s.%s : %s" % (label, lang, st))
