#!/usr/bin/env python3
"""Injecte data-nl / data-en (et variantes placeholder) dans un HTML i18n.

Parse les balises caractere par caractere : un `>` dans un attribut
(ex. alt="a > b") ne coupe plus la balise.

Idempotent. Ignore le contenu de script/style/textarea/title.
N'ecrit pas si des cles manquent. Conserve les traductions existantes
tant qu'une cle n'est pas remplaçable.

Limite : un `</script>` (ou style/textarea/title) dans une chaine JS
est traite comme vraie fermeture — tokenizer HTML incomplet.

Usage:
  python3 inject_i18n.py
  python3 inject_i18n.py --html ~/jcode-agency/studio/index.html
  python3 inject_i18n.py --html ~/jcode-agency/studio/prompts/index.html
  python3 inject_i18n.py --dry-run
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

DEFAULT_HTML = Path.home() / "jcode-agency" / "studio" / "index.html"
DEFAULT_MAP = Path("/tmp/studio_i18n_map.json")

PAIRS = (
    ("data-fr", "data-nl", "data-en"),
    ("data-fr-placeholder", "data-nl-placeholder", "data-en-placeholder"),
)
SRC_ATTRS = {src for src, _, _ in PAIRS}
TARGET_ATTRS = {name for _, nl, en in PAIRS for name in (nl, en)}
PAIR_BY_SRC = {src: (nl, en) for src, nl, en in PAIRS}
RAW_TEXT_TAGS = frozenset({"script", "style", "textarea", "title"})
ATTR_NAME = re.compile(r"[^\s=/>]+")
TAG_NAME = re.compile(r"[^\s/>]+")


def scan_tag_end(src: str, lt: int) -> int | None:
    """Index du '>' de fermeture, en ignorant les '>' quotes."""
    i = lt + 1
    n = len(src)
    quote = None
    while i < n:
        c = src[i]
        if quote:
            if c == quote:
                quote = None
            i += 1
            continue
        if c in ('"', "'"):
            quote = c
            i += 1
            continue
        if c == ">":
            return i
        if c == "<":
            return None
        i += 1
    return None


def skip_raw_text(src: str, after_open: int, tag_name: str) -> int:
    """Saute jusqu'apres </tag_name> (ASCII, casse ignoree, index source)."""
    i = after_open
    n = len(src)
    name_len = len(tag_name)
    while i < n:
        pos = src.find("</", i)
        if pos < 0:
            return n
        k = pos + 2
        while k < n and src[k].isspace():
            k += 1
        matched = (
            k + name_len <= n
            and all(src[k + t].lower() == tag_name[t] for t in range(name_len))
        )
        if matched:
            end = k + name_len
            if end >= n or src[end].isspace() or src[end] in ">/":
                gt = scan_tag_end(src, pos)
                return n if gt is None else gt + 1
        i = pos + 1
    return n


def skip_declaration(src: str, lt: int) -> int:
    """Saute <!...> / <?...> en tenant compte des quotes."""
    gt = scan_tag_end(src, lt)
    if gt is None:
        end = src.find(">", lt + 2)
        return len(src) if end < 0 else end + 1
    return gt + 1


def tag_name_of(tag: str) -> str:
    m = TAG_NAME.match(tag, 1)
    return m.group(0).lower() if m else ""


def iter_opening_tags(src: str):
    i = 0
    n = len(src)
    while i < n:
        lt = src.find("<", i)
        if lt < 0:
            return
        if src.startswith("<!--", lt):
            end = src.find("-->", lt + 4)
            i = n if end < 0 else end + 3
            continue
        if src.startswith("<![CDATA[", lt):
            end = src.find("]]>", lt + 9)
            i = n if end < 0 else end + 3
            continue
        if src.startswith("<!", lt) or src.startswith("<?", lt):
            i = skip_declaration(src, lt)
            continue
        if lt + 1 < n and src[lt + 1] == "/":
            gt = scan_tag_end(src, lt)
            i = n if gt is None else gt + 1
            continue
        gt = scan_tag_end(src, lt)
        if gt is None:
            i = lt + 1
            continue
        end = gt + 1
        tag = src[lt:end]
        name = tag_name_of(tag)
        yield lt, end, tag
        if name in RAW_TEXT_TAGS and not tag.rstrip().endswith("/>"):
            i = skip_raw_text(src, end, name)
        else:
            i = end


