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
