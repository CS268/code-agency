#!/usr/bin/env python3
"""Régénère nl/index.html et en/index.html depuis index.html (racine)."""
import html, json, re, shutil, sys

WRITE = "--write" in sys.argv
read = lambda p: open(p, encoding="utf-8").read()
root = read("index.html")
T = json.load(open("i18n/translations.json", encoding="utf-8"))

HEAD_KEEP = [
    r'<title>.*?</title>',
    r'<meta name="description"[^>]*>',
    r'<meta property="og:title"[^>]*>',
    r'<meta property="og:description"[^>]*>',
    r'<meta property="og:url"[^>]*>',
    r'<meta property="og:locale"[^>]*>',
    r'<meta name="twitter:title"[^>]*>',
    r'<meta name="twitter:description"[^>]*>',
]
NODE = re.compile(
    r'(?P<open><(?P<tag>[a-zA-Z0-9]+)\b[^>]*?\sdata-i18n(?P<h>-html)?="(?P<key>[^"]+)"[^>]*>)'
    r'(?P<inner>.*?)(?P<close></(?P=tag)>)', re.S)

def build(lang):
    old = read(f"{lang}/index.html")
    head, sep, body = root.partition("</head>")
    if not sep:
        sys.exit("</head> introuvable dans index.html")
    head, n = re.subn(r'<html lang="fr">', f'<html lang="{lang}">', head, count=1)
    if n != 1:
        sys.exit('<html lang="fr"> introuvable dans index.html')
    if "<base " in head:
        sys.exit("la racine contient déjà un <base>")
    head = head.replace(
        "<head>",
        '<head><base href="/"><script>try{localStorage.setItem(\'jcode_lang\',\'%s\')}catch(e){}</script>' % lang, 1)
    canon = '<link rel="canonical" href="https://jcode.store/">'
    if canon not in head:
        sys.exit("canonical introuvable dans index.html")
    head = head.replace(canon, f'<link rel="canonical" href="https://jcode.store/{lang}/">', 1)
    old_head = old.partition("</head>")[0]
    notes = []
    for pat in HEAD_KEEP:
        a, b = re.search(pat, head, re.S), re.search(pat, old_head, re.S)
        if a and b:
            head = head[:a.start()] + b.group(0) + head[a.end():]
        else:
            notes.append("head sans équivalent : " + pat[:32])

    st = {"remplacés": 0, "ignorés": [], "manquants": []}
    def sub(m):
        key, tag, inner = m["key"], m["tag"], m["inner"]
        val = T.get(key, {}).get(lang)
        if val is None:
            st["manquants"].append(key); return m.group(0)
        if re.search(r"<" + tag + r"\b", inner) or (not m["h"] and "<" in inner):
            st["ignorés"].append(key); return m.group(0)
        st["remplacés"] += 1
        txt = val if m["h"] else html.escape(val, quote=False)
        return m["open"] + txt + m["close"]
    body = NODE.sub(sub, body)
    anchors = body.count('href="#')
    body = body.replace('href="#', f'href="/{lang}/#')
    body = body.replace("studio/index.html?lang=fr", f"studio/index.html?lang={lang}")
    return head + sep + body, st, anchors, notes

results, bad = {}, False
for lang in ("nl", "en"):
    out, st, anchors, notes = build(lang)
    print(f"[{lang}] textes remplacés : {st['remplacés']} | ancres réécrites : {anchors} "
          f"| ignorés : {len(st['ignorés'])} | clés absentes du JSON : {len(st['manquants'])}")
    if st["ignorés"]:
        print("   ignorés (à vérifier à l'écran) :", ", ".join(st["ignorés"][:10]))
    if st["manquants"]:
        print("   MANQUANTES :", ", ".join(st["manquants"][:10])); bad = True
    for x in notes:
        print("  ", x)
    results[lang] = out

if bad:
    sys.exit("Clés absentes du JSON : rien écrit.")
if not WRITE:
    print("Simulation seulement. Relance avec --write pour écrire.")
    sys.exit(0)
for lang, out in results.items():
    shutil.copy(f"{lang}/index.html", f"{lang}/index.html.bak-revamp")
    open(f"{lang}/index.html", "w", encoding="utf-8").write(out)
print("OK : nl/index.html et en/index.html régénérés (sauvegardes .bak-revamp).")
