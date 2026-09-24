> ⚠️ **Ce skill est un outil INTERNEMENT utilisé par JCODE Agency.**  
> Le client ne reçoit pas "le skill interview-me" — il reçoit la **fiche de cadrage** que ce skill nous permet de produire.  
> Cette page est une référence interne. Ne pas l'envoyer telle quelle au client.
# Interview-Me — v1.0
Package : Starter
Date de livraison : [date]
Statut : En test

## 1. En une phrase
Transforme une demande vague en besoin réel, par un entretien une question
à la fois.

## 2. Problème qu'il résout
Quand un client (ou vous) demande "un site", "une app", "un dashboard",
on ne sait pas encore ce qui est VRAIMENT voulu. Le skill creuse jusqu'à
~95% de confiance AVANT d'écrire un plan, une spec ou un devis — là où
se joue la vraie qualité de la mission.

## 3. Quand l'utiliser
- Avant de deviser un projet client
- Quand une demande est vague ou conventionnelle ("je veux un site")
- Avant de créer un plan, une spec ou du code
- Avant un discovery call (préparation des questions)

## 4. Quand ne PAS l'utiliser
- Renommer une variable, corriger une typo
- Question d'information pure ("comment ça marche ?")
- Quand la demande est déjà claire et sans ambiguïté
- Quand le client demande explicitement la vitesse plutôt que la vérification

## 5. Comment l'utiliser (prompt exact)
Copiez-collez ceci dans Claude (ou Kimi) :
---
Agent : j'utilise le skill interview-me. Une question à la fois, avec ton
hypothèse + ton niveau de confiance (0-100%) à chaque question. Arrête
quand tu atteins ~95% de confiance sur le besoin réel.
---

## 6. Exemple concret
Demande : "je veux un site pour mon restaurant"
-> Après 8 questions : vrai besoin = réservation en ligne + menu QR,
   budget 800 EUR, public local, pas besoin d'e-commerce.
Résultat : le devis porte sur le Pro (999 EUR) avec Réservation Auto,
   pas sur un site e-commerce surdimensionné.

## 7. Résultat attendu
Une liste de questions posées + une synthèse du besoin réel (qui, pourquoi,
succès attendu, contrainte) + un niveau de confiance final.

## 8. Test d'acceptation (vous validez)
Relancez le skill sur un vrai client. Si après ~15 questions vous pouvez
prédire ses réponses, le skill fonctionne. Objectif : devis exact du
premier coup.

## 9. Dépendances
Aucune. Skill complémentaire : to-spec (transformer le résultat en
spec/devis écrit).

## 10. Notes / Limitations
- Interactif : nécessite une personne qui répond (pas en automatique).
- Le "want vs should want" : le client demande ce qu'il croit vouloir,
  pas ce dont il a besoin — le skill expose cet écart.
