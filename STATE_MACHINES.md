# STATE_MACHINES.md

Documentation seulement : aucun code n'est modifié par ce fichier.
Écrit d'après le commit `2672bcd`. Les numéros de ligne peuvent bouger : cherchez le texte cité.

Trois machines à états cachées sont décrites ici. Chacune a : les états, les transitions, ce que voit le client, et les points de risque.

---

## 1. Commande vidéo payée (VIDEOCREATOR)

Fichier : `server/payments.js`
Stockage : mémoire du serveur seulement (`const orders = new Map()`). Un redémarrage efface toutes les commandes.

### États internes (champ `order.status`)

| État | Sens |
|---|---|
| `awaiting_payment` | Commande créée, carte pas encore autorisée |
| `submitting` | Carte autorisée, envoi à Agnes en cours (avec nouvelles tentatives) |
| `generating` | Agnes fabrique la vidéo, le serveur la suit toutes les 5 s |
| `completed` | Vidéo prête. Le paiement n'est capturé que si `order.captured` vaut `true` |
| `failed` | Échec. L'autorisation sur la carte est annulée (sauf échec de capture) |
| `expired` | Pas payée dans l'heure |

Drapeau caché : `order.captured` (vrai quand le paiement est encaissé).

### Transitions

| De | Vers | Déclencheur | Où |
|---|---|---|---|
| (création) | `awaiting_payment` | Le client envoie fichiers + prompt | `createOrderHandler` |
| `awaiting_payment` | `submitting` | Webhook Stripe `payment_intent.amount_capturable_updated`, montant correct | `handleAuthorized` |
| `awaiting_payment` | `failed` (`amount_mismatch`) | Montant ou devise différents du prix attendu | `handleAuthorized` |
| `awaiting_payment` | `expired` | Plus d'1 h depuis la création | `tick` |
| `submitting` | `generating` | Agnes accepte la demande | `submitWithRetries` |
| `submitting` | `failed` (`file_processing_failed`) | Erreur de préparation des fichiers | `submitWithRetries` |
| `submitting` | `failed` (`queue_full` ou `agnes_error`) | Agnes refuse (6 essais max, 20 s entre chaque pour file pleine) | `submitWithRetries` |
| `generating` | `completed` | Agnes répond `completed` avec une URL, puis tentative de capture | `pollGenerating` |
| `generating` | `failed` (`no_video_url`) | Agnes dit terminé mais sans URL | `pollGenerating` |
| `generating` | `failed` (`generation_failed`) | Agnes répond `failed` | `pollGenerating` |
| `generating` | `failed` (`timeout`) | Plus de 20 min de génération | `pollGenerating` |
| `completed` | `completed` + `captured = true` | Capture Stripe réussie | `tryCapture` |
| `completed` | `failed` (`payment_capture_failed`) | 20 échecs de capture | `tryCapture` |
| `completed`, `failed`, `expired` | supprimé | Plus de 24 h depuis la création | `tick` |

