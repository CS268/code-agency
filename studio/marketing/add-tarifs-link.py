#!/usr/bin/env python3
"""Ajoute lien Tarifs dans la nav + bandeau abonnements au-dessus du bouton Générer"""
import os, re, shutil, subprocess, sys, tempfile, time

TARGET = os.path.expanduser("~/jcode-agency/studio/marketing/index.html")
if not os.path.isfile(TARGET):
    sys.exit("ABANDON : fichier introuvable : " + TARGET)
html = open(TARGET, encoding="utf-8").read()

if "Voir les abonnements" in html:
    sys.exit("ABANDON : le bandeau abonnements semble déjà présent.")

# 1. Lien Tarifs dans la nav (juste avant le CTA jcode.store)
cta_anchor = '<a href="https://jcode.store" target="_blank"'
if html.count(cta_anchor) != 1:
    sys.exit("ABANDON : CTA jcode.store trouvé %d fois." % html.count(cta_anchor))
tarifs_link = ('<a href="/studio/marketing/tarifs.html" '
               'style="color:var(--ink-dim);text-decoration:none;font-size:0.85rem;">Tarifs</a>\n        ')
html = html.replace(cta_anchor, tarifs_link + cta_anchor, 1)

# 2. Bandeau au-dessus du bouton Générer
btn_anchor = '<button type="button" class="btn-primary" id="generate-btn" disabled>'
if html.count(btn_anchor) != 1:
    sys.exit("ABANDON : bouton générer trouvé %d fois." % html.count(btn_anchor))
banner = ('<div style="max-width:900px;margin:0 auto 1rem;display:flex;align-items:center;'
          'justify-content:space-between;gap:1rem;background:var(--grad-soft);'
          'border:1px solid var(--border);border-radius:999px;padding:0.7rem 1.2rem;'
          'font-size:0.82rem;color:var(--ink-dim);flex-wrap:wrap;">'
          '<span>💡 <strong style="color:var(--ink);">Besoin de volume ?</strong> '
          'Des abonnements pour 5, 15 ou 40 vidéos par mois.</span>'
          '<a href="/studio/marketing/tarifs.html" style="color:#a5b4fc;font-weight:700;'
          'text-decoration:none;white-space:nowrap;">Voir les abonnements →</a></div>\n')
html = html.replace(btn_anchor, banner + btn_anchor, 1)

# 3. Vérification JS
m = re.search(r"<script>(.*)</script>", html, flags=re.S)
if not m:
    sys.exit("ABANDON : bloc script introuvable.")
with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
    tmp.write(m.group(1))
    tmp_path = tmp.name
check = subprocess.run(["node", "--check", tmp_path], capture_output=True, text=True)
os.unlink(tmp_path)
if check.returncode != 0:
    sys.exit("ABANDON : erreur de syntaxe :\n" + check.stderr[:600])

backup = "/tmp/studio-marketing-tarifslink-" + time.strftime("%Y%m%d-%H%M%S") + ".bak"
shutil.copy2(TARGET, backup)
open(TARGET, "w", encoding="utf-8").write(html)
print("✅ Sauvegarde : " + backup)
print("✅ Lien Tarifs (nav) + bandeau abonnements ajoutés")
