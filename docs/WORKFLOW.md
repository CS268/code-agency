# WORKFLOW JCODE Agency — Livraison par Skills IA

> Adapté à une agence solo (+ 1 freelance occasionnel).
> Sources : mattpocock/skills + addyosmani/agent-skills (MIT).
> Tools : Kimi, Claude, Cursor, VS Code.

## A. LES SKILLS = LES LIVRABLES AI CONCIERGE

Les skills ne sont pas que des outils internes : ce sont **les livrables vendus dans AI Concierge** (packages Starter / Pro / Elite). Quand un client souscrit, il reçoit des skills Claude codifiés, livrés via ce workflow.

### Mapping packages -> skills livrés

| Package Concierge | Prix/mois | Skills livrés au client |
|---|---|---|
| **Starter** | 1 000 EUR | 2 skills Claude/mois au choix (voir catalogue section B) + Hub Notion + Voxer + email récap après chaque appel |
| **Pro** | 1 500 EUR | Skills Claude **illimités** + workflows Make.com + support prioritaire Voxer (<6h) + rapports bi-mensuels + templates exclusifs |
| **Elite** | 2 000 EUR | Tout Pro + 4 appels/mois + rapports mensuels avec ROI détaillé + stratégie IA trimestrielle + canal Slack/Discord dédié + **déploiement Vercel inclus** |

### Catalogue des skills livrables (section B)

Chaque skill du catalogue est un livrable autonome : nom, problème résolu, quand l'utiliser, difficulté, dépendances. Tu les livres dans l'ordre des packages ci-dessus.

---

## B. CATALOGUE DES SKILLS LIVRABLES

> A = addyosmani/agent-skills · M = mattpocock/skills

### B.1 Noyau a maîtriser (recommandes)

| Skill | Repo | Problème résolu | Contexte client | Diff. | Dépendances |
|---|---|---|---|---|---|
| grill-me / interview-me | M / A | Comprendre le vrai besoin avant de coder | Discovery call | 1 | Aucune |
| grill-with-docs | M | Construire le jargon partagé (CONTEXT.md, ADR) | Projets récurrents | 2 | grill-me |
| to-spec / spec-driven-development | M / A | Transformer la discussion en spec/devis écrit | Après le call, avant devis | 1-2 | grill-me |
| planning-and-task-breakdown | A | Découper la spec en tâches vérifiables | Spec validée -> plan | 2 | spec |
| tdd / test-driven-development | M / A | Test d'abord, code ensuite (red-green-refactor) | Toute fonctionnalité | 3 | Aucune |
| implement / incremental-implementation | M / A | Construire tranche par tranche, commit par commit | Build client | 2-3 | spec + tdd |
| code-review | M | Revue 2 axes (standards + spec) en sous-agents | Avant livraison | 2 | tdd |
| code-review-and-quality | A | Revue 5 axes, labels Nit/Optional/FYI | Avant merge | 2 | Aucune |
| security-and-hardening | A | OWASP Top 10, secrets, validation inputs | Tout formulaire client | 3 | Aucune |
| diagnosing-bugs / debugging-and-error-recovery | M / A | Boucle disciplinée de debug | Bugs en maintenance | 3 | tdd |
| browser-testing-with-devtools | A | Test navigateur réel (DOM, console, réseau, perf) | Avant mise en prod | 2 | Aucune |
| handoff | M | Passer un projet propre à un autre agent/freelance | Sous-traitance | 1 | Aucune |
| shipping-and-launch | A | Checklist pré-lancement, rollback, monitoring | Mise en production | 2 | ci-cd |
| git-workflow-and-versioning | A | Commits atomiques, trunk-based | Toujours | 1 | Aucune |
| frontend-ui-engineering | A | Composants, WCAG 2.1 AA, responsive | Sites vitrine | 2 | Aucune |
| api-and-interface-design | A | Contract-first, erreurs sémantiques | API backend | 3 | Aucune |

### B.2 Catalogue complet addyosmani/agent-skills (24)

