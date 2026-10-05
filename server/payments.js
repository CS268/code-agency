// server/payments.js — paiement Stripe (Checkout, capture différée) pour VIDEOCREATOR.
// Actif seulement si STRIPE_SECRET_KEY et STRIPE_WEBHOOK_SECRET existent (voir server.js).
// Déroulement : l'interface envoie fichiers + prompt -> commande en attente + session Checkout (autorisation sans capture)
// -> webhook "autorisé" -> appel Agnes -> suivi côté serveur -> capture du paiement si la vidéo est prête,
// annulation de l'autorisation sinon (le client n'est alors pas débité).
import Stripe from 'stripe';
import { randomUUID } from 'crypto';
import { unlinkSync, existsSync, readFileSync } from 'fs';

const IMAGE_FORMATS = ['image/jpeg', 'image/png', 'image/webp'];
const VIDEO_FORMATS = ['video/mp4', 'video/webm', 'video/quicktime'];
const MAX_IMAGE_SIZE = 15 * 1024 * 1024;
const MAX_VIDEO_SIZE = 50 * 1024 * 1024;
const MAX_TOTAL_SIZE = 50 * 1024 * 1024;
const MAX_IMAGES = 8;
const MIN_PROMPT = 10;
const MAX_PROMPT = 3000;

const MODEL = 'agnes-video-2.5'; // modèle payant uniquement, jamais le modèle gratuit
const VIDEO_SECONDS = 12;
const SIZE = '720P';
const ASPECT_RATIO = '9:16';

// Prix en centimes d'euro : montants finaux (aucune TVA prélevée). Un seul endroit à modifier.
export const OFFERS = {
  'reference-images': { cents: 150, label: { fr: 'Images de référence', en: 'Reference images', nl: 'Referentiebeelden' } },
  'reference-video': { cents: 200, label: { fr: 'Vidéo de référence', en: 'Reference video', nl: 'Referentievideo' } },
  mix: { cents: 250, label: { fr: 'Mix images + vidéo', en: 'Mix images + video', nl: 'Mix beelden + video' } },
};

const AWAITING_TTL_MS = 60 * 60 * 1000; // commande non payée : supprimée après 1 h
const GENERATION_TIMEOUT_MS = 20 * 60 * 1000;
const KEEP_MS = 24 * 60 * 60 * 1000;
const SUBMIT_MAX_ATTEMPTS = 6;
const SUBMIT_RETRY_MS = 20 * 1000;
const POLL_MS = 5 * 1000;
const CAPTURE_MAX_ATTEMPTS = 20;
const RATE_WINDOW_MS = 60 * 60 * 1000;
const RATE_MAX = 10;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const msg = (fr, en, nl) => ({ message_fr: fr, message_en: en, message_nl: nl });

const FAILURE_MESSAGES = {
  queue_full: msg(
    "La file d'attente de génération est pleine. Vous n'avez pas été débité, réessayez dans quelques minutes.",
    'The generation queue is full. You have not been charged, please try again in a few minutes.',
    'De wachtrij voor generatie is vol. U bent niet gedebiteerd, probeer het over een paar minuten opnieuw.'
  ),
  default: msg(
    "La génération a échoué. Vous n'avez pas été débité (un montant en attente sur votre carte sera libéré automatiquement).",
    'The generation failed. You have not been charged (any amount on hold on your card will be released automatically).',
    'De generatie is mislukt. U bent niet gedebiteerd (een bedrag in de wacht op uw kaart wordt automatisch vrijgegeven).'
  ),
  payment_capture_failed: msg(
    "Un problème est survenu lors de la finalisation du paiement. Contactez-nous en indiquant votre numéro de commande.",
    'A problem occurred while finalizing the payment. Please contact us with your order number.',
    'Er is een probleem opgetreden bij het afronden van de betaling. Neem contact met ons op met uw bestelnummer.'
  ),
};

function removeFiles(files) {
  for (const f of files || []) {
    try {
      if (f.path && existsSync(f.path)) unlinkSync(f.path);
    } catch (err) {
      console.error('Delete failed:', err?.message);
    }
  }
}

