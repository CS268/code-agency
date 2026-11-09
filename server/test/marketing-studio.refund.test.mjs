// server/test/marketing-studio.refund.test.mjs
// Tests du remboursement du quota du Studio Marketing (server/marketing-studio.js).
// Supabase et Agnes sont simulés : aucun accès réseau.
// Lancer, depuis le dossier server/ : node --test test/marketing-studio.refund.test.mjs
// Voir STATE_MACHINES.md, section 2.
import { test, mock, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';

process.env.SUPABASE_URL = 'https://example.supabase.co';
process.env.SUPABASE_SERVICE_KEY = 'service-key';
process.env.AGNES_API_KEY = 'agnes-key';
const { supabase } = await import('../supabase.js');

// --- Faux Supabase : tables en mémoire, seulement les appels utilisés par le module ---------

class Query {
  constructor(tables, name) {
    this.rows = tables[name];
    this.filters = [];
    this.op = 'select';
    this.patch = null;
    this.wantRows = false;
    this.one = null;
  }
  select() { if (this.op === 'update') this.wantRows = true; return this; }
  update(patch) { this.op = 'update'; this.patch = patch; return this; }
  insert(row) { this.op = 'insert'; this.patch = row; return this; }
  eq(col, val) { this.filters.push((r) => r[col] === val); return this; }
  is(col, val) { this.filters.push((r) => (val === null ? r[col] == null : r[col] === val)); return this; }
  order() { return this; }
  limit() { return this; }
  single() { this.one = 'single'; return this; }
  maybeSingle() { this.one = 'maybe'; return this; }
  then(resolve, reject) { return Promise.resolve(this.run()).then(resolve, reject); }
  run() {
    if (this.op === 'insert') { this.rows.push({ statut: this.defaultStatut, ...this.patch }); return { data: null, error: null }; }
    const matched = this.rows.filter((r) => this.filters.every((f) => f(r)));
    if (this.op === 'update') {
      matched.forEach((r) => Object.assign(r, this.patch));
      return { data: this.wantRows ? matched.map((r) => ({ ...r })) : null, error: null };
    }
    if (this.one === 'single') return matched[0] ? { data: { ...matched[0] }, error: null } : { data: null, error: { message: 'no row' } };
    if (this.one === 'maybe') {
      if (matched.length > 1) return { data: null, error: { message: 'multiple rows' } };
      return { data: matched[0] ? { ...matched[0] } : null, error: null };
    }
    return { data: matched.map((r) => ({ ...r })), error: null };
  }
}

let tables;
let defaultStatut;
let agnesStatus;
let instance = 0;

const FUTURE = new Date(Date.now() + 24 * 3600 * 1000).toISOString();

function resetData() {
  tables = {
    abonnes_marketing: [
      { id: 'sub1', palier: 'pro', quota_mensuel: 10, videos_utilisees: 3, statut: 'actif', magic_token: 'tok1', magic_token_expires_at: FUTURE },
      { id: 'sub2', palier: 'pro', quota_mensuel: 10, videos_utilisees: 5, statut: 'actif', magic_token: 'tok2', magic_token_expires_at: FUTURE },
    ],
    marketing_videos: [],
  };
}

beforeEach(() => {
  resetData();
  defaultStatut = 'en_cours';
  agnesStatus = { status: 'processing', progress: 10 };
  mock.method(console, 'log', () => {});
  mock.method(console, 'error', () => {});
  mock.method(supabase, 'from', (name) => {
    const q = new Query(tables, name);
    q.defaultStatut = defaultStatut;
    return q;
  });
  mock.method(globalThis, 'fetch', async (url) => {
    const u = String(url);
    if (u.endsWith('/videos')) return { ok: true, status: 200, text: async () => '', json: async () => ({ video_id: 'vidA' }) };
    return { ok: true, status: 200, text: async () => '', json: async () => agnesStatus };
  });
});
afterEach(() => mock.restoreAll());

// --- Faux serveur Express : chaque "instance" est une copie neuve du module (jobs vide) ----

async function startServer() {
  instance++;
  const { registerMarketingStudio } = await import(`../marketing-studio.js?instance=${instance}`);
  const routes = {};
  registerMarketingStudio({
    get: (path, ...h) => { routes[`GET ${path}`] = h.at(-1); },
    post: (path, ...h) => { routes[`POST ${path}`] = h.at(-1); },
  });
  const call = async (route, { token = 'tok1', query = {}, body = {} } = {}) => {
    const res = { statusCode: 200, body: null, status(c) { this.statusCode = c; return this; }, json(b) { this.body = b; return this; } };
    await routes[route]({ get: (n) => (n.toLowerCase() === 'x-marketing-token' ? token : undefined), query, body }, res);
    return res;
  };
  return {
    generate: (opts) => call('POST /api/marketing/generate', {
      ...opts,
      body: { prompt: 'pub', image: 'data:image/png;base64,AAAA', frame_rate: 24, num_frames: 120, width: 720, height: 1280 },
    }),
    status: (videoId = 'vidA', opts = {}) => call('GET /api/marketing/status', { ...opts, query: { video_id: videoId } }),
  };
}

const used = (id) => tables.abonnes_marketing.find((s) => s.id === id).videos_utilisees;
const video = () => tables.marketing_videos.find((v) => v.agnes_video_id === 'vidA');

// --- Comportement sans redémarrage (existant, à ne pas casser) ---------------------------------

test('génération : le quota est réservé et la vidéo enregistrée', async () => {
  const server = await startServer();
  const res = await server.generate();
  assert.equal(res.body.videoId, 'vidA');
  assert.equal(used('sub1'), 4);
  assert.equal(video().abonne_id, 'sub1');
});

test('quota épuisé : 403 quota_exhausted, rien n\'est réservé', async () => {
  tables.abonnes_marketing[0].videos_utilisees = 10;
  const server = await startServer();
  const res = await server.generate();
  assert.equal(res.statusCode, 403);
  assert.equal(res.body.error, 'quota_exhausted');
  assert.equal(used('sub1'), 10);
});

test('échec Agnes sans redémarrage : quota rendu une seule fois, statut echec', async () => {
  const server = await startServer();
  await server.generate();
  agnesStatus = { status: 'failed' };
  assert.equal((await server.status()).body.status, 'failed');
  assert.equal((await server.status()).body.status, 'failed');
  assert.equal(used('sub1'), 3);
  assert.equal(video().statut, 'echec');
});

test('vidéo terminée : statut termine avec l\'adresse, aucun remboursement', async () => {
  const server = await startServer();
  await server.generate();
  agnesStatus = { status: 'completed', url: 'https://video.test/a.mp4' };
  const res = await server.status();
  assert.equal(res.body.status, 'completed');
  assert.equal(video().statut, 'termine');
  assert.equal(video().video_url, 'https://video.test/a.mp4');
  assert.equal(used('sub1'), 4);
});

// --- Après un redémarrage du serveur (la mémoire des jobs est vide) --------------------------------

test('après redémarrage : un échec Agnes rend le quota et passe le statut à echec', async () => {
  const before = await startServer();
  await before.generate();
  const after = await startServer();
  agnesStatus = { status: 'failed' };
  const res = await after.status();
  assert.equal(res.body.status, 'failed');
  assert.equal(used('sub1'), 3);
  assert.equal(video().statut, 'echec');
});

test('après redémarrage : plusieurs interrogations ne remboursent qu\'une seule fois', async () => {
  const before = await startServer();
  await before.generate();
  const after = await startServer();
  agnesStatus = { status: 'failed' };
  await after.status();
  await after.status();
  await Promise.all([after.status(), after.status()]);
  assert.equal(used('sub1'), 3);
});

test('après redémarrage : "terminé sans adresse" rend aussi le quota', async () => {
  const before = await startServer();
  await before.generate();
  const after = await startServer();
  agnesStatus = { status: 'completed' };
  const res = await after.status();
  assert.equal(res.body.error, 'no_url');
  assert.equal(used('sub1'), 3);
});

test('après redémarrage : une valeur de départ vide (null) dans statut est gérée', async () => {
  defaultStatut = null;
  const before = await startServer();
  await before.generate();
  assert.equal(video().statut, null);
  const after = await startServer();
  agnesStatus = { status: 'failed' };
  await after.status();
  assert.equal(used('sub1'), 3);
  assert.equal(video().statut, 'echec');
});

test('après redémarrage : une vidéo déjà terminée n\'est jamais remboursée', async () => {
  const before = await startServer();
  await before.generate();
  agnesStatus = { status: 'completed', url: 'https://video.test/a.mp4' };
  await before.status();
  const after = await startServer();
  agnesStatus = { status: 'failed' };
  await after.status();
  assert.equal(video().statut, 'termine');
  assert.equal(used('sub1'), 4);
});

test('après redémarrage : un autre abonné ne peut déclencher aucun remboursement', async () => {
  const before = await startServer();
  await before.generate();
  const after = await startServer();
  agnesStatus = { status: 'failed' };
  await after.status('vidA', { token: 'tok2' });
  assert.equal(used('sub1'), 4);
  assert.equal(used('sub2'), 5);
  assert.equal(video().statut, 'en_cours');
});

test('après redémarrage : vidéo inconnue de la base, aucun remboursement et pas d\'erreur', async () => {
  const server = await startServer();
  agnesStatus = { status: 'failed' };
  const res = await server.status('vidInconnue');
  assert.equal(res.body.status, 'failed');
  assert.equal(used('sub1'), 3);
});

test('après redémarrage : statut Agnes encore en cours, rien ne change', async () => {
  const before = await startServer();
  await before.generate();
  const after = await startServer();
  const res = await after.status();
  assert.equal(res.body.status, 'processing');
  assert.equal(used('sub1'), 4);
  assert.equal(video().statut, 'en_cours');
});
