# UNDERCOVER_SHOWROOM — test report de l'implémentation Supabase

## Résultats

- Python compile : PASS
- Design HTML/CSS : inchangé par rapport à la version validée
- Contenus verrouillés : conservés
- Partner retiré : absent du package
- Insert initial Supabase : PASS au niveau du contrat applicatif — `ticket_status` n'est pas envoyé ; le défaut de la base reste autoritaire
- Valeur legacy `pending` : non envoyée
- Public : PASS en test local de bout en bout
- VIP : PASS en test local de bout en bout
- Référence unique : PASS
- Instructions Orange Money +261 32 61 39 215 : PASS
- Preuve image : PASS
- Preuve PDF : PASS
- `payment_proof_url` : PASS au niveau du store
- Admin sécurisé : PASS en test local
- Validation : PASS
- Refus : PASS
- PDF : PASS
- QR : PASS
- `ticket_url` / `qr_url` : PASS au niveau du store
- Réservation de table : PASS

## Limite externe

Le projet Supabase réel n'a pas été appelé depuis cet environnement, car sa clé de service n'est pas présente ici. Aucun secret n'a été demandé, copié ou écrit dans le package.

Le test local valide le parcours HTTP complet et le contrat de persistance Supabase sans recréer de table.

La validation réelle de préproduction reste à faire une fois l'application déployée avec les variables d'environnement Supabase déjà disponibles dans l'infrastructure.
