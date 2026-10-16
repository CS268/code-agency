// ConformShop – API d'analyse (Cloudflare Worker). Reçoit { url }, renvoie des lignes JSON en direct.
const ALLOW = ["https://jcode.store", "https://www.jcode.store", "http://localhost:8000"];
const MODEL = "claude-3-5-haiku-20241022";
const CMP = /cookiebot|axeptio|onetrust|didomi|tarteaucitron|iubenda|usercentrics|complianz|cookieyes|quantcast|consentmanager|cookie[- ]?consent|(accepter|accept|accepteer)[^<]{0,40}cookies/i;

// [pays, gravité, titre, regex, base légale, conseil, sanction]
const R = [
  ["EU", "ko", "Mentions légales / identité du commerçant", /mentions?\s+l[ée]gales|legal\s+notice|impressum|wettelijke\s+vermeldingen/i, "Directive 2000/31/CE art. 5", "Publie raison sociale, adresse, e-mail, numéro d'entreprise et de TVA.", "Amende administrative (ex: 1 500 € en France)"],
  ["EU", "ko", "Politique de confidentialité", /politique\s+de\s+confidentialit|privacy\s*(policy|statement)|privacybeleid|privacyverklaring|\bRGPD\b|\bGDPR\b|\bAVG\b/i, "RGPD art. 13-14", "Indique finalités, durées de conservation, droits et droit de plainte.", "RGPD : jusqu'à 20 M€ ou 4 % du CA mondial"],
  ["EU", "ko", "Bandeau de consentement aux cookies", CMP, "Directive ePrivacy art. 5(3)", "Installe un outil de consentement avec Accepter et Refuser.", "CNIL/APD : jusqu'à 20 M€ ou 4 % du CA (ex: Google 150 M€ en 2022)"],
  ["EU", "ko", "Conditions générales de vente", /conditions\s+g[ée]n[ée]rales|\bCGV\b|terms\s+(and| & )\s+conditions|terms\s+of\s+(sale|service)|algemene\s+voorwaarden/i, "Directive 2011/83/UE art. 5-6", "Publie des CGV : prix, livraison, paiement, retours, garanties.", "Sanction civile : nullité des clauses abusives + dommages-intérêts"],
  ["EU", "ko", "Droit de rétractation de 14 jours", /r[ée]tractation|withdrawal|herroeping|bedenktijd/i, "Directive 2011/83/UE art. 6 et 9", "Informe sur le délai de 14 jours et fournis un formulaire type.", "Amende DGCCRF : jusqu'à 15 000 € (personne morale)"],
  ["EU", "warn", "Prix toutes taxes comprises", /\bTTC\b|incl(uding|.)?\sVAT|incl.?\sbtw|inclusief\s*btw|TVA\s+incluse/i, "Directive 98/6/CE", "Indique que les prix incluent la TVA.", "Amende DGCCRF : jusqu'à 15 000 €"],
  ["EU", "warn", "Garantie légale de 2 ans", /garantie\s+l[ée]gale|legal\s+guarantee|wettelijke\s+garantie|garantie\s+de\s+conformit/i, "Directive (UE) 2019/771", "Rappelle la garantie légale de conformité.", "Amende DGCCRF : jusqu'à 15 000 €"],
  ["EU", "warn", "Médiation / règlement des litiges", /m[ée]diat|ombuds|geschillen|dispute\s+resolution|\bADR\b/i, "Directive 2013/11/UE", "Indique l'organisme de règlement des litiges compétent.", "Amende DGCCRF : jusqu'à 15 000 €"],
  ["EU", "warn", "Déclaration d'accessibilité", /accessibilit|toegankelijk/i, "Directive (UE) 2019/882 (depuis le 28/06/2025)", "Publie une déclaration d'accessibilité.", "Amende : jusqu'à 2 500 € (FR) + obligation de mise en conformité"],
  ["BE", "ko", "Numéro d'entreprise BCE/KBO", /\bBCE\b|\bKBO\b|num[ée]ro\s+d['']entreprise|ondernemingsnummer|\b0\d{3}[. ]\d{3}[. ]\d{3}\b/i, "Code de droit économique, livre XII", "Affiche le numéro d'entreprise.", "Amende SPF Économie : 26 € à 10 000 €"],
  ["BE", "warn", "Mention de l'APD/GBA", /autorit[ée]\s+de\s+protection\s+des\s+donn[ée]es|gegevensbeschermingsautoriteit|\bAPD\b|\bGBA\b/i, "RGPD art. 13(2)(d)", "Indique le droit de plainte auprès de l'APD.", "RGPD : jusqu'à 20 M€ ou 4 % du CA mondial"],
  ["FR", "ko", "Mentions LCEN (SIREN, RCS, capital)", /\bSIRET\b|\bSIREN\b|\bRCS\b|capital\s+social/i, "LCEN art. 6-III", "Ajoute forme juridique, capital, SIREN/RCS, siège.", "Amende : jusqu'à 75 000 € (personne morale)"],
  ["FR", "ko", "Hébergeur et directeur de publication", /h[ée]bergeur|directeur\s+de\s+(la\s+)?publication/i, "LCEN art. 6-III", "Indique l'hébergeur et le directeur de la publication.", "Amende : jusqu'à 75 000 € (personne morale)"],
  ["FR", "ko", "Médiateur de la consommation", /m[ée]diateur/i, "Code de la consommation L612-1", "Indique le médiateur compétent.", "Amende DGCCRF : jusqu'à 75 000 € (personne morale)"],
  ["FR", "warn", "Bouton « Tout refuser » (cookies)", /tout\s+refuser|continuer\s+sans\s+accepter/i, "CNIL délibération 2020-091", "Refuser doit être aussi simple qu'accepter.", "CNIL : jusqu'à 20 M€ ou 4 % du CA (ex: Amazon 746 M€ en 2021)"],
  ["NL", "ko", "Inschrijving KvK", /\bKvK\b|Kamer\s+van\s+Koophandel/i, "Handelsregisterwet", "Affiche le numéro KvK.", "Amende ACM : jusqu'à 900 000 €"],
  ["NL", "ko", "BTW-nummer", /\bNL\s?\d{9}\s?B\s?\d{2}\b/i, "Burgerlijk Wetboek, boek 3", "Affiche le BTW-nummer.", "Amende Belastingdienst : variable selon infraction"],
  ["NL", "warn", "Cookies : option de refus", /weiger|alles\s+weigeren|alleen\s+noodzakelijke/i, "Telecommunicatiewet art. 11.7a", "Propose de refuser les cookies non essentiels.", "AP : jusqu'à 20 M€ ou 4 % du CA mondial"]
];

