import nodemailer from 'nodemailer';

let transporter = null;

function getTransporter() {
  if (transporter) return transporter;
  const host = process.env.MAGIC_MAIL_HOST;
  const port = Number(process.env.MAGIC_MAIL_PORT || 465);
  const user = process.env.MAGIC_MAIL_USER;
  const pass = process.env.MAGIC_MAIL_PASSWORD;
  if (!host || !user || !pass) return null;
  transporter = nodemailer.createTransport({
    host,
    port,
    secure: port === 465,
    auth: { user, pass },
  });
  return transporter;
}

export const mailEnabled = () => getTransporter() !== null;

export async function sendMagicLink(to, link, palier) {
  const t = getTransporter();
  if (!t) throw new Error('Envoi email non configure (variables MAGIC_MAIL_*)');
  await t.sendMail({
    from: `jcode.store <${process.env.MAGIC_MAIL_USER}>`,
    to,
    subject: 'Votre accès au Studio Marketing jcode.store',
    text: `Bonjour,\n\nMerci pour votre abonnement ${palier}.\nVoici votre lien d'accès personnel :\n${link}\n\nNe le partagez pas.\n\njcode.store`,
    html: `<p>Bonjour,</p><p>Merci pour votre abonnement <b>${palier}</b>.</p><p><a href="${link}">Accéder au Studio Marketing</a></p><p>Ne partagez pas ce lien.</p><p>jcode.store</p>`,
  });
}

export async function sendAlert(subject, text) {
  const t = getTransporter();
  if (!t) { console.error('[ALERTE]', subject, text); return; }
  try {
    await t.sendMail({
      from: `jcode.store <${process.env.MAGIC_MAIL_USER}>`,
      to: process.env.ALERT_EMAIL || process.env.MAGIC_MAIL_USER,
      subject: '[JCODE ALERTE] ' + subject,
      text,
    });
  } catch (err) {
    console.error('[ALERTE] envoi echoue:', err?.message);
  }
}

export async function sendAuditRequest({ email, site, analysis, lang }) {
  const t = getTransporter();
  if (!t) throw new Error('Envoi email non configure (variables MAGIC_MAIL_*)');
  const oneLine = (s) => String(s).replace(/[\r\n]+/g, ' ').slice(0, 200);
  await t.sendMail({
    from: `jcode.store <${process.env.MAGIC_MAIL_USER}>`,
    to: process.env.AUDIT_EMAIL || 'contact@jcode.store',
    replyTo: email,
    subject: '[Audit complet 400 EUR] ' + oneLine(site),
    text: `Nouvelle demande d'audit complet (langue : ${lang})\n\nSite : ${site}\nE-mail : ${email}\n\n--- Résultat de l'analyse fourni par le visiteur ---\n${analysis || '(aucun résultat fourni)'}\n`,
  });
}
