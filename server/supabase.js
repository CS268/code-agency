// server/supabase.js — client Supabase partagé pour le suivi des abonnements Marketing Studio.
// Actif seulement si SUPABASE_URL et SUPABASE_SERVICE_KEY existent.
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

export const supabase = (SUPABASE_URL && SUPABASE_SERVICE_KEY)
  ? createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
      auth: { persistSession: false },
    })
  : null;

export const supabaseEnabled = () => supabase !== null;
