#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Etape B - partie 2 : correctif des 2 omissions (RGPD + FAQ upgrade Pro).
Meme logique atomique que stepb_p1.py : validation en memoire d'abord,
ecriture seulement si tout est valide.
Usage : python3 stepb_p2.py   (a lancer depuis ~/jcode-agency)
"""
import io, json, os, shutil, sys, time

TR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)) or ".", "i18n", "translations.json")

def jsquote(v):
    return json.dumps(v, ensure_ascii=False)

TR_EDITS = []

def tr(label, lang, old_v, new_v):
    TR_EDITS.append((label, lang, old_v, new_v))

# --- RGPD (article 6.1.b) ---
tr("rgpd_497", "fr",
   "Le traitement repose sur <strong>l'article 6.1.b du RGPD</strong> : exécution du contrat. Vous payez 497€ pour un site vitrine personnalisé — les données sont indispensables à ce service.",
   "Le traitement repose sur <strong>l'article 6.1.b du RGPD</strong> : exécution du contrat. Vous payez 37€ ce mois-ci (code PROMO460, au lieu de 497€) pour un site vitrine personnalisé — les données sont indispensables à ce service.")
tr("rgpd_497", "en",
   "Processing is based on <strong>Article 6.1.b of GDPR</strong>: contract performance. You pay €497 for a personalized showcase site — the data is essential for this service.",
   "Processing is based on <strong>Article 6.1.b of GDPR</strong>: contract performance. You pay €37 this month (code PROMO460, instead of €497) for a personalized showcase site — the data is essential for this service.")
tr("rgpd_497", "nl",
   "De verwerking is gebaseerd op <strong>artikel 6.1.b van de AVG</strong>: uitvoering van de overeenkomst. U betaalt €497 voor een gepersonaliseerde vitrine-site — de gegevens zijn onmisbaar voor deze dienst.",
   "De verwerking is gebaseerd op <strong>artikel 6.1.b van de AVG</strong>: uitvoering van de overeenkomst. U betaalt 37€ deze maand (code PROMO460, in plaats van €497) voor een gepersonaliseerde vitrine-site — de gegevens zijn onmisbaar voor deze dienst.")

# --- FAQ "passer au Pro" ---
tr("faq_upgrade_pro", "fr",
   "Oui, vous pouvez passer au forfait Pro à 999€ pour une personnalisation avancée avec photos, textes sur mesure et menu détaillé.",
   "Oui, vous pouvez passer au forfait Pro à 539€ ce mois-ci (code PROMO460, au lieu de 999€) pour une personnalisation avancée avec photos, textes sur mesure et menu détaillé.")
tr("faq_upgrade_pro", "en",
   "Yes, you can move up to the Pro plan at €999 for advanced customisation with photos, custom texts and a detailed menu.",
   "Yes, you can move up to the Pro plan at €539 this month (code PROMO460, instead of €999) for advanced customisation with photos, custom texts and a detailed menu.")
tr("faq_upgrade_pro", "nl",
   "Ja, u kunt overstappen naar het Pro-pakket aan 999€ voor geavanceerde aanpassingen met foto's, maatteksten en een gedetailleerd menu.",
   "Ja, u kunt overstappen naar het Pro-pakket voor 539€ deze maand (code PROMO460, in plaats van 999€) voor geavanceerde aanpassingen met foto's, maatteksten en een gedetailleerd menu.")

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
bak_tr = os.path.join("/tmp", "jcode_tr_bak_stepB2_%s.json" % ts)
shutil.copyfile(TR_PATH, bak_tr)
print("Sauvegarde : %s" % bak_tr)

with io.open(TR_PATH, "w", encoding="utf-8") as f:
    f.write(raw_tr)
print("translations.json : maj OK (%d valeurs)" % len(applied))

print("\n-- translations.json --")
for label, lang, st in applied:
    print("  %s.%s : %s" % (label, lang, st))
