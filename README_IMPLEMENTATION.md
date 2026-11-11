# UNDERCOVER_SHOWROOM — implémentation Supabase / préproduction

Cette version conserve le HTML/CSS et les contenus validés. Le changement porte sur la couche de persistance et le stockage : l'application utilise Supabase en production et un store SQLite local uniquement pour les tests déterministes.

## Correction du statut `pending`

L'ancienne logique ne doit plus envoyer la valeur `pending` à `ticket_requests.ticket_status`.

Lors de la création d'une demande, l'application **n'envoie volontairement pas `ticket_status`** : la valeur par défaut définie par la base reste donc l'autorité pour le statut initial. Le code utilise ensuite les quatre libellés validés par le workflow :

- `En attente`
- `Paiement à vérifier`
- `Validé`
- `Refusé`

Les valeurs sont configurables par variables d'environnement sans modification de table ni suppression de données.

## Parcours implémenté

1. Formulaire Public / VIP.
2. Référence unique `UCS-XXXXXXXX`.
3. Insert dans `ticket_requests`.
4. Statut initial laissé au défaut de la base — aucun `pending` envoyé.
5. Instructions Orange Money +261 32 61 39 215.
6. Upload de preuve image/PDF.
7. Enregistrement de `payment_proof_url` dans `ticket_requests`.
8. Interface administrateur protégée.
9. Validation / refus.
10. Génération PDF + QR.
11. Upload du billet et du QR dans un bucket Supabase privé et enregistrement de `ticket_url` / `qr_url`.
12. Envoi e-mail ou WhatsApp selon le choix.
13. Formulaire de réservation connecté à `table_reservations`.

## Stockage

Deux buckets privés sont utilisés :

- `undercover-proofs`
- `undercover-tickets`

L'application les crée de façon idempotente au démarrage si nécessaire. Les preuves et billets ne sont jamais exposés comme fichiers publics. Les liens signés sont temporaires lorsqu'un accès fichier est nécessaire.

## Secrets

Ne jamais committer :

- `SUPABASE_SERVICE_ROLE_KEY`
- `ADMIN_PASSWORD_HASH`
- `ADMIN_SESSION_SECRET`
- `SMTP_PASSWORD`
- `WHATSAPP_TOKEN`

Les variables sont fournies par l'environnement d'hébergement.

## Tests réalisés

### Tests locaux déterministes

- création Public : PASS
- calcul du montant Public : PASS
- création VIP : PASS
- calcul du montant VIP : PASS
- référence unique : PASS
- dépôt de preuve : PASS
- statut `Paiement à vérifier` : PASS
- connexion admin : PASS
- validation : PASS
- génération PDF : PASS
- QR inclus dans le PDF : PASS
- refus : PASS
- réservation de table : PASS
- contrôle de logique Supabase : PASS — `pending` n'est jamais envoyé lors de l'insert initial.

### Limite volontaire

Le projet Supabase réel ne peut pas être interrogé depuis cet environnement sans sa clé de service. Le code est donc testé localement de bout en bout et la construction du payload PostgREST est testée séparément. Aucun secret n'a été créé ou enregistré dans le dépôt.

## Déploiement

Le service doit être déployé en préproduction HTTPS avec les variables de `.env.example`. La production publique reste bloquée tant que les tests réels HTTPS, persistance, SMTP, WhatsApp et téléphone/ordinateur ne sont pas validés.