function validateOrder(mode, prompt, files) {
  if (!Object.prototype.hasOwnProperty.call(OFFERS, mode)) {
    return msg('Mode invalide', 'Invalid mode', 'Ongeldige modus');
  }
  if (typeof prompt !== 'string' || prompt.length < MIN_PROMPT || prompt.length > MAX_PROMPT) {
    return msg('Prompt invalide (10-3000 caractères)', 'Invalid prompt (10-3000 chars)', 'Ongeldige prompt (10-3000 tekens)');
  }
  const images = files.filter((f) => IMAGE_FORMATS.includes(f.mimetype));
  const videos = files.filter((f) => VIDEO_FORMATS.includes(f.mimetype));
  if (images.length + videos.length !== files.length) {
    return msg('Type de fichier non supporté', 'Unsupported file type', 'Bestandstype niet ondersteund');
  }
  const okCount =
    (mode === 'reference-images' && images.length >= 1 && images.length <= MAX_IMAGES && videos.length === 0) ||
    (mode === 'reference-video' && videos.length === 1 && images.length === 0) ||
    (mode === 'mix' && images.length >= 1 && images.length <= MAX_IMAGES && videos.length === 1);
  if (!okCount) {
    return msg('Fichiers non conformes au mode choisi', 'Files do not match the selected mode', 'Bestanden komen niet overeen met de gekozen modus');
  }
  if (images.some((f) => f.size > MAX_IMAGE_SIZE)) {
    return msg('Image trop lourde (max 15 Mo)', 'Image too large (max 15 MB)', 'Afbeelding te groot (max 15 MB)');
  }
  if (videos.some((f) => f.size > MAX_VIDEO_SIZE)) {
    return msg('Vidéo trop lourde (max 50 Mo)', 'Video too large (max 50 MB)', 'Video te groot (max 50 MB)');
  }
  if (files.reduce((sum, f) => sum + f.size, 0) > MAX_TOTAL_SIZE) {
    return msg('Taille totale trop élevée (max 50 Mo)', 'Total size too large (max 50 MB)', 'Totale grootte te groot (max 50 MB)');
  }
  return null;
}