| Skill | Problème résolu | Contexte |
|---|---|---|
| api-and-interface-design | Contract-first, erreurs sémantiques | API backend |
| browser-testing-with-devtools | Test navigateur réel (DOM, console, réseau, perf) | Avant mise en prod |
| ci-cd-and-automation | Pipeline build/test/deploy | Deploiement continu |
| code-review-and-quality | Revue 5 axes, labels Nit/Optional/FYI | Avant merge |
| code-simplification | Reduire la complexite du code | Refactoring |
| context-engineering | Optimiser le contexte donne aux agents | Pour vos agents IA |
| debugging-and-error-recovery | Boucle disciplinée de debug | Bugs |
| deprecation-and-migration | Migrer sans casser | Anciens systemes |
| documentation-and-adrs | ADR, pourquoi des decisions | Architecture |
| doubt-driven-development | Lever les doutes au bon moment | Decisions critiques |
| frontend-ui-engineering | Composants, WCAG 2.1 AA, responsive | Sites vitrine |
| git-workflow-and-versioning | Commits atomiques, trunk-based | Toujours |
| idea-refine | Affiner une idee en spec | Idees clients |
| incremental-implementation | Construire tranche par tranche | Build |
| interview-me | Questions pour extraire le besoin | Discovery |
| observability-and-instrumentation | Logs, metrics, tracing | Production |
| performance-optimization | Ameliorer la vitesse | Perf |
| planning-and-task-breakdown | Decouper en taches verifiables | Spec -> plan |
| security-and-hardening | OWASP Top 10, secrets, inputs | Formulaires |
| shipping-and-launch | Checklist pre-lancement, rollback | Mise en prod |
| source-driven-development | Spec/source comme reference unique | Grosses bases |
| spec-driven-development | PRD rigide avant le code | Gros projets |
| test-driven-development | Red-green-refactor | Toute fonctionnalite |
| using-agent-skills | Router vers le bon skill | Utilisation quotidienne |

### B.3 Catalogue complet mattpocock/skills (29 stables + 6 in-progress)

| Skill | Dossier | Problème résolu |
|---|---|---|
| ask-matt | engineering | Repondre "comment Matt ferait ca ?" (best practices) |
| code-review | engineering | Revue 2 axes (standards + spec) en sous-agents |
| codebase-design | engineering | Structurer une base de code |
| diagnosing-bugs | engineering | Boucle disciplinée de debug |
| domain-modeling | engineering | Modeliser le domaine metier |
| grill-with-docs | engineering | Construire le jargon partage (CONTEXT.md, ADR) |
| implement | engineering | Implementer une spec tache par tache |
| improve-codebase-architecture | engineering | Ameliorer l'architecture existante |
| prototype | engineering | Prototyper vite pour valider une idee |
| research | engineering | Rechercher avant de coder |
| resolving-merge-conflicts | engineering | Resoudre des conflits git |
| setup-matt-pocock-skills | engineering | Installer les skills |
| tdd | engineering | Test d'abord, code ensuite |
| to-spec | engineering | Discussion -> spec ecrite |
| to-tickets | engineering | Spec -> tickets |
| triage | engineering | Router les demandes vers la bonne equipe |
| wayfinder | engineering | Naviguer une base de code inconnue |
| wizard | engineering | Guide pas a pas pour installer/configurer |
| grill-me | productivity | Interroger pour extraire le besoin reel |
| grilling | productivity | Techniques de questionnement approfondi |
| handoff | productivity | Passer un projet propre |
| teach | productivity | Enseigner un concept a un agent |
| to-questionnaire | productivity | Spec -> questionnaire de validation |
| wait-what | productivity | Detecter les hypotheses non verifiees |
| writing-for-agents | productivity | Ecrire des instructions claires pour agents |
| git-guardrails-claude-code | misc | Garde-fous git pour Claude Code |
| migrate-to-shoehorn | misc | Migrer un setup |
| scaffold-exercises | misc | Generer des exercices d'entrainement |
| setup-pre-commit | misc | Configurer pre-commit |

> **Noyau à maîtriser (stables)** : grill-me, to-spec, tdd, implement, code-review, handoff, diagnosing-bugs
> **Autres stables** : ask-matt, codebase-design, domain-modeling, prototype, research, resolving-merge-conflicts, setup-matt-pocock-skills, to-tickets, triage, wayfinder, wizard, grilling, teach, to-questionnaire, wait-what, writing-for-agents, git-guardrails-claude-code, migrate-to-shoehorn, scaffold-exercises, setup-pre-commit
> **En cours (non stables)** : claude-handoff, loop-me, setup-ts-deep-modules, writing-beats, writing-fragments, writing-shape

