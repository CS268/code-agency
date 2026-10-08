#!/usr/bin/env python3
"""Rend le Studio Marketing visible depuis le site principal"""
import re, shutil, time, os

ROOT = "/Users/matovuruky/jcode-agency"
TARGETS = {
    "prompts": os.path.join(ROOT, "studio/prompts/index.html"),
    "home":    os.path.join(ROOT, "index.html"),
    "promo":   os.path.join(ROOT, "promo-septembre.html"),
}

results = {}

# ═══════════════════════════════════════════════════════════
# PATCH NAV LINKS (identique pour les 3 pages)
# ═══════════════════════════════════════════════════════════
MARKETING_NAV_LINK = (
    '<a href="/studio/marketing/" '
    'data-fr="Marketing" data-nl="Marketing" data-en="Marketing" '
    'style="color:var(--primary);position:relative;">'
    'MARKETING <span style="background:#ff006e;color:#fff;font-size:10px;'
    'padding:2px 6px;border-radius:8px;vertical-align:super;font-weight:700;">'
    'NEW</span></a>'
)

# ═══════════════════════════════════════════════════════════
# BANNIERE CTA pour /studio/prompts/
# ═══════════════════════════════════════════════════════════
PROMPTS_BANNER = '''
<div class="marketing-cta-banner" style="max-width:1100px;margin:1.5rem auto;padding:1rem 1.5rem;background:linear-gradient(135deg,rgba(99,102,241,.12),rgba(139,92,246,.12));border:1px solid rgba(99,102,241,.3);border-radius:16px;display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap;">
  <div>
    <div style="font-size:.72rem;color:var(--primary);font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin-bottom:.3rem;">✨ Nouveau</div>
    <div style="font-size:1.05rem;font-weight:700;color:var(--text);margin-bottom:.2rem;">Studio Marketing — Vidéos publicitaires IA prêtes à publier</div>
    <div style="font-size:.85rem;color:var(--muted);">10 types de campagne, formats TikTok / Reels / YouTube, accroche et appel à l'action intégrés. À partir de 9,90 €/mois.</div>
  </div>
  <a href="/studio/marketing/" style="background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;text-decoration:none;padding:.7rem 1.4rem;border-radius:999px;font-weight:700;font-size:.9rem;white-space:nowrap;box-shadow:0 4px 20px rgba(99,102,241,.3);">Essayer →</a>
</div>
'''

# ═══════════════════════════════════════════════════════════
# CARTE STUDIO MARKETING pour la home
# ═══════════════════════════════════════════════════════════
HOME_CARD = '''
                <a href="/studio/marketing/" class="service-card reveal studio-card" style="display:block; text-decoration:none; color:inherit;">
                    <div class="service-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg></div>
                    <h3>Studio Marketing <span style="background:#ff006e;color:#fff;font-size:10px;padding:2px 8px;border-radius:8px;vertical-align:middle;font-weight:700;margin-left:.5rem;">NEW</span></h3>
                    <p data-i18n="index.services.marketing.desc">Vidéos publicitaires IA prêtes à publier : 10 types de campagne, formats TikTok / Reels / YouTube, accroche et appel à l'action intégrés. À partir de 9,90 €/mois.</p>
                </a>
'''

# ═══════════════════════════════════════════════════════════
# BACKUP
# ═══════════════════════════════════════════════════════════
backups = []
for key, path in TARGETS.items():
    if os.path.isfile(path):
        bak = f"/tmp/{os.path.basename(path)}.marketing-bak-{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(path, bak)
        backups.append((key, bak))

# ═══════════════════════════════════════════════════════════
# 1. PAGE PROMPTS
# ═══════════════════════════════════════════════════════════
p = TARGETS["prompts"]
html = open(p, encoding="utf-8").read()
modif = []

# 1a. Lien Marketing dans nav-links
anchor = '<div class="nav-spacer"></div>'
if anchor in html and MARKETING_NAV_LINK not in html:
    html = html.replace(
        anchor,
        f'    {MARKETING_NAV_LINK}\n    {anchor}',
        1,
    )
    modif.append("nav-link ajouté")

# 1b. Bannière CTA après le header (cherche le premier </header>)
header_close = re.search(r"</header>", html)
if header_close and "marketing-cta-banner" not in html:
    insert_at = header_close.end()
    html = html[:insert_at] + "\n" + PROMPTS_BANNER + html[insert_at:]
    modif.append("bannière CTA ajoutée")

open(p, "w", encoding="utf-8").write(html)
results["prompts"] = modif or ["rien à faire"]

# ═══════════════════════════════════════════════════════════
# 2. HOME
# ═══════════════════════════════════════════════════════════
p = TARGETS["home"]
html = open(p, encoding="utf-8").read()
modif = []

# 2a. Lien Marketing juste après VIDEOCREATOR
videocreator_anchor = '<a href="/studio/index.html?lang=fr" style="color:var(--primary);position:relative;">VIDEOCREATOR'
if videocreator_anchor in html and '/studio/marketing/' not in html:
    idx = html.find(videocreator_anchor)
    end_of_link = html.find("</a>", idx) + 4
    new_link = f'\n                {MARKETING_NAV_LINK}'
    html = html[:end_of_link] + new_link + html[end_of_link:]
    modif.append("nav-link MARKETING ajouté")

# 2b. Carte Marketing juste après carte VideoCreator
video_card_end_pattern = re.compile(
    r'(<h3[^>]*>VideoCreator</h3>\s*<p[^>]*>[^<]+</p>\s*</a>)',
    re.S,
)
m = video_card_end_pattern.search(html)
if m and "Studio Marketing" not in html:
    html = html[:m.end()] + "\n" + HOME_CARD + html[m.end():]
    modif.append("carte Studio Marketing ajoutée")

open(p, "w", encoding="utf-8").write(html)
results["home"] = modif or ["rien à faire"]

# ═══════════════════════════════════════════════════════════
# 3. PROMO-SEPTEMBRE
# ═══════════════════════════════════════════════════════════
p = TARGETS["promo"]
if os.path.isfile(p):
    html = open(p, encoding="utf-8").read()
    modif = []
    anchor = '<div class="nav-spacer"></div>'
    if anchor in html and MARKETING_NAV_LINK not in html:
        html = html.replace(
            anchor,
            f'    {MARKETING_NAV_LINK}\n    {anchor}',
            1,
        )
        modif.append("nav-link ajouté")
    open(p, "w", encoding="utf-8").write(html)
    results["promo"] = modif or ["nav non reconnue / rien à faire"]
else:
    results["promo"] = ["fichier absent"]

# ═══════════════════════════════════════════════════════════
# RAPPORT
# ═══════════════════════════════════════════════════════════
print("✅ Patchs appliqués :\n")
for key, mods in results.items():
    print(f"  [{key}] {' · '.join(mods)}")
print("\n📦 Backups :")
for key, bak in backups:
    print(f"  {key} → {bak}")
