#!/usr/bin/env python3
"""
Exécution hebdomadaire de la veille Actualités — lancé par
.github/workflows/actualites-weekly.yml sur les serveurs GitHub Actions
(indépendant de toute session Claude.ai ou du PC du client).

Ce script :
1. Charge sources.json / state.json / articles.json.
2. Si baseline_done=false : appelle l'API Claude pour "faire le point" sur
   chaque source (sans publier), enregistre l'état, s'arrête.
3. Sinon : appelle l'API Claude (avec l'outil web_search) pour vérifier les
   sources et rédiger un article UNIQUEMENT si une vraie nouveauté est trouvée,
   dans un format JSON strict.
4. Valide et publie via add_article.py, met à jour state.json.
5. Écrit un résumé dans GITHUB_STEP_SUMMARY (visible dans l'onglet Actions et
   repris par la notification GitHub si le client l'a activée).

Ne fait AUCUN commit/push lui-même — c'est le workflow .yml qui s'en charge
après un run réussi, pour garder ce script testable isolément.
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_articles as lib
from add_article import add_article, _fill_category_accents

STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")
SOURCES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources.json")
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def call_claude(system, user_message, use_web_search=True, max_tokens=4000):
    """Appel direct à l'API Messages d'Anthropic (pas de SDK, pour rester à une
    seule dépendance : le module standard urllib)."""
    if not API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY manquant dans l'environnement (secret GitHub Actions).")
    body = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user_message}],
    }
    if use_web_search:
        body["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    texts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
    return "\n".join(texts)


def extract_json(text):
    """Le prompt demande du JSON pur, mais on tolère un bloc ```json ... ``` par prudence."""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if m:
        text = m.group(1)
    return json.loads(text)


def write_summary(text):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)


def run_baseline(sources, state):
    write_summary("## Veille Actualités — passe baseline\n")
    system = (
        "Tu fais un état des lieux pour une veille éditoriale. Pour chaque source "
        "fournie, utilise la recherche web pour identifier la publication/actualité "
        "la plus récente visible aujourd'hui sur son site officiel ou sa page "
        "actus/presse. Réponds UNIQUEMENT en JSON, aucun texte autour, au format : "
        '{"source_name": "résumé très court (<12 mots) de la dernière publication vue, ou null si rien trouvé"}'
    )
    flat_sources = []
    for theme, block in sources.items():
        if theme.startswith("_"):
            continue
        for s in block.get("sources", []):
            flat_sources.append(s["name"])
    if not flat_sources:
        write_summary("Aucune source avec URL exploitable pour l'instant.")
        state["baseline_done"] = True
        return state
    user_msg = "Sources à vérifier :\n" + "\n".join(f"- {n}" for n in flat_sources)
    try:
        raw = call_claude(system, user_msg)
        result = extract_json(raw)
    except Exception as e:
        write_summary(f"⚠️ Erreur pendant la baseline : {e}. Nouvelle tentative la semaine prochaine.")
        return state
    for name, seen in result.items():
        state["last_seen_by_source"][name] = seen
    state["baseline_done"] = True
    write_summary(f"Baseline enregistrée pour {len(result)} sources. Aucun article publié cette semaine (comportement attendu).")
    return state


def run_weekly(sources, state, articles):
    write_summary("## Veille Actualités — exécution hebdomadaire\n")
    existing_slugs = {a["slug"] for a in articles}
    accents = _fill_category_accents()
    valid_categories = sorted(accents.keys())

    flat_sources = []
    for theme, block in sources.items():
        if theme.startswith("_"):
            continue
        for s in block.get("sources", []):
            flat_sources.append({"theme": theme, "name": s["name"], "url": s.get("url")})

    last_seen_json = json.dumps(state.get("last_seen_by_source", {}), ensure_ascii=False)
    today = date.today().isoformat()

    system = f"""Tu es l'équipe éditoriale du site maisonmikis.fr (opticien/audioprothésiste, Paris 13e).
Tu géres une veille hebdomadaire : vérifier des sources professionnelles, et si une
VRAIE nouveauté existe depuis la dernière vérification, rédiger un article de blog
factuel et bien sourcé pour le site, dans le style des articles déjà publiés
(informatif, accessible, jamais promotionnel à l'excès, toujours reformulé, jamais
copié verbatim).

