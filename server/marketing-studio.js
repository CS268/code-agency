import express from 'express';
import { supabase, supabaseEnabled } from './supabase.js';

const AGNES_BASE = 'https://apihub.agnes-ai.com/v1';
const POLL_BASE = 'https://apihub.agnes-ai.com/agnesapi';
const MODEL = 'agnes-video-2.5';
const MAX_SECONDS = 12;
const MAX_GENERATION_MS = 15 * 60 * 1000;

const jobs = new Map(); // videoId -> { subscriberId, createdAt, refunded }

async function getSubscriber(req) {
  const token = String(req.get('x-marketing-token') || '').trim();
  if (!token || token.length > 200) return { code: 401, error: 'invalid_token' };
  const { data, error } = await supabase
    .from('abonnes_marketing')
    .select('id, palier, quota_mensuel, videos_utilisees, statut, magic_token_expires_at')
    .eq('magic_token', token)
    .maybeSingle();
  if (error) return { code: 500, error: 'server_error' };
  if (!data) return { code: 401, error: 'invalid_token' };
  if (data.statut !== 'actif') return { code: 403, error: 'subscription_inactive' };
  if (!data.magic_token_expires_at || new Date(data.magic_token_expires_at) < new Date()) {
    return { code: 401, error: 'token_expired' };
  }
  return { sub: data };
}

// delta = +1 (reserver une video) ou -1 (rendre une video). Renvoie false si le quota est atteint.
async function changeUsage(id, delta) {
  for (let i = 0; i < 5; i++) {
    const { data: row, error } = await supabase
      .from('abonnes_marketing')
      .select('videos_utilisees, quota_mensuel')
      .eq('id', id)
      .single();
    if (error) throw new Error(error.message);
    const next = row.videos_utilisees + delta;
    if (delta > 0 && next > row.quota_mensuel) return false;
    if (next < 0) return true;
    const { data: upd, error: e2 } = await supabase
      .from('abonnes_marketing')
      .update({ videos_utilisees: next, updated_at: new Date().toISOString() })
      .eq('id', id)
      .eq('videos_utilisees', row.videos_utilisees)
      .select('id');
    if (e2) throw new Error(e2.message);
    if (upd && upd.length) return true;
  }
  throw new Error('conflit de mise a jour du quota');
}

async function refundJob(videoId) {
  const job = jobs.get(videoId);
  if (!job || job.refunded) return;
  job.refunded = true;
  try {
    await changeUsage(job.subscriberId, -1);
    console.log('[MARKETING-STUDIO] video rendue au quota');
  } catch (err) {
    console.error('[MARKETING-STUDIO] remboursement quota echoue:', err?.message);
  }
}

