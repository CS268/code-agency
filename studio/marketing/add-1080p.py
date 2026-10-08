#!/usr/bin/env python3
"""Ajoute l'option 1080P premium (v2 robuste)"""
import os, re, shutil, subprocess, sys, tempfile, time

TARGET = os.path.expanduser("~/jcode-agency/studio/marketing/index.html")
if not os.path.isfile(TARGET):
    sys.exit("ABANDON : fichier introuvable : " + TARGET)

html = open(TARGET, encoding="utf-8").read()

if "resolution-select" in html or "resolution: state.resolution" in html:
    sys.exit("ABANDON : le patch 1080P semble déjà appliqué.")

# 1. Selecteur dans l'UI (après le select intensite)
ui_anchor = '<select id="intensity-select">'
if ui_anchor not in html:
    sys.exit("ABANDON : select intensité introuvable.")
ui_block = '''            <div class="input-row">
                <label class="input-label">Qualité vidéo</label>
                <select id="resolution-select">
                    <option value="720P" selected>720P HD · standard (inclus)</option>
                    <option value="1080P">1080P Full HD · premium</option>
                </select>
                <div class="prompt-main-hint" style="margin-top:0.4rem;">
                    💡 La 1080P offre des détails plus nets pour YouTube / site web. La 720P est optimisée TikTok / Reels / Instagram et réduit le coût de génération.
                </div>
            </div>
        </div>'''
# on insère le bloc juste avant la fermeture de la section tech
tech_close = html.rfind('</div>\n    </div>\n</div>\n\n<button type="button" class="btn-primary"')
if tech_close == -1:
    # fallback : on insère après le dernier </select> de la section tech
    idx = html.find('</select>\n            </div>\n        </div>\n    </div>\n\n<button type="button" class="btn-primary"')
    if idx == -1:
        sys.exit("ABANDON : point d'insertion UI introuvable.")
    html = html[:idx] + '</select>\n            </div>\n' + ui_block.replace('        </div>\n', '', 1) + html[idx+len('</select>\n            </div>\n        </div>\n'):]
else:
    html = html[:tech_close] + ui_block + html[tech_close+len('</div>\n    </div>\n</div>\n'):]

# 2. Etat
state_pat = re.compile(r"(intensity: 'moderate',)")
if not state_pat.search(html):
    sys.exit("ABANDON : état introuvable.")
html = state_pat.sub(r"\1\n    resolution: '720P',", html, count=1)

# 3. Payload (robuste : peu importe l'indentation / presence de width-height)
payload_pat = re.compile(r"frame_rate: FRAME_RATE,?")
if not payload_pat.search(html):
    sys.exit("ABANDON : frame_rate introuvable dans le payload.")
html = payload_pat.sub("frame_rate: FRAME_RATE,\n        resolution: state.resolution,", html, count=1)

# 4. Listener (insertion avant le listener du bouton generer)
gen_line = "    document.getElementById('generate-btn')?.addEventListener('click', startGeneration);"
if gen_line not in html:
    sys.exit("ABANDON : listener generate-btn introuvable.")
listener = "    document.getElementById('resolution-select')?.addEventListener('change', e => {\n        state.resolution = e.target.value;\n    });\n"
html = html.replace(gen_line, listener + gen_line, 1)

# 5. Verification JS
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

# 6. Backup + ecriture
backup = "/tmp/studio-marketing-1080p-" + time.strftime("%Y%m%d-%H%M%S") + ".bak"
shutil.copy2(TARGET, backup)
open(TARGET, "w", encoding="utf-8").write(html)
print("✅ Sauvegarde : " + backup)
print("✅ Option 1080P premium ajoutée (v2)")