---

## 0. INSTALLATION (30 min, une seule fois)

```bash
# Matt Pocock — choisir : grill-me, to-spec, tdd, implement, code-review, handoff, diagnosing-bugs
npx skills@latest add mattpocock/skills

# Addy Osmani — installer tout, filtrer après
npx skills add addyosmani/agent-skills

# Claude Code (optionnel)
/plugin marketplace add https://github.com/addyosmani/agent-skills.git
/plugin install agent-skills@addy-agent-skills
```

---

## 1. LE FLUX COMPLET

```
1. INTAKE FORM (existant)
2. CHATBOT IA (existant) — qualification auto
3. RESERVATION AUTO (existant) — la demo se reserve
4. DISCOVERY CALL — /grill-me ou /interview-me
   -> spec produite avec /to-spec = document de devis
5. STRIPE (existant) — Teaser/Pro/Pro Max paye
6. BUILD — /tdd + /implement + incremental
7. QUALITY GATE — /code-review + security-checklist + personas
8. SHIPPING — /shipping-and-launch (checklist, rollback)
9. LIVRAISON + RAPPORTS (argument commercial)
10. MAINTENANCE — /diagnosing-bugs sur les tickets
```

| Etape du parcours | Skill a utiliser | Outil |
|---|---|---|
| Formulaire rempli | `using-agent-skills` pour router | Kimi/Claude |
| Qualification chatbot | `/interview-me` (preparer le call) | — |
| Demo reservee | `/grill-me` (preparer le call) | Claude |
| Discovery call | `/grill-me` + `/to-spec` | Cursor/VS Code |
| Devis valide | `spec-driven-development` (PRD) | VS Code |
| Paiement Stripe | — (existant) | — |
| Build | `/tdd` + `incremental-implementation` + `/implement` | Cursor/VS Code |
| Revue | `/code-review` + personas + `security-and-hardening` | Cursor/Claude |
| Deploiement | `git-workflow-and-versioning` + `shipping-and-launch` | VS Code + terminal |
| Bug client | `diagnosing-bugs` + `debugging-and-error-recovery` | Cursor |
| Sous-traitance | `/handoff` | Kimi/Claude |

### Mapping de la pipeline existante (jcode-site-generator) — aout 2026

Ta pipeline deja construite dans `~/jcode-site-generator` correspond en partie aux skills. Table de correspondance :

| Ta fonction (jcode-site-generator) | Skill equivalent | Ce que le skill apporte en plus |
|---|---|---|
| Intake form + discovery call | `interview-me` / `grill-me` | Questionnement structure avec hypothese + score de confiance |
| `STATE.md` (cerveau vivant) | `context-engineering` | Charger le bon contexte au bon moment |
| `orchestrator.py` (chaines d'agents) | — (pas d'equivalent engineering) | L'orchestrateur = deja un meta-skill maison |
| — phase PLAN absente | `spec-driven-development` / `to-spec` | **GAP** : ecrire la spec AVANT de generer |
| `build_demo_prompt` (Site Generator) | `incremental-implementation` | **GAP** : generation one-shot vs tranches fines verifiees |
| `verify_site_quality` (16 checks) | `test-driven-development` | **GAP** : verifier APRES vs tester D'ABORD (failing test) |
| `autoverify_v2.py` (Playwright E2E) | `browser-testing-with-devtools` | Deja equivalent, voire plus complet |
| Loop Rectifier (retry prompt renforce) | `debugging-and-error-recovery` | Reproduire -> localiser -> fixer -> garde-fou |
| Deploy Vercel <2 min | `shipping-and-launch` | Checklist pre-lancement + rollback plan |
| — phase REVOIR absente | `code-review-and-quality` | **GAP** : revue du code genere avant livraison |
| GBRAIN (apprentissage des echecs) | — (aucun skill ne le fait) | Force maison, a preserver |

