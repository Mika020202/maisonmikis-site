#!/usr/bin/env python3
"""
Ajoute un nouvel article au site Actualités de maisonmikis.fr.

Usage :
    python3 add_article.py nouvel_article.json

Le fichier JSON d'entrée doit contenir :
{
  "slug": "mon-nouvel-article",
  "title": "Titre affiché (h1, cartes, breadcrumb)",
  "page_title": "Titre affiché (balise <title>) — en général 'Titre | Maison Mikis'",
  "meta_description": "Description meta (~150-160 caractères)",
  "excerpt": "Phrase courte affichée sur la carte (grille + à lire aussi)",
  "category": "sante-visuelle",   // doit exister dans CATEGORY_ORDER de lib_articles.py
  "image": "/images/actualites/mon-image.jpg",
  "image_alt": "Texte alternatif descriptif",
  "date_iso": "2026-08-03",
  "body_html": "<h2>...</h2><p>...</p>..."   // corps de l'article, sans le H1/hero (déjà généré)
}

Ce script :
1. Vérifie que le slug n'existe pas déjà (jamais d'écrasement silencieux).
2. Insère le nouvel article en tête de la liste maître (scripts/articles.json)
   — donc en tête de la grille Actualités (le plus récent en premier).
3. Régénère la grille de actualites.html.
4. Régénère la page dédiée du nouvel article.
5. Régénère la section "à lire aussi" de TOUS les articles existants
   (la rotation change dès qu'un article est ajouté — piège documenté du 26/07/2026).
6. Ajoute l'URL au sitemap.xml.
Ne fait AUCUN git commit / push — ça reste une étape manuelle explicite ensuite,
pour garder un contrôle humain sur ce qui part réellement en production.
"""
import sys
import json
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_articles as lib

CATEGORY_ACCENTS = {
    "sante-visuelle": ("--accent:var(--wood);--accent-bg:rgba(185,138,94,0.16);", "Santé visuelle"),
    "sante-auditive": ("--accent:var(--terracotta);--accent-bg:rgba(193,101,59,0.12);", "Santé auditive"),
    "mode-lunettes": ("--accent:var(--sage);--accent-bg:rgba(138,148,131,0.18);", "Mode & tendances"),
    "tech-verres": ("--accent:var(--terracotta-dark);--accent-bg:rgba(163,79,44,0.14);", "Technologies verres"),
    "tech-lentilles": ("--accent:var(--wood-dark);--accent-bg:rgba(140,98,57,0.16);", "Technologies lentilles"),
}


def _fill_category_accents():
    """Complète CATEGORY_ACCENTS pour les catégories restantes en le lisant
    depuis un article existant de chaque catégorie, pour ne jamais inventer
    une couleur qui n'existe pas déjà dans le site."""
    articles = lib.load_articles()
    for a in articles:
        if a["category"] not in CATEGORY_ACCENTS:
            CATEGORY_ACCENTS[a["category"]] = (a["accent_style"], a["category_label"])
    return CATEGORY_ACCENTS


def add_article(new_article):
    articles = lib.load_articles()
    existing_slugs = {a["slug"] for a in articles}
    if new_article["slug"] in existing_slugs:
        raise ValueError(
            f"Le slug '{new_article['slug']}' existe déjà — choisir un autre slug "
            "ou traiter ceci comme une mise à jour explicite, pas un ajout."
        )

    accents = _fill_category_accents()
    if new_article["category"] not in accents:
        raise ValueError(
            f"Catégorie inconnue : {new_article['category']}. "
            f"Catégories valides : {sorted(accents.keys())}"
        )
    accent_style, category_label = accents[new_article["category"]]

    entry = {
        "slug": new_article["slug"],
        "category": new_article["category"],
        "image": new_article["image"],
        "image_alt": new_article["image_alt"],
        "accent_style": accent_style,
        "category_label": category_label,
        "title": new_article["title"],
        "excerpt": new_article["excerpt"],
        "date_display": lib.date_display_from_iso(new_article["date_iso"]),
        "date_iso": new_article["date_iso"],
        "meta_description": new_article["meta_description"],
        "page_title": new_article["page_title"],
    }

    # 1. Insertion en tête (le plus récent en premier dans la grille)
    articles.insert(0, entry)

    # 2. Grille de actualites.html
    lib.rewrite_actualites_grid(articles)

    # 3. Page dédiée du nouvel article (idx = 0 puisqu'on vient de l'insérer en tête)
    page_html = lib.render_article_page(entry, new_article["body_html"], articles, 0)
    out_path = os.path.join(lib.ARTICLES_DIR, f"{entry['slug']}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page_html)

    # 4. Rotation "à lire aussi" sur TOUS les articles (y compris le nouveau, déjà fait ci-dessus,
    #    on le refait ici aussi par simplicité/cohérence — coût négligeable)
    for i, a in enumerate(articles):
        lib.rewrite_related_section(a["slug"], articles, i)

    # 5. Sitemap
    lib.sitemap_add_url(entry["slug"], entry["date_iso"])

    # 6. Sauvegarde de la liste maître
    lib.save_articles(articles)

    print(f"OK — article '{entry['slug']}' ajouté. Total articles : {len(articles)}")
    return entry


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 add_article.py nouvel_article.json")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    add_article(data)
