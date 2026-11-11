# UNDERCOVER_SHOWROOM — préparation mise en production

Cette préparation conserve strictement le design et les contenus validés. Aucun contenu événementiel n'est ajouté ou modifié.

## État au 09 novembre 2026

### 1. Hébergement public HTTPS
- **Déjà configuré :** Dockerfile + configuration Render ; l'application écoute le port `PORT` et le déploiement prévoit un disque persistant.
- **À fournir :** compte d'hébergement et domaine public/DNS.
- **Prêt à tester :** dès que le service de préproduction est créé. Render fournit TLS géré et redirige HTTP vers HTTPS sur les domaines configurés. citeturn971342search0turn971342search1

### 2. Base de données persistante
- **Déjà configuré :** l'application peut écrire sa base SQLite sous `DATA_ROOT`; la configuration Render prévoit `/var/data` sur disque persistant.
- **À fournir :** création/activation du service et du disque persistant. Le prototype ne doit pas être lancé sur un filesystem éphémère.
- **Prêt à tester :** création de demande → preuve → validation → billet, puis redémarrage du service et vérification de la persistance. Render indique qu'un disque persistant conserve les changements du filesystem entre redéploiements/redémarrages ; il est attaché à une seule instance. citeturn396962search3

### 3. Authentification sécurisée de l'administration
- **Déjà configuré :** la préparation remplace la session mémoire de démonstration par des sessions signées à durée limitée, cookies `HttpOnly`/`SameSite=Strict` et `Secure` en HTTPS ; le mot de passe de production est prévu sous forme de hash scrypt.
- **À fournir :** définir le mot de passe administrateur définitif et générer son hash ; définir `ADMIN_SESSION_SECRET`.
- **Prêt à tester :** connexion admin, expiration de session, refus sans session, protection CSRF des actions administratives.

### 4. Stockage sécurisé des preuves et billets
- **Déjà configuré :** séparation des données dans `DATA_ROOT`, protection de l'accès aux preuves par l'administration et protection de l'accès direct aux billets par l'administration dans la préparation.
- **À fournir :** valider le choix de stockage. Pour la production, un bucket privé S3-compatible (par exemple Cloudflare R2) est préférable si l'on veut découpler les fichiers du serveur ; les clés doivent être limitées au bucket. R2 prend en charge les API S3 et les URLs présignées temporaires. citeturn747905search0turn747905search2
- **Prêt à tester :** upload image/PDF, consultation admin, génération PDF/QR, redémarrage, restauration et vérification qu'aucune preuve n'est publiquement accessible.

### 5. SMTP
- **Déjà configuré :** adaptateur SMTP de l'application + variables de configuration.
- **À fournir :** compte SMTP, domaine expéditeur vérifié, identifiant SMTP, clé/mot de passe SMTP et adresse `From`. Brevo documente notamment le relais SMTP sur le port 587/STARTTLS et l'utilisation d'une clé SMTP. citeturn971342search6
- **Prêt à tester :** billet validé → e-mail réel avec PDF en pièce jointe.

### 6. WhatsApp Cloud API
- **Déjà configuré :** adaptateur d'envoi et variables `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_GRAPH_VERSION`.
- **À fournir :** configuration Meta/WhatsApp Business, numéro, token d'accès et identifiant du numéro. Le canal devra être testé avec un numéro autorisé avant activation commerciale.
- **Prêt à tester :** billet validé → envoi réel du PDF sur WhatsApp.

### 7. Test complet téléphone + ordinateur
- **Déjà configuré :** responsive CSS et parcours HTTP fonctionnels localement ; le rapport précédent précise qu'un test interactif Chromium sur localhost n'avait pas pu être validé dans cet environnement.
- **À fournir :** URL HTTPS de préproduction et accès à un téléphone réel + un ordinateur réel.
- **Prêt à tester :** après validation des étapes 1 à 6.

## Blocage volontaire de mise en production

La mise en production reste volontairement bloquée tant que les points critiques ne sont pas validés : HTTPS public, stockage persistant, authentification admin sécurisée, protection des preuves/billets, SMTP, WhatsApp si activé, puis tests réels téléphone/ordinateur.

## Contenus verrouillés

- UNDERCOVER_SHOWROOM
- 04 décembre 2026
- LE FUN CLUB · Diego-Suarez
- Public 5 000 Ar
- VIP 20 000 Ar
- Table 10 000 Ar
- Orange Money : +261 32 61 39 215
- programme et partenaires validés

Aucun partenaire retiré ne doit être réintroduit.
