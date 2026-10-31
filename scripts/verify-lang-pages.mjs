#!/usr/bin/env node
// Vérifications des pages nl/ et en/ (générées depuis index.html).
// Usage : node scripts/verify-lang-pages.mjs <mode> [révision-git]
// Modes : keys | drift <rev> | french-leak | grid | css | lang-active | links
// Lancer depuis la racine du dépôt. Ne modifie aucun fichier.
import { readFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';

const [, , mode, arg] = process.argv;
const ROOT = process.cwd();
const LANGS = ['nl', 'en'];
const read = (p) => readFileSync(join(ROOT, p), 'utf8');
const page = (l) => (l === 'fr' ? 'index.html' : `${l}/index.html`);

let accepted = { drift: [], leaks: [], links: [] };
if (existsSync(join(ROOT, 'scripts/lang-accepted.json'))) {
  accepted = { ...accepted, ...JSON.parse(read('scripts/lang-accepted.json')) };
}

function fail(title, lines) {
  console.error(`FAIL ${title} (${lines.length})`);
  for (const l of lines.slice(0, 400)) console.error('  - ' + l);
  if (lines.length > 400) console.error(`  ... et ${lines.length - 400} autres`);
  process.exit(1);
}
const control = (ok, what) => {
  if (!ok) { console.error(`FAIL témoin de contrôle : ${what}`); process.exit(1); }
};

const decode = (s) => s
  .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&quot;/g, '"')
  .replace(/&#x27;|&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>');
const norm = (s) => decode(s).replace(/\s+/g, ' ').trim();

// data-i18n / data-i18n-html -> liste des contenus internes
function i18nEntries(html) {
  const out = new Map();
  const open = /<([a-zA-Z0-9]+)\b[^>]*?\sdata-i18n(?:-html)?="([^"]+)"[^>]*>/g;
  let m;
  while ((m = open.exec(html))) {
    const [full, tag, key] = m;
    const start = m.index + full.length;
    const re = new RegExp(`<(/?)${tag}\\b[^>]*>`, 'gi');
    re.lastIndex = start;
    let depth = 1, e, end = -1;
    while ((e = re.exec(html))) {
      if (e[1]) depth--; else if (!/\/>$/.test(e[0])) depth++;
      if (depth === 0) { end = e.index; break; }
    }
    if (end < 0) continue;
    if (!out.has(key)) out.set(key, []);
    out.get(key).push(norm(html.slice(start, end)));
  }
  return out;
}

// Segments de texte visibles (hors script/style/commentaires) + attributs lisibles
function visibleSegments(html) {
  const h = html
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[\s\S]*?<\/style>/gi, ' ');
  const segs = [];
  for (const t of h.split(/<[^>]*>/)) { const s = norm(t); if (/\p{L}/u.test(s)) segs.push(s); }
  for (const m of h.matchAll(/\b(?:placeholder|title|alt|aria-label)="([^"]*)"/g)) {
    const s = norm(m[1]); if (/\p{L}/u.test(s)) segs.push(s);
  }
  return segs;
}

const FR_WORDS = ['votre', 'vous', 'nous', 'notre', 'des', 'une', 'avec', 'pour', 'dès', 'prêt', 'prêtes',
  'vidéos', 'publicitaires', 'partenaire', 'automatisation', 'automatisations', 'construit', 'mois',
  'gratuit', 'découvrir', 'réserver', 'contactez', 'offres', 'tarifs', 'accroche', 'intégrés', 'publier'];
const FR_RE = new RegExp(`(?<![\\p{L}])(?:${FR_WORDS.join('|')})(?![\\p{L}])|[àâçèêùûô]`, 'iu');
const looksFrench = (s) => FR_RE.test(s);

function activeLangs(html) {
  const res = [];
  for (const m of html.matchAll(/<a\b[^>]*class="lang-btn"[^>]*>/g)) {
    const lang = (m[0].match(/data-lang="([a-z]{2})"/) || [])[1];
    if (lang && /\sdata-lang-active\b/.test(m[0])) res.push(lang);
  }
  return res;
}

function resolveLocal(href) {
  const p = href.split('#')[0].split('?')[0];
  if (!p.startsWith('/') || p.startsWith('//')) return null;
  const rel = p.replace(/^\/+/, '');
  const cands = p.endsWith('/') ? [join(rel, 'index.html')]
    : /\.[a-z0-9]+$/i.test(rel) ? [rel] : [rel + '.html', join(rel, 'index.html')];
  return cands.length ? cands : ['index.html'];
}
const exists = (c) => c.some((x) => existsSync(join(ROOT, x === '' ? 'index.html' : x)));

