#!/usr/bin/env python3
"""Harmonise le Studio Marketing avec le design jcode.store"""
import os, re, shutil, subprocess, sys, tempfile, time

TARGET = os.path.expanduser("~/jcode-agency/studio/marketing/index.html")
if not os.path.isfile(TARGET):
    sys.exit("ABANDON : fichier introuvable : " + TARGET)

html = open(TARGET, encoding="utf-8").read()

# Garde-fou : si déjà patché, on arrête
if "logo-mark" in html and "--acc:#6366f1" in html:
    sys.exit("ABANDON : les corrections semblent déjà appliquées.")

# ═══ REMPLACEMENTS ═══
REPLACEMENTS = [
    # 1. VARIABLES CSS (remplace :root existant)
    (":root {",
     ":root { /* design jcode.store */\n"
     "    --bg: #0f172a; --bg-2: #1e293b;\n"
     "    --panel: #121627; --panel-2: #1a1f33;\n"
     "    --border: rgba(255,255,255,.075);\n"
     "    --ink: #f8fafc; --ink-dim: #94a3b8; --ink-faint: #64748b;\n"
     "    --success: #10b981; --error: #ff3d81; --warn: #f59e0b; --info: #6366f1;\n"
     "    --acc: #6366f1; --acc-2: #8b5cf6; --acc-3: #ff3d81;\n"
     "    --accent: #6366f1; --accent-2: #8b5cf6;\n"
     "    --grad: linear-gradient(135deg,#6366f1 0%,#8b5cf6 50%,#d946ef 100%);\n"
     "    --grad-soft: linear-gradient(120deg,rgba(99,102,241,.16),rgba(139,92,246,.16));\n"
     "    --glow: 0 0 0 1px rgba(99,102,241,.35), 0 0 40px -8px rgba(99,102,241,.45);\n"
     "    --radius: 16px; --radius-lg: 22px;\n"
     "    --ff: 'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;\n"),

    # 2. FONT-FAMILY GLOBAL
    ("font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, Arial, sans-serif;",
     "font-family: var(--ff);"),

    # 3. BANNIERE INFO (dégradé doux cohérent)
    ("background: linear-gradient(135deg, rgba(225,29,72,0.12), rgba(249,115,22,0.12));\n        border-left: 3px solid var(--accent);",
     "background: var(--grad-soft);\n        border-left: 3px solid var(--acc);"),

    # 4. SELECTIONS (cards marketing)
    ("background: linear-gradient(135deg, rgba(225,29,72,0.2), rgba(249,115,22,0.2));\n        border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent);",
     "background: var(--grad-soft);\n        border-color: var(--acc); box-shadow: var(--glow);"),

    # 5. BOUTON CROIX SUPPR IMAGE
    ("background: rgba(225,29,72,0.9);",
     "background: rgba(255,61,129,0.9);"),

    # 6. BOUTON PRIMAIRE (dégradé + pill + glow)
    ("background: linear-gradient(135deg, var(--accent), var(--accent-2));",
     "background: var(--grad);"),
    ("box-shadow: 0 4px 20px rgba(225,29,72,0.25);",
     "box-shadow: var(--glow);"),

    # 7. PILLS (border-radius complet)
    (".btn-primary {", ".btn-primary { border-radius: 999px;"),
    (".api-save-btn {", ".api-save-btn { border-radius: 999px;"),
    (".prompt-preset {", ".prompt-preset { border-radius: 999px;"),

    # 8. TITRE H1 (blanc + partie en dégradé)
    ("background: linear-gradient(135deg, var(--accent), var(--accent-2));\n        -webkit-background-clip: text; background-clip: text;\n        -webkit-text-fill-color: transparent;\n    }\n    .subtitle",
     "color: #fff;\n    }\n    h1 .grad { background: var(--grad); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }\n    .subtitle"),
    ("<h1>Studio Marketing</h1>",
     "<h1>Studio <span class=\"grad\">Marketing</span></h1>"),

    # 9. NAVIGATION COMPLÈTE (cohérente avec le site)
    ("<nav class=\"jcode-nav\">\n    <span class=\"logo\">JCode</span>\n    <a href=\"/studio/prompts/\">← Studio Prompts</a>\n    <a href=\"/studio/marketing/\">Studio Marketing</a>\n</nav>",
     "<nav class=\"jcode-nav\" style=\"background:rgba(15,23,42,0.85);backdrop-filter:blur(12px);border-bottom:1px solid var(--border);padding:0.9rem 1.5rem;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:50;\">\n"
     "    <a href=\"/\" style=\"display:flex;align-items:center;gap:0.6rem;text-decoration:none;\">\n"
     "        <span class=\"logo-mark\" style=\"width:34px;height:34px;border-radius:10px;background:var(--grad);color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center;\">J</span>\n"
     "        <span class=\"logo-txt\" style=\"color:#fff;font-weight:800;letter-spacing:0.02em;\">JCODE</span>\n"
     "        <span style=\"width:1px;height:18px;background:var(--border);\"></span>\n"
     "        <span class=\"logo-sub\" style=\"color:var(--ink-faint);font-size:0.68rem;letter-spacing:0.18em;font-weight:600;\">STUDIO IA VIDÉO</span>\n"
     "    </a>\n"
     "    <div class=\"nav-links\" style=\"display:flex;align-items:center;gap:1.4rem;flex-wrap:wrap;\">\n"
     "        <a href=\"/studio/prompts/\" style=\"color:var(--ink-dim);text-decoration:none;font-size:0.85rem;\">Studio</a>\n"
     "        <a href=\"/studio/marketing/\" style=\"color:#fff;text-decoration:none;font-size:0.85rem;font-weight:600;\">Marketing</a>\n"
     "        <a href=\"https://jcode.store\" target=\"_blank\" rel=\"noopener\" style=\"background:var(--grad);color:#fff !important;padding:0.5rem 1rem;border-radius:999px;font-weight:600;text-decoration:none;font-size:0.85rem;\">jcode.store ↗</a>\n"
     "    </div>\n"
     "</nav>"),

    # 10. HERO BADGE (au-dessus du titre)
    ("<header>\n    <h1>",
     "<header>\n    <div style=\"display:inline-flex;align-items:center;gap:0.5rem;background:var(--panel);border:1px solid var(--border);padding:0.4rem 0.95rem;border-radius:999px;font-size:0.72rem;color:var(--ink-dim);margin-bottom:1rem;\">\n"
     "        <span style=\"width:7px;height:7px;border-radius:50%;background:var(--success);\"></span>\n"
     "        Nouveau · génération directe de pubs IA\n"
     "    </div>\n    <h1>"),

    # 11. SUPPRIMER L'ANCIEN LOGO TEXTUEL (devient inutile avec le logo carré)
    (".jcode-nav .logo {\n        font-weight: 700;\n        color: #fff;\n        margin-right: auto;\n    }\n", ""),
]

for old, new in REPLACEMENTS:
    if old not in html:
        print(f"⚠️  NON TROUVÉ : {old[:40]}...")
    else:
        html = html.replace(old, new, 1)

# ═══ VERIFICATION JS ═══
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

# ═══ BACKUP + ECRITURE ═══
backup = "/tmp/studio-marketing-harmonize-" + time.strftime("%Y%m%d-%H%M%S") + ".bak"
shutil.copy2(TARGET, backup)
open(TARGET, "w", encoding="utf-8").write(html)
print("✅ Sauvegarde : " + backup)
print("✅ Patch appliqué : navigation, couleurs, dégradé signature, polices Inter")
