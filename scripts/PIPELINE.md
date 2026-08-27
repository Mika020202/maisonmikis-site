# PIPELINE.md — Veille et publication automatique, Maison Mikis

Document de maintenance du depot `Mika020202/maisonmikis-site`.
**Reecrit le 27/08/2026.** La version precedente decrivait un pipeline qui
n'existait plus : elle renvoyait a `.github/workflows/actualites-weekly.yml` et a
`scripts/weekly_run.py`, tous deux supprimes. Si vous lisez une consigne qui ne
correspond pas aux fichiers presents, c'est ce document qui a tort : verifiez le
workflow, il fait foi.

## Ce qui tourne reellement aujourd'hui

Un seul workflow : `.github/workflows/publication.yml`. Il tourne sur les serveurs
GitHub — ni ordinateur allume, ni navigateur ouvert, ni session Claude en cours.

Deux passages par semaine, **lundi et jeudi** :
- `cron: '23 6 * * 1,4'` — 06h23 UTC (08h23 Paris en ete)
- `cron: '47 8 * * 1,4'` — rattrapage si le premier est reste dans la file d'attente
  de GitHub. La minute ronde ':00' est evitee volontairement : elle est saturee et
  provoquait des retards de plusieurs heures.

Le rattrapage ne consomme rien si le passage du matin a eu lieu : `veille.py` lit
`state.json.dernier_passage` et s'arrete immediatement.

## Chaine complete d'un passage

1. **Archive deposee** (facultatif) — un `.zip` pose a la racine du depot est
   decompresse, filtre par extension, range dans le depot, puis supprime.
2. **Veille** — `scripts/veille.py` interroge l'API Claude avec l'outil de
   recherche web, balaie les sources de `sources.json` sur 60 jours, et rédige un
   article **si et seulement si** un fait franchit le seuil editorial. Il n'ecrit
   qu'un fichier de donnees : `scripts/articles_auto.json`. **Aucune page HTML.**
3. **Generation** — `build.py` (racine du depot) est le **SEUL** generateur. Il
   reecrit toutes les pages, la feuille de style et le sitemap a partir du modele
   unique. Un article automatique passe donc par exactement le meme gabarit, le
   meme maillage interne et le meme JSON-LD qu'un article ecrit a la main.
4. **Enregistrement** — le workflow commit et pousse lui-meme. `veille.py` ne
   commit jamais, pour rester testable isolement.
5. **Mise en ligne** — miroir SFTP (repli FTPS) vers `/public` chez IONOS.

## Garde-fous a ne jamais retirer

- **Le miroir se fait SANS `--delete`.** Le workflow sait ajouter et remplacer des
  fichiers en ligne, il ne sait PAS en supprimer. Une erreur ne peut donc pas vider
  le site.
- **Moins de 30 pages HTML preparees = mise en ligne annulee.** Filet contre une
  generation partielle.
- **Aucun `.py` ne doit se trouver dans les fichiers publies** — verifie avant envoi.
- **Un slug deja utilise est refuse.** Jamais d'ecrasement d'un article existant.
- **Le controle qualite de `validate()` rejette l'article plutot que de publier du
  contenu hors norme** (longueur, balises interdites, sources non exploitables).
- **Le modele n'ecrit ni lien ni image.** Le maillage interne et les illustrations
  sont poses par le code, a partir de listes en dur : un lien casse est impossible.

## Secrets du depot (Settings → Secrets and variables → Actions)

