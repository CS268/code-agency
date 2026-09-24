> **Version vérifiée :** mattpocock/skills @ `84fdeff` | addyosmani/agent-skills @ `7676817`
> **Recheck mensuel** : 1er de chaque mois.
# LIVRABLES SKILLS — Fiches vérifiées + Template Hub Notion

> Contenus vérifiés sur les repos réels (mattpocock/skills + addyosmani/agent-skills, MIT).
> Date de vérification : aout 2026. Source par skill indiquee (A/M).

---

## PARTIE 1 — FICHES DES 6 SKILLS DU NOYAU (contenu reel verifie)

### 1. grill-me (M, productivity) — L'entretien implacable

**Ce que le skill fait reellement** (SKILL.md complet = 4 lignes) :
Le SKILL.md de grill-me est volontairement minimal : `Run a /grilling session.`
La vraie substance est dans le skill **grilling** (productivity) qu'il invoque.

- Mode : interactif, une question a la fois
- But : aiguiser un plan ou un design par un questionnement sans concession
- Usage : avant de valider un plan, une spec, un devis
- Limite : `disable-model-invocation: true` — l'agent ne l'invoque pas seul, l'utilisateur doit le demander

**A rapprocher de interview-me (A)** qui lui ajoute :
- Une HYPOTHESE + un CONFIDENCE (0-100%) a chaque question
- Le principe "want vs should want" (ce que le client demande != ce qu'il veut reellement)
- Le critere d'arret a ~95% de confiance

### 2. to-spec (M, engineering) — La discussion devient spec

**Processus reel (5 etapes)** :
1. Explorer le repo et utiliser le glossaire du domaine
2. Definir les **seams** (points de test) — preferer ceux qui existent, viser le moins possible
3. Valider ces seams avec l'utilisateur
4. Ecrire la spec avec le template officiel et la publier dans le tracker
5. Appliquer le label `ready-for-agent`

**Template de spec officiel** (inclus dans le skill) :
- Problem Statement (du point de vue utilisateur)
- Solution (du point de vue utilisateur)
- User Stories : liste LONGUE, numerotee, format "As an <actor>, I want a <feature>, so that <benefit>"
- Implementation Decisions (modules, interfaces, schema, API — PAS de chemins de fichiers)
- Testing Decisions (les seams choisis)

**Regle** : NE PAS interviewer l'utilisateur — synthetiser la discussion existante.

### 3. tdd (M, engineering) — Reference du red-green

**Les 4 piliers du skill** :
- **Bon test** : verifie le comportement via l'interface publique, pas les details d'implementation. Se lit comme une spec.
- **Seams** : on ne teste qu'aux seams AGREES AVANT d'ecrire les tests. "Quelle est l'interface publique, quels seams doit-on tester ?"
- **Anti-patterns** : tests couples a l'implementation, tests tautologiques (assertion recalculee comme le code), slicing horizontal (tous les tests puis tout le code — a eviter, travailler en tranches verticales)
- **Regles de la boucle** : red avant green, une tranche a la fois, le refactoring n'est PAS dans la boucle (il appartient au code-review)

**A rapprocher de test-driven-development (A)** qui ajoute :
- "Discover the stack first" : trouver les vraies commandes de test du repo (package.json, gradlew, pytest...)
- Le "Prove-It Pattern" pour les bugs : reproduire le bug par un test avant de corriger

### 4. code-review (M, engineering) — Revue 2 axes en sous-agents

**Processus reel (5 etapes)** :
1. **Piner le point fixe** : `git diff <fixed-point>...HEAD` (three-dot)
2. **Identifier la source spec** : issues dans les commits (#123), chemin passe, fichier spec
3. **Identifier les standards** : CODING_STANDARDS.md, CONTRIBUTING.md + **baseline des 12 code smells de Fowler** :
   Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man, Refused Bequest
4. **Lancer 2 sous-agents en parallele** (Standards + Spec) — chacun avec sa promesse, <400 mots
5. **Agreger** : rapports cote a cote sous ## Standards et ## Spec, NE PAS merger les axes

**A rapprocher de code-review-and-quality (A)** qui ajoute :
- Revue 5 axes (correctness, readability, architecture, security, performance)
- Standard d'approbation : "approuver si ca ameliore la sante globale du code, meme imparfait"
- Labels Nit / Optional / FYI

### 5. handoff (M, productivity) — Passation propre

**Regles reelles** :
- Compacter la conversation en document de passation
- Sauver dans le dossier temp de l'OS (PAS le workspace)
- Section "suggested skills" : quels skills l'agent suivant doit invoquer
- NE PAS dupliquer le contenu deja capture (specs, plans, ADRs, issues, commits) — reference par chemin/URL
- Rediger secrets, cles API, PII
- `argument-hint` : "A quoi servira la prochaine session ?"

### 6. diagnosing-bugs (M, engineering) — Boucle de debug disciplinee

**Le principe fondateur** : "Build a feedback loop. **This is the skill.** Everything else is mechanical."
Un signal pass/fail TIGHT qui devient rouge sur CE bug = le bug est 90% trouve.

**10 facons de construire la boucle** (dans l'ordre) :
1. Test qui echoue au bon seam
2. Script curl/HTTP contre le serveur dev
3. CLI avec fixture, diff vs snapshot connu-bon
4. Script headless browser (Playwright/Puppeteer) — DOM/console/reseau
5. Rejouer une trace capturee (request/payload reels sauves sur disque)
6. Harness jetable (sous-ensemble minimal du systeme)
7. Loop property/fuzz : 1000 inputs aleatoires
8. Harness de bisection : `git bisect run`
9. Loop differentielle : ancienne vs nouvelle version, diff des sorties
10. Script HITL (dernier recours) — `scripts/hitl-loop.template.sh`

**Redaction** : rediger les secrets d'abord, `<REDACTED>` a la place, montrer seulement les lignes porteuses du signal.

---

## PARTIE 2 — TEMPLATE DE LIVRAISON D'UN SKILL (Hub Notion)

> A copier dans le Hub Notion du client pour CHAQUE skill livre.

### Template page skill (page Notion par skill)

```markdown
# [NOM DU SKILL] — v1.0
Package : Starter / Pro / Elite (entourer)
Date de livraison : [date]
Statut : [Actif / En test / En révision]

## 1. En une phrase
[Ce que le skill fait pour vous, en jargon client]

## 2. Problème qu'il résout
[Le problème métier concret, pas technique]

## 3. Quand l'utiliser
- [Cas d'usage 1]
- [Cas d'usage 2]
- [Cas d'usage 3]

## 4. Quand ne PAS l'utiliser
- [Cas où il faut un autre skill]

## 5. Comment l'utiliser (prompt exact)
Copiez-collez ceci dans Claude :
---
<insérer le prompt de déclenchement>
---

## 6. Exemple concret
[Exemple réel du métier du client, avant/après]

## 7. Résultat attendu
[Livrable concret : spec, test, plan, rapport...]

## 8. Test d'acceptation (le client valide)
[Comment le client vérifie que le skill fonctionne sur SON cas]

## 9. Dépendances
[Autres skills à installer avant, réglages, accès]

## 10. Notes / Limitations
[Ce que le skill ne fait pas, mises en garde]
```

### Contenu type pour chaque package

#### Starter (2 skills/mois) — exemple de page remplie

```markdown
# Grill-Me — v1.0
Package : Starter
Date : [date]
Statut : En test

## 1. En une phrase
Transforme une demande vague en besoin réel, par un entretien
une question à la fois.

## 2. Problème qu'il résout
Quand un client (ou vous) demande "une app", "un dashboard",
vous ne savez pas encore ce qui est vraiment voulu. Le skill
creuse jusqu'à ~95% de confiance AVANT d'écrire un plan.

## 3. Quand l'utiliser
- Avant de deviser un projet
- Quand une demande est vague ou conventionnelle
- Avant de créer un plan, une spec ou du code

## 4. Quand ne PAS l'utiliser
- Renommer une variable, corriger une typo
- Question d'information pure ("comment ça marche ?")
- Quand la demande est déjà claire

## 5. Comment l'utiliser (prompt exact)
Agent : j'utilise le skill interview-me. Une question à la fois,
avec ton hypothèse + ton niveau de confiance (0-100%) à chaque fois.
Arrête quand tu atteins ~95% de confiance.

## 6. Exemple concret
Demande : "je veux un site pour mon restaurant"
-> Après 8 questions : vrai besoin = réservation en ligne + menu
   QR, budget 800 EUR, public local, pas besoin d'e-commerce.

## 7. Résultat attendu
Une liste de questions + une synthèse du besoin réel.

## 8. Test d'acceptation
Relancez le skill sur un vrai client. Si après 15 questions
vous pouvez prédire ses réponses, le skill fonctionne.

## 9. Dépendances
Aucune.

## 10. Notes
Skill complémentaire : to-spec (transformer le résultat en devis écrit).
```

#### Pro (skills illimités) — exemples d'ajouts

- Fiches grill-me + to-spec + tdd + code-review + handoff + diagnosing-bugs (complet)
- Un workflow Make.com par automatisation liée : ex. "Nouvelle spec créée -> notification Slack + création page Notion"
- Template de rapport bi-mensuel : skills livrés, usage mesuré, exemples réussis

#### Elite (tout + stratégie) — exemples d'ajouts

- Stratégie IA trimestrielle : quels skills deployer en priorité selon le métier
- Déploiement Vercel : le skill du client est installé/upgradé sur SES services
- ROI détaillé : temps gagné par skill, tâches automatisées, valeur mensuelle

### Script de livraison d'un skill (checklist de l'agence)

```markdown
[ ] 1. Call de cadrage : quel problème métier, pour qui, résultat attendu
[ ] 2. Choisir le skill source (fiche Partie 1) + adapter au jargon client
[ ] 3. Remplir la page Notion (template Partie 2)
[ ] 4. Tester sur un cas réel du client AVANT livraison
[ ] 5. Livrer : page Notion + prompt + exemple concret + test d'acceptation
[ ] 6. Email récap (Starter) / rapport bi-mensuel (Pro) / rapport mensuel+ROI (Elite)
[ ] 7. Enregistrer dans le Hub Notion
```

---

## PARTIE 3 — PROMPTS DE DECLENCHEMENT (verifies sur le contenu reel)

| Skill | Prompt exact à donner à Claude |
|---|---|
| interview-me | "Interview me. Une question à la fois, avec ton hypothèse + ton niveau de confiance (0-100%)." |
| grill-me | "/grill-me" (lance /grilling automatiquement) |
| to-spec | "Synthetise notre discussion en spec avec le template officiel : problem statement, solution, user stories, implementation decisions, testing decisions." |
| tdd | "TDD red-green-refactor sur [feature]. Test qui échoue d'abord, implémente le minimum, refactore. Une tranche verticale à la fois." |
| code-review | "Revue du diff [point fixe]...HEAD sur 2 axes en sous-agents : standards (respecte-t-il les conventions + smells Fowler ?) et spec (implémente-t-il la spec source ?)." |
| code-review-and-quality | "Revue 5 axes (correctness, readability, architecture, security, performance). Standard : un staff engineer approuverait-il ce changement ? Labels Nit/Optional/FYI." |
| diagnosing-bugs | "Diagnostique [bug]. D'abord construis un feedback loop tight pass/fail, minimise le cas, formule une hypothèse, instrumente, corrige, ajoute un test de régression." |
| handoff | "Crée un document handoff pour [objectif de la prochaine session]. Dans le dossier temp, avec section suggested skills, sans dupliquer les artefacts existants, en rédigeant les secrets." |

---

## SOURCES VERIFIEES

- mattpocock/skills : https://github.com/mattpocock/skills (skills/engineering, skills/productivity, skills/misc)
- addyosmani/agent-skills : https://github.com/addyosmani/agent-skills (skills/)
- Licence des deux repos : MIT (reutilisation et revente autorisees, citation de bonne pratique)
