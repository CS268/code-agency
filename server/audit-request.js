import { sendAuditRequest } from './mailer.js';

const WINDOW_MS = 60 * 60 * 1000; // une heure
const MAX_PER_IP = 3;
const MAX_TOTAL = 30;
const hits = new Map();
let total = [];

function clientIp(req) {
  const xf = String(req.get('x-forwarded-for') || '').split(',').map((s) => s.trim()).filter(Boolean);
  return xf[xf.length - 1] || (req.socket && req.socket.remoteAddress) || 'inconnu';
}

function allow(ip) {
  const now = Date.now();
  total = total.filter((t) => now - t < WINDOW_MS);
  if (hits.size > 5000) hits.clear();
  const arr = (hits.get(ip) || []).filter((t) => now - t < WINDOW_MS);
  if (arr.length >= MAX_PER_IP || total.length >= MAX_TOTAL) {
    hits.set(ip, arr);
    return false;
  }
  arr.push(now);
  total.push(now);
  hits.set(ip, arr);
  return true;
}

const clean = (s, n) => String(s == null ? '' : s).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '').slice(0, n);

export function registerAuditRequest(app) {
  app.post('/api/audit-request', async (req, res) => {
    const b = req.body || {};
    if (b.website) return res.json({ ok: true }); // champ piege : seuls les robots le remplissent
    const email = clean(b.email, 200).trim();
    const site = clean(b.site, 300).trim();
    const analysis = clean(b.analysis, 20000);
    const lang = ['fr', 'nl', 'en'].includes(b.lang) ? b.lang : 'fr';
    if (!/^[^\s@<>"]+@[^\s@<>"]+\.[^\s@<>"]+$/.test(email)) return res.status(400).json({ error: 'email_invalid' });
    if (!/^https?:\/\/\S{3,290}$/i.test(site) && !/^[a-z0-9.-]+\.[a-z]{2,}(\/\S*)?$/i.test(site)) return res.status(400).json({ error: 'site_invalid' });
    if (b.consent !== true) return res.status(400).json({ error: 'consent_required' });
    if (!allow(clientIp(req))) return res.status(429).json({ error: 'rate_limited' });
    try {
      await sendAuditRequest({ email, site, analysis, lang });
      return res.json({ ok: true });
    } catch (err) {
      console.error('[AUDIT] envoi echoue:', err && err.message);
      return res.status(500).json({ error: 'send_failed' });
    }
  });
}
