#!/usr/bin/env python3
"""Ajoute data-fr / data-fr-placeholder sur l'UI statique de studio/prompts/index.html.

Ne touche pas aux <script> (260 effets). Idempotent.
Usage:
  python3 annotate_prompts_fr.py
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

HTML_PATH = Path.home() / "jcode-agency" / "studio" / "prompts" / "index.html"

REPLACEMENTS = [
    (
        '<div class="logo-sub">Studio IA Vidéo</div>',
        '<div class="logo-sub" data-fr="Studio IA Vidéo">Studio IA Vidéo</div>',
    ),
    (
        '<a href="#studio">Studio</a>',
        '<a href="#studio" data-fr="Studio">Studio</a>',
    ),
    (
        '<a href="#categories">Catégories</a>',
        '<a href="#categories" data-fr="Catégories">Catégories</a>',
    ),
    (
        '<a href="#comment">Comment ça marche</a>',
        '<a href="#comment" data-fr="Comment ça marche">Comment ça marche</a>',
    ),
    (
        '<div class="pill"><span class="pill-dot"></span><b id="pillCount">—</b> effets cinématiques · moteur de prompts IA</div>',
        '<div class="pill"><span class="pill-dot"></span><b id="pillCount">—</b> <span data-fr="effets cinématiques · moteur de prompts IA">effets cinématiques · moteur de prompts IA</span></div>',
    ),
    (
        "<h1>Génère des vidéos IA<br><span class=\"grad\">au niveau cinéma.</span></h1>",
        '<h1><span data-fr="Génère des vidéos IA">Génère des vidéos IA</span><br><span class="grad" data-fr="au niveau cinéma.">au niveau cinéma.</span></h1>',
    ),
    (
        "<p>Sélectionne des actions, des mouvements de caméra, des effets VFX et des directions artistiques. Le studio assemble un prompt structuré, prêt à coller dans Sora, Runway, Kling ou Veo.</p>",
        '<p data-fr="Sélectionne des actions, des mouvements de caméra, des effets VFX et des directions artistiques. Le studio assemble un prompt structuré, prêt à coller dans Sora, Runway, Kling ou Veo.">Sélectionne des actions, des mouvements de caméra, des effets VFX et des directions artistiques. Le studio assemble un prompt structuré, prêt à coller dans Sora, Runway, Kling ou Veo.</p>',
    ),
    (
        'placeholder="Rechercher un effet, un style, une émotion…"',
        'placeholder="Rechercher un effet, un style, une émotion…" data-fr-placeholder="Rechercher un effet, un style, une émotion…"',
    ),
    (
        '<button class="btn btn-primary" id="btnRandom">⚡ Combo aléatoire</button>',
        '<button class="btn btn-primary" id="btnRandom" data-fr="⚡ Combo aléatoire">⚡ Combo aléatoire</button>',
    ),
    (
        '<button class="btn btn-ghost" id="btnFav">★ Mes favoris <span id="favCount" style="opacity:.6">(0)</span></button>',
        '<button class="btn btn-ghost" id="btnFav"><span data-fr="★ Mes favoris">★ Mes favoris</span> <span id="favCount" style="opacity:.6">(0)</span></button>',
    ),
    (
        '<button class="btn btn-ghost" id="btnReset">Réinitialiser</button>',
        '<button class="btn btn-ghost" id="btnReset" data-fr="Réinitialiser">Réinitialiser</button>',
    ),
    (
        '<div class="stat"><div class="stat-v" id="statTotal">—</div><div class="stat-l">Effets</div></div>',
        '<div class="stat"><div class="stat-v" id="statTotal">—</div><div class="stat-l" data-fr="Effets">Effets</div></div>',
    ),
    (
        '<div class="stat"><div class="stat-v">23</div><div class="stat-l">Catégories</div></div>',
        '<div class="stat"><div class="stat-v">23</div><div class="stat-l" data-fr="Catégories">Catégories</div></div>',
    ),
    (
        '<div class="stat"><div class="stat-v" id="statSel">0</div><div class="stat-l">Sélectionnés</div></div>',
        '<div class="stat"><div class="stat-v" id="statSel">0</div><div class="stat-l" data-fr="Sélectionnés">Sélectionnés</div></div>',
    ),
    (
        '<div class="stat"><div class="stat-v">5</div><div class="stat-l">Modèles IA</div></div>',
        '<div class="stat"><div class="stat-v">5</div><div class="stat-l" data-fr="Modèles IA">Modèles IA</div></div>',
    ),
    (
        '<div class="tb-count"><b id="shown">—</b> effets affichés</div>',
        '<div class="tb-count"><b id="shown">—</b> <span data-fr="effets affichés">effets affichés</span></div>',
    ),
    (
        '<option value="num">Tri · Numéro</option>',
        '<option value="num" data-fr="Tri · Numéro">Tri · Numéro</option>',
    ),
    (
        '<option value="num-desc">Tri · Numéro inversé</option>',
        '<option value="num-desc" data-fr="Tri · Numéro inversé">Tri · Numéro inversé</option>',
    ),
    (
        '<option value="az">Tri · A → Z</option>',
        '<option value="az" data-fr="Tri · A → Z">Tri · A → Z</option>',
    ),
    (
        '<option value="cat">Tri · Catégorie</option>',
        '<option value="cat" data-fr="Tri · Catégorie">Tri · Catégorie</option>',
    ),
    (
        "<h2>Comment ça marche</h2>",
        '<h2 data-fr="Comment ça marche">Comment ça marche</h2>',
    ),
    (
        '<div class="n">ÉTAPE 1</div>',
        '<div class="n" data-fr="ÉTAPE 1">ÉTAPE 1</div>',
    ),
    (
        "<h3>Sélectionne des effets</h3>",
        '<h3 data-fr="Sélectionne des effets">Sélectionne des effets</h3>',
    ),
    (
        "<p>Parcours 260 effets cinématiques classés par catégorie — action, caméra, VFX, style, genre. Clique pour ajouter un effet à ta combinaison.</p>",
        '<p data-fr="Parcours 260 effets cinématiques classés par catégorie — action, caméra, VFX, style, genre. Clique pour ajouter un effet à ta combinaison.">Parcours 260 effets cinématiques classés par catégorie — action, caméra, VFX, style, genre. Clique pour ajouter un effet à ta combinaison.</p>',
    ),
    (
        '<div class="n">ÉTAPE 2</div>',
        '<div class="n" data-fr="ÉTAPE 2">ÉTAPE 2</div>',
    ),
    (
        "<h3>Choisis ton modèle</h3>",
        '<h3 data-fr="Choisis ton modèle">Choisis ton modèle</h3>',
    ),
    (
        "<p>Sora 2, Runway Gen-4, Kling 2.0, Veo 3 ou Luma — chaque modèle a ses forces. Le studio adapte le format et la durée à ton choix.</p>",
        '<p data-fr="Sora 2, Runway Gen-4, Kling 2.0, Veo 3 ou Luma — chaque modèle a ses forces. Le studio adapte le format et la durée à ton choix.">Sora 2, Runway Gen-4, Kling 2.0, Veo 3 ou Luma — chaque modèle a ses forces. Le studio adapte le format et la durée à ton choix.</p>',
    ),
    (
        '<div class="n">ÉTAPE 3</div>',
        '<div class="n" data-fr="ÉTAPE 3">ÉTAPE 3</div>',
    ),
    (
        "<h3>Génère et colle</h3>",
        '<h3 data-fr="Génère et colle">Génère et colle</h3>',
    ),
    (
        "<p>Le studio assemble un prompt long, une version courte optimisée mots-clés, et un negative prompt. Copie et colle dans ton générateur préféré.</p>",
        '<p data-fr="Le studio assemble un prompt long, une version courte optimisée mots-clés, et un negative prompt. Copie et colle dans ton générateur préféré.">Le studio assemble un prompt long, une version courte optimisée mots-clés, et un negative prompt. Copie et colle dans ton générateur préféré.</p>',
    ),
    (
        "<span><kbd>/</kbd> rechercher</span>",
        '<span><kbd>/</kbd> <span data-fr="rechercher">rechercher</span></span>',
    ),
    (
        "<span><kbd>Shift</kbd>+<kbd>R</kbd> combo aléatoire</span>",
        '<span><kbd>Shift</kbd>+<kbd>R</kbd> <span data-fr="combo aléatoire">combo aléatoire</span></span>',
    ),
    (
        "<span><kbd>⌘</kbd>+<kbd>Enter</kbd> générer le prompt</span>",
        '<span><kbd>⌘</kbd>+<kbd>Enter</kbd> <span data-fr="générer le prompt">générer le prompt</span></span>',
    ),
    (
        "<span><kbd>Échap</kbd> fermer</span>",
        '<span><kbd>Échap</kbd> <span data-fr="fermer">fermer</span></span>',
    ),
    (
        "<span>clic droit ou bouton ★ au survol · ajouter aux favoris</span>",
        '<span data-fr="clic droit ou bouton ★ au survol · ajouter aux favoris">clic droit ou bouton ★ au survol · ajouter aux favoris</span>',
    ),
    (
        '<div class="dock-n"><span id="dockCount">0</span> élément(s) sélectionné(s)</div>',
        '<div class="dock-n"><span id="dockCount">0</span> <span data-fr="élément(s) sélectionné(s)">élément(s) sélectionné(s)</span></div>',
    ),
    (
        '<button class="dock-clear" id="dockClear">Vider</button>',
        '<button class="dock-clear" id="dockClear" data-fr="Vider">Vider</button>',
    ),
    (
        '<button class="btn btn-primary" id="btnGenerate">Générer le prompt ✦</button>',
        '<button class="btn btn-primary" id="btnGenerate" data-fr="Générer le prompt ✦">Générer le prompt ✦</button>',
    ),
    (
        '<h2 id="modalTitle">Prompt vidéo IA</h2>',
        '<h2 id="modalTitle" data-fr="Prompt vidéo IA">Prompt vidéo IA</h2>',
    ),
    (
        'aria-label="Fermer"',
        'aria-label="Fermer" data-fr="Fermer"',
    ),
    (
        '<label for="oModel">Modèle cible</label>',
        '<label for="oModel" data-fr="Modèle cible">Modèle cible</label>',
    ),
    (
        '<label for="oRatio">Format</label>',
        '<label for="oRatio" data-fr="Format">Format</label>',
    ),
    (
        '<option value="16:9">16:9 — Cinéma / YouTube</option>',
        '<option value="16:9" data-fr="16:9 — Cinéma / YouTube">16:9 — Cinéma / YouTube</option>',
    ),
    (
        '<option value="9:16">9:16 — TikTok / Reels</option>',
        '<option value="9:16" data-fr="9:16 — TikTok / Reels">9:16 — TikTok / Reels</option>',
    ),
    (
        '<option value="1:1">1:1 — Carré</option>',
        '<option value="1:1" data-fr="1:1 — Carré">1:1 — Carré</option>',
    ),
    (
        '<option value="2.39:1">2.39:1 — Anamorphique</option>',
        '<option value="2.39:1" data-fr="2.39:1 — Anamorphique">2.39:1 — Anamorphique</option>',
    ),
    (
        '<label for="oDur">Durée</label>',
        '<label for="oDur" data-fr="Durée">Durée</label>',
    ),
    (
        '<option value="5 s">5 secondes</option>',
        '<option value="5 s" data-fr="5 secondes">5 secondes</option>',
    ),
    (
        '<option value="10 s" selected>10 secondes</option>',
        '<option value="10 s" selected data-fr="10 secondes">10 secondes</option>',
    ),
    (
        '<option value="15 s">15 secondes</option>',
        '<option value="15 s" data-fr="15 secondes">15 secondes</option>',
    ),
    (
        '<option value="30 s">30 secondes</option>',
        '<option value="30 s" data-fr="30 secondes">30 secondes</option>',
    ),
    (
        '<button class="btn btn-primary" id="btnCopy">⧉ Copier le prompt</button>',
        '<button class="btn btn-primary" id="btnCopy" data-fr="⧉ Copier le prompt">⧉ Copier le prompt</button>',
    ),
    (
        '<button class="btn btn-ghost" id="btnDownload">↓ Télécharger .txt</button>',
        '<button class="btn btn-ghost" id="btnDownload" data-fr="↓ Télécharger .txt">↓ Télécharger .txt</button>',
    ),
    (
        '<button class="btn btn-ghost" id="btnShuffle">⟳ Variante</button>',
        '<button class="btn btn-ghost" id="btnShuffle" data-fr="⟳ Variante">⟳ Variante</button>',
    ),
    (
        '<span id="toastMsg">Copié !</span>',
        '<span id="toastMsg" data-fr="Copié !">Copié !</span>',
    ),
    (
        '<p>JCODE Studio — <span id="footTotal">260</span> effets cinématiques pour la génération vidéo IA.</p>',
        '<p>JCODE Studio — <span id="footTotal">260</span> <span data-fr="effets cinématiques pour la génération vidéo IA.">effets cinématiques pour la génération vidéo IA.</span></p>',
    ),
    (
        '">Propulsé par <a href="https://jcode.store" target="_blank" rel="noopener">jcode.store</a> · Agence de contenu & motion design</p>',
        '"><span data-fr="Propulsé par">Propulsé par</span> <a href="https://jcode.store" target="_blank" rel="noopener">jcode.store</a> · <span data-fr="Agence de contenu & motion design">Agence de contenu & motion design</span></p>',
    ),
]

SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.DOTALL | re.IGNORECASE)
PLACEHOLDER = "___JCODE_SCRIPT_{}___"


def main() -> int:
    if not HTML_PATH.exists():
        print(f"Introuvable : {HTML_PATH}", file=sys.stderr)
        return 1
    src = HTML_PATH.read_text(encoding="utf-8")

    scripts = []

    def save_script(match: re.Match) -> str:
        scripts.append(match.group(0))
        return PLACEHOLDER.format(len(scripts) - 1)

    out = SCRIPT_RE.sub(save_script, src)

    ok = 0
    missing = []
    for old, new in REPLACEMENTS:
        if new in out:
            ok += 1
            continue
        if old not in out:
            missing.append(old[:80])
            continue
        count = out.count(old)
        if count != 1:
            missing.append(f"({count}x) {old[:80]}")
            continue
        out = out.replace(old, new, 1)
        ok += 1

    if missing:
        print(f"Stop : {len(missing)} remplacement(s) introuvable(s), aucune ecriture.")
        for m in missing:
            print(f"  ?? {m!r}")
        return 2

    def restore_script(match: re.Match) -> str:
        return scripts[int(match.group(1))]

    out = re.sub(r"___JCODE_SCRIPT_(\d+)___", restore_script, out)

    backup = HTML_PATH.with_suffix(HTML_PATH.suffix + ".pre-fr.bak")
    shutil.copy2(HTML_PATH, backup)
    HTML_PATH.write_text(out, encoding="utf-8")
    n_fr = out.count("data-fr=")
    n_ph = out.count("data-fr-placeholder=")
    print(f"Sauvegarde : {backup}")
    print(f"Remplacements : {ok}/{len(REPLACEMENTS)}")
    print(f"data-fr={n_fr}  data-fr-placeholder={n_ph}")
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