export function registerMarketingStudio(app) {
  if (!supabaseEnabled()) {
    console.log('[MARKETING-STUDIO] desactive (Supabase non configure)');
    return;
  }

  setInterval(() => {
    const limit = Date.now() - 60 * 60 * 1000;
    for (const [id, job] of jobs) if (job.createdAt < limit) jobs.delete(id);
  }, 10 * 60 * 1000).unref();

  app.get('/api/marketing/session', async (req, res) => {
    const auth = await getSubscriber(req);
    if (!auth.sub) return res.status(auth.code).json({ error: auth.error });
    const s = auth.sub;
    res.json({
      palier: s.palier,
      quota: s.quota_mensuel,
      used: s.videos_utilisees,
      remaining: Math.max(0, s.quota_mensuel - s.videos_utilisees),
      max_seconds: MAX_SECONDS,
    });
  });

  app.post('/api/marketing/generate', express.json({ limit: '25mb' }), async (req, res) => {
    const auth = await getSubscriber(req);
    if (!auth.sub) return res.status(auth.code).json({ error: auth.error });
    const key = process.env.AGNES_API_KEY;
    if (!key) return res.status(500).json({ error: 'api_key_missing' });

    const b = req.body || {};
    const prompt = String(b.prompt || '').trim();
    const image = String(b.image || '');
    const frameRate = Math.round(Number(b.frame_rate));
    let numFrames = Math.round(Number(b.num_frames));
    const width = Math.round(Number(b.width));
    const height = Math.round(Number(b.height));

    if (prompt.length < 1 || prompt.length > 3000) return res.status(400).json({ error: 'prompt_invalid' });
    if (!/^data:image\/(png|jpe?g|webp);base64,/.test(image) || image.length > 20 * 1024 * 1024) {
      return res.status(400).json({ error: 'image_invalid' });
    }
    if (!(frameRate >= 1 && frameRate <= 60) || !(numFrames >= 1)) return res.status(400).json({ error: 'duration_invalid' });
    if (!(width >= 256 && width <= 2048 && height >= 256 && height <= 2048)) return res.status(400).json({ error: 'size_invalid' });
    numFrames = Math.min(numFrames, MAX_SECONDS * frameRate); // plafond de duree impose par le serveur

    let reserved;
    try { reserved = await changeUsage(auth.sub.id, +1); }
    catch (err) { console.error('[MARKETING-STUDIO] quota:', err?.message); return res.status(500).json({ error: 'server_error' }); }
    if (!reserved) return res.status(403).json({ error: 'quota_exhausted' });

    const giveBack = () => changeUsage(auth.sub.id, -1).catch((e) => console.error('[MARKETING-STUDIO] remboursement:', e?.message));

    try {
      const r = await fetch(`${AGNES_BASE}/videos`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: MODEL, prompt, image,
          num_frames: numFrames, frame_rate: frameRate,
          resolution: '720P', width, height,
        }),
      });
      if (!r.ok) {
        const txt = await r.text();
        console.error('[MARKETING-STUDIO] Agnes erreur:', r.status, txt.slice(0, 200));
        await giveBack();
        const full = /video_queue_full/.test(txt);
        return res.status(full ? 503 : 502).json({ error: full ? 'queue_full' : 'agnes_error' });
      }
      const data = await r.json();
      const videoId = data.video_id || data.id || data.task_id;
      if (!videoId) { await giveBack(); return res.status(502).json({ error: 'agnes_error' }); }
      jobs.set(videoId, { subscriberId: auth.sub.id, createdAt: Date.now(), refunded: false });
      res.json({
        videoId,
        remaining: Math.max(0, auth.sub.quota_mensuel - auth.sub.videos_utilisees - 1),
      });
    } catch (err) {
      console.error('[MARKETING-STUDIO] Agnes injoignable:', err?.message);
      await giveBack();
      res.status(502).json({ error: 'agnes_unavailable' });
    }
  });

  app.get('/api/marketing/status', async (req, res) => {
    const auth = await getSubscriber(req);
    if (!auth.sub) return res.status(auth.code).json({ error: auth.error });
    const videoId = String(req.query.video_id || '');
    if (!videoId || videoId.length > 200) return res.status(400).json({ error: 'video_id_invalid' });
    const job = jobs.get(videoId);
    if (job && job.subscriberId !== auth.sub.id) return res.status(404).json({ error: 'not_found' });

    if (job && Date.now() - job.createdAt > MAX_GENERATION_MS) {
      await refundJob(videoId);
      return res.json({ status: 'failed', error: 'timeout' });
    }
    try {
      const r = await fetch(
        `${POLL_BASE}?video_id=${encodeURIComponent(videoId)}&model_name=${encodeURIComponent(MODEL)}`,
        { headers: { Authorization: `Bearer ${process.env.AGNES_API_KEY}` } }
      );
      if (!r.ok) return res.json({ status: 'processing', progress: 0 });
      const d = await r.json();
      const status = d.status || 'unknown';
      if (['completed', 'succeeded', 'done'].includes(status)) {
        const url = (d.metadata && d.metadata.url) || d.url || (d.output && d.output.url);
        if (!url) { await refundJob(videoId); return res.json({ status: 'failed', error: 'no_url' }); }
        jobs.delete(videoId);
        return res.json({ status: 'completed', url });
      }
      if (['failed', 'error', 'cancelled'].includes(status)) {
        await refundJob(videoId);
        return res.json({ status: 'failed' });
      }
      res.json({ status: 'processing', progress: d.progress || 0 });
    } catch (err) {
      res.json({ status: 'processing', progress: 0 });
    }
  });
}
