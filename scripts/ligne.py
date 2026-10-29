"""
Ligne editoriale — ajoutee le 29/10/2026.

Constat : la veille surveillait surtout la presse professionnelle et publiait
des sujets de metier (fraude, proces, syndicats, dirigeants de groupes...) qui
n'interessent pas un client et n'amenent personne en boutique.

Ce module lit scripts/ligne_editoriale.json (modifiable sans toucher au code)
et fournit :
  - bloc_prompt()        : themes autorises, theme impose du moment, sujets
                           interdits, faits sur la boutique, orientation boutique ;
  - controle_interdits() : filet de securite apres redaction (titre, slug, resume) ;
  - nettoyer_encart()    : verification de l'encart « Chez nous ».

Meme fichier dans les depots Actueyes et Maison Mikis : seul le JSON differe.
"""
import json
import os
import re
import unicodedata

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
LIGNE_PATH = os.path.join(SCRIPTS_DIR, "ligne_editoriale.json")

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]


def charger(path=LIGNE_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def theme_impose(ligne, today):
    """Theme phare impose a certaines dates (ex. premier jeudi du mois)."""
    phare = ligne.get("theme_phare")
    if not phare:
        return None
    jours = phare.get("jours_semaine", [3])          # 3 = jeudi
    max_jour = int(phare.get("jusqu_au_jour_du_mois", 7))
    if today.weekday() in jours and today.day <= max_jour:
        return next((t for t in ligne["themes"] if t["id"] == phare["theme"]), None)
    return None


def _liste(items, puce="- "):
    return "\n".join(puce + str(i) for i in items)


def bloc_faits(ligne):
    return ("FAITS SUR LA BOUTIQUE — les SEULS que tu peux affirmer. N'invente aucun "
            "autre service, équipement, horaire, prix, délai, marque, chiffre ou "
            "partenariat.\n" + _liste(ligne["faits_boutique"]) + "\n")


def bloc_prompt(ligne, today, mode):
    """Texte ajoute au prompt systeme, pour les guides comme pour la veille."""
    nom = ligne["boutique"]
    themes = []
    for t in ligne["themes"]:
        ligne_t = "- %s [%s, rubrique « %s »] : %s" % (
            t["label"], t["priorite"], t["category"], t["perimetre"])
        if t.get("exemples"):
            ligne_t += "\n    Exemples de bons sujets : " + " / ".join(
                "« %s »" % e for e in t["exemples"])
        themes.append(ligne_t)

    saison = ligne.get("calendrier", {}).get(str(today.month), "")
    impose = theme_impose(ligne, today) if mode != "guide" else None

    txt = """
LIGNE ÉDITORIALE — prioritaire sur tout le reste.

Le lecteur est un CLIENT ou un futur client de %(nom)s, jamais un professionnel
de l'optique. Chaque article doit répondre à une question qu'il se pose vraiment
et lui donner envie de venir en boutique.

TEST DU CLIENT, à passer avant d'écrire : « Un client de la boutique taperait-il
cette question dans Google ? » Si la réponse est non, le sujet est refusé.

THÈMES AUTORISÉS (en dehors de ces thèmes, aucun article) :
%(themes)s

SUJETS INTERDITS, même s'ils touchent un thème autorisé :
%(interdits)s
""" % {"nom": nom, "themes": "\n".join(themes),
       "interdits": _liste(ligne["sujets_interdits"])}

    if saison:
        txt += "\nSAISON — nous sommes en %s : %s Privilégie ce thème à qualité égale.\n" % (
            MOIS[today.month - 1], saison)

    if impose:
        txt += ("\nSUJET IMPOSÉ AUJOURD'HUI — thème phare « %s ». Tu rédiges un article "
                "sur ce thème, et sur aucun autre. S'il n'y a aucune actualité, tu "
                "rédiges un article de fond qui répond à une vraie question de client "
                "sur ce thème (voir les exemples), non encore traitée sur le site. "
                "Ne réponds JAMAIS {\"no_novelty\": true} aujourd'hui.\n" % impose["label"])

    if mode != "guide":
        txt += """
SOURCES — chaque source a un rôle (« role ») :
- « source » : organismes officiels et associations de patients. Ils servent à
  écrire et à vérifier les règles, les droits et les chiffres.
- « idees » : questions réelles posées par le public. Elles servent à CHOISIR un
  sujet, jamais à vérifier une règle ni à être citées.
- « fabricant » et « marque » : ils servent seulement à présenter un nouveau
  produit ou une nouvelle collection vendus chez nous (champ « marques » quand il
  est indiqué) : jamais leurs résultats, rachats, dirigeants ou stratégie. Une
  marque absente des faits ci-dessous n'est jamais traitée.
- « radar » (presse professionnelle, syndicats) : sert UNIQUEMENT à repérer
  qu'une nouveauté existe. L'article s'appuie alors sur la source officielle ou
  le fabricant, ne cite jamais le radar et ne parle jamais de la profession.

S'IL N'Y A AUCUNE NOUVEAUTÉ qui passe le test du client dans un thème autorisé,
tu ne réponds pas « aucune nouveauté » : tu rédiges un article de fond, durable,
qui répond à une vraie question de client dans le thème de saison ou dans un
thème « phare » ou « haute », non encore traitée sur le site. Dans ce cas,
« source_used » vaut exactement : article de fond.
"""

    txt += """
ORIENTATION BOUTIQUE — l'article doit faire venir des clients, pas seulement
informer.
- Environ 70 %% du texte est une vraie réponse utile : c'est ce qui permet d'être
  bien classé par Google. Le reste relie le sujet à ce que %(nom)s propose.
- Dans le corps, UN paragraphe (pas le dernier) explique concrètement ce que le
  lecteur trouve chez nous sur ce sujet précis, à partir des faits ci-dessous.
- Le dernier paragraphe invite à passer en boutique (adresse ou repère d'accès).
- « encart_boutique » : 35 à 70 mots, texte brut sans balise, écrit au « nous » :
  ce que le lecteur trouve chez nous sur CE sujet + une invitation à passer.
  Uniquement des faits listés ci-dessous.
- Toujours factuel et vérifiable : chiffres de la boutique, délais, services.
  Interdits : superlatifs invérifiables (« le meilleur », « le plus grand
  choix », « exceptionnel », « n° 1 »), prix chiffrés, promotions datées,
  urgence commerciale, comparaison avec un confrère.
- Ne cite JAMAIS le nom d'un fournisseur, d'un grossiste ou d'une centrale
  d'achat de la boutique (les marques de montures et d'appareils, oui).

""" % {"nom": nom}
    txt += bloc_faits(ligne)
    return txt


def _sans_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def controle_interdits(ligne, *textes):
    """Filet de securite : refuse un titre, slug ou resume qui touche un sujet
    interdit. Leve ValueError, ce qui relance la redaction avec la cause."""
    bas = _sans_accents(" ".join(str(t) for t in textes).lower().replace("-", " "))
    for motif in ligne.get("motifs_interdits", []):
        if re.search(_sans_accents(motif.lower()), bas):
            raise ValueError(
                "sujet interdit par la ligne éditoriale (motif « %s »). Choisis un "
                "sujet qui passe le test du client, dans un thème autorisé" % motif)


SUPERLATIFS = (r"\ble meilleur\b", r"\bla meilleure\b", r"\bles meilleurs\b",
               r"plus grand choix", r"exceptionnel", r"\bn[°o] ?1\b", r"imbattable",
               r"incomparable")


def nettoyer_encart(texte):
    t = re.sub(r"<[^>]+>", "", str(texte or "")).strip()
    t = re.sub(r"\s+", " ", t)
    mots = len(t.split())
    if not 25 <= mots <= 90:
        raise ValueError("encart_boutique : %d mots (attendu 35 à 70)" % mots)
    for motif in SUPERLATIFS:
        if re.search(motif, t.lower()):
            raise ValueError("encart_boutique : superlatif invérifiable (%s), reste "
                             "factuel" % motif)
    return t
