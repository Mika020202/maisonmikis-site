#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Veille hebdomadaire Actualites — Maison Mikis.

Lance chaque lundi par .github/workflows/publication.yml, sur les serveurs
GitHub Actions : ni session Claude ouverte, ni ordinateur du client allume.

Ce que fait ce script :
  1. lit scripts/sources.json (les sources professionnelles a surveiller) et
     scripts/state.json (ce qui a deja ete vu et publie) ;
  2. interroge l'API Claude avec l'outil de recherche web, en imposant un seuil
     d'importance editoriale strict ;
  3. si — et seulement si — une vraie nouveaute existe, il fait rediger un
     article au format editorial du site et l'ajoute a scripts/articles_auto.json ;
  4. met a jour scripts/state.json et ecrit un resume dans l'onglet Actions.

Ce qu'il ne fait PAS, volontairement :
  - il ne genere aucune page HTML. C'est build.py, a la racine du depot, qui
    reste le SEUL generateur du site : un article automatique passe donc par
    exactement le meme gabarit, le meme maillage interne et le meme JSON-LD que
    les articles ecrits a la main ;
  - il ne choisit aucune URL interne ni aucune image : build.py s'en charge, a
    partir de listes ecrites en dur. Le modele ecrit le texte, le code place
    les liens. Un lien casse devient ainsi impossible ;
  - il ne fait aucun commit : c'est le workflow qui commit et met en ligne.

En cas de doute, il ne publie rien. Une semaine sans article est un
fonctionnement normal, pas une panne.
"""
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from datetime import date, timedelta

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPTS_DIR)
sys.path.insert(0, ROOT)

STATE_PATH = os.path.join(SCRIPTS_DIR, "state.json")
SOURCES_PATH = os.path.join(SCRIPTS_DIR, "sources.json")
AUTO_PATH = os.path.join(SCRIPTS_DIR, "articles_auto.json")

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-5"

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------
def load(path, default=None):
    if not os.path.exists(path) and default is not None:
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_summary(text):
    """Ecrit dans le resume d'execution GitHub (visible dans l'onglet Actions
    et repris dans la notification recue par le client)."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)


def date_fr(d):
    jour = d.day if d.day > 1 else "1er"
    return "%s %s %d" % (jour, MOIS[d.month - 1], d.year)


def strip_tags(html):
    html = re.sub(r"<[^>]+>", " ", html)
    html = html.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", html).strip()


def word_count(text):
    return len([w for w in re.split(r"\s+", text) if w])