def split_tag(tag: str):
    stripped = tag.rstrip()
    if stripped.endswith("/>"):
        inner_end = tag.rfind("/>")
        closer = tag[inner_end:]
    elif stripped.endswith(">"):
        inner_end = tag.rfind(">")
        closer = tag[inner_end:]
    else:
        return tag[:1], [], tag[1:] if len(tag) > 1 else ""
    m = ATTR_NAME.match(tag, 1)
    if not m:
        return tag[:1], [], closer
    prefix = tag[: m.end()]
    attrs = []
    i = m.end()
    n = inner_end
    while i < n:
        start = i
        while i < n and tag[i].isspace():
            i += 1
        ws = tag[start:i]
        if i >= n:
            if ws:
                attrs.append({"kind": "ws", "raw": ws})
            break
        m = ATTR_NAME.match(tag, i)
        if not m:
            attrs.append({"kind": "raw", "raw": tag[start:n]})
            break
        name = m.group(0)
        i = m.end()
        value = None
        eq = ""
        if i < n:
            eq_start = i
            while i < n and tag[i].isspace():
                i += 1
            if i < n and tag[i] == "=":
                i += 1
                while i < n and tag[i].isspace():
                    i += 1
                eq = tag[eq_start:i]
                if i < n and tag[i] in ('"', "'"):
                    q = tag[i]
                    j = i + 1
                    while j < n and tag[j] != q:
                        j += 1
                    value = tag[i : j + 1] if j < n else tag[i:n]
                    i = j + 1 if j < n else n
                else:
                    j = i
                    while j < n and not tag[j].isspace() and tag[j] != ">":
                        if tag[j] == "/" and j + 1 < len(tag) and tag[j + 1] == ">":
                            break
                        j += 1
                    value = tag[i:j]
                    i = j
            else:
                i = eq_start
        attrs.append(
            {
                "kind": "attr",
                "name": name,
                "ws": ws,
                "eq": eq,
                "value": value,
            }
        )
    return prefix, attrs, closer


def unquote(value: str | None) -> str:
    if value is None:
        return ""
    if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
        return html.unescape(value[1:-1])
    return html.unescape(value)


def attr_html(value: str) -> str:
    return html.escape(str(value), quote=True)


def rebuild(prefix: str, attrs: list, closer: str) -> str:
    parts = [prefix]
    for a in attrs:
        if a["kind"] != "attr":
            parts.append(a["raw"])
            continue
        if a["value"] is None:
            parts.append(f'{a["ws"]}{a["name"]}')
        else:
            parts.append(f'{a["ws"]}{a["name"]}{a["eq"]}{a["value"]}')
    parts.append(closer)
    return "".join(parts)


def lookup_entry(mapping: dict, key: str):
    entry = mapping.get(key)
    if not isinstance(entry, dict):
        return None
    nl, en = entry.get("nl"), entry.get("en")
    if not isinstance(nl, str) or not isinstance(en, str):
        return None
    return nl, en


def inject_tag(tag: str, mapping: dict, stats: dict, missing: list) -> str:
    prefix, attrs, closer = split_tag(tag)
    lowered = [
        a["name"].lower() if a["kind"] == "attr" else None for a in attrs
    ]
    if not any(name in SRC_ATTRS for name in lowered if name):
        return tag

    stats["tags"] += 1
    seen_src: set[str] = set()
    out = []
    skip_targets = set()
    pending_pairs: dict[str, tuple[str, str, str]] = {}
    dup = False

    for a, lname in zip(attrs, lowered):
        if a["kind"] != "attr":
            out.append(a)
            continue
        if lname in SRC_ATTRS:
            if lname in seen_src:
                stats["dup_src"] += 1
                dup = True
                out.append(a)
                continue
            seen_src.add(lname)
            key = unquote(a["value"])
            found = lookup_entry(mapping, key)
            nl_name, en_name = PAIR_BY_SRC[lname]
            if found is None:
                stats["manquants"] += 1
                missing.append((lname, key))
                out.append(a)
                continue
            skip_targets.add(nl_name)
            skip_targets.add(en_name)
            pending_pairs[lname] = (nl_name, en_name, key)
            out.append(a)
            continue
        out.append(a)

    if dup:
        return tag

    filtered = []
    for a in out:
        if a["kind"] == "attr" and a["name"].lower() in skip_targets:
            if filtered and filtered[-1]["kind"] == "ws":
                filtered.pop()
            continue
        filtered.append(a)
        if a["kind"] != "attr":
            continue
        lname = a["name"].lower()
        if lname not in pending_pairs:
            continue
        nl_name, en_name, key = pending_pairs[lname]
        nl, en = lookup_entry(mapping, key)
        inject_ws = a["ws"] if a["ws"] else " "
        filtered.append(
            {
                "kind": "attr",
                "name": nl_name,
                "ws": inject_ws,
                "eq": "=",
                "value": f'"{attr_html(nl)}"',
            }
        )
        filtered.append(
            {
                "kind": "attr",
                "name": en_name,
                "ws": inject_ws,
                "eq": "=",
                "value": f'"{attr_html(en)}"',
            }
        )
        stats["ok"] += 1
    return rebuild(prefix, filtered, closer)


def tag_pairs_ok(tag: str) -> tuple[bool, dict[str, int]]:
    _prefix, attrs, _closer = split_tag(tag)
    counts: dict[str, int] = {src_name: 0 for src_name, _, _ in PAIRS}
    for _, nl, en in PAIRS:
        counts[nl] = 0
        counts[en] = 0
    for a in attrs:
        if a["kind"] != "attr":
            continue
        lname = a["name"].lower()
        if lname in counts:
            counts[lname] += 1
    ok = True
    for src_name, nl, en in PAIRS:
        if counts[src_name] == 0:
            continue
        if counts[src_name] != 1 or counts[nl] != 1 or counts[en] != 1:
            ok = False
    return ok, counts