**Verdict formation 14 jours :**
- Deja acquis (ne pas reapprendre) : verification (16 checks + autoverify), deploiement, memoire (STATE.md/GBRAIN), orchestration.
- **3 GAPS a prioriser** : (1) `to-spec`/`spec-driven-development` avant generation, (2) `test-driven-development` (test d'abord), (3) `code-review-and-quality` avant livraison client.
- Le reste du catalogue (productivity, finance) : survoler seulement.

---

## 2. CONTEXT.md — le fondement (a faire en premier)

Cree `CONTEXT.md` a la racine de chaque projet client. C'est le jargon partage qui rend tous les agents 3x plus precis.

### Exemple pour JCODE Agency (`~/code-agency/CONTEXT.md`)

```markdown
# CONTEXT — JCODE Agency

## Metier
Agence de sites web + IA pour commerces locaux belges
(business, restaurant, coiffeur, boulanger, ...).

## Vocabulaire
### Offres sites vitrines (paiement unique)
- Teaser : package d'entree 497 EUR, site vitrine 1 page, paiement unique
- Pro : 999 EUR, site jusqu'a 3 pages + QR code, paiement unique
- Pro Max : 1,599 EUR, jusqu'a 5 pages + QR + reservation + chatbot

### AI Concierge (abonnement mensuel)
- Starter : 1 000 EUR/mois — 2 skills Claude/mois, 2 appels 45 min, Hub Notion, Voxer
- Pro : 1 500 EUR/mois — skills Claude illimites, workflows Make.com, support prioritaire
- Elite : 2 000 EUR/mois — 4 appels/mois, rapports mensuels + ROI, strategie IA trimestrielle, Slack/Discord, deploiement Vercel inclus
- Un skill livrable = un agent codifie (grill-me, tdd, code-review, ...) livre au client via ce workflow
- Reservation Auto : service de reservation en ligne (widget vert)
- Chatbot IA : widget de chat (bouton mauve) connecte au backend /chatbot
- Menu QR Code : QR vers le menu/les infos (widget)
- Endpoint /booking : API backend de reservation (Render)
- Endpoint /chatbot : API backend du chatbot (Render)
- i18n : systeme de traduction fr/en/nl par fichier translations.json
- data-i18n : attribut HTML utilise par i18n.js pour traduire
- data-i18n-html : variante qui autorise le HTML
- Ne PAS mettre d'elements a l'interieur d'un div data-i18n
  (i18n.js ecrase le contenu par innerHTML)

## Stack
- Frontend : HTML/CSS/JS vanilla, GitHub Pages (CS268/code-agency)
- Backend : Python Flask sur Render (jcode-site-generator)
- Paiement : Stripe (liens buy.stripe.com)
- Traductions : fr/en/nl

## Decisions
- Toute insertion visuelle = soeur du div data-i18n, jamais enfant
- Les widgets sont des fichiers JS auto-contenus en fin de page
- Positions : boutons fixes bas-droite, z-index au-dessus du cookie banner (9999)
```

### Comment le construire
Lance `/grill-with-docs` sur le projet : il t'interroge, puis ecrit et affine `CONTEXT.md` et les ADR en direct.

---

## 3. PROMPTS COPY-PASTE

### Discovery call (avant l'appel)

> Agent : j'utilise le skill `/grill-me`. Interroge-moi sur ce projet client un point a la fois. But : extraire le besoin reel, pas ce que le client croit vouloir. Pose les questions de facon ordonnee : objectif -> public -> pages -> fonctionnalites -> paiement -> design -> budget -> delai -> risques. Ne fais PAS de plan, seulement des questions jusqu'a ce que chaque branche soit resolue.

### Devis documente (apres le call)

> Agent : j'utilise `/to-spec`. Synthetise toute la discussion precedente en une spec structuree : objectif, perimetre inclus/exclus, pages, fonctionnalites, design, livrables, delais, hypotheses. Publie-la dans `specs/<client>.md`. Sois precis et utilisable comme document de devis.

### PRD rigide (pour gros projets)

> Agent : j'utilise `spec-driven-development`. Ecris un PRD pour <projet> : objectifs, commandes/API, structure du projet, style de code, strategie de test, limites du scope. Rien n'est code avant validation du PRD.

### Plan de taches

> Agent : j'utilise `planning-and-task-breakdown`. Decoupe la spec `<fichier>` en taches verifiables : chacune avec criteres d'acceptation et ordre de dependance. Une tache = un commit possible. Liste dans l'ordre d'execution.

### TDD (logique metier)

> Agent : j'utilise `/tdd`. Red-green-refactor sur <fonctionnalite>. Ecris le test qui echoue d'abord, verifie qu'il echoue, implemente le minimum pour passer, refactore. Une tranche verticale a la fois.

### Revue avant livraison (2 outils)

> Agent mattpocock : j'utilise `/code-review`. Revue du diff sur 2 axes en sous-agents paralleles : (1) Standards — respecte-t-il les conventions du repo + baseline des code smells de Fowler ? (2) Spec — implemente-t-il fidelement la spec/ticket source ?

> Agent addyosmani : j'utilise le persona `code-reviewer`. Revue 5 axes avec le standard "un staff engineer approuverait-il ce changement ?". Labels Nit / Optional / FYI. Taille de changement raisonnable (~100 lignes).

### Securite avant mise en prod

> Agent : j'utilise `security-and-hardening` + `references/security-checklist.md`. Audite ce service : validation des inputs, auth, secrets, dependances, CORS. Passe les 3 couches de perimetre. Remonte les vulns par severite. N'ecris RIEN dans les logs sensibles.

### Bug client (maintenance)

> Agent : j'utilise `diagnosing-bugs`. Boucle disciplinee : (1) construis un feedback loop qui rend le bug rouge, (2) minimise le cas, (3) formule une hypothese, (4) instrumente pour verifier, (5) corrige, (6) ajoute un test de regression. Ne passe pas a l'etape suivante sans evidence.

### Debugging navigateur (site client)

> Agent : j'utilise `browser-testing-with-devtools`. Ouvre la page en Chrome DevTools MCP : inspecte le DOM, la console, le reseau (fetch), la performance. Diagnostique le comportement reel, pas ce qui "devrait" etre.

### Sous-traitance a un freelance

> Agent : j'utilise `/handoff`. Compacte la conversation actuelle en document de passation : contexte, decisions prises, etat du travail, fichiers touches, prochaines etapes, pieges. L'objectif : un autre agent reprend sans poser de questions.

### Mise en production

> Agent : j'utilise `shipping-and-launch`. Checklist pre-lancement : tests verts, feature flags, rollback planifie, monitoring en place, prets a deployer progressivement.

---

## 4. TEMPLATES DE LIVRAISON CLIENT

### 4.1 Livraisons AI Concierge (abonnement) — les skills SONT le produit

Les skills sont les livrables des packages Starter / Pro / Elite. Chaque livraison suit ce cycle.

#### Starter (1 000 EUR/mois) — 2 skills/mois
- Exemple de livraison : "Tu recois ce mois-ci 2 skills Claude : `/grill-me` (trouver le vrai besoin d'un client) et `/to-spec` (transformer une discussion en spec de devis). Livres dans ton Hub Notion, avec template et exemples."
- Cycle de livraison : call de cadrage -> production du skill -> test sur ton cas reel -> email recap + enregistrement dans le Hub Notion
- Skills les plus vends : grill-me, to-spec, tdd, code-review, diagnosing-bugs, handoff

#### Pro (1 500 EUR/mois) — skills illimites + workflows Make.com
- Tout Starter, en illimite.
- Ajouts : workflows Make.com (automatisations liees aux skills), support prioritaire Voxer (<6h), rapports bi-mensuels sur les skills livres et leur usage.
- Cycle : same + rapport bi-mensuel + templates exclusifs

#### Elite (2 000 EUR/mois) — tout Pro + reporting + strategie
- 4 appels/mois (acces prioritaire), rapports mensuels avec ROI detaille (temps gagne, taches automatisees), strategie IA trimestrielle, canal Slack/Discord dedie.
- Deploiement Vercel inclus : les skills du client sont deployes/upgrades directement sur ses services.

#### Contrat de livraison d'un skill (commun aux 3 packages)
- Scope : 1 skill = 1 probleme resolu, nomme, avec mode d'emploi et exemples.
- Acceptation : le client teste le skill sur un cas reel avant validation.
- Facturation : inclus dans le package mensuel ; hors package = a la piece (section 4.2). > **Option B** (moyennes entreprises avec équipe de dev) : aspirationnelle,
> aucun client concret à ce jour. Ne pas complexifier les templates pour ce cas.
> Réévaluer quand un premier prospect B apparaît.                           > **Plafond AI Concierge :** Max 5 clients simultanés en Starter/Pro.
> Au-delà, sous-traiter ou refuser.

### 4.2 Services a la piece (site vitrines + maintenance)

### Audit & Spec (grill-me + to-spec)
- Pitch : "En 48h, je te livre un document qui decrit EXACTEMENT ce que ton site fera, avec ton jargon, valide par toi avant qu'on code quoi que ce soit."
- Livrable : spec ecrite + glossaire + perimetre ferme + planning
- Duree : 2-3 jours
- Prix : 200-400 EUR (ou inclus dans Teaser 497 EUR)
- Workflow : intake form -> /interview-me -> /grill-me -> /to-spec -> validation -> devis

### Build garanti (tdd + implement + incremental)
- Pitch : "Je construis ton site tranche par tranche, chaque fonctionnalite est testee AVANT d'etre livree."
- Livrable : site fonctionnel + tests verts + commits tracables
- Duree : 1-3 semaines
- Prix : 999 EUR (Pro) + options
- Workflow : spec -> planning -> incremental + /tdd -> demo par tranche -> code-review

### Qualite production (review + security + shipping)
- Pitch : "Ton site est livre comme un produit de production : revu par des agents specialises (securite, perf, accessibilite), teste en navigateur reel, deploye avec rollback."
- Livrable : site + rapport securite (OWASP) + rapport perf (Core Web Vitals) + garantie 90 jours
- Duree : +3-5 jours sur le Pro
- Prix : 1,599 EUR
- Workflow : code-review + personas security-auditor + web-performance-auditor + browser-testing -> shipping-and-launch -> livraison avec rapports

### Resolution de bug (diagnosing-bugs)
- Pitch : "Un souci sur ton site ? Je le corrige avec une methode eprouvee et je garantis que ca ne revient pas."
- Livrable : fix + test de regression + rapport cause racine
- Duree : 24-72h
- Prix : 75-150 EUR / intervention, ou 49-99 EUR/mois en maintenance
- Workflow : ticket -> diagnosing-bugs -> fix + /tdd -> regression -> deploiement

### Handoff propre (interne)
- Pitch : "Je te passe un projet entierement documente, tu n'as AUCUNE question a me poser."
- Livrable : document handoff
- Duree : 30 min
- Cout : economise en clarifications
- Workflow : /handoff -> transfert -> revue du travail avec /code-review

---

## 5. OVERKILL — a eviter dans ce contexte

| Skill | Verdict | Raison |
|---|---|---|
| wayfinder, triage, to-tickets | Overkill | Penses pour grosses equipes, pas pour toi |
| observability, ci-cd complet | Overkill | Render/Vercel tout-en-un suffisent |
| doubt-driven-development | Overkill au quotidien | Reserver aux decisions critiques |
| deprecation-and-migration | Overkill | Tu ne depries pas de systemes clients |
| teach, to-questionnaire, wizard | A la demande | Peu frequent |

**Noyau a maitriser (80% de la valeur) :**
1. grill-me / interview-me — la qualite en amont (discovery)
2. to-spec / spec-driven-development — le devis documente
3. tdd — la qualite du code
4. code-review + security-and-hardening — la ceinture de securite
5. handoff — la sous-traitance propre
6. diagnosing-bugs — la maintenance

---

## 6. PLANNING 14 JOURS (rappel)

- Jours 1-2 : Fondations (CONTEXT.md + using-agent-skills)
- Jours 3-5 : Matt Pocock (grill-me -> to-spec -> tdd)
- Jours 6-8 : Addy Osmani (spec -> plan -> build)
- Jours 9-11 : Verification & Review (test -> review -> security)
- Jours 12-14 : Integration (diagnosing-bugs, handoff, shipping)

---

## 7. NOTES LEGALES

Les 2 repos sont sous licence MIT : utilisables et revendables dans tes prestations.
Citer les sources est une bonne pratique (mattpocock/skills, addyosmani/agent-skills). > **Recheck mensuel** : 1er de chaque mois, vérifier si les skills du noyau
> ont changé de catégorie ou de comportement (repo évolutif : 420+ commits).