Règles strictes :
- N'invente JAMAIS une nouveauté qui n'existe pas réellement dans les résultats de recherche.
- Si rien de neuf n'est trouvé pour aucune source, réponds exactement {{"no_novelty": true}}.
- **Seuil d'importance éditoriale — sois exigeant.** Une simple différence par rapport à la dernière vérification ne suffit PAS à justifier un article. Ne rédige un article QUE si la nouveauté correspond à au moins une de ces catégories :
  - Lancement d'un vrai nouveau produit ou d'une nouvelle technologie
  - Résultat financier ou annonce stratégique significative (croissance notable, acquisition, changement de direction)
  - Changement réglementaire ou législatif touchant l'optique/l'audition (remboursements, normes, obligations)
  - Étude, enquête ou statistique notable d'une autorité de santé ou d'un organisme professionnel reconnu
  - Événement de fond pour la profession (congrès majeur, évolution de norme BIAP, etc.)
  Ignore explicitement : mises à jour cosmétiques de site web, republications, changements de prix mineurs, contenu promotionnel sans substance, sponsoring d'événements mondains sans lien direct avec le métier, nominations à des postes non stratégiques. Dans le doute, ne publie pas — mieux vaut manquer une semaine que publier un article creux.
- Ne publie JAMAIS sur un sujet déjà couvert (voir la liste des slugs déjà utilisés).
- Le corps de l'article (body_html) doit faire 400-700 mots, structuré en 2-4 sections <h2>/<p>, ton factuel.
- meta_description : 150-160 caractères. excerpt : une phrase courte pour une carte.
- category doit être une valeur EXACTE parmi : {valid_categories}
- date_iso doit être : {today}
- slug : minuscules, tirets, sans accents, ne doit PAS être dans cette liste déjà utilisée : {sorted(existing_slugs)}
- image : réutiliser un chemin déjà existant sur le site cohérent avec le thème (voir PIPELINE.md pour le mapping), jamais une nouvelle image externe.

Réponds UNIQUEMENT en JSON, sans aucun texte autour, sans balises markdown, soit :
{{"no_novelty": true}}
soit :
{{
  "source_used": "nom exact de la source utilisée",
  "slug": "...", "title": "...", "page_title": "... | Maison Mikis",
  "meta_description": "...", "excerpt": "...", "category": "...",
  "image": "/images/...", "image_alt": "...", "date_iso": "{today}",
  "body_html": "<h2>...</h2><p>...</p>..."
}}"""

    user_msg = (
        "Sources à vérifier (theme, name, url) :\n"
        + json.dumps(flat_sources, ensure_ascii=False, indent=2)
        + "\n\nDernière publication vue par source (pour comparaison) :\n"
        + last_seen_json
    )

    try:
        raw = call_claude(system, user_msg)
        result = extract_json(raw)
    except Exception as e:
        write_summary(f"⚠️ Erreur pendant la génération : {e}. Aucun article publié, à revoir la semaine prochaine.")
        return state, None

    if result.get("no_novelty"):
        write_summary("Aucune vraie nouveauté détectée cette semaine. Aucun article publié (comportement attendu, pas une erreur).")
        return state, None

    required = ["slug", "title", "page_title", "meta_description", "excerpt",
                "category", "image", "image_alt", "date_iso", "body_html"]
    missing = [k for k in required if k not in result]
    if missing:
        write_summary(f"⚠️ Réponse incomplète de l'API (champs manquants : {missing}). Aucun article publié.")
        return state, None

    if result["slug"] in existing_slugs:
        write_summary(f"⚠️ Slug '{result['slug']}' déjà utilisé — publication annulée par sécurité (voir règle : jamais d'écrasement).")
        return state, None

    if result["category"] not in valid_categories:
        write_summary(f"⚠️ Catégorie invalide '{result['category']}' — publication annulée.")
        return state, None

    entry = add_article({k: result[k] for k in required})

    state["used_slugs"].append(entry["slug"])
    source_name = result.get("source_used", "source non précisée")
    state["last_seen_by_source"][source_name] = entry["title"]
    state["publication_log"].append({
        "slug": entry["slug"], "title": entry["title"], "date": entry["date_iso"],
        "source": source_name,
    })
    if entry["category"] == "mode-lunettes":
        rot = state["mode_lunettes_brand_rotation"]
        rot["next_index"] = (rot["next_index"] + 1) % len(rot["brands_order"])

    write_summary(
        f"✅ Nouvel article publié : **{entry['title']}** ({entry['category_label']})\n\n"
        f"URL : https://www.maisonmikis.fr/actualites/{entry['slug']}.html\n\n"
        f"Source d'inspiration : {source_name}"
    )
    return state, entry


def main():
    sources = load(SOURCES_PATH)
    state = load(STATE_PATH)
    articles = lib.load_articles()

    if not state.get("baseline_done"):
        state = run_baseline(sources, state)
    else:
        state, published = run_weekly(sources, state, articles)

    save(STATE_PATH, state)


if __name__ == "__main__":
    main()
