import crypto from 'node:crypto';
import { supabase, supabaseEnabled } from './supabase.js';
import { sendMagicLink } from './mailer.js';

const PALIERS = {
  price_1UOGek2UNDGrRiqnd1fNq96S: { palier: 'decouverte', quota: 5, label: 'Découverte' },
  price_1UOGfk2UNDGrRiqne9ymfRRZ: { palier: 'pro', quota: 15, label: 'Pro' },
  price_1UOGgd2UNDGrRiqnQTh9z66x: { palier: 'agence', quota: 40, label: 'Agence' },
};

const TOKEN_DAYS = 7;
const MAGIC_BASE_URL = process.env.MARKETING_PUBLIC_URL || 'https://jcode.store/studio/marketing/';

async function handleCheckoutCompleted(stripe, session) {
  if (session.mode !== 'subscription') return;
  if (!supabaseEnabled()) {
    console.error('[MARKETING] Supabase non configure');
    return;
  }
  const items = await stripe.checkout.sessions.listLineItems(session.id, { limit: 1 });
  const priceId = items.data[0]?.price?.id;
  const plan = PALIERS[priceId];
  if (!plan) {
    console.log('[MARKETING] abonnement hors Studio Marketing, ignore:', priceId);
    return;
  }
  const email = session.customer_details?.email || session.customer_email;
  const subscriptionId = typeof session.subscription === 'string' ? session.subscription : session.subscription?.id;
  const customerId = typeof session.customer === 'string' ? session.customer : session.customer?.id;
  if (!email || !subscriptionId) {
    console.error('[MARKETING] email ou abonnement manquant dans la session', session.id);
    return;
  }

  const { data: existing, error: findError } = await supabase
    .from('abonnes_marketing')
    .select('id')
    .eq('stripe_subscription_id', subscriptionId)
    .maybeSingle();
  if (findError) throw new Error(findError.message);
  if (existing) return;

  const token = crypto.randomBytes(32).toString('hex');
  const expiresAt = new Date(Date.now() + TOKEN_DAYS * 24 * 60 * 60 * 1000).toISOString();
  const { error: insertError } = await supabase.from('abonnes_marketing').insert({
    email,
    stripe_customer_id: customerId,
    stripe_subscription_id: subscriptionId,
    palier: plan.palier,
    quota_mensuel: plan.quota,
    magic_token: token,
    magic_token_expires_at: expiresAt,
  });
  if (insertError) throw new Error(insertError.message);
  console.log('[MARKETING] abonne cree, palier:', plan.palier);

  try {
    await sendMagicLink(email, `${MAGIC_BASE_URL}?token=${token}`, plan.label);
    console.log('[MARKETING] lien magique envoye');
  } catch (err) {
    console.error('[MARKETING] envoi email echoue:', err?.message);
  }
}

async function handleInvoicePaid(invoice) {
  if (invoice.billing_reason !== 'subscription_cycle') return;
  if (!supabaseEnabled()) return;
  const sub = invoice.subscription || invoice.parent?.subscription_details?.subscription;
  const subscriptionId = typeof sub === 'string' ? sub : sub?.id;
  if (!subscriptionId) return;
  const now = new Date().toISOString();
  const { error } = await supabase
    .from('abonnes_marketing')
    .update({ videos_utilisees: 0, cycle_debut: now, updated_at: now })
    .eq('stripe_subscription_id', subscriptionId);
  if (error) throw new Error(error.message);
  console.log('[MARKETING] quota remis a zero');
}

export async function handleMarketingEvent(stripe, event) {
  if (event.type === 'checkout.session.completed') return handleCheckoutCompleted(stripe, event.data.object);
  if (event.type === 'invoice.paid') return handleInvoicePaid(event.data.object);
}
