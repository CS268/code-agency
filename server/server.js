import express from 'express';
import multer from 'multer';
import cors from 'cors';
import dotenv from 'dotenv';
import fetch from 'node-fetch';
import { randomUUID } from 'crypto';
import { unlinkSync, existsSync, mkdirSync, readFileSync } from 'fs';
import sharp from 'sharp';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PORT = process.env.PORT || 3001;
const AGNES_API_KEY = process.env.AGNES_API_KEY;
const AGNES_BASE_URL = 'https://apihub.agnes-ai.com/v1';
const UPLOAD_DIR = join(__dirname, 'uploads');
// FIX — chemin vers le build Vite (à ajuster si le frontend n'est pas copié ici, voir étape de déploiement)
const FRONTEND_DIST = join(__dirname, 'public');

if (!existsSync(UPLOAD_DIR)) {
  mkdirSync(UPLOAD_DIR, { recursive: true });
}

const IMAGE_FORMATS = ['image/jpeg', 'image/png', 'image/webp'];
const VIDEO_FORMATS = ['video/mp4', 'video/webm', 'video/quicktime'];
const MAX_IMAGE_SIZE = 15 * 1024 * 1024;
const MAX_VIDEO_SIZE = 50 * 1024 * 1024;
const MAX_KEYFRAME_IMAGES = 2;
const MAX_REFERENCE_IMAGES = 8;
const MAX_MIX_IMAGES = 8;
const MAX_MIX_VIDEOS = 1;
const MIN_PROMPT = 10;
const MAX_PROMPT = 3000;

const rateLimitMap = new Map();
const RATE_LIMIT_WINDOW = 60 * 60 * 1000;
const RATE_LIMIT_MAX = 5;

function checkRateLimit(ip) {
  const now = Date.now();
  const record = rateLimitMap.get(ip);
  if (!record) {
    rateLimitMap.set(ip, { count: 1, firstRequest: now });
    return true;
  }
  if (now - record.firstRequest > RATE_LIMIT_WINDOW) {
    rateLimitMap.set(ip, { count: 1, firstRequest: now });
    return true;
  }
  if (record.count >= RATE_LIMIT_MAX) {
    return false;
  }
  record.count++;
  return true;
}

const jobs = new Map();

// FIX — nettoyage périodique des jobs terminés depuis plus d'1h, pour éviter une fuite mémoire
setInterval(() => {
  const now = Date.now();
  for (const [id, job] of jobs.entries()) {
    if ((job.status === 'completed' || job.status === 'failed') && now - job.createdAt > 60 * 60 * 1000) {
      jobs.delete(id);
    }
  }
}, 15 * 60 * 1000);

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOAD_DIR),
  filename: (req, file, cb) => cb(null, `${randomUUID()}-${file.originalname}`),
});

const upload = multer({
  storage,
  // FIX — la limite globale sert de garde-fou large ; la vraie limite par type est vérifiée après coup, dans la route
  limits: { fileSize: MAX_VIDEO_SIZE },
  fileFilter: (req, file, cb) => {
    const allowedTypes = [...IMAGE_FORMATS, ...VIDEO_FORMATS];
    if (!allowedTypes.includes(file.mimetype)) {
      // FIX — on rejette explicitement avec une erreur plutôt que de laisser le fichier disparaître silencieusement
      return cb(new Error('unsupported_file_type'));
    }
    cb(null, true);
  },
});

const app = express();

// FIX — indispensable sur Render (et tout PaaS derrière un proxy) pour que req.ip soit la vraie IP du visiteur,
// sinon le rate-limit s'applique à tort à l'ensemble des visiteurs confondus
app.set('trust proxy', 1);

app.use(cors());
app.use(express.json());
app.use('/uploads', express.static(UPLOAD_DIR));

// FIX — sert les fichiers du build React (une fois copiés dans FRONTEND_DIST, voir étape de déploiement)
if (existsSync(FRONTEND_DIST)) {
  app.use(express.static(FRONTEND_DIST));
}

function cleanupFiles(files) {
  files.forEach(file => {
    const filePath = file.path || join(UPLOAD_DIR, file.filename);
    if (existsSync(filePath)) {
      try { unlinkSync(filePath); } catch (err) { console.error('Delete failed:', err); }
    }
  });
}