def report_pairs(label: str, html_text: str) -> bool:
    totals = {src_name: 0 for src_name, _, _ in PAIRS}
    for _, nl, en in PAIRS:
        totals[nl] = 0
        totals[en] = 0
    broken = 0
    for _start, _end, tag in iter_opening_tags(html_text):
        ok, counts = tag_pairs_ok(tag)
        for k, v in counts.items():
            totals[k] = totals.get(k, 0) + v
        if any(counts.get(src_name, 0) for src_name, _, _ in PAIRS) and not ok:
            broken += 1
    print(
        f"{label} : data-fr={totals['data-fr']}  "
        f"data-nl={totals['data-nl']}  data-en={totals['data-en']}"
    )
    print(
        f"{label} : data-fr-placeholder={totals['data-fr-placeholder']}  "
        f"data-nl-placeholder={totals['data-nl-placeholder']}  "
        f"data-en-placeholder={totals['data-en-placeholder']}"
    )
    if broken:
        print(f"{label} : {broken} balise(s) avec paires incompletes/dupliquees")
        return False
    return True


def load_mapping(map_path: Path) -> dict:
    data = json.loads(map_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Le mapping doit etre un objet JSON {cle: {nl, en}}")
    cleaned = {}
    bad = 0
    for key, entry in data.items():
        if not isinstance(key, str):
            bad += 1
            continue
        if not isinstance(entry, dict):
            bad += 1
            continue
        nl, en = entry.get("nl"), entry.get("en")
        if not isinstance(nl, str) or not isinstance(en, str):
            bad += 1
            continue
        cleaned[key] = {"nl": nl, "en": en}
    if bad:
        print(f"Mapping : {bad} entree(s) ignoree(s) (format invalide)")
    return cleaned


def process(html_path: Path, map_path: Path, dry_run: bool) -> int:
    if not html_path.exists():
        print(f"Introuvable : {html_path}", file=sys.stderr)
        return 1
    if not map_path.exists():
        print(f"Introuvable : {map_path}", file=sys.stderr)
        return 1

    try:
        mapping = load_mapping(map_path)
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        print(f"Mapping invalide : {exc}", file=sys.stderr)
        return 1

    print(f"Mapping charge : {len(mapping)} entrees")
    print(f"Cible          : {html_path}")

    try:
        raw = html_path.read_bytes()
        src = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"Lecture impossible : {exc}", file=sys.stderr)
        return 1

    stats = {"tags": 0, "ok": 0, "manquants": 0, "dup_src": 0}
    missing: list[tuple[str, str]] = []
    chunks = []
    last = 0
    for start, end, tag in iter_opening_tags(src):
        chunks.append(src[last:start])
        chunks.append(inject_tag(tag, mapping, stats, missing))
        last = end
    chunks.append(src[last:])
    out = "".join(chunks)

    print()
    print(f"Balises i18n (data-fr*) : {stats['tags']}")
    print(f"  -> paires injectees   : {stats['ok']}")
    print(f"  -> cle absente        : {stats['manquants']}")
    if stats["dup_src"]:
        print(f"  -> data-fr duplique   : {stats['dup_src']}")
    for attr, key in sorted(set(missing), key=lambda x: (x[0], x[1])):
        print(f"     ?? [{attr}] {key!r}")

    if stats["manquants"] > 0:
        print()
        print("Stop : cles manquantes, aucune ecriture.")
        report_pairs("Simule", out)
        return 2

    if dry_run:
        print()
        print("Dry-run : aucun fichier ecrit.")
        ok = report_pairs("Simule", out)
        print("OK coherent." if ok else "ECHEC (dry-run)")
        return 0 if ok else 2

    backup = html_path.with_suffix(html_path.suffix + ".bak")
    try:
        shutil.copy2(html_path, backup)
        print(f"Sauvegarde     : {backup}")
    except OSError as exc:
        print(f"Backup impossible : {exc}", file=sys.stderr)
        return 1

    try:
        html_path.write_bytes(out.encode("utf-8"))
    except OSError as exc:
        print(f"Ecriture impossible : {exc}", file=sys.stderr)
        return 1

    try:
        final = html_path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"Relecture impossible : {exc}", file=sys.stderr)
        return 1

    print()
    ok = report_pairs("Post-ecriture", final)
    if ok:
        print("OK coherent.")
        return 0
    try:
        shutil.copy2(backup, html_path)
        print(f"ECHEC - restaure automatiquement depuis {backup}")
    except OSError:
        print(f"ECHEC - restaurer : mv {backup} {html_path}")
    return 2


def main() -> int:
    p = argparse.ArgumentParser(description="Injection i18n data-nl/data-en")
    p.add_argument("--html", type=Path, default=DEFAULT_HTML)
    p.add_argument("--map", type=Path, default=DEFAULT_MAP)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    return process(args.html, args.map, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())

