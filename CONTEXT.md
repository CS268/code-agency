# Infrastructure JCODE Agency — Référence (24 août 2026)

## En bref
Rien n'était cassé. jcode.store a tourné sans interruption sur le même repo GitHub Pages pendant toute l'enquête. La "disparition" de code-agency venait d'un check non-authentifié (404 ≠ supprimé — GitHub renvoie délibérément 404 sur un repo privé/inaccessible) combiné à une confusion de noms de dossiers locaux qui a fait perdre le fil.

## Carte de référence — copier-coller au besoin, ne pas re-dériver

| Repo GitHub | Visibilité | Rôle | Hébergement réel | Domaine |
|---|---|---|---|---|
| CS268/code-agency | Public | Frontend — jcode.store (site vitrine + widgets booking/chatbot) | GitHub Pages, branche main | jcode.store |
| CS268/jcode-site-generator | Private | Backend — générateur de site, /booking, emails SMTP | Render (Web Service Starter, srv-d94enhnlk1mc73b55m30) | jcode-site-generator.onrender.com |
| CS268/crousty-night | Private | Site client Crousty Night (Mons) | non vérifié dans cette conversation | — |
| CS268/alibaba-photos | Public | Photos client AliBaba Snack (Cuesmes) | — | — |
| CS268/eden-photos | Public | Photos client "Eden" (Cuesmes) — nouveau client, pas encore documenté ailleurs | — | — |
| CS268/jcode-docs-private | Private | Backup docs internes (skills, CONTEXT.md) | — | — |
| CS268/jcode-agents | Private | Rôle non documenté ici | — | — |

**Dossier local `~/jcode-agency` = repo GitHub `CS268/code-agency`** (vérifié via `git remote -v`, confirmé le 27 août 2026).

DNS de jcode.store : géré via Alibaba Cloud DNS (ns7.alidns.com) — ça, c'est juste le registrar/DNS, pas l'hébergeur du site. Les 4 A-records (185.199.108.153, .109.153, .110.153, .111.153) sont les IP officielles GitHub Pages pour un domaine apex.

## ⚠️ Point encore ouvert, à vérifier
Le prompt d'audit Python/Flask envoyé plus tôt dans cette conversation annonçait "Déploiement : Vercel" pour jcode-site-generator. Le dashboard Render consulté ici montre que c'est faux — c'est Render, pas Vercel. Si un correctif a été conçu en supposant un environnement serverless Vercel (timeouts, config de déploiement), il faut le revérifier contre les vraies contraintes Render avant de le considérer fiable.

## Ce qui a causé la confusion
1. **Noms de dossiers locaux instables.** `~/code-agency` a désigné le frontend dans un prompt, puis le backend dans un autre (`~/jcode-agency` prenant sa place) — le repo GitHub, lui, n'a jamais bougé.
2. **404 mal interprété.** Un check non-authentifié sur un repo privé renvoie 404 par design (pas 403, pour ne pas confirmer son existence à quelqu'un sans accès) — un 404 seul ne prouve pas qu'un repo a disparu.
3. **Mauvais repo vérifié en premier.** L'absence de Pages sur jcode-site-generator (le backend — normal, attendu) a été traitée comme un indice général, alors que la question portait sur le frontend.
4. **Indice secondaire pris pour preuve principale.** Un fichier `_headers` (résidu, convention Netlify) a lancé toute une hypothèse d'hébergement alternatif, avant même de re-vérifier l'état déjà connu et fonctionnel (code-agency avait servi avec succès des déploiements plus tôt dans cette même conversation — boutons Stripe, widget de réservation).

## Règles pour la prochaine fois
- Toujours nommer les repos par leur identifiant GitHub complet (`CS268/code-agency`), jamais par un chemin local — coller cette référence en contexte à chaque nouvelle session ou nouvel outil IA.
- Pour vérifier qu'un repo existe/est accessible : se connecter et regarder `github.com/CS268?tab=repositories` (montre aussi les privés), pas un fetch anonyme.
- Le check le plus direct pour "qui sert ce domaine" est Settings → Pages sur le repo concerné — à faire en premier, pas en dernier recours après une enquête DNS.
- Avant d'explorer une hypothèse d'hébergement alternatif, re-confirmer l'état déjà connu comme fonctionnel dans la conversation en cours.