| Secret | Role |
|---|---|
| `ANTHROPIC_API_KEY` | permet a la veille de rechercher et de rediger |
| `IONOS_HOST` | serveur SFTP de l'hebergement |
| `IONOS_USER` | identifiant technique SFTP (type `su123456`, PAS l'adresse e-mail) |
| `IONOS_PASSWORD` | mot de passe de l'acces SFTP, distinct du mot de passe IONOS |
| `IONOS_USER_ALT` | second acces SFTP, essaye si le premier echoue |

Aucun identifiant ne figure dans un fichier du depot. Le depot est public.

## Une semaine sans article n'est pas une panne

Le seuil editorial est volontairement severe (voir `CHARTE` et le prompt de
`run_weekly()` dans `veille.py`). Un passage peut se terminer sans rien publier :
c'est le comportement attendu. Ne relachez le seuil que si vous assumez des
articles moins solides.

Un **echec**, en revanche, est bruyant : depuis le 26/08/2026 le workflow s'arrete
en erreur si la veille tombe en panne, et GitHub previent le proprietaire du depot
par e-mail. Un voyant vert signifie desormais que la veille a reellement tourne.

## Les trois pannes du 27/08/2026 — a connaitre avant de toucher a l'API

Elles etaient empilees : chacune masquait la suivante. Symptome commun : plus aucun
article automatique depuis le 13/08/2026, alors que les passages s'affichaient en
vert.

1. **Modele retire.** `MODEL = "claude-sonnet-4-6"` n'existe plus → HTTP 400 a chaque
   appel. Remplace par `claude-sonnet-5`. **Verifiez cette valeur en premier** si la
   veille se remet a echouer : les identifiants de modele sont retires avec le temps.
2. **`stop_reason: "pause_turn"` non gere.** L'API interrompt d'elle-meme les tours
   de recherche longs et renvoie une reponse SANS texte final. Il faut lui renvoyer
   sa propre reponse, inchangee, pour qu'elle reprenne. Sans cela : erreur
   `Expecting value: line 1 column 1`.
3. **Appel trop long coupe par le reseau** (`Remote end closed connection without
   response` apres 9 minutes). Un appel non "streame" ne tient pas aussi longtemps.
   Corrige par `max_uses` sur l'outil de recherche (14 recherches par appel) et trois
   tentatives automatiques sur coupure.

Si vous devez un jour allonger fortement la recherche, la bonne reponse n'est pas
d'augmenter `max_uses` sans limite : c'est de passer l'appel en mode "streame", ou de
scinder la veille en deux appels (reperage, puis redaction).

## Fichiers du depot

| Fichier | Role |
|---|---|
| `.github/workflows/publication.yml` | la recette complete, fait foi |
| `build.py` (racine) | generateur unique du site |
| `scripts/veille.py` | veille + redaction, ecrit `articles_auto.json` |
| `scripts/sources.json` | sources professionnelles surveillees |
| `scripts/state.json` | memoire : slugs utilises, dernier passage, journal |
| `scripts/articles.json` | articles ecrits a la main |
| `scripts/articles_auto.json` | articles produits par la veille |
| `scripts/lib_articles.py` | fonctions partagees |
| `scripts/add_article.py` | ajout manuel — **non appele par le workflow** |
| `scripts/migrate_freshness_and_sort.py` | migration ponctuelle du 29/07/2026, ne plus relancer |

`add_article.py` et `migrate_freshness_and_sort.py` sont des outils manuels herites.
Ils ne participent a aucun passage automatique. A verifier avant tout usage : ils
datent d'une epoque ou les pages HTML etaient ecrites directement, alors que
`build.py` est desormais le seul generateur.

## Declenchements manuels (onglet Actions → Run workflow)

Quatre modes, utilisables depuis un telephone :
- **Remettre tout le site en ligne** — regenere et renvoie tout, sans veille.
- **Publication hebdomadaire (veille + mise en ligne)** — le passage complet.
- **Tester la connexion IONOS** — depose un fichier temoin.
- **Supprimer le fichier de test** — le retire.

## Tri par date et bandeau de fraicheur

La grille est triee par `date_iso` decroissant. Chaque page article affiche, **cote
navigateur**, un avertissement si l'article a plus de 6 mois (seuil
`FRESHNESS_THRESHOLD_MONTHS` dans `lib_articles.py`). Calcule a la visite : aucune
regeneration necessaire avec le temps.

## Incident du 27/07/2026 (pour memoire)

Le pipeline d'origine vivait dans une session cloud ephemere et a ete perdu.
Lecon retenue, toujours valable : **tout ce qui doit survivre d'une semaine a
l'autre vit dans ce depot**, jamais uniquement dans une session.