app.post('/api/studio-video/generate', upload.array('files', 9), async (req, res) => {
  try {
    const { mode, prompt, lang = "fr", duration = "5" } = req.body;
    const { pin: _omitPin, ...safeBody } = req.body || {};
    console.log("[DEBUG] req.body:", JSON.stringify(safeBody));
    const files = req.files || [];
    const clientIp = req.ip || 'unknown';

    if (!AGNES_API_KEY) {
      return res.status(500).json({ error: 'api_key_missing', message_fr: 'Clé API manquante', message_en: 'API key missing' });
    }

    if (!checkRateLimit(clientIp)) {
      cleanupFiles(files);
      return res.status(429).json({ error: 'rate_limited', message_fr: 'Trop de tentatives', message_en: 'Rate limited' });
    }

    const accessPin = process.env.STUDIO_ACCESS_PIN;
    if (!accessPin) {
      cleanupFiles(files);
      return res.status(503).json({ error: 'pin_not_configured', message_fr: 'Accès temporairement désactivé', message_en: 'Access temporarily disabled' });
    }
    if (String(req.body?.pin || '') !== accessPin) {
      cleanupFiles(files);
      return res.status(401).json({ error: 'access_denied', message_fr: "Code d'accès invalide", message_en: 'Invalid access code' });
    }

    if (!['keyframe', 'reference-images', 'reference-video', 'mix'].includes(mode)) {
      cleanupFiles(files);
      return res.status(400).json({ error: 'invalid_mode', message_fr: 'Mode invalide', message_en: 'Invalid mode' });
    }

    if (files.length === 0) {
      return res.status(400).json({ error: 'no_files', message_fr: 'Aucun fichier', message_en: 'No files' });
    }

    // FIX — vérification réelle des limites par type, plus seulement une garde globale côté Multer
    for (const file of files) {
      const isImage = IMAGE_FORMATS.includes(file.mimetype);
      const isVideo = VIDEO_FORMATS.includes(file.mimetype);
      if (isImage && file.size > MAX_IMAGE_SIZE) {
        cleanupFiles(files);
        return res.status(400).json({ error: 'image_too_large', message_fr: 'Image trop lourde (max 15 Mo)', message_en: 'Image too large (max 15 MB)' });
      }
      if (isVideo && file.size > MAX_VIDEO_SIZE) {
        cleanupFiles(files);
        return res.status(400).json({ error: 'video_too_large', message_fr: 'Vidéo trop lourde (max 50 Mo)', message_en: 'Video too large (max 50 MB)' });
      }
    }

    if (mode === 'keyframe' && files.length > MAX_KEYFRAME_IMAGES) {
      cleanupFiles(files);
      return res.status(400).json({ error: 'too_many_files', message_fr: 'Trop de fichiers (max 2)', message_en: 'Too many files (max 2)' });
    }

    if (mode === 'reference-images' && files.length > MAX_REFERENCE_IMAGES) {
      cleanupFiles(files);
      return res.status(400).json({ error: 'too_many_files', message_fr: 'Trop de fichiers (max 8)', message_en: 'Too many files (max 8)' });
    }
    if (mode === 'mix') {
      const imageExts = ['.jpg', '.jpeg', '.png', '.webp'];
      const videoExts = ['.mp4', '.mov', '.webm'];
      const imageCount = files.filter(f => imageExts.some(ext => f.originalname.toLowerCase().endsWith(ext))).length;
      const videoCount = files.filter(f => videoExts.some(ext => f.originalname.toLowerCase().endsWith(ext))).length;
      if (imageCount > MAX_MIX_IMAGES || videoCount > MAX_MIX_VIDEOS) {
        cleanupFiles(files);
        return res.status(400).json({ error: 'too_many_files', message_fr: 'Mix: max 8 images + 1 vidéo', message_en: 'Mix: max 8 images + 1 video' });
      }
    }


    if (!prompt || prompt.length < MIN_PROMPT || prompt.length > MAX_PROMPT) {
      cleanupFiles(files);
      return res.status(400).json({ error: 'prompt_invalid', message_fr: 'Prompt invalide (10-3000 caractères)', message_en: 'Invalid prompt (10-3000 chars)' });
    }

    // FIX — validation de la durée, pas de valeur arbitraire envoyée telle quelle à Agnes
    const durationNum = Number(duration);
    if (!Number.isInteger(durationNum) || durationNum < 4 || durationNum > 12) {
      cleanupFiles(files);
      return res.status(400).json({ error: 'duration_invalid', message_fr: 'Durée invalide (4 à 12 secondes)', message_en: 'Invalid duration (4-12 seconds)', message_nl: 'Ongeldige duur (4 tot 12 seconden)' });
    }

    const publicUrls = [];
    for (const file of files) {
      const absPath = file.path || join(UPLOAD_DIR, file.filename);
      const mime = file.mimetype || 'application/octet-stream';
      const isImage = IMAGE_FORMATS.includes(mime);
      if (isImage) {
        const meta = await sharp(absPath).metadata();
        const w = meta.width || 1;
        const h = meta.height || 1;
        const ratio = w / h;
        console.log('[DEBUG] image dims', file.originalname, w + 'x' + h, 'ratio', Number(ratio.toFixed(3)));
        let pipeline = sharp(absPath);
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
        publicUrls.push(`data:image/png;base64,${buf.toString('base64')}`);
      } else {
        const buf = readFileSync(absPath);
        publicUrls.push(`data:${mime};base64,${buf.toString('base64')}`);
      }
    }
    console.log('[DEBUG] media data-uris', publicUrls.map(u => u.slice(0, 48) + ' len=' + u.length));

    const MODEL_PAID = 'agnes-video-2.5';
    const MODEL_FLASH = 'agnes-video-2.5-flash';
    const FLASH_MAX_IMAGES = 5;
    const wantedSize = String(req.body?.resolution || '720P').toUpperCase() === '1080P' ? '1080P' : '720P';
    const agnesRequest = {
      model: MODEL_PAID, // ajusté plus bas selon le mode, les médias et la résolution
      prompt,
      seconds: String(durationNum),
      size: wantedSize,
      aspect_ratio: '9:16',
    };

    if (mode === 'keyframe') {
      agnesRequest.mode = 'keyframe';
      if (publicUrls[0]) agnesRequest.first_frame = publicUrls[0];
      if (publicUrls[1]) agnesRequest.last_frame = publicUrls[1];
    } else if (mode === 'reference-images') {
      agnesRequest.mode = 'reference';
      agnesRequest.images = publicUrls;
    } else if (mode === 'reference-video') {
      agnesRequest.mode = 'reference';
      agnesRequest.videos = [{ url: publicUrls[0], start_seconds: 0, require_audio: false }];
    } else if (mode === 'mix') {
      agnesRequest.mode = 'reference';
      const imageExts = ['.jpg', '.jpeg', '.png', '.webp'];
      const videoExts = ['.mp4', '.mov', '.webm'];
      const imageUrls = publicUrls.filter((_, i) => imageExts.some(ext => files[i].originalname.toLowerCase().endsWith(ext)));
      const videoUrls = publicUrls.filter((_, i) => videoExts.some(ext => files[i].originalname.toLowerCase().endsWith(ext)));
      if (imageUrls.length > 0) agnesRequest.images = imageUrls;
      if (videoUrls.length > 0) agnesRequest.videos = videoUrls.map(url => ({ url, start_seconds: 0, require_audio: false }));
    }

    // Routage de modèle : le modèle gratuit (flash) ne gère ni vidéo de référence, ni plus de 5 images, ni le 1080P
    const refImages = agnesRequest.images ? agnesRequest.images.length : 0;
    const refVideos = agnesRequest.videos ? agnesRequest.videos.length : 0;
    const needsPaidModel = wantedSize === '1080P' || refVideos > 0 || refImages > FLASH_MAX_IMAGES;
    agnesRequest.model = needsPaidModel ? MODEL_PAID : MODEL_FLASH;
    agnesRequest.size = needsPaidModel ? wantedSize : '720P';
    console.log('[ROUTING]', mode, '->', agnesRequest.model, agnesRequest.size);

    let agnesResponse;
    try {
      const response = await fetch(`${AGNES_BASE_URL}/videos`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${AGNES_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(agnesRequest),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Agnes API error:', errorText);
        if (/video_queue_full/.test(errorText)) {
          cleanupFiles(files);
          return res.status(503).json({
            error: 'queue_full',
            message_fr: "La file d'attente de génération est pleine, réessayez dans quelques minutes.",
            message_en: 'The generation queue is full, please try again in a few minutes.',
            message_nl: 'De wachtrij voor generatie is vol, probeer het over een paar minuten opnieuw.',
          });
        }
        cleanupFiles(files);
        return res.status(response.status).json({
          error: 'agnes_api_error',
          message_fr: 'Erreur API Agnes',
          message_en: 'Agnes API error',
          details: errorText,
        });
      }

      agnesResponse = await response.json();
    } catch (err) {
      console.error('Agnes API call failed:', err);
      cleanupFiles(files);
      return res.status(500).json({
        error: 'agnes_unavailable',
        message_fr: 'Service Agnes indisponible',
        message_en: 'Agnes service unavailable',
      });
    }

    // FIX — on ne supprime plus les fichiers immédiatement : si Agnes va chercher les fichiers de façon
    // asynchrone après avoir accepté le job, une suppression trop rapide les rendrait introuvables.
    // Suppression programmée après un délai de sécurité (à ajuster une fois le comportement réel d'Agnes confirmé).
    setTimeout(() => cleanupFiles(files), 10 * 60 * 1000);

    const jobId = randomUUID();
    jobs.set(jobId, {
      jobId,
      model: agnesRequest.model,
      size: agnesRequest.size,
      videoId: agnesResponse.video_id,
      status: 'queued',
      progress: 0,
      createdAt: Date.now(),
    });

    res.json({
      jobId,
      videoId: agnesResponse.video_id,
      status: 'queued',
    });

  } catch (err) {
    console.error('Generate error:', err);
    res.status(500).json({ error: 'server_error', message_fr: 'Erreur serveur', message_en: 'Server error' });
  }
});

app.get('/api/studio-video/status/:jobId', async (req, res) => {
  try {
    const { jobId } = req.params;
    const job = jobs.get(jobId);

    if (!job) {
      return res.status(404).json({ error: 'job_not_found', message_fr: 'Job introuvable', message_en: 'Job not found' });
    }

    if (job.status === 'completed' || job.status === 'failed') {
      return res.json(job);
    }

    try {
      const response = await fetch(
        `${AGNES_BASE_URL.replace('/v1', '')}/agnesapi?video_id=${job.videoId}&model_name=${job.model || 'agnes-video-2.5'}`,
        { headers: { 'Authorization': `Bearer ${AGNES_API_KEY}` } }
      );

      if (!response.ok) {
        return res.json(job);
      }

      const agnesStatus = await response.json();
      job.status = agnesStatus.status;
      job.progress = agnesStatus.progress || 0;

      if (agnesStatus.status === 'completed') {
        job.videoUrl = agnesStatus.url;
        job.status = 'completed';
        job.progress = 100;
      } else if (agnesStatus.status === 'failed') {
        job.status = 'failed';
        job.error = agnesStatus.error?.message || 'Failed';
      } else {
        job.status = 'processing';
      }

      jobs.set(jobId, job);
      res.json(job);
    } catch (err) {
      console.error('Status check error:', err);
      res.json(job);
    }
  } catch (err) {
    res.status(500).json({ error: 'server_error', message_fr: 'Erreur serveur', message_en: 'Server error' });
  }
});

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', service: 'jcode-video-backend', timestamp: new Date().toISOString() });
});