Cas spéciaux (aucun changement d'état) :
- Webhook en double : ignoré si l'état n'est plus `awaiting_payment`.
- Autorisation reçue pour une commande inconnue ou expirée : l'autorisation est annulée.
- Webhook sans `orderId` : ignoré (autre produit).

### Ce que voit le client (`getOrderHandler`)

| État interne | Statut envoyé au client |
|---|---|
| `awaiting_payment` | `awaiting_payment` |
| `expired` | `expired` |
| `failed` | `failed` (avec message FR/EN/NL) |
| `completed` et `captured` | `completed` (progression 100, avec `videoUrl`) |
| tout le reste (`submitting`, `generating`, `completed` non capturé) | `processing` (progression plafonnée à 99) |

Conséquence : le client ne voit jamais `submitting`, et une vidéo prête mais non encaissée reste « processing ».

### Points de risque

- Redémarrage du serveur : les commandes disparaissent. Une carte déjà autorisée n'est ni capturée ni annulée explicitement (elle expire côté Stripe).
- `submitting` n'a pas de limite de temps dans `tick` (seuls `awaiting_payment`, `generating` et `completed` non capturé sont traités).
- L'échec de capture ne passe pas par `failOrder` : l'état passe à `failed` sans nettoyage commun.

---

## 2. Tâche vidéo du Studio Marketing (abonnés)

Fichier : `server/marketing-studio.js`
Stockage : en mémoire (`jobs`) pour le suivi, et Supabase (`marketing_videos.statut`) pour l'historique.
Prérequis : abonné avec `statut = actif` et jeton non expiré (`getSubscriber`).

### États (aucun champ unique : ils se déduisent de plusieurs endroits)

| État | Comment le reconnaître |
|---|---|
| Quota réservé | `changeUsage(+1)` fait, avant l'appel à Agnes |
| En cours | Entrée dans `jobs` avec `refunded: false`, ligne dans `marketing_videos` |
| Terminée | `jobs.delete`, `statut = termine`, `video_url` enregistrée |
| Échec remboursé | `refunded = true`, `statut = echec`, quota rendu (`changeUsage(-1)`) |

### Transitions

| De | Vers | Déclencheur |
|---|---|---|
| (rien) | Quota réservé | `POST /api/marketing/generate`, vérifications passées |
| Quota réservé | (rien) | Quota épuisé (`quota_exhausted`) ou erreur Agnes : le quota est rendu (`giveBack`) |
| Quota réservé | En cours | Agnes renvoie un `videoId` |
| En cours | Terminée | `GET /api/marketing/status` : Agnes répond `completed`, `succeeded` ou `done`, avec URL |
| En cours | Échec remboursé | Agnes répond `failed`, `error` ou `cancelled` |
| En cours | Échec remboursé | Statut Agnes terminé mais sans URL (`no_url`) |
| En cours | Échec remboursé | Plus de 12 min depuis la création (`timeout`) |
| En cours (après redémarrage) | Échec remboursé | Agnes répond `failed`, `error`, `cancelled`, ou terminé sans URL : le remboursement se fait depuis la table `marketing_videos` (`refundFromDatabase`), une seule fois, et seulement pour le propriétaire de la vidéo |
| En cours | En cours | Autre statut, ou erreur réseau : le client reçoit `processing`, progression 0 |
| `jobs` | supprimé | Plus d'1 h (nettoyage toutes les 10 min) |

### Points de risque

- Après un redémarrage du serveur, `jobs` est vide. Le remboursement passe alors par `marketing_videos` : il est fait une seule fois (le statut ne change que si personne ne l'a changé entre-temps) et jamais pour une vidéo déjà `termine` ou `echec`. Limites restantes : le contrôle de 12 min est sauté (il dépend de `jobs`), et si la vidéo n'a pas pu être enregistrée dans `marketing_videos` à la création, aucun remboursement n'est possible.
- Trois mots différents pour « terminé » (`completed`, `succeeded`, `done`) sont acceptés ici, alors que `server/payments.js` n'accepte que `completed`.
- `marketing_videos.statut` n'a que deux valeurs écrites par ce code (`termine`, `echec`). La valeur de départ vient de la base, elle n'est pas visible dans ce dépôt.

---

## 3. File d'attente de la page Studio Marketing (navigateur)

Fichier : `studio/marketing/index.html` (objet `state`, puis `startGeneration`, `createTaskOnly`, `pollTaskAndDisplay`).
Stockage : mémoire de la page. Un rechargement efface tout.

### États d'un élément de la file (`item.status`)

| État | Affichage |
|---|---|
| `pending` | « En file » |
| `creating` | « Préparation… » |
| `processing` | progression |
| `done` | « Terminé » |
| `failed` | « Échec » |
| `cancelled` | « Arrêté » (affiché en grisé comme `pending`) |

### Drapeaux globaux (`state`)

`isRunning`, `stopRequested`, `completed` (compteur), `failed` (compteur).

### Transitions

| De | Vers | Déclencheur |
|---|---|---|
| (création de la file) | `pending` | `startGeneration`, un élément par image |
| `pending` | `creating` | `createTaskOnly`, une image toutes les 62 s minimum |
| `creating` | `processing` | Le serveur renvoie un `videoId` |
| `creating` | `failed` | Erreur de création : compteur `state.failed` + 1 |
| `pending` ou `creating` | `cancelled` | Arrêt demandé : la requête n'est pas envoyée au serveur. Le compteur `state.failed` n'augmente pas, mais l'élément compte comme terminé dans l'indicateur |
| `processing` | `done` | Statut `completed`, `succeeded` ou `done` avec URL : compteur `state.completed` + 1 |
| `processing` | `failed` | Statut d'échec, délai dépassé (100 essais de 8 s) ou erreur : compteur `state.failed` + 1 |

Arrêt (`stopGeneration`) :
- Met `stopRequested = true` si `isRunning`.
- La boucle d'envoi s'arrête. Les éléments pas encore envoyés (`pending`, ou `creating` si l'arrêt tombe pendant une nouvelle tentative après une erreur 429 ou 503) passent à `cancelled`.
- Seule la création peut être interrompue : le suivi (`Polling`) ne lève jamais « Arrêt demandé ».
- Les vidéos déjà envoyées continuent d'être suivies jusqu'au bout.
- À la fin : `isRunning = false` et `stopRequested = false`.

### Points de risque

- Avant la correction, les éléments non envoyés restaient `pending` (« En file ») ou bloqués sur `creating` (« Préparation… ») après un arrêt, et l'indicateur n'affichait jamais « Terminé ». L'état `cancelled` corrige cela.
- Code inutile : dans `pollTaskAndDisplay`, la branche qui traite « Arrêt demandé » (statut `failed`, texte « Arrêté ») n'est jamais atteinte, car seul `apiFetch` avec l'étiquette `Création` lève cette erreur. Elle a été laissée telle quelle.
- Plusieurs drapeaux séparés (`isRunning`, `stopRequested`, `isLoadingImages`) décrivent en réalité une seule phase de la page.
