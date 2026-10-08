#!/usr/bin/env python3
"""v3 : bannière Studio Marketing enrichie + lien nav replacé (page prompts)"""
import os, re, shutil, time

P = "/Users/matovuruky/jcode-agency/studio/prompts/index.html"
html = open(P, encoding="utf-8").read()

if "mkt-banner" in html:
    print("ABANDON : bannière v3 déjà présente.")
    raise SystemExit

CSS = '''<style>
.mkt-banner{position:relative;overflow:hidden;max-width:1100px;margin:1.5rem auto;padding:1.4rem 1.6rem;border-radius:22px;background:linear-gradient(120deg,rgba(99,102,241,.14),rgba(139,92,246,.14) 45%,rgba(217,70,239,.14));border:1px solid rgba(139,92,246,.35);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);display:flex;align-items:center;justify-content:space-between;gap:1.2rem;flex-wrap:wrap;box-shadow:0 0 0 1px rgba(99,102,241,.15),0 0 40px -8px rgba(99,102,241,.45),0 24px 70px -20px rgba(0,0,0,.9);}
.mkt-banner::before{content:"";position:absolute;top:0;left:-60%;width:40%;height:100%;background:linear-gradient(100deg,transparent,rgba(255,255,255,.10),transparent);transform:skewX(-18deg);animation:mkt-shine 4.5s ease-in-out infinite;pointer-events:none;}
@keyframes mkt-shine{0%{left:-60%}55%{left:130%}100%{left:130%}}
.mkt-banner .orb{position:absolute;border-radius:50%;filter:blur(30px);opacity:.45;pointer-events:none;}
.mkt-banner .orb1{width:140px;height:140px;background:#6366f1;top:-60px;left:-40px;animation:mkt-float 7s ease-in-out infinite;}
.mkt-banner .orb2{width:120px;height:120px;background:#d946ef;bottom:-50px;right:-30px;animation:mkt-float 9s ease-in-out infinite reverse;}
@keyframes mkt-float{0%,100%{transform:translateY(0)}50%{transform:translateY(14px)}}
.mkt-banner .inner{position:relative;z-index:1;flex:1;min-width:260px;}
.mkt-eyebrow{display:inline-flex;align-items:center;gap:.45rem;font-size:.68rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#c7d2fe;background:rgba(99,102,241,.18);border:1px solid rgba(99,102,246,.4);padding:.3rem .7rem;border-radius:999px;margin-bottom:.6rem;}
.mkt-eyebrow .pulse{width:6px;height:6px;border-radius:50%;background:#34d399;animation:mkt-pulse 1.6s ease-in-out infinite;}
@keyframes mkt-pulse{0%,100%{box-shadow:0 0 0 0 rgba(52,211,153,.5)}50%{box-shadow:0 0 0 5px rgba(52,211,153,0)}}
.mkt-title{font-size:1.25rem;font-weight:800;letter-spacing:-.02em;color:#f8fafc;margin-bottom:.35rem;}
.mkt-title .grad{background:linear-gradient(135deg,#6366f1,#8b5cf6 50%,#d946ef);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
.mkt-desc{font-size:.86rem;color:#94a3b8;margin-bottom:.7rem;}
.mkt-chips{display:flex;gap:.4rem;flex-wrap:wrap;}
.mkt-chip{font-size:.66rem;font-weight:700;color:#a5b4fc;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);padding:.25rem .6rem;border-radius:999px;}
.mkt-cta{position:relative;z-index:1;display:inline-flex;flex-direction:column;align-items:center;gap:.25rem;background:linear-gradient(135deg,#6366f1,#8b5cf6 50%,#d946ef);color:#fff;text-decoration:none;padding:.85rem 1.6rem;border-radius:999px;font-weight:800;font-size:.95rem;box-shadow:0 0 0 1px rgba(99,102,241,.35),0 0 40px -8px rgba(99,102,241,.45);transition:transform .15s ease,box-shadow .15s ease;}
.mkt-cta:hover{transform:translateY(-2px);box-shadow:0 0 0 1px rgba(139,92,246,.5),0 0 60px -8px rgba(139,92,246,.6);}
.mkt-cta .arr{transition:transform .15s ease;}
.mkt-cta:hover .arr{transform:translateX(4px);}
.mkt-price{font-size:.68rem;font-weight:600;color:#e9d5ff;opacity:.85;}
</style>'''

BANNER = '''<div class="mkt-banner">
  <span class="orb orb1"></span><span class="orb orb2"></span>
  <div class="inner">
    <span class="mkt-eyebrow"><span class="pulse"></span> Nouveau</span>
    <div class="mkt-title">Studio Marketing — <span class="grad">des pubs IA prêtes à publier</span></div>
    <div class="mkt-desc">10 types de campagne, accroche des 3 premières secondes et appel à l'action intégrés. Ton produit reste identique à ta photo.</div>
    <div class="mkt-chips"><span class="mkt-chip">📱 9:16 TikTok / Reels</span><span class="mkt-chip">⬛ 1:1 Instagram</span><span class="mkt-chip">🖥️ 16:9 YouTube</span><span class="mkt-chip">⚡ 6,4 s</span></div>
  </div>
  <a class="mkt-cta" href="/studio/marketing/">Essayer maintenant <span class="arr">→</span><span class="mkt-price">dès 9,90 €/mois</span></a>
</div>'''

# 1. Remplacer l'ancienne bannière par la nouvelle
old_banner = re.search(r'<div class="marketing-cta-banner".*?</a>\s*</div>', html, re.S)
if not old_banner:
    print("ABANDON : ancienne bannière introuvable.")
    raise SystemExit
html = html[:old_banner.start()] + BANNER + html[old_banner.end():]

# 2. Injecter le CSS dans le head
if "</head>" not in html:
    print("ABANDON : </head> introuvable.")
    raise SystemExit
html = html.replace("</head>", CSS + "\n</head>", 1)

# 3. Replacer le lien nav : supprimer l'ancien (mal placé), réinsérer après "Comment ça marche"
old_link = re.search(r'<a href="/studio/marketing/"[^>]*>MARKETING.*?</a>', html, re.S)
if old_link:
    html = html[:old_link.start()] + html[old_link.end():]
anchor = 'data-en="How it works">Comment ça marche</a>'
new_link = ('<a href="/studio/marketing/" data-fr="Marketing" data-nl="Marketing" data-en="Marketing" '
            'style="color:#c7d2fe;font-weight:700;">Marketing <span style="background:linear-gradient(135deg,#6366f1,#d946ef);'
            'color:#fff;font-size:9px;padding:2px 6px;border-radius:8px;vertical-align:super;font-weight:800;">NEW</span></a>')
if anchor in html:
    html = html.replace(anchor, anchor + "\n      " + new_link, 1)
else:
    print("⚠️  ancre nav introuvable, lien non déplacé (bannière appliquée quand même)")

bak = "/tmp/prompts-beautify-" + time.strftime("%Y%m%d-%H%M%S") + ".bak"
shutil.copy2(P, bak)
open(P, "w", encoding="utf-8").write(html)
print("✅ Sauvegarde :", bak)
print("✅ Bannière enrichie + lien nav replacé")
