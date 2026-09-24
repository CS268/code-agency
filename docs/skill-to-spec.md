> ⚠️ **Ce skill est un outil INTERNEMENT utilisé par JCODE Agency.**  
> Le client ne reçoit pas "le skill to-spec" — il reçoit le **cahier des charges** que ce skill nous permet de produire.  
> Cette page est une référence interne. Ne pas l'envoyer telle quelle au client.
# To-Spec — v1.0
Package : Starter
Date de livraison : [date]
Statut : En test

## 1. En une phrase
Transforme une discussion en spec écrite, structurée et prête à servir de
document de devis.

## 2. Problème qu'il résout
Après un discovery call, tout est dans la conversation — rien n'est écrit.
Le client n'a pas de document à valider, l'agence n'a pas de périmètre
fermé. To-spec fige la discussion en spec : objectif, périmètre, user
stories, décisions d'implémentation, décisions de test.

## 3. Quand l'utiliser
- Après un discovery call (grill-me / interview-me)
- Avant d'envoyer un devis
- Avant de planifier les tâches de développement

## 4. Quand ne PAS l'utiliser
- Avant d'avoir assez discuté (il synthétise, il n'interviewe pas)
- Pour des micro-changements sans ambiguïté

## 5. Comment l'utiliser (prompt exact)
Copiez-collez ceci dans Claude (ou Kimi) :
---
Agent : j'utilise le skill to-spec. Synthétise notre discussion en spec
avec le template officiel : problem statement, solution, user stories
(longues et numérotées), implementation decisions (sans chemins de
fichiers), testing decisions. Publie-la dans specs/<client>.md.
---

## 6. Exemple concret
Après le call "restaurant", la spec contient :
- Problem statement : "Le restaurateur perd des réservations hors horaires
  d'ouverture."
- Solution : "Un site 1 page + widget de réservation en ligne + menu QR."
- User stories : "En tant que client, je veux réserver en ligne, pour être
  sûr d'avoir une table."
- Implementation decisions : widget booking + endpoint /booking + i18n.
- Testing decisions : seams = endpoint /booking + rendu du widget.

## 7. Résultat attendu
Un document de spec complet, structuré, validé par le client = le document
de devis.

## 8. Test d'acceptation (vous validez)
Relancez le skill après un call réel. Vérifiez que le client reconnaît SA
discussion dans la spec, et que le devis en découle sans ambiguïté.

## 9. Dépendances
Pré-requis : une discussion préalable (grill-me / interview-me).
Skill complémentaire : planning-and-task-breakdown (découper la spec en
tâches).

## 10. Notes / Limitations
- Ne PAS interviewer : il synthétise la discussion EXISTANTE.
- Les user stories doivent être LONGUES et couvrir tous les aspects.
- Pas de chemins de fichiers dans les décisions (ils changent vite).
