#!/usr/bin/env python3
"""
Migration ponctuelle (29/07/2026) :
1. Trie articles.json + la grille actualites.html par date décroissante
   (au lieu de l'ordre d'insertion historique, qui mélangeait le lot de
   lancement du 26/07 et le backfill de janvier 2025 à avril 2026).
2. Ajoute l'attribut data-date-iso + le script de bandeau de fraîcheur
   ("cet article a plus de 6 mois...") sur les 24 pages existantes.
3. Régénère la rotation "à lire aussi" selon le nouvel ordre.

À exécuter une seule fois. Idempotent si besoin de le relancer (ne duplique
pas le bandeau JS si déjà présent).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_articles as lib


def add_date_attribute(slug, date_iso):
    path = os.path.join(lib.ARTICLES_DIR, f"{slug}.html")
    content = open(path, encoding="utf-8").read()
    if 'data-date-iso' in content:
        return False  # déjà migré
    new_content = content.replace(
        '<section class="article-prose story-block">',
        f'<section class="article-prose story-block" data-date-iso="{date_iso}">',
        1
    )
    if new_content == content:
        raise RuntimeError(f"Marqueur article-prose introuvable dans {slug}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


def inject_freshness_script(slug):
    path = os.path.join(lib.ARTICLES_DIR, f"{slug}.html")
    content = open(path, encoding="utf-8").read()
    if 'article-freshness-notice' in content:
        return False  # déjà migré
    pattern = re.compile(
        r"(<script>\n\n  document\.getElementById\('year'\).*?)(</script>)", re.S
    )
    m = pattern.search(content)
    if not m:
        raise RuntimeError(f"Bloc <script> introuvable dans {slug}.html")
    new_content = content[:m.start()] + m.group(1) + lib.FRESHNESS_JS + m.group(2) + content[m.end():]
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


def main():
    articles = lib.load_articles()
    print(f"Avant tri : {[a['slug'] for a in articles[:3]]} ...")
    articles = lib.sort_by_date_desc(articles)
    print(f"Après tri : {[a['slug'] for a in articles[:3]]} ...")

    # 1. Grille triée
    lib.rewrite_actualites_grid(articles)

    # 2. Attribut de date + script de fraîcheur sur chaque page
    n_date, n_script = 0, 0
    for a in articles:
        if add_date_attribute(a["slug"], a["date_iso"]):
            n_date += 1
        if inject_freshness_script(a["slug"]):
            n_script += 1

    # 3. Rotation "à lire aussi" selon le nouvel ordre
    for i, a in enumerate(articles):
        lib.rewrite_related_section(a["slug"], articles, i)

    # 4. Sauvegarde de l'ordre définitif
    lib.save_articles(articles)

    print(f"OK — {n_date} pages avec attribut de date ajouté, {n_script} pages avec bandeau de fraîcheur injecté.")


if __name__ == "__main__":
    main()