def slugify(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return re.sub(r"-{2,}", "-", value)


# ---------------------------------------------------------------------------
# Appel API
# ---------------------------------------------------------------------------
def call_claude(system, user_message, use_web_search=True, max_tokens=12000,
                max_recherches=14):
    """Appel direct a l'API Messages d'Anthropic. Pas de SDK : une seule
    dependance, urllib, donc rien a installer sur le runner.

    Trois pieges, rencontres l'un apres l'autre en conditions reelles :

    1. l'API interrompt d'elle-meme les tours de recherche longs et renvoie
       stop_reason = "pause_turn". La reponse ne contient alors AUCUN texte
       final : il faut lui renvoyer sa propre reponse, inchangee, pour qu'elle
       reprenne la ou elle s'est arretee ;
    2. un appel non "streame" qui dure trop longtemps se fait couper par le
       reseau ("Remote end closed connection without response"). On borne donc
       le nombre de recherches par appel : chaque requete reste courte ;
    3. une coupure reseau reste toujours possible. Elle est passagere : on
       reessaie trois fois avant d'abandonner, plutot que de perdre la semaine.
    """
    import time

    if not API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY absent de l'environnement (secret du depot GitHub).")

    messages = [{"role": "user", "content": user_message}]
    data = {}
    textes = []

    for _ in range(10):
        body = {
            "model": MODEL,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        if use_web_search:
            body["tools"] = [{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": max_recherches,
            }]
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

        data = None
        coupure = None
        for essai in range(3):
            try:
                with urllib.request.urlopen(req, timeout=600) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")
                raise RuntimeError(
                    "l'API a refuse la requete (HTTP %s) : %s"
                    % (exc.code, detail[:600])) from None
            except Exception as exc:
                coupure = exc
                time.sleep(5 * (essai + 1))

        if data is None:
            raise RuntimeError(
                "connexion a l'API interrompue malgre trois tentatives : %s" % coupure)

        contenu = data.get("content", [])
        textes = [b["text"] for b in contenu if b.get("type") == "text"]
        if data.get("stop_reason") != "pause_turn":
            break
        messages.append({"role": "assistant", "content": contenu})

    if not any(t.strip() for t in textes):
        raise RuntimeError(
            "l'API n'a renvoye aucun texte exploitable (stop_reason = %s). "
            "Aucun article n'a pu etre lu." % data.get("stop_reason"))
    return "\n".join(textes)


def extract_json(text):
    """Le prompt exige du JSON pur ; on tolere un bloc ```json ... ``` et du
    bavardage autour, par prudence.

    strict=False est indispensable : le modele glisse regulierement un vrai saut
    de ligne a l'interieur d'une chaine (typiquement dans body_html, qui fait
    plusieurs milliers de caracteres). Le parseur strict refuse alors tout le
    document avec "Invalid control character at ...", et l'article entier est
    perdu pour un simple retour a la ligne.
    """
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if m:
        text = m.group(1)
    else:
        first, last = text.find("{"), text.rfind("}")
        if first != -1 and last > first:
            text = text[first:last + 1]
    return json.loads(text, strict=False)


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
def flatten_sources(sources):
    out = []
    for theme, block in sources.items():
        if theme.startswith("_"):
            continue
        for s in block.get("sources", []):
            out.append({"theme": theme, "name": s["name"], "url": s.get("url")})
    return out


# ---------------------------------------------------------------------------
# Passe baseline (etat des lieux, sans publier)
# ---------------------------------------------------------------------------
def run_baseline(sources, state):
    write_summary("## Veille Actualités — état des lieux initial\n")
    names = [s["name"] for s in flatten_sources(sources)]
    if not names:
        write_summary("Aucune source exploitable. Rien à faire.")
        state["baseline_done"] = True
        return state
    system = (
        "Tu fais un état des lieux pour une veille éditoriale. Pour chaque source "
        "fournie, utilise la recherche web pour identifier la publication la plus "
        "récente visible aujourd'hui sur son site officiel ou sa page actualités. "
        "Réponds UNIQUEMENT en JSON, sans texte autour : "
        '{"nom de la source": "résumé de moins de 12 mots, ou null si rien trouvé"}'
    )
    user = "Sources à vérifier :\n" + "\n".join("- " + n for n in names)
    try:
        result = extract_json(call_claude(system, user, max_tokens=4000))
    except Exception as exc:
        write_summary("⚠️ Échec de l'état des lieux : %s. Nouvelle tentative "
                      "la semaine prochaine." % exc)
        return state
    state.setdefault("last_seen_by_source", {}).update(result)
    state["baseline_done"] = True
    write_summary("État des lieux enregistré pour %d sources. Aucun article publié "
                  "cette semaine : c'est le comportement attendu." % len(result))
    return state


# ---------------------------------------------------------------------------
# Charte editoriale — elle est la memoire du travail fait avec le client.
# ---------------------------------------------------------------------------
CHARTE = """CHARTE ÉDITORIALE DU SITE — à respecter sans exception.

Qui parle. Les articles sont signés « l'équipe Maison Mikis ». Tu écris au « nous ».
N'écris JAMAIS le nom d'une personne comme auteur, et ne mentionne JAMAIS un
diplôme, un titre ou une qualification professionnelle d'un membre de l'équipe.

Ton. Informatif, précis, utile. Jamais promotionnel à l'excès, jamais anxiogène,
jamais racoleur. On explique un mécanisme avant de donner un conseil. On admet ce
qui n'est pas démontré plutôt que de le survendre (exemple : la lumière bleue).

Sources. Tout fait chiffré vient d'une source réelle trouvée par la recherche web,
et tu la cites. Tu REFORMULES systématiquement dans tes propres mots : jamais de
copie mot pour mot d'une phrase de la source, jamais de citation longue.

Ancrage local. Maison Mikis est Galerie Oslo, 44 avenue d'Ivry, Paris 13e, sur
l'esplanade des Olympiades (métro 14). Le quartier peut apparaître UNE fois, dans
le corps du texte, seulement si c'est naturel et justifié (par exemple dans un
paragraphe final qui ramène au comptoir). Jamais dans le titre, jamais dans la
meta description, jamais de façon répétée.

Structure imposée.
- « answer » : la réponse directe à la question du titre, en 40 à 60 mots, sans
  balise HTML, autosuffisante. C'est ce que lira un moteur de recherche.
- « body_html » : 800 à 1400 mots, en HTML simple. 3 à 5 sections <h2>, des <h3>
  quand c'est utile, des <p>. Tu peux utiliser <ul>/<ol>/<li> et <strong>.
  Le premier <h2> ne répète pas le titre. Le dernier paragraphe ramène au
  concret : quand consulter, quoi faire, ou ce que nous faisons en boutique.
- N'écris AUCUNE balise <a> et AUCUN lien : le maillage interne est posé
  automatiquement par le générateur du site. Un lien que tu écrirais serait faux.
- N'écris AUCUNE balise <h1>, <img>, <script>, <style> ni aucun attribut style.
- Utilise &nbsp; avant % et entre un nombre et son unité (ex. 60&nbsp;%, 40&nbsp;cm).

Titre et métadonnées.
- « title » : phrase claire, 55-75 caractères, sans nom de marque du site.
- « meta_title » : se termine par « | Maison Mikis », 60 caractères maximum
  avant ce suffixe.
- « meta_description » : 145 à 160 caractères, JAMAIS plus de 170 : compte-les
  avant de repondre. Utile, sans superlatif creux.
- « excerpt » : une seule phrase, 90 à 160 caractères, pour la carte de la grille.

FAQ. 3 ou 4 questions réellement posées par des clients, avec des réponses de 2 à
4 phrases. Pas de question dont la réponse est dans le titre.

Interdits absolus : promesse de résultat de santé, conseil qui remplace un avis
médical, comparaison dénigrante d'un confrère, prix, promotion, urgence commerciale.
"""


# ---------------------------------------------------------------------------
# Passe hebdomadaire
# ---------------------------------------------------------------------------
def run_weekly(sources, state, site):
    write_summary("## Veille Actualités — exécution hebdomadaire\n")

    known_slugs = sorted({a["slug"] for a in site.ARTICLES} | set(state.get("used_slugs", [])))
    categories = sorted(site.ARTICLE_CATEGORIES.keys())
    titres_existants = [a["title"] for a in site.ARTICLES]
    today = date.today()

    system = """Tu es l'équipe éditoriale du site maisonmikis.fr, opticien et
audioprothésiste indépendant à Paris 13e. Tu tiens une veille hebdomadaire : tu
vérifies des sources professionnelles, et tu ne rédiges un article QUE si un fait
réellement notable mérite d'être porté à la connaissance des clients de la
boutique.

FENÊTRE DE RECHERCHE — soixante jours.
Tu ne te limites pas à ce qui est apparu depuis la dernière vérification. Tu
retiens tout fait notable des SOIXANTE derniers jours qui n'a pas encore été
traité sur le site. La liste des sujets déjà couverts t'est donnée plus bas :
si un fait important des dernières semaines n'y figure pas, il est légitime de
l'écrire aujourd'hui, même s'il date de plusieurs semaines. Un décret publié il
y a un mois et jamais expliqué à nos clients reste une information neuve POUR EUX.
À qualité égale, tu préfères le fait le plus récent.

SEUIL D'IMPORTANCE — sois exigeant, c'est le cœur de ta mission.
L'ancienneté n'est pas un critère de rejet ; la faiblesse du sujet en est un.
Tu ne rédiges que si le fait relève d'au moins une de ces catégories :
  - lancement d'un vrai produit ou d'une vraie technologie ;
  - changement réglementaire ou de remboursement touchant l'optique ou l'audition ;
  - étude, enquête ou statistique notable d'une autorité de santé ou d'un
    organisme professionnel reconnu ;
  - annonce stratégique lourde d'un acteur majeur du secteur ;
  - évolution de fond de la profession (norme, recommandation, congrès majeur).
Tu ignores explicitement : mise à jour cosmétique de site, republication, variation
de prix, communiqué promotionnel sans substance, sponsoring mondain, nomination à
un poste non stratégique, marronnier saisonnier.
Un article creux abîme le site : mieux vaut ne rien publier que publier du vide.
Mais avant de renoncer, tu dois avoir réellement balayé les soixante derniers
jours et vérifié qu'aucun fait de ces catégories n'est resté non traité. Ne
renonce que si ce balayage ne donne rien.

Si rien ne franchit ce seuil, réponds EXACTEMENT : {"no_novelty": true}

""" + CHARTE + """

CONTRAINTES TECHNIQUES
- « category » : exactement une valeur de cette liste : %s
- « slug » : minuscules, tirets, sans accent, 3 à 8 mots, descriptif.
  Il ne doit être AUCUN de ceux-ci : %s
- Ne traite AUCUN sujet déjà couvert par les articles existants (liste ci-dessous).
- « sources » : 2 à 4 entrées [nom, url]. Chaque url doit être une adresse https
  réelle rencontrée pendant ta recherche, jamais inventée, jamais un moteur de
  recherche.

FORMAT DE RÉPONSE — du JSON pur, rien avant, rien après, aucune balise markdown :
{
  "source_used": "nom exact de la source qui a déclenché l'article",
  "justification": "en une phrase, pourquoi cette nouveauté franchit le seuil",
  "category": "...",
  "slug": "...",
  "title": "...",
  "meta_title": "... | Maison Mikis",
  "meta_description": "...",
  "excerpt": "...",
  "answer": "...",
  "faq": [["question", "réponse"], ["question", "réponse"], ["question", "réponse"]],
  "sources": [["nom", "https://..."], ["nom", "https://..."]],
  "body_html": "<h2>...</h2><p>...</p>..."
}""" % (categories, known_slugs)

    user = (
        "Sources à vérifier :\n"
        + json.dumps(flatten_sources(sources), ensure_ascii=False, indent=2)
        + "\n\nPour information seulement — dernière publication repérée sur chaque "
          "source lors d'un passage précédent. Ce n'est PAS une borne : un fait "
          "antérieur peut très bien n'avoir jamais été traité chez nous.\n"
        + json.dumps(state.get("last_seen_by_source", {}), ensure_ascii=False, indent=2)
        + "\n\nTitres déjà publiés sur le site (ne redis pas la même chose) :\n"
        + "\n".join("- " + t for t in titres_existants)
        + "\n\nNous sommes le %s. Ta fenêtre de recherche va donc du %s à "
          "aujourd'hui." % (today.isoformat(), (today - timedelta(days=60)).isoformat())
    )

    # Trois tentatives avant d'abandonner la semaine. Une reponse mal formee
    # ou un article refuse au controle qualite ne doit pas coûter le passage
    # entier : on redonne au modele la cause exacte de l'echec et on relance.
    # Seul "aucune nouveaute" sort tout de suite : c'est une reponse valable.
    article = None
    result = {}
    dernier_probleme = "cause inconnue"
    consigne = ""

    for tentative in range(3):
        try:
            result = extract_json(call_claude(system, user + consigne))
        except Exception as exc:
            dernier_probleme = "reponse illisible (%s)" % exc
            consigne = (
                "\n\nATTENTION : ta reponse precedente n'a pas pu etre lue (%s). "
                "Renvoie du JSON strictement valide. N'insere JAMAIS un vrai saut "
                "de ligne a l'interieur d'une chaine : ecris \\n." % exc)
            continue

        state["dernier_passage"] = today.isoformat()

        if result.get("no_novelty"):
            write_summary("Aucune nouveauté ne franchit le seuil éditorial cette "
                          "semaine. **Aucun article publié** — c'est le comportement "
                          "attendu, pas une erreur.")
            return state, None

        try:
            article = validate(result, site, known_slugs, today)
            break
        except ValueError as exc:
            dernier_probleme = "article refusé au contrôle qualité (%s)" % exc
            consigne = (
                "\n\nATTENTION : ton article precedent a ete refuse pour cette "
                "raison precise : %s. Corrige uniquement ce point et renvoie "
                "l'article complet, en JSON strictement valide." % exc)

    state["dernier_passage"] = today.isoformat()

    if article is None:
        # La formule "Erreur pendant la veille" est le mot-cle que guette le
        # workflow pour echouer bruyamment. Ne pas la retirer.
        write_summary("⚠️ Erreur pendant la veille : trois tentatives, aucune "
                      "exploitable. Dernière cause : %s\n\nAucun article publié. "
                      "Le site reste inchangé." % dernier_probleme)
        return state, None

    auto = load(AUTO_PATH, default=[])
    auto.append(article)
    save(AUTO_PATH, auto)

    state.setdefault("used_slugs", []).append(article["slug"])
    source_name = result.get("source_used", "source non précisée")
    state.setdefault("last_seen_by_source", {})[source_name] = article["title"]
    state.setdefault("publication_log", []).append({
        "slug": article["slug"],
        "title": article["title"],
        "date": article["date_iso"],
        "source": source_name,
    })

    write_summary(
        "✅ **Nouvel article publié : %s**\n\n"
        "En ligne dans quelques minutes ici : https://www.maisonmikis.fr/actualites/%s.html\n\n"
        "- Rubrique : %s\n- Source : %s\n- Pourquoi ce sujet : %s\n- Longueur : %d mots\n\n"
        "Si cet article ne vous convient pas, dites-le : il se retire en une manipulation."
        % (article["title"], article["slug"],
           site.ARTICLE_CATEGORIES[article["category"]]["label"].replace("&amp;", "&"),
           source_name, result.get("justification", "—"),
           word_count(strip_tags(article["body"])))
    )
    return state, article


# ---------------------------------------------------------------------------
# Controle qualite — tout ce qui ne passe pas ici n'est PAS publie.
# ---------------------------------------------------------------------------
FORBIDDEN_TAGS = ("<a ", "<a>", "<h1", "<img", "<script", "<style", "<iframe", "style=")


def raccourcir(texte, limite):
    """Coupe proprement a la limite : sur une fin de phrase si possible, sinon
    sur un mot entier. Un simple depassement de longueur ne doit jamais faire
    perdre un article entier."""
    texte = " ".join(str(texte).split())
    if len(texte) <= limite:
        return texte
    coupe = texte[:limite]
    for sep in (". ", "! ", "? "):
        pos = coupe.rfind(sep)
        if pos > limite * 0.6:
            return coupe[:pos + 1].strip()
    pos = coupe.rfind(" ")
    return (coupe[:pos] if pos > 0 else coupe).rstrip(" ,;:-") + "."


def nettoyer_html(html):
    """Retire les balises que le modele n'aurait pas du ecrire, au lieu de
    refuser l'article : liens, images, styles, scripts ; <h1> requalifie en <h2>."""
    html = re.sub(r"</?a\b[^>]*>", "", html, flags=re.I)
    html = re.sub(r"<(img|script|style|iframe)\b[^>]*>.*?</\1>", "", html, flags=re.I | re.S)
    html = re.sub(r"<(img|script|style|iframe)\b[^>]*/?>", "", html, flags=re.I)
    html = re.sub(r'\s+style="[^"]*"', "", html, flags=re.I)
    html = re.sub(r"\s+style='[^']*'", "", html, flags=re.I)
    html = re.sub(r"<(/?)h1\b", r"<\1h2", html, flags=re.I)
    return html.strip()


def validate(r, site, known_slugs, today):
    champs = ["category", "slug", "title", "meta_title", "meta_description",
              "excerpt", "answer", "faq", "sources", "body_html"]
    manquants = [c for c in champs if c not in r or r[c] in (None, "", [])]
    if manquants:
        raise ValueError("champs manquants ou vides : %s" % manquants)

    cat = r["category"]
    if cat not in site.ARTICLE_CATEGORIES:
        raise ValueError("rubrique inconnue : %r" % cat)

    slug = slugify(r["slug"])
    if not slug or len(slug) < 8:
        raise ValueError("slug inexploitable : %r" % r["slug"])
    if slug in known_slugs:
        raise ValueError("slug déjà utilisé : %r (jamais d'écrasement)" % slug)

    body = nettoyer_html(r["body_html"])
    bas = body.lower()
    for tag in FORBIDDEN_TAGS:
        if tag in bas:
            raise ValueError("balise interdite non nettoyable : %r" % tag.strip())
    if "<h2" not in bas:
        raise ValueError("le corps ne contient aucune section <h2>")
    mots = word_count(strip_tags(body))
    if not 650 <= mots <= 1700:
        raise ValueError("longueur hors norme : %d mots (attendu 800-1400)" % mots)

    answer = strip_tags(r["answer"])
    if not 30 <= word_count(answer) <= 80:
        raise ValueError("bloc réponse hors norme : %d mots (attendu 40-60)"
                         % word_count(answer))

    meta = raccourcir(r["meta_description"], 175)
    if len(meta) < 120:
        raise ValueError("meta description trop courte : %d caractères" % len(meta))

    titre = raccourcir(r["title"], 95).rstrip(".")
    if len(titre) < 30:
        raise ValueError("titre trop court : %d caractères" % len(titre))

    meta_title = r["meta_title"].strip()
    if not meta_title.endswith("| Maison Mikis"):
        meta_title = "%s | Maison Mikis" % meta_title.rstrip(" |")
    if len(meta_title) > 90:
        base, _, suffixe = meta_title.rpartition("|")
        meta_title = "%s | %s" % (
            raccourcir(base, 86 - len(suffixe)).rstrip("."), suffixe.strip())

    faq = [(str(q).strip(), str(a).strip()) for q, a in r["faq"]]
    faq = faq[:5]
    if len(faq) < 2:
        raise ValueError("FAQ : %d questions (attendu 3 ou 4)" % len(faq))
    if any(not q or not a for q, a in faq):
        raise ValueError("FAQ : une question ou une réponse est vide")

    sources = []
    for nom, url in r["sources"]:
        url = str(url).strip()
        if not url.startswith("https://"):
            continue
        if any(bad in url for bad in ("google.com/search", "bing.com/search",
                                      "duckduckgo.com")):
            continue
        sources.append((str(nom).strip(), url))
    sources = sources[:5]
    if not sources:
        raise ValueError("aucune source exploitable")

    image, image_alt = pick_image(site, cat)

    return {
        "slug": slug,
        "category": cat,
        "title": titre,
        "meta_title": meta_title,
        "meta_description": meta,
        "excerpt": r["excerpt"].strip(),
        "answer": answer,
        "faq": [list(x) for x in faq],
        "sources": [list(x) for x in sources],
        "image": image,
        "image_alt": image_alt,
        "date_display": date_fr(today),
        "date_iso": today.isoformat(),
        "body": body,
    }


def pick_image(site, category):
    """L'image n'est jamais choisie par le modele : on reprend, en rotation, une
    illustration deja presente sur le site pour cette rubrique, avec son texte
    alternatif d'origine. Une image manquante en production devient impossible."""
    couples, vus = [], set()
    for a in site.ARTICLES:
        if a["category"] == category and a["image"] not in vus:
            vus.add(a["image"])
            couples.append((a["image"], a["image_alt"]))
    if not couples:
        for a in site.ARTICLES:
            if a["image"] not in vus:
                vus.add(a["image"])
                couples.append((a["image"], a["image_alt"]))
    deja = sum(1 for a in getattr(site, "AUTO_ARTICLES", []) if a["category"] == category)
    return couples[deja % len(couples)]


# ---------------------------------------------------------------------------
def main():
    sources = load(SOURCES_PATH)
    state = load(STATE_PATH)

    # Creneau de rattrapage : il n'existe que pour le cas ou le passage du
    # matin serait reste bloque dans la file d'attente de GitHub. Si ce
    # passage a bien eu lieu aujourd'hui, on s'arrete ici : aucune veille
    # relancee, aucun credit consomme pour rien.
    if (os.environ.get("CRON_RATTRAPAGE") == "1"
            and state.get("dernier_passage") == date.today().isoformat()):
        write_summary("Le passage du matin a bien eu lieu aujourd'hui. "
                      "Rattrapage inutile : aucune veille relancee, aucun "
                      "credit consomme.")
        return
    import build as site   # noqa: E402  (import tardif : build.py lit articles_auto.json)

    if not state.get("baseline_done"):
        state = run_baseline(sources, state)
    else:
        state, _ = run_weekly(sources, state, site)

    save(STATE_PATH, state)


if __name__ == "__main__":
    main()
