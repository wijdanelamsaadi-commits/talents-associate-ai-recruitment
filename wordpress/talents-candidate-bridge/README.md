# Talents Candidate Bridge

Plugin WordPress autonome pour afficher les offres publiques Talents Associate et envoyer les candidatures vers l'API FastAPI.

## Installation

1. Installer le ZIP `talents-candidate-bridge.zip` depuis **Extensions > Ajouter > Téléverser une extension**.
2. Activer l'extension **Talents Candidate Bridge**.
3. Ouvrir **Réglages > Talents Candidate Bridge**.

## Configuration

Renseigner :

- URL API : `https://api.talentsag.ma/api/portal/applications`
- Clé API WordPress : la clé sécurisée fournie côté backend

La clé API reste côté serveur WordPress. Elle n'est jamais envoyée au navigateur, affichée dans le HTML, transmise dans l'URL ou écrite dans les logs.

## Pages WordPress à créer

Créer le menu parent **Opportunités de carrières** sans lien cliquable, puis ajouter les pages suivantes.

### Page "Opportunités en cours"

Shortcode :

```text
[talents_jobs_list]
```

Cette page récupère les offres ouvertes depuis :

```text
GET https://api.talentsag.ma/api/portal/jobs
```

Elle affiche les filtres : recherche par mot-clé, localisation, type de contrat, niveau d'expérience.

### Page "Détail de l'offre"

Shortcode :

```text
[talents_job_detail]
```

Le plugin résout automatiquement la page par son slug WordPress `detail-offre`, puis ajoute `job_id` avec `add_query_arg()`. Les liens fonctionnent donc avec les permaliens simples `?page_id=...` comme avec les permaliens personnalisés.

URL lisible recommandée si les permaliens personnalisés sont activés :

```text
/detail-offre/?job_id=UUID
```

Le shortcode valide strictement `job_id` et charge le détail depuis l'API. Aucun titre libre n'est accepté. La description est affichée sous le titre **Missions** et en liste à puces. Les compétences techniques sont affichées sous **Compétences techniques**, et les compétences comportementales `soft_skills` sont affichées sous **Compétences comportementales**. Si aucune compétence comportementale n'est renseignée, la section **Compétences comportementales** est masquée.

### Page "Postuler à l'offre"

Shortcode :

```text
[talents_job_apply]
```

Le plugin résout automatiquement la page par son slug WordPress `postuler-offre`, puis ajoute `job_id` avec `add_query_arg()`.

URL lisible recommandée si les permaliens personnalisés sont activés :

```text
/postuler-offre/?job_id=UUID
```

Le formulaire affiche l'offre sélectionnée. Le candidat ne peut pas choisir une autre offre depuis cette page. L'UUID exact est envoyé dans le champ multipart `opportunite`.

### Page "Candidature spontanée"

Shortcode inchangé :

```text
[talents_candidature_form]
```

Cette page conserve le formulaire existant, avec choix obligatoire d'une offre ouverte dans le champ **Opportunité**.

## Fonctionnement API

- Liste des offres : `GET https://api.talentsag.ma/api/portal/jobs`
- Détail d'une offre : `GET https://api.talentsag.ma/api/portal/jobs/{job_id}`
- Envoi candidature : `POST https://api.talentsag.ma/api/portal/applications`

Payload multipart envoyé :

- `opportunite` : UUID exact de l'offre
- `nom`
- `prenom`
- `email`
- `telephone`
- `ville`
- `message`
- `cv`

Le header `X-Talents-Api-Key` est ajouté uniquement côté serveur WordPress.

## Cache

Le plugin utilise un cache WordPress de 5 minutes pour :

- la liste des offres ;
- le détail des offres.

Le cache est renouvelé automatiquement après expiration.

## Validations

- UUID strict pour `job_id` et `opportunite`.
- Email valide.
- Champs obligatoires : opportunité, nom, prénom, email, ville, CV.
- CV PDF, DOC ou DOCX uniquement.
- Taille maximale : 5 Mo.
- Nonce WordPress.
- Protection contre double soumission.
- Aucun secret dans le JavaScript ou le HTML.

## Messages

- Succès : `Votre candidature a bien été reçue.`
- Aucune offre : `Aucune offre n'est disponible actuellement.`
- Offre absente ou invalide : `Cette offre n'est plus disponible.`
- API indisponible : message clair en français sans détail technique.

## Ancienne page WordPress

Le plugin ne supprime aucune page automatiquement.

Après validation des nouvelles pages, l'ancienne page :

```text
/formulaire-de-recrutement/
```

devra être retirée du menu puis mise en brouillon ou redirigée vers :

```text
/opportunites-en-cours/
```

## Test

1. Configurer l'URL API et la clé.
2. Cliquer sur **Tester la connexion** dans les réglages.
3. Ouvrir la page **Opportunités en cours**.
4. Vérifier les filtres et les cartes d'offres.
5. Ouvrir un détail via `Voir détails`.
6. Ouvrir le formulaire via `Postuler`.
7. Envoyer une candidature avec un CV PDF ou DOCX.
8. Vérifier dans la plateforme recruteur que la candidature est liée à la bonne offre.
9. Tester les erreurs : email invalide, CV absent, format interdit, job_id invalide, API indisponible.

## Retour arrière

1. Désactiver l'extension **Talents Candidate Bridge**.
2. Supprimer les shortcodes des pages si nécessaire.
3. Réactiver manuellement l'ancien mécanisme d'envoi par email uniquement si l'équipe décide de revenir à l'ancien flux.
