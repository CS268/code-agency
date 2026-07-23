# Guide Make.com — JCODE AI Concierge

## Variables d'environnement à configurer

| Variable | Valeur | Où |
|----------|--------|-----|
| WEBHOOK_SECRET | [clé secrète] | Make.com Connection |
| GMAIL_APP_PASSWORD | [mot de passe app] | Gmail Connection |
| CLAUDE_API_KEY | [clé API] | HTTP Module Header |
| NOTION_API_KEY | [clé API] | Notion Connection |
| RENDER_SERVER_URL | https://jcode-site-generator.onrender.com | HTTP Module |
| JCODE_EMAIL | matovuruky@gmail.com | Gmail From |

---

## Scénario 1 : Intake Form Submitted

**Déclencheur :** Webhook (Custom webhook URL)

### Modules :

1. **Webhook > Custom Webhook**
   - Method: POST
   - Data structure: voir Payload ci-dessous

2. **HTTP > POST vers Render**
   - URL: `https://jcode-site-generator.onrender.com/api/client-intake`
   - Headers: `X-Webhook-Secret: {{WEBHOOK_SECRET}}`
   - Body: JSON du formulaire

3. **Gmail > Send Email (Email 1 : Bienvenue)**
   - To: `{{email}}`
   - Subject: "🎉 Bienvenue dans l'AI Concierge — JCODE Agency"
   - Template: email-1-intake.html (remplacer variables)

4. **Notion > Create Database Item**
   - Database: "Clients AI Concierge"
   - Properties:
     - Name: `{{business_name}}`
     - Status: "Intake reçu"
     - Sector: `{{sector}}`
     - Email: `{{email}}`
     - Budget: `{{budget}}`
     - Date intake: `{{now}}`

5. **Slack/Discord > Post Message** (optionnel)
   - Channel: #nouveaux-clients
   - Message: "🆕 Nouveau client: {{business_name}} ({{sector}}) — Budget: {{budget}}€/mois"

### Payload Intake Form :
```json
{
  "business_name": "Salon Élégance",
  "sector": "coiffeur",
  "employees": "2-5",
  "website": "https://...",
  "tools": ["instagram", "google_business", "reservation"],
  "time_wasters": "Répondre aux messages, gérer les RDV...",
  "repetitive": "Rappels RDV, posts réseaux sociaux...",
  "budget": 1500,
  "tech_level": 2,
  "goal": "Automatiser les réservations et les rappels",
  "email": "client@email.com",
  "submitted_at": "2026-07-23T10:00:00Z"
}
```

---

## Scénario 2 : Rappel 24h Avant Appel

**Déclencheur :** Schedule (tous les jours à 08:00)

### Modules :

1. **Notion > Search Database**
   - Filter: "Prochain appel" = demain
   - Filter: "Status" ≠ "Annulé"

2. **Iterator > Break** (si plusieurs résultats)

3. **Gmail > Send Email (Email 3 : Rappel)**
   - To: `{{client_email}}`
   - Subject: "⏰ Rappel : votre appel JCODE est demain à {{heure}}"
   - Template: email-3-rappel.html

4. **HTTP > Check Confirmation** (optionnel)
   - Si pas confirmé → notification Slack

---

## Scénario 3 : Post-Call Follow-up

**Déclencheur :** Webhook (appel terminé — trigger manuel ou Zapier/Calendly)

### Modules :

1. **Webhook > Custom Webhook**
   - Reçoit: transcription + metadata appel

2. **HTTP > POST Claude API**
   - URL: `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key: {{CLAUDE_API_KEY}}`, `anthropic-version: 2023-06-01`
   - Body:
   ```json
   {
     "model": "claude-3-5-sonnet-20241022",
     "max_tokens": 4000,
     "system": "[skill-1-call-log.md content]",
     "messages": [{"role": "user", "content": "Transcription: {{transcription}}"}]
   }
   ```

3. **JSON > Parse Response**
   - Extraire: call_log, action_items, quick_wins

4. **Notion > Update Page**
   - Ajouter call log dans la page client
   - Créer action items (sous-pages)
   - Mettre à jour "Dernier appel"

5. **Gmail > Send Email (Email 4 : Follow-up)**
   - To: `{{client_email}}`
   - Subject: "📝 Résumé de notre appel — {{date}}"
   - Template: email-4-followup.html (injecter call_log)

6. **HTTP > POST Render (update hub)**
   - URL: `https://jcode-site-generator.onrender.com/api/hub-update`
   - Body: call_log + action_items

### Payload Call Ended :
```json
{
  "client_id": "notion-page-id",
  "client_name": "Salon Élégance",
  "client_email": "client@email.com",
  "call_date": "2026-07-23T14:00:00Z",
  "call_duration_minutes": 45,
  "call_type": "optimize",
  "session_number": 4,
  "transcription": "Texte complet de la transcription...",
  "recording_url": "https://..."
}
```

---

## Scénario 4 : Rapport Mensuel Auto

**Déclencheur :** Schedule (1er du mois à 09:00)

### Modules :

1. **Notion > Search Database**
   - Filter: "Status" = "Actif"
   - Récupérer tous les clients actifs

2. **Iterator > Break** (pour chaque client)

3. **Notion > Get Page + Relations**
   - Récupérer: appels du mois, deliverables, action items

4. **HTTP > POST Claude API**
   - System: [skill-3-monthly-report.md content]
   - User: "Données du mois: {{monthly_data}}"

5. **Gmail > Send Email (Email 5 : Rapport)**
   - To: `{{client_email}}`
   - Subject: "📊 Rapport Mensuel — {{mois}} | JCODE AI Concierge"
   - Template: email-5-rapport-mensuel.html

6. **Notion > Create Page**
   - Database: "Rapports"
   - Archiver le rapport généré

### Payload Monthly Report Trigger :
```json
{
  "trigger": "monthly_report",
  "month": "2026-07",
  "clients": ["all_active"]
}
```

---

## Configuration Gmail (Make.com)

1. Créer une Google App Password : https://myaccount.google.com/apppasswords
2. Dans Make.com : Add Connection > Gmail > Authorize with Google
3. Utiliser l'adresse : matovuruky@gmail.com
4. Templates : copier le HTML des emails/ et mapper les variables {{}}

## Configuration Notion

1. Créer une Integration : https://www.notion.so/my-integrations
2. Partager les databases avec l'integration
3. Databases à créer :
   - **Clients** : Name, Email, Sector, Status, Budget, Formule, Prochain appel, Dernier appel
   - **Appels** : Date, Type, Durée, Client (relation), Call Log, Recording
   - **Action Items** : Action, Owner, Deadline, Priority, Status, Client (relation)
   - **Deliverables** : Nom, Type, Date, Impact, Client (relation)
   - **Rapports** : Mois, Client (relation), Contenu, ROI

## Tests

1. Tester chaque scénario avec le bouton "Run once"
2. Vérifier les emails dans les spams la première fois
3. Monitorer les exécutions dans Make.com > History
4. Alertes : configurer une notification si un scénario échoue
