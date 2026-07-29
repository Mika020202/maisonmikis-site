"""
Bibliothèque de génération pour le système Actualités de maisonmikis.fr,
reconstruite le 28/07/2026 après la migration GitHub Pages (build.py n'existe plus).

Source de vérité : scripts/articles.json (liste ordonnée, la plus récente en premier).
Toutes les fonctions ici produisent EXACTEMENT le même HTML que celui déjà en ligne
(vérifié par diff sur les 24 articles existants avant tout usage en production).
"""
import json
import os
import re
import hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # /home/claude/site
ARTICLES_JSON = os.path.join(ROOT, "scripts", "articles.json")
ACTUALITES_HTML = os.path.join(ROOT, "actualites.html")
SITEMAP = os.path.join(ROOT, "sitemap.xml")
ARTICLES_DIR = os.path.join(ROOT, "actualites")

CATEGORY_ORDER = [
    ("all", "Tous"),
    ("sante-visuelle", "Santé visuelle"),
    ("sante-auditive", "Santé auditive"),
    ("mode-lunettes", "Mode & tendances"),
    ("tech-verres", "Technologies verres"),
    ("tech-lentilles", "Technologies lentilles"),
    ("remboursements", "Remboursements & démarches"),
    ("vie-boutique", "Vie de la boutique"),
    ("enfant", "Vision & audition de l'enfant"),
]

MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
             "août", "septembre", "octobre", "novembre", "décembre"]


def date_display_from_iso(date_iso):
    y, m, d = date_iso.split("-")
    return f"{int(d)} {MONTHS_FR[int(m) - 1]} {y}"


def load_articles():
    with open(ARTICLES_JSON, encoding="utf-8") as f:
        return json.load(f)


def save_articles(articles):
    with open(ARTICLES_JSON, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)


def render_card(a):
    return (
        f'      <a href="/actualites/{a["slug"]}.html" class="article-card reveal" data-category="{a["category"]}">\n'
        f'        <div class="article-img"><img src="{a["image"]}" alt="{a["image_alt"]}" loading="lazy"></div>\n'
        f'        <div class="article-card-body">\n'
        f'          <span class="article-tag" style="{a["accent_style"]}">{a["category_label"]}</span>\n'
        f'          <h3>{a["title"]}</h3>\n'
        f'          <p>{a["excerpt"]}</p>\n'
        f'          <div class="article-meta"><span>{a["date_display"]}</span><span class="more">Lire l\'article <span aria-hidden="true">⤢</span></span></div>\n'
        f'        </div>\n'
        f'      </a>\n'
    )


def render_grid(articles):
    return "".join(render_card(a) for a in articles)


def render_related_cards(articles, idx, n=3):
    """Rotation identique à l'ancien build.py : ARTICLES[(idx+i) % len(ARTICLES)],
    en sautant l'article courant."""
    total = len(articles)
    picks = []
    i = 1
    while len(picks) < n and i <= total:
        cand = articles[(idx + i) % total]
        if cand["slug"] != articles[idx]["slug"]:
            picks.append(cand)
        i += 1
    return "".join(render_card(p) for p in picks)


