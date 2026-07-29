# PIPELINE.md — Veille & publication automatique Actualités, Maison Mikis

Reconstruit le 28/07/2026 après l'incident du 27/07/2026 (voir section dédiée en bas).
Ce fichier vit dans le dépôt Git (`Mika020202/maisonmikis-site`), pas dans une session
Claude éphémère — c'est la leçon de l'incident : tout ce qui doit survivre d'une
semaine à l'autre doit être ici, jamais uniquement dans `/home/claude/`.

## Objectif
Publier 1 à 2 articles par semaine sur `actualites.html`, rédigés à partir de vraies
nouveautés repérées chez les sources listées dans `sources.json` — jamais une copie
verbatim, toujours reformulé, jamais un article inventé de toutes pièces sans base
réelle.

## Règles éditoriales (ne jamais déroger)
1. **Jamais de copie verbatim** d'une source — toujours reformulé avec des mots
   différents. Citation courte (<15 mots) autorisée occasionnellement, jamais plus
   d'une par source.
2. **Encart source en fin d'article** : `<div class="article-source-note">Contenu
   rédigé par l'équipe Maison Mikis à partir de sources professionnelles vérifiées
   (fabricants, presse spécialisée, autorités de santé), mis à jour en [mois année].
   </div>` — pas de lien sortant vers les concurrents/sources.
3. **Les nouveaux articles ne doivent JAMAIS écraser les anciens.** Toujours ajouter
   à la liste existante via `scripts/add_article.py`, jamais modifier/supprimer un
   article existant sauf demande explicite du client (préférence confirmée le
   27/07/2026).
4. **Maximum 2 publications par semaine** au total, toutes thématiques confondues
   (voir `state.json` → `max_publications_per_week`).
5. **Mapping thème → image par défaut** : si aucune nouvelle photo n'est fournie,
   réutiliser une image déjà existante sur le site, cohérente avec le thème :
   - Santé visuelle → `images/sante/*` ou `images/actualites/*`
   - Santé auditive → `images/audition/*`
   - Mode & tendances → `images/actualites/tendances-montures.jpg` ou `images/marquee/*`
   - Technologies verres → `images/actualites/tech-verres.jpg` ou `images/conseils/*`
   - Technologies lentilles → `images/actualites/tech-lentilles.jpg` ou `images/conseils/*`
   - Remboursements → `images/conseils/*`
   - Vie de la boutique → `images/accueil/*`
   - Enfant → `images/sante/*`
   Ne jamais sourcer une nouvelle photo automatiquement sans validation — sauf si le
   client en a fourni une nouvelle explicitement.

## Piège déjà rencontré à ne jamais reproduire
Les cartes "à lire aussi" sont calculées par rotation sur la position de chaque
article dans la liste (`ARTICLES[(idx+i) % len(ARTICLES)]` dans l'ancien `build.py`,
même logique dans `scripts/lib_articles.py`). **Ajouter un article change la
position relative de tous les autres** → `scripts/add_article.py` régénère déjà
automatiquement la section "à lire aussi" de TOUS les articles à chaque ajout.
Ne jamais contourner ce script en éditant un fichier HTML à la main.

## Procédure pas à pas pour publier un nouvel article

1. `git clone https://github.com/Mika020202/maisonmikis-site.git` (ou `git pull` si
   déjà cloné) — toujours repartir d'un état à jour.
2. Charger `scripts/state.json` : vérifier `baseline_done`.
   - Si `false` : c'est la toute première exécution. **Ne publier aucun article.**
     Parcourir chaque source de `sources.json`, noter dans
     `state.json.last_seen_by_source` le dernier article/communiqué visible à ce
     jour (ou une valeur qui indique "vérifié à telle date" si la source n'a pas
     d'ID stable). Passer `baseline_done` à `true`. Commit + push. Fin de
     l'exécution — pas d'article cette semaine.
3. Si `baseline_done` est `true` : pour chaque source (dans l'ordre de
   `sources.json`, en tenant compte de la rotation des 19 marques pour
   "mode-lunettes" via `mode_lunettes_brand_rotation`), vérifier s'il existe une
   vraie nouveauté publiée depuis `last_seen_by_source[source]`.
4. Dès qu'une vraie nouveauté est trouvée (max 2 par semaine, cf règle 4) :
   a. Rédiger l'article : titre, `page_title`, `meta_description` (~150-160
      caractères), `excerpt` (~1 phrase courte pour les cartes), corps `body_html`
      (structure `<h2>...</h2><p>...</p>`, ton identique aux 24 articles existants
      — factuel, accessible, jamais promotionnel à l'excès).
   b. Choisir un `slug` unique (vérifier qu'il n'existe pas déjà dans
      `scripts/articles.json`), une `category` valide, une `date_iso` (date du
      jour de publication), une image selon le mapping ci-dessus.
   c. Écrire ces champs dans un fichier JSON temporaire et lancer :
      `python3 scripts/add_article.py nouvel_article.json`
   d. Vérifier que ça s'est bien passé (le script échoue explicitement si le slug
      existe déjà ou si la catégorie est invalide — ne jamais forcer autrement).
5. Mettre à jour `state.json` : `last_seen_by_source` pour la source utilisée,
   `used_slugs` (ajouter le nouveau slug), `publication_log` (ajouter une entrée
   avec slug, date, source d'origine), et faire avancer
   `mode_lunettes_brand_rotation.next_index` si une marque a été traitée.
6. `git add -A && git commit -m "Actualités : ajout de [titre]" && git push`.
7. Envoyer un email de notification au client (voir "Notification" ci-dessous).
8. Format attendu du message de fin d'exécution (sert de corps à l'email) :
   > Nouvel article publié sur maisonmikis.fr : "[titre]" ([catégorie]).
   > URL : https://www.maisonmikis.fr/actualites/[slug].html
   > Source d'inspiration : [nom de la source, jamais de lien direct vers un concurrent dans l'email si non pertinent]

## Notification
Le client a demandé un **email à chaque publication** (informatif, pas de validation
préalable requise), **jamais de push**. Voir la section "Mode d'exécution" ci-dessous
pour le mécanisme technique d'envoi selon l'option retenue.

## Mode d'exécution — décidé le 28/07/2026 : GitHub Actions
Le client a choisi l'option GitHub Actions (voir échange du 28/07/2026) plutôt
qu'une tâche planifiée Claude, précisément pour éviter de reproduire le problème de
persistance qui a causé l'incident du 27/07/2026. Le workflow tourne directement
sur l'infrastructure GitHub, indépendant de toute session Claude ou du PC du client.

**Fichiers concernés :**
- `.github/workflows/actualites-weekly.yml` — déclenche l'exécution tous les lundis
  07:00 UTC (aussi déclenchable manuellement depuis l'onglet "Actions" du dépôt,
  bouton "Run workflow").
- `scripts/weekly_run.py` — appelle l'API Anthropic (avec l'outil `web_search`)
  pour vérifier les sources et rédiger un article si une vraie nouveauté existe,
  puis publie via `add_article.py`.

**Mise en service (à faire une seule fois) :**
1. Créer une clé API sur `console.anthropic.com` (compte séparé de Claude.ai).
2. Dans le dépôt GitHub → Settings → Secrets and variables → Actions → "New
   repository secret" → nom `ANTHROPIC_API_KEY`, valeur = la clé créée à l'étape 1.
3. Aucune autre configuration nécessaire : le push se fait via le jeton
   `GITHUB_TOKEN` fourni automatiquement par Actions à chaque exécution (scope
   limité à ce seul dépôt, pas de jeton personnel à gérer ni à renouveler).

**Notification au client :** pas de service d'envoi d'email dédié configuré (aurait
nécessité des identifiants SMTP supplémentaires en secret). À la place, le client
doit activer, une seule fois, la notification native de GitHub pour les workflows :
GitHub → photo de profil → Settings → Notifications → section "Actions" → cocher
"Send notifications for failed workflow runs only" ou, pour être notifié à CHAQUE
exécution (succès compris, cohérent avec la demande initiale), configurer plutôt le
"Watch" du dépôt sur "All Activity" (bouton "Watch" en haut de la page du dépôt).
Si le client veut un email plus détaillé (avec le titre de l'article directement
dans le corps du message plutôt qu'un simple lien vers le run), ça reste possible
en ajoutant une étape d'envoi SMTP au workflow — non fait par défaut pour limiter le
nombre de secrets à gérer.

**Premier test recommandé :** déclencher manuellement le workflow une fois
("Run workflow" dans l'onglet Actions) après avoir ajouté le secret, pour vérifier
que la passe baseline s'exécute sans erreur avant d'attendre le premier lundi.

## ⚠️ Incident du 27/07/2026 (pour mémoire)
La première exécution planifiée s'est lancée dans une session cloud neuve et vide :
aucun fichier du 26/07/2026 (`build.py`, images locales, ancien pipeline) n'était
présent. Cause : chaque session tourne dans un conteneur éphémère, jamais partagé
d'une session à l'autre. Conséquence : aucun article publié cette semaine-là, mais
aucune action à l'aveugle sur le site en ligne non plus (aucune régression).
Leçon retenue : tout ce qui doit persister doit vivre dans le dépôt Git.