export function createPayments({
  stripeSecretKey,
  webhookSecret,
  agnesApiKey,
  agnesBaseUrl,
  publicBaseUrl,
  fetchFn,
  stripe: stripeOverride,
  sharpLoader,
  submitRetryMs = SUBMIT_RETRY_MS,
}) {
  const stripe = stripeOverride || new Stripe(stripeSecretKey);
  const loadSharp = sharpLoader || (async () => (await import('sharp')).default);
  const orders = new Map();
  const ipHits = new Map();
  let tickRunning = false;

  // --- Limite de débit par IP (avant la réception des fichiers) ---
  function rateLimit(req, res, next) {
    const ip = req.ip || 'unknown';
    const now = Date.now();
    const rec = ipHits.get(ip);
    if (!rec || now - rec.first > RATE_WINDOW_MS) {
      ipHits.set(ip, { count: 1, first: now });
      return next();
    }
    if (rec.count >= RATE_MAX) {
      return res.status(429).json({ error: 'rate_limited', ...msg('Trop de tentatives, réessayez plus tard', 'Too many attempts, please try again later', 'Te veel pogingen, probeer het later opnieuw') });
    }
    rec.count++;
    next();
  }

  // --- Création de la commande + session de paiement ---
  async function createOrderHandler(req, res) {
    const files = (req.files || []).map((f) => ({ path: f.path, mimetype: f.mimetype, size: f.size, originalname: f.originalname }));
    const body = req.body || {};
    const mode = body.mode;
    const prompt = body.prompt;
    const problem = validateOrder(mode, prompt, files);
    if (problem) {
      removeFiles(files);
      return res.status(400).json({ error: 'order_invalid', ...problem });
    }
    const lang = ['fr', 'en', 'nl'].includes(body.lang) ? body.lang : 'fr';
    const offer = OFFERS[mode];
    const id = randomUUID();
    let session;
    try {
      session = await stripe.checkout.sessions.create({
        mode: 'payment',
        line_items: [
          {
            quantity: 1,
            price_data: {
              currency: 'eur',
              unit_amount: offer.cents,
              product_data: { name: `Vidéo TikTok 12 s - ${offer.label[lang]}` },
            },
          },
        ],
        payment_intent_data: { capture_method: 'manual', metadata: { orderId: id } },
        client_reference_id: id,
        metadata: { orderId: id },
        success_url: `${publicBaseUrl}/?order=${id}`,
        cancel_url: `${publicBaseUrl}/?cancelled=1`,
      });
    } catch (err) {
      console.error('Stripe session creation failed:', err?.message);
      removeFiles(files);
      return res.status(502).json({
        error: 'payment_unavailable',
        ...msg('Paiement momentanément indisponible, réessayez plus tard.', 'Payment temporarily unavailable, please try again later.', 'Betaling tijdelijk niet beschikbaar, probeer het later opnieuw.'),
      });
    }
    orders.set(id, {
      id,
      mode,
      prompt,
      lang,
      files,
      priceCents: offer.cents,
      status: 'awaiting_payment',
      createdAt: Date.now(),
      sessionId: session.id,
      consent: body.consent === 'true',
      captured: false,
      captureAttempts: 0,
      progress: 0,
    });
    return res.json({ orderId: id, checkoutUrl: session.url });
  }

  // --- Suivi d'une commande par l'interface ---
  function getOrderHandler(req, res) {
    const order = orders.get(req.params.id);
    if (!order) {
      return res.status(404).json({ error: 'order_not_found', ...msg('Commande introuvable', 'Order not found', 'Bestelling niet gevonden') });
    }
    let status = 'processing';
    if (order.status === 'awaiting_payment') status = 'awaiting_payment';
    else if (order.status === 'expired') status = 'expired';
    else if (order.status === 'failed') status = 'failed';
    else if (order.status === 'completed' && order.captured) status = 'completed';
    const payload = { orderId: order.id, status, progress: status === 'completed' ? 100 : Math.min(order.progress || 0, 99), mode: order.mode };
    if (status === 'completed') payload.videoUrl = order.videoUrl;
    if (status === 'failed') {
      Object.assign(payload, FAILURE_MESSAGES[order.error] || FAILURE_MESSAGES.default, { error: order.error });
    }
    return res.json(payload);
  }

  // --- Webhook Stripe ---
  function webhookHandler(req, res) {
    let event;
    try {
      event = stripe.webhooks.constructEvent(req.body, req.headers['stripe-signature'], webhookSecret);
    } catch (err) {
      console.error('Stripe webhook signature check failed');
      return res.status(400).send('invalid signature');
    }
    res.json({ received: true });
    if (event.type === 'payment_intent.amount_capturable_updated') {
      handleAuthorized(event.data.object).catch((err) => console.error('handleAuthorized error:', err?.message));
    }
  }

  async function safeCancel(paymentIntentId, reason) {
    if (!paymentIntentId) return;
    try {
      await stripe.paymentIntents.cancel(paymentIntentId);
      console.log('Authorization cancelled:', reason);
    } catch (err) {
      console.error('Authorization cancel failed:', err?.message);
    }
  }

  async function failOrder(order, code) {
    order.status = 'failed';
    order.error = code;
    removeFiles(order.files);
    order.files = [];
    console.log('Order failed:', order.id, code);
    await safeCancel(order.paymentIntentId, code);
  }

  async function handleAuthorized(pi) {
    const orderId = pi?.metadata?.orderId;
    if (!orderId) return; // paiement sans rapport avec VIDEOCREATOR : on n'y touche pas
    const order = orders.get(orderId);
    if (!order || order.status === 'expired') {
      await safeCancel(pi.id, 'unknown or expired order');
      return;
    }
    if (order.status !== 'awaiting_payment') return; // notification en double
    if (pi.amount_capturable !== order.priceCents || pi.currency !== 'eur') {
      order.paymentIntentId = pi.id;
      await failOrder(order, 'amount_mismatch');
      return;
    }
    order.paymentIntentId = pi.id;
    order.status = 'submitting';
    await submitWithRetries(order);
  }

  // --- Appel à Agnes ---
  async function buildAgnesRequest(order) {
    const sharp = await loadSharp();
    const uris = [];
    const kinds = [];
    for (const f of order.files) {
      if (IMAGE_FORMATS.includes(f.mimetype)) {
        const meta = await sharp(f.path).metadata();
        const w = meta.width || 1;
        const h = meta.height || 1;
        const ratio = w / h;
        let pipeline = sharp(f.path);
        if (ratio < 0.4) {
          const newH = Math.max(1, Math.round(w / 0.5));
          const top = Math.max(0, Math.floor((h - newH) / 2));
          pipeline = pipeline.extract({ left: 0, top, width: w, height: Math.min(newH, h) });
        } else if (ratio > 2.5) {
          const newW = Math.max(1, Math.round(h * 2.0));
          const left = Math.max(0, Math.floor((w - newW) / 2));
          pipeline = pipeline.extract({ left, top: 0, width: Math.min(newW, w), height: h });
        }
        const buf = await pipeline.png().toBuffer();
        uris.push(`data:image/png;base64,${buf.toString('base64')}`);
        kinds.push('image');
      } else {
        const buf = readFileSync(f.path);
        uris.push(`data:${f.mimetype};base64,${buf.toString('base64')}`);
        kinds.push('video');
      }
    }
    const images = uris.filter((_, i) => kinds[i] === 'image');
    const videos = uris.filter((_, i) => kinds[i] === 'video');
    const request = {
      model: MODEL,
      prompt: order.prompt,
      seconds: String(VIDEO_SECONDS),
      size: SIZE,
      aspect_ratio: ASPECT_RATIO,
      mode: 'reference',
    };
    if (images.length > 0) request.images = images;
    if (videos.length > 0) request.videos = videos.map((url) => ({ url, start_seconds: 0, require_audio: false }));
    return request;
  }

  async function callAgnes(payload) {
    try {
      const response = await fetchFn(`${agnesBaseUrl}/videos`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${agnesApiKey}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const text = await response.text();
        console.error('Agnes API error:', response.status, String(text).slice(0, 300));
        return { ok: false, queueFull: /video_queue_full/.test(text) };
      }
      const data = await response.json();
      if (!data || !data.video_id) return { ok: false, queueFull: false };
      return { ok: true, videoId: data.video_id };
    } catch (err) {
      console.error('Agnes API call failed:', err?.message);
      return { ok: false, queueFull: false };
    }
  }

  async function submitWithRetries(order) {
    let payload;
    try {
      payload = await buildAgnesRequest(order);
    } catch (err) {
      console.error('File processing failed:', err?.message);
      return failOrder(order, 'file_processing_failed');
    }
    for (let attempt = 1; attempt <= SUBMIT_MAX_ATTEMPTS; attempt++) {
      const result = await callAgnes(payload);
      if (result.ok) {
        order.videoId = result.videoId;
        order.status = 'generating';
        order.generatingSince = Date.now();
        order.progress = 0;
        removeFiles(order.files);
        order.files = [];
        console.log('Order submitted to Agnes:', order.id, order.mode);
        return;
      }
      if (result.queueFull && attempt < SUBMIT_MAX_ATTEMPTS) {
        await sleep(submitRetryMs);
        continue;
      }
      return failOrder(order, result.queueFull ? 'queue_full' : 'agnes_error');
    }
  }

  // --- Suivi côté serveur : indépendant du navigateur du client ---
  async function pollGenerating(order, now) {
    if (now - order.generatingSince > GENERATION_TIMEOUT_MS) {
      return failOrder(order, 'timeout');
    }
    let data;
    try {
      const url = `${agnesBaseUrl.replace('/v1', '')}/agnesapi?video_id=${encodeURIComponent(order.videoId)}&model_name=${MODEL}`;
      const response = await fetchFn(url, { headers: { Authorization: `Bearer ${agnesApiKey}` } });
      if (!response.ok) return;
      data = await response.json();
    } catch (err) {
      return; // on réessaiera au prochain passage
    }
    if (data.status === 'completed') {
      if (!data.url) return failOrder(order, 'no_video_url');
      order.videoUrl = data.url;
      order.progress = 100;
      order.status = 'completed';
      await tryCapture(order);
    } else if (data.status === 'failed') {
      await failOrder(order, 'generation_failed');
    } else {
      order.progress = data.progress || 0;
    }
  }

  async function tryCapture(order) {
    order.captureAttempts += 1;
    try {
      await stripe.paymentIntents.capture(order.paymentIntentId);
      order.captured = true;
      console.log('Payment captured:', order.id);
    } catch (err) {
      console.error('Capture failed:', order.id, err?.message);
      if (order.captureAttempts >= CAPTURE_MAX_ATTEMPTS) {
        order.status = 'failed';
        order.error = 'payment_capture_failed';
        order.videoUrl = undefined;
      }
    }
  }

  async function tick() {
    if (tickRunning) return;
    tickRunning = true;
    try {
      const now = Date.now();
      for (const order of Array.from(orders.values())) {
        try {
          if (order.status === 'awaiting_payment' && now - order.createdAt > AWAITING_TTL_MS) {
            order.status = 'expired';
            removeFiles(order.files);
            order.files = [];
          } else if (order.status === 'generating') {
            await pollGenerating(order, now);
          } else if (order.status === 'completed' && !order.captured) {
            await tryCapture(order);
          }
          if (['completed', 'failed', 'expired'].includes(order.status) && now - order.createdAt > KEEP_MS) {
            orders.delete(order.id);
          }
        } catch (err) {
          console.error('Order tick error:', order.id, err?.message);
        }
      }
      for (const [ip, rec] of Array.from(ipHits.entries())) {
        if (now - rec.first > RATE_WINDOW_MS) ipHits.delete(ip);
      }
    } finally {
      tickRunning = false;
    }
  }

  function startBackgroundTasks() {
    const timer = setInterval(tick, POLL_MS);
    if (timer.unref) timer.unref();
  }

  return {
    rateLimit,
    createOrderHandler,
    getOrderHandler,
    webhookHandler,
    startBackgroundTasks,
    _internals: { orders, tick, handleAuthorized },
  };
}