const modes = {
  keys() {
    const rootKeys = new Set(i18nEntries(read('index.html')).keys());
    const problems = [];
    for (const l of LANGS) {
      const k = new Set(i18nEntries(read(page(l))).keys());
      for (const x of k) if (!rootKeys.has(x)) problems.push(`${l}: clé absente de la racine : ${x}`);
      for (const x of rootKeys) if (!k.has(x)) problems.push(`${l}: clé de la racine absente : ${x}`);
    }
    if (rootKeys.size < 20) problems.push(`racine : seulement ${rootKeys.size} clés lues (parseur ou fichier suspect)`);
    if (problems.length) fail('clés data-i18n différentes de la racine', problems);
    console.log(`keys verification passed (${rootKeys.size} clés, nl et en identiques à la racine)`);
  },

  drift() {
    if (!arg) { console.error('usage : drift <révision-git>'); process.exit(2); }
    const problems = []; let compared = 0, removed = 0, added = 0;
    for (const l of LANGS) {
      const oldHtml = execFileSync('git', ['show', `${arg}:${page(l)}`], { cwd: ROOT, encoding: 'utf8', maxBuffer: 1 << 26 });
      const oldE = i18nEntries(oldHtml), newE = i18nEntries(read(page(l)));
      for (const [key, olds] of oldE) {
        if (!newE.has(key)) { removed++; continue; }
        compared++;
        const news = newE.get(key);
        if (olds.join('\u0001') !== news.join('\u0001') && !accepted.drift.includes(`${l}:${key}`)) {
          problems.push(`${l}:${key}\n      avant : ${olds[0].slice(0, 110)}\n      après : ${news[0].slice(0, 110)}`);
        }
      }
      for (const key of newE.keys()) if (!oldE.has(key)) added++;
    }
    console.error(`info : ${compared} clés comparées, ${removed} clés disparues, ${added} clés nouvelles (par rapport à ${arg})`);
    if (compared < 10) fail('comparaison vide : trop peu de clés communes avec la révision de référence', [`${compared} clés comparées`]);
    if (problems.length) fail(`traductions modifiées depuis ${arg}`, problems);
    console.log(`drift verification passed (${compared} traductions identiques à ${arg}, ou acceptées)`);
  },

  'french-leak'() {
    control(looksFrench('Vidéos publicitaires IA prêtes à publier pour votre site'), 'phrase française non détectée');
    control(!looksFrench('Ready-to-publish AI ad videos for your site'), 'phrase anglaise détectée à tort');
    control(!looksFrench("Gebruiksklare AI-advertentievideo's voor uw website"), 'phrase néerlandaise détectée à tort');
    const problems = [];
    for (const l of LANGS) {
      for (const s of new Set(visibleSegments(arg ? execFileSync('git', ['show', `${arg}:${page(l)}`], { cwd: ROOT, encoding: 'utf8', maxBuffer: 1 << 26 }) : read(page(l))))) {
        if (looksFrench(s) && !accepted.leaks.includes(s)) problems.push(`${l}: ${s.slice(0, 120)}`);
      }
    }
    if (problems.length) fail('texte français visible dans nl/ ou en/', problems);
    console.log('french-leak verification passed (aucun texte français visible dans nl/ et en/)');
  },

  grid() {
    const re = /\.services-grid\s*\{[^}]*grid-template-columns:\s*repeat\(2,\s*1fr\)/;
    control(!re.test('.services-grid { display:grid; grid-template-columns: repeat(3, 1fr); }'), 'repeat(3) accepté à tort');
    control(re.test('.services-grid { display:grid; grid-template-columns: repeat(2, 1fr); }'), 'repeat(2) refusé à tort');
    const bad = ['fr', ...LANGS].filter((l) => !re.test(read(page(l)))).map((l) => `${page(l)} : .services-grid n'est pas en repeat(2, 1fr)`);
    if (bad.length) fail('grille des services pas en 2 colonnes', bad);
    console.log('grid verification passed (2 colonnes dans index.html, nl/ et en/)');
  },

  css() {
    const needles = ['.logo { white-space: nowrap; }', '.nav-links a { white-space: nowrap; }',
      'html[lang="en"] .hero-title', 'html[lang="nl"] .hero-title'];
    const has = (h, n) => h.replace(/\s+/g, ' ').includes(n);
    control(!has('/* vide */', needles[0]), 'règle trouvée dans un texte vide');
    const bad = [];
    for (const l of ['fr', ...LANGS]) {
      const h = read(page(l));
      for (const n of needles) if (!has(h, n)) bad.push(`${page(l)} : règle manquante : ${n}`);
    }
    if (bad.length) fail('règles CSS menu / titre absentes', bad);
    console.log('css verification passed (menu sur une ligne et titre EN/NL réduit présents dans les 3 pages)');
  },

  'lang-active'() {
    const two = '<a class="lang-btn" data-lang="fr" data-lang-active="fr">FR</a><a class="lang-btn" data-lang="en" data-lang-active="en">EN</a>';
    control(activeLangs(two).join() === 'fr,en', 'deux boutons actifs non détectés');
    const bad = [];
    for (const l of ['fr', ...LANGS]) {
      const a = activeLangs(read(page(l)));
      if (a.length !== 1 || a[0] !== l) bad.push(`${page(l)} : boutons actifs = [${a.join(', ') || 'aucun'}], attendu [${l}]`);
    }
    if (bad.length) fail('mauvais bouton de langue actif', bad);
    console.log('lang-active verification passed (un seul bouton actif par page, celui de la langue)');
  },

  links() {
    control(!exists(resolveLocal('/__unlazy_lien_inexistant__.html')), 'lien inexistant considéré comme présent');
    control(exists(resolveLocal('/')), 'la racine / est introuvable');
    const bad = new Set();
    for (const l of LANGS) {
      for (const m of read(page(l)).matchAll(/\b(?:href|src)="(\/[^"]*)"/g)) {
        const c = resolveLocal(m[1]);
        if (c && !exists(c) && !accepted.links.includes(m[1])) bad.add(`${l}: ${m[1]}`);
      }
    }
    if (bad.size) fail('liens internes vers un fichier introuvable', [...bad]);
    console.log('links verification passed (tous les liens internes de nl/ et en/ existent)');
  },
};

if (!modes[mode]) { console.error('modes : ' + Object.keys(modes).join(' | ')); process.exit(2); }
modes[mode]();