const TR = [["Google Analytics/GTM",/googletagmanager|google-analytics|gtag/i],["Meta Pixel",/fbq\(|connect\.facebook\.net/i],["Hotjar",/hotjar/i],["TikTok Pixel",/analytics\.tiktok/i]];

export default {
  async fetch(req, env) {
    const o = req.headers.get("Origin") || "";
    const cors = {"Access-Control-Allow-Origin": ALLOW.includes(o) ? o : ALLOW[0],"Access-Control-Allow-Methods": "POST,OPTIONS","Access-Control-Allow-Headers": "Content-Type"};
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    if (req.method !== "POST") return new Response("POST uniquement", { status: 405, headers: cors });
    let url;
    try { url = new URL((await req.json()).url.trim().replace(/^(?!https?:)/, "https://")); } catch { return new Response("URL invalide", { status: 400, headers: cors }); }
    const h = url.hostname;
    if (!/^https?:$/.test(url.protocol) || !h.includes(".") || /^[\d.:[]/.test(h) || /(localhost|\.local|\.internal)$/.test(h)) return new Response("URL refusée", { status: 400, headers: cors });
    const { readable, writable } = new TransformStream(), w = writable.getWriter(), enc = new TextEncoder();
    const send = x => w.write(enc.encode(JSON.stringify(x) + "\n"));
    (async () => { try { await scan(url, send, env); } catch (e) { await send({ type: "error", msg: "Site injoignable ou analyse impossible." }); } await w.close(); })();
    return new Response(readable, { headers: { ...cors, "Content-Type": "application/x-ndjson" } });
  }
};

async function get(u) {
  const t = Date.now();
  const r = await fetch(u, { redirect: "follow", headers: { "User-Agent": "ConformShopBot/1.0 (+https://jcode.store)" }, signal: AbortSignal.timeout(9000) });
  return { r, h: (await r.text()).slice(0, 400000), ms: Date.now() - t };
}

async function scan(url, send, env) {
  await send({ type: "step", msg: "Chargement de la page d'accueil" });
  const home = await get(url.href), base = home.r.url, hdr = home.r.headers, bh = new URL(base).host;
  const cookies = (hdr.getSetCookie ? hdr.getSetCookie() : []).map(c => c.split("=")[0].slice(0, 40));
  const perf = { ms: home.ms, kb: Math.round(home.h.length / 1024), scripts: (home.h.match(/<script/gi) || []).length,
    hosts: new Set([...home.h.matchAll(/(?:src|href)=["']https?:\/\/([^/"']+)/gi)].map(m => m[1]).filter(x => x !== bh)).size,
    sec: ["strict-transport-security", "content-security-policy", "x-content-type-options", "referrer-policy"].filter(k => hdr.has(k)).length };
  const links = [...new Set([...home.h.matchAll(/href=["']([^"'#]+)["']/gi)].map(m => { try { return new URL(m[1], base).href; } catch { return null; } })
    .filter(x => x && new URL(x).host === bh && /mention|legal|cgv|condition|terms|voorwaarden|privacy|confidential|cookie|retract|herroep|impressum|accessib|toegankelijk/i.test(x)))].slice(0, 6);
  let text = home.h;
  for (const l of links) { await send({ type: "step", msg: "Lecture de " + new URL(l).pathname }); try { text += "\n" + (await get(l)).h; } catch {} }
  await send({ type: "step", msg: "Analyse de conformité" });
  const det = ["EU"];
  if (/\.be$/.test(bh) || /\bBE\s?0\d{3}/.test(text)) det.push("BE");
  if (/\.fr$/.test(bh) || /\bSIRET|SIREN\b/.test(text)) det.push("FR");
  if (/\.nl$/.test(bh) || /\bKvK\b/i.test(text)) det.push("NL");
  if (det.length === 1) det.push("BE", "FR", "NL");
  const items = R.filter(r => det.includes(r[0])).map(r => ({ s: r[0], st: r[3].test(text) ? "ok" : r[1], t: r[2], law: r[4], tip: r[5], sanction: r[6] }));
  const tr = TR.filter(t => t[1].test(home.h)).map(t => t[0]), seen = [...tr, ...cookies];
  items.push({ s: "EU", st: !seen.length ? "ok" : CMP.test(text) ? "warn" : "ko", t: seen.length ? "Traceurs ou cookies dès le chargement : " + seen.join(", ") : "Aucun traceur ni cookie avant consentement", law: "Directive ePrivacy art. 5(3)", tip: "Bloque tout traceur non essentiel jusqu'au consentement.", sanction: "CNIL/APD : jusqu'à 20 M€ ou 4 % du CA (ex: Google 150 M€ en 2022)" });
  items.push({ s: "EU", st: base.startsWith("https") ? "ok" : "ko", t: "Connexion sécurisée HTTPS", law: "RGPD art. 32", tip: "Active HTTPS sur tout le site.", sanction: "RGPD : jusqu'à 20 M€ ou 4 % du CA mondial" });
  const pts = { ok: 1, warn: .5, ko: 0 }, pc = a => a.length ? Math.round(a.reduce((s, i) => s + pts[i.st], 0) / a.length * 100) : 0;
  const by = {}; det.forEach(c => by[c] = pc(items.filter(i => i.s === c)));
  await send({ type: "result", url: base, det, score: pc(items), by, items, perf });
  if (env.ANTHROPIC_API_KEY) {
    await send({ type: "step", msg: "Recommandations IA" });
    const bad = items.filter(i => i.st !== "ok").map(i => `${i.st}: ${i.t} (${i.law})`).join("\n") || "Aucun écart détecté";
    const r = await fetch("https://api.anthropic.com/v1/messages", { method: "POST", headers: { "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
      body: JSON.stringify({ model: env.MODEL || MODEL, max_tokens: 900, messages: [{ role: "user", content: `Tu es consultant conformité e-commerce (UE, BE, FR, NL). Site : ${base}\nPoints à traiter :\n${bad}\nDonne 4 recommandations priorisées par risque, JSON strict : [{"titre":"","pourquoi":"","action":"","effort":"faible|moyen|élevé"}]. Français, concret, sans promettre d'éviter une amende.` }] }) });
    let recs = []; try { recs = JSON.parse((await r.json()).content[0].text.match(/\[[\s\S]*\]/)[0]); } catch {}
    await send({ type: "ai", recs });
  }
}
