#!/usr/bin/env python3
"""Enrichit la carte Studio Marketing sur la home (cohérence avec bannière prompts)"""
import os, re, shutil, time

P = "/Users/matovuruky/jcode-agency/index.html"
html = open(P, encoding="utf-8").read()

# Ancrage : la carte actuelle
old_card = re.search(
    r'<a href="/studio/marketing/" class="service-card reveal studio-card"[^>]*>.*?</a>',
    html, re.S
)
if not old_card:
    print("ABANDON : carte Studio Marketing introuvable.")
    raise SystemExit

# Nouvelle carte enrichie
NEW_CARD = '''<a href="/studio/marketing/" class="service-card reveal studio-card" style="display:block; text-decoration:none; color:inherit; position:relative; overflow:hidden;">
                    <div style="position:absolute; top:1.2rem; right:1.2rem; background:linear-gradient(135deg,#6366f1,#d946ef); color:#fff; font-size:10px; padding:3px 8px; border-radius:8px; font-weight:800; letter-spacing:.04em;">NEW</div>
                    <div class="service-icon" style="position:relative;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                            <circle cx="12" cy="12" r="10"/>
                            <circle cx="12" cy="12" r="6"/>
                            <circle cx="12" cy="12" r="2"/>
                            <path d="M12 2v2M12 20v2M2 12h2M20 12h2" opacity=".6"/>
                        </svg>
                        <div style="position:absolute; inset:-8px; background:radial-gradient(circle, rgba(99,102,241,.25), transparent 70%); border-radius:50%; pointer-events:none;"></div>
                    </div>
                    <h3 style="background:linear-gradient(135deg,#6366f1,#8b5cf6 50%,#d946ef); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; font-size:1.35rem; margin-top:.3rem;">Studio Marketing</h3>
                    <p style="color:var(--muted); margin-top:.4rem;">Vidéos publicitaires IA prêtes à publier : 10 types de campagne, formats TikTok / Reels / YouTube, accroche et appel à l'action intégrés.</p>
                    <div style="margin-top:.9rem; display:flex; align-items:center; gap:.5rem; font-size:.78rem; color:#c7d2fe; font-weight:600;">
                        <span style="background:rgba(99,102,241,.15); border:1px solid rgba(99,102,246,.3); padding:.2rem .6rem; border-radius:999px;">dès 9,90 €/mois</span>
                        <span style="opacity:.7;">→</span>
                    </div>
                </a>'''

html = html[:old_card.start()] + NEW_CARD + html[old_card.end():]

bak = "/tmp/home-card-" + time.strftime("%Y%m%d-%H%M%S") + ".bak"
shutil.copy2(P, bak)
open(P, "w", encoding="utf-8").write(html)
print("✅ Sauvegarde :", bak)
print("✅ Carte Studio Marketing enrichie")