// FIX — repli SPA : toute route non-API renvoie index.html, pour que le routage côté React fonctionne
// une fois rechargé directement sur une sous-page (ex: video.jcode.store/resultat)
app.get('*', (req, res, next) => {
  if (req.path.startsWith('/api/') || req.path.startsWith('/uploads/')) return next();
  const indexPath = join(FRONTEND_DIST, 'index.html');
  if (existsSync(indexPath)) {
    res.sendFile(indexPath);
  } else {
    next();
  }
});

// FIX — middleware d'erreurs déplacé ici, APRÈS toutes les routes (sinon il ne capte jamais rien)
app.use((err, req, res, next) => {
  console.error('Error:', err);
  if (err instanceof multer.MulterError && err.code === 'LIMIT_FILE_SIZE') {
    return res.status(400).json({ error: 'file_too_large', message_fr: 'Fichier trop lourd (max 50 Mo)', message_en: 'File too large (max 50 MB)' });
  }
  if (err.message === 'unsupported_file_type') {
    return res.status(400).json({ error: 'unsupported_file_type', message_fr: 'Type de fichier non supporté', message_en: 'Unsupported file type' });
  }
  res.status(500).json({ error: 'server_error', message_fr: 'Erreur serveur', message_en: 'Server error' });
});

app.listen(PORT, () => {
  console.log(`\n🎬 JCODE Video Backend running on http://localhost:${PORT}\n`);
});
