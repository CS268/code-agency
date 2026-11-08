// server/test/payments.states.test.mjs
// Tests de caractérisation : ils figent le comportement ACTUEL de server/payments.js.
// Ils ne changent aucun code. Lancer, depuis le dossier server/ : node --test test/payments.states.test.mjs
// Voir STATE_MACHINES.md, section 1, pour le tableau des états et des transitions.
import { test, mock, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { createPayments } from '../payments.js';

beforeEach(() => {
  mock.method(console, 'log', () => {});
  mock.method(console, 'error', () => {});
});
afterEach(() => mock.restoreAll());

// --- Faux éléments ---------------------------------------------------------

function fakeRes() {
  return {
    statusCode: 200,
    body: null,
    status(code) { this.statusCode = code; return this; },
    json(body) { this.body = body; return this; },
    send(body) { this.body = body; return this; },
  };
}

function fakeStripe({ captureFails = false } = {}) {
  const calls = { cancel: [], capture: [], sessions: 0 };
  return {
    calls,
    checkout: { sessions: { create: async () => { calls.sessions++; return { id: 'cs_1', url: 'https://pay.test/cs_1' }; } } },
    paymentIntents: {
      cancel: async (id) => { calls.cancel.push(id); },
      capture: async (id) => {
        calls.capture.push(id);
        if (captureFails) throw new Error('capture refused');
      },
    },
    webhooks: { constructEvent: () => { throw new Error('bad signature'); } },
  };
}

// Réponses de fetch jouées dans l'ordre ; la dernière est répétée si besoin.
function fakeFetch(responses) {
  const calls = [];
  const fn = async (url, options) => {
    calls.push({ url, options });
    const r = responses[Math.min(calls.length - 1, responses.length - 1)];
    if (r instanceof Error) throw r;
    return {
      ok: r.ok !== false,
      status: r.status || 200,
      text: async () => r.text || '',
      json: async () => r.json || {},
    };
  };
  fn.calls = calls;
  return fn;
}

const fakeSharp = async () => {
  const chain = {
    metadata: async () => ({ width: 1000, height: 1000 }),
    extract() { return chain; },
    png() { return chain; },
    toBuffer: async () => Buffer.from('x'),
  };
  return () => chain;
};

function setup({ fetchResponses = [{ json: { video_id: 'vid_1' } }], captureFails = false } = {}) {
  const stripe = fakeStripe({ captureFails });
  const fetchFn = fakeFetch(fetchResponses);
  const payments = createPayments({
    stripeSecretKey: 'sk_test',
    webhookSecret: 'whsec_test',
    agnesApiKey: 'agnes_key',
    agnesBaseUrl: 'https://agnes.test/v1',
    publicBaseUrl: 'https://site.test',
    fetchFn,
    stripe,
    sharpLoader: fakeSharp,
    submitRetryMs: 0,
  });
  return { payments, stripe, fetchFn, orders: payments._internals.orders };
}

async function createOrder(payments, overrides = {}) {
  const res = fakeRes();
  await payments.createOrderHandler(
    {
      files: [{ path: '/tmp/does-not-exist.png', mimetype: 'image/png', size: 1000, originalname: 'a.png' }],
      body: { mode: 'reference-images', prompt: 'a nice product video prompt', lang: 'en', ...overrides },
    },
    res
  );
  return res;
}

function publicStatus(payments, orderId) {
  const res = fakeRes();
  payments.getOrderHandler({ params: { id: orderId } }, res);
  return res;
}

const authorized = (orderId, amount = 150) => ({
  id: 'pi_1',
  metadata: { orderId },
  amount_capturable: amount,
  currency: 'eur',
});

const MINUTE = 60 * 1000;
const HOUR = 60 * MINUTE;

// --- Création ----------------------------------------------------------------

test('création valide : commande awaiting_payment, non capturée', async () => {
  const { payments, orders } = setup();
  const res = await createOrder(payments);
  assert.equal(res.statusCode, 200);
  assert.equal(res.body.checkoutUrl, 'https://pay.test/cs_1');
  const order = orders.get(res.body.orderId);
  assert.equal(order.status, 'awaiting_payment');
  assert.equal(order.captured, false);
  assert.equal(order.priceCents, 150);
  assert.equal(publicStatus(payments, res.body.orderId).body.status, 'awaiting_payment');
});

test('création invalide : erreur 400, aucune commande, Stripe non appelé', async () => {
  const { payments, stripe, orders } = setup();
  const res = await createOrder(payments, { prompt: 'court' });
  assert.equal(res.statusCode, 400);
  assert.equal(res.body.error, 'order_invalid');
  assert.equal(orders.size, 0);
  assert.equal(stripe.calls.sessions, 0);
});

test('commande inconnue : 404 order_not_found', () => {
  const { payments } = setup();
  const res = publicStatus(payments, 'nope');
  assert.equal(res.statusCode, 404);
  assert.equal(res.body.error, 'order_not_found');
});

test('une nouvelle instance ne connaît aucune commande (stockage en mémoire seulement)', async () => {
  const first = setup();
  const created = await createOrder(first.payments);
  const second = setup();
  assert.equal(publicStatus(second.payments, created.body.orderId).statusCode, 404);
});

// --- Autorisation de la carte -------------------------------------------------

test('autorisation correcte : awaiting_payment -> submitting -> generating', async () => {
  const { payments, orders, fetchFn } = setup();
  const { body } = await createOrder(payments);
  await payments._internals.handleAuthorized(authorized(body.orderId));
  const order = orders.get(body.orderId);
  assert.equal(order.status, 'generating');
  assert.equal(order.videoId, 'vid_1');
  assert.deepEqual(order.files, []);
  assert.equal(fetchFn.calls.length, 1);
  const shown = publicStatus(payments, body.orderId).body;
  assert.equal(shown.status, 'processing');
  assert.equal(shown.progress, 0);
});

test('montant incorrect : failed (amount_mismatch) et autorisation annulée', async () => {
  const { payments, orders, stripe } = setup();
  const { body } = await createOrder(payments);
  await payments._internals.handleAuthorized(authorized(body.orderId, 999));
  assert.equal(orders.get(body.orderId).status, 'failed');
  assert.equal(orders.get(body.orderId).error, 'amount_mismatch');
  assert.deepEqual(stripe.calls.cancel, ['pi_1']);
  const shown = publicStatus(payments, body.orderId).body;
  assert.equal(shown.status, 'failed');
  assert.equal(shown.error, 'amount_mismatch');
});

test('autorisation en double : ignorée, Agnes appelé une seule fois', async () => {
  const { payments, fetchFn } = setup();
  const { body } = await createOrder(payments);
  await payments._internals.handleAuthorized(authorized(body.orderId));
  await payments._internals.handleAuthorized(authorized(body.orderId));
  assert.equal(fetchFn.calls.length, 1);
});

test('autorisation pour une commande inconnue : autorisation annulée', async () => {
  const { payments, stripe, orders } = setup();
  await payments._internals.handleAuthorized(authorized('inconnue'));
  assert.deepEqual(stripe.calls.cancel, ['pi_1']);
  assert.equal(orders.size, 0);
});

test('autorisation sans orderId : rien ne se passe', async () => {
  const { payments, stripe, fetchFn } = setup();
  await payments._internals.handleAuthorized({ id: 'pi_x', metadata: {}, amount_capturable: 150, currency: 'eur' });
  assert.deepEqual(stripe.calls.cancel, []);
  assert.equal(fetchFn.calls.length, 0);
});

test('autorisation tardive sur commande expirée : annulée, état reste expired', async () => {
  const { payments, orders, stripe } = setup();
  const { body } = await createOrder(payments);
  orders.get(body.orderId).createdAt = Date.now() - 2 * HOUR;
  await payments._internals.tick();
  assert.equal(orders.get(body.orderId).status, 'expired');
  await payments._internals.handleAuthorized(authorized(body.orderId));
  assert.equal(orders.get(body.orderId).status, 'expired');
  assert.deepEqual(stripe.calls.cancel, ['pi_1']);
});

test('signature webhook invalide : 400', () => {
  const { payments } = setup();
  const res = fakeRes();
  payments.webhookHandler({ body: '{}', headers: { 'stripe-signature': 'x' } }, res);
  assert.equal(res.statusCode, 400);
});

// --- Expiration ---------------------------------------------------------------

test('non payée depuis plus d\'1 h : expired', async () => {
  const { payments, orders } = setup();
  const { body } = await createOrder(payments);
  orders.get(body.orderId).createdAt = Date.now() - 61 * MINUTE;
  await payments._internals.tick();
  assert.equal(orders.get(body.orderId).status, 'expired');
  assert.equal(publicStatus(payments, body.orderId).body.status, 'expired');
});

test('non payée depuis moins d\'1 h : reste awaiting_payment', async () => {
  const { payments, orders } = setup();
  const { body } = await createOrder(payments);
  orders.get(body.orderId).createdAt = Date.now() - 59 * MINUTE;
  await payments._internals.tick();
  assert.equal(orders.get(body.orderId).status, 'awaiting_payment');
});

// --- Envoi à Agnes ------------------------------------------------------------

test('file pleine : 6 essais puis failed (queue_full), autorisation annulée', async () => {
  const { payments, orders, fetchFn, stripe } = setup({
    fetchResponses: [{ ok: false, status: 429, text: 'video_queue_full' }],
  });
  const { body } = await createOrder(payments);
  await payments._internals.handleAuthorized(authorized(body.orderId));
  assert.equal(fetchFn.calls.length, 6);
  assert.equal(orders.get(body.orderId).status, 'failed');
  assert.equal(orders.get(body.orderId).error, 'queue_full');
  assert.deepEqual(stripe.calls.cancel, ['pi_1']);
});

test('erreur Agnes autre que file pleine : un seul essai, failed (agnes_error)', async () => {
  const { payments, orders, fetchFn } = setup({
    fetchResponses: [{ ok: false, status: 500, text: 'boom' }],
  });
  const { body } = await createOrder(payments);
  await payments._internals.handleAuthorized(authorized(body.orderId));
  assert.equal(fetchFn.calls.length, 1);
  assert.equal(orders.get(body.orderId).error, 'agnes_error');
});

// --- Génération ---------------------------------------------------------------

async function generatingOrder(fetchResponses, options = {}) {
  const ctx = setup({ fetchResponses, ...options });
  const { body } = await createOrder(ctx.payments);
  await ctx.payments._internals.handleAuthorized(authorized(body.orderId));
  return { ...ctx, orderId: body.orderId, order: ctx.orders.get(body.orderId) };
}

test('génération terminée : completed, capture faite, statut public completed', async () => {
  const { payments, order, orderId, stripe } = await generatingOrder([
    { json: { video_id: 'vid_1' } },
    { json: { status: 'completed', url: 'https://video.test/v.mp4' } },
  ]);
  await payments._internals.tick();
  assert.equal(order.status, 'completed');
  assert.equal(order.captured, true);
  assert.deepEqual(stripe.calls.capture, ['pi_1']);
  const shown = publicStatus(payments, orderId).body;
  assert.equal(shown.status, 'completed');
  assert.equal(shown.progress, 100);
  assert.equal(shown.videoUrl, 'https://video.test/v.mp4');
});

test('génération en cours : la progression est recopiée', async () => {
  const { payments, order, orderId } = await generatingOrder([
    { json: { video_id: 'vid_1' } },
    { json: { status: 'processing', progress: 42 } },
  ]);
  await payments._internals.tick();
  assert.equal(order.status, 'generating');
  assert.equal(publicStatus(payments, orderId).body.progress, 42);
});

test('progression publique plafonnée à 99 tant que la commande n\'est pas terminée', async () => {
  const { payments, order, orderId } = await generatingOrder([
    { json: { video_id: 'vid_1' } },
    { json: { status: 'processing', progress: 100 } },
  ]);
  await payments._internals.tick();
  assert.equal(order.progress, 100);
  assert.equal(publicStatus(payments, orderId).body.progress, 99);
});

test('Agnes répond failed : failed (generation_failed), autorisation annulée', async () => {
  const { payments, order, stripe } = await generatingOrder([
    { json: { video_id: 'vid_1' } },
    { json: { status: 'failed' } },
  ]);
  await payments._internals.tick();
  assert.equal(order.status, 'failed');
  assert.equal(order.error, 'generation_failed');
  assert.deepEqual(stripe.calls.cancel, ['pi_1']);
});

test('Agnes répond completed sans URL : failed (no_video_url)', async () => {
  const { payments, order } = await generatingOrder([
    { json: { video_id: 'vid_1' } },
    { json: { status: 'completed' } },
  ]);
  await payments._internals.tick();
  assert.equal(order.status, 'failed');
  assert.equal(order.error, 'no_video_url');
});

test('plus de 20 min de génération : failed (timeout) sans interroger Agnes', async () => {
  const { payments, order, fetchFn } = await generatingOrder([{ json: { video_id: 'vid_1' } }]);
  order.generatingSince = Date.now() - 21 * MINUTE;
  const callsBefore = fetchFn.calls.length;
  await payments._internals.tick();
  assert.equal(order.status, 'failed');
  assert.equal(order.error, 'timeout');
  assert.equal(fetchFn.calls.length, callsBefore);
});

test('erreur réseau pendant le suivi : l\'état ne change pas', async () => {
  const { payments, order } = await generatingOrder([
    { json: { video_id: 'vid_1' } },
    new Error('network down'),
  ]);
  await payments._internals.tick();
  assert.equal(order.status, 'generating');
});

// --- Capture du paiement --------------------------------------------------------

test('capture qui échoue : completed non capturé reste visible comme processing, sans videoUrl', async () => {
  const { payments, order, orderId } = await generatingOrder(
    [
      { json: { video_id: 'vid_1' } },
      { json: { status: 'completed', url: 'https://video.test/v.mp4' } },
    ],
    { captureFails: true }
  );
  await payments._internals.tick();
  assert.equal(order.status, 'completed');
  assert.equal(order.captured, false);
  const shown = publicStatus(payments, orderId).body;
  assert.equal(shown.status, 'processing');
  assert.equal(shown.videoUrl, undefined);
});

test('20 échecs de capture : failed (payment_capture_failed)', async () => {
  const { payments, order, orderId, stripe } = await generatingOrder(
    [
      { json: { video_id: 'vid_1' } },
      { json: { status: 'completed', url: 'https://video.test/v.mp4' } },
    ],
    { captureFails: true }
  );
  for (let i = 0; i < 25 && order.status !== 'failed'; i++) {
    await payments._internals.tick();
  }
  assert.equal(order.status, 'failed');
  assert.equal(order.error, 'payment_capture_failed');
  assert.equal(order.captureAttempts, 20);
  assert.equal(stripe.calls.capture.length, 20);
  assert.equal(order.videoUrl, undefined);
  const shown = publicStatus(payments, orderId).body;
  assert.equal(shown.status, 'failed');
  assert.equal(shown.error, 'payment_capture_failed');
});

// --- Nettoyage et trous connus -----------------------------------------------------

test('completed, failed et expired sont supprimés après 24 h', async () => {
  const { payments, orders } = setup();
  const old = Date.now() - 25 * HOUR;
  orders.set('a', { id: 'a', status: 'completed', captured: true, createdAt: old, captureAttempts: 1, files: [] });
  orders.set('b', { id: 'b', status: 'failed', createdAt: old, files: [] });
  orders.set('c', { id: 'c', status: 'expired', createdAt: old, files: [] });
  await payments._internals.tick();
  assert.equal(orders.size, 0);
});

test('TROU CONNU : une commande submitting n\'est jamais traitée ni supprimée par tick', async () => {
  const { payments, orders } = setup();
  orders.set('s', { id: 's', status: 'submitting', createdAt: Date.now() - 25 * HOUR, files: [] });
  await payments._internals.tick();
  assert.equal(orders.get('s').status, 'submitting');
});

test('le client voit submitting comme processing', () => {
  const { payments, orders } = setup();
  orders.set('s', { id: 's', mode: 'mix', status: 'submitting', createdAt: Date.now(), progress: 0, files: [] });
  assert.equal(publicStatus(payments, 's').body.status, 'processing');
});