def css_version():
    css_path = os.path.join(ROOT, "site.css")
    with open(css_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()[:8]


def breadcrumb_jsonld(title, slug):
    return (
        '<script type="application/ld+json">\n'
        '{\n'
        '  "@context": "https://schema.org",\n'
        '  "@type": "BreadcrumbList",\n'
        '  "itemListElement": [\n'
        '    {\n'
        '      "@type": "ListItem",\n'
        '      "position": 1,\n'
        '      "name": "La Boutique",\n'
        '      "item": "https://www.maisonmikis.fr/"\n'
        '    },\n'
        '    {\n'
        '      "@type": "ListItem",\n'
        '      "position": 2,\n'
        '      "name": "Actualités",\n'
        '      "item": "https://www.maisonmikis.fr/actualites.html"\n'
        '    },\n'
        '    {\n'
        '      "@type": "ListItem",\n'
        '      "position": 3,\n'
        f'      "name": "{title}",\n'
        f'      "item": "https://www.maisonmikis.fr/actualites/{slug}.html"\n'
        '    }\n'
        '  ]\n'
        '}\n'
        '</script>\n'
    )


def article_jsonld(a):
    return (
        '<script type="application/ld+json">\n'
        '{\n'
        '  "@context": "https://schema.org",\n'
        '  "@type": "Article",\n'
        f'  "headline": "{a["title"]}",\n'
        f'  "description": "{a["meta_description"]}",\n'
        f'  "image": "https://www.maisonmikis.fr{a["image"]}",\n'
        f'  "datePublished": "{a["date_iso"]}",\n'
        f'  "dateModified": "{a["date_iso"]}",\n'
        '  "author": {\n'
        '    "@type": "Organization",\n'
        '    "name": "Maison Mikis"\n'
        '  },\n'
        '  "publisher": {\n'
        '    "@type": "Organization",\n'
        '    "name": "Maison Mikis",\n'
        '    "logo": {\n'
        '      "@type": "ImageObject",\n'
        '      "url": "https://www.maisonmikis.fr/og-image.jpg"\n'
        '    }\n'
        '  },\n'
        '  "mainEntityOfPage": {\n'
        '    "@type": "WebPage",\n'
        f'    "@id": "https://www.maisonmikis.fr/actualites/{a["slug"]}.html"\n'
        '  }\n'
        '}\n'
        '</script>\n'
    )


OPTICIAN_JSONLD = (
    '<script type="application/ld+json">\n'
    '{\n'
    '  "@context": "https://schema.org",\n'
    '  "@type": "Optician",\n'
    '  "name": "Maison Mikis",\n'
    '  "description": "Opticien et audioprothésiste à Paris 13e. Lunettes de vue et de soleil, lentilles de contact et solutions auditives.",\n'
    '  "url": "https://www.maisonmikis.fr/",\n'
    '  "telephone": "+33182280018",\n'
    '  "email": "mikis75013@gmail.com",\n'
    '  "priceRange": "€€",\n'
    '  "image": "https://www.maisonmikis.fr/og-image.jpg",\n'
    '  "address": {\n'
    '    "@type": "PostalAddress",\n'
    '    "streetAddress": "44 Avenue d\'Ivry, Galerie Oslo – Olympiades",\n'
    '    "addressLocality": "Paris",\n'
    '    "postalCode": "75013",\n'
    '    "addressCountry": "FR"\n'
    '  },\n'
    '  "openingHoursSpecification": {\n'
    '    "@type": "OpeningHoursSpecification",\n'
    '    "dayOfWeek": ["Tuesday","Wednesday","Thursday","Friday","Saturday"],\n'
    '    "opens": "10:00",\n'
    '    "closes": "19:30"\n'
    '  },\n'
    '  "sameAs": [\n'
    '    "https://www.instagram.com/maisonmikis/"\n'
    '  ]\n'
    '}\n'
    '</script>\n'
)

HEADER_HTML = '''<header id="siteHeader">
  <div class="container">
    <a href="/index.html" class="logo">
      <div class="logo-mark">M</div>
      <div class="logo-text">
        <div class="name">Maison Mikis</div>
        <div class="tag">Optique · Audition</div>
      </div>
    </a>
    <nav class="main-nav" id="mainNav">
      <a href="/index.html">La Boutique</a>
      <a href="/nos-conseils.html">Nos Conseils</a>
      <a href="/marques.html">Nos Marques</a>
      <a href="/espace-sante.html">Espace Santé</a>
      <a href="/espace-audition.html">Espace Audition</a>
      <a href="/actualites.html" class="active">Actualités</a>
      <a href="/contact.html">Contact</a>
    </nav>
    <div class="header-actions">
      <a href="tel:0182280018" class="header-phone">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
        01 82 28 00 18
      </a>
      <a href="/contact.html" class="btn btn-primary">Nous rendre visite</a>
      <button class="burger" id="burger" aria-label="Menu"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>
'''

FOOTER_HTML = '''<footer>
  <div class="container">
    <div class="footer-top">
      <div class="footer-logo">
        <div class="logo-mark" style="width:36px;height:36px;font-size:16px;">M</div>
        <div class="name">Maison Mikis</div>
      </div>
      <div class="footer-links">
        <div>
          <h4>Navigation</h4>
          <ul>
            <li><a href="/nos-conseils.html">Nos Conseils</a></li>
            <li><a href="/marques.html">Nos Marques</a></li>
            <li><a href="/espace-sante.html">Espace Santé</a></li>
            <li><a href="/espace-audition.html">Espace Audition</a></li>
            <li><a href="/actualites.html">Actualités</a></li>
          </ul>
        </div>
        <div>
          <h4>Contact</h4>
          <ul>
            <li>44 Avenue d'Ivry, 75013 Paris</li>
            <li>01 82 28 00 18</li>
            <li>mikis75013@gmail.com</li>
          </ul>
        </div>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© <span id="year"></span> Maison Mikis — Tous droits réservés.</span>
      <span>Optique · Audition · Paris 13e</span>
    </div>
  </div>
</footer>
'''

MODAL_HTML = '''<div class="article-modal-overlay" id="articleModalOverlay" aria-hidden="true">
  <div class="article-modal" role="dialog" aria-modal="true" aria-label="Article">
    <button type="button" class="article-modal-close" aria-label="Fermer l'article">✕</button>
    <div class="article-modal-body"></div>
  </div>
</div>
'''

# Le bloc <script> commun (reveal, burger, modal bulles) est identique sur toutes
# les pages articles : on le récupère depuis un article existant au premier import
# pour ne jamais désynchroniser une copie collée à la main.
_SCRIPT_CACHE = None


def common_script_block():
    global _SCRIPT_CACHE
    if _SCRIPT_CACHE is None:
        sample = os.path.join(ARTICLES_DIR, "fatigue-oculaire-ecrans.html")
        content = open(sample, encoding="utf-8").read()
        m = re.search(r"(<script>\n\n  document\.getElementById\('year'\).*?</script>)", content, re.S)
        _SCRIPT_CACHE = m.group(1)
    return _SCRIPT_CACHE


def render_article_page(a, body_html, all_articles, idx):
    v = css_version()
    breadcrumb_title = a["title"]
    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="google-site-verification" content="RFV22sLGR_g4pfYghQAlKFtBIV64vG5hz6ztsw15mFY" />
<title>{a["page_title"]}</title>
<meta name="description" content="{a["meta_description"]}">
<meta property="og:title" content="{a["page_title"]}">
<meta property="og:description" content="{a["meta_description"]}">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:url" content="https://www.maisonmikis.fr/actualites/{a["slug"]}.html">
<meta property="og:image" content="https://www.maisonmikis.fr/og-image.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="https://www.maisonmikis.fr/actualites/{a["slug"]}.html">
<meta name="robots" content="index, follow">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='48' fill='%23C1653B'/%3E%3Ctext x='50' y='66' font-size='48' text-anchor='middle' fill='%23FBF6EF' font-family='Georgia,serif'%3EM%3C/text%3E%3C/svg%3E">
{OPTICIAN_JSONLD}{breadcrumb_jsonld(breadcrumb_title, a["slug"])}{article_jsonld(a)}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,400&family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;500;700;800&family=Archivo+Black&family=Playfair+Display:ital,wght@0,500;0,600;1,500&family=Comfortaa:wght@600;700&family=Space+Grotesk:wght@700&family=Marcellus&family=Anton&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/site.css?v={v}">
<style>:root{{--hero-img:url('{a["image"]}');}}</style>
</head>
<body>

{HEADER_HTML}

<section class="page-hero">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / <a href="/actualites.html">Actualités</a> / {a["title"]}</div>
    <span class="eyebrow">{a["category_label"]}</span>
    <h1>{a["title"]}</h1>
    <div class="article-meta-row">
      <span class="article-tag" style="{a["accent_style"]}">{a["category_label"]}</span>
      <span class="article-date">{a["date_display"]}</span>
    </div>
  </div>
</section>

<section class="article-prose story-block">
  <div class="container-narrow">
    <div class="arch-frame reveal" style="margin-bottom:40px;aspect-ratio:16/9;border-radius:24px;">
      <img src="{a["image"]}" alt="{a["image_alt"]}">
    </div>
    {body_html}
    <div class="article-source-note">Contenu rédigé par l'équipe Maison Mikis à partir de sources professionnelles vérifiées (fabricants, presse spécialisée, autorités de santé), mis à jour en {date_display_from_iso(a["date_iso"])}.</div>
  </div>
</section>

<section class="related-articles story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">À lire aussi</span>
      <h2>D'autres articles qui pourraient vous intéresser</h2>
    </div>
    <div class="article-grid">
{render_related_cards(all_articles, idx)}    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Envie d'en discuter avec nous ?</h2>
    <p>Prenez rendez-vous en boutique, Galerie Oslo – Olympiades, pour un conseil personnalisé.</p>
    <a href="/contact.html" class="btn btn-primary">Prendre rendez-vous</a>
  </div>
</section>


{FOOTER_HTML}
{MODAL_HTML}
{common_script_block()}

</body>
</html>
'''


def rewrite_actualites_grid(articles):
    """Remplace tout le contenu de <div class="article-grid"> ... </div> par
    les cartes issues de `articles`, sans toucher au reste du fichier."""
    content = open(ACTUALITES_HTML, encoding="utf-8").read()
    pattern = re.compile(r'(<div class="article-grid">\n).*?(\n    </div>\n  </div>\n</section>)', re.S)
    m = pattern.search(content)
    if not m:
        raise RuntimeError("Marqueur de grille introuvable dans actualites.html — vérifier la structure avant de continuer.")
    new_grid = render_grid(articles)
    new_content = content[:m.start()] + m.group(1) + new_grid + m.group(2) + content[m.end():]
    with open(ACTUALITES_HTML, "w", encoding="utf-8") as f:
        f.write(new_content)


def rewrite_related_section(slug, articles, idx):
    """Met à jour uniquement le bloc 'à lire aussi' d'une page article déjà
    existante sur le disque, sans toucher au reste de la page (corps, meta...)."""
    path = os.path.join(ARTICLES_DIR, f"{slug}.html")
    content = open(path, encoding="utf-8").read()
    pattern = re.compile(
        r'(<section class="related-articles story-block">\s*<div class="container">\s*'
        r'<div class="section-head center">\s*<span class="eyebrow">À lire aussi</span>\s*'
        r'<h2>D\'autres articles qui pourraient vous intéresser</h2>\s*</div>\s*'
        r'<div class="article-grid">\n).*?(\n    </div>\n  </div>\n</section>)',
        re.S
    )
    m = pattern.search(content)
    if not m:
        raise RuntimeError(f"Marqueur 'à lire aussi' introuvable dans {slug}.html")
    new_related = render_related_cards(articles, idx)
    new_content = content[:m.start()] + m.group(1) + new_related + m.group(2) + content[m.end():]
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)


def sitemap_add_url(slug, date_iso):
    content = open(SITEMAP, encoding="utf-8").read()
    new_entry = (
        f"  <url>\n"
        f"    <loc>https://www.maisonmikis.fr/actualites/{slug}.html</loc>\n"
        f"    <lastmod>{date_iso}</lastmod>\n"
        f"    <changefreq>monthly</changefreq>\n"
        f"    <priority>0.6</priority>\n"
        f"  </url>\n"
    )
    content = content.replace("</urlset>", new_entry + "</urlset>")
    with open(SITEMAP, "w", encoding="utf-8") as f:
        f.write(content)
