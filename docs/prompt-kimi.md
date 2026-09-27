# PROMPT POUR KIMI — Application des skills dans ~/code-agency

Copie-colle tout ce qui suit (entre les balises BEGIN/END) dans Kimi.

---

BEGIN PROMPT

# PROMPT POUR KIMI — Application des skills dans ~/jcode-agency

Copie-colle tout ce qui suit (entre les balises BEGIN/END) dans Kimi.

---

BEGIN PROMPT

## CONTEXTE

Tu interviens sur le projet `~/jcode-agency` — le site vitrine de JCODE Agency
(github.com/CS268/code-agency, hébergé sur GitHub Pages). C'est une agence
solo qui vend des sites web + IA pour commerces locaux belges, avec 3 packages
sites (Teaser 497 EUR, Pro 999 EUR, Pro Max 1 599 EUR, paiement unique) et un
abonnement mensuel AI Concierge (Starter 1 000 EUR, Pro 1 500 EUR, Elite
2 000 EUR).

Deux fichiers de travail viennent d'être ajoutés dans `~/jcode-agency/docs/` :
- `WORKFLOW.md` — le workflow complet de livraison par skills IA
- `livrables-skills.md` — fiches vérifiées des 6 skills du noyau + templates
  de livraison prêts pour le Hub Notion

## CE QUI A ETE FAIT AVANT TOI

1. Deux repos de skills Claude ont été identifiés et inventoriés via l'API
   GitHub (contenu RÉEL vérifié, pas supposé) :
   - `mattpocock/skills` : 29 skills stables (engineering 18, productivity 7,
     misc 4) + 6 in-progress (claude-handoff, loop-me, setup-ts-deep-modules,
     writing-beats, writing-fragments, writing-shape)
   - `addyosmani/agent-skills` : 24 skills dont interview-me,
     test-driven-development, code-review-and-quality, security-and-hardening,
     shipping-and-launch
2. `docs/WORKFLOW.md` documente : le mapping des skills avec les packages
   AI Concierge (Starter = 2 skills/mois, Pro = illimité, Elite = tout +
   déploiement Vercel), le catalogue complet des 2 repos, le flux complet de
   livraison, des prompts copy-paste, les templates de livraison client et les
   verdicts overkill.
3. `docs/livrables-skills.md` contient les fiches vérifiées des 6 skills du
   noyau (à partir des SKILL.md réels), le template de page Notion par skill
   (10 sections), le contenu type par package, la checklist de livraison et
   les prompts de déclenchement exacts.

## CE QUE JE TE DEMANDE DE FAIRE

1. **Vérifie et affines** : lis les deux fichiers dans `docs/` puis vérifie
   que mes instructions ci-dessous sont cohérentes avec eux.
2. **Génère en TEXTE (pas d'installation, pas d'accès terminal)** :
   Tu n'as PAS accès au disque ni au terminal — ni installation de skills,
   ni création de fichiers. Produis uniquement du texte prêt à copier-coller :
   a. Un CONTEXT.md complet pour le site (métier, vocabulaire, stack,
      règles critiques), à partir de l'exemple du WORKFLOW.md section 2.
   b. Deux pages Notion prêtes à coller (format du template dans
      livrables-skills.md, Partie 2) pour les 2 premiers skills Starter :
      `interview-me` et `to-spec`, avec le jargon réel du site.
3. **Reporte** toute incohérence entre mes instructions et les fichiers du
   repo, et tout skill dont le nom réel diffère de ce que j'ai listé.

## REGLES DE TRAVAIL

- Produis uniquement du texte prêt à copier-coller : aucun fichier n'est créé
  ni modifié par toi, c'est l'utilisateur qui colle les livrables.
- Ne touche PAS au backend (jcode-site-generator).
- Ne touche PAS aux widgets live (booking-widget.js, chatbot-widget.js).
- Le site est édité via GitHub (crayon), pas via ce repo local. Les livrables
  sont des documents de préparation, pas des modifications directes de
  index.html.
- Si un élément est inséré dans une page traduite : c'est un frère d'un div
  data-i18n, jamais un enfant.
- Rédige en français sauf les prompts destinés aux agents (ceux-là restent
  tels quels).



END PROMPT
