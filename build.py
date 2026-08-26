#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build script for Maison Mikis multi-page site.
Generates static HTML files from shared header/footer/CSS + per-page content,
to avoid manually duplicating markup across files.
"""
import os
import re
import json
import hashlib

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://www.maisonmikis.fr"

# ----------------------------------------------------------------------------
# SHARED CSS (base, from original single-page site) + new components for
# multi-page layouts (page-hero, split-grid, story blocks)
# ----------------------------------------------------------------------------
SHARED_CSS = """
  :root{
    --cream:#FBF6EF;
    --cream-2:#F3EADD;
    --wood:#B98A5E;
    --wood-dark:#8C6239;
    --terracotta:#C1653B;
    --terracotta-dark:#A34F2C;
    --charcoal:#2B2621;
    --charcoal-soft:#4A4238;
    --sage:#8A9483;
    --line:#E4D8C6;
    --shadow: 0 20px 50px -20px rgba(43,38,33,0.25);
    --radius-arch: 200px 200px 12px 12px;
    --header-h: 70px;
    /* Cadrage vertical par defaut des photos de bandeau. Surchargeable page
       par page via hero_pos dans render_page(). */
    --hero-pos: 15%;
  }
  *{margin:0;padding:0;box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{
    font-family:'Inter',sans-serif;
    color:var(--charcoal);
    background:var(--cream);
    line-height:1.6;
    -webkit-font-smoothing:antialiased;
    overflow-x:hidden;
    /* Le header est desormais opaque en permanence (31/07/2026) : on decale
       tout le contenu de sa hauteur pour que la photo commence sous le menu
       au lieu de passer derriere. */
    padding-top:var(--header-h);
  }
  h1,h2,h3,h4{font-family:'Fraunces',serif;font-weight:500;line-height:1.15;color:var(--charcoal);}
  a{text-decoration:none;color:inherit;}
  ul{list-style:none;}
  img{max-width:100%;display:block;}
  .container{max-width:1180px;margin:0 auto;padding:0 28px;}
  .container-narrow{max-width:760px;margin:0 auto;padding:0 28px;}
  .eyebrow{
    font-family:'Inter',sans-serif;
    text-transform:uppercase;
    letter-spacing:0.18em;
    font-size:12.5px;
    font-weight:600;
    color:var(--terracotta);
    display:inline-block;
    margin-bottom:14px;
  }
  .section-head{max-width:640px;margin-bottom:56px;}
  .section-head h2{font-size:clamp(28px,3.6vw,42px);margin-bottom:14px;}
  .section-head p{color:var(--charcoal-soft);font-size:16.5px;}
  .section-head.center{margin-left:auto;margin-right:auto;text-align:center;}
  section{padding:110px 0;}
  .btn{
    display:inline-flex;align-items:center;gap:10px;
    padding:15px 30px;border-radius:100px;
    font-weight:600;font-size:14.5px;letter-spacing:0.02em;
    transition:all .25s ease; border:1.5px solid transparent; cursor:pointer;
  }
  .btn-primary{background:var(--terracotta);color:var(--cream);}
  .btn-primary:hover{background:var(--terracotta-dark);transform:translateY(-2px);box-shadow:0 12px 24px -10px rgba(163,79,44,0.55);}
  .btn-ghost{border-color:rgba(251,246,239,0.55);color:var(--cream);}
  .btn-ghost:hover{background:rgba(251,246,239,0.12);}
  .btn-outline{border-color:var(--wood-dark);color:var(--charcoal);}
  .btn-outline:hover{background:var(--wood-dark);color:var(--cream);}

  /* HEADER */
  header{
    position:fixed;top:0;left:0;right:0;z-index:100;
    padding:22px 0; transition:all .35s ease;
  }
  header.scrolled{
    background:rgba(251,246,239,0.92);
    backdrop-filter:blur(10px);
    padding:14px 0;
    box-shadow:0 4px 24px -12px rgba(43,38,33,0.15);
  }
  header .container{display:flex;align-items:center;justify-content:space-between;}
  .logo{display:flex;align-items:center;gap:12px;font-family:'Fraunces',serif;}
  .logo-mark{
    width:42px;height:42px;border-radius:50%;background:var(--terracotta);
    color:var(--cream);display:flex;align-items:center;justify-content:center;
    font-size:19px;flex-shrink:0;
  }
  .logo{flex-shrink:0;}
  .logo-text{line-height:1.1;}
  .logo-text .name{font-size:17px;font-weight:600;color:var(--cream);transition:color .35s;white-space:nowrap;}
  header.scrolled .logo-text .name{color:var(--charcoal);}
  .logo-text .tag{font-family:'Inter',sans-serif;font-size:10px;letter-spacing:0.08em;text-transform:uppercase;color:rgba(251,246,239,0.75);transition:color .35s;white-space:nowrap;}
  header.scrolled .logo-text .tag{color:var(--wood-dark);}
  /* La marge negative compense le rembourrage horizontal des bulles : sans
     elle, les six onglets occuperaient ~120px de plus qu'avant et viendraient
     toucher le logo autour de 1000px de large. */
  nav.main-nav{display:flex;align-items:center;gap:0;flex-shrink:1;margin:0 -12px;}
  nav.main-nav a{
    font-size:13px;font-weight:500;color:var(--cream);position:relative;
    padding:8px 12px;border-radius:100px;border:1px solid transparent;
    transition:color .35s, background .25s ease, border-color .25s ease;white-space:nowrap;
  }
  header.scrolled nav.main-nav a{color:var(--charcoal-soft);}
  nav.main-nav a:hover{color:var(--terracotta);}
  /* Onglet de la page en cours : bulle « voile translucide » (piste 1 validee
     par le client le 30/07/2026). Le marquage .active est deja emis par
     render_header(), donc c'est un changement purement CSS. */
  nav.main-nav a.active{
    background:rgba(251,246,239,0.18);
    border-color:rgba(251,246,239,0.30);
    color:var(--cream);
  }
  header.scrolled nav.main-nav a.active{
    background:rgba(193,101,59,0.10);
    border-color:rgba(193,101,59,0.22);
    color:var(--terracotta);
  }
  .header-actions{display:flex;align-items:center;gap:14px;flex-shrink:0;}
  .header-phone-bubble{
    display:flex;align-items:center;gap:7px;white-space:nowrap;
    background:var(--terracotta);color:var(--cream);
    font-size:13px;font-weight:600;
    padding:9px 18px;border-radius:100px;border:1.5px solid transparent;
    transition:background .25s ease, transform .25s ease, box-shadow .25s ease;
  }
  .header-phone-bubble:hover{background:var(--terracotta-dark);transform:translateY(-2px);box-shadow:0 10px 20px -10px rgba(163,79,44,0.55);}
  .burger{display:none;width:26px;height:20px;position:relative;cursor:pointer;background:none;border:none;}
  .burger span{position:absolute;left:0;right:0;height:2px;background:var(--cream);transition:all .3s;}
  header.scrolled .burger span{background:var(--charcoal);}
  .burger span:nth-child(1){top:0;} .burger span:nth-child(2){top:9px;} .burger span:nth-child(3){top:18px;}

  /* HERO — boutons d'appel a l'action du bandeau.
     Les regles .hero / .hero::after / .hero-content ont ete retirees le
     06/08/2026 : plus aucune page ne portait class="hero" (tous les bandeaux
     utilisent .page-hero), et .hero pointait encore sur une image picsum.photos
     externe. Ne pas les reintroduire. */
  .hero-actions{display:flex;gap:16px;flex-wrap:wrap;}
  .hero-scroll{
    position:absolute;bottom:36px;left:50%;transform:translateX(-50%);z-index:2;
    color:var(--cream);font-size:11px;letter-spacing:0.15em;text-transform:uppercase;
    display:flex;flex-direction:column;align-items:center;gap:10px;opacity:.85;
  }
  .hero-scroll .line{width:1px;height:34px;background:rgba(251,246,239,0.6);animation:scrollLine 1.8s infinite;}
  @keyframes scrollLine{0%{transform:scaleY(0);transform-origin:top;}50%{transform:scaleY(1);transform-origin:top;}51%{transform-origin:bottom;}100%{transform:scaleY(0);transform-origin:bottom;}}

  /* PAGE HERO (inner pages) */
  .page-hero{
    position:relative;padding:56px 0 56px;color:var(--cream);
    /* 31/07/2026 : cadrage descendu (demande du client). Le bandeau garde sa
       hauteur, on remonte la fenetre de cadrage dans l'image (15% au lieu de
       50%) : la photo parait descendue et c'est son bas qui est rogne. */
    background:linear-gradient(180deg, rgba(43,38,33,0.62), rgba(43,38,33,0.78)),
      var(--hero-img) center var(--hero-pos, 15%)/cover no-repeat;
  }
  .page-hero .eyebrow{color:#E7B08C;}
  .page-hero h1{color:var(--cream);font-size:clamp(32px,4.6vw,52px);max-width:760px;}
  .page-hero p{color:rgba(251,246,239,0.85);max-width:600px;margin-top:16px;font-size:16.5px;}
  .page-hero.page-hero--compact{padding:58px 0 41px;}
  .breadcrumb{font-size:12.5px;color:rgba(251,246,239,0.65);margin-bottom:18px;}
  .breadcrumb a{color:rgba(251,246,239,0.85);}
  .breadcrumb a:hover{color:var(--cream);text-decoration:underline;}

  /* PAGE HERO — SCROLLING PHOTO MARQUEE (defile de mode) */
  .hero-marquee{
    position:relative;min-height:267px;overflow:hidden;
    padding:100px 0 37px; /* hauteur de bandeau conservee : le contenu est cale en bas, ce padding pilote la hauteur de la frise */
    display:flex;align-items:flex-end;background:var(--wood-dark);
  }
  .hero-marquee-track{
    position:absolute;inset:0;display:flex;align-items:stretch;gap:5px;
    width:max-content;animation:marqueeScroll 160s linear infinite;
    will-change:transform;
  }
  .hero-marquee-track img{
    height:100%;width:auto;aspect-ratio:3/4;object-fit:cover;flex:none;
    filter:sepia(22%) saturate(74%) contrast(103%) brightness(109%) grayscale(6%);
  }
  .hero-marquee-overlay{
    position:absolute;inset:0;pointer-events:none;
    background:linear-gradient(180deg, rgba(74,56,33,0.12) 0%, rgba(74,56,33,0.22) 45%, rgba(43,38,33,0.62) 100%);
  }
  .hero-marquee .container{position:relative;z-index:2;}
  .hero-marquee .breadcrumb,
  .hero-marquee .eyebrow{color:rgba(251,246,239,0.9);}
  @keyframes marqueeScroll{from{transform:translateX(0);}to{transform:translateX(-50%);}}
  @media (prefers-reduced-motion: reduce){.hero-marquee-track{animation:none;}}

  /* ARCH IMAGE FRAME */
  .arch-frame{
    border-radius:var(--radius-arch);
    overflow:hidden;box-shadow:var(--shadow);
    aspect-ratio:3/4;position:relative;
  }
  .arch-frame img{width:100%;height:100%;object-fit:cover;filter:sepia(18%) saturate(115%) contrast(102%);}

  /* SPLIT / STORY BLOCKS (reusable across pages) */
  .split{background:var(--cream);}
  .split.alt{background:var(--cream-2);}
  .split-grid{display:grid;grid-template-columns:1fr 1fr;gap:70px;align-items:center;}
  .split-grid .split-text{order:1;}
  .split-grid .arch-frame{order:2;}
  .split-grid.reverse .split-text{order:2;}
  .split-grid.reverse .arch-frame{order:1;}
  .split-text .eyebrow{color:var(--terracotta);}
  .split-text h2{font-size:clamp(26px,3.2vw,36px);margin-bottom:20px;}
  .split-text p{color:var(--charcoal-soft);margin-bottom:16px;font-size:16px;}
  .split-text .check-list{margin-top:20px;display:flex;flex-direction:column;gap:14px;}
  .split-text .check-list li{display:flex;gap:12px;align-items:flex-start;font-size:14.5px;color:var(--charcoal-soft);}
  .split-text .check-list .check{
    width:20px;height:20px;border-radius:50%;background:var(--sage);color:var(--cream);
    display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:11px;margin-top:2px;
  }
  .story-block + .story-block{border-top:1px solid var(--line);}
  .story-block{padding:86px 0;}

  .founders{
    margin-top:28px;display:flex;gap:14px;align-items:center;
    padding:18px 22px;background:var(--cream-2);border-radius:16px;border:1px solid var(--line);
  }
  .founders .initials{display:flex;}
  .founders .initials span{
    width:40px;height:40px;border-radius:50%;background:var(--wood);color:var(--cream);
    display:flex;align-items:center;justify-content:center;font-family:'Fraunces',serif;font-size:15px;
    border:2px solid var(--cream-2);margin-left:-10px;
  }
  .founders .initials span:first-child{margin-left:0;}
  .founders .meta{font-size:13.5px;color:var(--charcoal-soft);}
  .founders .meta strong{color:var(--charcoal);display:block;font-size:14.5px;font-family:'Fraunces',serif;font-weight:500;}

  .pull-quote{
    font-family:'Fraunces',serif;font-style:italic;font-weight:500;
    font-size:clamp(20px,2.4vw,27px);line-height:1.4;color:var(--wood-dark);
    border-left:3px solid var(--terracotta);padding:6px 0 6px 26px;margin:34px 0;
  }

  /* SERVICES GRID (teasers) */
  .services{background:var(--cream-2);}
  .services-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;}
  .service-card{
    background:var(--cream);padding:36px 26px;border-radius:20px;border:1px solid var(--line);
    transition:all .3s ease;
  }
  .service-card:hover{transform:translateY(-6px);box-shadow:var(--shadow);border-color:transparent;}
  .service-icon{
    width:56px;height:56px;border-radius:16px;background:var(--terracotta);
    display:flex;align-items:center;justify-content:center;margin-bottom:22px;color:var(--cream);
  }
  .service-card h3{font-size:19px;margin-bottom:10px;}
  .service-card p{font-size:14.5px;color:var(--charcoal-soft);}
  .service-card .more{display:inline-block;margin-top:14px;font-size:13.5px;font-weight:600;color:var(--terracotta);}

  /* HOMEPAGE — aperçu des 4 univers (cartes photo) */
  .services-refined{background:var(--cream-2);padding:96px 0;}
  .section-head-split{
    display:grid;grid-template-columns:1.1fr 0.9fr;gap:40px;align-items:end;
    margin-bottom:56px;padding-bottom:28px;border-bottom:1px solid var(--line);
  }
  .section-head-split h2{font-size:clamp(28px,3.2vw,36px);margin-top:10px;}
  .section-head-split > p{color:var(--charcoal-soft);font-size:15.5px;max-width:420px;margin:0;}
  .refined-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;}
  .refined-card{
    display:block;background:var(--cream);border-radius:20px;overflow:hidden;
    border:1px solid var(--line);text-decoration:none;color:inherit;
    transition:transform .35s ease, box-shadow .35s ease, border-color .35s ease;
  }
  .refined-card:hover{transform:translateY(-6px);box-shadow:var(--shadow);border-color:transparent;}
  .refined-photo{
    position:relative;height:148px;background:var(--img) center/cover no-repeat;
    transition:transform .6s ease;
  }
  .refined-photo::after{
    content:"";position:absolute;inset:0;
    background:linear-gradient(180deg, rgba(43,38,33,0) 55%, rgba(43,38,33,0.4) 100%);
  }
  .refined-card:hover .refined-photo{transform:scale(1.07);}
  .refined-icon{
    position:absolute;left:18px;bottom:-22px;z-index:2;width:44px;height:44px;border-radius:13px;
    background:var(--terracotta);color:var(--cream);display:flex;align-items:center;justify-content:center;
    box-shadow:0 10px 22px -8px rgba(43,38,33,0.45);transition:background .3s ease;
  }
  .refined-card:hover .refined-icon{background:var(--terracotta-dark);}
  .refined-body{padding:36px 22px 26px;}
  .refined-body h3{font-size:19px;margin-bottom:9px;}
  .refined-body p{font-size:14px;color:var(--charcoal-soft);margin-bottom:15px;}
  .refined-body .more{display:inline-block;font-size:13.5px;font-weight:600;color:var(--terracotta);transition:transform .25s ease;}
  .refined-card:hover .more{transform:translateX(3px);}
  @media (max-width:900px){.refined-grid{grid-template-columns:repeat(2,1fr);}}
  @media (max-width:760px){
    .section-head-split{grid-template-columns:1fr;gap:14px;}
    .refined-grid{grid-template-columns:1fr;}
  }

  /* AMBIANCE GALLERY */
  .ambiance{background:var(--cream);}
  .ambiance-grid{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:22px;align-items:end;}
  .ambiance-grid .arch-frame:first-child{aspect-ratio:4/5;}
  .ambiance-grid .arch-frame{aspect-ratio:3/4;}
  .ambiance-caption{
    margin-top:34px;text-align:center;color:var(--charcoal-soft);font-family:'Fraunces',serif;
    font-style:italic;font-size:18px;
  }

  /* MARQUES */
  .marques{background:var(--cream-2);}
  .marques-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:18px;}
  .marque-item{
    background:var(--cream);border:1px solid var(--line);border-radius:14px;
    padding:26px 18px;display:flex;align-items:center;justify-content:center;
    font-family:'Fraunces',serif;font-size:17px;color:var(--wood-dark);text-align:center;
    min-height:88px;transition:all .25s;
  }
  .marque-item:hover{border-color:var(--terracotta);color:var(--terracotta);}

  /* BRAND STATS STRIP (page Nos Marques) */
  .brand-stats{display:flex;justify-content:center;gap:14px;flex-wrap:wrap;margin:26px 0 6px;}
  .brand-stat{
    display:flex;align-items:baseline;gap:8px;background:var(--cream);border:1px solid var(--line);
    border-radius:100px;padding:10px 22px;
  }
  .brand-stat strong{font-family:'Fraunces',serif;font-size:20px;color:var(--terracotta);}
  .brand-stat span{font-size:12.5px;text-transform:uppercase;letter-spacing:0.06em;color:var(--charcoal-soft);font-weight:600;}

  /* BRAND CARDS (page Nos Marques) */
  .brand-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;}
  .brand-card{
    background:var(--cream);border:1px solid var(--line);border-radius:22px;
    padding:0 0 30px;overflow:hidden;transition:transform .3s ease, box-shadow .3s ease, border-color .3s ease;
    position:relative;
  }
  .brand-card::before{
    content:"";display:block;height:7px;
    background:linear-gradient(90deg, var(--accent,var(--terracotta)), var(--accent,var(--terracotta)) 40%, transparent 40%, transparent 100%);
    background-size:200% 100%;background-position:0 0;
    transition:background-position .35s ease;
  }
  .brand-card:hover::before{background-position:-100% 0;}
  .brand-card:hover{transform:translateY(-7px);box-shadow:var(--shadow);border-color:transparent;}
  .brand-card-body{padding:26px 26px 0;}
  .brand-logo-plate{
    background:var(--accent-bg,var(--cream-2));border-radius:14px;padding:20px 22px;
    display:flex;align-items:center;min-height:64px;margin-bottom:18px;transition:transform .3s ease;
  }
  .brand-card:hover .brand-logo-plate{transform:scale(1.04);}
  .brand-wordmark{font-size:23px;color:var(--charcoal);line-height:1.15;}
  .brand-logo{display:block;max-width:150px;max-height:42px;width:auto;height:auto;object-fit:contain;object-position:left center;}
  .brand-meta{
    display:inline-flex;align-items:center;gap:6px;font-size:11.5px;text-transform:uppercase;letter-spacing:0.07em;
    color:var(--accent,var(--terracotta));font-weight:700;margin-bottom:14px;
    background:var(--accent-bg,rgba(193,101,59,0.12));padding:6px 13px;border-radius:100px;
  }
  .brand-card p{font-size:14px;color:var(--charcoal-soft);padding:0 26px;line-height:1.55;}

  /* Wordmark type treatments — fonts chosen to evoke each maison's real
     visual identity as closely as free web fonts allow. These are NOT the
     brands' actual proprietary logo artwork (those are bespoke, unlicensed
     custom typefaces) — just a stylistic nod using freely licensed fonts. */
  .wm-stencil{font-family:'Poppins',sans-serif;font-weight:800;text-transform:uppercase;letter-spacing:-0.01em;}                 /* Ray-Ban — bold, sporty */
  .wm-serif-caps{font-family:'Archivo Black',sans-serif;text-transform:uppercase;letter-spacing:0.01em;}                        /* Fendi — chunky, bold */
  .wm-script{font-family:'Playfair Display',serif;font-style:italic;font-weight:500;}                                           /* Fred — elegant jewelry italic */
  .wm-thin-caps-a{font-family:'Inter',sans-serif;font-weight:300;text-transform:uppercase;letter-spacing:0.18em;}               /* Loewe — minimal thin wide */
  .wm-thin-caps-b{font-family:'Inter',sans-serif;font-weight:400;text-transform:uppercase;letter-spacing:0.14em;}               /* Celine — thin caps */
  .wm-lower-bold{font-family:'Poppins',sans-serif;font-weight:700;text-transform:lowercase;letter-spacing:-0.01em;}             /* Marc Jacobs — bold lowercase */
  .wm-geo-caps{font-family:'Poppins',sans-serif;font-weight:800;text-transform:uppercase;letter-spacing:0.02em;}                /* Prada — bold geometric caps */
  .wm-plain{font-family:'Inter',sans-serif;font-weight:500;}                                                                    /* Andy Brook — simple, clean */
  .wm-lower-round{font-family:'Comfortaa',sans-serif;font-weight:600;text-transform:lowercase;letter-spacing:0.01em;}           /* CHIMI — rounded Scandinavian */
  .wm-italic{font-family:'Fraunces',serif;font-style:italic;font-weight:500;}                                                   /* Miu Miu — playful serif italic */
  .wm-lower-wide{font-family:'Space Grotesk',sans-serif;font-weight:700;text-transform:lowercase;letter-spacing:0.02em;}        /* LOOL — geometric, architectural */
  .wm-classic-serif{font-family:'Playfair Display',serif;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;}       /* Ralph Lauren — heritage serif */
  .wm-thin-wide{font-family:'Inter',sans-serif;font-weight:200;text-transform:uppercase;letter-spacing:0.24em;}                 /* Armani — ultra-thin, luxe */
  .wm-elegant-caps{font-family:'Marcellus',serif;text-transform:uppercase;letter-spacing:0.08em;}                               /* Longchamp — refined inscription serif */
  .wm-bold-condensed{font-family:'Anton',sans-serif;text-transform:uppercase;letter-spacing:0.01em;}                            /* Guess — bold blocky impact */
  .wm-wide-caps{font-family:'Inter',sans-serif;font-weight:500;text-transform:uppercase;letter-spacing:0.2em;}                  /* Givenchy — fallback en attente du vrai logo */

  /* BRAND PILLS (homepage teaser) */
  .brand-pills{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;}
  .brand-pill{
    padding:10px 22px;background:var(--cream);border:1px solid var(--line);border-radius:100px;
    font-size:13.5px;font-weight:600;color:var(--charcoal-soft);
  }

  /* AUDITION — signes / auto-évaluation */
  .check-list-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px 32px;margin-top:8px;}
  .check-list-grid li{display:flex;gap:12px;align-items:flex-start;font-size:15px;color:var(--charcoal-soft);}
  .check-list-grid .check{
    width:22px;height:22px;border-radius:50%;background:var(--terracotta);color:var(--cream);
    display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:12px;margin-top:1px;
  }

  /* AUDITION — degrés de perte auditive */
  .degree-scale{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;}
  .degree-card{
    background:var(--cream);border:1px solid var(--line);border-radius:18px;
    padding:26px 22px;position:relative;overflow:hidden;
  }
  .degree-card::before{content:"";position:absolute;top:0;left:0;right:0;height:6px;background:var(--bar,var(--terracotta));}
  .degree-card .db{font-family:'Fraunces',serif;font-size:15px;color:var(--terracotta-dark);font-weight:500;margin-bottom:6px;}
  .degree-card h3{font-size:17px;margin-bottom:8px;}
  .degree-card p{font-size:13.5px;color:var(--charcoal-soft);}

  /* AUDITION — types d'appareils */
  .device-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;}
  .device-card{
    background:var(--cream-2);border:1px solid var(--line);border-radius:20px;padding:32px 28px;
  }
  .device-card .discretion{display:flex;gap:5px;margin-bottom:16px;}
  .device-card .discretion span{width:22px;height:6px;border-radius:3px;background:var(--line);}
  .device-card .discretion span.on{background:var(--terracotta);}
  .device-card h3{font-size:19px;margin-bottom:10px;}
  .device-card p{font-size:14.5px;color:var(--charcoal-soft);margin-bottom:12px;}
  .device-card .suited{font-size:12px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:var(--wood-dark);}

  /* AUDITION — 100% Santé / reste à charge */
  .reimburse-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;}
  .reimburse-card{background:var(--cream);border:1px solid var(--line);border-radius:20px;padding:32px 30px;}
  .reimburse-card.highlight{border-color:var(--terracotta);box-shadow:var(--shadow);}
  .reimburse-card .tag{
    display:inline-block;font-size:11.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:700;
    color:var(--terracotta);background:rgba(193,101,59,0.1);padding:5px 12px;border-radius:100px;margin-bottom:14px;
  }
  .reimburse-card h3{font-size:20px;margin-bottom:10px;}
  .reimburse-card p{font-size:14.5px;color:var(--charcoal-soft);}

  /* AUDITION — FAQ accordion */
  .faq-list{display:flex;flex-direction:column;gap:12px;max-width:780px;margin:0 auto;}
  .faq-item{background:var(--cream);border:1px solid var(--line);border-radius:16px;padding:6px 26px;}
  .faq-item summary{
    list-style:none;cursor:pointer;padding:20px 0;font-family:'Fraunces',serif;font-size:17px;
    display:flex;justify-content:space-between;align-items:center;gap:16px;color:var(--charcoal);
  }
  .faq-item summary::-webkit-details-marker{display:none;}
  .faq-item summary .plus{
    width:26px;height:26px;border-radius:50%;border:1.5px solid var(--terracotta);color:var(--terracotta);
    display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:15px;transition:transform .25s;
  }
  .faq-item[open] summary .plus{transform:rotate(45deg);}
  .faq-item p{font-size:14.5px;color:var(--charcoal-soft);padding-bottom:22px;}

  /* ACTUALITÉS — filtre par thématique */
  .article-filter-bar{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-bottom:48px;}
  .filter-pill{
    padding:9px 20px;border-radius:100px;border:1.5px solid var(--line);background:var(--cream);
    font-size:13px;font-weight:600;color:var(--charcoal-soft);cursor:pointer;transition:all .2s ease;
    font-family:'Inter',sans-serif;
  }
  .filter-pill:hover{border-color:var(--terracotta);color:var(--terracotta);}
  .filter-pill.active{background:var(--terracotta);border-color:var(--terracotta);color:var(--cream);}

  /* ACTUALITÉS — grille d'articles ("bulles" cliquables : voir .article-modal-* plus bas) */
  .article-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:28px;}
  .article-card{
    background:var(--cream);border:1px solid var(--line);border-radius:28px;overflow:hidden;cursor:pointer;
    transition:transform .3s ease, box-shadow .3s ease, border-color .3s ease; display:flex; flex-direction:column;
  }
  .article-card:hover{transform:translateY(-6px) scale(1.015);box-shadow:var(--shadow);border-color:transparent;}
  .article-card .article-img{aspect-ratio:4/3;overflow:hidden;}
  .article-card .article-img img{width:100%;height:100%;object-fit:cover;filter:sepia(14%) saturate(108%) contrast(101%);transition:transform .4s ease;}
  .article-card:hover .article-img img{transform:scale(1.06);}
  .article-card-body{padding:24px 24px 28px;display:flex;flex-direction:column;flex:1;}
  .article-tag{
    display:inline-flex;align-self:flex-start;align-items:center;font-size:11.5px;text-transform:uppercase;
    letter-spacing:0.07em;color:var(--accent,var(--terracotta));font-weight:700;
    background:var(--accent-bg,rgba(193,101,59,0.12));padding:6px 13px;border-radius:100px;margin-bottom:14px;
  }
  .article-card h3{font-size:19px;margin-bottom:10px;line-height:1.3;}
  .article-card p{font-size:14px;color:var(--charcoal-soft);margin-bottom:16px;flex:1;}
  .article-card .article-meta{font-size:12.5px;color:var(--charcoal-soft);display:flex;justify-content:space-between;align-items:center;margin-top:auto;}
  .article-card .article-meta .more{font-weight:600;color:var(--terracotta);display:inline-flex;align-items:center;gap:5px;}

  /* ARTICLE — page individuelle */
  .article-meta-row{display:flex;gap:14px;align-items:center;margin-top:18px;flex-wrap:wrap;}
  .article-meta-row .article-tag{margin-bottom:0;}
  .article-meta-row .article-date{font-size:13px;color:rgba(251,246,239,0.75);}
  .article-prose{background:var(--cream);}
  .article-prose h2{font-size:clamp(22px,2.6vw,28px);margin:44px 0 16px;}
  .article-prose h2:first-child{margin-top:0;}
  .article-prose p{font-size:16px;color:var(--charcoal-soft);margin-bottom:18px;line-height:1.75;}
  .article-prose .check-list{display:flex;flex-direction:column;gap:12px;margin:22px 0;}
  .article-prose .check-list li{display:flex;gap:12px;align-items:flex-start;font-size:15px;color:var(--charcoal-soft);}
  .article-prose .check-list .check{
    width:20px;height:20px;border-radius:50%;background:var(--sage);color:var(--cream);
    display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:11px;margin-top:2px;
  }
  .article-prose .pull-quote{margin:30px 0;}

  /* ====================================================================
     GABARIT SEO EDITORIAL (31/07/2026, soir)
     1. .answer-lead  : reponse directe de 40-60 mots placee juste sous le
        titre. C'est ce bloc que Google et les moteurs de reponse IA
        extraient en priorite. Doit rester court : au-dela de ~60 mots il
        cesse d'etre extractible tel quel.
     2. .article-prose h3 / table / ol : sous-niveaux, tableaux
        comparatifs et listes numerotees, formats les plus repris par les
        AI Overviews et les extraits enrichis.
     3. .article-faq  : FAQ VISIBLE en HTML. Le rich result FAQ a ete
        supprime par Google en mai-juin 2026, mais le format reste lu par
        les moteurs de reponse et utile au lecteur — on le garde donc en
        HTML lisible, sans compter sur un affichage enrichi.
     ==================================================================== */
  .answer-lead{
    margin:0 0 34px;padding:22px 26px;background:var(--cream-2);
    border:1px solid var(--line);border-left:3px solid var(--sage);border-radius:16px;
  }
  .answer-lead p{font-size:17px;line-height:1.65;color:var(--charcoal);margin-bottom:0;font-weight:500;}
  .answer-lead .eyebrow{margin-bottom:8px;display:block;}

  .article-prose h3{font-size:clamp(17px,1.9vw,20px);margin:30px 0 12px;color:var(--charcoal);}
  .article-prose ol{margin:20px 0 24px;padding-left:22px;list-style:decimal;}
  .article-prose ol li{font-size:15.5px;color:var(--charcoal-soft);line-height:1.7;margin-bottom:10px;padding-left:4px;}
  .article-prose ul.plain-list{margin:20px 0 24px;padding-left:20px;list-style:disc;}
  .article-prose ul.plain-list li{font-size:15.5px;color:var(--charcoal-soft);line-height:1.7;margin-bottom:9px;}

  .table-wrap{overflow-x:auto;margin:26px 0 30px;-webkit-overflow-scrolling:touch;}
  .article-prose table{
    width:100%;border-collapse:collapse;font-size:14.5px;background:var(--cream-2);
    border:1px solid var(--line);border-radius:14px;overflow:hidden;
  }
  .article-prose thead th{
    background:var(--sage);color:var(--cream);text-align:left;font-weight:600;
    padding:12px 16px;font-size:13.5px;letter-spacing:.02em;
  }
  .article-prose tbody td{
    padding:12px 16px;border-top:1px solid var(--line);color:var(--charcoal-soft);
    line-height:1.6;vertical-align:top;
  }
  .article-prose tbody tr td:first-child{font-weight:600;color:var(--charcoal);}

  .article-faq{margin:46px 0 4px;}
  .article-faq h2{margin-bottom:8px;}
  .article-faq .faq-intro{font-size:15px;color:var(--charcoal-soft);margin-bottom:22px;}
  .article-faq .faq-item{
    padding:20px 24px;background:var(--cream-2);border:1px solid var(--line);
    border-radius:14px;margin-bottom:12px;
  }
  .article-faq .faq-item h3{margin:0 0 8px;font-size:16.5px;line-height:1.4;}
  .article-faq .faq-item p{font-size:15px;margin-bottom:0;}

  .article-source-note{
    margin-top:40px;padding:18px 22px;background:var(--cream-2);border-radius:14px;
    font-size:12.5px;color:var(--charcoal-soft);border:1px solid var(--line);
  }
  .related-articles{background:var(--cream-2);}

  /* ====================================================================
     MAILLAGE INTERNE (31/07/2026)
     Les liens du corps de page etaient invisibles : la regle globale
     a{text-decoration:none;color:inherit} les rendait indistinguables du
     texte. On style donc explicitement les liens contextuels, dans les
     articles comme dans les pages (classe .ilink).
     ==================================================================== */
  .article-prose p a, .article-prose li a, .ilink{
    color:var(--terracotta-dark);
    border-bottom:1px solid rgba(193,101,59,0.38);
    transition:color .2s ease, border-color .2s ease;
  }
  .article-prose p a:hover, .article-prose li a:hover, .ilink:hover{
    color:var(--terracotta);border-bottom-color:var(--terracotta);
  }

  /* --------------------------------------------------------------------
     COMPLEMENT 06/08/2026 — la classe .ilink ecrite le 31/07 n'a jamais ete
     posee dans le HTML : les liens contextuels des PAGES (hors articles)
     restaient donc invisibles, notamment les 3 renvois de contact.html vers
     l'Espace Sante. On cible desormais directement les <p> de corps de page.
     Deux variantes : sombre sur fond clair, creme sur fond fonce/terracotta.
     :not(.btn) preserve les boutons, .breadcrumb et .block-more ne sont pas
     dans des <p> et ne sont donc pas touches.
     -------------------------------------------------------------------- */
  .split-text p a:not(.btn), .section-head p a:not(.btn),
  .faq-item p a:not(.btn), .marques-intro p a:not(.btn),
  .legal p a:not(.btn), .legal li a:not(.btn){
    color:var(--terracotta-dark);
    border-bottom:1px solid rgba(193,101,59,0.38);
    transition:color .2s ease, border-color .2s ease;
  }
  .split-text p a:not(.btn):hover, .section-head p a:not(.btn):hover,
  .faq-item p a:not(.btn):hover, .marques-intro p a:not(.btn):hover,
  .legal p a:not(.btn):hover, .legal li a:not(.btn):hover{
    color:var(--terracotta);border-bottom-color:var(--terracotta);
  }
  .cta-band p a:not(.btn), .dark-card p a:not(.btn),
  .dark-section .section-head p a:not(.btn){
    color:var(--cream);
    border-bottom:1px solid rgba(251,246,239,0.45);
    transition:border-color .2s ease;
  }
  .cta-band p a:not(.btn):hover, .dark-card p a:not(.btn):hover,
  .dark-section .section-head p a:not(.btn):hover{
    border-bottom-color:var(--cream);
  }

  /* Encadre "Pour aller plus loin", en fin de corps d'article */
  .go-further{
    margin:46px 0 4px;padding:26px 28px;background:var(--cream-2);
    border:1px solid var(--line);border-left:3px solid var(--terracotta);
    border-radius:16px;
  }
  .go-further .eyebrow{margin-bottom:8px;}
  .go-further h3{font-size:19px;margin-bottom:18px;}
  .go-further ul{display:flex;flex-direction:column;gap:14px;}
  .go-further li{display:flex;gap:12px;align-items:flex-start;}
  .go-further .arrow{color:var(--terracotta);flex-shrink:0;font-size:13px;line-height:1.7;}
  .article-prose .go-further a, .go-further a{
    font-weight:600;color:var(--charcoal);font-size:15px;line-height:1.45;border-bottom:none;
  }
  .article-prose .go-further a:hover, .go-further a:hover{color:var(--terracotta);border-bottom:none;}
  .go-further .go-desc{display:block;font-weight:400;font-size:13.5px;color:var(--charcoal-soft);margin-top:3px;}

  /* Lien discret en fin de bloc de page (accueil, pages de service) */
  .block-more{
    display:inline-block;margin-top:22px;font-size:14px;font-weight:600;
    color:var(--terracotta);border-bottom:1px solid rgba(193,101,59,0.4);
    transition:color .2s ease,border-color .2s ease;
  }
  .block-more:hover{color:var(--terracotta-dark);border-bottom-color:var(--terracotta-dark);}
  .block-more-center{text-align:center;margin-top:36px;}

  /* ACTUALITÉS — bulle agrandie (modale) : le contenu complet de l'article est
     chargé depuis sa page dédiée (fetch) et affiché sans quitter la page en
     cours, tout en gardant cette page dédiée pleinement fonctionnelle pour le
     SEO, le partage de lien et la navigation sans JavaScript. */
  .article-modal-overlay{
    position:fixed;inset:0;background:rgba(43,38,33,0.55);backdrop-filter:blur(3px);
    display:flex;align-items:center;justify-content:center;padding:24px;
    z-index:999;opacity:0;visibility:hidden;transition:opacity .3s ease, visibility .3s ease;
  }
  .article-modal-overlay.open{opacity:1;visibility:visible;}
  .article-modal{
    background:var(--cream);border-radius:32px;max-width:800px;width:100%;max-height:88vh;
    overflow-y:auto;position:relative;box-shadow:0 40px 100px -20px rgba(43,38,33,0.5);
    transform:scale(0.92) translateY(20px);opacity:0;
    transition:transform .35s cubic-bezier(.2,.8,.2,1), opacity .3s ease;
  }
  .article-modal-overlay.open .article-modal{transform:scale(1) translateY(0);opacity:1;}
  .article-modal-close{
    position:absolute;top:18px;right:18px;width:40px;height:40px;border-radius:50%;
    background:var(--cream);border:1px solid var(--line);display:flex;align-items:center;justify-content:center;
    cursor:pointer;z-index:2;font-size:16px;line-height:1;color:var(--charcoal);
    transition:background .2s ease, color .2s ease, transform .2s ease;
  }
  .article-modal-close:hover{background:var(--terracotta);color:var(--cream);border-color:var(--terracotta);transform:rotate(90deg);}
  .article-modal-hero{aspect-ratio:16/9;overflow:hidden;border-radius:32px 32px 0 0;}
  .article-modal-hero img{width:100%;height:100%;object-fit:cover;filter:sepia(14%) saturate(108%) contrast(101%);}
  .article-modal-content{padding:36px 40px 44px;}
  .article-modal-content .article-tag{margin-bottom:14px;}
  .article-modal-title{font-size:clamp(24px,3vw,32px);margin-bottom:8px;font-family:'Fraunces',serif;font-weight:500;line-height:1.2;color:var(--charcoal);}
  .article-modal-date{font-size:13px;color:var(--charcoal-soft);margin-bottom:28px;}
  .article-modal-loading{padding:80px 40px;text-align:center;color:var(--charcoal-soft);font-size:15px;}
  .article-modal-loading a{color:var(--terracotta);font-weight:600;}
  .article-modal-permalink{display:inline-block;margin-top:12px;font-size:13.5px;font-weight:600;color:var(--terracotta);}
  body.modal-open{overflow:hidden;}

  /* DARK CARD GRID (avantages / garanties / engagements) */
  .dark-section{background:var(--charcoal);color:var(--cream);}
  .dark-section .section-head h2, .dark-section .section-head p{color:var(--cream);}
  .dark-section .section-head p{color:rgba(251,246,239,0.72);}
  .card-grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;}
  .dark-card{
    background:rgba(251,246,239,0.06);border:1px solid rgba(251,246,239,0.14);
    border-radius:18px;padding:32px 26px;
  }
  .dark-card .badge{
    display:inline-flex;align-items:center;justify-content:center;
    width:46px;height:46px;border-radius:50%;background:var(--terracotta);margin-bottom:18px;
  }
  .dark-card h3{color:var(--cream);font-size:18px;margin-bottom:8px;}
  .dark-card p{color:rgba(251,246,239,0.68);font-size:14.5px;}

  /* CONTACT */
  .contact{background:var(--cream-2);}
  .contact-grid{display:grid;grid-template-columns:1fr 1fr;gap:60px;}
  .contact-info-card{
    background:var(--cream);border-radius:22px;padding:44px;border:1px solid var(--line);box-shadow:var(--shadow);
  }
  .contact-info-card h3{font-size:22px;margin-bottom:26px;}
  .info-row{display:flex;gap:16px;margin-bottom:22px;align-items:flex-start;}
  .info-row .ico{
    width:40px;height:40px;border-radius:12px;background:var(--cream-2);color:var(--terracotta);
    display:flex;align-items:center;justify-content:center;flex-shrink:0;
  }
  .info-row strong{display:block;font-size:14.5px;margin-bottom:2px;}
  .info-row span, .info-row a{font-size:14.5px;color:var(--charcoal-soft);}
  .info-row a:hover{color:var(--terracotta);}
  .social-row{display:flex;gap:12px;margin-top:28px;}
  .social-row a{
    width:42px;height:42px;border-radius:50%;background:var(--cream-2);display:flex;
    align-items:center;justify-content:center;color:var(--charcoal);transition:all .25s;
  }
  .social-row a:hover{background:var(--terracotta);color:var(--cream);}
  .map-frame{border-radius:22px;overflow:hidden;box-shadow:var(--shadow);min-height:100%;}
  .map-frame iframe{width:100%;height:100%;min-height:420px;border:0;}

  /* CTA BAND */
  .cta-band{background:var(--terracotta);color:var(--cream);text-align:center;}
  .cta-band h2{color:var(--cream);font-size:clamp(24px,3vw,34px);margin-bottom:16px;}
  .cta-band p{color:rgba(251,246,239,0.9);margin-bottom:30px;max-width:560px;margin-left:auto;margin-right:auto;}
  .cta-band .btn-primary{background:var(--cream);color:var(--terracotta-dark);}
  .cta-band .btn-primary:hover{background:var(--cream-2);}

  /* FOOTER */
  footer{background:var(--charcoal);color:rgba(251,246,239,0.65);padding:56px 0 28px;}
  .footer-top{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:30px;padding-bottom:36px;border-bottom:1px solid rgba(251,246,239,0.12);}
  .footer-logo{display:flex;align-items:center;gap:12px;}
  .footer-logo .name{color:var(--cream);font-family:'Fraunces',serif;font-size:18px;}
  .footer-links{display:flex;gap:44px;flex-wrap:wrap;}
  .footer-links h4{color:var(--cream);font-size:13px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:14px;font-family:'Inter',sans-serif;font-weight:600;}
  .footer-links ul li{margin-bottom:9px;font-size:14px;}
  .footer-links a:hover{color:var(--terracotta);}
  .footer-bottom{padding-top:26px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;font-size:12.5px;color:rgba(251,246,239,0.45);}
  .footer-bottom a{border-bottom:1px solid rgba(251,246,239,0.22);transition:color .2s ease,border-color .2s ease;}
  .footer-bottom a:hover{color:var(--terracotta);border-bottom-color:var(--terracotta);}

  .reveal{opacity:0;transform:translateY(28px);transition:opacity .8s ease, transform .8s ease;}
  .reveal.in{opacity:1;transform:translateY(0);}

  @media (max-width:980px){
    .split-grid, .contact-grid{grid-template-columns:1fr;gap:40px;}
    .split-grid .split-text, .split-grid .arch-frame, .split-grid.reverse .split-text, .split-grid.reverse .arch-frame{order:initial;}
    .services-grid{grid-template-columns:repeat(2,1fr);}
    .marques-grid{grid-template-columns:repeat(3,1fr);}
    .brand-grid{grid-template-columns:repeat(2,1fr);}
    .card-grid-3{grid-template-columns:1fr;}
    .ambiance-grid{grid-template-columns:1fr 1fr;}
    .ambiance-grid .arch-frame:first-child{grid-column:1/-1;}
    .degree-scale{grid-template-columns:1fr 1fr;}
    .device-grid{grid-template-columns:1fr;}
    .reimburse-grid{grid-template-columns:1fr;}
    .article-grid{grid-template-columns:1fr 1fr;}
  }
  @media (max-width:1130px){
    /* En dessous de cette largeur, la barre de navigation (7 onglets) ne
       tient plus confortablement sur une seule ligne à côté du logo et de la
       bulle téléphone — on bascule sur le menu burger plutôt que de laisser
       les onglets se couper ou passer à la ligne.
       Historique du seuil : 980px, puis 1010px le 30/07/2026 (les bulles
       d'onglet ajoutent du rembourrage horizontal), puis 1130px le
       31/07/2026 avec le retour de l'onglet « Nous rendre visite ».
       Mesure : la nav a besoin de 1057px utiles, soit 1113px de fenetre ;
       1130px laisse une marge de securite. */
    nav.main-nav{
      position:fixed;top:0;right:-100%;height:100vh;width:78%;max-width:340px;
      background:var(--cream);flex-direction:column;padding:110px 30px;gap:11px;margin:0;
      transition:right .4s ease;box-shadow:-10px 0 40px rgba(0,0,0,0.15);
    }
    nav.main-nav.open{right:0;}
    nav.main-nav a{color:var(--charcoal);font-size:16px;padding:9px 16px;align-self:flex-start;}
    /* Dans le panneau burger le fond est deja creme : la bulle prend la
       teinte terracotta quel que soit l'etat de defilement. */
    nav.main-nav a.active, header.scrolled nav.main-nav a.active{
      background:rgba(193,101,59,0.10);
      border-color:rgba(193,101,59,0.22);
      color:var(--terracotta);
    }
    .burger{display:block;}
  }
  @media (max-width:480px){
    .header-phone-bubble span.phone-full{display:none;}
  }
  @media (max-width:760px){
    section{padding:76px 0;}
    .story-block{padding:56px 0;}
    .page-hero{padding:44px 0 43px;}
    .page-hero.page-hero--compact{padding:46px 0 31px;}
    .hero-marquee{min-height:227px;padding:87px 0 27px;}
    .services-grid{grid-template-columns:1fr;}
    .marques-grid{grid-template-columns:repeat(2,1fr);}
    .brand-grid{grid-template-columns:1fr;}
    .ambiance-grid{grid-template-columns:1fr;}
    .footer-bottom{flex-direction:column;}
    .check-list-grid{grid-template-columns:1fr;}
    .degree-scale{grid-template-columns:1fr;}
    .faq-item summary{font-size:15.5px;}
    .article-grid{grid-template-columns:1fr;}
    .article-filter-bar{gap:8px;}
    .filter-pill{padding:8px 16px;font-size:12.5px;}
    .article-modal-overlay{padding:0;}
    .article-modal{max-height:100vh;height:100%;border-radius:0;max-width:none;}
    .article-modal-hero{border-radius:0;}
    .article-modal-content{padding:26px 22px 40px;}
  }
"""

# Short content hash used as a cache-busting query string on site.css
# (?v=xxxxxxxx) so browsers cache the stylesheet aggressively across page
# navigations, while still picking up changes automatically whenever
# SHARED_CSS is edited and the site is rebuilt.
CSS_VERSION = hashlib.md5(SHARED_CSS.encode("utf-8")).hexdigest()[:8]

SCRIPT_JS = """
  document.getElementById('year').textContent = new Date().getFullYear();

  /* Le header garde en permanence la classe "scrolled" (demande du client,
     31/07/2026) : fond creme translucide et bulle d'onglet actif terracotta
     des le haut de page. L'ancien listener de scroll qui basculait la classe
     au-dela de 40px a donc ete supprime. */

  const burger = document.getElementById('burger');
  const nav = document.getElementById('mainNav');
  burger.addEventListener('click', () => nav.classList.toggle('open'));
  nav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => nav.classList.remove('open')));

  const revealEls = document.querySelectorAll('.reveal');
  let ticking = false;
  function checkReveal(){
    revealEls.forEach(el => {
      if (el.classList.contains('in')) return;
      const r = el.getBoundingClientRect();
      if (r.top < window.innerHeight * 0.94 && r.bottom > 0) {
        el.classList.add('in');
      }
    });
    ticking = false;
  }
  function onScroll(){
    if (!ticking) {
      requestAnimationFrame(checkReveal);
      ticking = true;
    }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  checkReveal();

  // ACTUALITÉS — bulles extensibles : un clic sur une carte article agrandit
  // une "bulle" sur place avec le texte complet, plutôt que de quitter la
  // page. Le contenu vient de la page dédiée de l'article (fetch), donc rien
  // n'est dupliqué et la page dédiée reste intacte pour le SEO/le partage.
  const articleOverlay = document.getElementById('articleModalOverlay');
  if (articleOverlay) {
    const modalClose = articleOverlay.querySelector('.article-modal-close');
    const modalBody = articleOverlay.querySelector('.article-modal-body');
    const baseTitle = document.title;
    let lastFocused = null;

    async function openArticleModal(url) {
      lastFocused = document.activeElement;
      modalBody.innerHTML = '<div class="article-modal-loading">Chargement de l’article…</div>';
      document.body.classList.add('modal-open');
      articleOverlay.classList.add('open');
      articleOverlay.setAttribute('aria-hidden', 'false');
      modalClose.focus();

      try {
        const res = await fetch(url);
        if (!res.ok) throw new Error('http ' + res.status);
        const html = await res.text();
        const doc = new DOMParser().parseFromString(html, 'text/html');
        const heroImg = doc.querySelector('.article-prose .arch-frame img');
        const tag = doc.querySelector('.article-meta-row .article-tag');
        const dateEl = doc.querySelector('.article-meta-row .article-date');
        const h1 = doc.querySelector('.page-hero h1');
        const prose = doc.querySelector('.article-prose .container-narrow');

        document.title = doc.title || baseTitle;

        let out = '';
        if (heroImg) {
          out += '<div class="article-modal-hero"><img src="' + heroImg.getAttribute('src') + '" alt="' + (heroImg.getAttribute('alt') || '') + '"></div>';
        }
        out += '<div class="article-modal-content">';
        if (tag) out += tag.outerHTML;
        if (h1) out += '<h2 class="article-modal-title">' + h1.textContent + '</h2>';
        if (dateEl) out += '<div class="article-modal-date">' + dateEl.textContent + '</div>';
        if (prose) {
          const clone = prose.cloneNode(true);
          const frame = clone.querySelector('.arch-frame');
          if (frame) frame.remove();
          out += '<div class="article-prose">' + clone.innerHTML + '</div>';
        }
        out += '<a href="' + url + '" class="article-modal-permalink">Voir cet article sur sa page dédiée →</a>';
        out += '</div>';
        modalBody.innerHTML = out;
      } catch (err) {
        modalBody.innerHTML = '<div class="article-modal-loading">Impossible de charger l’article pour le moment. <a href="' + url + '">Ouvrir la page complète</a>.</div>';
      }
    }

    function closeArticleModal() {
      articleOverlay.classList.remove('open');
      articleOverlay.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('modal-open');
      document.title = baseTitle;
      if (lastFocused && lastFocused.focus) lastFocused.focus();
    }

    document.querySelectorAll('.article-card').forEach(card => {
      card.addEventListener('click', (e) => {
        // laisse le comportement natif (nouvel onglet, etc.) si l'utilisateur
        // utilise un clic modifié — seul le clic gauche simple ouvre la bulle
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button === 1) return;
        e.preventDefault();
        openArticleModal(card.getAttribute('href'));
      });
    });

    modalClose.addEventListener('click', closeArticleModal);
    articleOverlay.addEventListener('click', (e) => {
      if (e.target === articleOverlay) closeArticleModal();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && articleOverlay.classList.contains('open')) closeArticleModal();
    });
  }
"""

# Libelles utilises uniquement dans la nav du haut, quand ils different du
# libelle canonique de NAV_ITEMS (qui sert au fil d'Ariane et au JSON-LD).
NAV_TOP_LABELS = {"contact": "Nous rendre visite"}

NAV_ITEMS = [
    ("accueil", "La Boutique", "index.html"),
    ("conseils", "Nos Conseils", "nos-conseils.html"),
    ("marques", "Nos Marques", "marques.html"),
    ("sante", "Espace Santé", "espace-sante.html"),
    ("audition", "Espace Audition", "espace-audition.html"),
    ("actualites", "Actualités", "actualites.html"),
    ("contact", "Contact", "contact.html"),
]

FOOTER_ICON_SVGS = {
    "instagram": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1"/></svg>'
}


def render_head(title, description, path, og_image="og-image.jpg", extra_jsonld=None):
    canonical = f"{BASE_URL}/{path}" if path != "index.html" else f"{BASE_URL}/"
    jsonld = extra_jsonld or ""
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="google-site-verification" content="RFV22sLGR_g4pfYghQAlKFtBIV64vG5hz6ztsw15mFY" />
<title>{title}</title>
<meta name="description" content="{description}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE_URL}/{og_image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='48' fill='%23C1653B'/%3E%3Ctext x='50' y='66' font-size='48' text-anchor='middle' fill='%23FBF6EF' font-family='Georgia,serif'%3EM%3C/text%3E%3C/svg%3E">
{jsonld}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,400&family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;500;700;800&family=Archivo+Black&family=Playfair+Display:ital,wght@0,500;0,600;1,500&family=Comfortaa:wght@600;700&family=Space+Grotesk:wght@700&family=Marcellus&family=Anton&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/site.css?v={CSS_VERSION}">"""


def render_header(active_key):
    link_parts = []
    for key, label, href in NAV_ITEMS:
        # L'onglet vers contact.html a ete retire le 30/07/2026 puis remis le
        # 31/07/2026 a la demande du client, sous le libelle « Nous rendre
        # visite » (le libelle canonique « Contact » reste celui du fil
        # d'Ariane et du JSON-LD).
        cls = ' class="active"' if key == active_key else ""
        link_parts.append(f'<a href="/{href}"{cls}>{NAV_TOP_LABELS.get(key, label)}</a>')
    links = "\n      ".join(link_parts)
    # La classe "scrolled" est appliquee en dur depuis le 31/07/2026 (demande du
    # client) : le header garde en permanence son fond creme translucide et sa
    # bulle d'onglet actif terracotta, y compris en haut de page. Elle reste une
    # classe (plutot qu'une fusion dans le style de base) pour ne rien changer a
    # la cascade CSS existante, deja verifiee sur 31 pages.
    return f"""<header id="siteHeader" class="scrolled">
  <div class="container">
    <a href="/index.html" class="logo">
      <div class="logo-mark">M</div>
      <div class="logo-text">
        <div class="name">Maison Mikis</div>
        <div class="tag">Optique · Audition</div>
      </div>
    </a>
    <nav class="main-nav" id="mainNav">
      {links}
    </nav>
    <div class="header-actions">
      <a href="tel:0182280018" class="header-phone-bubble">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
        <span class="phone-full">01 82 28 00 18</span>
      </a>
      <button class="burger" id="burger" aria-label="Menu"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>"""


FOOTER = """<footer>
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
            <li><a href="/notre-histoire.html">Notre histoire</a></li>
            <li><a href="/nos-conseils.html">Nos Conseils</a></li>
            <li><a href="/marques.html">Nos Marques</a></li>
            <li><a href="/espace-sante.html">Espace Santé</a></li>
            <li><a href="/espace-audition.html">Espace Audition</a></li>
            <li><a href="/actualites.html">Actualités</a></li>
            <li><a href="/opticien-paris-13.html">Opticien à Paris 13e</a></li>
          </ul>
        </div>
        <div>
          <h4>Contact</h4>
          <ul>
            <li>Galerie Oslo – Olympiades</li>
            <li>44 Avenue d'Ivry, 75013 Paris</li>
            <li>01 82 28 00 18</li>
            <li>mikis75013@gmail.com</li>
          </ul>
        </div>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© <span id="year"></span> Maison Mikis — Tous droits réservés.</span>
      <span><a href="/mentions-legales.html">Mentions légales</a> · <a href="/mentions-legales.html#confidentialite">Confidentialité</a></span>
      <span>Opticien et audioprothésiste à Paris 13e — Olympiades</span>
    </div>
  </div>
</footer>"""


def render_page(active_key, title, description, path, body, hero_img=None, extra_jsonld=None, breadcrumb_override=None, hero_pos=None, hero_veil=None):
    # hero_veil : voile sombre pose sur la photo de bandeau, surchargeable page
    # par page. La regle est ecrite dans le <style> en ligne de la page (donc
    # apres site.css) : elle l'emporte a specificite egale, et surtout elle ne
    # modifie pas SHARED_CSS, donc ni CSS_VERSION ni les 30 autres pages.
    # Maillage interne : les pages listees dans PAGE_ARTICLES recoivent un bloc
    # "Nos articles sur le sujet" insere juste avant leur CTA final.
    body = with_page_articles(path, body)

    hero_pos_decl = f'--hero-pos:{hero_pos};' if hero_pos else ''
    veil_rule = (
        f'.page-hero{{background:{hero_veil},'
        f'var(--hero-img) center var(--hero-pos, 15%)/cover no-repeat;}}'
    ) if hero_veil else ''
    style_var = f'<style>:root{{--hero-img:url(\'{hero_img}\');{hero_pos_decl}}}{veil_rule}</style>\n' if hero_img else ''

    # Structured data: the Optician/LocalBusiness block goes on every page
    # (not just the homepage) so Google can associate NAP + hours with each
    # URL independently, plus a BreadcrumbList matching the visible
    # breadcrumb on inner pages. Page-specific schema (FAQPage, etc.) is
    # passed in via extra_jsonld and appended after these.
    # breadcrumb_override lets callers supply a full custom crumb trail (list
    # of (name, url) tuples) instead of the default 2-level "La Boutique >
    # Nav label" — used by individual /actualites/<slug>.html article pages,
    # which need a 3rd level ("La Boutique > Actualités > Titre article").
    jsonld_parts = [OPTICIAN_JSONLD]
    if breadcrumb_override:
        jsonld_parts.append(breadcrumb_jsonld(breadcrumb_override))
    elif active_key != "accueil":
        nav_label = next((label for key, label, _ in NAV_ITEMS if key == active_key), title)
        jsonld_parts.append(breadcrumb_jsonld([
            ("La Boutique", f"{BASE_URL}/"),
            (nav_label, f"{BASE_URL}/{path}"),
        ]))
    if extra_jsonld:
        jsonld_parts.append(extra_jsonld)
    combined_jsonld = "\n".join(jsonld_parts)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
{render_head(title, description, path, extra_jsonld=combined_jsonld)}
{style_var}</head>
<body>

{render_header(active_key)}

{body}

{FOOTER}

<div class="article-modal-overlay" id="articleModalOverlay" aria-hidden="true">
  <div class="article-modal" role="dialog" aria-modal="true" aria-label="Article">
    <button type="button" class="article-modal-close" aria-label="Fermer l'article">✕</button>
    <div class="article-modal-body"></div>
  </div>
</div>

<script>
{SCRIPT_JS}
</script>

</body>
</html>
"""
    out_path = os.path.join(OUT_DIR, path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {path} ({len(html)} bytes)")


# ============================================================================
# PAGE 1 — index.html (page d'accueil = "La Boutique")
# Historiquement une page séparée "la-boutique.html" : devenue la page
# d'accueil le 24/07/2026 à la demande du client, l'onglet nav gardant le nom
# "La Boutique" (voir NAV_ITEMS). Contenu recentré le 24/07/2026 sur l'histoire
# pure (fondateurs + quartier) — la section "Nos services" migrée ici depuis
# l'ancienne page services.html avait alors été déplacée vers nos-conseils.html.
#
# Refonte du 30/07/2026 : le client a jugé, après coup, que faire atterrir
# chaque visiteur directement sur le grand récit (sans aperçu des activités du
# magasin) n'était pas idéal côté expérience client. La page est devenue une
# "vraie" page d'accueil : nouveau hero de bienvenue + CTA, puis un aperçu des
# 4 univers (Optique/Nos Marques/Espace Santé/Espace Audition) sous forme de
# cartes photo cliquables (`.services-refined` / `.refined-card`, voir CSS).
# L'intégralité du récit d'origine (hero "Notre histoire" + les 4 sections
# fondateurs/quartier + le bloc "Aujourd'hui") est conservée SANS AUCUNE
# COUPURE, simplement repoussée plus bas sur la page, juste après l'aperçu des
# 4 univers — l'ancien texte du hero (eyebrow+h1+intro) devient l'intro de la
# nouvelle section "Notre histoire" qui rouvre le récit. Le CTA final "Envie de
# nous rencontrer ?" reste inchangé, tout en bas. Voir le projet Claude pour le
# détail de cette décision et des maquettes validées par le client.
#
# Photos des 4 cartes (30/07/2026, remplacées le jour même) : premier essai
# avec des photos secondaires déjà sur le site (jugé insatisfaisant : le
# client voulait des photos entièrement nouvelles, pas déjà utilisées
# ailleurs). Le client a fourni 4 nouvelles photos (Pexels) le jour même,
# recadrées/optimisées par Claude pour le format carte (ratio ~2.3:1, 1000px
# de large, JPEG optimisé) et stockées dans /images/accueil-cartes/ :
# accueil-optique-lunetterie.jpg, marques-vitrine.jpg, accueil-espace-sante.jpg,
# accueil-espace-audition.jpg. Ce sont les photos définitives.
#
# Refonte du 31/07/2026 (demande client : « la page est vide mise a part
# l'histoire de la boutique »). La page d'accueil devient une vraie vitrine :
#   1. hero de bienvenue (inchange)
#   2. apercu des 4 univers, textes enrichis (2 phrases par carte)
#   3. NOUVEAU « En boutique » : examen de vue SANS rendez-vous (optique) et
#      test auditif SUR rendez-vous (audition), avec explicatif complet
#   4. NOUVEAU bloc sombre « Ce que dit la loi » : adaptation d'ordonnance par
#      l'opticien (art. R4362-12 et D4362-12-1 CSP, decrets 2016-1381 et
#      2024-617), durees de validite (1 an < 16 ans / 5 ans 16-42 / 3 ans > 42)
#      et maintien du remboursement Secu + mutuelle
#   5. NOUVEAU bloc 100 % Sante (monture plafonnee a 30 EUR, classe 1 audio)
#   6. NOUVEAU bandeau marques (10 noms + lien vers marques.html)
#   7. APERCU de l'histoire + bouton vers la nouvelle page notre-histoire.html
#   8. NOUVEAU apercu des 3 dernieres actualites (injecte au moment du rendu
#      via le jeton <!--ACTUALITES_TEASER-->, car ARTICLES est defini bien plus
#      bas dans ce fichier)
#   9. NOUVEAU bandeau infos pratiques (adresse/horaires/acces/tel + carte)
#  10. CTA final (inchange)
# Aucune classe CSS nouvelle n'a ete introduite : SHARED_CSS est intact, donc
# CSS_VERSION ne bouge pas et les autres pages n'ont pas a etre redeployees.
# ============================================================================
BODY_BOUTIQUE = """
<section class="page-hero page-hero--compact">
  <div class="container">
    <span class="eyebrow">Galerie Oslo — Olympiades · 44 avenue d'Ivry</span>
    <h1>Opticien et audioprothésiste à Paris 13e</h1>
    <p>Maison Mikis est une maison familiale installée au cœur du Triangle de Choisy, dédiée à votre vue et à votre audition : conseil sincère, marques choisies avec exigence, et le temps qu'il faut pour bien vous accompagner.</p>
    <div class="hero-actions">
      <a href="/contact.html" class="btn btn-primary">Prendre rendez-vous</a>
      <a href="/marques.html" class="btn btn-ghost">Découvrir nos marques</a>
    </div>
  </div>
</section>

<section class="services-refined">
  <div class="container">
    <div class="section-head-split">
      <div>
        <span class="eyebrow">Chez Maison Mikis</span>
        <h2>Votre vue et votre audition,<br>sous un même toit</h2>
      </div>
      <p>Quatre univers pensés avec la même exigence de conseil, du choix de votre monture au suivi de votre audition.</p>
    </div>
    <div class="refined-grid">
      <a class="refined-card reveal" href="/nos-conseils.html">
        <div class="refined-photo" style="--img:url('/images/accueil-cartes/accueil-optique-lunetterie.jpg');">
          <span class="refined-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="15" r="3.2"/><circle cx="18" cy="15" r="3.2"/><path d="M9.2 15h5.6M2.5 13l1.8-6.5a2 2 0 0 1 1.9-1.5h.3M21.5 13l-1.8-6.5a2 2 0 0 0-1.9-1.5h-.3"/></svg></span>
        </div>
        <div class="refined-body">
          <h3>Optique &amp; lunetterie</h3>
          <p>Montures, verres, traitements, amincissement : nos conseils pour bien choisir et faire durer vos lunettes. On prend le temps de l'essayage, et on réajuste votre monture aussi souvent qu'il le faut.</p>
          <span class="more">En savoir plus →</span>
        </div>
      </a>
      <a class="refined-card reveal" href="/marques.html">
        <div class="refined-photo" style="--img:url('/images/accueil-cartes/marques-vitrine.jpg');">
          <span class="refined-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.6 3H5a2 2 0 0 0-2 2v7.6c0 .5.2 1 .6 1.4l9 9c.8.8 2 .8 2.8 0l7-7c.8-.8.8-2 0-2.8l-9-9c-.4-.4-.9-.6-1.4-.6z"/><circle cx="8.5" cy="8.5" r="1.4"/></svg></span>
        </div>
        <div class="refined-body">
          <h3>Nos marques</h3>
          <p>19 maisons sélectionnées une par une, de Ray-Ban à Loewe en passant par Prada, Dior et Saint Laurent. Des grandes maisons aux créateurs plus confidentiels, chaque collection est choisie, jamais subie.</p>
          <span class="more">En savoir plus →</span>
        </div>
      </a>
      <a class="refined-card reveal" href="/espace-sante.html">
        <div class="refined-photo" style="--img:url('/images/accueil-cartes/accueil-espace-sante.jpg');">
          <span class="refined-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg></span>
        </div>
        <div class="refined-body">
          <h3>Espace santé</h3>
          <p>Examen de vue, défauts visuels, myopie de l'enfant, maladies de l'œil : tout ce qu'il faut savoir pour prendre soin de votre vision. Un contrôle régulier reste la meilleure des préventions.</p>
          <span class="more">En savoir plus →</span>
        </div>
      </a>
      <a class="refined-card reveal" href="/espace-audition.html">
        <div class="refined-photo" style="--img:url('/images/accueil-cartes/accueil-espace-audition.jpg');">
          <span class="refined-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 13.5c0 2.8 2.2 5 5 4.9 3-.1 5.5-2.7 5.5-6.4 0-4.5-3.4-8-8-8a7.6 7.6 0 0 0-7.6 7.6c0 1.6.4 2.6 1.1 4.1.5 1.1.8 1.8.8 2.8a2 2 0 0 1-2 2"/><path d="M9.3 13.2c0-1.7 1.3-2.7 2.7-2.7s2.3 1 2.3 2.2-.9 1.8-1.9 1.8"/></svg></span>
        </div>
        <div class="refined-body">
          <h3>Espace audition</h3>
          <p>Bilan auditif gratuit, essai d'au moins 30 jours en conditions réelles et suivi dans la durée, dans un espace confidentiel dédié. Notre audioprothésiste vous reçoit sur rendez-vous.</p>
          <span class="more">En savoir plus →</span>
        </div>
      </a>
    </div>
  </div>
</section>

<section class="section-head center" style="padding:78px 0 0;">
  <div class="container">
    <span class="eyebrow">En boutique</span>
    <h2>Faire le point sur votre vue<br>ou sur votre audition</h2>
    <p style="max-width:660px;margin:0 auto;">Deux rendez-vous simples, gratuits et sans engagement, que vous pouvez faire chez nous au 44 avenue d'Ivry — l'un quand vous voulez, l'autre sur rendez-vous.</p>
  </div>
</section>

<section class="split story-block" id="examen-de-vue">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/sante/examen-refracteur.jpg" alt="Examen de vue au réfracteur dans l'espace dédié de la boutique" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Sans rendez-vous</span>
        <h2>L'examen de vue en boutique, quand vous voulez</h2>
        <p>Vos lunettes ne vous conviennent plus, mais votre prochain rendez-vous chez l'ophtalmologiste est encore loin ? Poussez simplement la porte : notre opticien réalise un <a href="/espace-sante.html#examen" class="ilink">examen de vue complet</a> dans l'espace de réfraction attenant au magasin, gratuitement et sans rendez-vous.</p>
        <p>Un point important à connaître : cet examen n'est pas une consultation médicale et ne donne pas lieu à une nouvelle ordonnance. En revanche, la réglementation autorise l'opticien à <a href="/actualites/renouveler-lunettes-sans-nouvelle-ordonnance-opticien.html" class="ilink">adapter la correction inscrite sur une ordonnance que vous possédez déjà</a> — et c'est précisément ce que permet cet examen.</p>
        <ul class="check-list">
          <li><span class="check">✓</span> Gratuit, sans rendez-vous et sans engagement</li>
          <li><span class="check">✓</span> Mesure de la vision de loin et de près, en conditions d'examen</li>
          <li><span class="check">✓</span> Adaptation de la correction de votre ordonnance en cours de validité</li>
          <li><span class="check">✓</span> Votre prescripteur est informé de toute modification apportée</li>
          <li><span class="check">✓</span> Vos lunettes restent remboursées par la Sécurité sociale et votre mutuelle</li>
        </ul>
        <a href="/espace-sante.html" class="block-more">Découvrir tout notre Espace Santé →</a>
      </div>
    </div>
  </div>
</section>

<style>
.terra-section{background:var(--terracotta);}
.terra-section .block-more{color:var(--cream);border-bottom-color:rgba(251,246,239,0.55);}
.terra-section .block-more:hover{color:var(--cream);border-bottom-color:var(--cream);}
.terra-section .eyebrow{color:var(--cream);}
.terra-section .section-head p{color:rgba(251,246,239,0.86);}
.terra-section .dark-card{background:rgba(251,246,239,0.10);border-color:rgba(251,246,239,0.26);}
.terra-section .dark-card .badge{background:var(--cream);}
.terra-section .dark-card .badge svg{stroke:var(--terracotta);}
.terra-section .dark-card p{color:rgba(251,246,239,0.88);}
</style>
<section class="dark-section terra-section">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Bon à savoir</span>
      <h2>Ce que l'examen en boutique permet — et ce qu'il ne permet pas</h2>
      <p>Le rôle de l'opticien est encadré par la loi. Trois repères pour savoir exactement à quoi vous attendre en poussant notre porte.</p>
    </div>
    <div class="card-grid-3">
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg></div>
        <h3>Adapter, oui — prescrire, non</h3>
        <p>Depuis 2016, l'opticien-lunetier peut modifier la correction figurant sur votre ordonnance après un examen de la réfraction, sauf opposition expresse du prescripteur mentionnée sur l'ordonnance. Depuis 2024, il peut même le faire dès la première délivrance, avec l'accord du prescripteur. Il ne peut en revanche ni établir une première ordonnance, ni poser un diagnostic médical : le suivi ophtalmologique reste indispensable.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
        <h3>Votre ordonnance vaut plusieurs années</h3>
        <p>Une ordonnance de lunettes reste valable 1 an avant 16 ans, 5 ans entre 16 et 42 ans, et 3 ans au-delà de 42 ans. Tant qu'elle court, nous pouvons y adapter votre correction. Deux exceptions à retenir : les moins de 16 ans, et une presbytie découverte pour la première fois, qui nécessitent l'un comme l'autre un passage chez l'ophtalmologiste.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="9"/></svg></div>
        <h3>Le remboursement est préservé</h3>
        <p>C'est tout l'intérêt de la démarche : des lunettes délivrées sur une ordonnance adaptée par l'opticien restent prises en charge par la Sécurité sociale et votre mutuelle, dans les conditions habituelles — un équipement tous les 2 ans à partir de 16 ans, tous les ans avant 16 ans. Vous ne perdez rien, vous gagnez du temps.</p>
      </div>
    </div>
    <div class="block-more-center"><a href="/actualites/renouveler-lunettes-sans-nouvelle-ordonnance-opticien.html" class="block-more">Ordonnance expirée ? Tout ce que l'opticien peut faire →</a></div>
  </div>
</section>

<section class="split alt story-block" id="test-auditif">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Sur rendez-vous</span>
        <h2>Le test auditif, gratuit et sans engagement</h2>
        <p>Côté audition, la démarche est un peu différente : le bilan se fait sur rendez-vous, parce qu'il demande une cabine correctement isolée, un vrai temps d'écoute et l'attention exclusive de notre <a href="/espace-audition.html" class="ilink">audioprothésiste</a>. Comptez une petite heure, dans un espace confidentiel dédié.</p>
        <p>Là encore, ce bilan n'est pas un diagnostic médical : il mesure votre audition et vous dit précisément où vous en êtes. Si un appareillage se justifie, une prescription médicale — médecin traitant ou ORL — reste obligatoire, et nous pouvons vous orienter vers un ORL partenaire. Nous prenons ensuite le relais pour l'essai, les réglages et le suivi.</p>
        <ul class="check-list">
          <li><span class="check">✓</span> Bilan auditif complet, gratuit et sans engagement</li>
          <li><span class="check">✓</span> Cabine isolée et espace confidentiel dédié</li>
          <li><span class="check">✓</span> Sur rendez-vous, pour vous consacrer le temps nécessaire</li>
          <li><span class="check">✓</span> Essai d'au moins 30 jours avant tout achat, garanti par la loi</li>
          <li><span class="check">✓</span> Accompagnement dans toutes vos démarches de remboursement</li>
        </ul>
        <a href="/espace-audition.html" class="block-more">Découvrir tout notre Espace Audition →</a>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/audition/accompagnement.jpg" alt="Bilan auditif avec l'audioprothésiste Maison Mikis" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Vos remboursements</span>
      <h2>Le reste à charge 0, en optique comme en audition</h2>
      <p>La réforme 100 % Santé garantit, dans les deux métiers, une gamme d'équipements de qualité intégralement prise en charge. Voici ce que cela change concrètement pour vous.</p>
    </div>
    <div class="reimburse-grid">
      <div class="reimburse-card highlight reveal">
        <span class="tag">Reste à charge 0</span>
        <h3>L'offre 100 % Santé</h3>
        <p>Avec une affiliation à la Sécurité sociale et une complémentaire santé responsable, la prise en charge couvre l'intégralité du prix : 0 € à votre charge. Côté lunettes, cela comprend une monture plafonnée à 30 € — proposée en plusieurs coloris — et des verres traités <a href="/nos-conseils.html#traitements-verres" class="ilink">anti-reflet, anti-rayure et amincis</a> selon votre correction, quelle qu'elle soit. Côté audition, un appareil de classe 1 à prix plafonné, réglages et suivi inclus pendant 4 ans.</p>
      </div>
      <div class="reimburse-card reveal">
        <span class="tag">Vos démarches</span>
        <h3>Nous nous occupons de la paperasse</h3>
        <p>Nous vérifions vos droits, appliquons le tiers payant dès que votre mutuelle le permet et vous remettons un <a href="/actualites/comprendre-devis-normalise-lunettes-aides-auditives.html" class="ilink">devis normalisé</a> gratuit avant tout engagement, pour que vous puissiez comparer en toute transparence. Rien ne vous oblige à choisir le 100 % Santé : vous pouvez aussi panacher, par exemple une monture libre avec des verres 100 % Santé. Le renouvellement est pris en charge tous les 2 ans à partir de 16 ans, tous les ans avant 16 ans.</p>
      </div>
    </div>
    <div class="block-more-center"><a href="/actualites/100-pour-cent-sante-2026.html" class="block-more">Le 100 % Santé en 2026, en détail →</a></div>
  </div>
</section>

<section class="marques">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Nos marques</span>
      <h2>19 maisons, choisies une par une</h2>
      <p>Des grandes maisons de couture aux créateurs plus confidentiels, une sélection resserrée que nous assumons entièrement — et que vous pouvez essayer tranquillement en boutique.</p>
    </div>
    <div class="marques-grid">
      <div class="marque-item">Ray-Ban</div>
      <div class="marque-item">Prada</div>
      <div class="marque-item">Dior</div>
      <div class="marque-item">Gucci</div>
      <div class="marque-item">Saint Laurent</div>
      <div class="marque-item">Celine</div>
      <div class="marque-item">Loewe</div>
      <div class="marque-item">Fendi</div>
      <div class="marque-item">Miu Miu</div>
      <div class="marque-item">Ralph Lauren</div>
    </div>
    <div style="text-align:center;margin-top:40px;">
      <a href="/marques.html" class="btn btn-outline">Voir les 19 marques</a>
    </div>
  </div>
</section>

<section class="split story-block">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/accueil/boutique-comptoir.jpg" alt="Intérieur de la boutique Maison Mikis" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Notre histoire</span>
        <h2>Une maison née dans le Triangle de Choisy</h2>
        <p>Avant Maison Mikis, il y a une autre boutique, à Montreuil, où Sudaya rejoint Mikhael comme directeur de boutique. Deux ans de travail commun, et une envie qui finit par s'imposer : ouvrir ensemble, cette fois, une enseigne à leur image.</p>
        <p>Elle voit le jour en 2023 au 44 avenue d'Ivry, en plein cœur du triangle de Choisy — le quartier où Sudaya a grandi, et dont Mikhael est tombé amoureux au fil des visites. Bois clair, arches terracotta, lumière douce : un lieu où le temps s'accorde à l'attention.</p>
        <div class="founders">
          <div class="initials"><span>S</span><span>M</span></div>
          <div class="meta"><strong>Sudaya &amp; Mikhael</strong>Fondateurs de Maison Mikis</div>
        </div>
        <a href="/notre-histoire.html" class="btn btn-primary" style="margin-top:30px;">Lire toute notre histoire</a>
      </div>
    </div>
  </div>
</section>

<style>
/* Bloc avis clients — ajoute le 01/08/2026.
   Regle stricte : on n'affiche que de courts extraits d'avis reellement
   publies sur Google, attribues par prenom + initiale (respect de la vie
   privee), avec un lien vers la fiche complete. On ne recopie jamais un avis
   entier (texte tiers), et on n'ecrit AUCUN aggregateRating dans le JSON-LD :
   Google ignore, et sanctionne parfois, les notes qu'un site s'attribue a
   lui-meme. La note affichee ici est editoriale et verifiable en un clic. */
.avis-section{background:var(--cream-2);}
.avis-score{display:flex;align-items:center;justify-content:center;gap:14px;margin:6px 0 12px;}
.avis-score .note{font-family:'Fraunces',serif;font-size:44px;line-height:1;color:var(--terracotta);}
.avis-stars{display:flex;gap:3px;}
.avis-stars svg{display:block;}
.avis-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:26px;margin-top:46px;}
.avis-card{background:var(--cream);border:1px solid var(--line);border-radius:14px;padding:30px 28px;display:flex;flex-direction:column;gap:16px;}
.avis-card blockquote{font-family:'Fraunces',serif;font-size:18px;line-height:1.55;color:var(--charcoal);margin:0;}
.avis-card .avis-auteur{font-size:13.5px;color:var(--charcoal-soft);letter-spacing:0.02em;margin-top:auto;}
.avis-actions{margin-top:42px;display:flex;gap:14px;justify-content:center;flex-wrap:wrap;}
@media (max-width:900px){.avis-grid{grid-template-columns:1fr;gap:18px;}}
</style>
<section class="avis-section">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Vos retours</span>
      <div class="avis-score">
        <span class="note">5,0</span>
        <span class="avis-stars" aria-label="Note de 5 sur 5">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="#C9764B" aria-hidden="true"><path d="M12 2l2.9 6.2 6.6.9-4.8 4.6 1.2 6.6L12 17.2 6.1 20.3l1.2-6.6L2.5 9.1l6.6-.9z"/></svg>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="#C9764B" aria-hidden="true"><path d="M12 2l2.9 6.2 6.6.9-4.8 4.6 1.2 6.6L12 17.2 6.1 20.3l1.2-6.6L2.5 9.1l6.6-.9z"/></svg>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="#C9764B" aria-hidden="true"><path d="M12 2l2.9 6.2 6.6.9-4.8 4.6 1.2 6.6L12 17.2 6.1 20.3l1.2-6.6L2.5 9.1l6.6-.9z"/></svg>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="#C9764B" aria-hidden="true"><path d="M12 2l2.9 6.2 6.6.9-4.8 4.6 1.2 6.6L12 17.2 6.1 20.3l1.2-6.6L2.5 9.1l6.6-.9z"/></svg>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="#C9764B" aria-hidden="true"><path d="M12 2l2.9 6.2 6.6.9-4.8 4.6 1.2 6.6L12 17.2 6.1 20.3l1.2-6.6L2.5 9.1l6.6-.9z"/></svg>
        </span>
      </div>
      <h2>Ce que disent les clients de la boutique</h2>
      <p>Plus de 160 avis publiés sur notre fiche Google, et une moyenne de 5,0. En voici trois extraits — vous pouvez tous les lire, et vérifier la note, en un clic.</p>
    </div>
    <div class="avis-grid">
      <figure class="avis-card reveal">
        <blockquote>« Les employés sont à l'écoute, attentionnés et transparents. »</blockquote>
        <figcaption class="avis-auteur">Williams T. — avis Google</figcaption>
      </figure>
      <figure class="avis-card reveal">
        <blockquote>« L'équipe prend le temps de bien comprendre les besoins. »</blockquote>
        <figcaption class="avis-auteur">F. B. — avis Google</figcaption>
      </figure>
      <figure class="avis-card reveal">
        <blockquote>« Des conseils avisés, adaptés à mes besoins et à mon budget. »</blockquote>
        <figcaption class="avis-auteur">Annie C. — avis Google</figcaption>
      </figure>
    </div>
    <div class="avis-actions">
      <a href="https://maps.google.com/?cid=6701951749895757703" class="btn btn-outline" target="_blank" rel="noopener">Lire tous les avis sur Google</a>
      <a href="/contact.html" class="btn btn-primary">Venir nous voir</a>
    </div>
  </div>
</section>

<!--ACTUALITES_TEASER-->

<section class="contact" style="background:var(--cream);">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Nous rendre visite</span>
      <h2>Infos pratiques</h2>
      <p>Galerie Oslo – Olympiades, au pied des tours, à deux minutes de la sortie du métro. Tout savoir sur <a href="/opticien-paris-13.html">votre opticien à Paris 13e</a> : services, quartiers desservis et accès.</p>
    </div>
    <div class="contact-grid">
      <div class="contact-info-card reveal">
        <h3>Maison Mikis</h3>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg></div>
          <div><strong>Adresse</strong><span>44 Avenue d'Ivry, 75013 Paris<br>Galerie Oslo – Olympiades</span></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
          <div><strong>Horaires</strong><span>Mardi – Samedi, 10h00 – 19h30<br>Fermé le dimanche et le lundi</span></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div>
          <div><strong>Accès</strong><span>Métro ligne 14 — Olympiades</span></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg></div>
          <div><strong>Téléphone</strong><a href="tel:0182280018">01 82 28 00 18</a></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 6l-10 7L2 6"/><rect x="2" y="4" width="20" height="16" rx="2"/></svg></div>
          <div><strong>Email</strong><a href="mailto:mikis75013@gmail.com">mikis75013@gmail.com</a></div>
        </div>
        <div class="social-row">
          <a href="https://www.instagram.com/maisonmikis/" target="_blank" rel="noopener" aria-label="Instagram">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1"/></svg>
          </a>
        </div>
      </div>
      <div class="map-frame reveal">
        <iframe src="https://www.google.com/maps?q=44+Avenue+d'Ivry+75013+Paris&output=embed" loading="lazy" allowfullscreen title="Localisation Maison Mikis"></iframe>
      </div>
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Envie de nous rencontrer ?</h2>
    <p>Venez découvrir la boutique, Galerie Oslo – Olympiades, et échanger avec Sudaya et Mikhael.</p>
    <a href="/contact.html" class="btn btn-primary">Prendre rendez-vous</a>
  </div>
</section>
"""


# ============================================================================
# PAGE 8 — notre-histoire.html
# ============================================================================
# Creee le 31/07/2026 a la demande du client : la page d'accueil ne garde plus
# qu'un APERCU de l'histoire (bloc "Notre histoire" + bouton), et l'integralite
# du recit d'origine (fondateurs + quartier + "Aujourd'hui") est deplacee ici
# SANS AUCUNE COUPURE. Le client a choisi de ne PAS ajouter d'onglet dans le
# menu du haut : on y accede par le bouton de l'accueil et par le pied de page.
# La page reprend donc active_key="accueil" (l'onglet "La Boutique" reste
# surligne, ce qui est coherent : c'est une sous-page de la boutique) avec un
# breadcrumb_override explicite pour le JSON-LD.
BODY_HISTOIRE = """
<section class="page-hero">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / Notre histoire</div>
    <span class="eyebrow">Notre histoire</span>
    <h1>Une maison née dans le Triangle de Choisy</h1>
    <p>L'histoire de Maison Mikis est aussi celle d'un quartier : le triangle de Choisy, cœur battant du 13e arrondissement de Paris. Une aventure familiale, née de la rencontre de deux regards qui ont fini par se rejoindre.</p>
  </div>
</section>

<section class="split story-block">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/accueil/boutique-comptoir.jpg" alt="Intérieur de la boutique Maison Mikis">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">2023</span>
        <h2>Une maison, un regard</h2>
        <p>Avant Maison Mikis, il y a une autre boutique — celle que Mikhael dirige déjà à Montreuil. C'est là que Sudaya le rejoint en tant que directeur de boutique, et prend en main, pendant deux ans, sous sa responsabilité, l'accueil, le conseil et la gestion de l'équipe au quotidien.</p>
        <p>De cette collaboration naît une envie commune : ouvrir, ensemble cette fois, une enseigne à leur image. Maison Mikis voit le jour en 2023, pensée pour une clientèle en quête de qualité, de style et d'une attention sincère. Pas de vitrine impersonnelle, pas de conseil expédié. Bois clair, arches terracotta, lignes sobres et lumière douce composent un espace où le temps s'accorde à l'attention : pour votre vue comme pour votre audition.</p>
        <div class="founders">
          <div class="initials"><span>S</span><span>M</span></div>
          <div class="meta"><strong>Sudaya &amp; Mikhael</strong>Fondateurs de Maison Mikis</div>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Racines</span>
        <h2>Sudaya, enfant du quartier</h2>
        <p>Né en 1994, Sudaya a grandi ici, dans les tours qui bordent l'avenue d'Ivry et l'avenue de Choisy. Sa famille, d'origine cambodgienne et vietnamienne, s'y est installée à la fin des années 1970, comme des dizaines de milliers d'autres familles arrivées d'Asie du Sud-Est. Il a grandi au rythme du quartier : les étals du marché, les effluves des restaurants, les paniers de courses remontés le dimanche, les défilés du Nouvel An lunaire avec leurs lions et leurs dragons sur l'esplanade des Olympiades.</p>
        <p>C'est de cette enfance-là qu'il tient une certaine idée du commerce : un lieu où l'on prend le temps de bien faire les choses, où la relation compte autant que le produit — une exigence qu'il a mise au service de Mikhael pendant deux ans, avant de la mettre au service de leur propre maison.</p>
        <div class="pull-quote">« Ici, tout le monde se connaissait un peu — entre le marché, les commerces de la Galerie et les fêtes du Nouvel An. C'est ce lien-là que j'ai voulu retrouver dans la boutique. »</div>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/histoire/nouvel-an-lunaire-olympiades.jpg" alt="Lions dansants du défilé du Nouvel An lunaire sur l'esplanade des Olympiades, Paris 13e" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="split story-block">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/histoire/esplanade-olympiades.jpg" alt="L'esplanade des Olympiades et ses dalles couvertes, à deux pas de la Galerie Oslo, Paris 13e" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Un regard neuf</span>
        <h2>Mikhael, une attirance venue d'ailleurs</h2>
        <p>Né en 1990, Mikhael n'a lui ni grandi dans le 13e ni dans une famille aux racines asiatiques. C'est au fil de ces deux années de travail commun que Sudaya lui fait découvrir le quartier de son enfance — une adresse, une anecdote, une invitation à goûter tel plat plutôt qu'un autre. Peu à peu, quelque chose l'accroche : le mélange des langues, les effluves qui se croisent d'une échoppe à l'autre, l'énergie tranquille d'un quartier qui vit à son propre rythme, entre plusieurs générations et plusieurs mondes.</p>
        <p>Cette attirance pour le métissage et la vie de quartier ne l'a plus quitté. Alors, au moment de choisir où poser les arches de leur propre maison, l'esplanade des Olympiades s'impose à eux deux comme une évidence.</p>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Le quartier</span>
        <h2>Une histoire écrite dans le béton et les épices</h2>
        <p>Le quartier asiatique du 13e arrondissement — le « triangle de Choisy », délimité par l'avenue de Choisy, l'avenue d'Ivry et le boulevard Masséna — doit son visage actuel à l'histoire. Au milieu des années 1970, après la guerre du Vietnam et le génocide cambodgien, des dizaines de milliers de réfugiés d'Asie du Sud-Est arrivent en France. Les grandes tours construites ici quelques années plus tôt dans le cadre de l'opération « Italie 13 », pensées pour de jeunes cadres parisiens, peinent alors à trouver preneurs.</p>
        <p>Les familles vietnamiennes, cambodgiennes et laotiennes s'y installent en nombre, et le quartier se transforme peu à peu : commerces, restaurants, épiceries, grandes surfaces asiatiques comme Tang Frères ou Paristore, associations, temples bouddhistes. Aujourd'hui encore, le quartier reste un point de rendez-vous pour toute la communauté asiatique d'Île-de-France, notamment lors du Nouvel An lunaire.</p>
        <p style="margin-top:8px;">C'est au 44 avenue d'Ivry, juste au bord de l'esplanade des Olympiades et en plein cœur de ce triangle, que Maison Mikis a choisi de poser ses arches.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/accueil/boutique-ambiance.jpg" alt="Ambiance chaleureuse de la boutique Maison Mikis" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Aujourd'hui</span>
      <h2>Une maison à taille humaine</h2>
      <p>Sudaya et Mikhael accueillent chaque client comme un voisin : avec le temps qu'il faut pour bien conseiller, et l'attention d'une maison où l'on se souvient de vous d'une visite à l'autre. Une philosophie qu'ils appliquent aussi bien à l'optique qu'à l'audition, avec la même exigence.</p>
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Envie de nous rencontrer ?</h2>
    <p>Venez découvrir la boutique, Galerie Oslo – Olympiades, et échanger avec Sudaya et Mikhael.</p>
    <a href="/contact.html" class="btn btn-primary">Prendre rendez-vous</a>
  </div>
</section>
"""


# ============================================================================
# PAGE 3 — espace-sante.html (prévention et santé visuelle)
# ============================================================================
BODY_SANTE = """
<section class="page-hero">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / Espace Santé</div>
    <span class="eyebrow">Prévention &amp; conseils</span>
    <h1>Espace Santé</h1>
    <p>Examen de vue, défauts visuels, myopie de l'enfant, maladies de l'œil et conseils du quotidien : toutes les clés pour comprendre et prendre soin de votre vue, à chaque âge de la vie.</p>
  </div>
</section>

<section class="split story-block" id="examen">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/accueil-cartes/accueil-espace-sante.jpg" alt="Examen de vue au réfracteur en boutique">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Examen de vue</span>
        <h2>Un contrôle régulier, la meilleure des préventions</h2>
        <p>L'acuité visuelle se mesure en deux temps : de loin, avec l'échelle de Monoyer (lecture de lettres à quelques mètres), et de près, avec l'échelle de Parinaud (lecture à distance de bras). Ensemble, elles permettent à notre équipe d'évaluer précisément votre vue et de détecter une éventuelle évolution de votre correction.</p>
        <ul class="check-list">
          <li><span class="check">✓</span> Difficulté à lire les panneaux ou plaques de rue</li>
          <li><span class="check">✓</span> Besoin de rapprocher un texte ou un écran pour le lire</li>
          <li><span class="check">✓</span> Maux de tête ou fatigue oculaire en fin de journée</li>
          <li><span class="check">✓</span> Vision qui se trouble ponctuellement, de près ou de loin</li>
        </ul>
        <p>Le moindre doute mérite un contrôle : n'attendez pas de gêne franche pour prendre rendez-vous.</p>
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Bonnes pratiques</span>
      <h2>À quelle fréquence contrôler sa vue ?</h2>
      <p>Le rythme recommandé dépend surtout de l'âge et des facteurs de risque : voici les grands repères à connaître.</p>
    </div>
    <div class="degree-scale">
      <div class="degree-card reveal" style="--bar:var(--sage);">
        <div class="db">Enfants</div>
        <h3>Dès 6 mois</h3>
        <p>Premiers dépistages à 6 mois, 3 ans et 6 ans, puis suivi par un ophtalmologiste tous les 2 ans.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--wood);">
        <div class="db">18 – 40 ans</div>
        <h3>Tous les 2 ans</h3>
        <p>En l'absence de trouble, un contrôle tous les 2 ans suffit — annuel en cas de forte exposition aux écrans.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta);">
        <div class="db">40 – 60 ans</div>
        <h3>Tous les 1 à 2 ans</h3>
        <p>La presbytie s'installe et le risque de glaucome augmente : un suivi plus rapproché est recommandé.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta-dark);">
        <div class="db">60 ans et +</div>
        <h3>Chaque année</h3>
        <p>Cataracte, DMLA et glaucome deviennent plus fréquents : un contrôle annuel est conseillé.</p>
      </div>
    </div>
  </div>
</section>

<section class="services alt" id="defauts">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Défauts visuels</span>
      <h2>Mieux comprendre les troubles de la vue</h2>
      <p>Myopie, hypermétropie, astigmatisme et presbytie sont des troubles de la réfraction très courants — chacun se corrige différemment selon son origine.</p>
    </div>
    <div class="services-grid">
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 3v18M3 12h18"/></svg></div>
        <h3>Myopie</h3>
        <p>La vision de loin est floue tandis que la vision de près reste nette. C'est le trouble visuel le plus répandu, souvent diagnostiqué dès l'enfance.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/></svg></div>
        <h3>Hypermétropie</h3>
        <p>À l'inverse de la myopie, c'est la vision de près qui demande un effort de mise au point, avec parfois une fatigue oculaire associée.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12h16M4 6h16M4 18h10"/></svg></div>
        <h3>Astigmatisme</h3>
        <p>Une courbure irrégulière de la cornée déforme légèrement les images, de près comme de loin, et nécessite une correction spécifique.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg></div>
        <h3>Presbytie</h3>
        <p>À partir de 44-45 ans environ, l'œil accommode moins bien de près : elle concerne tout le monde, tôt ou tard, myope ou non.</p>
      </div>
    </div>
    <p style="max-width:680px;margin:32px auto 0;text-align:center;color:var(--charcoal-soft);font-size:14.5px;">Le daltonisme, trouble de la perception des couleurs, est plus rare et généralement présent dès la naissance : un dépistage spécifique permet de le confirmer et d'adapter certains équipements au quotidien.</p>
  </div>
</section>

<section class="split story-block" id="myopie-enfant">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/sante/myopie-enfant-signes.jpg" alt="Dépistage visuel chez l'enfant" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Myopie de l'enfant</span>
        <h2>Une vigilance particulière entre 7 et 12 ans</h2>
        <p>C'est souvent entre 7 et 12 ans que la myopie apparaît et évolue le plus rapidement chez l'enfant. Quelques signes doivent alerter les parents :</p>
        <ul class="check-list">
          <li><span class="check">✓</span> L'enfant plisse les yeux pour regarder au loin</li>
          <li><span class="check">✓</span> Il se rapproche du tableau, de la télévision ou d'un livre</li>
          <li><span class="check">✓</span> Il se plaint de maux de tête après l'école</li>
          <li><span class="check">✓</span> Il se frotte les yeux fréquemment</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Bons réflexes</span>
        <h2>Ralentir la progression, au quotidien</h2>
        <p>Certaines habitudes simples, adoptées tôt, aident à freiner l'évolution de la myopie chez l'enfant :</p>
        <ul class="check-list-grid">
          <li><span class="check">✓</span> 40 minutes à 2 heures de temps extérieur chaque jour</li>
          <li><span class="check">✓</span> Écrans de loisir limités à 30 minutes par jour</li>
          <li><span class="check">✓</span> La règle des 20-20-20 : toutes les 20 min, regarder 20 sec à 20 m</li>
          <li><span class="check">✓</span> Une distance de lecture d'au moins 30 cm</li>
        </ul>
        <p>Selon les cas, notre équipe peut également orienter vers des verres ou lentilles spécifiquement conçus pour ralentir la progression de la myopie, prescrits par un ophtalmologiste.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/sante/myopie-enfant-suivi.jpg" alt="Suivi ophtalmologique de l'enfant, consultation avec dépistage à l'ophtalmoscope" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Calendrier</span>
      <h2>Le suivi visuel de l'enfant, étape par étape</h2>
    </div>
    <div class="degree-scale">
      <div class="degree-card reveal" style="--bar:var(--sage);">
        <div class="db">9 mois – 1 an</div>
        <h3>Premier dépistage</h3>
        <p>Recherche d'un strabisme ou d'un trouble précoce lors des visites de suivi du nourrisson.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--wood);">
        <div class="db">3 – 4 ans</div>
        <h3>Bilan préscolaire</h3>
        <p>Contrôle systématique avant l'entrée à l'école, période clé pour détecter amblyopie et troubles précoces.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta);">
        <div class="db">6 ans</div>
        <h3>Âge de lecture</h3>
        <p>Les troubles de la réfraction (myopie, astigmatisme) apparaissent souvent à cet âge, à l'entrée en CP.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta-dark);">
        <div class="db">Après 6 ans</div>
        <h3>Suivi régulier</h3>
        <p>Contrôle tous les 2-3 ans, ou chaque année en cas de correction portée, jusqu'à 16 ans.</p>
      </div>
    </div>
  </div>
</section>

<section class="split story-block" id="maladies">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/sante/maladies-modele-oeil.jpg" alt="Modèle anatomique de l'œil" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Maladies de l'œil</span>
        <h2>Le dépistage régulier, votre meilleure protection</h2>
        <p>Certaines pathologies évoluent silencieusement pendant des années : seul un contrôle régulier permet de les détecter tôt. Voici les trois plus fréquentes à connaître.</p>
      </div>
    </div>
  </div>
</section>

<section class="dark-section">
  <div class="container">
    <div class="card-grid-3">
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/></svg></div>
        <h3>Cataracte</h3>
        <p>Opacification progressive du cristallin liée à l'âge, qui touche plus de 20 % des personnes après 65 ans. Vision qui se voile, éblouissements : une intervention chirurgicale permet de remplacer le cristallin et de retrouver une vision nette.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10"/><path d="M12 6v6l4 2"/></svg></div>
        <h3>DMLA</h3>
        <p>Première cause de malvoyance après 50 ans en France. La forme sèche évolue lentement sur plusieurs années ; la forme humide, plus rapide, se traite par injections. Lignes droites déformées ou tache centrale doivent alerter sans tarder.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="9"/></svg></div>
        <h3>Glaucome</h3>
        <p>Une pression intraoculaire trop élevée qui endommage le nerf optique, souvent sans aucun symptôme au début. Il touche 1 à 2 % des plus de 40 ans et environ 10 % des plus de 70 ans : le dépistage régulier est essentiel.</p>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block" id="conseils">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Nos conseils</span>
        <h2>Les bons réflexes pour préserver votre vue</h2>
        <p>Fatigue oculaire, écrans, protection solaire, lentilles... quelques repères simples pour préserver le confort de vos yeux au quotidien.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/sante/conseils-fatigue-oculaire.jpg" alt="Homme se frottant les yeux, fatigue oculaire" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container-narrow">
    <div class="faq-list">
      <details class="faq-item reveal">
        <summary>Comment limiter la fatigue oculaire liée aux écrans ?<span class="plus">+</span></summary>
        <p>Appliquez la règle des 20-20-20 : toutes les 20 minutes, faites une pause de 20 secondes en regardant un point situé à 20 mètres. Pensez aussi à cligner des yeux régulièrement et à régler la luminosité de vos écrans.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Comment bien choisir sa protection solaire pour les yeux ?<span class="plus">+</span></summary>
        <p>La teinte se choisit selon l'usage : brun ou jaune pour le contraste en conduite ou activité sportive, gris pour une vision naturelle des couleurs, vert pour un bon compromis. Les verres polarisants sont recommandés pour la conduite, l'eau ou la montagne, où les reflets sont importants.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Quelles sont les bonnes pratiques d'hygiène avec des lentilles de contact ?<span class="plus">+</span></summary>
        <p>Lavez-vous toujours les mains avant manipulation, respectez la durée de port et de renouvellement indiquée, évitez le contact avec l'eau du robinet ou de la douche, et ne dormez jamais avec des lentilles non prévues pour un port prolongé, sauf avis contraire de votre praticien.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Comment choisir une monture adaptée à mon visage et à mon activité ?<span class="plus">+</span></summary>
        <p>La forme de la monture se choisit en fonction de la morphologie du visage, mais aussi de votre usage principal : une monture légère et enveloppante pour le sport, un maintien renforcé pour le vélo, la voile ou le ski. Notre équipe vous conseille en essayage.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Quels traitements choisir pour mes verres ?<span class="plus">+</span></summary>
        <p>Plusieurs options se combinent selon vos besoins : verres photochromiques qui s'assombrissent automatiquement à la lumière, filtre anti-lumière bleue pour le confort devant les écrans, ou verres polarisants pour réduire les reflets et l'éblouissement en extérieur.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Que faire en cas d'yeux secs ou d'allergies oculaires ?<span class="plus">+</span></summary>
        <p>Les allergies saisonnières, notamment au pollen, touchent 20 à 25 % de la population française et provoquent rougeurs et démangeaisons. Des larmes artificielles et l'évitement des frottements soulagent les symptômes légers ; en cas de gêne persistante, un avis médical est recommandé.</p>
      </details>
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Une question sur votre vue ?</h2>
    <p>Prenez rendez-vous en boutique, Galerie Oslo – Olympiades, pour un examen ou un conseil personnalisé.</p>
    <a href="/contact.html" class="btn btn-primary">Prendre rendez-vous</a>
  </div>
</section>
"""


# ============================================================================
# PAGE 4 — marques.html
# ============================================================================
# NOTE: .brand-wordmark uses stylised typography (font/weight/case), not the
# brands' actual trademarked logo artwork — we don't have licensed access to
# official logo files. Swap in real logo images once Mikhael obtains them
# from each brand's dealer/press portal (just replace the wordmark div with
# an <img>).
BRANDS = [
    {
        "name": "Ray-Ban", "founded": "1937", "country": "États-Unis", "wm": "wm-stencil", "logo": "/logos/ray-ban.png",
        "story": "Fondée en 1937 aux États-Unis pour équiper les pilotes de l'armée américaine de verres anti-éblouissants, la maison invente cette même année l'Aviator, puis dessine en 1952 le Wayfarer — deux silhouettes devenues les plus copiées de l'histoire des lunettes.",
    },
    {
        "name": "Fendi", "founded": "1925", "country": "Italie", "wm": "wm-serif-caps", "logo": "/logos/fendi.png",
        "story": "Née à Rome en 1925 d'un atelier de maroquinerie fondé par Adele et Edoardo Fendi, la maison italienne a bâti sa réputation sur un savoir-faire d'exception en cuir et en fourrure, porté pendant plus de cinquante ans par Karl Lagerfeld. Ce même souci du détail se retrouve dans ses montures.",
    },
    {
        "name": "Fred", "founded": "1936", "country": "France", "wm": "wm-script", "logo": "/logos/fred.png",
        "story": "Fondée à Paris en 1936 par Fred Samuel, surnommé le « joaillier solaire », la maison doit sa renommée au bracelet Force 10, né en 1966 de l'univers du câble marin. Depuis 1988, cette signature se prolonge jusque dans ses montures, où le maillon torsadé devient motif.",
    },
    {
        "name": "Loewe", "founded": "1846", "country": "Espagne", "wm": "wm-thin-caps-a", "logo": "/logos/loewe.png",
        "story": "Fondée à Madrid en 1846 par le maître-cuirier Enrique Loewe Roessberg, Loewe compte parmi les plus anciennes maisons de cuir d'Europe. Une exigence artisanale que l'on retrouve dans chacune de ses montures, pensées comme de petits objets de maroquinerie.",
    },
    {
        "name": "Celine", "founded": "1945", "country": "France", "wm": "wm-thin-caps-b", "logo": "/logos/celine.png",
        "story": "Fondée à Paris en 1945 par Céline Vipiana, la maison a débuté par la chaussure sur-mesure avant de s'imposer dans la maroquinerie et le prêt-à-porter. Une élégance discrète, façon « quiet luxury », que l'on retrouve dans des montures aussi sobres qu'affirmées.",
    },
    {
        "name": "Marc Jacobs", "founded": "1986", "country": "États-Unis", "wm": "wm-lower-bold", "logo": "/logos/marc-jacobs.png",
        "story": "Lancée à New York au milieu des années 1980, la maison Marc Jacobs s'impose dès 1992 avec sa collection dite « grunge », qui bouscule les codes du prêt-à-porter américain. Un esprit pop et facétieux qui irrigue toute sa ligne de lunetterie.",
    },
    {
        "name": "Prada", "founded": "1913", "country": "Italie", "wm": "wm-geo-caps", "logo": "/logos/prada.png",
        "story": "Fondée à Milan en 1913 par Mario Prada comme maroquinier de luxe, la maison doit sa réinvention à sa petite-fille Miuccia Prada, qui lui insuffle dès les années 1980 un esthétisme minimaliste et intellectuel — une élégance épurée que l'on retrouve jusque dans ses montures.",
    },
    {
        "name": "Andy Brook", "founded": "2017", "country": "France", "wm": "wm-plain", "logo": "/logos/andy-brook.png",
        "story": "Fondée en France en 2017, Andy Brook est une jeune maison qui mise sur un savoir-faire artisanal et des matières premium, assemblées à la main. Une approche contemporaine et exigeante de la lunetterie, portée par une génération attachée au fabriqué avec soin.",
    },
    {
        "name": "CHIMI", "founded": "2016", "country": "Suède", "wm": "wm-lower-round", "logo": "/logos/chimi.png",
        "story": "Fondée à Stockholm en 2016 par Charlie Lindström et Daniel Djurdjevic, CHIMI incarne une lunetterie scandinave minimaliste et colorée, pensée pour s'accorder à tous les styles. Une fraîcheur nordique, entre simplicité des formes et générosité des teintes.",
    },
    {
        "name": "Miu Miu", "founded": "1993", "country": "Italie", "wm": "wm-italic", "logo": "/logos/miu-miu.png",
        "story": "Créée par Miuccia Prada au début des années 1990 comme la petite sœur facétieuse de Prada, Miu Miu cultive un esprit provocateur et ludique, entre audace et fraîcheur. Une lunetterie qui n'a pas peur de jouer avec les codes.",
    },
    {
        "name": "LOOL", "founded": "2016", "country": "Espagne", "wm": "wm-lower-wide", "logo": "/logos/lool.png",
        "story": "Fondée à Barcelone en 2016 par le designer Aris Rubio et l'entrepreneur Alex Carrasco, LOOL réinvente la monture en acier inoxydable, découpée au laser et assemblée sans une seule vis grâce à sa charnière brevetée. Une lunetterie ultralégère, à l'esthétique inspirée de l'architecture rétrofuturiste.",
    },
    {
        "name": "Ralph Lauren", "founded": "1967", "country": "États-Unis", "wm": "wm-classic-serif", "logo": "/logos/ralph-lauren.png",
        "story": "Fondée à New York en 1967 par Ralph Lauren, la maison a démocratisé dans le monde entier une élégance « preppy » si américaine, entre héritage universitaire et art de vivre. Ses montures perpétuent ce classicisme intemporel, chic et évident.",
    },
    {
        "name": "Armani", "founded": "1975", "country": "Italie", "wm": "wm-thin-wide", "logo": "/logos/armani.png",
        "story": "Fondée à Milan en 1975 par Giorgio Armani et Sergio Galeotti, la maison a révolutionné le vestiaire en déstructurant la veste pour une élégance plus fluide. Une sophistication discrète que l'on retrouve dans chacune de ses montures, entre rigueur et douceur des lignes.",
    },
    {
        "name": "Longchamp", "founded": "1948", "country": "France", "wm": "wm-elegant-caps", "logo": "/logos/longchamp.png",
        "story": "Fondée à Paris en 1948 par Jean Cassegrain, Longchamp débute dans la maroquinerie fine avant de devenir, en 1993, la maison du Pliage — ce sac pliable en toile et cuir devenu un classique mondial. Une élégance française pratique, transmise de génération en génération au sein de la famille Cassegrain.",
    },
    {
        "name": "Guess", "founded": "1981", "country": "États-Unis", "wm": "wm-bold-condensed", "logo": "/logos/guess.png",
        "story": "Fondée à Los Angeles en 1981 par les frères Marciano, Guess impose d'emblée un denim ajusté qui tranche avec les coupes amples de l'époque, puis des campagnes en noir et blanc devenues cultes. Un esprit américain affirmé, porté par son triangle devenu l'un des logos les plus reconnaissables de la mode.",
    },
    {
        "name": "Dior", "founded": "1946", "country": "France", "wm": "wm-classic-serif", "logo": "/logos/dior.png",
        "story": "Fondée à Paris en 1946 par Christian Dior, la maison bouleverse la mode dès 1947 avec le « New Look », qui redonne à la silhouette féminine sa taille marquée et ses jupes amples. Une élégance parisienne intemporelle, que l'on retrouve aujourd'hui jusque dans ses montures.",
    },
    {
        "name": "Gucci", "founded": "1921", "country": "Italie", "wm": "wm-elegant-caps", "logo": "/logos/gucci.png",
        "story": "Fondée à Florence en 1921 par Guccio Gucci comme sellerie de cuir fin, la maison italienne s'impose au fil du XXe siècle comme une référence du luxe, entre héritage équestre et esprit maximaliste. Une audace transalpine que l'on retrouve dans chacune de ses lunettes.",
    },
    {
        "name": "Saint Laurent", "founded": "1961", "country": "France", "wm": "wm-bold-condensed", "logo": "/logos/saint-laurent.png",
        "story": "Fondée à Paris en 1961 par Yves Saint Laurent et Pierre Bergé, la maison impose dès 1966 le smoking pour femme et la ligne Rive Gauche, pionnière du prêt-à-porter de luxe. Devenue Saint Laurent Paris en 2012 sous la direction d'Hedi Slimane, elle cultive une élégance rock et acérée qui se prolonge jusque dans ses montures.",
    },
    {
        "name": "Givenchy", "founded": "1952", "country": "France", "wm": "wm-wide-caps", "logo": "/logos/givenchy.png",
        "story": "Fondée à Paris en 1952 par Hubert de Givenchy, la maison se distingue très tôt par sa collaboration avec Audrey Hepburn, qu'il habille dès 1954. Une élégance épurée et raffinée, entre haute couture et modernité, qui irrigue toute sa ligne de lunetterie.",
    },
]


# Rotating accent palette for brand cards — cycles through the site's
# existing colour tokens so the grid feels varied rather than monochrome,
# without introducing any new colours to the design system.
BRAND_ACCENTS = [
    ("var(--wood)", "rgba(185,138,94,0.16)"),
    ("var(--terracotta)", "rgba(193,101,59,0.12)"),
    ("var(--sage)", "rgba(138,148,131,0.18)"),
    ("var(--terracotta-dark)", "rgba(163,79,44,0.14)"),
    ("var(--wood-dark)", "rgba(140,98,57,0.16)"),
]

COUNTRY_FLAGS = {
    "France": "🇫🇷",
    "Italie": "🇮🇹",
    "États-Unis": "🇺🇸",
    "Espagne": "🇪🇸",
    "Suède": "🇸🇪",
}


# Familles éditoriales — la page Nos Marques est structurée en sections H2
# plutôt qu'en une grille unique de 19 cartes sous le H1. Chaque marque
# n'appartient qu'à une seule famille (total = len(BRANDS)).
BRAND_FAMILIES = [
    {
        "id": "maisons-de-couture",
        "eyebrow": "Haute couture",
        "title": "Les maisons de couture",
        "intro": (
            "Ce sont les noms que tout le monde connaît, et ce sont aussi ceux sur lesquels on se trompe le "
            "plus souvent : une monture signée par une grande maison n'est pas une monture « de luxe » "
            "interchangeable, c'est le prolongement d'un vocabulaire de formes construit sur plusieurs décennies. "
            "Chez Dior ou Celine, la ligne reste sobre et le geste précis ; chez Gucci, Fendi ou Miu Miu, elle "
            "s'autorise la couleur, le volume et le motif. Nous vous aidons à trouver, à l'intérieur de cette "
            "famille, celle dont l'écriture correspond réellement à votre visage et à votre manière de vous habiller — "
            "et non simplement le logo le plus visible."
        ),
        "names": ["Dior", "Celine", "Givenchy", "Saint Laurent", "Fendi", "Prada", "Miu Miu", "Gucci", "Armani", "Loewe"],
    },
    {
        "id": "intemporels",
        "eyebrow": "Classiques",
        "title": "Les intemporels et l'esprit américain",
        "intro": (
            "Une paire que l'on garde dix ans ne se choisit pas comme une paire de saison. Ces maisons ont en "
            "commun d'avoir créé des silhouettes qui n'ont jamais quitté le paysage — l'Aviator et la Wayfarer de "
            "Ray-Ban, la ligne universitaire de Ralph Lauren — et de proposer des montures dont les formes "
            "restent lisibles quelle que soit l'année. C'est la famille vers laquelle nous orientons souvent une "
            "première paire de solaires, ou une monture de vue destinée à être portée tous les jours au bureau : "
            "le risque de s'en lasser est faible, et les pièces détachées restent disponibles longtemps."
        ),
        "names": ["Ray-Ban", "Ralph Lauren", "Marc Jacobs", "Guess"],
    },
    {
        "id": "savoir-faire-francais",
        "eyebrow": "Savoir-faire français",
        "title": "La maroquinerie et la joaillerie françaises",
        "intro": (
            "Deux maisons parisiennes venues d'un autre métier — le bracelet pour Fred, le sac pour Longchamp — "
            "et qui ont transposé leur savoir-faire dans la lunetterie sans en changer les codes. On y retrouve "
            "des détails que l'on remarque à l'usage plus qu'en vitrine : un maillon repris sur la branche, une "
            "épaisseur de métal juste, une charnière qui ne prend pas de jeu. C'est une famille que nous "
            "recommandons volontiers à qui cherche une monture discrète mais signée, sans logo apparent."
        ),
        "names": ["Fred", "Longchamp"],
    },
    {
        "id": "createurs-independants",
        "eyebrow": "Indépendants",
        "title": "Les créateurs indépendants",
        "intro": (
            "C'est la partie de la sélection dont nous sommes le plus fiers, parce qu'elle ne se trouve pas partout. "
            "Ces trois maisons ne dépendent d'aucun grand groupe : elles fabriquent en petites séries et "
            "concentrent leur travail sur la construction de la monture plutôt que sur la notoriété du nom. LOOL "
            "assemble ses montures en acier découpé au laser, sans une seule vis ; CHIMI travaille des acétates "
            "colorés dans une grammaire scandinave épurée ; Andy Brook mise sur l'assemblage à la main et des "
            "matières haut de gamme. Si vous cherchez une paire que personne d'autre ne portera dans votre "
            "immeuble, commencez par celles-là."
        ),
        "names": ["LOOL", "CHIMI", "Andy Brook"],
    },
]


def brands_by_name(names):
    """Retourne les dicts BRANDS correspondant à une liste de noms, dans l'ordre donné."""
    index = {b["name"]: b for b in BRANDS}
    missing = [n for n in names if n not in index]
    if missing:
        raise ValueError("Marque inconnue dans BRAND_FAMILIES : %s" % ", ".join(missing))
    return [index[n] for n in names]


def render_brand_families():
    """Rend les 4 sections H2 de la page Nos Marques."""
    covered = [n for fam in BRAND_FAMILIES for n in fam["names"]]
    if sorted(covered) != sorted(b["name"] for b in BRANDS):
        raise ValueError(
            "BRAND_FAMILIES ne couvre pas exactement BRANDS "
            "(%d classées / %d marques)" % (len(covered), len(BRANDS))
        )
    out, offset = [], 0
    for fam in BRAND_FAMILIES:
        subset = brands_by_name(fam["names"])
        out.append(
            '<section class="marques brand-family" id="{id}">\n'
            '  <div class="container">\n'
            '    <div class="section-head">\n'
            '      <span class="eyebrow">{eyebrow}</span>\n'
            '      <h2>{title}</h2>\n'
            '      <p class="family-intro">{intro}</p>\n'
            '    </div>\n'
            '    <div class="brand-grid">\n'
            '{cards}\n'
            '    </div>\n'
            '  </div>\n'
            '</section>'.format(cards=render_brand_cards(subset, offset=offset), **fam)
        )
        offset += len(subset)
    return "\n\n".join(out)


def render_brand_cards(brands, offset=0):
    cards = []
    for j, b in enumerate(brands):
        i = j + offset
        slug = b["name"].lower().replace(" ", "-")
        accent, accent_bg = BRAND_ACCENTS[i % len(BRAND_ACCENTS)]
        flag = COUNTRY_FLAGS.get(b["country"], "")
        if b.get("logo"):
            mark = '<img class="brand-logo" src="{logo}" alt="Logo {name}" loading="lazy">'.format(**b)
        else:
            mark = '<div class="brand-wordmark {wm}">{name}</div>'.format(**b)
        cards.append(
            '      <div class="brand-card reveal" id="{slug}" style="--accent:{accent};--accent-bg:{accent_bg};">\n'
            '        <div class="brand-card-body">\n'
            '          <div class="brand-logo-plate">{mark}</div>\n'
            '          <div class="brand-meta">{flag} Fondée en {founded} · {country}</div>\n'
            '        </div>\n'
            '        <p>{story}</p>\n'
            '      </div>'.format(
                slug=slug, mark=mark, accent=accent, accent_bg=accent_bg, flag=flag, **b
            )
        )
    return "\n".join(cards)


def render_brand_stats(brands):
    n_brands = len(brands)
    n_countries = len({b["country"] for b in brands})
    oldest_year = min(int(b["founded"]) for b in brands)
    return (
        '    <div class="brand-stats">\n'
        '      <div class="brand-stat"><strong>{n_brands}</strong><span>Maisons</span></div>\n'
        '      <div class="brand-stat"><strong>{n_countries}</strong><span>Pays représentés</span></div>\n'
        '      <div class="brand-stat"><strong>{oldest_year}</strong><span>Maison la plus ancienne</span></div>\n'
        '    </div>'
    ).format(n_brands=n_brands, n_countries=n_countries, oldest_year=oldest_year)


def render_brand_pills(brands):
    pills = [f'      <a href="/marques.html#{b["name"].lower().replace(" ", "-")}" class="brand-pill">{b["name"]}</a>' for b in brands]
    return "\n".join(pills)


MARQUEE_PHOTO_COUNT = 36

# Display order: interleaved round-robin across the different people/styles in the
# photo set (rather than upload order) so the strip reads as a mixed, varied cast
# from the very first frame instead of clustering similar photos together.
MARQUEE_ORDER = [
    1, 6, 15, 16, 17, 21,
    2, 7, 19, 27, 18, 23,
    3, 8, 28, 33, 20, 25,
    4, 9, 32, 22, 31,
    5, 12, 26,
    10, 13, 29,
    11, 14, 30,
    24, 34,
    35,
    36,
]


def render_marquee_track():
    imgs = [
        '<img src="/images/marquee/marquee-{:02d}.jpg" alt="" loading="{}">'.format(
            i, "eager" if pos < 4 else "lazy"
        )
        for pos, i in enumerate(MARQUEE_ORDER)
    ]
    # duplicate the full set once so the track can loop seamlessly via translateX(-50%)
    all_imgs = imgs + imgs
    return "\n".join("      " + tag for tag in all_imgs)


BODY_MARQUES = """
<section class="page-hero hero-marquee">
  <div class="hero-marquee-track" aria-hidden="true">
""" + render_marquee_track() + """
  </div>
  <div class="hero-marquee-overlay"></div>
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / Nos Marques</div>
    <span class="eyebrow">Sélection</span>
    <h1>Nos marques</h1>
    <p>De Ray-Ban à Loewe, en passant par Prada ou CHIMI : un choix de maisons reconnues, chacune avec sa propre histoire, sélectionnées pour leur qualité et leur fiabilité.</p>
  </div>
</section>

<style>
  .brand-family{padding-top:34px;padding-bottom:34px;}
  .brand-family + .brand-family{border-top:1px solid rgba(0,0,0,.06);}
  .brand-family .section-head{max-width:760px;margin-bottom:26px;}
  .brand-family .family-intro{margin-top:10px;}
  .marques-intro .section-head{max-width:760px;margin:0 auto;}
  .family-nav{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:22px;}
  .family-nav a{font-size:.86rem;letter-spacing:.02em;padding:8px 16px;border:1px solid rgba(0,0,0,.14);border-radius:999px;text-decoration:none;color:inherit;transition:background .2s,border-color .2s;}
  .family-nav a:hover{background:rgba(193,101,59,.08);border-color:var(--terracotta);}
</style>

<section class="marques marques-intro">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Un choix exigeant</span>
      <h2>Dix-neuf maisons, choisies une par une</h2>
      <p>Nous ne référençons pas un catalogue : nous choisissons. Chaque maison présente en boutique a été retenue pour trois raisons concrètes — une fabrication dont nous connaissons l'origine, un service après-vente qui répond réellement quand une branche casse ou qu'une charnière prend du jeu, et une gamme de formes assez large pour habiller des visages différents. C'est ce qui explique que vous ne trouviez pas ici certaines marques très diffusées : elles ne cochaient pas les trois cases.</p>
      <p>Pour vous y retrouver, la sélection est présentée en quatre familles. Elles ne correspondent pas à des gammes de prix mais à des manières de dessiner une monture — et c'est souvent ce critère-là, plus que le budget, qui fait qu'une paire vous va ou ne vous va pas.</p>
""" + render_brand_stats(BRANDS) + """
      <nav class="family-nav" aria-label="Familles de marques">
        <a href="#maisons-de-couture">Maisons de couture</a>
        <a href="#intemporels">Intemporels</a>
        <a href="#savoir-faire-francais">Savoir-faire français</a>
        <a href="#createurs-independants">Créateurs indépendants</a>
      </nav>
    </div>
  </div>
</section>

""" + render_brand_families() + """

<section class="split alt">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">En boutique</span>
        <h2>Le plus simple : venir les essayer</h2>
        <p>Photos et fiches produits ne remplacent jamais l'essayage. Une monture qui paraît parfaite à l'écran peut appuyer sur le nez, glisser dès que vous baissez la tête, ou couper le regard parce que la hauteur du cercle ne correspond pas à votre visage. Ces trois points ne se voient sur aucune photo.</p>
        <p>En boutique, nous regardons d'abord votre écart pupillaire, la hauteur de vos yeux dans la monture et la façon dont elle se pose sur votre nez et vos oreilles — puis seulement le style. C'est aussi le moment où votre correction entre en jeu : une forte myopie supporte mal les grands cercles, une progression a besoin d'une certaine hauteur de verre. Nous vous le disons avant l'achat, pas après.</p>
        <p>Comptez une vingtaine de minutes pour un essayage tranquille, sans rendez-vous. Si une référence précise vous intéresse, appelez-nous avant de venir : nous vérifions qu'elle est bien en boutique dans votre coloris.</p>
        <a href="/contact.html" class="btn btn-outline" style="margin-top:6px;">Nous rendre visite</a>
      </div>
      <div class="arch-frame reveal">
        <img src="https://images.pexels.com/photos/5766564/pexels-photo-5766564.jpeg?auto=compress&cs=tinysrgb&w=800&h=1000&fit=crop" alt="Présentoir de montures Maison Mikis" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Une marque en particulier vous intéresse ?</h2>
    <p>Contactez-nous, nous vous confirmerons sa disponibilité en boutique.</p>
    <a href="/contact.html" class="btn btn-primary">Nous contacter</a>
  </div>
</section>
"""


# ============================================================================
# PAGE 5 — espace-audition.html
# ============================================================================
BODY_AUDITION = """
<section class="page-hero">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / Espace Audition</div>
    <span class="eyebrow">Espace dédié</span>
    <h1>Espace Audition</h1>
    <p>Bilan auditif gratuit, essai en conditions réelles, appareillage sur mesure et suivi dans la durée — un espace confidentiel pensé pour prendre le temps de bien vous entendre.</p>
  </div>
</section>

<section class="split story-block">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/accueil-cartes/accueil-espace-audition.jpg" alt="Accompagnement personnalisé Maison Mikis" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Un accompagnement humain</span>
        <h2>Du bilan au suivi, à votre rythme</h2>
        <p>Notre audioprothésiste vous reçoit dans un espace confidentiel dédié, pour un bilan auditif complet et gratuit, puis un essai en conditions réelles avant tout engagement d'achat.</p>
        <p>Ce bilan dure une quarantaine de minutes. Il commence par une conversation — dans quelles situations vous gêne-t-on, depuis quand, est-ce plutôt le volume ou la compréhension qui manque — parce que deux personnes ayant la même courbe audiométrique ne vivent pas du tout la même gêne. Vient ensuite la mesure elle-même : sons purs à différentes fréquences, puis reconnaissance de mots, dans le calme puis dans le bruit. Cette seconde partie est la plus parlante : c'est elle qui explique la phrase que nous entendons le plus souvent en boutique, « j'entends, mais je ne comprends pas ».</p>
        <p>Un point important pour éviter tout malentendu : ce bilan est un dépistage, pas un diagnostic médical. Il nous dit s'il y a lieu de s'inquiéter et de quel ordre de grandeur ; il ne remplace pas la consultation d'un médecin ORL, dont la prescription reste obligatoire avant tout appareillage. Si le bilan révèle quelque chose, nous vous le disons clairement et vous orientons — y compris, parfois, pour vous annoncer qu'un simple bouchon de cérumen explique tout et qu'aucun appareil n'est nécessaire.</p>
        <p>Rien n'est engagé à ce stade. Vous pouvez repartir avec le résultat, y réfléchir quelques semaines, en parler à votre médecin, et revenir quand vous le souhaitez : le dossier vous attend.</p>
        <ul class="check-list">
          <li><span class="check">✓</span> Bilan auditif complet et gratuit, sans engagement</li>
          <li><span class="check">✓</span> Essai de solutions auditives en conditions réelles</li>
          <li><span class="check">✓</span> Suivi personnalisé et réglages sur mesure</li>
          <li><span class="check">✓</span> Accompagnement dans vos démarches de remboursement</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Reconnaître les signes</span>
        <h2>Et si c'était votre audition ?</h2>
        <p>La perte auditive s'installe presque toujours progressivement — l'entourage la remarque souvent avant la personne concernée. Ces quelques signes doivent alerter :</p>
        <ul class="check-list-grid">
          <li><span class="check">✓</span> Vous montez le son de la télévision plus qu'avant</li>
          <li><span class="check">✓</span> Vous faites répéter vos proches régulièrement</li>
          <li><span class="check">✓</span> Les conversations en groupe ou dans le bruit vous fatiguent</li>
          <li><span class="check">✓</span> Vous entendez mais comprenez mal certains mots</li>
          <li><span class="check">✓</span> Un sifflement ou bourdonnement (acouphènes) persiste</li>
          <li><span class="check">✓</span> Vous évitez les lieux bruyants ou les réunions de famille</li>
        </ul>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/audition/parcours-audition.jpg" alt="Reconnaître les signes d'une perte auditive" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Comprendre sa perte auditive</span>
      <h2>Les quatre degrés de perte auditive</h2>
      <p>La perte auditive se mesure en décibels (dB) : c'est le volume à partir duquel les sons deviennent audibles pour vous. Voici la classification de référence et ce qu'elle change au quotidien.</p>
    </div>
    <div class="degree-scale">
      <div class="degree-card reveal" style="--bar:var(--sage);">
        <div class="db">26 – 40 dB</div>
        <h3>Légère</h3>
        <p>Les conversations à voix basse ou dans le bruit deviennent difficiles à suivre.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--wood);">
        <div class="db">41 – 60 dB</div>
        <h3>Moyenne</h3>
        <p>Besoin d'augmenter le son de la télévision ; certains sons du quotidien passent inaperçus.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta);">
        <div class="db">61 – 80 dB</div>
        <h3>Sévère</h3>
        <p>Suivre une conversation ou un groupe sans amplification devient un vrai effort.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta-dark);">
        <div class="db">81 dB et +</div>
        <h3>Profonde</h3>
        <p>Même la parole amplifiée est difficile, voire impossible, à percevoir sans appareillage.</p>
      </div>
    </div>
  </div>
</section>

<section class="services alt">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Des solutions sur mesure</span>
      <h2>Les types d'appareils auditifs</h2>
      <p>Chaque morphologie d'oreille et chaque degré de perte auditive orientent vers une forme d'appareil différente. Notre audioprothésiste vous conseille celle qui vous correspond, tous fabricants confondus.</p>
    </div>
    <div class="device-grid">
      <div class="device-card reveal">
        <div class="discretion"><span class="on"></span><span class="on"></span><span></span></div>
        <h3>Contour d'oreille classique</h3>
        <p>Le boîtier se loge derrière l'oreille et transmet le son par un fin tube vers le conduit auditif. Le plus puissant et le plus robuste des trois formats.</p>
        <span class="suited">Pertes sévères à profondes</span>
      </div>
      <div class="device-card reveal">
        <div class="discretion"><span class="on"></span><span class="on"></span><span class="on"></span></div>
        <h3>Micro-contour à écouteur déporté</h3>
        <p>Un boîtier miniaturisé derrière l'oreille et un écouteur directement placé dans le conduit : plus discret, très polyvalent.</p>
        <span class="suited">Pertes légères à sévères</span>
      </div>
      <div class="device-card reveal">
        <div class="discretion"><span class="on"></span><span class="on"></span><span class="on"></span></div>
        <h3>Intra-auriculaire</h3>
        <p>Fabriqué sur mesure à partir de l'empreinte de votre oreille, il se loge entièrement dans le conduit auditif — certains modèles sont quasi invisibles.</p>
        <span class="suited">Pertes légères à moyennes</span>
      </div>
    </div>
  </div>
</section>

<section class="split story-block">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/audition/signes-audition.jpg" alt="Appareillage auditif Maison Mikis" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Étape par étape</span>
        <h2>Votre parcours audition</h2>
        <p>Un appareillage auditif ne se règle pas en une visite. Le cerveau a cessé de traiter certaines fréquences depuis souvent plusieurs années : lui rendre le son d'un coup produit une sensation désagréable, métallique, que beaucoup décrivent comme « trop fort partout ». La progressivité n'est donc pas un confort commercial, c'est la condition pour que l'appareil soit porté au lieu de finir dans un tiroir. Voici comment cela se déroule concrètement.</p>
        <ul class="check-list">
          <li><span class="check">1</span> Rendez-vous découverte pour évoquer votre gêne auditive</li>
          <li><span class="check">2</span> Bilan auditif complet et gratuit</li>
          <li><span class="check">3</span> Essai d'au moins 30 jours en conditions de vie réelles</li>
          <li><span class="check">4</span> Réglages et ajustements personnalisés de l'appareil</li>
          <li><span class="check">5</span> Suivi obligatoire à 3, 6 et 12 mois, puis deux fois par an</li>
        </ul>
        <p>L'essai de trente jours minimum est un droit, pas une faveur : vous emportez l'appareil chez vous, vous le portez dans votre cuisine, dans le métro, au restaurant, au téléphone avec vos petits-enfants. C'est là que se révèlent les vraies difficultés, jamais dans le calme d'une cabine. Nous vous revoyons pendant cette période pour corriger ce qui doit l'être, et si la solution ne convient pas, vous la rendez sans avoir rien payé.</p>
        <p>Le suivi qui suit l'achat est inclus dans le prix de l'appareil — c'est la loi, et c'est aussi ce qui fait la différence entre un appareil qui fonctionne et un appareil qui déçoit. Votre audition évolue, vos habitudes aussi ; les réglages doivent suivre. À cela s'ajoutent l'entretien courant, le remplacement des dômes et des filtres pare-cérumen, et le nettoyage : autant de rendez-vous courts pour lesquels vous n'avez rien à débourser.</p>
        <p>Comptez environ trois mois entre le premier rendez-vous et le moment où tout est calé. C'est un investissement de temps réel, et nous préférons vous le dire d'emblée plutôt que de le découvrir en cours de route.</p>
        <div class="pull-quote">« Bien entendre, ça se construit dans la durée — pas en une seule visite. »</div>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Financement</span>
      <h2>100 % Santé : ce que vous payez réellement</h2>
      <p>Depuis la réforme 100 % Santé, deux classes d'appareils coexistent — à vous de choisir selon vos besoins et votre budget, en toute transparence.</p>
    </div>
    <div class="reimburse-grid">
      <div class="reimburse-card highlight reveal">
        <span class="tag">Reste à charge 0</span>
        <h3>Classe 1</h3>
        <p>Prix plafonné (950 € par appareil en 2026), incluant réglages et suivi sur 4 ans. Avec une prescription ORL, une affiliation à la Sécurité sociale et une mutuelle responsable, la prise en charge (Sécurité sociale + complémentaire) couvre l'intégralité du prix : 0 € reste à votre charge.</p>
      </div>
      <div class="reimburse-card reveal">
        <span class="tag">Prix libre</span>
        <h3>Classe 2</h3>
        <p>Technologies plus avancées (connectivité, rechargeable, réduction de bruit fine) à prix libre. Remboursement partiel par la Sécurité sociale et votre mutuelle, variable selon votre contrat — un devis normalisé gratuit vous permet de comparer avant de choisir.</p>
      </div>
    </div>
  </div>
</section>

<section class="dark-section">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Encadré par la loi</span>
      <h2>Vos garanties, en toute transparence</h2>
      <p>L'achat d'une aide auditive est strictement encadré par la réglementation française — voici ce à quoi vous avez droit.</p>
    </div>
    <div class="card-grid-3">
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
        <h3>Essai minimum 30 jours</h3>
        <p>La réglementation impose un essai d'au moins 30 jours de l'aide auditive avant tout engagement d'achat, en conditions de vie réelles.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="9"/></svg></div>
        <h3>Garantie légale de 4 ans</h3>
        <p>Chaque aide auditive vendue en boutique est couverte par une garantie légale de 4 ans.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0"/></svg></div>
        <h3>Suivi obligatoire 3-6-12 mois</h3>
        <p>Trois consultations de suivi sont assurées la première année (3e, 6e et 12e mois), puis deux par an les années suivantes, pendant toute la durée de vie de l'appareil.</p>
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container-narrow">
    <div class="section-head center">
      <span class="eyebrow">Questions fréquentes</span>
      <h2>Tout ce que vous vous demandez</h2>
    </div>
    <div class="faq-list">
      <details class="faq-item reveal">
        <summary>Le bilan auditif est-il vraiment gratuit et sans engagement ?<span class="plus">+</span></summary>
        <p>Oui. Le bilan réalisé en boutique par notre audioprothésiste est gratuit et ne vous engage à rien. Il permet simplement d'évaluer précisément votre audition et, si besoin, d'envisager les solutions adaptées.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Ai-je besoin d'une ordonnance pour être appareillé ?<span class="plus">+</span></summary>
        <p>Une prescription médicale (généraliste ou ORL) est nécessaire pour un premier appareillage et pour bénéficier du remboursement Sécurité sociale. Nous pouvons vous orienter vers un ORL partenaire si besoin.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Combien de temps dure la période d'essai ?<span class="plus">+</span></summary>
        <p>Au moins 30 jours, en conditions de vie réelles — chez vous, au travail, dans le bruit — avant toute décision d'achat. C'est une obligation légale, pas une option commerciale.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Quelle est la différence entre Classe 1 et Classe 2 ?<span class="plus">+</span></summary>
        <p>La Classe 1 offre un reste à charge 0 avec un prix plafonné et des prestations essentielles. La Classe 2, à prix libre, donne accès à des technologies plus avancées (connectivité, rechargeable...) avec un remboursement partiel selon votre mutuelle.</p>
      </details>
      <details class="faq-item reveal">
        <summary>L'appareillage se voit-il beaucoup ?<span class="plus">+</span></summary>
        <p>Cela dépend du type d'appareil : un intra-auriculaire sur mesure est quasiment invisible, un micro-contour à écouteur déporté reste très discret. Nous vous montrons les options en essayage avant de choisir.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Que se passe-t-il après l'achat ?<span class="plus">+</span></summary>
        <p>Un suivi est obligatoire aux 3e, 6e et 12e mois, puis deux fois par an — réglages, entretien, changement d'embouts si besoin. Ce suivi est inclus pendant toute la durée de vie de l'appareil.</p>
      </details>
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Prêt à mieux entendre ?</h2>
    <p>Prenez rendez-vous pour un bilan auditif gratuit, sans engagement.</p>
    <a href="/contact.html" class="btn btn-primary">Prendre rendez-vous</a>
  </div>
</section>
"""


# ============================================================================
# PAGE 6 — contact.html
# ============================================================================
BODY_CONTACT = """
<section class="page-hero">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / Contact</div>
    <span class="eyebrow">Venez nous rencontrer</span>
    <h1>Contact</h1>
    <p>Nous serions ravis de vous accueillir en boutique, Galerie Oslo – Olympiades.</p>
  </div>
</section>

<section class="contact">
  <div class="container">
    <div class="contact-grid">
      <div class="contact-info-card reveal">
        <h3>Maison Mikis</h3>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg></div>
          <div><strong>Adresse</strong><span>44 Avenue d'Ivry, 75013 Paris<br>Galerie Oslo – Olympiades</span></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg></div>
          <div><strong>Téléphone</strong><a href="tel:0182280018">01 82 28 00 18</a></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16v16H4z" opacity="0"/><path d="M22 6l-10 7L2 6"/><rect x="2" y="4" width="20" height="16" rx="2"/></svg></div>
          <div><strong>Email</strong><a href="mailto:mikis75013@gmail.com">mikis75013@gmail.com</a></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
          <div><strong>Horaires</strong><span>Mardi – Samedi, 10h00 – 19h30<br>Fermé le dimanche et le lundi</span></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div>
          <div><strong>Accès</strong><span>Métro ligne 14 — Olympiades</span></div>
        </div>
        <div class="social-row">
          <a href="https://www.instagram.com/maisonmikis/" target="_blank" rel="noopener" aria-label="Instagram">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1"/></svg>
          </a>
        </div>
      </div>
      <div class="map-frame reveal">
        <iframe src="https://www.google.com/maps?cid=6701951749895757703&output=embed" loading="lazy" allowfullscreen title="Maison Mikis sur Google Maps — 44 avenue d'Ivry, Paris 13e"></iframe>
      </div>
    </div>
  </div>
</section>

<style>
  .contact-prose{padding-top:10px;}
  .contact-prose .section-head{max-width:760px;}
  .contact-prose .split-text p + p{margin-top:14px;}
  .hours-table{width:100%;max-width:420px;border-collapse:collapse;margin-top:18px;}
  .hours-table th,.hours-table td{text-align:left;padding:9px 0;border-bottom:1px solid rgba(0,0,0,.07);font-size:.95rem;font-weight:400;}
  .hours-table td{text-align:right;}
  .hours-table tr.closed th,.hours-table tr.closed td{opacity:.55;}
</style>

<section class="split contact-prose story-block">
  <div class="container">
    <div class="split-grid">
      <div class="split-text reveal">
        <span class="eyebrow">Y venir</span>
        <h2>Comment nous trouver</h2>
        <p>Maison Mikis se trouve au 44 avenue d'Ivry, dans la Galerie Oslo, au pied de la dalle des Olympiades. La sortie du métro ligne 14 « Olympiades » débouche à quelques dizaines de mètres de la boutique : une fois remonté à l'air libre, vous êtes déjà avenue d'Ivry, et la galerie est sur votre gauche.</p>
        <p>Si vous arrivez par la ligne 7, les stations Tolbiac et Porte d'Ivry sont toutes deux à une petite dizaine de minutes de marche, et la place d'Italie est à un quart d'heure en remontant l'avenue de Choisy. Beaucoup de nos clients viennent d'ailleurs à pied depuis le Triangle de Choisy, en faisant leurs courses.</p>
        <p>En voiture, le stationnement de surface du quartier est payant et souvent saturé en fin de journée ; plusieurs parkings souterrains sont accessibles autour de la dalle et restent la solution la plus simple si vous venez le samedi. La galerie et la boutique sont de plain-pied, sans marche à franchir.</p>
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Quand venir</span>
        <h2>Nos horaires</h2>
        <p>Nous sommes ouverts du mardi au samedi, sans interruption entre midi et deux — vous pouvez donc passer sur votre pause déjeuner sans crainte de trouver porte close.</p>
        <table class="hours-table">
          <tr class="closed"><th scope="row">Lundi</th><td>Fermé</td></tr>
          <tr><th scope="row">Mardi</th><td>10h00 – 19h30</td></tr>
          <tr><th scope="row">Mercredi</th><td>10h00 – 19h30</td></tr>
          <tr><th scope="row">Jeudi</th><td>10h00 – 19h30</td></tr>
          <tr><th scope="row">Vendredi</th><td>10h00 – 19h30</td></tr>
          <tr><th scope="row">Samedi</th><td>10h00 – 19h30</td></tr>
          <tr class="closed"><th scope="row">Dimanche</th><td>Fermé</td></tr>
        </table>
        <p>Le samedi après-midi est de loin le moment le plus fréquenté. Si vous souhaitez prendre votre temps pour essayer plusieurs montures, ou si vous venez pour un bilan auditif, privilégiez plutôt le milieu de semaine ou la matinée.</p>
      </div>
    </div>
  </div>
</section>

<section class="split alt contact-prose story-block">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Sans rendez-vous</span>
        <h2>Faut-il prendre rendez-vous ?</h2>
        <p>Dans la grande majorité des cas, non. Vous pouvez pousser la porte quand vous voulez pendant nos horaires d'ouverture pour essayer des montures, faire ajuster une paire, remplacer des plaquettes, resserrer une charnière, commander des lentilles ou simplement poser une question. Ces gestes-là ne se planifient pas, et nous les faisons volontiers, y compris si vos lunettes n'ont pas été achetées chez nous.</p>
        <p>Un rendez-vous devient utile dès qu'il faut du temps et du calme. C'est le cas pour un <a href="/espace-sante.html">examen de vue</a>, qui demande une vingtaine de minutes en salle dédiée, et plus encore pour un <a href="/espace-audition.html">bilan auditif</a>, qui en demande une quarantaine dans notre espace confidentiel. Un simple appel au <a href="tel:0182280018">01 82 28 00 18</a> suffit pour caler un créneau, souvent dans la même semaine.</p>
        <p>Enfin, si vous cherchez une référence précise, appelez-nous avant de vous déplacer : nous vérifions en direct qu'elle est bien en boutique dans le coloris et la taille qui vous intéressent, plutôt que de vous faire faire le trajet pour rien.</p>
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Sur place</span>
        <h2>Ce qui se passe une fois chez nous</h2>
        <p>Nous ne travaillons pas à la chaîne. Vous êtes reçu par la personne qui vous suivra ensuite, et l'échange commence toujours par vos usages plutôt que par le catalogue : ce que vous faites de vos journées, ce qui vous gêne aujourd'hui, ce que vous portiez avant et pourquoi cela ne vous convenait plus.</p>
        <p>Pour gagner du temps, vous pouvez apporter votre ordonnance si vous en avez une, votre ancienne paire — elle nous renseigne beaucoup, même hors d'usage —, votre carte Vitale et les coordonnées de votre mutuelle. Rien de tout cela n'est obligatoire pour une première visite : nous savons aussi commencer sans.</p>
        <p>Et si vous repartez sans rien acheter, ce n'est pas un problème. Un devis vous est remis systématiquement, il n'engage à rien, et il vous permet de comparer sereinement ou de le transmettre à votre mutuelle avant de décider.</p>
      </div>
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Une question avant de venir ?</h2>
    <p>Appelez-nous au 01 82 28 00 18 ou écrivez-nous : nous répondons rapidement, et souvent la réponse évite un déplacement.</p>
    <a href="tel:0182280018" class="btn btn-primary">01 82 28 00 18</a>
  </div>
</section>
"""


# ============================================================================
# JSON-LD (main entity, homepage only, to avoid duplicate structured data)
# ============================================================================
OPTICIAN_JSONLD = """<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Optician",
  "name": "Maison Mikis",
  "description": "Opticien et audioprothésiste à Paris 13e. Lunettes de vue et de soleil, lentilles de contact et solutions auditives.",
  "url": "https://www.maisonmikis.fr/",
  "telephone": "+33182280018",
  "email": "mikis75013@gmail.com",
  "priceRange": "€€",
  "image": "https://www.maisonmikis.fr/og-image.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "44 Avenue d'Ivry, Galerie Oslo – Olympiades",
    "addressLocality": "Paris",
    "postalCode": "75013",
    "addressCountry": "FR"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 48.8234642,
    "longitude": 2.3660567
  },
  "areaServed": [
    {"@type": "AdministrativeArea", "name": "Paris 13e arrondissement"},
    {"@type": "Place", "name": "Olympiades"},
    {"@type": "Place", "name": "Triangle de Choisy"},
    {"@type": "Place", "name": "Tolbiac"},
    {"@type": "Place", "name": "Place d'Italie"},
    {"@type": "Place", "name": "Porte d'Ivry"},
    {"@type": "Place", "name": "Avenue de France"},
    {"@type": "City", "name": "Ivry-sur-Seine"}
  ],
  "openingHoursSpecification": {
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Tuesday","Wednesday","Thursday","Friday","Saturday"],
    "opens": "10:00",
    "closes": "19:30"
  },
  "sameAs": [
    "https://www.instagram.com/maisonmikis/",
    "https://maps.google.com/?cid=6701951749895757703",
    "https://www.pagesjaunes.fr/pros/65236969",
    "https://lopticien.net/75/paris/maison-mikis-h9h",
    "https://maison-mikis-paris.monopticien.com/"
  ],
  "hasMap": "https://maps.google.com/?cid=6701951749895757703"
}
</script>"""


def faq_jsonld(items):
    """OBSOLETE — NE PLUS APPELER. Conserve pour memoire uniquement.

    Google a annonce le 08/05/2026 la fin des resultats enrichis FAQ et retire
    la documentation FAQPage le 15/06/2026. Le balisage ne produit plus aucun
    affichage. Les deux seuls appels (espace-sante, espace-audition) ont ete
    supprimes le 01/08/2026. Les FAQ restent visibles en clair dans les pages,
    ce qui suffit aux moteurs de reponse. Ne pas reintroduire ces appels.

    items: list of (question, answer_plain_text) tuples -> FAQPage JSON-LD block.
    Mirrors the visible <details>/<summary> FAQ accordions word-for-word, so the
    structured data always matches what's on the page (required by Google's
    guidelines for FAQ rich results / AI Overviews eligibility)."""
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in items
        ],
    }
    return f'<script type="application/ld+json">\n{json.dumps(data, ensure_ascii=False, indent=2)}\n</script>'


def breadcrumb_jsonld(crumbs):
    """crumbs: list of (name, url_or_None) tuples, in display order."""
    items = []
    for i, (name, url) in enumerate(crumbs):
        entry = {"@type": "ListItem", "position": i + 1, "name": name}
        if url:
            entry["item"] = url
        items.append(entry)
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }
    return f'<script type="application/ld+json">\n{json.dumps(data, ensure_ascii=False, indent=2)}\n</script>'


# FAQ text below is copy-pasted verbatim from the visible <details>/<summary>
# accordions in BODY_SANTE and BODY_AUDITION (see further down this file) so
# the structured data never drifts from what visitors actually read.
FAQ_SANTE_ITEMS = [
    ("Comment limiter la fatigue oculaire liée aux écrans ?",
     "Appliquez la règle des 20-20-20 : toutes les 20 minutes, faites une pause de 20 secondes en regardant un point situé à 20 mètres. Pensez aussi à cligner des yeux régulièrement et à régler la luminosité de vos écrans."),
    ("Comment bien choisir sa protection solaire pour les yeux ?",
     "La teinte se choisit selon l'usage : brun ou jaune pour le contraste en conduite ou activité sportive, gris pour une vision naturelle des couleurs, vert pour un bon compromis. Les verres polarisants sont recommandés pour la conduite, l'eau ou la montagne, où les reflets sont importants."),
    ("Quelles sont les bonnes pratiques d'hygiène avec des lentilles de contact ?",
     "Lavez-vous toujours les mains avant manipulation, respectez la durée de port et de renouvellement indiquée, évitez le contact avec l'eau du robinet ou de la douche, et ne dormez jamais avec des lentilles non prévues pour un port prolongé, sauf avis contraire de votre praticien."),
    ("Comment choisir une monture adaptée à mon visage et à mon activité ?",
     "La forme de la monture se choisit en fonction de la morphologie du visage, mais aussi de votre usage principal : une monture légère et enveloppante pour le sport, un maintien renforcé pour le vélo, la voile ou le ski. Notre équipe vous conseille en essayage."),
    ("Quels traitements choisir pour mes verres ?",
     "Plusieurs options se combinent selon vos besoins : verres photochromiques qui s'assombrissent automatiquement à la lumière, filtre anti-lumière bleue pour le confort devant les écrans, ou verres polarisants pour réduire les reflets et l'éblouissement en extérieur."),
    ("Que faire en cas d'yeux secs ou d'allergies oculaires ?",
     "Les allergies saisonnières, notamment au pollen, touchent 20 à 25 % de la population française et provoquent rougeurs et démangeaisons. Des larmes artificielles et l'évitement des frottements soulagent les symptômes légers ; en cas de gêne persistante, un avis médical est recommandé."),
]

FAQ_AUDITION_ITEMS = [
    ("Le bilan auditif est-il vraiment gratuit et sans engagement ?",
     "Oui. Le bilan réalisé en boutique par notre audioprothésiste est gratuit et ne vous engage à rien. Il permet simplement d'évaluer précisément votre audition et, si besoin, d'envisager les solutions adaptées."),
    ("Ai-je besoin d'une ordonnance pour être appareillé ?",
     "Une prescription médicale (généraliste ou ORL) est nécessaire pour un premier appareillage et pour bénéficier du remboursement Sécurité sociale. Nous pouvons vous orienter vers un ORL partenaire si besoin."),
    ("Combien de temps dure la période d'essai ?",
     "Au moins 30 jours, en conditions de vie réelles — chez vous, au travail, dans le bruit — avant toute décision d'achat. C'est une obligation légale, pas une option commerciale."),
    ("Quelle est la différence entre Classe 1 et Classe 2 ?",
     "La Classe 1 offre un reste à charge 0 avec un prix plafonné et des prestations essentielles. La Classe 2, à prix libre, donne accès à des technologies plus avancées (connectivité, rechargeable...) avec un remboursement partiel selon votre mutuelle."),
    ("L'appareillage se voit-il beaucoup ?",
     "Cela dépend du type d'appareil : un intra-auriculaire sur mesure est quasiment invisible, un micro-contour à écouteur déporté reste très discret. Nous vous montrons les options en essayage avant de choisir."),
    ("Que se passe-t-il après l'achat ?",
     "Un suivi est obligatoire aux 3e, 6e et 12e mois, puis deux fois par an — réglages, entretien, changement d'embouts si besoin. Ce suivi est inclus pendant toute la durée de vie de l'appareil."),
]


# ============================================================================
# PAGE 7 — nos-conseils.html (services + guide d'achat + entretien + style)
# Nouvel onglet créé le 24/07/2026, à la place de "La Boutique" dans la nav
# (dont le contenu devient la page d'accueil) — voir décision client.
# Le 24/07/2026 (même jour, précision du client), la page d'accueil a été
# recentrée sur l'histoire pure (fondateurs + quartier) : la section
# "Nos services" (Optique/Solaire/Lentilles/Audition + garanties légales),
# qui s'y trouvait, a donc été déplacée ici, en tête de page.
# Toujours le 24/07/2026 (nouvelle demande le même jour), le client a
# souhaité un vrai guide d'achat, ajouté ici entre "Nos services" et
# "Entretien" : lecture d'ordonnance, choix de monture (fusionné avec
# l'ancien tableau "forme du visage"), types de verres selon la correction,
# traitements de verres, indices d'amincissement, lunettes vs lentilles,
# et quand changer ses lunettes. Faits recherchés sur le web (atol.fr,
# optic2000.com, direct-optic.fr, opticiensparconviction.fr, etc.) et
# reformulés avec les mots de Claude, jamais copiés verbatim. Le reste du
# contenu (entretien courant + style) reste volontairement distinct des
# FAQ déjà présentes dans Espace Santé et Espace Audition (pas de rappels
# médicaux ici).
# ============================================================================
BODY_CONSEILS = """
<section class="page-hero">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / Nos Conseils</div>
    <span class="eyebrow">Au quotidien</span>
    <h1>Nos conseils</h1>
    <p>Comment choisir votre monture, vos verres, leurs traitements et leur amincissement, lunettes ou lentilles, et nos conseils pour bien entretenir et accorder vos lunettes au quotidien.</p>
  </div>
</section>

<section class="split story-block" id="lire-ordonnance">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/conseils/lire-ordonnance.jpg" alt="Verres correcteurs, repère pour lire une ordonnance">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Comprendre sa prescription</span>
        <h2>Comment lire son ordonnance</h2>
        <p>Une ordonnance ophtalmologique peut sembler cryptée au premier regard. Voici comment déchiffrer les principales mentions :</p>
        <ul class="check-list">
          <li><span class="check">✓</span> <strong>OD / OG</strong> — œil droit et œil gauche : chaque œil a sa propre ligne de correction, la vision différant souvent de l'un à l'autre</li>
          <li><span class="check">✓</span> <strong>Sphère</strong> — la puissance de correction en dioptries : un signe négatif corrige la myopie, un signe positif l'hypermétropie</li>
          <li><span class="check">✓</span> <strong>Cylindre et axe</strong> — présents en cas d'astigmatisme, ils précisent l'irrégularité de la cornée et son orientation, de 0° à 180°</li>
          <li><span class="check">✓</span> <strong>Addition</strong> — la puissance supplémentaire pour la vision de près, à partir de la presbytie (généralement après 40-45 ans)</li>
          <li><span class="check">✓</span> <strong>Écart pupillaire</strong> — la distance entre vos pupilles, indispensable pour bien centrer les verres dans la monture</li>
        </ul>
        <p>Une ordonnance reste valable 5 ans entre 16 et 42 ans, 3 ans au-delà de 42 ans, et 1 an pour les moins de 16 ans. En cas de doute sur une mention, notre équipe se fait un plaisir de vous l'expliquer en boutique.</p>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block" id="type-verres">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Vos verres</span>
        <h2>Quel type de verres selon votre correction</h2>
        <p>Le choix du verre dépend avant tout de votre correction et de vos besoins au quotidien — notre équipe vous oriente vers la meilleure option lors de votre examen.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/conseils/type-verres.jpg" alt="Sélection de verres correcteurs" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="services alt">
  <div class="container">
    <div class="device-grid">
      <div class="device-card reveal">
        <h3>Verres unifocaux</h3>
        <p>Une seule correction sur toute la surface du verre : concave et plus fin au centre pour la myopie, convexe et plus épais au centre pour l'hypermétropie, ou adapté à la courbure de votre cornée pour l'astigmatisme.</p>
        <span class="suited">Myopie, hypermétropie, astigmatisme</span>
      </div>
      <div class="device-card reveal">
        <h3>Verres progressifs</h3>
        <p>Trois zones de vision réunies sur un même verre — loin en haut, intermédiaire au centre, près en bas — pour voir net à toutes les distances sans changer de lunettes.</p>
        <span class="suited">Presbytie</span>
      </div>
      <div class="device-card reveal">
        <h3>Verres de proximité</h3>
        <p>Une large zone dédiée à la vision de près et intermédiaire, pensée pour le travail sur écran ou les métiers de précision plutôt que pour la vision de loin.</p>
        <span class="suited">Jeunes presbytes, métiers de précision</span>
      </div>
    </div>
  </div>
</section>

<section class="split story-block" id="traitements-verres">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/conseils/traitements-verres.jpg" alt="Traitements et finitions de verres correcteurs" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Vos traitements</span>
        <h2>Quels traitements pour vos verres</h2>
        <p>Au-delà de la correction, plusieurs traitements peuvent être associés à vos verres selon votre mode de vie et vos habitudes.</p>
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="services-grid">
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l2.4 7.2H22l-6 4.6L18.4 22 12 17.4 5.6 22 8 13.8l-6-4.6h7.6z"/></svg></div>
        <h3>Durcissement anti-rayure</h3>
        <p>Un vernis protecteur qui prolonge la durée de vie du verre et prépare la surface à recevoir les autres traitements.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg></div>
        <h3>Anti-reflet</h3>
        <p>Supprime les reflets et l'effet miroir sur le verre pour une meilleure transparence — particulièrement utile la nuit, en conduite et devant les écrans.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M2 12h4M18 12h4M4.9 19.1l2.8-2.8M16.3 7.7l2.8-2.8"/></svg></div>
        <h3>Anti-salissure</h3>
        <p>Rend la surface du verre plus lisse pour repousser l'eau, la poussière et les traces de doigts, et facilite le nettoyage au quotidien.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/></svg></div>
        <h3>Filtre lumière bleue</h3>
        <p>Atténue une partie de la lumière bleu-violet émise par les écrans, pour limiter la fatigue visuelle en cas d'usage prolongé.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg></div>
        <h3>Photochromique</h3>
        <p>Le verre s'assombrit automatiquement à la lumière du jour et redevient clair en intérieur, avec une protection UV permanente.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg></div>
        <h3>Polarisant</h3>
        <p>Filtre les reflets éblouissants sur l'eau, la neige ou la route, pour un meilleur contraste — idéal en conduite et en extérieur.</p>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block" id="amincissement">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Vos verres, plus fins</span>
        <h2>Quel amincissement selon votre correction</h2>
        <p>Plus l'indice de votre verre est élevé, plus il est fin et léger — un vrai confort pour les corrections importantes.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/conseils/amincissement.jpg" alt="Verres amincis à indice de réfraction élevé" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="degree-scale">
      <div class="degree-card reveal" style="--bar:var(--sage);">
        <div class="db">Indice 1.50</div>
        <h3>Corrections jusqu'à ±2</h3>
        <p>Le verre standard, suffisant pour les corrections légères.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--wood);">
        <div class="db">Indice 1.60</div>
        <h3>Corrections jusqu'à ±4</h3>
        <p>Environ 20 % plus fin qu'un verre standard, pour un bon compromis poids/prix.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta);">
        <div class="db">Indice 1.67</div>
        <h3>Corrections jusqu'à ±6</h3>
        <p>Environ 35 % plus fin, recommandé à partir des corrections fortes.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta-dark);">
        <div class="db">Indice 1.74</div>
        <h3>Corrections au-delà de ±6</h3>
        <p>Le plus fin de nos indices, environ 45 % de gain d'épaisseur, réservé aux très fortes corrections.</p>
      </div>
    </div>
    <p style="max-width:760px;margin:32px auto 0;text-align:center;color:var(--charcoal-soft);font-size:14.5px;">Au-delà de la correction, l'indice le plus adapté dépend aussi de la taille de la monture choisie — notre équipe vous conseille l'équilibre le plus confortable entre finesse, poids et budget.</p>
  </div>
</section>

<section class="split story-block" id="choix-monture">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/accueil-cartes/accueil-optique-lunetterie.jpg" alt="Essayage d'une monture de lunettes" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Bien choisir</span>
        <h2>Comment bien choisir sa monture</h2>
        <p>Entre ajustement, matériau et forme du visage, quelques repères simples pour s'y retrouver avant l'essayage en boutique.</p>
        <ul class="check-list">
          <li><span class="check">✓</span> La monture doit suivre la ligne de vos sourcils, sans les recouvrir</li>
          <li><span class="check">✓</span> Elle ne doit pas toucher vos pommettes, même en souriant</li>
          <li><span class="check">✓</span> Elle doit épouser la largeur de votre visage, sans comprimer les tempes</li>
          <li><span class="check">✓</span> Le poids doit être bien réparti sur le nez et les oreilles, sans marque après plusieurs heures</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <p style="max-width:760px;margin:0 auto 40px;text-align:center;color:var(--charcoal-soft);font-size:14.5px;">Côté matériau : le métal et le titane offrent légèreté, solidité et une allure sobre, avec pour le titane un excellent confort hypoallergénique. L'acétate permet des couleurs et des formes plus affirmées, avec un ajustement facile par nos opticiens. Pour les corrections plus fortes, une monture plus petite et fermée masque mieux l'épaisseur des verres.</p>
    <div class="degree-scale">
      <div class="degree-card reveal" style="--bar:var(--sage);">
        <div class="db">Visage rond</div>
        <h3>Formes angulaires</h3>
        <p>Une monture rectangulaire ou géométrique contraste avec les courbes du visage et lui apporte du caractère.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--wood);">
        <div class="db">Visage carré</div>
        <h3>Formes rondes ou ovales</h3>
        <p>Des bords arrondis adoucissent des traits marqués et équilibrent l'ensemble du visage.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta);">
        <div class="db">Visage ovale</div>
        <h3>Presque toutes les formes</h3>
        <p>Ce visage équilibré s'accommode de la plupart des montures, des plus géométriques aux plus arrondies.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta-dark);">
        <div class="db">Visage en cœur</div>
        <h3>Formes ovales ou rondes</h3>
        <p>Des bords arrondis, plutôt fins sur le haut, rééquilibrent un front plus large que le menton.</p>
      </div>
    </div>
  </div>
</section>

<section class="split story-block" id="entretien-lunettes">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/conseils/entretien-lunettes.jpg" alt="Nettoyage d'un verre de lunettes avec un chiffon doux" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Entretien</span>
        <h2>Bien nettoyer et entretenir ses lunettes</h2>
        <p>Un entretien simple mais régulier prolonge la durée de vie de vos verres et de leurs traitements (anti-reflets, anti-rayures) :</p>
        <ul class="check-list">
          <li><span class="check">✓</span> Rincez les verres à l'eau tiède avant d'essuyer, pour éviter que les poussières ne les rayent</li>
          <li><span class="check">✓</span> Utilisez un savon doux ou un spray nettoyant spécial optique, puis séchez avec un chiffon microfibre propre</li>
          <li><span class="check">✓</span> Évitez alcool, ammoniaque, eau très chaude, essuie-tout ou pan de vêtement, qui abîment les traitements de surface</li>
          <li><span class="check">✓</span> Rangez vos lunettes dans leur étui, verres vers le haut, plutôt que de les poser à plat sur une table</li>
        </ul>
        <p>Un contrôle et un nettoyage aux ultrasons chez votre opticien, une fois par an, complètent utilement l'entretien à la maison.</p>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block" id="quand-changer">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Bon à savoir</span>
        <h2>Quand changer ses lunettes ?</h2>
        <p>Vos verres correcteurs sont un équipement médical à part entière, qui mérite un suivi régulier : tous les ans pour les enfants dont la vue évolue vite, tous les 2 à 3 ans pour les adultes, et tous les 2 ans pour les seniors, davantage exposés aux pathologies oculaires.</p>
        <ul class="check-list">
          <li><span class="check">✓</span> Rayures visibles ou traitements qui s'estompent</li>
          <li><span class="check">✓</span> Fatigue visuelle ou maux de tête en fin de journée</li>
          <li><span class="check">✓</span> Vision moins nette en faible luminosité</li>
          <li><span class="check">✓</span> Gêne en lecture de près qui s'installe</li>
        </ul>
        <p>Le cerveau compense souvent, en douceur, une correction qui n'est plus tout à fait adaptée — d'où l'intérêt d'un contrôle régulier plutôt que d'attendre une gêne franche.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/conseils/quand-changer.jpg" alt="Renouvellement de lunettes de vue" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="split story-block" id="style">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/conseils/style.jpg" alt="Porter ses lunettes avec style au quotidien" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Style</span>
        <h2>Accorder ses lunettes à son look</h2>
        <p>Vos lunettes sont aussi un accessoire à part entière : quelques repères simples pour les intégrer naturellement à votre style.</p>
      </div>
    </div>
  </div>
</section>

<section class="dark-section">
  <div class="container">
    <div class="card-grid-3">
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><circle cx="6" cy="12" r="3.5"/><circle cx="18" cy="12" r="3.5"/><path d="M9.5 12h5M2 12h.5M21.5 12h.5"/></svg></div>
        <h3>Une paire neutre au quotidien</h3>
        <p>Une monture dans des teintes neutres (écaille, noir, transparent) se marie avec toutes les tenues : idéale comme paire de tous les jours.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 3v18M3 12h18"/></svg></div>
        <h3>Harmoniser les métaux</h3>
        <p>Accordez la couleur de la monture (or, argent, cuivré) à vos bijoux et accessoires habituels, pour une silhouette cohérente.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg></div>
        <h3>Une paire signature</h3>
        <p>Une deuxième monture, plus colorée ou plus graphique, pour affirmer votre style lors d'occasions particulières.</p>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block" id="lunettes-ou-lentilles">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Alternative</span>
        <h2>Lunettes ou lentilles : comment choisir</h2>
        <p>Les deux corrigent aussi bien votre vue — le choix dépend surtout de votre mode de vie et de votre confort au quotidien.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/conseils/lunettes-lentilles.jpg" alt="Montures de lunettes, une alternative aux lentilles" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="reimburse-grid">
      <div class="reimburse-card reveal">
        <span class="tag">Style &amp; simplicité</span>
        <h3>Lunettes</h3>
        <p>Un accessoire à part entière qui affirme votre style, sans manipulation ni entretien quotidien. Aucune contre-indication médicale, adaptées à tous les âges.</p>
      </div>
      <div class="reimburse-card highlight reveal">
        <span class="tag">Liberté &amp; sport</span>
        <h3>Lentilles</h3>
        <p>Quasiment invisibles, elles suivent le mouvement de l'œil pour une vision panoramique sans monture — idéales pour le sport. Elles demandent en revanche un entretien rigoureux et ne conviennent pas en cas d'yeux secs ou d'irritations.</p>
      </div>
    </div>
    <p style="max-width:760px;margin:24px auto 0;text-align:center;color:var(--charcoal-soft);font-size:14.5px;">De nombreux clients associent les deux : les lentilles pour le sport ou les sorties, les lunettes le reste du temps. Notre équipe évalue avec vous si vos yeux sont compatibles avec le port de lentilles lors d'une séance d'adaptation.</p>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Une question sur l'entretien de vos équipements ?</h2>
    <p>Passez en boutique, Galerie Oslo – Olympiades : nettoyage, ajustages et petits conseils sont assurés sur place.</p>
    <a href="/contact.html" class="btn btn-primary">Nous rendre visite</a>
  </div>
</section>
"""


# ============================================================================
# BUILD ALL PAGES
# ============================================================================
# ============================================================================
# ACTUALITÉS — journal du site (lancé le 26/07/2026)
# Chaque article a sa propre URL (actualites/<slug>.html) plutôt que d'être
# une simple section sur une grande page : chaque page peut ainsi être
# indexée et positionnée individuellement par Google sur sa propre requête,
# avec son propre titre/meta-description (voir plan SEO — "contenu longue
# traîne", action "en continu"). actualites.html est la page d'index, avec un
# filtre par thématique (JS léger, purement additif : le contenu reste
# entièrement dans le HTML, donc indexable même JS désactivé).
# Contenu recherché sur le web et reformulé avec les mots de Claude, jamais
# copié verbatim, conformément à la politique de citation du site.
# ============================================================================

CATEGORY_ORDER = [
    ("sante-visuelle", "Santé visuelle"),
    ("sante-auditive", "Santé auditive"),
    ("mode-lunettes", "Mode &amp; tendances"),
    ("tech-verres", "Technologies verres"),
    ("tech-lentilles", "Technologies lentilles"),
    ("remboursements", "Remboursements &amp; démarches"),
    ("vie-boutique", "Vie de la boutique"),
    ("enfant", "Vision &amp; audition de l'enfant"),
]
ARTICLE_CATEGORIES = {}
for _i, (_key, _label) in enumerate(CATEGORY_ORDER):
    _accent, _accent_bg = BRAND_ACCENTS[_i % len(BRAND_ACCENTS)]
    ARTICLE_CATEGORIES[_key] = {"label": _label, "accent": _accent, "accent_bg": _accent_bg}

ART_BODY_FATIGUE = """
<h2>Pourquoi les écrans fatiguent-ils autant les yeux ?</h2>
<p>La fatigue visuelle numérique — les ophtalmologistes parlent de syndrome de vision informatique — n'est pas une maladie, mais l'accumulation de deux contraintes que l'œil n'a jamais été conçu pour encaisser huit heures d'affilée. Selon un baromètre OpinionWay réalisé pour l'Asnav, près d'un tiers des actifs français déclarent en souffrir, soit environ dix millions de personnes, et la proportion grimpe encore chez les télétravailleurs. Le temps d'écran quotidien moyen, vie professionnelle et personnelle confondues, avoisine désormais douze heures.</p>

<h3>Un clignement divisé par deux</h3>
<p>Devant un écran, on cligne des yeux jusqu'à 60&nbsp;% moins souvent que dans une conversation normale. Or c'est le clignement qui étale le film lacrymal, cette pellicule de quelques micromètres qui lubrifie et nettoie la surface de l'œil. Moins de clignements, c'est un film qui se rompt entre deux passages : d'où la sécheresse, les picotements, cette impression de grain de sable sous la paupière en fin de journée. Le chauffage en hiver et la climatisation en été assèchent l'air ambiant et aggravent encore le phénomène.</p>

<h3>Un muscle qui ne se relâche jamais</h3>
<p>Le second mécanisme est musculaire. Pour voir net de près, l'œil bombe son cristallin grâce au muscle ciliaire : c'est l'accommodation. Sur un écran placé trop près, trop haut, ou lu pendant des heures sans interruption, ce muscle reste contracté en permanence — exactement comme un bras qui tiendrait une bouteille à l'horizontale toute la journée. La vision qui se brouille par intermittence, les maux de tête frontaux et la difficulté à refaire le point sur un objet lointain en fin de journée viennent de là.</p>

<h2>Quels symptômes doivent alerter, et que traduisent-ils ?</h2>
<p>Les signes se répètent d'un patient à l'autre, et chacun renvoie assez précisément à l'un des deux mécanismes. Ce tableau résume ce que nous entendons le plus souvent au comptoir.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Ce que vous ressentez</th><th>Ce que cela traduit le plus souvent</th><th>Premier réflexe</th></tr>
    </thead>
    <tbody>
      <tr><td>Sécheresse, picotements, œil qui gratte</td><td>Film lacrymal instable par manque de clignement</td><td>Larmes artificielles sans conservateur, air moins sec</td></tr>
      <tr><td>Vision qui se brouille par moments</td><td>Muscle accommodatif épuisé</td><td>Pauses régulières, écran reculé à 50-70&nbsp;cm</td></tr>
      <tr><td>Maux de tête en fin de journée</td><td>Effort de mise au point prolongé, parfois correction inadaptée</td><td>Contrôle de la vue</td></tr>
      <tr><td>Tension dans la nuque et les épaules</td><td>Posture de compensation devant un écran mal placé</td><td>Rehausser ou abaisser l'écran, revoir le siège</td></tr>
      <tr><td>Éblouissement, reflets gênants</td><td>Éclairage ambiant en conflit avec l'écran</td><td>Écran perpendiculaire à la fenêtre, traitement antireflet</td></tr>
      <tr><td>Gêne surtout après 45 ans</td><td>Début de presbytie masqué par le travail sur écran</td><td>Examen de vue, verres adaptés à la distance de travail</td></tr>
    </tbody>
  </table>
</div>

<h2>Les verres anti-lumière bleue sont-ils vraiment utiles ?</h2>
<p>C'est la question qu'on nous pose le plus, et la réponse mérite d'être honnête. Plusieurs revues scientifiques récentes, dont une synthèse Cochrane, ne trouvent pas de preuve solide que les verres filtrant la lumière bleue réduisent la fatigue visuelle numérique en elle-même. Le mécanisme de cette fatigue tient au clignement et à l'accommodation, pas à la longueur d'onde de l'écran. Vendre un filtre comme la solution au problème serait donc inexact.</p>
<p>Cela ne veut pas dire que ces traitements ne servent à rien. Le lien entre exposition à la lumière bleue en soirée et perturbation de l'endormissement est, lui, mieux documenté : si vous travaillez tard, le bénéfice se jouera sur votre sommeil plutôt que sur vos yeux. Et le confort visuel dépend beaucoup du traitement antireflet, qui supprime les reflets parasites de l'éclairage derrière vous — un point souvent confondu avec le filtre bleu alors qu'il s'agit de deux choses différentes.</p>

<h2>Que faire concrètement pour soulager ses yeux ?</h2>
<p>Voici le protocole que nous conseillons en boutique, dans cet ordre. Les quatre premiers points ne coûtent rien et suffisent dans la majorité des cas.</p>
<ol>
  <li><strong>Appliquez la règle des 20-20-20.</strong> Toutes les 20 minutes, regardez quelque chose à environ 20 pieds — soit 6 mètres — pendant 20 secondes. Le muscle accommodatif se relâche, et vous reclignez naturellement.</li>
  <li><strong>Reculez et abaissez l'écran.</strong> Comptez 50 à 70&nbsp;cm entre vos yeux et la dalle, avec le haut de l'écran au niveau des yeux ou légèrement en dessous. Un regard qui plonge un peu expose moins de surface oculaire à l'air.</li>
  <li><strong>Clignez volontairement.</strong> Pendant les phases de concentration intense, deux ou trois clignements appuyés par minute changent réellement le confort de fin de journée.</li>
  <li><strong>Utilisez des larmes artificielles sans conservateur en prévention</strong>, le matin et en milieu d'après-midi, plutôt qu'en rattrapage une fois la gêne installée.</li>
  <li><strong>Réglez la luminosité sur celle de la pièce</strong> et placez l'écran perpendiculairement à la fenêtre, jamais dos ou face à elle.</li>
  <li><strong>Après 40-45 ans, parlez de verres « bureau ».</strong> Ces verres à faible dégression élargissent la zone nette entre 40&nbsp;cm et 2&nbsp;m : c'est souvent le déclic pour ceux qui enchaînent écran, clavier et collègue en face.</li>
</ol>

<h2>Quand faut-il consulter plutôt que régler son écran ?</h2>
<p>Si la gêne persiste après deux à trois semaines de bons réglages, le problème n'est probablement plus ergonomique. Une correction même légère et non portée, un astigmatisme ignoré, une presbytie qui démarre ou de simples verres mal centrés suffisent à expliquer des mois de fatigue visuelle. Une douleur oculaire vraie, une baisse de vision brutale, une vision double ou des éclairs lumineux, en revanche, relèvent d'un avis médical rapide et non de l'opticien.</p>
<p>À Maison Mikis, Galerie Oslo sur l'Esplanade des Olympiades, nous voyons beaucoup de salariés des tours voisines et d'étudiants du quartier Tolbiac venir avec exactement ce tableau. Le contrôle de vue se fait sans rendez-vous, et prend une vingtaine de minutes : dans un cas sur deux, il s'agit d'un simple ajustement de correction ou d'une paire dédiée au poste de travail, pas d'un problème de santé.</p>
"""

ART_BODY_AUDITION_SILENCIEUSE = """
<h2>Pourquoi une baisse d'audition passe-t-elle si longtemps inaperçue ?</h2>
<p>La perte auditive liée à l'âge et celle liée au bruit avancent par petits pas, sur des années, sans douleur et sans rupture nette. Ce sont d'abord les fréquences aiguës qui s'émoussent, or ce sont elles qui portent les consonnes — le « s », le « f », le « ch ». Les voyelles, plus graves, restent parfaitement audibles. On continue donc d'entendre qu'on vous parle, mais on comprend de moins en moins bien ce qui est dit. Cette dissociation entre entendre et comprendre est le vrai piège du dépistage précoce.</p>

<h3>Le cerveau compense sans prévenir</h3>
<p>Face à une information sonore incomplète, le cerveau reconstitue : il s'appuie sur le contexte de la phrase, sur les mouvements des lèvres, sur les habitudes de langage de l'interlocuteur. Ce travail est si efficace qu'il masque la gêne pendant des années, tant que la conversation se déroule dans le calme et en face à face. Il a pourtant un coût : une fatigue d'écoute bien réelle, qui se traduit en fin de journée par une envie de silence, une irritabilité inhabituelle ou l'abandon progressif des repas de famille.</p>

<h3>L'entourage s'en aperçoit souvent le premier</h3>
<p>Dans la plupart des situations que nous voyons en boutique, ce n'est pas la personne concernée qui pousse la porte : c'est son conjoint, ses enfants ou un collègue. Les remarques reviennent presque toujours dans les mêmes termes : la télévision est trop forte, il faut tout répéter, les échanges au téléphone tournent court. La personne, elle, a le sentiment sincère que les autres articulent mal. Ce décalage de perception explique une bonne part du retard au diagnostic.</p>

<h2>Quels signes doivent faire penser à une perte auditive ?</h2>
<p>Aucun signe pris isolément ne suffit à conclure, et une baisse passagère après un rhume ou un bouchon de cérumen n'a rien à voir avec une atteinte durable. En revanche, l'accumulation de plusieurs de ces situations sur plusieurs mois mérite une vérification. Voici les motifs que nous entendons le plus souvent, et ce qu'ils traduisent en général.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Ce que vous vivez</th><th>Ce que cela traduit le plus souvent</th><th>Premier réflexe</th></tr>
    </thead>
    <tbody>
      <tr><td>Vous décrochez au restaurant ou en réunion</td><td>Difficulté à séparer la parole du bruit de fond</td><td>Faire vérifier son audition</td></tr>
      <tr><td>Vous faites répéter, on « articule mal »</td><td>Consonnes aiguës moins bien perçues</td><td>Faire vérifier son audition</td></tr>
      <tr><td>La télévision monte cran par cran</td><td>Seuil d'audition qui glisse progressivement</td><td>Comparer le volume avec celui des proches</td></tr>
      <tr><td>Le téléphone est devenu inconfortable</td><td>Absence de lecture labiale, son plus étroit</td><td>Tester l'autre oreille, noter l'asymétrie</td></tr>
      <tr><td>Sifflements ou bourdonnements persistants</td><td>Les acouphènes accompagnent souvent une atteinte de l'oreille interne</td><td>Avis d'un professionnel de l'audition</td></tr>
      <tr><td>Baisse brutale d'un seul côté, vertiges</td><td>Situation potentiellement urgente</td><td>Consulter un médecin ou un ORL sans délai</td></tr>
    </tbody>
  </table>
</div>

<h2>Pourquoi attend-on 7 à 10 ans avant de consulter ?</h2>
<p>Selon le Syndicat des Audioprothésistes, il s'écoule en moyenne 7 à 10 ans entre l'apparition des premiers symptômes et le premier appareillage en France. Le chiffre surprend, jusqu'à ce qu'on regarde ce qui se passe une fois la décision prise : le premier rendez-vous intervient généralement sous 18 jours, parfois davantage en zone rurale. Autrement dit, le frein n'est pas la disponibilité des professionnels, mais le temps que met chacun à se décider.</p>
<p>Les raisons de cette hésitation sont toujours les mêmes : on associe encore l'appareillage à la vieillesse, on se dit qu'on entend « quand même », on redoute la dépense avant même de savoir de quoi il retourne. Un bilan auditif ne préjuge pourtant de rien. Il peut conclure à une audition normale, à un simple bouchon de cérumen, ou à une gêne qui ne justifie aucun équipement dans l'immédiat.</p>

<h2>Que dit la Lancet Commission sur les risques d'une perte non traitée ?</h2>
<p>Le rapport 2020 de la Lancet Commission on dementia prevention, confirmé et renforcé par sa mise à jour de 2024, identifie la perte auditive non traitée en milieu de vie comme le principal facteur de risque modifiable de démence, devant tous les autres facteurs évitables. Le mécanisme suspecté passe en grande partie par l'isolement social : fatigue d'écoute, retrait des conversations de groupe, réduction des sorties et des sollicitations, autant d'éléments qui entretiennent à leur tour le risque cognitif. Il s'agit d'une association établie à l'échelle des populations, pas d'une garantie individuelle — mais elle suffit à changer le regard sur un dépistage que l'on repousse volontiers.</p>
<p>Les repères de dépistage suivent la même logique. En France, environ 65&nbsp;% des personnes de plus de 65 ans présentent des troubles auditifs, et l'Organisation mondiale de la santé recommande un dépistage systématique dès 60 ans. Pour les actifs, un premier contrôle est proposé dès 45-50 ans par la médecine du travail, en particulier dans les métiers exposés au bruit.</p>

<h2>Comment s'auto-évaluer avant de prendre rendez-vous ?</h2>
<p>Des outils d'auto-évaluation existent pour se faire une première idée. Ils ne remplacent jamais une mesure en cabine, mais ils ont un mérite : transformer une impression vague en constat clair, et donc aider à ne plus repousser la démarche.</p>
<ol>
  <li><strong>Observez-vous en situation bruyante</strong> plutôt que dans le calme. C'est au restaurant, dans un hall de gare ou lors d'un repas de famille que la gêne apparaît en premier.</li>
  <li><strong>Comparez vos deux oreilles</strong> au téléphone, sur le même appel. Une différence nette entre les deux côtés est une information importante à signaler.</li>
  <li><strong>Demandez à un proche</strong> de régler votre téléviseur au volume qui lui convient. L'écart est souvent plus parlant qu'un long questionnaire.</li>
  <li><strong>Faites un test d'écoute rapide</strong> en ligne ou en application, dans une pièce silencieuse et avec un casque correct. Le résultat n'a valeur que d'orientation.</li>
  <li><strong>Après 60 ans, essayez un questionnaire validé</strong> comme le HHIE-S, conçu pour mesurer le retentissement de la gêne auditive au quotidien.</li>
  <li><strong>Notez ce que vous avez remarqué</strong>, depuis quand et dans quelles circonstances. Ces quelques lignes font gagner du temps au rendez-vous.</li>
</ol>

<h2>Comment se passe un contrôle de l'audition, et à qui s'adresser ?</h2>
<p>Un bilan auditif chez l'audioprothésiste dure une petite heure. Il commence par un entretien sur vos gênes et vos antécédents, se poursuit par un examen du conduit et du tympan à l'otoscope, puis par des mesures en cabine : on cherche le seuil auquel vous percevez des sons purs, oreille par oreille, et on vérifie votre capacité à répéter des mots, dans le silence puis dans le bruit. C'est ce dernier point qui reflète le mieux la vie réelle.</p>
<p>La répartition des rôles mérite d'être rappelée. L'audioprothésiste dépiste, mesure, appareille et assure le suivi ; le diagnostic, la recherche d'une cause et la prescription relèvent du médecin traitant ou de l'ORL. Une baisse brutale, une douleur, un écoulement ou des vertiges imposent un avis médical rapide.</p>
<p>À Maison Mikis, Galerie Oslo sur l'Esplanade des Olympiades, ce contrôle est gratuit, sans engagement, et se fait sur rendez-vous. Beaucoup de nos clients viennent accompagnés d'un proche, et nous les y encourageons : celui qui vous entend parler tous les jours apporte des observations que l'on ne se formule jamais soi-même. Si tout est normal, nous vous le dirons simplement, et nous vous proposerons de repasser dans deux ou trois ans pour comparer.</p>
"""

ART_BODY_MONTURES_2026 = """
<h2>Quelles formes de montures s'imposent en 2026 ?</h2>
<p>La saison confirme le retour en force des formes géométriques : carrées, rectangulaires, parfois hexagonales, elles donnent au regard un cadre net et une allure affirmée. À côté d'elles, le papillon hérité des années 50-60 revient dans une version allégée, avec des branches fines et une silhouette redessinée, tandis que l'œil-de-chat assume une ligne remontante franchement graphique. Les rondes et les ovales, elles, n'ont jamais quitté les présentoirs : elles reviennent réinterprétées, souvent avec des branches plus travaillées que le face lui-même. La bonne nouvelle, c'est qu'il n'existe pas une forme obligatoire cette année, mais plusieurs familles qui cohabitent sans se contredire.</p>

<h3>Le grand format continue de progresser</h3>
<p>À l'autre bout du spectre, les modèles oversize et architecturaux gagnent du terrain, parfois jusqu'à un effet enveloppant qui rappelle le masque. C'est une tendance spectaculaire, très visible en photo, et qui demande d'être essayée avec un peu de recul : plus une monture est large, plus elle dépend de la largeur réelle du visage et de la hauteur du nez pour rester confortable. Dans le même temps, l'aviateur reste ce qu'il a toujours été, une valeur sûre que l'on retrouve chaque saison sans qu'elle ait besoin d'être remise au goût du jour.</p>

<h2>Quelles matières et quelles couleurs dominent la saison ?</h2>
<p>L'acétate demeure le matériau roi de la lunetterie : léger, résistant, il se décline dans une variété de couleurs qu'aucune autre matière n'égale. L'écaille, ou tortoiseshell, continue de dominer largement, dans des teintes caramel, chocolat et ambre qui ont l'avantage de s'accorder à presque toutes les carnations. En parallèle, la transparence s'installe durablement, avec des acétates cristallins et des teintes translucides de type blush ou champagne, plus discrètes sur le visage. Côté couleurs, les tons neutres et nude dominent, ponctués de bourgogne ou de vert profond, et les verres légèrement teintés — ambre, brun, rose léger — se portent désormais au quotidien et plus seulement en solaire.</p>

<h3>Le métal fin et l'esprit minimaliste</h3>
<p>Le métal fin, doré, argenté ou bronze, s'est imposé comme l'autre grande signature de la saison, dans un esprit que le vocabulaire de la mode appelle quiet luxury : peu de matière, une ligne nette, aucune ostentation. Ce type de monture a un vrai atout pratique, celui de se faire oublier sur le visage, et un point de vigilance, celui de la solidité des branches très fines si l'on a l'habitude de manipuler ses lunettes d'une seule main. Ce n'est pas rédhibitoire, c'est simplement une chose à savoir avant de choisir.</p>

<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Tendance 2026</th><th>Ce qu'elle apporte</th><th>Point de vigilance</th></tr>
    </thead>
    <tbody>
      <tr><td>Formes géométriques</td><td>Un cadre net, un regard structuré</td><td>Les angles marqués durcissent parfois les traits anguleux</td></tr>
      <tr><td>Papillon et œil-de-chat</td><td>Une ligne montante qui ouvre le regard</td><td>Demande une hauteur de verre suffisante pour les progressifs</td></tr>
      <tr><td>Oversize et architectural</td><td>Un effet mode immédiat</td><td>Poids et appui sur le nez à vérifier après quelques minutes</td></tr>
      <tr><td>Acétate translucide</td><td>Une présence légère, très facile à porter</td><td>Se marie mal avec certaines montures très colorées</td></tr>
      <tr><td>Métal fin doré ou argenté</td><td>Discrétion et confort de port</td><td>Branches fines à manipuler à deux mains</td></tr>
      <tr><td>Verres légèrement teintés</td><td>Un confort lumineux et un vrai parti pris esthétique</td><td>Teinte à choisir selon l'usage, pas seulement selon la couleur</td></tr>
    </tbody>
  </table>
</div>

<h2>Les lunettes ont-elles encore un genre ?</h2>
<p>Un mouvement de fond, plus discret que les formes mais sans doute plus durable, traverse les collections : les frontières entre montures dites « homme » et « femme » s'estompent. Les fabricants dessinent de plus en plus des modèles pensés pour s'adapter à des morphologies variées, et les palettes neutres qui dominent la saison accompagnent naturellement ce glissement. Concrètement, en boutique, cela signifie qu'il n'y a plus grand sens à guider quelqu'un vers un présentoir plutôt qu'un autre selon son genre. Nous préférons partir de la largeur du visage, de la correction et du style recherché, ce qui ouvre presque toujours des pistes auxquelles la personne n'aurait pas pensé.</p>
<p>Autre évolution notable, les matériaux responsables progressent dans les collections : acétate biosourcé, plastique recyclé, mais aussi titane et fibres de carbone pour des montures hybrides très légères. Ces matières ne relèvent plus de la niche militante, elles se retrouvent aujourd'hui aussi bien chez des maisons indépendantes que dans les collections des grands groupes.</p>

<h2>Comment savoir si une tendance vous ira vraiment ?</h2>
<p>Une monture à la mode ne sert à rien si elle ne s'accorde ni à votre visage ni à votre correction. Voici l'ordre dans lequel nous conseillons de raisonner, en boutique comme chez soi.</p>
<ol>
  <li><strong>Commencez par la largeur du visage.</strong> Une monture dont le face dépasse nettement les tempes glissera, quelle que soit sa beauté sur le présentoir. C'est le critère qui élimine le plus de modèles, et le plus rapidement.</li>
  <li><strong>Vérifiez ensuite la compatibilité avec vos verres.</strong> Une forte correction supporte mal les grandes formes très fines, et un verre progressif demande une hauteur suffisante pour que la zone de lecture existe réellement.</li>
  <li><strong>Regardez le nez et les oreilles.</strong> L'appui nasal et la position des branches déterminent le confort au bout de deux heures, pas au bout de deux minutes devant le miroir.</li>
  <li><strong>Choisissez la matière selon votre usage</strong> plutôt que selon la seule esthétique : un acétate épais encaisse mieux les manipulations quotidiennes qu'un métal très fin.</li>
  <li><strong>Gardez la couleur pour la fin.</strong> C'est le critère le plus amusant, mais aussi celui qui fait le plus souvent regretter un achat lorsqu'il passe en premier.</li>
</ol>

<h2>Faut-il vraiment tout tester avant de choisir ?</h2>
<p>Nous le pensons, oui, et pas par principe commercial. Beaucoup de formes très photogéniques en ligne se comportent tout autrement une fois posées sur un vrai visage, parce qu'une photo ne restitue ni le poids, ni le galbe, ni la façon dont la monture bouge quand on parle. À l'inverse, un modèle que l'on n'aurait jamais décroché du présentoir se révèle parfois évident dès qu'on le porte. C'est aussi pour cela que nous encourageons à venir essayer plusieurs familles de formes, y compris celles dont on est certain qu'elles ne conviendront pas.</p>
<p>Dans notre boutique de la Galerie Oslo, sur l'Esplanade des Olympiades, un essayage se fait sans rendez-vous et sans obligation d'achat. Nous prenons le temps de prérégler la monture sur le visage avant de vous laisser juger dans la glace, car une paire mal posée donne systématiquement une mauvaise impression. Et si la question de la correction se pose en même temps, un contrôle de la vue permet de savoir où vous en êtes, sachant qu'une ordonnance en cours de validité reste indispensable pour toute commande de verres correcteurs.</p>
"""

ART_BODY_TECH_VERRES = """
<h2>Qu'est-ce qui a vraiment changé dans les verres correcteurs ?</h2>
<p>Vu de loin, un verre correcteur ressemble encore à ce qu'il était il y a vingt ans : un disque transparent taillé pour compenser un défaut optique. Ce qui a bougé se joue ailleurs, dans trois domaines qui avancent en parallèle. D'abord la géométrie de la surface, aujourd'hui calculée point par point par ordinateur plutôt que choisie dans un catalogue de designs standard. Ensuite les traitements de surface, qui se sont spécialisés au lieu de tout bloquer indistinctement. Enfin, et c'est le changement le plus important sur le plan de la santé publique, l'apparition de verres dont l'objectif n'est plus seulement de corriger la vue d'un enfant, mais d'agir sur l'évolution de son trouble. Tout le reste relève du confort, ce qui n'est pas rien mais ne se compare pas.</p>

<h2>Peut-on freiner la myopie chez l'enfant avec des verres ?</h2>
<p>C'est l'axe de recherche le plus actif du secteur, et le seul où les verriers travaillent sur une trajectoire de santé plutôt que sur du confort. En France, environ 2,1 millions d'enfants sont concernés par la myopie, dont 510&nbsp;000 en forme forte ou en évolution rapide. L'enjeu n'est pas la gêne du moment, qu'une correction classique règle très bien : c'est le fait qu'un œil devenu trop long expose davantage, à l'âge adulte, à des complications de la rétine.</p>

<h3>Le principe du myodéfocus périphérique</h3>
<p>Deux familles de verres se partagent aujourd'hui le sujet. Essilor Stellest, dont la deuxième génération a été lancée en 2025, s'appuie sur un réseau de micro-lentilles disposées en anneaux concentriques autour d'une zone centrale de correction classique. Hoya MiyoSmart, développé avec l'Université Polytechnique de Hong Kong, repose sur un principe voisin, la technologie D.I.M.S. Dans les deux cas, l'idée est identique : l'enfant voit net par le centre du verre, tandis que la périphérie renvoie volontairement l'image légèrement en avant de la rétine, un signal censé freiner l'allongement du globe oculaire.</p>

<h3>Ce que ces verres ne font pas</h3>
<p>Soyons clairs : ils ne corrigent pas définitivement le défaut et ne le font pas régresser. Hoya indique que MiyoSmart, adossé à plus de cent publications scientifiques, peut freiner une progression cliniquement significative dès douze mois d'utilisation chez les 4-12 ans — c'est une donnée annoncée par le fabricant, pas une promesse de résultat individuel. La prescription et le suivi relèvent de l'ophtalmologiste, qui mesure l'évolution de la correction et, quand c'est possible, la longueur de l'œil. Notre rôle d'opticien s'arrête au montage, au centrage précis et à la vérification du port réel, car ces verres ne servent à rien s'ils passent la journée dans un cartable.</p>

<h2>Les verres photochromiques tiennent-ils enfin leurs promesses ?</h2>
<p>Les verres qui foncent au soleil ont longtemps traîné une réputation de lenteur. La dernière génération de verres Transitions s'active en 25 secondes environ pour atteindre une teinte comparable à celle d'un verre solaire classique, et s'éclaircit deux fois plus vite que la génération précédente, avec un filtrage de la lumière bleue-violette annoncé jusqu'à 85&nbsp;% à l'état foncé et une protection contre les ultraviolets. Ces valeurs sont celles du fabricant, mesurées dans ses propres conditions d'essai.</p>
<p>Reste une limite qu'il vaut mieux connaître avant de commander : derrière un pare-brise, qui bloque déjà une grande partie des ultraviolets, l'activation demeure incomplète. Les verriers y travaillent, avec des performances qui varient encore beaucoup d'une marque à l'autre. Si vous conduisez souvent en plein soleil, une véritable paire solaire correctrice reste plus efficace, et nous préférons le dire avant l'achat plutôt qu'après.</p>

<h2>Le sur-mesure numérique change-t-il quelque chose pour le porteur ?</h2>
<p>Les verres progressifs ne sortent plus systématiquement d'un moule standard. Le surfaçage dit freeform permet de calculer la surface point par point en intégrant la morphologie du porteur, sa posture de lecture et la distance entre l'œil et le verre. Le bénéfice se sent surtout sur les zones latérales, souvent floues sur les designs anciens, et sur la facilité à trouver la bonne zone de netteté sans tourner la tête.</p>

<h3>Une personnalisation utile, mais pas pour tout le monde</h3>
<p>Honnêteté oblige : sur une correction simple et une monture classique, l'écart avec un bon verre de milieu de gamme est parfois modeste, alors que l'écart de prix, lui, ne l'est pas. La montée en gamme systématique sur les progressifs est une pratique répandue dans le secteur, et nous ne la trouvons pas justifiée pour tous les porteurs : mieux vaut partir de vos journées et de vos gênes réelles.</p>
<p>Pour le travail prolongé sur écran, une autre piste mérite d'être connue : les verres à faible dégression de puissance, comme la famille Eyezen chez Essilor, conçus pour soulager l'effort d'accommodation en vision de près et intermédiaire.</p>

<h2>Faut-il un filtre anti-lumière bleue sur ses verres ?</h2>
<p>Les traitements ont beaucoup évolué, et la première génération, qui bloquait indistinctement toute la lumière bleue, appartient au passé. Les solutions actuelles — Eye Protect System chez Essilor, BlueGuard chez Zeiss — filtrent de façon ciblée la lumière bleue-violette réputée la plus agressive, tout en laissant passer la lumière bleue-turquoise, celle qui participe à la régulation du rythme circadien. La protection contre les ultraviolets, de son côté, tend à être intégrée à la matière même du verre plutôt qu'appliquée en surface, ce qui la rend moins sensible à l'usure.</p>
<p>Cela dit, la fatigue ressentie devant un écran s'explique surtout par le manque de clignement et par une accommodation prolongée. Un filtre ne remplace ni les pauses ni un poste correctement réglé. Un bon antireflet, en revanche, change réellement le confort en supprimant les reflets parasites de l'éclairage situé derrière vous. Voici comment nous résumons ces quatre familles au comptoir.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Innovation</th><th>À qui elle s'adresse en priorité</th><th>Ce qu'elle ne fait pas</th></tr>
    </thead>
    <tbody>
      <tr><td>Verres de freination</td><td>Enfant dont la correction progresse vite</td><td>Ne supprime pas le trouble, ne dispense pas du suivi médical</td></tr>
      <tr><td>Photochromique récent</td><td>Porteur qui alterne intérieur et extérieur</td><td>Ne fonce pas pleinement derrière un pare-brise</td></tr>
      <tr><td>Surfaçage freeform</td><td>Correction complexe, monture galbée, forte demande de confort</td><td>N'améliore pas une correction mal mesurée au départ</td></tr>
      <tr><td>Verre à faible dégression</td><td>Journées longues devant un écran</td><td>Ne remplace pas une paire pour la vision de loin</td></tr>
      <tr><td>Filtre bleu-violet ciblé</td><td>Travail tardif, sensibilité à l'éblouissement</td><td>Ne soigne pas la fatigue visuelle numérique</td></tr>
    </tbody>
  </table>
</div>

<h2>Comment savoir lesquelles vous concernent vraiment ?</h2>
<p>La bonne méthode consiste à partir de votre quotidien, pas du catalogue. Voici l'ordre dans lequel nous abordons la question en boutique.</p>
<ol>
  <li><strong>Repartez d'une ordonnance à jour.</strong> Aucune technologie ne rattrape une correction ancienne ou approximative.</li>
  <li><strong>Décrivez vos journées</strong> : distances de travail, heures d'écran, trajets, conduite de nuit, activités extérieures.</li>
  <li><strong>Traitez d'abord la gêne principale</strong>, une seule à la fois, plutôt que d'empiler les options sur une même paire.</li>
  <li><strong>Demandez ce que chaque supplément apporte concrètement</strong>, et faites-vous expliquer ce qui relève du confort et ce qui relève de la santé.</li>
  <li><strong>Comparez sur devis normalisé</strong>, le seul document qui permette de mettre deux propositions côte à côte.</li>
</ol>
<p>À Maison Mikis, Galerie Oslo sur l'Esplanade des Olympiades, nous voyons beaucoup de familles du quartier venir avec une question simple : faut-il payer plus cher pour mieux voir ? La réponse est parfois oui, souvent non, et elle dépend de la correction et du mode de vie. Le contrôle de vue ne coûte rien, et repartir avec un devis à comparer chez soi nous paraît une démarche parfaitement saine.</p>
"""

ART_BODY_TECH_LENTILLES = """
<h2>Qu'est-ce qui a vraiment changé du côté des matériaux ?</h2>
<p>L'essentiel des progrès se joue sur un point discret mais décisif : la quantité d'oxygène qui atteint la cornée à travers la lentille, et la façon dont le matériau conserve son hydratation au fil des heures. Les silicone-hydrogels de nouvelle génération cherchent à réconcilier ces deux exigences longtemps opposées, avec une meilleure perméabilité à l'oxygène sans perdre en souplesse ni en confort. C'est ce qui permet à un porteur de tenir une journée entière sans cette sensation d'œil sec de fin d'après-midi que connaissaient bien les générations précédentes de lentilles.</p>
<p>Les fabricants communiquent beaucoup sur ce terrain, et il faut lire leurs annonces pour ce qu'elles sont : des revendications de marque. Alcon met en avant sur PRECISION1 une technologie baptisée SmartSurface, présentée comme une surface proche de celle de la cornée naturelle. Johnson &amp; Johnson positionne de son côté ACUVUE OASYS MAX 1-Day sur le même registre du confort prolongé. Dans les deux cas, ces gammes existent aussi en version conçue pour l'astigmatisme, ce qui n'allait pas de soi il y a quelques années.</p>

<h3>Journalières et mensuelles gardent chacune leur place</h3>
<p>Aucune de ces deux familles n'a rendu l'autre obsolète. La lentille journalière reste la plus recommandée sur le plan de l'hygiène, puisqu'elle supprime la manipulation d'un étui et d'une solution d'entretien, donc une partie du risque infectieux. Elle est particulièrement indiquée pour un port occasionnel ou en cas de terrain allergique. La lentille mensuelle, elle, conserve tout son intérêt pour un port régulier et un budget plus maîtrisé, à condition d'accepter la discipline d'entretien qui va avec. Le bon choix dépend de votre rythme de vie autant que de votre œil.</p>

<h2>Peut-on freiner la myopie d'un enfant avec des lentilles ?</h2>
<p>C'est probablement l'évolution la plus importante de ces dernières années, parce qu'elle change la nature même de l'objet : la lentille n'est plus seulement un outil de correction, elle devient un outil de freination. MiSight 1 day est la première lentille souple journalière à disposer d'une indication officielle de ralentissement de la progression de la myopie chez l'enfant, par un principe de défocalisation périphérique. CooperVision a construit autour de cet enjeu une gamme dédiée, Specialty EyeCare.</p>
<h3>Une décision qui revient à l'ophtalmologiste</h3>
<p>Une autre voie existe pour certains profils : l'orthokératologie, c'est-à-dire le port de lentilles rigides pendant la nuit, retirées au réveil. Dans tous les cas, il s'agit d'un parcours médical, pas d'un choix d'équipement : la décision revient à l'ophtalmologiste, avec un suivi rapproché de l'évolution. Aucun de ces dispositifs ne fait disparaître une myopie existante ; l'objectif est d'en limiter l'aggravation pendant la période de croissance.</p>

<h2>Astigmatisme et presbytie : l'offre s'est-elle vraiment élargie ?</h2>
<p>Oui, et c'est une bonne nouvelle pour deux profils longtemps mal servis. Les lentilles toriques, destinées à l'astigmatisme, bénéficient d'une stabilisation améliorée sur l'œil et de matériaux plus fins, y compris en version journalière : le rendu visuel est plus constant d'un clignement à l'autre. Pour la presbytie, les designs multifocaux dits « pupille-optimisés » élargissent l'offre destinée aux porteurs qui souhaitent se passer de lunettes au quotidien. Le résultat n'est jamais identique à celui d'un verre progressif, et il faut souvent accepter un temps d'adaptation, mais le confort obtenu s'est nettement amélioré.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Votre situation</th><th>Ce qui se discute le plus souvent</th><th>Point de vigilance</th></tr>
    </thead>
    <tbody>
      <tr><td>Port occasionnel, sport, week-end</td><td>Journalière en silicone-hydrogel</td><td>Ne pas conserver une journalière au-delà de la journée</td></tr>
      <tr><td>Port quotidien, budget suivi</td><td>Mensuelle avec entretien rigoureux</td><td>Respecter la date de renouvellement, sans la repousser</td></tr>
      <tr><td>Astigmatisme</td><td>Lentille torique, désormais aussi en journalière</td><td>Stabilité de la vision à vérifier à l'essai</td></tr>
      <tr><td>Presbytie</td><td>Multifocale, parfois associée à une correction en lunettes</td><td>Prévoir un temps d'adaptation avant de conclure</td></tr>
      <tr><td>Enfant myope en progression</td><td>Lentille freinatrice ou orthokératologie</td><td>Décision et suivi assurés par l'ophtalmologiste</td></tr>
    </tbody>
  </table>
</div>

<h2>Les lentilles connectées existent-elles déjà ?</h2>
<p>Le sujet revient régulièrement dans la presse, avec des images spectaculaires, et il mérite une réponse franche : non, rien de tel n'est aujourd'hui commercialisé. La start-up Mojo Vision développe, en partenariat avec le fabricant Menicon, des prototypes intégrant un micro-écran destiné à afficher de la réalité augmentée directement sur l'œil. Des démonstrations fonctionnelles ont été présentées publiquement, ce qui n'est déjà pas rien sur le plan technique, mais la technologie n'en est qu'à ses débuts et aucun porteur ne peut s'en équiper. Si l'on vous propose ce type de produit, méfiez-vous.</p>

<h2>Comment savoir laquelle vous conviendrait, et où l'essayer ?</h2>
<p>Aucune fiche technique ne remplace un essai sur votre œil. L'adaptation d'une lentille se fait toujours sur prescription d'un ophtalmologiste, puis avec un essai accompagné en boutique : nous mesurons, nous posons, nous vous apprenons à manipuler, et nous vous revoyons pour vérifier la tolérance avant de valider quoi que ce soit. Un matériau excellent sur le papier peut ne pas convenir à une cornée particulière ou à un film lacrymal fragile.</p>
<ol>
  <li><strong>Consultez d'abord un ophtalmologiste</strong> pour un examen complet et une prescription précisant le type de lentille.</li>
  <li><strong>Venez pour un essai accompagné</strong>, avec le temps nécessaire pour apprendre la pose, le retrait et les gestes d'hygiène.</li>
  <li><strong>Portez la lentille dans vos conditions réelles</strong> — écran, transports, sport — avant de vous décider.</li>
  <li><strong>Revenez pour le contrôle de tolérance</strong> : c'est lui qui valide l'adaptation, pas la première impression.</li>
  <li><strong>Respectez ensuite les règles d'hygiène</strong> : mains lavées et séchées, jamais d'eau du robinet sur les lentilles ni sur l'étui, solution d'entretien renouvelée à chaque usage et rythme de renouvellement scrupuleusement suivi.</li>
</ol>
<p>Un œil rouge, douloureux ou une baisse de vision chez un porteur de lentilles n'est jamais banal : on retire la lentille et on consulte sans attendre. Pour le reste, nos opticiens répondent volontiers aux questions du quotidien, à la Galerie Oslo sur l'Esplanade des Olympiades. Beaucoup de porteurs du quartier passent simplement pour vérifier qu'ils manipulent correctement leurs lentilles, et c'est une excellente raison de venir.</p>
"""

ART_BODY_REMBOURSEMENTS = """
<h2>Qu'est-ce que le 100 % Santé, concrètement ?</h2>
<p>Le 100 % Santé est un panier de soins défini par la réglementation, dans lequel l'Assurance Maladie et votre complémentaire santé se partagent la totalité de la facture. En optique comme en audiologie, le professionnel a l'obligation de vous proposer au moins une solution de ce panier, et de la faire apparaître sur le devis. Vous restez évidemment libre de choisir autre chose : le dispositif ouvre une porte, il ne referme rien.</p>
<p>Deux conditions doivent être réunies pour un reste à charge nul : disposer d'une complémentaire santé dite « responsable » — c'est le cas de la très grande majorité des contrats, y compris les contrats d'entreprise — et choisir un équipement classé dans le panier concerné. Sans complémentaire, l'Assurance Maladie seule ne couvre qu'une petite partie de la dépense.</p>

<h2>Combien coûtent des lunettes en 100 % Santé ?</h2>
<p>L'optique est découpée en deux classes. La classe A correspond au 100 % Santé : les prix y sont plafonnés par la réglementation et aucun dépassement n'est possible. La classe B rassemble tout le reste, avec des prix libres.</p>

<h3>Ce que couvre la classe A</h3>
<p>La monture de classe A est plafonnée à 30&nbsp;€. Les verres, eux, suivent une grille de prix maximaux fixée par arrêté, qui varie selon la complexité de la correction : un unifocal simple se situe en bas de la grille, un progressif pour forte correction en haut. Ces verres intègrent obligatoirement l'amincissement adapté à la correction, un traitement antireflet et un traitement anti-rayure. Autrement dit, un équipement de classe A n'est pas un équipement au rabais sur le plan technique : c'est un catalogue de montures plus restreint et des options esthétiques limitées, pas des verres de moindre qualité optique.</p>

<h3>Ce que change la classe B</h3>
<p>En classe B, le prix est libre. Les contrats responsables remboursent la monture à hauteur de 100&nbsp;€ maximum — un plafond relevé de 100&nbsp;€ à ce niveau par la réglementation en vigueur — et les verres selon les garanties de votre contrat. C'est là que le reste à charge apparaît, et qu'il varie énormément d'une mutuelle à l'autre. Rien n'interdit non plus de panacher : une monture de classe B avec des verres de classe A, par exemple, est parfaitement possible.</p>

<h2>Et pour les aides auditives, quels sont les montants ?</h2>
<p>Le principe est le même, avec une classe I (100 % Santé) et une classe II à prix libres. Voici les repères officiels à connaître avant de comparer deux devis.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Situation</th><th>Prix de vente maximal en classe I</th><th>Base de remboursement Assurance Maladie</th></tr>
    </thead>
    <tbody>
      <tr><td>Adulte de 20 ans et plus</td><td>950&nbsp;€ par oreille</td><td>400&nbsp;€ remboursés à 60&nbsp;%, soit 240&nbsp;€</td></tr>
      <tr><td>Moins de 20 ans, ou cécité</td><td>1&nbsp;400&nbsp;€ par oreille</td><td>1&nbsp;400&nbsp;€ remboursés à 60&nbsp;%, soit 840&nbsp;€</td></tr>
      <tr><td>Bénéficiaire de la C2S, 20 ans et plus</td><td>800&nbsp;€ par oreille</td><td>Prise en charge intégrale</td></tr>
      <tr><td>Bénéficiaire de la C2S, moins de 20 ans</td><td>1&nbsp;400&nbsp;€ par oreille</td><td>Prise en charge intégrale</td></tr>
      <tr><td>Classe II</td><td>Prix libre</td><td>Même base, mais remboursement complémentaire plafonné à 1&nbsp;700&nbsp;€ par aide en contrat responsable</td></tr>
    </tbody>
  </table>
</div>
<p>En classe I, c'est votre complémentaire qui comble l'écart entre le remboursement de l'Assurance Maladie et le prix de vente, d'où le reste à charge nul. En classe II, ce qui reste à payer dépend entièrement de vos garanties : c'est le seul point sur lequel nous vous demandons systématiquement votre tableau de garanties avant de chiffrer quoi que ce soit.</p>
<p>Quelle que soit la classe choisie, la réglementation impose un socle de prestations : une période d'essai d'au moins 30 jours avant l'achat définitif, une garantie de 4 ans minimum, et un suivi comprenant au moins trois séances de réglage la première année puis deux par an ensuite. Ce suivi est inclus dans le prix affiché — il n'est jamais facturé en plus.</p>

<h2>Tous les combien peut-on renouveler son équipement ?</h2>
<ol>
  <li><strong>Lunettes, à partir de 16 ans :</strong> une prise en charge tous les 2 ans.</li>
  <li><strong>Enfants de 6 à 16 ans :</strong> tous les ans.</li>
  <li><strong>Enfants de moins de 6 ans :</strong> tous les ans, ramené à 6 mois en cas de mauvaise adaptation ou d'évolution de la correction.</li>
  <li><strong>Aides auditives :</strong> tous les 4 ans, par oreille.</li>
  <li><strong>Renouvellement anticipé :</strong> toujours possible en optique en cas d'évolution de la vue justifiée par une nouvelle ordonnance, ou de pathologie évolutive (glaucome, DMLA, diabète, cataracte opérée…).</li>
</ol>

<h2>Ce « bonus de 42 € » dont on entend parler, c'est quoi ?</h2>
<p>Un supplément de 42&nbsp;€ a fait beaucoup parler en 2026, et il est très souvent mal compris. Ce n'est pas une aide versée aux patients, ni une réduction sur vos lunettes : c'est un supplément d'accompagnement versé aux opticiens, réservé à ceux dont la part d'équipements complets de classe A a dépassé un seuil sur une période de référence, et applicable seulement sur une fenêtre limitée de l'année. Si vous lisez quelque part que vous avez droit à 42&nbsp;€ supplémentaires sur votre équipement, l'information est inexacte. Nous préférons le dire clairement plutôt que de laisser s'installer une attente que la réglementation ne prévoit pas.</p>

<h2>Comment vérifier ce qui restera vraiment à votre charge ?</h2>
<p>Le devis normalisé est le seul document qui répond à cette question sans ambiguïté. Obligatoire depuis le 1<sup>er</sup> janvier 2020 en optique comme en audiologie, il suit un format identique chez tous les professionnels, ce qui le rend directement comparable d'une boutique à l'autre. Il doit obligatoirement mentionner une offre 100 % Santé, même si vous vous orientez vers autre chose, et détailler ligne par ligne le prix, la base de remboursement et le montant estimé à votre charge.</p>
<p>En boutique, nous établissons ce devis systématiquement et sans engagement. Nous interrogeons votre complémentaire quand elle le permet, ce qui donne le reste à charge réel et non une estimation, et nous appliquons le tiers payant chaque fois que le contrat l'autorise : vous ne réglez alors que votre part, sans avance de frais. Beaucoup de nos clients des Olympiades et du quartier de la place d'Italie viennent d'ailleurs simplement pour faire établir un devis et le comparer tranquillement chez eux — c'est une démarche parfaitement normale, et nous la trouvons saine.</p>
<p>Dernier point qui évite bien des déconvenues : les montants et les plafonds évoqués ici sont ceux de la réglementation nationale, mais les garanties des complémentaires, elles, varient d'un contrat à l'autre. Avant tout achat, un appel à votre mutuelle ou un coup d'œil à votre tableau de garanties reste le meilleur réflexe.</p>
"""

ART_BODY_VIE_BOUTIQUE = """
<h2>Comment Sudaya et Mikhael se sont-ils rencontrés ?</h2>
<p>L'histoire de Maison Mikis ne commence pas à l'ouverture de la boutique, mais plusieurs années plus tôt, à Montreuil. Mikhael y dirigeait alors un magasin d'optique. Sudaya l'y rejoint comme directeur de boutique et prend en charge le quotidien : l'accueil, le conseil au comptoir, l'organisation de l'équipe. Rien, à ce moment-là, ne ressemblait à un projet commun. C'était simplement deux personnes qui apprenaient à travailler ensemble, jour après jour, dans un métier où l'on passe beaucoup de temps côte à côte.</p>

<h3>Deux ans à se comprendre sans se le dire</h3>
<p>Deux années de collaboration, dans un commerce de proximité, cela représente des milliers de clients accueillis, des dizaines de situations délicates à démêler et une manière de faire qui finit par se partager. C'est là que l'envie a pris forme. Non pas dans une conversation décisive, mais dans l'accumulation de petites convergences : la même façon de considérer qu'un client mal conseillé revient toujours, la même réticence à expédier un essayage, la même idée de ce que devait être une boutique où l'on se sent attendu. À force, l'idée d'ouvrir ensemble une enseigne à eux est devenue moins une ambition qu'une suite logique.</p>

<h2>Pourquoi avoir choisi les Olympiades plutôt qu'ailleurs ?</h2>
<p>Le choix de l'emplacement n'a rien d'un calcul de zone de chalandise. Sudaya a grandi dans le Triangle de Choisy. Il en connaît les rues, les commerces, les habitudes, les gens qui y vivent depuis longtemps et ceux qui viennent d'y arriver. Quand on ouvre son premier commerce, savoir d'avance à qui l'on va ouvrir la porte change beaucoup de choses : on ne s'installe pas dans un marché, on s'installe dans un quartier que l'on comprend déjà.</p>

<h3>Un secteur façonné par son histoire</h3>
<p>Le Triangle de Choisy et les Olympiades ne ressemblent à aucun autre coin de Paris. La fin des années 1970 y a vu l'arrivée de dizaines de milliers de familles réfugiées d'Asie du Sud-Est, qui se sont installées au pied des tours et ont peu à peu donné à ces rues leur physionomie actuelle. Ce passé se lit encore partout : dans les enseignes, dans les langues qu'on entend d'une table à l'autre, dans la manière dont plusieurs générations cohabitent sur quelques centaines de mètres. On ne s'installe pas ici comme on s'installerait ailleurs, et c'est précisément ce qui plaisait aux deux associés.</p>

<h3>La découverte, à deux</h3>
<p>Pendant leurs deux années de travail commun, Sudaya a fait découvrir cet endroit à Mikhael. Une adresse, une anecdote, un plat à goûter plutôt qu'un autre. Ce quartier, Mikhael ne l'a donc pas choisi sur une carte : il l'a d'abord fréquenté, avant de s'y attacher. Quand est venu le moment de décider où poser leur propre enseigne, l'esplanade des Olympiades ne s'est pas discutée longtemps.</p>

<h2>Qu'est-ce qu'un opticien indépendant change au quotidien ?</h2>
<p>La différence ne se voit pas en vitrine. Elle se joue sur des choix que personne d'autre ne vient arbitrer à notre place, et qui finissent par se sentir au comptoir.</p>
<ol>
  <li><strong>La sélection des marques est la nôtre.</strong> Aucune centrale ne nous impose de référence à écouler, ce qui nous laisse libres de proposer ce qui convient réellement à un visage, pas ce qu'il faudrait vendre ce mois-ci.</li>
  <li><strong>Le temps passé avec chacun n'est pas minuté.</strong> Un essayage compliqué peut durer, un ajustage de trois minutes reste gratuit. Personne ne nous demande de compte sur ce point.</li>
  <li><strong>Nous assumons de déconseiller.</strong> Il nous arrive de dire qu'une monture ne va pas, ou qu'un équipement peut attendre. C'est plus facile quand on ne rend de comptes qu'à soi-même.</li>
  <li><strong>Nous connaissons nos clients dans la durée.</strong> Les mêmes visages reviennent d'une année sur l'autre, souvent avec leurs enfants ou leurs parents, et cette continuité vaut tous les fichiers clients.</li>
</ol>

<h2>Que veut dire « prendre le temps qu'il faut » ?</h2>
<p>Maison Mikis a ouvert ses portes en 2023, pensée dès le départ pour des personnes en quête de qualité, de style et d'une attention sincère. Cela suppose de renoncer à quelques réflexes du métier : le conseil expédié entre deux clients, la vitrine impersonnelle, la question de budget posée avant même d'avoir compris le besoin. Concrètement, cela veut dire commencer par écouter, expliquer ce qui se joue derrière une correction ou un appareillage, et laisser repartir sans acheter quelqu'un qui préfère réfléchir.</p>
<p>Cette manière de faire vaut pour la vue comme pour l'audition. Un accompagnement auditif s'inscrit dans le temps long, avec des essais, des réglages et des rendez-vous de suivi : rien de tout cela ne fonctionne si la relation se limite à une transaction. Quand un sujet dépasse notre champ — une gêne inhabituelle, une baisse brutale, un doute médical — nous le disons et nous orientons vers un ophtalmologiste, un ORL ou le médecin traitant. Savoir où s'arrête notre rôle fait partie du métier.</p>

<h2>Où nous trouver et comment nous rencontrer ?</h2>
<p>Nous sommes installés Galerie Oslo, sur l'esplanade des Olympiades, dans le 13e arrondissement. On peut pousser la porte pour un contrôle de la vue, pour parler d'une gêne auditive, pour faire resserrer une branche ou simplement pour essayer sans intention d'achat. Aucune de ces visites n'est moins légitime qu'une autre, et nous accueillons chaque personne comme un voisin, avec le temps qu'il faut. L'histoire complète de la boutique et du quartier est racontée plus longuement sur notre page <a href="/notre-histoire.html">Notre histoire</a>.</p>
"""

ART_BODY_ENFANT = """
<h2>Pourquoi un enfant ne dit-il jamais qu'il voit ou entend mal ?</h2>
<p>C'est la première chose que nous expliquons aux parents inquiets : un enfant n'a aucun point de comparaison. Il ne sait pas que le tableau de la classe devrait être net, ni que les voix devraient se détacher du bruit de la cantine. Il compose donc avec ce qu'il perçoit, sans jamais se plaindre, et il le fait si bien que la gêne passe souvent inaperçue pendant des mois. Ce n'est pas un défaut de vigilance de votre part : c'est simplement la façon dont un cerveau en construction s'adapte.</p>
<p>Conséquence pratique : ce sont les comportements, et non les mots de l'enfant, qui donnent l'alerte. Un signe isolé et passager ne veut généralement rien dire. C'est la répétition dans le temps, ou l'association de plusieurs signes, qui mérite d'en parler à un professionnel. L'immense majorité des situations que nous rencontrons se règlent avec une paire de lunettes ou une simple surveillance.</p>

<h2>Quels comportements doivent attirer l'attention côté vue ?</h2>
<h3>Chez le nourrisson et le tout-petit</h3>
<p>Avant l'âge de la parole, on observe surtout la façon dont le regard accroche le monde. Un bébé qui ne suit pas des yeux un visage penché sur lui, qui ne cherche pas un objet coloré déplacé lentement devant lui, ou qui semble indifférent à la lumière, mérite d'être signalé au médecin lors de la visite suivante. Un strabisme, ce que les familles appellent le fait de loucher, est fréquent et souvent intermittent dans les tout premiers mois ; en revanche, un strabisme permanent avant quatre mois justifie un avis rapide, sans attendre le rendez-vous prévu.</p>
<h3>À partir de l'école maternelle</h3>
<p>Plus tard, la gêne se lit dans les gestes du quotidien. Voici les observations que les parents nous rapportent le plus souvent, et qui méritent d'être mentionnées au médecin.</p>
<ul class="check-list">
  <li><span class="check">✓</span> Il plisse les yeux ou fronce le visage pour regarder au loin</li>
  <li><span class="check">✓</span> Il colle son livre au visage ou se rapproche beaucoup de l'écran</li>
  <li><span class="check">✓</span> Il incline ou tourne la tête toujours du même côté pour fixer quelque chose</li>
  <li><span class="check">✓</span> Il ferme un œil au soleil, se frotte les yeux plus que les autres</li>
  <li><span class="check">✓</span> Il bute dans les objets, hésite dans les escaliers, paraît maladroit</li>
  <li><span class="check">✓</span> Il peine à copier le tableau, se fatigue vite sur les devoirs</li>
</ul>

<h2>Et du côté de l'oreille, qu'est-ce qui doit interpeller ?</h2>
<p>Les signes touchant l'audition sont plus discrets encore, car un enfant qui entend mal compense énormément par le regard, le contexte et l'imitation. Chez le bébé, on s'inquiète d'une absence de réaction aux bruits soudains ou aux voix familières. Chez l'enfant plus grand, le motif le plus fréquent reste le langage : un vocabulaire qui stagne, une articulation qui ne se corrige pas, des mots systématiquement déformés. On observe aussi un enfant qui fait répéter, qui monte le son, qui semble ailleurs quand on l'appelle de dos, ou qui décroche à l'école alors qu'il suit très bien à la maison, dans le calme.</p>
<p>Attention toutefois à ne pas surinterpréter : une baisse temporaire liée à un rhume ou à une otite est banale et réversible. Ce qui compte, là encore, c'est la durée. Un doute qui persiste au-delà de quelques semaines se discute avec le médecin traitant, qui orientera si besoin vers un ORL.</p>

<h2>Comment s'organise le dépistage en France ?</h2>
<p>Les familles ne sont pas seules : un calendrier de rendez-vous systématiques existe, inscrit dans le carnet de santé. Il ne repose ni sur l'opticien ni sur l'audioprothésiste, mais sur la maternité, le médecin traitant, la PMI et la médecine scolaire.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Âge</th><th>Ce qui est prévu</th><th>Par qui</th></tr>
    </thead>
    <tbody>
      <tr><td>Naissance</td><td>Test auditif à la maternité, obligatoire depuis 2012, et premier examen des yeux</td><td>Maternité</td></tr>
      <tr><td>4 et 9 mois</td><td>Contrôle de l'audition et de la vision</td><td>Médecin traitant ou PMI</td></tr>
      <tr><td>24 mois</td><td>Contrôle auditif, suivi du langage</td><td>Médecin traitant ou PMI</td></tr>
      <tr><td>2 à 4 ans et demi</td><td>Examens visuels répétés, puis contrôle en petite section</td><td>PMI, médecine scolaire</td></tr>
      <tr><td>5 ans, grande section ou CP</td><td>Bilan avant l'apprentissage de la lecture</td><td>Médecine scolaire</td></tr>
      <tr><td>Vers 12 ans</td><td>Dernière visite systématique de l'enfance</td><td>Médecine scolaire</td></tr>
    </tbody>
  </table>
</div>
<p>Ce maillage repère la grande majorité des troubles avant qu'ils ne pèsent sur les apprentissages. Mais entre deux rendez-vous, il peut s'écouler plusieurs années, et c'est justement là que l'observation des parents prend le relais du dépistage organisé.</p>

<h2>Que faire quand un doute apparaît entre deux rendez-vous ?</h2>
<ol>
  <li><strong>Notez ce que vous observez</strong>, avec des exemples et des dates. Trois lignes sur un carnet valent mieux qu'un souvenir approximatif au moment de la consultation.</li>
  <li><strong>Testez simplement à la maison</strong>, sans dramatiser : appelez votre enfant hors de son champ de vision, demandez-lui de nommer un objet éloigné, observez s'il ferme un œil.</li>
  <li><strong>Parlez-en à l'école.</strong> L'enseignant voit votre enfant plusieurs heures par jour dans des conditions que vous ne connaissez pas et repère souvent des choses utiles.</li>
  <li><strong>Prenez rendez-vous chez le médecin traitant</strong>, qui décidera d'une orientation vers l'ophtalmologiste ou l'ORL. C'est lui le point d'entrée, y compris pour l'audition.</li>
  <li><strong>N'attendez pas la prochaine visite scolaire</strong> si le signe est net et durable : les délais de rendez-vous étant parfois longs, mieux vaut lancer la démarche tôt et l'annuler ensuite que l'inverse.</li>
</ol>

<h2>Peut-on venir en parler en boutique avant de consulter ?</h2>
<p>Oui, et beaucoup de familles du quartier des Olympiades le font. Soyons clairs sur notre rôle : nous ne posons aucun diagnostic, et nous ne remplaçons ni l'ophtalmologiste ni l'ORL. Ce que nous pouvons faire, c'est vous écouter, réaliser un premier contrôle de la vue quand l'âge de l'enfant le permet, vous dire si ce que vous décrivez ressemble à quelque chose de courant, et vous orienter vers le bon interlocuteur sans vous faire perdre de temps.</p>
<p>Si une correction est prescrite, nous prenons le temps qu'il faut avec l'enfant lui-même : expliquer chaque étape, laisser essayer, choisir une monture qu'il a envie de porter. Une paire adoptée est une paire portée, et c'est finalement tout ce qui compte. Nous sommes Galerie Oslo, sur l'Esplanade des Olympiades, et une question posée au comptoir n'engage évidemment à rien.</p>
"""

ART_BODY_VARILUX = """<h2>À quoi sert un verre progressif pensé pour l'intérieur ?</h2>
<p>Nos habitudes visuelles ont changé plus vite que nos équipements. Entre le travail sur ordinateur, les messages sur téléphone, la lecture et les réunions, une grande partie de la journée se joue désormais dans un rayon de quelques mètres, à l'intérieur, et non sur l'horizon. Un verre polyvalent classique consacre pourtant une large part de sa surface à la vision de loin, celle dont on se sert le moins entre neuf heures et dix-huit heures. C'est ce déséquilibre qu'Essilor a voulu corriger avec Varilux Immersia, commercialisé depuis le 14 avril 2026, en déplaçant le centre de gravité du verre vers les distances proches et intermédiaires.</p>
<p>Les chiffres avancés par le fabricant pour justifier ce choix sont parlants : selon Essilor, 72 % du temps visuel d'une personne presbyte se joue aujourd'hui en vision de près et intermédiaire, 77 % des 40-65 ans déclarent mener plusieurs tâches de front entre smartphone et ordinateur, et 80 % d'entre eux ressentent une fatigue visuelle en fin de journée standard. Ces données viennent de la marque et servent son argumentaire, il faut le garder en tête. Elles correspondent néanmoins assez bien à ce que nous entendons au comptoir.</p>

<h2>Varilux Immersia Mid ou Room : quelle version pour quel usage ?</h2>
<p>C'est la question la plus utile, et celle que l'on nous pose le plus souvent depuis le lancement. Le verre existe en deux dessins, qui ne se distinguent pas par un niveau de gamme mais par la distance jusqu'à laquelle ils restent confortables. Le bon choix se fait en décrivant une journée type, pas en comparant deux fiches techniques.</p>

<h3>Varilux Immersia Mid : jusqu'à 1,5 mètre</h3>
<p>La version Mid couvre le rayon d'un bureau : l'écran, le clavier, un document papier posé à côté, le téléphone. Essilor la destine à la lecture, aux loisirs minutieux et aux environnements multi-écrans. C'est le profil de quelqu'un dont la journée se passe assis à un poste fixe, avec une ou deux dalles devant soi et peu de déplacements. En contrepartie de ce champ élargi sur les courtes distances, tout ce qui dépasse un mètre cinquante devient franchement flou.</p>

<h3>Varilux Immersia Room : jusqu'à 3 mètres</h3>
<p>La version Room étend la zone nette à l'échelle d'une pièce. Elle vise, toujours selon Essilor, les porteurs qui passent d'une activité à l'autre dans un même espace et qui ont besoin de voir les visages en face d'eux : réunion autour d'une table, consultation, enseignement, accueil. On gagne en liberté de mouvement à l'intérieur, on perd un peu de largeur sur la vision de près par rapport à la version Mid.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th></th><th>Varilux Immersia Mid</th><th>Varilux Immersia Room</th></tr>
    </thead>
    <tbody>
      <tr><td>Distance nette annoncée</td><td>Jusqu'à environ 1,5 m</td><td>Jusqu'à environ 3 m</td></tr>
      <tr><td>Usage visé</td><td>Lecture, travaux minutieux, plusieurs écrans</td><td>Se déplacer et interagir dans une pièce</td></tr>
      <tr><td>Profil type</td><td>Poste de travail fixe, journée assise</td><td>Réunions, consultations, enseignement, accueil</td></tr>
      <tr><td>Vision de loin</td><td>Aucune au-delà de 1,5 m</td><td>Aucune au-delà de 3 m</td></tr>
      <tr><td>Conduite et extérieur</td><td>Exclue</td><td>Exclue</td></tr>
    </tbody>
  </table>
</div>
<p>Dans les deux cas, la conclusion est la même : ce verre ne sort pas de l'immeuble. C'est un outil de travail, pas une paire de tous les jours.</p>

<h2>En quoi ce verre diffère-t-il d'un progressif polyvalent ?</h2>
<p>La différence tient moins à une prouesse technique qu'à une répartition. Les verres progressifs classiques cherchent un compromis entre trois zones : loin, intermédiaire et près. Ici, la zone de loin est volontairement réduite au profit d'un champ élargi sur les distances de la vie intérieure. Le porteur gagne en confort là où il passe ses journées, et accepte une vision de loin moins généreuse.</p>
<p>L'argument le plus concret n'est d'ailleurs pas optique mais postural. Avec un progressif polyvalent, la zone qui permet de voir l'écran net se situe assez bas dans le verre. Quand le poste de travail ne peut pas être réglé — écran trop haut, siège non ajustable, bureau partagé — beaucoup de porteurs compensent en relevant le menton plutôt qu'en baissant les yeux, des centaines de fois par jour. C'est ce réflexe, et la tension de nuque qui l'accompagne en fin de journée, qu'un verre d'intérieur cherche à supprimer en remontant la zone utile.</p>

<h3>Les technologies mises en avant par Essilor</h3>
<p>Deux noms reviennent dans la communication du fabricant. <strong>AI Twinning</strong> désigne un modèle prédictif du porteur : plutôt qu'un dessin unique appliqué à tout le monde, la géométrie du verre est ajustée à partir d'une simulation du comportement visuel réel. <strong>Wave 2.0</strong> vise la netteté et la perception des contrastes, en réduisant les aberrations optiques pour stabiliser l'image quand la luminosité change — entre un éclairage de bureau et un écran, typiquement.</p>
<p>Ces deux éléments décrivent une intention de conception présentée par la marque. Ils ne constituent pas, à ce stade, un résultat validé par une évaluation indépendante, et nous préférons le dire plutôt que de les reprendre tels quels.</p>
<ul class="check-list">
<li><span class="check">✓</span> Deux versions distinctes : Immersia Mid jusqu'à 1,5 m, Immersia Room jusqu'à 3 m</li>
<li><span class="check">✓</span> Géométrie personnalisée par modélisation prédictive (AI Twinning)</li>
<li><span class="check">✓</span> Netteté et contrastes travaillés par la technologie Wave 2.0</li>
<li><span class="check">✓</span> Objectif affiché : limiter l'inclinaison de la tête devant un écran</li>
</ul>
<p>Une limite doit rester en tête, et elle vaut pour les deux versions : il n'y a pas de vision de loin dans ce verre. Ni conduite, ni marche en extérieur, ni cinéma.</p>

<h2>Faut-il remplacer ses lunettes actuelles par ce verre ?</h2>
<p>Non, et c'est le point sur lequel nous insistons le plus. Un verre dédié à l'intérieur ne remplace pas une paire polyvalente : il la complète. Avec une vision de loin réduite, il n'est adapté ni à la conduite, ni à la marche en extérieur, ni à une salle de spectacle. Le présenter comme une paire unique serait une erreur, et le proposer systématiquement à tout porteur relèverait d'une montée en gamme que nous ne trouvons pas honnête.</p>
<p>La bonne question n'est donc pas « est-ce meilleur ? » mais « combien d'heures par jour ce verre servirait-il ? ». Sous deux ou trois heures d'écran quotidiennes, une paire polyvalente bien centrée suffit généralement. Au-delà, et surtout si la gêne se manifeste en fin de journée sous forme de nuque tendue ou de vision qui se trouble, une seconde paire dédiée prend du sens. Il faut aussi savoir qu'une seconde paire représente une dépense réelle, souvent mal couverte par les complémentaires : mieux vaut le vérifier avant de la commander.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Votre situation</th><th>Ce qui se discute le plus souvent</th><th>Point de vigilance</th></tr>
    </thead>
    <tbody>
      <tr><td>Écran occasionnel, vie surtout en extérieur</td><td>Une paire polyvalente bien ajustée</td><td>Vérifier d'abord le centrage et l'ordonnance</td></tr>
      <tr><td>Bureau fixe, lecture, plusieurs écrans</td><td>Plutôt la version Immersia Mid</td><td>Inadaptée à la conduite et à la marche</td></tr>
      <tr><td>Déplacements fréquents dans une pièce</td><td>Plutôt la version Immersia Room</td><td>La vision de loin reste limitée</td></tr>
      <tr><td>Fatigue de fin de journée sans baisse de vue</td><td>Bilan visuel, puis réglage du poste de travail</td><td>Un verre ne remplace pas les pauses</td></tr>
      <tr><td>Budget contraint</td><td>Prioriser la paire principale</td><td>Interroger sa complémentaire avant toute seconde paire</td></tr>
    </tbody>
  </table>
</div>

<h2>Comment savoir si vous êtes concerné ?</h2>
<p>Ce type d'équipement s'adresse à un profil assez précis. Voici la démarche que nous suivons avant d'en parler.</p>
<ol>
  <li><strong>Vérifier que la correction est à jour.</strong> Une bonne partie des fatigues attribuées aux écrans vient d'une ordonnance ancienne.</li>
  <li><strong>Mesurer vos distances réelles</strong> : hauteur d'écran, éloignement du clavier, position du document papier. Un mètre ruban en dit plus long qu'un catalogue — et c'est précisément cette mesure qui départage la version Mid de la version Room.</li>
  <li><strong>Décrire précisément la gêne</strong> : moment de la journée, posture adoptée, tâche en cours. Une nuque douloureuse oriente différemment d'une vision qui se brouille.</li>
  <li><strong>Corriger d'abord l'environnement</strong> : hauteur du siège, éclairage, reflets sur la dalle, pauses régulières.</li>
  <li><strong>N'envisager une paire dédiée qu'ensuite</strong>, et sur devis, en comparant avec l'option d'un simple verre à faible dégression.</li>
</ol>

<h2>Où faire le point sur vos distances de travail ?</h2>
<p>Un verre progressif dédié à l'intérieur ne se choisit pas sur une brochure : il se choisit en décrivant une journée type. Nous prenons ces mesures en boutique, Galerie Oslo sur l'Esplanade des Olympiades, et il n'est pas rare que la conclusion soit qu'une paire supplémentaire n'est pas nécessaire. Beaucoup de porteurs travaillant dans les tours voisines repartent simplement avec un réglage de monture, une correction ajustée et quelques conseils d'ergonomie.</p>
<p>Un dernier repère : si la fatigue s'accompagne d'une douleur oculaire véritable, d'une vision double ou d'une baisse de vue rapide, ce n'est plus une question d'équipement. Ces signes relèvent d'un avis médical sans délai, et la prescription reste dans tous les cas du ressort de l'ophtalmologiste. Notre rôle s'arrête à l'adaptation, au montage et au suivi du confort dans la durée.</p>
"""

ART_BODY_NOVACEL_CELENE = """<h2>Qu'est-ce que Célène, le traitement de Novacel ?</h2>
<p>Pendant longtemps, la qualité d'un traitement anti-reflet s'est mesurée à sa discrétion : plus il se faisait oublier, mieux c'était. Novacel, verrier français connu pour son savoir-faire dans les traitements de surface, propose une lecture différente avec Célène. Le principe technique reste celui d'un traitement complet, mais la teinte du reflet résiduel a été travaillée pour tirer vers un nude légèrement rosé, au lieu du vert ou du bleu que l'on croise habituellement sur les verres. Autrement dit, ce qui était considéré comme un résidu inévitable devient ici un choix assumé.</p>
<p>Il ne s'agit pas d'un verre teinté, ni d'une fantaisie : de face, la personne en face de vous ne voit pas une couleur, elle perçoit un reflet un peu plus chaud quand la lumière accroche le verre. La différence est réelle mais discrète, et c'est précisément l'intention du fabricant.</p>

<h2>Pourquoi un traitement anti-reflet a-t-il toujours une couleur ?</h2>
<p>La question revient souvent au comptoir, et la réponse tient à la physique du traitement lui-même. Comprendre ce mécanisme aide à ne pas confondre un défaut avec un parti pris.</p>

<h3>D'où vient le reflet résiduel</h3>
<p>Un traitement antireflet est un empilement de couches très minces déposées sous vide sur les deux faces du verre. Chacune est calculée pour que les ondes lumineuses réfléchies s'annulent entre elles. Cette annulation ne peut jamais être parfaite sur l'ensemble du spectre visible : il subsiste toujours une petite quantité de lumière renvoyée, et sa couleur dépend de l'épaisseur et de la nature des couches empilées. C'est cette couleur que vous apercevez quand vous inclinez vos lunettes vers une lampe. Elle ne dit rien, à elle seule, de la performance du traitement.</p>

<h3>Le parti pris de la teinte nude</h3>
<p>Novacel a choisi d'orienter ce résidu vers une tonalité chaude et neutre, présentée comme capable de s'harmoniser aussi bien avec des carnations claires qu'avec des peaux plus mates. Le fabricant décrit un verre qui accompagne le regard sans s'imposer, un peu à la manière d'un maquillage discret. Cette formulation appartient à la marque et relève d'une intention esthétique, pas d'une performance mesurable. Elle répond toutefois à une demande que nous entendons réellement, en particulier chez des porteuses lassées des reflets froids qui bleuissent le regard sur les photos.</p>

<h2>Que fait un traitement de surface, au-delà de l'esthétique ?</h2>
<p>La dimension décorative ne dispense pas des fonctions attendues d'un bon traitement. Célène reste avant tout un anti-reflet complet, conçu pour durer et pour simplifier l'entretien quotidien.</p>
<ul class="check-list">
<li><span class="check">✓</span> Traitement durci, pour mieux résister aux micro-rayures du quotidien</li>
<li><span class="check">✓</span> Surface hydrofuge et oléofuge, qui limite les traces de doigts et l'adhérence de l'eau</li>
<li><span class="check">✓</span> Propriété antistatique, pour accrocher moins de poussière</li>
<li><span class="check">✓</span> Protection contre les rayons ultraviolets intégrée au traitement</li>
</ul>
<p>Ces quatre fonctions ne se voient pas sur un présentoir, mais ce sont elles qui décident de l'état de vos verres au bout de deux ans. Le tableau ci-dessous résume ce que chacune change concrètement, et ce qu'elle ne fait pas.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Fonction</th><th>Ce que vous remarquez au quotidien</th><th>Ce qu'elle ne remplace pas</th></tr>
    </thead>
    <tbody>
      <tr><td>Couches antireflets</td><td>Moins de halos la nuit, regard plus visible sur les photos</td><td>Un bon éclairage et une correction à jour</td></tr>
      <tr><td>Durcissement</td><td>Verres moins vite voilés de micro-rayures</td><td>Un étui rigide et des gestes de nettoyage corrects</td></tr>
      <tr><td>Hydrofuge et oléofuge</td><td>Traces de doigts qui partent d'un coup de microfibre</td><td>Un nettoyage régulier à l'eau tiède</td></tr>
      <tr><td>Antistatique</td><td>Moins de poussière rappelée juste après le nettoyage</td><td>Le rinçage, indispensable avant d'essuyer</td></tr>
      <tr><td>Filtre ultraviolet</td><td>Protection complémentaire en extérieur</td><td>Une vraie paire solaire quand la luminosité est forte</td></tr>
    </tbody>
  </table>
</div>
<p>Le traitement est proposé sur l'ensemble de la gamme du verrier, quel que soit l'indice choisi. Il peut donc être associé aussi bien à une correction légère qu'à une correction plus forte nécessitant un verre aminci, ce qui évite d'avoir à arbitrer entre esthétique du reflet et épaisseur du verre.</p>

<h2>Faut-il choisir ses verres pour la couleur de leurs reflets ?</h2>
<p>Non, et nous le disons volontiers aux clients qui posent la question. La hiérarchie reste la même : une correction juste, un verre bien centré, un traitement durable, puis seulement la teinte du reflet. Un anti-reflet dont la couleur vous plaît mais qui se raye en six mois ne vous rendra pas service. Inversement, si deux traitements se valent sur le plan technique et que l'un s'accorde mieux avec votre visage et votre monture, il n'y a aucune raison de s'en priver.</p>
<p>Ce type de produit illustre surtout une tendance de fond : les verres cessent d'être perçus comme un simple dispositif médical pour devenir un élément de style à part entière. C'est une évolution plutôt saine, à condition qu'elle ne serve pas de prétexte à faire monter systématiquement le devis. Un traitement esthétique ne se justifie que si le reste de l'équipement est déjà cohérent avec vos besoins visuels.</p>

<h2>Comment juger le rendu sur votre propre monture ?</h2>
<p>Aucune photo de catalogue ne remplace un essai à la lumière du jour, sur votre visage. Voici comment nous procédons quand un porteur hésite entre deux traitements.</p>
<ol>
  <li><strong>Regardez les verres de face, puis de trois quarts</strong>, à la lumière naturelle : c'est de trois quarts que le reflet se voit le plus.</li>
  <li><strong>Comparez avec la monture retenue</strong>, car une monture dorée, écaille ou noire ne renvoie pas du tout la même ambiance de couleur.</li>
  <li><strong>Faites-vous prendre en photo</strong> avec et sans flash : c'est là que la différence de tonalité apparaît le plus nettement.</li>
  <li><strong>Vérifiez ensuite le reste du devis</strong> : indice, amincissement, garantie du traitement, avant de trancher sur la teinte.</li>
</ol>
<p>Nous présentons ces différences en boutique, Galerie Oslo sur l'Esplanade des Olympiades, avec des verres de démonstration que l'on peut manipuler et incliner sous plusieurs éclairages. C'est cinq minutes qui évitent une déception à la livraison, et cela ne vous engage à rien. Si vous portez déjà des lunettes, apportez-les : la comparaison avec vos verres actuels est souvent la plus parlante.</p>
"""

ART_BODY_ALCON_PRECISION7 = """<h2>Qu'est-ce qu'une lentille à renouvellement hebdomadaire ?</h2>
<p>Depuis des années, les porteurs de lentilles souples se répartissaient entre deux rythmes seulement. D'un côté la journalière, sortie neuve de son blister le matin et jetée le soir. De l'autre la mensuelle, réutilisée pendant plusieurs semaines et nettoyée chaque jour. Alcon a introduit une troisième possibilité avec Precision7, présentée comme la première lentille conçue pour être renouvelée chaque semaine. Le raisonnement est simple : proposer une lentille neuve tous les sept jours à ceux qui trouvent la journalière trop coûteuse au quotidien, sans les obliger à garder la même lentille un mois entier.</p>

<h3>Un rythme intermédiaire, pas une catégorie miracle</h3>
<p>Il faut se garder de présenter cette nouveauté comme supérieure aux autres. Une lentille hebdomadaire ne corrige pas mieux, ne voit pas plus loin et ne dispense d'aucune précaution. Elle déplace simplement le curseur entre deux contraintes bien connues : le budget d'un côté, la fréquence de remplacement de l'autre. Pour certains porteurs, ce compromis tombe juste. Pour d'autres, la journalière restera plus adaptée, en particulier en cas de terrain allergique ou de port très occasionnel, où la simplicité prime sur tout le reste.</p>

<h2>Que promet la technologie ACTIV-FLO ?</h2>
<p>Le principal défi d'une lentille portée une semaine entière est de ne pas voir son confort s'effondrer au bout de trois ou quatre jours. Pour y répondre, Alcon a développé un système baptisé ACTIV-FLO. Selon le fabricant, la lentille associe un agent hydratant intégré directement à la matière et un second agent qui continue de libérer de l'humidité tout au long de la semaine, avec un objectif affiché de seize heures de confort par jour. Le matériau est un silicone-hydrogel contenant environ 55&nbsp;% d'eau, une composition proche de celle des journalières récentes.</p>
<p>Ces éléments sont des revendications de marque, et nous préférons le dire clairement plutôt que de les présenter comme des faits établis. Le confort d'une lentille dépend aussi de votre film lacrymal, de votre environnement de travail, du temps passé devant un écran ou de la climatisation de votre bureau. Deux porteurs équipés de la même référence peuvent avoir des ressentis très différents en fin de semaine : c'est précisément ce que l'essai sert à vérifier.</p>

<h2>Une lentille hebdomadaire demande-t-elle un entretien ?</h2>
<p>Oui, et c'est le point le plus souvent mal compris. Dès qu'une lentille est portée plus d'une journée, elle doit être nettoyée et conservée chaque soir dans une solution adaptée, exactement comme une mensuelle. Le rythme de renouvellement plus court ne remplace pas l'entretien quotidien : il limite l'accumulation de dépôts sur la durée, rien de plus. Les règles d'hygiène restent donc entières, et elles ne souffrent aucune exception.</p>
<ol>
  <li><strong>Lavez et séchez vos mains</strong> avant toute manipulation, avec une serviette qui ne peluche pas.</li>
  <li><strong>N'utilisez jamais d'eau du robinet</strong> sur vos lentilles ni sur votre étui : elle peut contenir des micro-organismes responsables d'infections cornéennes graves.</li>
  <li><strong>Renouvelez la solution à chaque usage</strong>, sans jamais compléter le liquide restant de la veille.</li>
  <li><strong>Changez d'étui régulièrement</strong> et laissez-le sécher à l'air libre, ouvert et retourné.</li>
  <li><strong>Respectez la date de renouvellement</strong> sans la repousser, même si la lentille vous semble encore confortable.</li>
</ol>

<h2>Les porteurs astigmates doivent-ils attendre ?</h2>
<p>Non, et c'est une particularité du lancement qui mérite d'être signalée. Une version sphérique et une version torique, destinée à l'astigmatisme, ont été proposées simultanément, alors qu'une nouvelle gamme arrive souvent d'abord en sphérique avant d'être déclinée un ou deux ans plus tard. Les porteurs astigmates n'ont donc pas à patienter pour envisager ce rythme de renouvellement, sous réserve bien sûr que leur correction figure dans les paramètres disponibles.</p>
<ul class="check-list">
<li><span class="check">✓</span> Un renouvellement hebdomadaire, entre la journalière et la mensuelle</li>
<li><span class="check">✓</span> Une hydratation continue revendiquée par le fabricant sur toute la semaine</li>
<li><span class="check">✓</span> Des versions sphérique et torique disponibles d'emblée</li>
</ul>

<h2>Journalière, hebdomadaire ou mensuelle : comment trancher ?</h2>
<p>Le choix se fait rarement sur la seule fiche technique. Il dépend de votre fréquence de port, de votre tolérance à la contrainte quotidienne et de votre budget annuel réel, qui n'est pas toujours celui qu'on imagine. Ce tableau résume les critères que nous passons en revue au comptoir.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Critère</th><th>Journalière</th><th>Hebdomadaire ou mensuelle</th></tr>
    </thead>
    <tbody>
      <tr><td>Entretien quotidien</td><td>Aucun</td><td>Nettoyage et étui chaque soir</td></tr>
      <tr><td>Port occasionnel</td><td>Très adapté</td><td>Moins intéressant, la lentille vieillit sans être portée</td></tr>
      <tr><td>Terrain allergique</td><td>Souvent préférable</td><td>À discuter selon la gêne saisonnière</td></tr>
      <tr><td>Budget sur l'année</td><td>Plus élevé en port quotidien</td><td>Généralement plus contenu</td></tr>
      <tr><td>Discipline demandée</td><td>Jeter chaque soir</td><td>Respecter la date de renouvellement</td></tr>
    </tbody>
  </table>
</div>

<h3>Le vrai critère reste votre œil</h3>
<p>Une sécheresse oculaire marquée, une allergie active ou une cornée fragile peuvent orienter vers la journalière quelles que soient les considérations budgétaires. À l'inverse, un porteur régulier, méthodique et sans gêne particulière tirera souvent un bénéfice d'un rythme plus long. Cette évaluation appartient au professionnel qui vous suit, sur la base de l'examen et de la prescription, jamais à une comparaison de prix sur internet.</p>

<h2>Comment essayer ce nouveau rythme de port ?</h2>
<p>Comme pour toute lentille, l'adaptation se fait sur prescription d'un ophtalmologiste, suivie d'un essai accompagné. Concrètement, nous vérifions les paramètres, nous posons la lentille, nous contrôlons son comportement sur l'œil, puis nous vous laissons la porter dans vos conditions habituelles avant un rendez-vous de contrôle. Changer de fréquence de renouvellement n'est pas anodin : ce qui se juge, c'est le confort au sixième ou septième jour, pas celui de la première heure.</p>
<p>Un œil rouge, douloureux, larmoyant ou une baisse de vision impose de retirer la lentille et de consulter rapidement. En dehors de ces situations, nos opticiens sont à votre disposition à la Galerie Oslo, sur l'Esplanade des Olympiades, pour reprendre les gestes de pose, revoir votre routine d'entretien ou simplement faire le point sur ce qui existe aujourd'hui. Aucun essai ne vous engage à acheter.</p>
"""

ART_BODY_BL_ASANA = """<h2>Qu'est-ce qu'une lentille rigide perméable au gaz ?</h2>
<p>Quand on parle de lentilles de contact, on pense presque toujours aux souples, journalières ou mensuelles. Il existe pourtant une seconde famille, plus ancienne et beaucoup moins visible du grand public : les lentilles rigides perméables au gaz, souvent désignées par leur abréviation RGP. Leur matière plus ferme ne se moule pas sur l'œil comme le ferait une lentille souple : elle conserve sa propre forme et laisse un fin film de larmes entre elle et la cornée. C'est ce détail qui explique l'essentiel de leur intérêt.</p>

<h3>Une forme stable qui corrige les irrégularités</h3>
<p>Sur une cornée régulière, ce principe n'apporte pas grand-chose de décisif. Sur une cornée déformée, en revanche, il change tout : le film lacrymal comble les irrégularités et la surface rigide restitue une géométrie optique nette. Une lentille souple, elle, épouse le relief de la cornée et en reproduit donc les défauts. C'est pour cette raison que les lentilles rigides restent la réponse de référence dans les situations où la souple atteint sa limite, y compris chez des porteurs qui avaient renoncé aux lentilles après plusieurs échecs.</p>

<h3>Un temps d'adaptation à accepter</h3>
<p>Il faut être honnête sur ce point : la sensation initiale est plus marquée qu'avec une souple. Les premiers jours, la paupière perçoit le bord de la lentille à chaque clignement, et il n'est pas rare de larmoyer. Cette gêne s'estompe progressivement à mesure que le porteur s'habitue, mais elle demande de la patience et un accompagnement. Beaucoup d'abandons viennent d'un porteur laissé seul face à cette phase, alors qu'un suivi rapproché aurait suffi à passer le cap.</p>

<h2>Dans quels cas ces lentilles sont-elles proposées ?</h2>
<p>Elles ne s'adressent pas au grand public. Leur indication est posée par l'ophtalmologiste, en fonction de la géométrie de la cornée et de ce que la correction en lunettes ou en lentille souple ne parvient pas à restituer. Voici les situations dans lesquelles elles reviennent le plus souvent.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Situation</th><th>Pourquoi la rigide est envisagée</th></tr>
    </thead>
    <tbody>
      <tr><td>Kératocône</td><td>La cornée se déforme progressivement ; une surface rigide restitue une optique régulière</td></tr>
      <tr><td>Astigmatisme important</td><td>La stabilité de la lentille évite les variations de netteté au clignement</td></tr>
      <tr><td>Cornée irrégulière</td><td>Le film de larmes sous la lentille compense les reliefs</td></tr>
      <tr><td>Après une chirurgie oculaire</td><td>La vision reste perturbée malgré une correction classique</td></tr>
      <tr><td>Certains protocoles d'orthokératologie</td><td>Des géométries inversées, portées la nuit, sous suivi médical</td></tr>
    </tbody>
  </table>
</div>

<h2>Qu'apporte la gamme Asana de Bausch + Lomb ?</h2>
<p>Plutôt qu'un modèle unique, Bausch + Lomb a construit avec Asana une gamme large : lentilles sphériques, asphériques, toriques, multifocales, multifocales toriques, géométries inversées destinées à certains protocoles d'orthokératologie, ainsi que des designs spécifiquement pensés pour le kératocône. Cette étendue n'a rien d'anecdotique pour un porteur : elle permet souvent de trouver une réponse sans changer de fabricant, du premier essai jusqu'aux ajustements ultérieurs.</p>
<p>Le fabricant indique fabriquer l'ensemble de la gamme à partir de matériaux dits « Boston », connus de longue date dans l'univers des lentilles rigides pour leur bonne résistance aux dépôts de protéines et de corps gras. Ce point compte au quotidien : un matériau qui s'encrasse peu conserve une vision nette plus longtemps entre deux nettoyages. Il s'agit là de la position de la marque, et non d'une comparaison indépendante entre matériaux.</p>
<ul class="check-list">
<li><span class="check">✓</span> Une gamme couvrant sphérique, torique, multifocale et kératocône</li>
<li><span class="check">✓</span> Des matériaux réputés pour leur résistance aux dépôts</li>
<li><span class="check">✓</span> Une réponse pour les cornées irrégulières et les suites de chirurgie</li>
</ul>

<h2>Comment se passe l'adaptation, concrètement ?</h2>
<p>Une lentille rigide n'est jamais un produit que l'on choisit sur catalogue. Chaque lentille est réalisée en fonction de la morphologie de la cornée, ce qui suppose un examen approfondi puis un essai accompagné, avec plusieurs rendez-vous d'ajustement. Le parcours est plus long qu'en souple, mais il se déroule presque toujours dans le même ordre.</p>
<ol>
  <li><strong>Examen et prescription par l'ophtalmologiste</strong>, qui pose l'indication et précise le type de lentille attendu.</li>
  <li><strong>Mesures et choix d'une géométrie d'essai</strong>, adaptées à la courbure et au relief de votre cornée.</li>
  <li><strong>Essai accompagné en boutique</strong> : pose, retrait, apprentissage des gestes et observation du comportement de la lentille sur l'œil.</li>
  <li><strong>Période de port progressive</strong>, quelques heures par jour au début, en augmentant selon la tolérance.</li>
  <li><strong>Contrôles d'ajustement</strong>, jusqu'à obtenir une vision stable et un confort durable ; la géométrie peut être modifiée à ce stade.</li>
</ol>
<p>Les règles d'hygiène sont les mêmes que pour toute lentille réutilisable, et elles ne tolèrent aucune approximation. Mains lavées et séchées avant chaque manipulation, jamais d'eau du robinet sur la lentille ni sur l'étui, solution d'entretien spécifique renouvelée à chaque usage, étui changé régulièrement et rythme de renouvellement respecté. Une lentille rigide dure plus longtemps qu'une souple, mais elle n'est pas éternelle : une lentille rayée ou déformée doit être remplacée.</p>

<h2>Faut-il en parler lors de votre prochain contrôle ?</h2>
<p>Si vous portez déjà des lentilles rigides, si des souples ne vous ont jamais réellement convenu, ou si l'on vous a parlé d'un kératocône, c'est typiquement le genre de sujet à évoquer avec votre ophtalmologiste puis avec votre opticien. L'évolution de l'offre ne change pas l'indication médicale, mais elle élargit les possibilités techniques pour des porteurs qui, il y a quelques années, s'entendaient dire qu'il n'y avait plus grand-chose à tenter.</p>
<p>À la Galerie Oslo, sur l'Esplanade des Olympiades, nous prenons le temps nécessaire pour ces adaptations, y compris pour reprendre calmement la pose et le retrait avec un porteur qui bute dessus. Rappelons enfin qu'un œil rouge, douloureux, une photophobie inhabituelle ou une baisse de vision imposent de retirer la lentille et de consulter sans attendre : chez un porteur de lentilles, ces signes ne doivent jamais être mis sur le compte de la fatigue.</p>
"""

ART_BODY_UV_SOLEIL = """<h2>Pourquoi les UV sont-ils un vrai facteur de risque pour les yeux ?</h2>
<p>Protéger sa peau du soleil est devenu un réflexe collectif. Protéger ses yeux, beaucoup moins. Pourtant, l'exposition solaire répétée est reconnue comme jouant un rôle dans plusieurs troubles oculaires, et le sujet fait consensus chez les ophtalmologistes. Une paire de lunettes de soleil n'est donc pas seulement un accessoire de style : c'est un équipement de protection, au même titre qu'une crème solaire, avec la différence qu'on ne peut pas rattraper après coup une exposition mal protégée.</p>

<h3>À court terme, un coup de soleil sur la cornée</h3>
<p>La photokératite, proche de ce que l'on appelle l'ophtalmie des neiges, est la manifestation la plus immédiate. Elle survient après une exposition intense, typiquement en montagne, sur l'eau ou sur le sable, et se déclare souvent plusieurs heures après, une fois rentré. Elle provoque douleur, larmoiement et une forte sensibilité à la lumière pendant deux à trois jours. Elle guérit spontanément, mais elle est franchement pénible, et son apparition signe une exposition qui aurait dû être évitée.</p>

<h3>À long terme, un effet cumulatif</h3>
<p>Le second mécanisme est plus sournois parce qu'il ne se ressent pas. L'exposition cumulée aux UV, année après année, accélère le vieillissement naturel du cristallin et favorise l'apparition de la cataracte. Certains travaux évoquent également un rôle possible des UV dans le développement de la DMLA, la dégénérescence maculaire liée à l'âge, sans que ce lien soit aussi solidement établi. Retenons l'essentiel : ce qui compte, c'est le total accumulé sur une vie, ce qui donne toute leur valeur aux habitudes prises tôt.</p>

<h2>Que signifient les catégories 0 à 4 des verres solaires ?</h2>
<p>Toutes les lunettes de soleil vendues en France doivent afficher le marquage CE et une catégorie de filtration comprise entre 0 et 4, définie par la norme européenne EN ISO 12312-1. Cette catégorie indique l'intensité de la teinte et l'usage auquel le verre est destiné. Elle se lit sur la branche ou sur l'étiquette, et c'est la première chose à vérifier avant même de regarder la monture.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Catégorie</th><th>Teinte</th><th>Usage prévu</th></tr>
    </thead>
    <tbody>
      <tr><td>0 et 1</td><td>Très peu teintée</td><td>Ne protège pas réellement du soleil ; tout au plus une luminosité faible</td></tr>
      <tr><td>2</td><td>Teinte moyenne</td><td>Exposition modérée, en ville l'été par exemple</td></tr>
      <tr><td>3</td><td>Teinte soutenue</td><td>Usage courant en extérieur : plage, balade, conduite</td></tr>
      <tr><td>4</td><td>Très sombre</td><td>Très forte luminosité : haute montagne, glacier ; interdite au volant</td></tr>
    </tbody>
  </table>
</div>
<p>Pour la vie de tous les jours en extérieur, la catégorie 3 est celle que recommande la plupart des professionnels de santé visuelle : elle offre une protection élevée tout en restant compatible avec la conduite. La catégorie 4, elle, est réservée aux conditions extrêmes et se révèle dangereuse au volant, car elle réduit trop la perception des couleurs et des feux de signalisation. Une paire de catégorie 4 dans la boîte à gants n'est donc pas une bonne idée, même pour dépanner.</p>

<h2>Une teinte foncée suffit-elle à protéger ?</h2>
<p>Non, et c'est probablement le malentendu le plus dangereux sur le sujet. La couleur du verre et la filtration des UV sont deux choses distinctes : un verre peut être très sombre sans filtrer correctement les ultraviolets. Le problème est alors pire que de ne rien porter du tout, car l'obscurité apparente fait dilater la pupille, qui laisse entrer davantage de rayons jusqu'au fond de l'œil. C'est précisément ce qui rend les paires de plage sans marquage réellement risquées.</p>
<ul class="check-list">
<li><span class="check">✓</span> Vérifiez toujours le marquage CE et la catégorie de filtration sur la branche ou l'étiquette</li>
<li><span class="check">✓</span> Une teinte foncée sans filtre UV certifié protège moins bien qu'une absence de lunettes</li>
<li><span class="check">✓</span> La catégorie doit correspondre à votre usage réel, pas à l'esthétique du verre</li>
<li><span class="check">✓</span> Une monture enveloppante limite les rayons qui entrent par les côtés</li>
</ul>

<h2>Les enfants ont-ils besoin d'une protection particulière ?</h2>
<p>Oui, et pour une raison anatomique simple. Chez le jeune enfant, le cristallin est naturellement plus transparent que chez l'adulte : il laisse donc passer une plus grande quantité de rayons UV jusqu'à la rétine. Les professionnels de santé visuelle recommandent d'habituer les enfants dès le plus jeune âge à porter des lunettes certifiées, avec des branches bien ajustées et, si possible, une monture enveloppante. L'enjeu n'est pas seulement immédiat : c'est aussi une habitude qui réduira l'exposition cumulée de toute une vie.</p>
<p>Le réflexe vaut également quand le ciel est couvert. Les nuages arrêtent une partie de la lumière visible, ce qui donne une impression de sécurité, mais laissent passer une grande partie des UV. C'est ce décalage qui explique les coups de soleil « surprise » en fin de journée nuageuse, sur la peau comme sur les yeux. La réverbération sur l'eau, le sable et la neige ajoute encore à l'exposition, quelle que soit la saison.</p>

<h2>Comment choisir une paire vraiment adaptée à votre usage ?</h2>
<p>Le choix se fait dans un ordre précis, et la monture arrive plus tard qu'on ne le croit. Voici la démarche que nous suivons en boutique.</p>
<ol>
  <li><strong>Partez de votre usage réel</strong> : conduite quotidienne, marche en ville, mer, montagne, sport, ou un peu de tout.</li>
  <li><strong>Choisissez la catégorie en conséquence</strong>, en gardant à l'esprit qu'une seule paire couvre rarement à la fois la ville et le glacier.</li>
  <li><strong>Vérifiez le marquage CE et la mention de la catégorie</strong> avant tout achat, y compris sur une paire achetée en vacances.</li>
  <li><strong>Regardez la couverture de la monture</strong> : forme, hauteur du verre et galbe comptent autant que le verre lui-même.</li>
  <li><strong>Faites ajuster la paire</strong> pour qu'elle tienne sans glisser, sinon elle finira sur le front, ce qui ne protège personne.</li>
  <li><strong>Si vous portez une correction</strong>, parlez de verres solaires correcteurs plutôt que de superposer une paire par-dessus vos lunettes de vue.</li>
</ol>
<p>Une exposition ancienne ne se rattrape pas, mais elle se surveille. Une gêne durable à la lumière, une vision qui se voile ou des halos autour des phares la nuit méritent un avis ophtalmologique, sans attendre le prochain renouvellement de vos lunettes. Notre rôle s'arrête à l'équipement et au conseil : le diagnostic appartient au médecin.</p>
<p>En boutique, Galerie Oslo sur l'Esplanade des Olympiades, nous vérifions volontiers le marquage d'une paire que vous possédez déjà et nous vous aidons à choisir une catégorie cohérente avec vos usages, pour vous comme pour vos enfants. Cela prend quelques minutes et n'engage à rien.</p>
"""

ART_BODY_PRESBYTIE = """<h2>Qu'est-ce que la presbytie, exactement ?</h2>
<p>Contrairement à une idée reçue tenace, la presbytie n'est pas une maladie et ne traduit aucune fragilité particulière. C'est une évolution naturelle et inévitable du système visuel, liée à l'âge, que rencontrent aussi bien les personnes qui n'ont jamais porté de correction que celles qui sont équipées depuis l'enfance. Selon les données disponibles en France, elle concernerait aujourd'hui plus de 4 personnes sur 10. Autant dire que c'est la situation la plus banale qui soit après un certain âge, même si elle est souvent vécue comme un cap symbolique désagréable.</p>

<h3>Un cristallin qui perd sa souplesse</h3>
<p>À l'intérieur de l'œil, le cristallin joue le rôle d'une lentille souple capable de changer de forme pour faire la mise au point sur les objets proches, grâce à un ensemble de fibres élastiques et de muscles. Avec les années, ce cristallin durcit progressivement et se bombe moins facilement. La conséquence est très caractéristique : la vision de loin reste généralement bonne, mais les caractères proches deviennent flous et le bras s'allonge instinctivement pour éloigner le texte. Le phénomène démarre en général vers 44-45 ans, progresse jusque vers 60-65 ans, puis se stabilise.</p>

<h2>Quels signes doivent vous mettre la puce à l'oreille ?</h2>
<p>Les premiers symptômes sont discrets et volontiers attribués à autre chose : la fatigue, un mauvais éclairage, une police d'écriture trop petite. Ils se répètent pourtant d'une personne à l'autre avec une régularité frappante.</p>
<ul class="check-list">
<li><span class="check">✓</span> Besoin d'éloigner un livre, un téléphone ou un document pour le lire nettement</li>
<li><span class="check">✓</span> Fatigue oculaire ou maux de tête en fin de journée après une lecture prolongée</li>
<li><span class="check">✓</span> Difficulté à lire en lumière faible, alors que cela ne posait aucun problème auparavant</li>
<li><span class="check">✓</span> Vision qui reste nette de loin mais se brouille nettement de près</li>
</ul>
<p>Si plusieurs de ces situations vous parlent, il n'y a pas d'urgence, mais il n'y a pas non plus de raison d'attendre. Forcer pendant des mois ne préserve rien : cela ajoute simplement de la fatigue et des maux de tête. En revanche, une baisse de vision rapide, une douleur, une vision double ou des taches dans le champ visuel ne relèvent pas de la presbytie et justifient un avis médical sans tarder.</p>

<h2>Quelles solutions pour bien voir de près ?</h2>
<p>La bonne nouvelle, c'est que ce trouble se corrige très bien, et de plusieurs façons. Le choix dépend moins de la correction elle-même que de vos habitudes : ce que vous faites de vos journées compte davantage que le chiffre inscrit sur l'ordonnance.</p>

<h3>Des lunettes de lecture aux verres progressifs</h3>
<p>Pour une personne qui voit bien de loin et n'a besoin d'aide que pour lire, une simple paire de vision de près suffit souvent. Pour celles qui portaient déjà une correction de loin, les verres progressifs restent la solution la plus courante : ils permettent de voir net à toutes les distances avec un seul équipement, sans rupture visible entre les zones. Il existe aussi des verres intermédiaires, dits de bureau, qui privilégient les distances de travail plutôt que la vision de loin, utiles pour ceux qui passent leurs journées entre un écran et un dossier papier.</p>

<h3>Les lentilles et la monovision</h3>
<p>Pour qui préfère se passer de lunettes au quotidien, les lentilles progressives ou multifocales constituent une alternative sérieuse. La monovision, qui consiste à corriger un œil pour le loin et l'autre pour le près, convient à certains porteurs et pas du tout à d'autres : elle demande un temps d'adaptation et une tolérance au léger déséquilibre qu'elle crée. Dans tous les cas, l'adaptation se fait sur prescription et avec un essai accompagné, jamais sur simple commande à distance.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Solution</th><th>À qui elle convient le mieux</th><th>Ce qu'il faut savoir</th></tr>
    </thead>
    <tbody>
      <tr><td>Lunettes de lecture</td><td>Bonne vision de loin, besoin ponctuel de près</td><td>À retirer pour se déplacer, donc à garder à portée de main</td></tr>
      <tr><td>Verre progressif</td><td>Correction de loin déjà existante</td><td>Temps d'adaptation variable, centrage déterminant</td></tr>
      <tr><td>Verre de bureau</td><td>Longues journées écran et papier</td><td>Vision de loin réduite, pas adapté à la conduite</td></tr>
      <tr><td>Lentille multifocale</td><td>Envie de se passer de lunettes</td><td>Adaptation sur prescription, essai indispensable</td></tr>
      <tr><td>Monovision</td><td>Porteur déjà habitué aux lentilles</td><td>Ne convient pas à tout le monde, à tester avant de valider</td></tr>
    </tbody>
  </table>
</div>
<p>Une remarque honnête sur les loupes vendues en grande surface : elles dépannent, mais elles délivrent la même puissance aux deux yeux, ignorent un éventuel astigmatisme et ne tiennent pas compte de l'écart entre vos pupilles. Pour un usage occasionnel, pourquoi pas. Pour lire tous les soirs, elles finissent souvent par fatiguer davantage qu'elles ne soulagent.</p>

<h2>Pourquoi faut-il refaire contrôler sa vue régulièrement ?</h2>
<p>Parce que la correction de la presbytie évolue jusque vers 60-65 ans. Il est donc normal de devoir l'ajuster tous les deux à trois ans environ pendant cette période, et ce n'est pas le signe que l'équipement précédent était mauvais. Ces rendez-vous réguliers ont un second intérêt, plus important encore : ils permettent de dépister des affections plus fréquentes après 45 ans, comme le glaucome ou la DMLA, qui évoluent longtemps sans symptôme.</p>
<ol>
  <li><strong>Faites un examen chez l'ophtalmologiste</strong> pour obtenir une prescription et vérifier la santé de l'œil, ce qui relève de lui seul.</li>
  <li><strong>Décrivez vos usages réels</strong> au moment de choisir l'équipement : distances de lecture, écrans, conduite, bricolage, musique.</li>
  <li><strong>Prenez le temps du choix de la forme</strong>, car une monture trop basse limite fortement le champ de vision de près d'un verre progressif.</li>
  <li><strong>Portez la nouvelle correction en continu</strong> les premiers jours plutôt que par intermittence : c'est ce qui accélère l'adaptation.</li>
  <li><strong>Revenez pour un ajustement</strong> si une gêne persiste après quelques semaines, plutôt que de ranger la paire dans un tiroir.</li>
</ol>

<h2>Où faire le point sur votre vision de près ?</h2>
<p>Il est utile de distinguer clairement les rôles. La prescription, le dépistage et le suivi médical appartiennent à l'ophtalmologiste. L'opticien, lui, prend le relais sur l'équipement : mesures de centrage, choix de la monture, montage, adaptation et réglages dans la durée. Ces deux temps sont complémentaires, et l'un ne remplace jamais l'autre.</p>
<p>À Maison Mikis, Galerie Oslo sur l'Esplanade des Olympiades, nous recevons beaucoup de personnes du quartier qui arrivent un peu contrariées d'en être là, et qui repartent surtout soulagées de relire un menu sans effort. Le contrôle de vue se fait sans rendez-vous et prend une vingtaine de minutes. Si vous hésitez entre plusieurs solutions, venez simplement en parler et repartez avec un devis à comparer chez vous : c'est une démarche saine, et nous la trouvons normale.</p>
"""

ART_BODY_CASQUES_JEUNES = """<h2>Pourquoi le casque expose-t-il plus qu'on ne le croit ?</h2>
<p>Écouteurs sur le trajet du matin, casque pendant les révisions, soirée le week-end : la musique accompagne désormais une grande partie de la journée des jeunes générations. Selon un sondage Ifop, près d'un tiers des moins de 35 ans déclarent écouter de la musique au casque plus de deux heures par jour, une proportion qui monte à 34&nbsp;% chez les 15-17 ans. Le problème n'est pas la musique en elle-même, mais l'addition silencieuse de ces heures d'écoute, jour après jour, sans qu'aucun signal ne vienne prévenir que l'on dépasse un seuil.</p>

<h3>Des appareils qui montent très haut</h3>
<p>Beaucoup d'appareils audio personnels peuvent délivrer plus de 105 décibels, un niveau comparable à celui d'une tronçonneuse. Personne n'écouterait volontairement une tronçonneuse pendant une heure, mais la même énergie sonore devient acceptable dès lors qu'elle prend la forme d'un morceau que l'on aime. L'oreille, elle, ne fait pas la différence entre un bruit désagréable et une musique choisie : ce sont les cellules ciliées de l'oreille interne qui encaissent, et elles ne se régénèrent pas.</p>

<h3>Le bruit ambiant pousse à monter le son</h3>
<p>Dans le métro, dans la rue ou dans un open space, le bruit de fond force à augmenter le volume pour continuer à distinguer la musique. C'est un réflexe presque automatique : un quart des personnes interrogées dans cette même enquête reconnaissent monter spontanément le son pour couvrir l'environnement. Résultat, les niveaux les plus élevés sont souvent atteints dans les situations les plus banales, pas lors des concerts que l'on identifie comme risqués.</p>

<h2>À partir de quel niveau et de quelle durée y a-t-il un risque ?</h2>
<p>Contrairement à une idée reçue, ce n'est pas seulement l'intensité qui compte : c'est la combinaison entre le niveau sonore et la durée d'exposition. Plus le son est fort, plus la durée tolérable s'effondre — et elle s'effondre beaucoup plus vite qu'on ne l'imagine.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Niveau sonore</th><th>Durée d'écoute recommandée au maximum</th><th>Situation correspondante</th></tr>
    </thead>
    <tbody>
      <tr><td>80 décibels</td><td>Environ 8 heures</td><td>Écoute au casque à volume modéré</td></tr>
      <tr><td>92 décibels</td><td>Environ 2 heures 30</td><td>Casque poussé pour couvrir le bruit des transports</td></tr>
      <tr><td>98 décibels</td><td>Moins de 40 minutes</td><td>Volume proche du maximum sur un appareil personnel</td></tr>
      <tr><td>104 à 112 décibels</td><td>Quelques dizaines de minutes suffisent à créer un risque</td><td>Niveau courant en discothèque</td></tr>
      <tr><td>Plus de 105 décibels</td><td>Exposition à éviter sans protection</td><td>Maximum délivré par de nombreux casques et écouteurs</td></tr>
    </tbody>
  </table>
</div>
<p>Une soirée en discothèque peut donc représenter un risque réel dès les premières dizaines de minutes si aucune protection n'est portée. Une étude publiée dans BMJ Global Health, consacrée aux habitudes d'écoute des 12-34 ans à travers le monde, estime d'ailleurs que près d'un quart d'entre eux pratiquent une écoute personnelle jugée à risque. De son côté, l'Organisation mondiale de la santé estimait que 1,1 milliard d'adolescents et de jeunes adultes s'exposaient dans le monde à un risque de perte auditive évitable.</p>

<h2>Quels signaux doivent alerter après une écoute ou une soirée ?</h2>
<p>Le premier avertissement de l'oreille est presque toujours le même, et il est massivement ignoré. Dans l'enquête Ifop, 37&nbsp;% des sondés rapportent avoir déjà ressenti des sifflements ou des bourdonnements après une écoute prolongée, un chiffre qui atteint 51&nbsp;% chez les 15-17 ans. Ce sifflement passager traduit une fatigue des cellules de l'oreille interne : le plus souvent il disparaît, mais sa répétition finit par laisser des traces définitives.</p>
<ul class="check-list">
  <li><span class="check">✓</span> Un sifflement ou un bourdonnement qui persiste après une soirée</li>
  <li><span class="check">✓</span> Une sensation d'oreille cotonneuse ou de son étouffé le lendemain</li>
  <li><span class="check">✓</span> Le besoin de faire répéter, notamment dans le bruit</li>
  <li><span class="check">✓</span> Une gêne ou une douleur pendant l'écoute, même brève</li>
</ul>
<p>Un sifflement apparu brutalement et qui ne s'estompe pas au bout de 24 à 48 heures, surtout d'un seul côté ou accompagné d'une baisse d'audition, ne relève pas de l'audioprothésiste mais d'un avis médical rapide. C'est l'un des rares cas où l'urgence compte vraiment.</p>

<h2>Quels réflexes adopter au quotidien ?</h2>
<p>Aucun de ces gestes ne demande de renoncer à la musique. Ils sont classés ici par ordre d'efficacité, du plus déterminant au plus accessoire.</p>
<ol>
  <li><strong>Ne pas dépasser environ 60&nbsp;% du volume maximal de l'appareil.</strong> C'est le repère le plus simple à retenir, et de loin le plus utile.</li>
  <li><strong>Utiliser la réduction de bruit</strong> plutôt que de monter le son. Elle permet d'écouter plus bas sans perdre en confort. Seuls 10&nbsp;% des utilisateurs y recourent activement, alors que la plupart des appareils récents en sont équipés.</li>
  <li><strong>S'accorder des pauses</strong> lors des écoutes longues. Quelques minutes sans casque toutes les heures laissent à l'oreille le temps de récupérer.</li>
  <li><strong>Porter des bouchons filtrants en concert et en soirée.</strong> Contrairement aux bouchons en mousse, ils atténuent sans déformer la musique et se portent toute la soirée.</li>
  <li><strong>S'éloigner des enceintes</strong> et sortir quelques minutes de la salle de temps en temps : le simple fait de réduire la durée d'exposition change la donne.</li>
  <li><strong>Activer les limitations proposées par les smartphones</strong>, qui signalent ou plafonnent les niveaux élevés, particulièrement utiles pour les plus jeunes.</li>
</ol>

<h2>Comment en parler avec un adolescent sans le braquer ?</h2>
<p>L'expérience du comptoir est assez constante : l'argument du risque lointain ne fonctionne pas. Ce qui parle, en revanche, c'est le sifflement ressenti après une soirée, le fait de ne plus suivre une conversation dans un bar, ou l'idée qu'une perte auditive ne se répare pas. Montrer le repère des 60&nbsp;% sur son propre téléphone est souvent plus efficace qu'un long discours. Interdire le casque n'a aucun sens ; apprendre à régler le volume et à protéger ses oreilles en soirée, oui.</p>
<p>Un mot sur les bouchons : les modèles filtrants pour musiciens et sorties existent en versions standard peu coûteuses ou sur mesure. Ils ne coupent pas la musique, ils l'atténuent de façon homogène. Beaucoup de jeunes que nous équipons découvrent qu'ils entendent mieux les détails d'un concert avec un filtre qu'à oreilles nues.</p>

<h2>Quand faire contrôler son audition ?</h2>
<p>Il n'est jamais trop tôt. Un bilan auditif prend moins d'une heure, ne coûte rien chez l'audioprothésiste et n'engage à rien : il mesure les seuils oreille par oreille et vérifie la compréhension de la parole dans le bruit, qui est souvent le premier domaine touché. Réalisé une première fois vers 18 ou 20 ans, il constitue surtout un point de référence, précieux pour comparer dix ans plus tard. Rappelons que l'audioprothésiste dépiste et conseille, tandis que le diagnostic et la recherche d'une cause relèvent du médecin ou de l'ORL.</p>
<p>À Maison Mikis, Galerie Oslo sur l'Esplanade des Olympiades, nous recevons régulièrement des étudiants du quartier venus après une soirée qui a laissé un sifflement. Dans la majorité des cas, la mesure est rassurante et l'échange porte surtout sur les habitudes d'écoute. C'est précisément ce moment-là qui est utile : celui où l'on peut encore changer quelque chose.</p>
"""

ART_BODY_ACOUPHENES = """<h2>Qu'est-ce qu'un acouphène, exactement ?</h2>
<p>Un acouphène est un son perçu par l'oreille alors qu'aucune source extérieure ne le produit. Sifflement aigu, bourdonnement sourd, grésillement continu, souffle qui va et vient : les descriptions varient d'une personne à l'autre, et parfois chez la même personne selon les moments de la journée. En France, on estime que plus de 6 millions de personnes en font l'expérience, de façon occasionnelle ou permanente. C'est donc un trouble banal par sa fréquence, ce qui ne l'empêche pas de rester très mal compris de l'entourage.</p>

<h3>Un son réel, même s'il est inaudible pour les autres</h3>
<p>La confusion la plus courante consiste à croire que l'acouphène « est dans la tête », au sens où il serait imaginaire. Il ne l'est pas. Le plus souvent, il correspond à une activité anormale du système auditif, qui produit un signal en l'absence de stimulation. Le fait que personne d'autre ne l'entende ne dit rien de son intensité vécue : deux personnes décrivant le même sifflement peuvent en souffrir de manière radicalement différente.</p>

<h3>Un acouphène n'est pas toujours le signe d'une surdité</h3>
<p>Autre idée reçue tenace : l'acouphène ne s'accompagne pas systématiquement d'une baisse d'audition mesurable. Il peut apparaître alors que l'oreille perçoit encore très bien la parole et les sons du quotidien. C'est même l'une des raisons pour lesquelles beaucoup de personnes concernées repoussent la consultation : puisqu'elles entendent bien, elles en déduisent qu'il n'y a rien à chercher. La mesure sert justement à trancher, dans un sens comme dans l'autre.</p>

<h2>D'où viennent les acouphènes ?</h2>
<p>Selon l'étude PESA, menée par la Journée Nationale de l'Audition et l'association France Acouphènes auprès de plus de 1&nbsp;500 personnes concernées, l'âge moyen d'apparition se situe autour de 41 ans. Chez les moins de 50 ans, le traumatisme sonore constitue la cause la plus fréquente, loin devant les autres origines : concert, soirée, exposition professionnelle, écoute prolongée au casque. Le tableau ci-dessous résume les situations que nous rencontrons le plus souvent au comptoir.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Contexte d'apparition</th><th>Ce que cela évoque souvent</th><th>Vers qui se tourner</th></tr>
    </thead>
    <tbody>
      <tr><td>Après un concert ou une soirée</td><td>Traumatisme sonore aigu</td><td>Avis médical rapide si le sifflement persiste au-delà de 24 heures</td></tr>
      <tr><td>Installation progressive après 50 ans</td><td>Vieillissement de l'oreille interne</td><td>Contrôle de l'audition chez l'audioprothésiste</td></tr>
      <tr><td>Oreille bouchée, audition en baisse</td><td>Bouchon de cérumen ou atteinte de l'oreille moyenne</td><td>Médecin traitant</td></tr>
      <tr><td>Bruit rythmé sur les battements du cœur</td><td>Acouphène dit pulsatile, à explorer</td><td>Consultation médicale, orientation possible vers un ORL</td></tr>
      <tr><td>Apparition brutale d'un seul côté</td><td>Situation à traiter comme une urgence</td><td>Service d'urgence ou ORL sans attendre</td></tr>
      <tr><td>Après un choc, un stress intense, un traitement</td><td>Facteurs déclenchants ou aggravants multiples</td><td>Médecin traitant, sans arrêter un traitement de soi-même</td></tr>
    </tbody>
  </table>
</div>
<p>Cette liste ne remplace évidemment aucun avis médical : elle sert à comprendre que derrière un même sifflement peuvent se cacher des situations très différentes, dont certaines relèvent d'une prise en charge rapide.</p>

<h2>Pourquoi les acouphènes pèsent-ils autant sur le quotidien ?</h2>
<p>Toujours selon l'étude PESA, près de la moitié des personnes concernées, soit 47,2&nbsp;%, rapportent une gêne modérée ; un cinquième décrit une forme sévère et plus d'une personne sur dix une gêne qualifiée de catastrophique. Les répercussions touchent d'abord le sommeil, la concentration et l'humeur, c'est-à-dire précisément les domaines dans lesquels un trouble invisible est le plus difficile à faire reconnaître.</p>
<p>Le retentissement professionnel est tout aussi concret : 16&nbsp;% des personnes interrogées ont dû s'absenter au moins une fois à cause de leurs acouphènes, et 11,4&nbsp;% ont changé de poste ou d'emploi. Il s'installe souvent un cercle difficile à rompre, où la fatigue accroît l'attention portée au bruit, laquelle nourrit à son tour la tension et le mauvais sommeil. Comprendre ce mécanisme fait déjà partie de la prise en charge.</p>

<h2>Quand faut-il consulter, et à quel rythme ?</h2>
<p>Un tiers des personnes touchées n'a jamais consulté de professionnel de santé à ce sujet, et le premier rendez-vous intervient en moyenne six à sept ans après l'apparition des symptômes. C'est beaucoup, d'autant que certaines situations ne souffrent aucun délai. Voici comment nous hiérarchisons les choses.</p>
<ol>
  <li><strong>Le jour même :</strong> acouphène apparu brutalement d'un seul côté, surtout s'il s'accompagne d'une baisse d'audition, de vertiges ou d'une douleur. C'est une urgence médicale.</li>
  <li><strong>Dans les jours qui suivent :</strong> sifflement persistant après un concert ou une exposition sonore forte, qui ne s'estompe pas au bout de 24 à 48 heures.</li>
  <li><strong>Sans tarder :</strong> bruit pulsatile, synchrone des battements du cœur, qui justifie un avis médical et parfois une orientation vers un ORL.</li>
  <li><strong>Dans les semaines qui suivent :</strong> acouphène installé depuis plus de quelques jours, même bien supporté. C'est le moment de faire le point sur l'audition.</li>
  <li><strong>En suivi :</strong> acouphène ancien dont la tonalité, l'intensité ou le retentissement changent. Un changement mérite toujours une réévaluation.</li>
</ol>

<h2>Que peut-on faire pour réduire la gêne au quotidien ?</h2>
<p>Il n'existe pas de solution unique, et nous nous méfions des promesses de disparition. Ce qui fonctionne, en revanche, tient souvent à un ensemble de gestes simples et à une prise en charge coordonnée. Le premier réflexe consiste à ne pas rechercher le silence absolu : dans une pièce parfaitement calme, le cerveau n'a plus rien d'autre à écouter et l'acouphène occupe tout l'espace. Un fond sonore discret, une fenêtre entrouverte ou une musique très basse au coucher suffisent souvent à réduire la perception.</p>
<p>La protection de l'oreille vient ensuite : bouchons adaptés en concert et en milieu bruyant, volume d'écoute raisonnable au casque, pauses régulières. Enfin, lorsqu'une baisse d'audition est associée, la corriger améliore fréquemment la gêne, parce que l'oreille reçoit à nouveau les sons de l'environnement. Le stress et le manque de sommeil, eux, ne créent pas l'acouphène mais amplifient nettement ce que l'on en ressent.</p>

<h2>Comment se passe un bilan chez l'audioprothésiste ?</h2>
<p>Un bilan auditif complet dure environ une heure et se déroule sans engagement. Il comprend un entretien détaillé sur les circonstances d'apparition et les facteurs aggravants, un examen du conduit et du tympan, puis des mesures en cabine, dans le silence et dans le bruit. L'objectif est double : rechercher une baisse d'audition associée, et poser des mots précis sur ce que vous entendez.</p>
<ul class="check-list">
  <li><span class="check">✓</span> Un entretien sur l'histoire de l'acouphène et son retentissement</li>
  <li><span class="check">✓</span> Des mesures pour objectiver une éventuelle atteinte auditive</li>
  <li><span class="check">✓</span> Des conseils concrets sur l'environnement sonore et la protection</li>
  <li><span class="check">✓</span> Une orientation vers un ORL lorsque la situation le demande</li>
</ul>
<p>Nous tenons à être clairs sur nos limites : l'audioprothésiste n'établit pas de diagnostic et ne prescrit aucun traitement. La recherche d'une cause relève du médecin traitant et, le cas échéant, du spécialiste. Notre rôle est de mesurer, d'expliquer et d'accompagner. À Maison Mikis, Galerie Oslo sur l'Esplanade des Olympiades, nous recevons régulièrement des personnes qui vivent avec un sifflement depuis des années sans en avoir jamais parlé à quiconque. Prendre rendez-vous ne coûte rien et permet, au minimum, de savoir où l'on en est.</p>
"""

ART_BODY_DEVIS_NORMALISE = """<h2>Qu'est-ce que le devis normalisé, et qui doit vous le remettre ?</h2>
<p>Depuis le 1<sup>er</sup> janvier 2020, tout opticien et tout audioprothésiste a l'obligation de vous remettre un devis normalisé avant la vente de lunettes, de lentilles ou d'aides auditives. Le mot important est « normalisé » : le document suit un modèle réglementaire identique d'un professionnel à l'autre, avec les mêmes rubriques dans le même ordre. Que vous poussiez la porte d'une enseigne nationale ou d'une boutique indépendante, vous retrouvez la même trame, ce qui rend deux propositions directement comparables.</p>
<p>Ce n'est donc pas une formalité administrative de plus. C'est un outil conçu pour le patient, dans un secteur où les prix sont largement libres et où le vocabulaire technique peut vite devenir opaque. Le devis vous est remis sans engagement, avant toute commande, et il reste valable au moins deux mois : vous avez le droit de le prendre, de rentrer chez vous et d'y réfléchir.</p>

<h2>Que doit obligatoirement contenir le document ?</h2>
<h3>Au moins une offre 100 % Santé</h3>
<p>C'est la règle la plus structurante : le devis doit toujours faire apparaître une proposition issue du panier 100 % Santé, même si vous avez d'emblée exprimé une préférence pour autre chose. En optique, cela correspond à la classe A, avec une monture plafonnée à 30&nbsp;€ et des verres dont les prix maximaux sont fixés par arrêté. En audiologie, cela correspond à la classe I, dont le prix de vente est plafonné à 950&nbsp;€ par oreille pour un adulte de 20 ans et plus, et à 1&nbsp;400&nbsp;€ pour les moins de 20 ans. Un devis qui ne mentionnerait aucune offre de ce type ne serait pas conforme.</p>
<h3>Les produits et les chiffres, ligne par ligne</h3>
<p>À côté de cette offre figure la proposition que vous avez retenue ou que le professionnel vous conseille. Pour chaque produit, le devis identifie la marque, le modèle et la référence fabricant, ainsi que les caractéristiques techniques essentielles. Puis viennent les montants : prix de vente, base de remboursement de l'Assurance Maladie, estimation du remboursement de votre complémentaire lorsque le professionnel dispose de l'information, et le solde qui en découle.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Rubrique du devis</th><th>Ce qu'elle signifie</th><th>Ce qu'il faut vérifier</th></tr>
    </thead>
    <tbody>
      <tr><td>Classe de l'équipement</td><td>Classe A ou B en optique, I ou II en audiologie</td><td>La classe A ou I ne peut pas dépasser le plafond réglementaire</td></tr>
      <tr><td>Marque, modèle, référence</td><td>Identification précise du produit vendu</td><td>Deux devis ne se comparent que sur des références équivalentes</td></tr>
      <tr><td>Prix de vente</td><td>Ce que vous payez au total, avant remboursement</td><td>Monture et verres doivent être chiffrés séparément</td></tr>
      <tr><td>Base de remboursement</td><td>Montant de référence de l'Assurance Maladie</td><td>Elle est réglementaire, et donc identique partout</td></tr>
      <tr><td>Estimation complémentaire</td><td>Ce que votre mutuelle devrait prendre en charge</td><td>Une estimation n'est pas un engagement de votre contrat</td></tr>
      <tr><td>Solde à votre charge</td><td>Ce qui vous restera réellement à payer</td><td>Le chiffre à comparer, plutôt que le prix affiché</td></tr>
    </tbody>
  </table>
</div>

<h2>Comment lire concrètement un devis, dans quel ordre ?</h2>
<p>Voici la méthode que nous conseillons aux clients qui repartent avec deux ou trois documents à comparer. Elle prend une dizaine de minutes à la table de la cuisine.</p>
<ol>
  <li><strong>Commencez par la dernière ligne.</strong> Le reste à charge estimé est la seule donnée qui vous concerne directement ; le prix de vente seul ne dit rien tant qu'on ignore la couverture.</li>
  <li><strong>Vérifiez que l'offre 100 % Santé figure bien sur le document</strong>, même si vous ne la retenez pas. Son absence est un signal.</li>
  <li><strong>Comparez des produits équivalents.</strong> Un progressif et un unifocal, ou deux aides auditives de classes différentes, ne se comparent pas — la référence fabricant permet de trancher.</li>
  <li><strong>Regardez ce qui est inclus.</strong> Traitements des verres, adaptation, réglages, garantie : deux prix identiques peuvent recouvrir des prestations très différentes.</li>
  <li><strong>Repérez la date de validité.</strong> Le devis tient au moins deux mois, ce qui vous laisse le temps d'interroger votre complémentaire.</li>
  <li><strong>Appelez votre mutuelle avec le devis sous les yeux.</strong> Les codes et montants qui y figurent lui permettent de répondre précisément, ce qu'une question générale ne permet jamais.</li>
</ol>

<h2>Pourquoi l'estimation peut-elle différer du remboursement réel ?</h2>
<p>C'est la question qui provoque le plus de déceptions, et elle mérite une réponse franche. La base de remboursement de l'Assurance Maladie est réglementaire : elle ne varie pas d'un magasin à l'autre. La part de la complémentaire, elle, dépend entièrement de votre contrat, de ses plafonds, de son éventuel délai de carence et de la date de votre dernier équipement. Le professionnel peut souvent interroger votre organisme en ligne et obtenir un chiffre fiable, mais quand cette interrogation n'est pas possible, la ligne « estimation » reste une estimation.</p>
<p>En audiologie, un point complémentaire compte autant que le prix : la réglementation impose une période d'essai d'au moins 30 jours avant l'achat définitif et une garantie de 4 ans minimum, quelle que soit la classe choisie. Ces prestations ne se lisent pas sur la ligne de total, mais elles font partie de ce que vous achetez. En optique, la mécanique est différente : en classe B, les contrats responsables remboursent la monture à hauteur de 100&nbsp;€ maximum, ce qui explique une bonne part des écarts constatés d'un devis à l'autre.</p>

<h2>Faut-il signer le jour même ?</h2>
<p>Non, et nous le disons à chaque fois. Rien ne vous oblige à décider sur place, et demander un devis pour le comparer ailleurs est une démarche parfaitement normale, que nous trouvons saine. Un professionnel qui s'en agace ou qui conditionne un prix à une signature immédiate vous en apprend beaucoup sur sa façon de travailler. Le devis existe précisément pour vous laisser ce temps.</p>
<p>En boutique, nous l'établissons systématiquement et sans engagement, y compris pour une simple simulation. Nous interrogeons votre complémentaire quand elle le permet, nous appliquons le tiers payant chaque fois que le contrat l'autorise, et nous reprenons volontiers chaque ligne avec vous jusqu'à ce que le document soit clair. Beaucoup de nos clients du Triangle de Choisy passent d'abord Galerie Oslo pour faire chiffrer une idée, puis reviennent plusieurs semaines plus tard : c'est exactement l'usage prévu.</p>
"""

ART_BODY_RENOUVELER_ORDONNANCE = """<h2>Peut-on vraiment changer de lunettes sans repasser par le médecin ?</h2>
<p>Beaucoup de personnes renoncent à remplacer une paire abîmée ou dépassée parce qu'elles pensent devoir d'abord obtenir un rendez-vous chez l'ophtalmologiste, avec des délais parfois longs. Dans une grande partie des cas, cette étape n'est pas nécessaire. Depuis le 15 avril 2007, la réglementation française autorise les opticiens-lunetiers à renouveler et à adapter une correction sans nouvelle consultation, dans un cadre précisé ensuite par le décret n° 2016-1381 du 12 octobre 2016.</p>
<p>Il ne s'agit pas d'un contournement du parcours de soins, mais d'une compétence encadrée. L'opticien n'établit pas de prescription : il travaille à partir d'une prescription médicale existante, encore valide, et il informe le médecin prescripteur de toute adaptation réalisée. Le rôle du praticien reste entier ; ce qui change, c'est que vous n'avez pas à attendre plusieurs mois pour continuer à voir correctement.</p>

<h2>Combien de temps une ordonnance reste-t-elle valable ?</h2>
<p>La durée dépend de l'âge de la personne au moment où la prescription a été établie, parce que la vue évolue à des rythmes très différents selon les périodes de la vie. Ce tableau résume les repères à connaître.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Âge lors de la prescription</th><th>Durée de validité</th><th>Ce que l'opticien peut faire</th></tr>
    </thead>
    <tbody>
      <tr><td>Moins de 16 ans</td><td>1 an</td><td>Renouvellement à l'identique uniquement, la vue évoluant vite à cet âge</td></tr>
      <tr><td>De 16 à 42 ans</td><td>5 ans</td><td>Renouvellement et adaptation de la correction si nécessaire</td></tr>
      <tr><td>Plus de 42 ans</td><td>3 ans</td><td>Renouvellement et adaptation de la correction si nécessaire</td></tr>
      <tr><td>Opposition écrite du prescripteur</td><td>Sans objet</td><td>Aucune adaptation possible, retour obligatoire chez le médecin</td></tr>
      <tr><td>Presbytie découverte</td><td>Sans objet</td><td>Orientation vers l'ophtalmologiste avant tout équipement</td></tr>
    </tbody>
  </table>
</div>
<p>Passé ces délais, l'ordonnance ne peut plus servir de base à un renouvellement pris en charge, et une nouvelle consultation devient nécessaire. Une prescription encore valable sur le papier n'oblige évidemment personne à s'en contenter : si votre vue vous semble avoir changé, un avis médical reste toujours possible et souvent souhaitable.</p>

<h2>Que peut faire l'opticien, et que ne peut-il pas faire ?</h2>
<h3>Ce qui relève de sa compétence</h3>
<p>Dans les délais rappelés ci-dessus, l'opticien peut refaire un équipement à l'identique, mais aussi ajuster la puissance des verres s'il constate un écart lors de l'examen de vue réalisé en magasin. Cette mesure n'a pas de valeur diagnostique : elle sert à déterminer la correction qui vous rendra la vision la plus confortable. L'adaptation est ensuite consignée et transmise au médecin, et elle porte sur la correction seule, jamais sur autre chose.</p>
<h3>Ce qui impose un retour chez le médecin</h3>
<p>Plusieurs situations sortent du cadre, et nous préférons les dire clairement plutôt que de laisser espérer un raccourci. Le prescripteur peut s'opposer par écrit au renouvellement directement sur l'ordonnance, et cette mention s'impose à tous. Une baisse de vision rapide, une douleur, une vision double, des éclairs lumineux ou des taches dans le champ visuel relèvent d'un avis médical sans délai. Les lentilles de contact, enfin, obéissent à des règles qui leur sont propres et ne suivent pas exactement celles des verres correcteurs.</p>

<h2>Pourquoi la presbytie change-t-elle la donne ?</h2>
<p>La presbytie apparaît généralement autour de la quarantaine : le cristallin perd de sa souplesse, la vision de près se brouille, on tend le bras pour lire une étiquette. C'est un phénomène naturel, qui n'a rien d'inquiétant en soi. Mais cette tranche d'âge coïncide avec le moment où un examen ophtalmologique complet devient réellement utile, notamment pour rechercher des pathologies silencieuses qui ne se manifestent par aucun symptôme au début.</p>
<p>C'est pourquoi la réglementation prévoit qu'une presbytie constatée pour la première fois impose une orientation vers l'ophtalmologiste : l'opticien ne peut pas créer lui-même cette correction de près. En revanche, si elle figure déjà sur une prescription en cours de validité, son renouvellement se fait dans les mêmes conditions que n'importe quelle autre correction. Beaucoup de personnes qui viennent nous voir en pensant avoir simplement besoin d'une paire de loupes découvrent à cette occasion qu'un bilan médical est le bon réflexe.</p>

<h2>Validité de l'ordonnance et remboursement, est-ce la même chose ?</h2>
<p>Non, et cette confusion revient très souvent au comptoir. La validité de la prescription détermine ce que l'opticien a le droit de faire ; la périodicité de prise en charge détermine ce que l'Assurance Maladie et votre complémentaire acceptent de rembourser. Les deux calendriers ne coïncident pas.</p>
<ol>
  <li><strong>À partir de 16 ans :</strong> une prise en charge tous les 2 ans.</li>
  <li><strong>Entre 6 et 16 ans :</strong> tous les ans.</li>
  <li><strong>Avant 6 ans :</strong> tous les ans, délai ramené à 6 mois en cas de mauvaise adaptation ou d'évolution de la correction.</li>
  <li><strong>Renouvellement anticipé :</strong> possible en cas d'évolution de la vue justifiée par une nouvelle prescription, ou de pathologie évolutive comme un glaucome, une DMLA, un diabète ou une cataracte opérée.</li>
  <li><strong>Hors de ces délais :</strong> rien n'interdit d'acheter une nouvelle paire, mais elle reste alors à votre charge, sous réserve des garanties propres à votre contrat.</li>
</ol>

<h2>Comment se passe la démarche en boutique ?</h2>
<p>C'est simple et cela commence toujours par la même chose : nous regardons la date et les mentions de votre prescription. Si elle est encore valable et qu'aucune opposition n'y figure, nous procédons à un contrôle, nous comparons le résultat à la correction en cours et nous vous expliquons ce que nous constatons. Si tout concorde, l'équipement peut être commandé dans la foulée. Si quelque chose nous semble avoir changé au-delà de ce que nous pouvons ajuster, nous vous le disons et nous vous orientons vers un ophtalmologiste, sans chercher à conclure une vente.</p>
<p>Cette prudence n'est pas une précaution de façade. Nous voyons régulièrement, Galerie Oslo sur l'Esplanade des Olympiades, des personnes venues pour une simple paire de secours chez qui le contrôle révèle un écart méritant un avis médical. Le renouvellement sans nouvelle ordonnance est un vrai gain de temps, mais il ne remplace pas le suivi ophtalmologique régulier — il permet simplement de ne pas rester des mois avec des verres inadaptés en attendant un rendez-vous.</p>
"""

ART_BODY_RAYBAN_META = """<h2>Qu'est-ce qu'une lunette connectée, exactement ?</h2>
<p>Depuis 2023, une catégorie d'objet que le grand public avait fini par enterrer est revenue sur le devant de la scène. EssilorLuxottica, le groupe italo-français propriétaire de Ray-Ban, s'est associé à Meta pour lancer des montures d'allure parfaitement classique — Wayfarer ou Headliner en tête — équipées d'une caméra discrète, de haut-parleurs dits open-ear qui diffusent le son sans boucher le conduit auditif, et d'un assistant vocal. Les tentatives précédentes de lunettes connectées, souvent jugées disgracieuses ou trop ostensiblement technologiques, n'avaient jamais dépassé les cercles d'initiés. Cette fois, c'est le succès esthétique autant que commercial qui a surpris le secteur.</p>

<h3>La technologie s'efface derrière le dessin</h3>
<p>C'est le point que la profession a le plus commenté, et il mérite d'être souligné : ce ne sont pas des objets électroniques auxquels on aurait ajouté des verres, mais des montures reconnaissables auxquelles on a ajouté de l'électronique. Les formes épurées, les charnières classiques et les coloris restent fidèles à l'héritage de la marque. Pour un opticien, cela change la conversation : on ne parle plus d'un gadget que l'on montre à ses amis, mais d'une paire que quelqu'un envisage sérieusement de porter tous les jours.</p>

<h2>Que promet l'écran intégré des Ray-Ban Display ?</h2>
<p>La suite de cette histoire s'est écrite à l'automne 2025, lors de la conférence Meta Connect, avec la présentation des Ray-Ban Display. Selon le fabricant, un mini-écran est intégré directement dans le verre droit et permet d'afficher des notifications, des itinéraires ou des traductions en temps réel, l'ensemble étant piloté par un bracelet à capteurs musculaires porté au poignet. Nous rapportons ici ce qu'annonce la marque : nous n'avons pas de recul indépendant sur le confort visuel réel d'un affichage placé dans le champ de vision, ni sur ce que cela donne au bout de plusieurs heures de port. C'est une réserve d'honnêteté, pas un procès d'intention.</p>

<h3>Ce que l'on ne sait pas encore</h3>
<p>Un affichage superposé à la vision naturelle soulève des questions que le marketing ne tranche pas : fatigue liée à la sollicitation permanente de l'attention, adaptation des yeux à deux plans de netteté, comportement pour une personne qui porte déjà une correction. Ces sujets demanderont du temps et des travaux indépendants. En attendant, si un affichage dans le verre provoque chez vous une gêne persistante, des maux de tête ou une vision qui se trouble, la bonne démarche est d'arrêter de le porter et d'en parler à un ophtalmologiste plutôt que de chercher à s'y habituer.</p>

<h2>Faut-il s'inquiéter de la caméra et de la vie privée ?</h2>
<p>C'est la question qui revient le plus souvent au comptoir, et elle est légitime. Une lunette équipée d'une caméra filme à hauteur de regard, sans le geste explicite de sortir un téléphone : les personnes en face ne savent pas toujours qu'un enregistrement est en cours. Selon le fabricant, un témoin lumineux signale que la capture est en cours, mais il faut avoir la lucidité de reconnaître qu'un voyant de cette taille peut passer inaperçu dans une rue animée. Nous ne connaissons pas non plus le détail du traitement des données par l'éditeur de l'assistant vocal : ce point relève de sa politique de confidentialité, qui mérite d'être lue avant l'achat plutôt qu'après.</p>
<p>Il existe par ailleurs un cadre juridique en France : filmer des personnes identifiables dans l'espace public et diffuser ces images n'est pas libre de droit, et certains lieux — établissements scolaires, hôpitaux, vestiaires, salles de spectacle — appliquent leurs propres interdictions. Le porteur reste responsable de ce qu'il enregistre. Nous préférons le dire clairement, y compris à ceux que ces montures font envie.</p>

<h2>Qu'est-ce que cela change au choix de votre prochaine monture ?</h2>
<p>Au-delà du cas particulier des modèles connectés, cette actualité déplace ce que l'on attend d'une paire de lunettes. Une monture que l'on garde du matin au soir, parce qu'elle sert aussi à écouter, à photographier ou à s'orienter, doit tenir sur le visage bien plus longtemps qu'une solaire portée deux heures. L'exigence de confort, d'équilibre du poids et d'adéquation à la morphologie devient donc centrale. Le tableau suivant résume ce que nous vérifions différemment selon les cas.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Critère</th><th>Monture classique</th><th>Monture connectée</th></tr>
    </thead>
    <tbody>
      <tr><td>Poids et répartition</td><td>Réparti sur le nez et les oreilles</td><td>Branches plus épaisses, appui déplacé vers l'arrière</td></tr>
      <tr><td>Durée de port</td><td>Selon l'usage, souvent partielle</td><td>Pensée pour être portée en continu</td></tr>
      <tr><td>Ajustage</td><td>Réglable finement à chaud ou à froid</td><td>Marge de réglage limitée par l'électronique intégrée</td></tr>
      <tr><td>Verres correcteurs</td><td>Toutes corrections selon la forme</td><td>Dépend du modèle et de la correction, à vérifier auprès du fabricant</td></tr>
      <tr><td>Entretien et réparation</td><td>Pièces d'usure remplaçables en boutique</td><td>Passe le plus souvent par le service du fabricant</td></tr>
      <tr><td>Durée de vie</td><td>Plusieurs années si la monture est entretenue</td><td>Liée à la batterie et aux mises à jour logicielles</td></tr>
    </tbody>
  </table>
</div>

<h2>Comment décider si ce type de lunettes est fait pour vous ?</h2>
<p>Nous ne cherchons ni à vanter ni à décourager ces produits. Voici plutôt les questions que nous conseillons de se poser, dans cet ordre, avant de s'engager.</p>
<ol>
  <li><strong>À quoi servira réellement la paire ?</strong> Si l'usage principal reste la correction de la vue toute la journée, une monture classique bien choisie répondra mieux au besoin, et pour longtemps.</li>
  <li><strong>Acceptez-vous la contrainte de la recharge ?</strong> Une lunette qui se recharge devient un objet dont il faut s'occuper, ce qui n'est pas anodin pour quelqu'un qui ne peut pas se passer de sa correction.</li>
  <li><strong>Avez-vous lu la politique de confidentialité ?</strong> C'est le document qui décrit ce qui est enregistré, transmis et conservé. Il ne remplace pas une garantie, mais il évite les mauvaises surprises.</li>
  <li><strong>Votre correction est-elle compatible ?</strong> Certaines corrections fortes ou complexes s'accommodent mal des contraintes de ces montures. Cette vérification se fait modèle par modèle, avec votre ordonnance en main.</li>
  <li><strong>Comment se passera l'après-vente ?</strong> Réparation, remplacement d'une branche, obsolescence logicielle : ces points se posent différemment d'une paire traditionnelle, et méritent d'être clarifiés avant l'achat.</li>
</ol>

<h2>Où faire le point sereinement sur tout cela ?</h2>
<p>Une chose au moins est certaine : les silhouettes qui inspirent ces modèles connectés — Wayfarer, Clubmaster, aviateur revisité — restent au cœur des tendances actuelles et continuent d'être demandées en version optique traditionnelle, sans la moindre électronique. Nous voyons d'ailleurs beaucoup de personnes venir avec une image de lunettes connectées en tête et repartir avec la forme, sans la technologie, parce que c'est le dessin qui leur plaisait.</p>
<p>Dans notre boutique de la Galerie Oslo, sur l'Esplanade des Olympiades, nous suivons ces évolutions de près sans nous laisser emporter par elles. Vous pouvez passer essayer les formes qui vous attirent, poser vos questions sur ce que ces objets font et ne font pas, et repartir sans rien décider. Pour la correction elle-même, une ordonnance en cours de validité reste nécessaire, et un contrôle de la vue permet en quelques minutes de savoir où vous en êtes avant de vous projeter dans quoi que ce soit.</p>
"""

ART_BODY_MATIERES_DURABLES = """<h2>Pourquoi la lunetterie est-elle concernée par la question environnementale ?</h2>
<p>Après le textile, c'est au tour de l'optique de revoir sa copie. Le secteur a longtemps reposé sur des acétates classiques et des chaînes de production éloignées des lieux de vente, sans qu'on s'interroge beaucoup sur l'origine de la matière. Depuis quelques années, une génération de marques a fait de ce sujet un élément central de son discours, et la question revient souvent au comptoir. Nous y répondons avec nuance : aucune paire de lunettes n'est neutre pour l'environnement. La vraie question n'est pas de trouver la lunette parfaite, mais de savoir sur quels leviers on agit réellement.</p>

<h3>Trois leviers, pas un seul</h3>
<p>Le premier levier est la matière : de quoi la monture est-elle faite, et cette matière a-t-elle été extraite, cultivée ou récupérée. Le deuxième est la fabrication : où, comment, et avec quel emballage. Le troisième, souvent négligé, est la durée de vie : une monture réparable et effectivement réparée vaut mieux qu'une monture irréprochable sur le papier mais jetée au bout de quelques saisons. C'est le seul des trois que vous pouvez vérifier vous-même, et celui sur lequel un opticien de quartier peut agir concrètement.</p>

<h2>Que recouvrent l'acétate biosourcé et le plastique recyclé ?</h2>
<p>L'acétate de cellulose est déjà, par nature, dérivé de matières végétales. Ce que les gammes dites biosourcées changent, c'est la composition des additifs et l'origine revendiquée des matières premières. Le fabricant italien Mazzucchelli 1849, référence historique de l'acétate haut de gamme qui fournit une grande partie de l'industrie du luxe, a ainsi développé des gammes composées en majorité de coton et de bois certifiés, selon les informations communiquées par l'entreprise. Cette matière irrigue aujourd'hui de nombreuses collections, des maisons indépendantes jusqu'aux grands groupes de licence.</p>
<p>Le plastique recyclé, lui, consiste à réintroduire de la matière déjà produite plutôt que d'en fabriquer de la neuve. Le principe est solide, mais il faut résister à la tentation d'en tirer des conclusions chiffrées : la proportion de matière recyclée, son origine et le procédé varient d'un modèle à l'autre, et seul le fabricant peut les documenter. Nous évitons donc de comparer deux montures sur ce terrain sans les fiches produits sous les yeux.</p>

<h3>Ce que ces matières ne changent pas</h3>
<p>Ni le biosourcé ni le recyclé ne modifient l'essentiel : la qualité des charnières, la tenue du face dans le temps, la précision de l'ajustage sur le visage. Une monture responsable mal dessinée reste une monture inconfortable. Inversement, ces matières n'imposent aucun sacrifice esthétique : les collections en acétate biosourcé offrent la même richesse de couleurs et de finitions que les acétates classiques, ce qui n'était pas gagné il y a quelques années.</p>

<h2>Quelles marques portent ce mouvement aujourd'hui ?</h2>
<p>Ce sont surtout les indépendants qui en ont fait leur signature. La maison italienne Andy Brook, fabriquée artisanalement dans la région de Belluno, berceau historique de la lunetterie italienne, revalorise les chutes d'acétate et travaille en séries limitées pour limiter le gaspillage de matière. La marque suédoise CHIMI, devenue un phénomène sur les réseaux sociaux avec ses formes rondes minimalistes et ses teintes pastel, a fait le choix de l'acétate biosourcé et d'un packaging réduit. En France, LOOL Eyewear, fondée à Paris, travaille le plastique recyclé et propose un service de réparation pensé pour allonger la durée de vie des montures.</p>
<p>Le mouvement ne se limite plus à ces petites structures. Les grandes licences d'optique — Thélios pour les maisons du groupe LVMH comme Fendi, Loewe ou Céline, EssilorLuxottica pour Ray-Ban ou Armani, Kering Eyewear pour Gucci ou Saint Laurent — communiquent désormais plus ouvertement sur l'origine de leurs acétates, la traçabilité des métaux employés pour les branches et les charnières, ou la réduction des emballages. Ces engagements émanent des groupes eux-mêmes et n'ont pas la même portée qu'une certification indépendante. Le sujet reste perfectible, mais la direction est prise, et les clients y sont manifestement attentifs au moment de choisir.</p>

<h2>Comment distinguer une démarche sérieuse d'un argument marketing ?</h2>
<p>C'est là que se joue l'essentiel, et nous n'avons pas de recette infaillible à proposer. Quelques questions permettent toutefois de faire le tri assez vite.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Ce que vous lisez</th><th>Ce que cela dit vraiment</th><th>Ce qu'il faut demander</th></tr>
    </thead>
    <tbody>
      <tr><td>« Acétate biosourcé »</td><td>Une matière dont l'origine est revendiquée par le fabricant</td><td>Quelle gamme précise, et documentée par qui</td></tr>
      <tr><td>« Matériaux recyclés »</td><td>Une part de matière réemployée, dont la proportion varie</td><td>Sur quelle pièce : le face, les branches, l'étui</td></tr>
      <tr><td>« Fabriqué en Europe »</td><td>Un lieu d'assemblage, pas toujours d'origine des matières</td><td>Quelle étape est réalisée où</td></tr>
      <tr><td>« Marque engagée »</td><td>Une formulation libre, sans définition réglementaire</td><td>Quel engagement concret, sur quoi</td></tr>
      <tr><td>« Monture réparable »</td><td>Le critère le plus vérifiable de tous</td><td>Les pièces détachées sont-elles disponibles, et combien de temps</td></tr>
    </tbody>
  </table>
</div>
<p>Un mot d'honnêteté sur notre position : en tant que revendeurs, nous relayons ce que les marques nous communiquent, et nous ne disposons pas des moyens d'auditer une chaîne de production. Nous pouvons en revanche vous dire quelles montures nous voyons revenir en réparation, lesquelles se démontent bien, et pour lesquelles nous obtenons encore des pièces plusieurs années après l'achat. C'est une information moins spectaculaire qu'un argumentaire, mais elle est de première main.</p>

<h2>Comment faire durer ses lunettes plus longtemps ?</h2>
<p>Aucune matière ne rivalise avec une paire que l'on garde. Voici les gestes qui allongent le plus efficacement la vie d'une monture, du plus utile au plus accessoire.</p>
<ol>
  <li><strong>Retirez vos lunettes à deux mains.</strong> C'est le geste qui use les charnières et détend le face plus vite que tout le reste, et le plus simple à corriger.</li>
  <li><strong>Rangez-les dans leur étui</strong> plutôt que posées verres contre la table ou glissées dans un sac. Les rayures profondes condamnent un verre bien avant que la monture ne fatigue.</li>
  <li><strong>Nettoyez à l'eau tiède et au savon doux</strong>, puis séchez avec un chiffon microfibre propre. Les mouchoirs en papier et les produits ménagers abîment les traitements de surface.</li>
  <li><strong>Faites resserrer et réaligner régulièrement.</strong> Une visite de quelques minutes chez votre opticien évite qu'une vis desserrée ne devienne une branche cassée.</li>
  <li><strong>Envisagez de remonter des verres neufs</strong> sur une monture que vous aimez toujours, si son état le permet. C'est souvent la solution la plus sobre lors d'un changement de correction.</li>
</ol>

<h2>Où voir ces collections et en parler tranquillement ?</h2>
<p>Nous aimons présenter ces alternatives aux côtés des maisons historiques, sans les isoler dans un rayon à part et sans en faire un argument de vente. Une monture responsable se choisit comme une autre : parce que sa forme vous va, parce qu'elle est confortable, et parce que vous avez envie de la porter. Le reste est un bonus, pas une raison suffisante d'acheter.</p>
<p>Dans notre boutique de la Galerie Oslo, sur l'Esplanade des Olympiades, vous pouvez venir essayer ces modèles sans rendez-vous, poser vos questions sur leur composition et repartir sans rien décider. Nous vous dirons ce que nous savons, et aussi ce que nous ignorons — ce qui, sur ce sujet, arrive souvent. Et si votre paire actuelle a simplement besoin d'un réglage ou d'une réparation, passez : c'est encore le geste le plus écologique que nous puissions vous proposer.</p>
"""

ART_BODY_JOURNEE_TYPE = """<h2>À quoi ressemble le début d'une journée en boutique ?</h2>
<p>Il est un peu avant dix heures quand le rideau de la Galerie Oslo se lève. Les commerces voisins ouvrent les uns après les autres, l'esplanade s'anime doucement, et nous disposons de quelques minutes avant les premiers clients. Ce temps-là n'a rien de décoratif : chaque monture est remise droite sur son présentoir, les paires essayées la veille retrouvent leur place, les commandes arrivées sont contrôlées et nous faisons le point sur les rendez-vous de la journée. C'est le seul moment où la boutique nous appartient vraiment, avant qu'elle ne se remplisse de conversations.</p>

<h3>Deux journées ne se ressemblent jamais</h3>
<p>Entre dix heures et dix-neuf heures trente, du mardi au samedi, le rythme est imprévisible. Certains jours, ce sont surtout des habitués qui passent dire bonjour en récupérant une paire réparée, et l'après-midi ressemble à une suite de conversations. D'autres jours, ce sont des visages nouveaux, poussés par une ordonnance qui arrive à expiration, par une paire cassée le matin même ou simplement par l'envie de changer de style. Nous ne cherchons pas à lisser ces variations : une boutique de quartier vit au rythme de ceux qui y entrent.</p>

<h2>Pourquoi un essayage prend-il autant de temps chez nous ?</h2>
<p>C'est une remarque qui revient souvent, parfois avec un peu de surprise. La réponse tient en une phrase : une monture n'est pas un objet qu'on pose sur un nez, c'est un objet qu'on porte à quelques centimètres de son visage, toute la journée, pendant plusieurs années. Un choix expédié en dix minutes se paie ensuite en inconfort, en paire qui glisse, ou en lunettes qui finissent dans un tiroir. Prendre trente minutes de plus au moment de choisir nous paraît un meilleur échange.</p>

<h3>Regarder le visage, mais aussi les gestes</h3>
<p>Nous observons évidemment la morphologie : la largeur du visage, la hauteur du nez, la position des oreilles, la façon dont la monture se pose. Mais nous regardons tout autant comment la personne bouge, parle, sourit avec ses lunettes sur le nez. Une monture qui semble parfaite devant le miroir peut ne plus rien vouloir dire dès que son porteur redevient lui-même. Avec dix-neuf marques en boutique, de Ray-Ban à Dior en passant par Andy Brook ou CHIMI, il y a presque toujours plusieurs pistes crédibles pour une même envie. Notre rôle n'est pas d'orienter vers une marque plutôt qu'une autre, mais d'aider chacun à se reconnaître dans la glace.</p>

<h2>Que se passe-t-il quand on arrive avec une ordonnance ?</h2>
<p>C'est le cas de figure le plus fréquent de la journée. Le déroulé varie peu, et il aide à comprendre pourquoi une commande de lunettes ne se règle pas en cinq minutes au comptoir.</p>
<ol>
  <li><strong>Nous lisons l'ordonnance avec vous.</strong> Sa date, sa durée de validité, ce qu'elle prévoit pour la vision de loin et de près : autant de points que nous reprenons à voix haute plutôt que de les garder pour nous.</li>
  <li><strong>Nous parlons de votre usage réel.</strong> Écran toute la journée, conduite de nuit, lecture, travail manuel : c'est cet usage qui détermine le type de verres, bien plus que la correction elle-même.</li>
  <li><strong>Vient l'essayage des montures</strong>, en tenant compte de la correction : certaines formes conviennent mal à des verres épais, et il vaut mieux le savoir avant de tomber amoureux d'un modèle.</li>
  <li><strong>Nous prenons les mesures</strong> une fois la monture choisie et préréglée sur le visage : écart pupillaire, hauteur de montage, angles. Un verre parfaitement calculé mais mal centré reste un verre inconfortable.</li>
  <li><strong>Nous établissons un devis détaillé</strong>, avec l'offre 100 % Santé et ce qui restera éventuellement à votre charge. Vous repartez avec, libre de comparer.</li>
</ol>

<h2>Et l'audition, quelle place prend-elle dans la journée ?</h2>
<p>Une partie de nos journées se passe à l'écart du magasin, dans le calme nécessaire à un bilan auditif. Ces créneaux se prennent sur rendez-vous, parce qu'ils demandent du temps et de l'attention : mesures, explications, essais, puis réglages fins au fil des semaines. Un accompagnement auditif ne se juge pas le jour de la vente mais plusieurs mois après, quand les appareils sont portés sans y penser. Nous rappelons systématiquement qu'un appareillage se fait après avis médical, et qu'une baisse d'audition brutale ou douloureuse relève de l'ORL, pas de nous.</p>

<h2>Que fait-on en fin de journée ?</h2>
<p>Le soir amène presque toujours son lot de petits gestes : une branche à resserrer, une plaquette à changer, une paire qui a pris un mauvais coup dans un sac. Ce sont des interventions de quelques minutes, souvent réalisées pendant que la personne attend debout devant le comptoir, et nous ne les refusons jamais. Elles font autant partie du métier que la vente elle-même. C'est d'ailleurs souvent là, sur ces réparations sans facture, que se construit la confiance qui ramène les gens d'une année sur l'autre.</p>

<h2>Faut-il prendre rendez-vous pour passer nous voir ?</h2>
<p>Pas pour tout. Un essayage, un ajustage, une question sur un devis ou un contrôle de la vue peuvent se faire en passant, dans notre coin du 13e, Galerie Oslo. Pour un bilan auditif ou un suivi d'appareillage, en revanche, mieux vaut réserver un créneau : c'est la seule façon de vous garantir le temps et le calme que ces rendez-vous demandent. Dans tous les cas, venir sans rien acheter est parfaitement normal, et c'est même souvent comme cela que commencent les relations les plus longues.</p>
"""

ART_BODY_NOUVEL_AN_LUNAIRE = """<h2>Pourquoi ce moment de l'année change-t-il le rythme du quartier ?</h2>
<p>Il y a des périodes dans l'année où le Triangle de Choisy ne fonctionne plus tout à fait de la même manière, et le Nouvel An lunaire en fait clairement partie. Les vitrines se parent de rouge et d'or, les commerces sortent leurs décorations, et l'esplanade des Olympiades, juste à côté de notre boutique, prend des allures de place de fête. Les odeurs qui montent de chez Tang Frères et des restaurants voisins changent, les allées se remplissent plus tôt dans la journée, et l'on sent qu'un pan entier du quartier se retrouve autour de cette date. Ce n'est pas un décor posé pour l'occasion : c'est un rythme de vie qui remonte à la surface.</p>

<h3>Une histoire longue, inscrite dans les tours</h3>
<p>Cette présence tient à l'histoire du quartier. L'immigration originaire d'Asie du Sud-Est s'y est installée à partir de la fin des années 1970, dans un ensemble de tours et de dalles alors récemment construit, et elle y a progressivement bâti des commerces, des associations, des habitudes. Le Nouvel An lunaire n'est donc pas une animation commerciale plaquée sur un arrondissement : c'est une fête familiale qui déborde dans l'espace public parce que les familles qui la célèbrent vivent ici depuis plusieurs générations. Nous nous gardons bien d'en faire une carte postale : ce sont des trajectoires personnelles, pas un folklore.</p>

<h2>Que voit-on depuis une boutique pendant ces quelques jours ?</h2>
<p>Concrètement, le Nouvel An lunaire se traduit d'abord par du monde en plus dans la Galerie Oslo. Des familles qui font leurs courses de fête s'arrêtent parfois simplement pour jeter un œil aux montures exposées, sans intention d'acheter quoi que ce soit, et c'est très bien ainsi. Des clients habituels passent nous souhaiter une bonne année en même temps qu'ils viennent chercher une paire commandée. Et la conversation au comptoir dérive presque toujours vers les préparatifs, les repas prévus, les proches que l'on attend ou ceux que l'on ne verra pas cette année.</p>

<h3>Des conversations qui durent un peu plus</h3>
<p>C'est sans doute le changement le plus net de cette période : le temps s'étire. Un ajustage de branches qui prend d'ordinaire trois minutes en prend dix, parce qu'on parle d'autre chose entre-temps. Une remise de lunettes devient l'occasion de prendre des nouvelles d'un parent qui n'est pas venu depuis des mois. Nous ne cherchons pas à comprimer ces moments-là : dans un métier où l'on touche le visage des gens et où l'on revient chaque année ou presque, ces conversations font partie du travail autant que les mesures.</p>

<h2>Comment un commerce comme le nôtre s'associe-t-il à la fête ?</h2>
<p>Avec beaucoup de modestie, en réalité. Nous ne sommes pas organisateurs, et nous n'avons aucune légitimité à l'être. Ce que nous pouvons faire tient à peu de choses, mais ces peu de choses comptent pour un commerce de proximité.</p>
<ol>
  <li><strong>Soigner la vitrine.</strong> Une devanture qui accompagne les couleurs de la période, sans surcharge et sans emprunter des symboles dont nous ne maîtriserions pas le sens.</li>
  <li><strong>Rester disponibles pour les petits gestes.</strong> Un resserrage, un changement de plaquettes, une paire tordue rattrapée en cinq minutes : c'est la demande la plus fréquente quand le quartier est en mouvement.</li>
  <li><strong>Adapter notre présence au comptoir.</strong> Les allées se remplissent plus tôt, donc nous évitons de programmer les rendez-vous longs aux heures les plus denses.</li>
  <li><strong>Accueillir ceux qui entrent sans rien demander.</strong> Une partie des visites de cette période n'a aucun objet précis, et il n'y a rien à corriger là-dedans.</li>
  <li><strong>Faire circuler l'information.</strong> Indiquer un commerce voisin, une sortie de galerie, un horaire : c'est souvent le service le plus utile que nous rendions ces jours-là.</li>
</ol>

<h2>Pourquoi tenons-nous à ce quartier plutôt qu'à un autre ?</h2>
<p>Nous n'avons jamais souhaité être une boutique qui se contente d'exister dans le 13e sans vraiment y appartenir. Quand nous avons ouvert Maison Mikis en 2023, le choix de nous installer ici n'avait rien d'un calcul d'emplacement : nous voulions un endroit où l'on croise deux fois la même personne dans la semaine, où l'on connaît le nom des commerçants d'à côté, et où une boutique d'optique n'est pas seulement un point de vente. Le Nouvel An lunaire est le rappel annuel le plus évident de ce choix. Notre clientèle ressemble au quartier : mélangée, fidèle, attachée à ses habitudes autant qu'à ses fêtes.</p>
<p>Cela a des conséquences très concrètes sur notre façon de travailler. Nous prenons le temps d'expliquer, y compris quand l'échange se fait dans un français hésitant ou avec l'aide d'un proche venu traduire. Nous préférons perdre une vente que laisser repartir quelqu'un avec un équipement qu'il n'a pas compris. Et nous savons que la confiance, ici, se construit sur des années, pas sur une opération commerciale.</p>

<h2>Que se passe-t-il chez nous à cette période ?</h2>
<p>Rien d'exceptionnel, et c'est volontaire. La boutique reste ouverte à ses horaires habituels, au 44 avenue d'Ivry, à deux pas de l'esplanade, et vous pouvez passer comme les autres semaines de l'année : essayer des montures sans rendez-vous, faire réajuster une paire qui glisse, demander un devis, ou faire un contrôle de la vue pour savoir où vous en êtes. Pour un bilan auditif, mieux vaut en revanche réserver un créneau, car ces rendez-vous demandent du calme, ce qui n'est pas la qualité première d'une galerie commerçante un jour de fête.</p>
<p>Si vous flânez dans les allées ces jours-là, poussez la porte même sans motif. Nous prenons plaisir à voir la rue se colorer, à entendre la musique qui s'échappe de l'esplanade, et à accueillir entre deux essayages des gens venus simplement partager un peu de cette effervescence. C'est, chaque année, l'un des meilleurs moments de notre calendrier, et il ne nous appartient pas : il appartient au quartier.</p>
"""

ART_BODY_ECRANS_MYOPIE_ENFANT = """<h2>Pourquoi la myopie touche-t-elle de plus en plus d'enfants ?</h2>
<p>Depuis une vingtaine d'années, les ophtalmologistes observent une hausse régulière du nombre de jeunes myopes, en France comme dans la plupart des pays industrialisés. Ce n'est pas une impression de comptoir : c'est un constat partagé par les sociétés savantes d'ophtalmologie, qui l'attribuent à deux évolutions parallèles de nos modes de vie. D'un côté, les activités de près se sont multipliées, écrans, tablettes et lecture confondus. De l'autre, le temps passé dehors, en lumière naturelle, a nettement reculé. Aucun de ces deux facteurs n'explique tout à lui seul, mais leur combinaison pèse.</p>
<h3>Ce qui se passe dans l'œil</h3>
<p>Un œil myope est un œil devenu un peu trop long : l'image se forme en avant de la rétine au lieu de se former dessus, et la vision de loin devient floue. Cet allongement se produit surtout pendant la croissance, ce qui explique le calendrier habituel du trouble : il apparaît le plus souvent entre 6 et 12 ans et tend, une fois installé, à progresser jusqu'à la fin de l'adolescence avant de se stabiliser. Rien de tout cela n'est irréversible sur le plan du confort, puisqu'une correction rétablit une vision nette. L'objectif du suivi est ailleurs : limiter autant que possible la progression pendant les années de croissance.</p>
<h3>Le rôle de l'hérédité</h3>
<p>La part familiale est réelle et bien connue. Un enfant dont l'un des parents est myope a davantage de risques de le devenir, et cette probabilité augmente encore lorsque les deux parents le sont. Ce n'est pas une fatalité, et ce n'est surtout pas une raison de culpabiliser : cela signifie simplement qu'il vaut la peine, dans ces familles, de faire contrôler la vue plus régulièrement et de soigner davantage les habitudes du quotidien.</p>

<h2>Le temps passé dehors protège-t-il vraiment la vue ?</h2>
<p>C'est le point qui surprend le plus les parents, et c'est pourtant le mieux documenté. Plusieurs travaux relayés par la communauté ophtalmologique montrent que l'exposition à la lumière naturelle stimule la libération de dopamine au niveau de la rétine, un mécanisme qui freinerait l'élongation excessive du globe oculaire. Autrement dit, un enfant qui joue dehors une à deux heures par jour, même sans pratiquer de sport particulier, protège davantage sa vue qu'un enfant resté à l'intérieur, écran ou pas. L'intensité lumineuse extérieure, même par temps couvert, n'a aucun équivalent dans un salon ou une salle de classe.</p>
<p>C'est aussi la recommandation la plus facile à appliquer, parce qu'elle n'oblige à interdire quoi que ce soit. Le trajet à pied vers l'école, le goûter au square, le mercredi après-midi au parc comptent autant qu'une activité encadrée. Beaucoup de familles des Olympiades nous disent manquer d'espace vert : le simple fait de faire les devoirs près d'une fenêtre, puis de sortir marcher avant le dîner, change déjà la donne.</p>

<h2>Quelles habitudes adopter à la maison ?</h2>
<p>Voici les repères que nous donnons le plus souvent aux parents, du plus utile au plus accessoire. Aucun ne demande d'équipement particulier.</p>
<ol>
  <li><strong>Sortir tous les jours</strong>, même brièvement, et privilégier l'extérieur chaque fois qu'une activité peut s'y transporter.</li>
  <li><strong>Faire une pause toutes les 20 minutes</strong> pendant les devoirs ou les écrans, en regardant au loin une vingtaine de secondes. Le muscle de la mise au point se relâche.</li>
  <li><strong>Surveiller la distance de lecture.</strong> Un livre ou une tablette collés au visage sollicitent l'œil bien davantage qu'un support tenu à distance du coude.</li>
  <li><strong>Éclairer correctement la pièce</strong> pendant la lecture et les devoirs : lire dans la pénombre pousse l'enfant à se rapprocher de son support.</li>
  <li><strong>Éviter les écrans le soir avant le coucher</strong>, pour le sommeil autant que pour le confort visuel.</li>
  <li><strong>Pas d'écran avant 3 ans</strong>, conformément aux recommandations des autorités de santé.</li>
</ol>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Habitude</th><th>Pourquoi elle compte</th><th>Repère simple</th></tr>
    </thead>
    <tbody>
      <tr><td>Jeu à l'extérieur</td><td>Lumière naturelle et vision de loin sollicitée</td><td>Une à deux heures par jour, fractionnables</td></tr>
      <tr><td>Pauses pendant les devoirs</td><td>Relâche l'effort de mise au point de près</td><td>Regarder au loin toutes les 20 minutes</td></tr>
      <tr><td>Distance de lecture</td><td>Plus le support est près, plus l'œil force</td><td>Environ la longueur de l'avant-bras</td></tr>
      <tr><td>Lumière de la pièce</td><td>Évite le rapprochement automatique du support</td><td>Lumière du jour ou lampe de bureau dédiée</td></tr>
      <tr><td>Écrans en soirée</td><td>Sommeil et confort visuel</td><td>Arrêt avant le rituel du coucher</td></tr>
      <tr><td>Avant 3 ans</td><td>Période clé du développement visuel</td><td>Pas d'écran</td></tr>
    </tbody>
  </table>
</div>

<h2>Faut-il consulter même si l'enfant ne se plaint de rien ?</h2>
<p>Oui, et c'est le message principal de cet article. Un enfant myope non corrigé ne se plaint presque jamais, parce qu'il n'a jamais connu autre chose : il s'habitue à voir flou de loin et développe des stratégies de compensation qui rendent le trouble invisible à la maison. Le flou se remarque plutôt à l'école, quand il faut copier un tableau, ou en extérieur, quand il ne reconnaît pas un camarade à distance. Un contrôle régulier chez l'ophtalmologiste, même en l'absence de symptôme, reste donc précieux — particulièrement si l'un des parents est lui-même concerné.</p>
<p>Si une myopie est confirmée, sachez que le suivi ne se limite plus à changer de verres quand la vue baisse. Des approches destinées à freiner la progression pendant la croissance existent aujourd'hui ; elles relèvent d'une prescription et d'un suivi médical, et c'est l'ophtalmologiste qui juge de leur pertinence pour un enfant donné. Notre rôle, en boutique, est de réaliser l'équipement et d'assurer les contrôles intermédiaires.</p>

<h2>Comment faire pour qu'un enfant porte réellement ses lunettes ?</h2>
<p>C'est la difficulté quotidienne dont les parents nous parlent le plus, et elle se joue en grande partie au moment du choix. Une paire rejetée finit dans le cartable ; une paire choisie par l'enfant se porte sans discussion. Nous laissons donc essayer largement, nous expliquons chaque étape avec des mots simples, et nous orientons vers des montures pensées pour un usage actif : matières souples, charnières résistantes, branches qui tiennent pendant la récréation. Le réglage compte autant que le modèle, et il se refait aussi souvent que nécessaire.</p>
<p>Nous sommes installés Galerie Oslo, sur l'Esplanade des Olympiades, et nous accueillons volontiers les familles pour un simple ajustement, un contrôle intermédiaire ou une question sur une ordonnance. Aucun rendez-vous n'est nécessaire, et venir demander conseil n'engage à rien.</p>
"""

ART_BODY_OTITES_ENFANT = """<h2>Pourquoi les otites sont-elles si fréquentes avant 3 ans ?</h2>
<p>L'otite moyenne aiguë figure parmi les infections les plus courantes de la petite enfance, avec un pic de fréquence entre 6 mois et 2 ans. Presque tous les tout-petits en font au moins une, et cela n'a rien d'anormal. Dans la grande majorité des cas, une otite bien prise en charge guérit sans laisser la moindre trace. Ce n'est donc pas l'épisode isolé qui doit retenir l'attention des parents, mais sa répétition ou son évolution vers une forme traînante.</p>

<h3>Une trompe d'Eustache encore immature</h3>
<p>La trompe d'Eustache relie l'oreille moyenne au fond de la gorge et sert à équilibrer les pressions et à évacuer les sécrétions. Chez le jeune enfant, elle est encore courte et pratiquement horizontale, ce qui la rend beaucoup moins efficace pour drainer l'oreille moyenne. Le moindre rhume suffit alors à faire remonter des sécrétions et à créer les conditions d'une otite. Cette anatomie évolue avec la croissance, et c'est en grande partie pour cela que les otites se raréfient spontanément en grandissant.</p>

<h3>Les facteurs qui favorisent les récidives</h3>
<p>Certains éléments reviennent régulièrement dans les histoires d'otites à répétition : la vie en collectivité, la crèche en particulier, qui multiplie les contacts avec les virus hivernaux ; le tabagisme passif, qui irrite les muqueuses respiratoires ; l'usage prolongé de la tétine au-delà des premiers mois. Aucun de ces facteurs ne provoque à lui seul une otite, et beaucoup d'enfants exposés n'en font jamais. Ils augmentent simplement la probabilité d'épisodes répétés, et deux d'entre eux au moins peuvent être réduits.</p>

<h2>Pourquoi une otite fait-elle baisser l'audition ?</h2>
<p>Pendant un épisode d'otite, du liquide s'accumule derrière le tympan. Cette membrane et les petits osselets qui lui font suite ne peuvent plus vibrer librement : la transmission des sons est amortie, comme lorsque l'on a les oreilles bouchées en avion ou sous l'eau. L'enfant n'est pas sourd, il entend moins bien et surtout moins nettement, en particulier les sons aigus et les consonnes. Cette baisse est en règle générale temporaire et disparaît avec la guérison.</p>
<p>La situation change lorsque les otites se succèdent ou que l'épanchement persiste plusieurs semaines après la fin de l'infection — ce que l'on appelle une otite séreuse ou séromuqueuse. L'audition reste alors affaiblie sur une période prolongée, souvent sans douleur ni fièvre, donc sans rien qui alerte les parents. C'est cette forme silencieuse, plus que l'otite aiguë bruyante, qui justifie une vérification.</p>

<h2>Les otites à répétition peuvent-elles retarder le langage ?</h2>
<p>Entre 1 et 3 ans, un enfant construit les bases de sa langue maternelle en s'appuyant presque exclusivement sur ce qu'il entend. Il repère les sons, les imite, les associe à des objets, affine peu à peu sa prononciation. Si l'audition fluctue pendant cette période — nette une semaine, feutrée la suivante — le matériau sonore sur lequel il travaille devient instable. C'est de là que vient le lien entre otites répétées et acquisition du langage.</p>
<p>Il faut cependant garder la mesure des choses. La plupart des enfants qui enchaînent quelques otites développent un langage tout à fait normal, et un retard de langage a bien d'autres causes possibles qu'une histoire d'oreilles. L'idée n'est pas d'établir un lien de cause à effet, mais de ne pas passer à côté d'une audition durablement diminuée à l'âge précis où elle compte le plus. Lorsqu'un doute existe, mieux vaut le lever par un examen que le laisser courir.</p>

<h2>Quels signes doivent faire vérifier l'audition d'un enfant ?</h2>
<p>Les jeunes enfants ne se plaignent presque jamais de mal entendre : ils s'adaptent, se rapprochent, observent les visages. Ce sont donc des changements de comportement qu'il faut repérer, plus qu'une plainte.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Ce que vous observez</th><th>Ce que cela peut traduire</th><th>Quoi faire</th></tr>
    </thead>
    <tbody>
      <tr><td>Il ne réagit pas quand on l'appelle de loin ou hors de son champ de vision</td><td>Audition possiblement diminuée par un épanchement</td><td>En parler au médecin traitant ou au pédiatre</td></tr>
      <tr><td>Il monte le son de la télévision, fait répéter souvent</td><td>Baisse de perception, surtout sur les aigus</td><td>Noter depuis quand, en parler à la consultation suivante</td></tr>
      <tr><td>Son langage stagne, sa prononciation reste peu claire</td><td>Retentissement possible d'une audition fluctuante</td><td>Avis médical, orientation vers un orthophoniste si besoin</td></tr>
      <tr><td>Plus de 3 à 4 otites en six mois</td><td>Forme récidivante à documenter</td><td>Consultation, avis ORL généralement proposé</td></tr>
      <tr><td>Un épanchement connu qui dure au-delà de trois mois</td><td>Otite séromuqueuse persistante</td><td>Contrôle ORL avec examen du tympan et audiogramme</td></tr>
      <tr><td>Oreille douloureuse, fièvre, écoulement</td><td>Otite en cours</td><td>Consulter un médecin sans attendre</td></tr>
    </tbody>
  </table>
</div>

<h2>Comment se déroule un audiogramme chez un jeune enfant ?</h2>
<p>La question inquiète souvent les parents, à tort : rien dans cet examen n'est douloureux ni impressionnant. Les techniques sont adaptées à l'âge et prennent presque toujours la forme d'un jeu, ce qui explique qu'un enfant de 3 ans puisse être testé de façon fiable. Voici comment se déroule en général le parcours.</p>
<ol>
  <li><strong>Le médecin traitant ou le pédiatre fait le point</strong> sur le nombre d'épisodes, leur date et le comportement de l'enfant à la maison. C'est le point de départ.</li>
  <li><strong>Un examen du tympan</strong> permet de voir l'état de la membrane et de rechercher du liquide derrière elle.</li>
  <li><strong>L'ORL complète si nécessaire</strong> par une mesure de la souplesse du tympan, qui objective un épanchement même en l'absence de symptômes.</li>
  <li><strong>L'audiogramme adapté à l'âge</strong> mesure les seuils oreille par oreille : l'enfant tourne la tête vers un son, place un jeton dans une boîte au signal, ou répond à des mots simples selon son niveau.</li>
  <li><strong>Un suivi est proposé</strong> si l'audition est diminuée : contrôle à distance après guérison, et bilan orthophonique lorsque le langage semble concerné.</li>
</ol>
<p>Un point mérite d'être précisé : la prise en charge d'un enfant qui fait des otites relève du médecin et de l'ORL, pas de l'audioprothésiste. Nous n'établissons aucun diagnostic et ne prenons jamais le relais d'un suivi médical en cours.</p>

<h2>Quand faut-il s'inquiéter, et vers qui se tourner ?</h2>
<p>Il ne s'agit pas de s'alarmer à la première otite. La plupart des enfants en font plusieurs sans aucune conséquence durable sur leur audition ni sur leur développement. L'objectif est simplement de ne pas laisser s'installer une situation d'otites répétées sans jamais avoir fait vérifier l'audition, en particulier à l'approche de l'entrée en maternelle, période charnière pour le langage et les apprentissages. En cas de doute, le médecin traitant ou le pédiatre reste le premier interlocuteur et orientera vers un ORL si l'examen le justifie.</p>
<p>À Maison Mikis, Galerie Oslo sur l'Esplanade des Olympiades, beaucoup de parents du quartier nous posent la question au comptoir, souvent en venant pour tout autre chose. Nous prenons le temps d'y répondre et d'expliquer ce qui distingue une gêne passagère d'une situation à faire examiner, puis nous renvoyons vers le médecin quand c'est nécessaire. C'est le rôle que nous nous donnons sur ce sujet : informer clairement, et aider les familles à ne pas rester dans le doute.</p>
"""

ARTICLES = [
    {
        "slug": "fatigue-oculaire-ecrans",
        "category": "sante-visuelle",
        "title": "Écrans et fatigue oculaire : comment protéger sa vue au quotidien",
        "meta_title": "Fatigue oculaire et écrans : que faire ? | Maison Mikis",
        "meta_description": "Sécheresse, maux de tête, vision brouillée : les causes réelles de la fatigue visuelle sur écran, ce que valent les verres anti-lumière bleue et ce qui aide.",
        "excerpt": "Sécheresse, maux de tête, vision qui se brouille : pourquoi les écrans fatiguent nos yeux, et ce qui aide vraiment.",
        "answer": "La fatigue oculaire sur écran vient de deux causes : on cligne des yeux jusqu'à 60&nbsp;% moins souvent, ce qui assèche le film lacrymal, et le muscle d'accommodation reste contracté des heures. La lumière bleue n'en est pas la cause principale. Pauses 20-20-20, écran à 50-70&nbsp;cm et correction à jour suffisent dans la plupart des cas.",
        "faq": [
            ("Combien de temps faut-il pour que la fatigue oculaire disparaisse ?",
             "Avec de bons réglages — pauses régulières, écran reculé, larmes artificielles — la plupart des gens ressentent une nette amélioration en une à deux semaines. Si rien ne bouge au bout de trois semaines, la cause est probablement optique : correction inadaptée, astigmatisme non corrigé ou presbytie qui démarre."),
            ("Les écrans peuvent-ils abîmer définitivement les yeux ?",
             "Chez l'adulte, aucune donnée ne montre que le travail sur écran provoque une lésion durable : la fatigue visuelle est réversible. Chez l'enfant, c'est différent — le temps passé en vision de près et le manque de lumière du jour favorisent la progression de la myopie."),
            ("Faut-il des lunettes spéciales pour l'ordinateur ?",
             "Pas systématiquement avant 40 ans, si la correction est à jour. Après 40-45 ans, des verres à faible dégression, dits verres bureau, élargissent la zone nette entre 40&nbsp;cm et 2&nbsp;m : c'est souvent un vrai soulagement pour ceux qui alternent écran, clavier et échanges en face à face."),
            ("Le mode nuit de mon téléphone remplace-t-il un verre traité ?",
             "Le mode nuit réduit la lumière bleue émise en soirée, ce qui peut aider au sommeil. Il n'agit pas sur la fatigue visuelle, dont la cause est ailleurs. C'est le traitement antireflet des verres, et non le filtre bleu, qui apporte un gain de confort mesurable devant un écran."),
            ("Peut-on utiliser des larmes artificielles tous les jours ?",
             "Oui, à condition de choisir une formule sans conservateur, en unidoses ou en flacon à valve stérile. Utilisés plusieurs fois par jour pendant des mois, les conservateurs finissent par irriter la surface de l'œil. Si la sécheresse persiste malgré cela, un avis ophtalmologique est préférable."),
        ],
        "sources": [
            ("Asnav", "https://www.asnav.org/"),
            ("INRS — travail sur écran", "https://www.inrs.fr/risques/travail-ecran.html"),
            ("Ameli.fr", "https://www.ameli.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/sante/conseils-fatigue-oculaire.jpg",
        "image_alt": "Personne se frottant les yeux, fatigue oculaire liée aux écrans",
        "date_display": "26 juillet 2026",
        "date_iso": "2026-07-26",
        "body": ART_BODY_FATIGUE,
    },
    {
        "slug": "perte-auditive-signes-precoces",
        "category": "sante-auditive",
        "title": "Perte auditive silencieuse : les signes à ne pas ignorer",
        "meta_title": "Perte auditive : les signes à repérer tôt | Maison Mikis",
        "meta_description": "Faire répéter, monter la télévision, décrocher au restaurant : les premiers signes d'une baisse d'audition sont discrets. Comment les reconnaître à temps.",
        "excerpt": "En France, 7 à 10 ans s'écoulent en moyenne avant la première consultation. Voici les signaux à repérer bien plus tôt.",
        "answer": "Les premiers signes d'une perte auditive sont rarement le silence : ce sont la difficulté à suivre une conversation en groupe, le besoin de faire répéter, la télévision montée cran par cran et une fatigue inhabituelle après une journée de réunions. Un contrôle de l'audition permet de lever le doute rapidement.",
        "faq": [
            ("Un bilan auditif est-il payant chez l'audioprothésiste ?",
             "Non, le contrôle de l'audition réalisé chez un audioprothésiste est gratuit et n'engage à rien. Il n'a pas valeur de diagnostic médical : seule la prescription d'un appareillage nécessite ensuite une ordonnance du médecin traitant ou de l'ORL. Vous repartez avec vos résultats commentés, que vous donniez suite ou non."),
            ("Faut-il une ordonnance pour faire contrôler son audition ?",
             "Aucune ordonnance n'est nécessaire pour un simple contrôle chez l'audioprothésiste. Elle devient obligatoire dès qu'un appareillage est envisagé, car la prescription relève du médecin traitant ou de l'ORL. Ce contrôle préalable sert justement à savoir s'il y a lieu de consulter, et avec quels éléments."),
            ("Peut-on perdre l'audition d'un seul côté ?",
             "Oui, et cette asymétrie doit être prise au sérieux. Une baisse installée d'un seul côté mérite un avis médical, et une perte survenue brutalement en quelques heures constitue une urgence : il faut consulter un médecin ou un ORL sans attendre."),
            ("À partir de quel âge faut-il faire vérifier son audition ?",
             "L'Organisation mondiale de la santé recommande un dépistage systématique dès 60 ans. Pour les personnes exposées au bruit dans leur métier, un premier contrôle est proposé dès 45-50 ans par la médecine du travail, et se justifie plus tôt en cas de gêne."),
            ("Les tests d'audition en ligne sont-ils fiables ?",
             "Ils donnent une orientation, pas une mesure. Le résultat dépend beaucoup du casque utilisé et du bruit ambiant de la pièce, et ils évaluent mal la compréhension de la parole dans le bruit, qui est pourtant le point le plus gênant au quotidien. Utilisez-les comme un déclencheur, jamais comme une conclusion."),
        ],
        "sources": [
            ("Organisation mondiale de la santé", "https://www.who.int/fr"),
            ("Assurance Maladie - ameli.fr", "https://www.ameli.fr/"),
            ("Ministère de la Santé", "https://sante.gouv.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/audition/signes-audition.jpg",
        "image_alt": "Personne portant un appareil auditif intra-auriculaire",
        "date_display": "26 juillet 2026",
        "date_iso": "2026-07-26",
        "body": ART_BODY_AUDITION_SILENCIEUSE,
    },
    {
        "slug": "tendances-montures-2026",
        "category": "mode-lunettes",
        "title": "Tendances montures 2026 : quelles formes et couleurs privilégier",
        "meta_title": "Tendances lunettes 2026 : formes & couleurs | Maison Mikis",
        "meta_description": "Formes géométriques, papillon revisité, écaille intemporelle, métal fin : le tour d'horizon des tendances lunettes 2026 et comment savoir ce qui vous ira.",
        "excerpt": "Formes géométriques, retour du papillon, écaille intemporelle : le tour d'horizon des tendances lunettes 2026.",
        "answer": "En 2026, les formes géométriques et le papillon revisité côtoient les rondes réinterprétées et les modèles oversize. L'acétate domine, avec l'écaille en tête et une percée des teintes translucides, tandis que le métal fin porte un style minimaliste et que les tons neutres s'imposent.",
        "faq": [
            ("Une monture tendance se démode-t-elle plus vite ?",
             "Parfois, oui. Les formes très marquées, comme les modèles oversize ou architecturaux, se datent plus facilement que les silhouettes classiques. Si vous ne changez de lunettes que tous les deux ou trois ans, il peut être judicieux de garder une forme sobre pour la paire principale et d'oser davantage sur une seconde paire."),
            ("Peut-on porter des verres teintés toute la journée ?",
             "Une teinte légère se porte au quotidien sans difficulté particulière, y compris en intérieur, et beaucoup la trouvent reposante. En revanche, une teinte soutenue destinée au soleil n'a pas d'intérêt à l'intérieur et gêne la perception des couleurs. Nous vous faisons comparer plusieurs intensités avant de trancher."),
            ("Combien coûte une monture à la mode ?",
             "Les écarts sont importants selon la matière, la marque et la finition, et nous préférons ne pas donner de fourchette générale qui serait trompeuse. Le devis remis en boutique détaille le prix de la monture et celui des verres séparément, avec l'offre 100 % Santé, ce qui permet de comparer sereinement."),
            ("Faut-il changer de monture à chaque nouvelle ordonnance ?",
             "Non. Si votre monture est en bon état et que sa forme accepte la nouvelle correction, il est tout à fait possible de n'y remonter que des verres neufs. Nous vérifions l'état des charnières, du face et des branches avant de vous le proposer, car une monture fatiguée supporte mal un remontage."),
            ("Les montures mixtes conviennent-elles vraiment à tout le monde ?",
             "Elles élargissent le choix, ce qui est déjà beaucoup, mais elles n'annulent pas les différences de morphologie. La largeur du visage, la hauteur du nez et l'écart entre les yeux restent les critères déterminants. Une monture dite mixte peut donc très bien convenir à une personne et pas du tout à une autre."),
        ],
        "sources": [
            ("Asnav — Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("EssilorLuxottica", "https://www.essilorluxottica.com/"),
            ("Service-public.fr", "https://www.service-public.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/tendances-montures.jpg",
        "image_alt": "Portrait mode avec lunettes de soleil fines, tendances 2026",
        "date_display": "26 juillet 2026",
        "date_iso": "2026-07-26",
        "body": ART_BODY_MONTURES_2026,
    },
    {
        "slug": "nouvelles-technologies-verres-correcteurs",
        "category": "tech-verres",
        "title": "Verres correcteurs : les innovations qui changent le quotidien",
        "meta_title": "Innovations des verres correcteurs 2026 | Maison Mikis",
        "meta_description": "Freination de la myopie chez l'enfant, photochromiques plus rapides, surfaçage sur mesure : ce qui a vraiment changé dans les verres correcteurs.",
        "excerpt": "Freination de la myopie, photochromiques nouvelle génération, verres bureau : le point sur les vraies innovations.",
        "answer": "Trois avancées comptent réellement : des verres capables de ralentir la progression de la myopie chez l'enfant, des photochromiques nettement plus réactifs, et un surfaçage numérique personnalisé. Les filtres anti-lumière bleue, eux, se sont affinés mais ne remplacent ni les pauses ni un poste de travail bien réglé.",
        "faq": [
            ("Les verres de freination sont-ils remboursés ?",
             "Ils relèvent le plus souvent de la classe à prix libres, et la prise en charge dépend donc de votre complémentaire santé. Certains contrats prévoient un forfait spécifique pour l'enfant, d'autres non. Demandez un devis normalisé et interrogez votre mutuelle avant de commander : les écarts entre contrats sont importants."),
            ("Un adulte myope peut-il porter des verres de freination ?",
             "Non, ces verres sont conçus pour la période de croissance de l'œil, chez l'enfant et l'adolescent. Chez l'adulte, l'œil a cessé de s'allonger dans la très grande majorité des cas et la freination n'a plus d'objet. Une correction classique bien ajustée reste la bonne réponse."),
            ("Faut-il changer de verres dès qu'une nouvelle technologie sort ?",
             "Rarement. Un verre en bon état, avec une correction toujours adaptée, n'a pas besoin d'être remplacé parce qu'une gamme plus récente est arrivée. Les vrais motifs de renouvellement restent l'évolution de la correction, l'usure des traitements et une gêne persistante que la paire actuelle ne règle pas."),
            ("Combien de temps faut-il pour s'habituer à un verre progressif ?",
             "Cela varie beaucoup d'une personne à l'autre : certains porteurs sont à l'aise immédiatement, d'autres ont besoin de plusieurs jours. Portez la paire en continu plutôt que par intermittence, et revenez si la gêne persiste. Un ajustement de centrage ou de monture règle une bonne partie des cas."),
            ("Les traitements antireflets s'abîment-ils avec le temps ?",
             "Oui, comme toute couche de surface. Un nettoyage à sec, avec un mouchoir ou un pan de chemise, use prématurément le traitement et crée un voile de micro-rayures. Rincez à l'eau tiède, séchez avec un tissu microfibre propre, et faites vérifier vos verres lors de vos passages en boutique."),
        ],
        "sources": [
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Essilor France", "https://www.essilor.fr/"),
            ("Organisation mondiale de la santé", "https://www.who.int/fr"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/tech-verres.jpg",
        "image_alt": "Verres correcteurs colorés en gros plan",
        "date_display": "26 juillet 2026",
        "date_iso": "2026-07-26",
        "body": ART_BODY_TECH_VERRES,
    },
    {
        "slug": "nouvelles-technologies-lentilles-contact",
        "category": "tech-lentilles",
        "title": "Lentilles de contact : les nouveautés à connaître",
        "meta_title": "Nouvelles technologies des lentilles | Maison Mikis",
        "meta_description": "Matériaux plus respirants, lentilles freinatrices de myopie chez l'enfant, prototypes connectés : ce qui a changé et ce qui reste du laboratoire.",
        "excerpt": "Matériaux nouvelle génération, freination de la myopie chez l'enfant, prototypes connectés : le point sur les vraies nouveautés.",
        "answer": "Les vraies avancées récentes portent sur trois points : des matériaux en silicone-hydrogel plus respirants et mieux hydratés, des lentilles souples journalières capables de ralentir la progression de la myopie chez l'enfant, et une offre élargie pour l'astigmatisme et la presbytie. Les lentilles connectées, elles, restent expérimentales.",
        "faq": [
            ("Peut-on dormir avec ses lentilles de contact ?",
             "Sauf lentille spécifiquement prescrite pour le port nocturne, comme en orthokératologie, la réponse est non. Dormir avec une lentille classique réduit fortement l'oxygénation de la cornée et augmente le risque d'infection. Si cela vous arrive par accident, retirez la lentille et surveillez l'apparition d'une rougeur ou d'une douleur."),
            ("Une lentille journalière peut-elle être portée deux jours de suite ?",
             "Non, jamais. Une journalière est conçue pour un seul port puis la poubelle : son matériau et sa surface ne sont pas prévus pour supporter un cycle d'entretien. La réutiliser expose à des dépôts, à une gêne et à un risque infectieux, y compris si la lentille paraît en parfait état."),
            ("Faut-il une ordonnance pour acheter des lentilles ?",
             "Oui. La délivrance de lentilles correctrices repose sur une prescription d'un ophtalmologiste, qui précise la correction et le type de lentille. L'opticien procède ensuite à l'adaptation et au suivi. Une ordonnance de lunettes ne suffit pas : les valeurs ne sont pas transposables telles quelles."),
            ("Les lentilles conviennent-elles après 50 ans ?",
             "Souvent oui. Les designs multifocaux actuels rendent le port possible pour beaucoup de presbytes, parfois en complément d'une paire de lunettes pour les tâches longues de près. La sécheresse oculaire, plus fréquente avec l'âge, est le vrai facteur limitant : elle se vérifie lors de l'essai."),
            ("Peut-on porter des lentilles quand on est allergique au pollen ?",
             "C'est possible, mais la lentille journalière est alors nettement préférable : elle repart chaque soir avec les allergènes déposés dessus. En période de forte gêne, mieux vaut réduire la durée de port ou revenir temporairement aux lunettes, et en parler à votre médecin."),
        ],
        "sources": [
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Assurance Maladie - ameli.fr", "https://www.ameli.fr/"),
            ("Alcon France", "https://www.alcon.com/fr-fr"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/tech-lentilles.jpg",
        "image_alt": "Femme posant une lentille de contact sur son doigt",
        "date_display": "26 juillet 2026",
        "date_iso": "2026-07-26",
        "body": ART_BODY_TECH_LENTILLES,
    },
    {
        "slug": "100-pour-cent-sante-2026",
        "category": "remboursements",
        "title": "100% Santé lunettes et audioprothèses en 2026 : ce qui est vraiment pris en charge",
        "meta_title": "100% Santé 2026 : lunettes et audioprothèses | Maison Mikis",
        "meta_description": "Plafonds, classes A/B et I/II, renouvellement, devis normalisé : ce que couvre vraiment le 100% Santé en lunettes et audition, et ce qui reste à votre charge.",
        "excerpt": "Reste à charge 0, plafonds, classes A/B et I/II : ce que couvre vraiment le 100% Santé en 2026.",
        "answer": "Le 100 % Santé garantit un reste à charge nul sur un panier d'équipements défini : monture plafonnée à 30&nbsp;€ et verres à prix encadrés en optique, aide auditive plafonnée à 950&nbsp;€ par oreille pour un adulte. Deux conditions : une complémentaire santé responsable, et un équipement de classe A ou de classe I.",
        "faq": [
            ("Le 100 % Santé est-il vraiment gratuit ?",
             "Oui, si vous avez une complémentaire santé responsable — c'est le cas de la très grande majorité des contrats — et si vous choisissez un équipement de classe A en optique ou de classe I en audiologie. Vous ne réglez alors rien. Sans complémentaire, l'Assurance Maladie seule ne couvre qu'une part réduite."),
            ("Les lunettes 100 % Santé sont-elles de moins bonne qualité ?",
             "Les verres de classe A intègrent obligatoirement l'amincissement adapté à la correction, un traitement antireflet et un anti-rayure : la qualité optique est celle d'un verre courant. La différence porte sur le choix de montures, plus restreint, et sur les options comme les verres photochromiques ou les designs premium."),
            ("Peut-on mélanger classe A et classe B ?",
             "Oui, et c'est très courant. Vous pouvez prendre une monture de classe B avec des verres de classe A, ou l'inverse. Le devis doit alors indiquer clairement quel élément relève de quelle classe et le reste à charge correspondant, ligne par ligne."),
            ("Que se passe-t-il si mes aides auditives ne me conviennent pas ?",
             "La réglementation impose une période d'essai d'au moins 30 jours avant tout achat définitif : si l'appareil ne convient pas, vous le rendez sans le payer. Les réglages se font pendant cette période, et le suivi ultérieur est compris dans le prix, jamais facturé en plus."),
            ("Mon ordonnance est-elle encore valable ?",
             "Une ordonnance de lunettes est valable 5 ans entre 16 et 42 ans, 3 ans au-delà de 42 ans et 1 an avant 16 ans. Dans ces délais, l'opticien peut adapter la correction sans repasser par l'ophtalmologiste. Au-delà, une nouvelle prescription est nécessaire."),
        ],
        "sources": [
            ("Ameli — 100 % Santé", "https://www.ameli.fr/assure/remboursements/rembourse/optique-audition-dentaire/100-sante"),
            ("Service-Public.fr", "https://www.service-public.fr/"),
            ("Légifrance", "https://www.legifrance.gouv.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/accueil-cartes/accueil-espace-audition.jpg",
        "image_alt": "Accompagnement personnalisé pour une aide auditive",
        "date_display": "26 juillet 2026",
        "date_iso": "2026-07-26",
        "body": ART_BODY_REMBOURSEMENTS,
    },
    {
        "slug": "pourquoi-sudaya-mikhael-ont-ouvert-maison-mikis",
        "category": "vie-boutique",
        "title": "Pourquoi Sudaya et Mikhael ont ouvert Maison Mikis",
        "meta_title": "L'histoire de la boutique, par ses fondateurs | Maison Mikis",
        "meta_description": "Une rencontre professionnelle à Montreuil, deux ans de travail commun, puis une enseigne ouverte à deux : voici comment et pourquoi Maison Mikis a vu le jour.",
        "excerpt": "D'une boutique de Montreuil à l'esplanade des Olympiades : comment est née l'idée de Maison Mikis.",
        "answer": "Maison Mikis est née de la rencontre de Sudaya et Mikhael dans une boutique d'optique de Montreuil, où ils ont travaillé deux ans ensemble. Sudaya ayant grandi dans le Triangle de Choisy, l'esplanade des Olympiades s'est imposée pour ouvrir, en 2023, une enseigne à leur image.",
        "faq": [
            ("Maison Mikis appartient-elle à un groupe ou à une franchise ?",
             "Non. Il s'agit d'une boutique indépendante, détenue et animée par ses deux fondateurs. Aucune enseigne nationale ne nous impose de catalogue, d'objectif commercial ni de durée d'entretien. Cette indépendance est ce qui nous permet de déconseiller un équipement quand il ne nous semble pas justifié."),
            ("Faut-il connaître le quartier pour venir vous voir ?",
             "Pas du tout. Nous recevons aussi bien des habitants installés là depuis des décennies que des personnes de passage, des salariés des tours voisines ou des étudiants. Notre ancrage local raconte notre histoire, il ne définit pas notre clientèle : la boutique est ouverte à tout le monde."),
            ("Proposez-vous à la fois l'optique et l'audition ?",
             "Oui, la boutique réunit les deux activités. Cela permet de suivre une même personne sur ses deux sens, parfois sur plusieurs années, et d'aborder une gêne auditive naissante chez quelqu'un venu au départ pour ses lunettes. Les deux métiers restent distincts et exercés comme tels."),
            ("Peut-on venir simplement pour un conseil, sans achat ?",
             "Oui, et cela arrive tous les jours. Comparer un devis, comprendre une ordonnance, savoir si une monture peut être réparée ou demander un avis avant de se décider sont des démarches normales. Nous ne facturons ni le conseil, ni les petits ajustages du quotidien."),
            ("Que faites-vous si mon problème dépasse votre compétence ?",
             "Nous vous le disons et nous vous orientons. Un opticien et un audioprothésiste ne posent pas de diagnostic médical : une douleur, une baisse rapide de la vision ou de l'audition, des vertiges ou un doute sur une pathologie relèvent de l'ophtalmologiste, de l'ORL ou du médecin traitant."),
        ],
        "sources": [
            ("Ville de Paris", "https://www.paris.fr/"),
            ("Asnav — Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Assurance Maladie", "https://www.ameli.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/accueil/boutique-comptoir.jpg",
        "image_alt": "Comptoir et arche Maison Mikis dans la boutique",
        "date_display": "26 juillet 2026",
        "date_iso": "2026-07-26",
        "body": ART_BODY_VIE_BOUTIQUE,
    },
    {
        "slug": "signes-troubles-visuels-auditifs-enfant",
        "category": "enfant",
        "title": "Premiers signes d'un trouble visuel ou auditif chez l'enfant : le guide des parents",
        "meta_title": "Troubles visuels et auditifs de l'enfant | Maison Mikis",
        "meta_description": "Plisse les yeux, se rapproche de la télé, ne se retourne pas quand on l'appelle : les signes à observer chez l'enfant et le calendrier des contrôles.",
        "excerpt": "Plisse les yeux, ne se retourne pas quand on l'appelle : les signes à observer tôt chez l'enfant.",
        "answer": "Un enfant ne dit presque jamais qu'il voit ou entend mal, parce qu'il ignore ce qu'est voir et entendre normalement. Ce sont les comportements qui parlent : se rapprocher, plisser, incliner la tête, faire répéter, retarder son langage. En cas de doute, le médecin traitant reste le premier interlocuteur.",
        "faq": [
            ("À partir de quel âge peut-on faire vérifier la vue d'un enfant ?",
             "Dès les premiers mois, dans le cadre des visites du carnet de santé. Un examen ne nécessite pas que l'enfant sache lire ou parler : les professionnels disposent de tests adaptés à chaque âge, avec des images, des jeux ou des mesures automatisées."),
            ("Mon enfant a réussi le test scolaire, faut-il quand même s'inquiéter ?",
             "Un test scolaire est un filtre utile mais rapide, réalisé sur un temps court et dans des conditions parfois bruyantes. Il repère l'essentiel, pas tout. Si vous observez au quotidien des signes durables et répétés, parlez-en à votre médecin traitant même après un test jugé normal."),
            ("Un enfant peut-il porter des lunettes très jeune ?",
             "Oui, et c'est parfois indispensable. Des modèles existent dès les premiers mois, avec des branches souples ou un bandeau élastique et une charnière conçue pour résister aux manipulations. Plus la correction est mise en place tôt, mieux le développement visuel se déroule au cours des premières années."),
            ("Les écouteurs et le casque abîment-ils l'audition des enfants ?",
             "Un usage prolongé à fort volume expose l'oreille à des risques bien documentés, à tout âge. La règle simple consiste à limiter la durée, à baisser le volume et à préférer un casque à un écouteur intra-auriculaire pour les plus jeunes."),
            ("Faut-il attendre l'entrée au CP pour agir ?",
             "Non, rien ne justifie d'attendre. Aborder l'apprentissage de la lecture avec une gêne visuelle ou auditive non repérée complique inutilement les choses. Si un signe vous inquiète dès la maternelle, consultez à ce moment-là : une prise en charge précoce est toujours plus simple qu'un rattrapage."),
        ],
        "sources": [
            ("Assurance Maladie", "https://www.ameli.fr/"),
            ("Ministère de la Santé", "https://sante.gouv.fr/"),
            ("Asnav", "https://www.asnav.org/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/sante/myopie-enfant-signes.jpg",
        "image_alt": "Enfant lors d'un contrôle visuel",
        "date_display": "26 juillet 2026",
        "date_iso": "2026-07-26",
        "body": ART_BODY_ENFANT,
    },
    {
        "slug": "lentilles-hebdomadaires-precision7-alcon",
        "category": "tech-lentilles",
        "title": "Lentilles hebdomadaires : la nouveauté Precision7 d'Alcon change la donne",
        "meta_title": "Lentilles hebdomadaires Precision7 : le point | Maison Mikis",
        "meta_description": "Ni journalière, ni mensuelle : Precision7 se renouvelle chaque semaine. Ce que cela change pour l'entretien, le confort et votre budget.",
        "excerpt": "Entre la journalière et la mensuelle, une troisième fréquence de renouvellement apparaît : la lentille changée chaque semaine.",
        "answer": "Precision7 est présentée par Alcon comme la première lentille souple conçue pour un renouvellement hebdomadaire. Elle occupe une place intermédiaire entre la journalière, jetée chaque soir, et la mensuelle. Elle demande un entretien quotidien, et son adaptation passe toujours par une prescription puis un essai accompagné.",
        "faq": [
            ("Peut-on garder une lentille hebdomadaire plus de sept jours ?",
             "Non. Le cycle de remplacement fait partie de la conception de la lentille et ne se négocie pas au ressenti. Une lentille conservée au-delà accumule dépôts et micro-lésions, ce qui augmente le risque d'irritation et d'infection, même si le confort paraît encore acceptable."),
            ("Ce rythme revient-il moins cher que la journalière ?",
             "En port quotidien, un rythme de renouvellement plus long revient généralement moins cher sur l'année, solution d'entretien comprise. En port occasionnel, l'avantage disparaît, car la lentille vieillit même sans être portée. Le calcul se fait sur votre usage réel, pas sur le prix de la boîte."),
            ("Que se passe-t-il si j'oublie un soir de retirer ma lentille ?",
             "Retirez-la dès que possible et laissez votre œil au repos, sans lentille, pendant quelques heures. Surveillez toute rougeur, douleur, sensation de corps étranger ou baisse de vision : ces signes imposent une consultation rapide. Un oubli isolé n'est pas une catastrophe, mais l'habitude en est une."),
            ("Peut-on passer directement de la mensuelle à ce rythme sans avis ?",
             "Non. Tout changement de type de lentille passe par une nouvelle prescription et un essai vérifié par un professionnel. Les paramètres ne sont pas transposables d'une gamme à l'autre, et une lentille commandée seule sur internet à partir d'anciennes valeurs expose à une mauvaise adaptation."),
            ("Peut-on nager ou se doucher avec ses lentilles ?",
             "Il vaut mieux l'éviter. L'eau de piscine, de mer et celle du robinet peuvent contenir des micro-organismes qui se fixent sur la lentille et provoquent des infections cornéennes sévères. Si vous nagez régulièrement, parlez-en : des lunettes de natation correctrices sont souvent la meilleure réponse."),
        ],
        "sources": [
            ("Alcon France", "https://www.alcon.com/fr-fr"),
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Assurance Maladie - ameli.fr", "https://www.ameli.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/tech-lentilles.jpg",
        "image_alt": "Gros plan sur une lentille de contact souple posée sur un doigt",
        "date_display": "16 janvier 2025",
        "date_iso": "2025-01-16",
        "body": ART_BODY_ALCON_PRECISION7,
    },
    {
        "slug": "proteger-yeux-soleil-uv",
        "category": "sante-visuelle",
        "title": "Soleil et UV : comment bien protéger ses yeux en toute saison",
        "meta_title": "Protéger ses yeux du soleil et des UV | Maison Mikis",
        "meta_description": "Photokératite, cataracte, DMLA : les UV abîment aussi les yeux. Comment lire les catégories de filtration 0 à 4 et choisir une paire réellement protectrice.",
        "excerpt": "Le soleil n'agresse pas que la peau : les UV jouent aussi un rôle dans plusieurs atteintes oculaires, à court et à long terme.",
        "answer": "Les UV provoquent à court terme une photokératite, sorte de coup de soleil de la cornée, et contribuent à long terme au vieillissement du cristallin et à la cataracte. Pour un usage courant en extérieur, la catégorie 3 est celle que recommandent la plupart des professionnels de santé visuelle.",
        "faq": [
            ("Les lunettes de soleil vendues sur les marchés sont-elles sûres ?",
             "Tout dépend du marquage. Sans marquage CE ni indication de catégorie de filtration, rien ne garantit que le verre filtre les UV, et une teinte sombre non filtrante aggrave l'exposition en faisant dilater la pupille. En cas de doute, faites vérifier la paire par un professionnel avant de la porter."),
            ("Faut-il porter des lunettes de soleil en hiver ?",
             "Oui, surtout à la montagne et par temps de neige, où la réverbération est très forte et le risque de photokératite élevé. En ville, un soleil bas d'hiver éblouit aussi beaucoup, notamment au volant. La protection se raisonne selon la luminosité et la réverbération, pas selon la saison."),
            ("Des verres photochromiques suffisent-ils pour l'été ?",
             "Ils apportent un vrai confort en s'assombrissant selon la lumière, mais leur teinte maximale ne correspond pas toujours à celle d'une paire solaire dédiée, et ils foncent moins derrière un pare-brise. Pour la plage ou la montagne, une paire solaire réellement adaptée reste préférable."),
            ("Les lentilles de contact avec filtre UV dispensent-elles de lunettes ?",
             "Non. Une lentille ne couvre que la cornée et laisse la paupière ainsi que tout le pourtour de l'œil exposés aux rayons. Elle peut compléter la protection, jamais la remplacer. Une paire solaire correctement dimensionnée, et si possible enveloppante, reste indispensable dès que l'exposition devient importante."),
            ("Peut-on regarder une éclipse avec des lunettes de soleil ?",
             "Non, en aucun cas, quelle que soit la catégorie de filtration. L'observation directe du soleil exige des lunettes spécifiquement conçues et certifiées pour cet usage. Regarder une éclipse avec des lunettes de soleil ordinaires peut provoquer des lésions rétiniennes définitives et indolores sur le moment."),
        ],
        "sources": [
            ("Organisation mondiale de la santé", "https://www.who.int/fr"),
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Ministère de la Santé", "https://sante.gouv.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/accueil-cartes/accueil-espace-sante.jpg",
        "image_alt": "Personne essayant une paire de lunettes de soleil en boutique d'optique",
        "date_display": "5 août 2025",
        "date_iso": "2025-08-05",
        "body": ART_BODY_UV_SOLEIL,
    },
    {
        "slug": "lentilles-rigides-asana-bausch-lomb",
        "category": "tech-lentilles",
        "title": "Lentilles rigides perméables au gaz : Bausch + Lomb lance sa gamme Asana",
        "meta_title": "Lentilles rigides : à qui elles s'adressent | Maison Mikis",
        "meta_description": "Kératocône, cornée irrégulière, astigmatisme fort : ce qu'apportent les lentilles rigides perméables au gaz, et comment se passe l'adaptation.",
        "excerpt": "Moins connues que les souples, les lentilles rigides perméables au gaz restent la solution de référence pour les cornées irrégulières.",
        "answer": "Les lentilles rigides perméables au gaz gardent une forme stable sur l'œil, ce qui leur permet de compenser une cornée irrégulière là où une lentille souple échoue. Elles sont surtout proposées en cas de kératocône, d'astigmatisme important ou après une chirurgie oculaire, et sont réalisées sur mesure.",
        "faq": [
            ("Les lentilles rigides font-elles mal ?",
             "Elles ne font pas mal, mais elles se sentent au début. La paupière perçoit le bord de la lentille pendant les premiers jours, avec parfois un larmoiement. Cette sensation diminue nettement avec l'habitude. Une douleur vraie, elle, n'est jamais normale et doit conduire à retirer la lentille et à consulter."),
            ("Combien de temps une lentille rigide se garde-t-elle ?",
             "Nettement plus longtemps qu'une lentille souple, mais pas indéfiniment. La durée dépend du matériau, de l'entretien et de l'évolution de votre cornée. Une lentille rayée, déformée ou qui ne donne plus la même netteté doit être remplacée, même si elle vous semble encore utilisable."),
            ("Peut-on faire du sport avec ?",
             "Oui pour la plupart des activités, avec une réserve pour les sports de contact et ceux où la lentille peut se déloger brutalement. Les sports aquatiques sont à éviter avec toute lentille, en raison du risque infectieux lié à l'eau. Parlez de votre pratique lors de l'adaptation."),
            ("Sont-elles remboursées ?",
             "La prise en charge des lentilles par l'Assurance Maladie est limitée à certaines indications médicales précises, sur prescription, et les complémentaires santé prévoient souvent un forfait annuel distinct de celui des lunettes. Le mieux reste de demander un devis et de vérifier votre tableau de garanties avant de vous engager."),
            ("Que faire si une lentille rigide se déplace sous la paupière ?",
             "Ne frottez pas votre œil. Clignez plusieurs fois, appliquez quelques gouttes de sérum physiologique et ramenez doucement la lentille vers le centre en massant la paupière fermée. Si elle reste bloquée ou si l'œil devient douloureux, faites-vous aider par un professionnel sans forcer."),
        ],
        "sources": [
            ("Bausch + Lomb", "https://www.bausch.com/"),
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Assurance Maladie - ameli.fr", "https://www.ameli.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/conseils/lunettes-lentilles.jpg",
        "image_alt": "Opticien tenant une lentille de contact rigide entre deux doigts devant un plateau d'essai",
        "date_display": "9 septembre 2025",
        "date_iso": "2025-09-09",
        "body": ART_BODY_BL_ASANA,
    },
    {
        "slug": "casques-ecouteurs-proteger-audition-jeunes",
        "category": "sante-auditive",
        "title": "Casques et écouteurs : comment protéger l'audition des jeunes générations",
        "meta_title": "Casques et écouteurs : protéger son audition | Maison Mikis",
        "meta_description": "Écouteurs, casque, discothèque : à partir de quel niveau et de quelle durée l'écoute devient risquée, et les réflexes simples pour préserver ses oreilles.",
        "excerpt": "Entre écouteurs portés du matin au soir et sorties en soirée, l'audition des jeunes est exposée à des niveaux sous-estimés.",
        "answer": "Le risque auditif ne dépend pas seulement de l'intensité du son, mais de la combinaison entre niveau et durée d'écoute. Les repères de santé auditive situent la limite autour de 80 décibels sur huit heures, contre moins de quarante minutes à 98 décibels.",
        "faq": [
            ("La réduction de bruit protège-t-elle vraiment l'audition ?",
             "Indirectement, oui. Elle n'atténue pas la musique mais le bruit de fond, ce qui supprime la raison principale de monter le son dans les transports ou dans la rue. À contenu identique, on écoute alors nettement moins fort, ce qui réduit l'exposition."),
            ("Un casque est-il plus dangereux que des écouteurs intra-auriculaires ?",
             "Ce n'est pas la forme qui compte, mais le niveau reçu par l'oreille et la durée. Les intra-auriculaires isolent souvent mieux, ce qui aide à baisser le son. Un casque mal isolé pousse au contraire à augmenter le volume dans un environnement bruyant."),
            ("Les bouchons d'oreilles empêchent-ils de profiter d'un concert ?",
             "Les bouchons filtrants conçus pour la musique atténuent l'ensemble des fréquences de façon homogène, sans étouffer le son comme le fait la mousse. La plupart des utilisateurs rapportent entendre les détails aussi bien, voire mieux, avec une fatigue auditive bien moindre en fin de soirée."),
            ("Une perte auditive due au bruit peut-elle se soigner ?",
             "Les cellules sensorielles de l'oreille interne détruites par le bruit ne se régénèrent pas, et aucun traitement ne les remplace aujourd'hui. C'est ce qui rend la prévention si importante : on peut compenser une perte installée par un appareillage, mais pas revenir en arrière."),
            ("À quel âge peut-on faire contrôler l'audition d'un adolescent ?",
             "Un contrôle est possible dès qu'un adolescent peut répondre de façon fiable pendant la mesure, ce qui est le cas bien avant l'âge du lycée. Il se justifie surtout en cas de sifflements répétés, de gêne dans le bruit ou d'écoute prolongée au casque."),
        ],
        "sources": [
            ("Organisation mondiale de la santé", "https://www.who.int/fr"),
            ("INRS - Risques liés au bruit", "https://www.inrs.fr/"),
            ("Ministère de la Santé", "https://sante.gouv.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/audition/hero-audition.jpg",
        "image_alt": "Jeune adulte souriant portant des écouteurs sans fil dans la rue",
        "date_display": "23 septembre 2025",
        "date_iso": "2025-09-23",
        "body": ART_BODY_CASQUES_JEUNES,
    },
    {
        "slug": "lunettes-connectees-ray-ban-meta-mode-tech",
        "category": "mode-lunettes",
        "title": "Ray-Ban Meta : quand la lunette connectée devient un objet de mode",
        "meta_title": "Lunettes connectées Ray-Ban Meta : notre avis | Maison Mikis",
        "meta_description": "Caméra, assistant vocal, mini-écran dans le verre : ce que les lunettes connectées changent au choix d'une monture, et les questions à se poser.",
        "excerpt": "Entre caméra intégrée, assistant vocal et mini-écran dans le verre, la lunette connectée pose de nouvelles questions au moment de choisir sa monture.",
        "answer": "Les lunettes connectées Ray-Ban Meta sont des montures d'allure classique intégrant une caméra, des haut-parleurs open-ear et un assistant vocal. Elles changent surtout le rapport à la monture, portée du matin au soir, et posent des questions concrètes de confort, d'autonomie et de vie privée.",
        "faq": [
            ("Peut-on mettre des verres progressifs dans une lunette connectée ?",
             "Cela dépend entièrement du modèle et de votre correction, et seul le fabricant fait autorité sur ce point. La hauteur de verre disponible et l'épaisseur admissible sont plus contraintes que sur une monture classique. Apportez votre ordonnance : nous vérifions ensemble ce qui est réellement possible avant toute commande."),
            ("Ces lunettes remplacent-elles des aides auditives ?",
             "Non, en aucun cas. Des haut-parleurs diffusant du son près de l'oreille n'ont rien à voir avec un appareillage auditif, qui repose sur un bilan, un réglage personnalisé et un suivi médicalement encadré. Si vous entendez moins bien, parlez-en à votre médecin ou à un ORL plutôt que d'acheter un objet grand public."),
            ("Comment savoir si quelqu'un est en train de filmer avec ses lunettes ?",
             "Les fabricants annoncent un témoin lumineux signalant l'enregistrement, mais il est discret et peut échapper à l'attention, surtout en extérieur. Il n'existe pas de moyen fiable de le garantir. En pratique, la responsabilité repose sur le porteur, tenu de respecter le droit à l'image des personnes qu'il filme."),
            ("Ces montures s'ajustent-elles comme des lunettes normales ?",
             "Moins facilement. L'électronique intégrée dans les branches limite la marge de cintrage et interdit certaines interventions à chaud que nous pratiquons couramment sur l'acétate ou le métal. Un ajustage reste possible dans une certaine mesure, mais il faut accepter un confort un peu moins finement réglable."),
            ("Une lunette connectée dure-t-elle aussi longtemps qu'une paire classique ?",
             "Sa durée de vie utile dépend de la batterie et du suivi logiciel du fabricant, pas seulement de l'état de la monture. Une paire traditionnelle bien entretenue peut se garder plusieurs années et se remonter avec de nouveaux verres, ce qui n'est pas comparable. C'est un critère à intégrer au budget."),
        ],
        "sources": [
            ("EssilorLuxottica", "https://www.essilorluxottica.com/"),
            ("Ray-Ban", "https://www.ray-ban.com/"),
            ("CNIL — Commission nationale de l'informatique et des libertés", "https://www.cnil.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/tendances-montures.jpg",
        "image_alt": "Portrait mode d'une personne élégante portant des lunettes de soleil noires de style Wayfarer",
        "date_display": "4 novembre 2025",
        "date_iso": "2025-11-04",
        "body": ART_BODY_RAYBAN_META,
    },
    {
        "slug": "ecrans-myopie-enfant-habitudes-protectrices",
        "category": "enfant",
        "title": "Écrans, temps dehors et myopie : quelles habitudes protègent les yeux de mon enfant ?",
        "meta_title": "Écrans et myopie chez l'enfant : quoi faire | Maison Mikis",
        "meta_description": "Pourquoi la myopie progresse chez les enfants, ce que change vraiment le temps passé dehors, et les habitudes simples qui protègent leur vue au quotidien.",
        "excerpt": "La myopie des enfants progresse partout dans le monde, portée par plus d'activités de près et moins de temps dehors.",
        "answer": "La myopie infantile progresse dans la plupart des pays industrialisés, en lien avec plus d'activités de près et moins de temps passé à l'extérieur. Le levier le mieux documenté reste le jeu dehors, à la lumière du jour, complété par des pauses régulières et une distance de lecture raisonnable.",
        "faq": [
            ("La myopie de mon enfant peut-elle disparaître en grandissant ?",
             "Non, une myopie installée ne régresse pas spontanément. Elle progresse généralement pendant la croissance, puis se stabilise vers la fin de l'adolescence. En revanche, une correction bien adaptée rétablit immédiatement une vision nette et un confort normal, à tout âge et sans effet secondaire."),
            ("Les lunettes affaiblissent-elles la vue à force d'être portées ?",
             "C'est une idée reçue tenace, mais fausse. Porter une correction adaptée ne rend pas l'œil paresseux et n'accélère rien. Ne pas la porter, en revanche, expose l'enfant à la fatigue visuelle, aux maux de tête et à des difficultés scolaires évitables."),
            ("Les verres filtrant la lumière bleue protègent-ils de la myopie ?",
             "Rien ne permet de l'affirmer aujourd'hui. Ces filtres n'agissent pas sur l'allongement du globe oculaire, qui est le mécanisme en cause dans la myopie. Le temps passé dehors, les pauses régulières et une distance de lecture raisonnable restent les seuls leviers réellement documentés."),
            ("À quelle fréquence faire contrôler la vue d'un enfant déjà corrigé ?",
             "Le rythme est fixé par l'ophtalmologiste, généralement plus rapproché que chez l'adulte parce que la correction évolue avec la croissance. Entre deux consultations, nous pouvons vérifier le réglage de l'équipement, mesurer la vision et vous alerter si quelque chose nous semble avoir changé."),
            ("Une paire de secours est-elle vraiment utile ?",
             "Elle évite bien des journées sans correction, notamment à l'école, au sport ou en voyage scolaire, et elle limite le stress en cas de casse. Certains contrats de complémentaire santé et certaines offres de fabricants la facilitent : le mieux reste d'en parler au moment du devis, avant l'achat."),
        ],
        "sources": [
            ("Asnav", "https://www.asnav.org/"),
            ("Organisation mondiale de la santé", "https://www.who.int/fr"),
            ("Ministère de la Santé", "https://sante.gouv.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/sante/myopie-enfant-suivi.jpg",
        "image_alt": "Enfant souriant passant un test de vue chez l'opticien",
        "date_display": "11 novembre 2025",
        "date_iso": "2025-11-11",
        "body": ART_BODY_ECRANS_MYOPIE_ENFANT,
    },
    {
        "slug": "comprendre-devis-normalise-lunettes-aides-auditives",
        "category": "remboursements",
        "title": "Le devis normalisé chez l'opticien et l'audioprothésiste : comment le lire",
        "meta_title": "Devis normalisé optique et audition : le lire | Maison Mikis",
        "meta_description": "Obligatoire depuis 2020, le devis normalisé se lit de la même façon partout. Ce qu'il doit contenir et ce qu'il faut vérifier avant de signer.",
        "excerpt": "Un document obligatoire, au format identique partout, qui vous permet de comparer deux offres avant d'acheter.",
        "answer": "Le devis normalisé est un document obligatoire depuis le 1er janvier 2020 chez tout opticien et tout audioprothésiste. Il présente les mêmes rubriques dans le même ordre partout, comporte toujours au moins une offre 100 % Santé, et chiffre le reste à charge estimé avant tout engagement.",
        "faq": [
            ("Le devis est-il payant ou engageant ?",
             "Ni l'un ni l'autre. Il est remis gratuitement et ne vaut en aucun cas commande. Vous pouvez repartir avec, le comparer ailleurs, le montrer à votre complémentaire santé, puis revenir ou non. Aucun professionnel ne peut vous facturer son établissement ni exiger un acompte pour l'obtenir."),
            ("Que faire si l'opticien ne me propose pas de devis ?",
             "Demandez-le explicitement : c'est une obligation légale, pas une faveur commerciale. Si le refus persiste, mieux vaut aller ailleurs, car la transparence sur les prix conditionne tout le reste. Vous pouvez également signaler la situation à la répression des fraudes ou en parler à votre complémentaire santé."),
            ("Mon devis mentionne un délai de validité : que se passe-t-il après ?",
             "Passé ce délai, les prix ne sont plus garantis et un nouveau document doit être établi. Rien n'est perdu pour autant : il suffit de repasser, la reprise d'un devis existant prend quelques minutes si votre correction n'a pas changé."),
            ("Peut-on demander un devis sans avoir d'ordonnance ?",
             "Oui, pour obtenir un ordre de prix sur une monture ou sur un modèle qui vous plaît. En revanche, le chiffrage précis des verres et des remboursements suppose de connaître votre correction, donc de disposer d'une prescription en cours de validité au moment de la commande."),
            ("Le devis change-t-il quelque chose au tiers payant ?",
             "Il le prépare directement. Les informations qu'il contient permettent d'interroger votre complémentaire et de savoir si la dispense d'avance de frais s'applique à votre contrat. Le jour de la commande, vous ne réglez alors que la part qui vous revient réellement, sans faire l'avance du reste."),
        ],
        "sources": [
            ("Assurance Maladie", "https://www.ameli.fr/"),
            ("Service-public.fr", "https://www.service-public.fr/"),
            ("Ministère de la Santé", "https://sante.gouv.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/accueil-cartes/accueil-espace-audition.jpg",
        "image_alt": "Gros plan sur un devis papier et une paire de lunettes posés sur un comptoir d'opticien",
        "date_display": "18 novembre 2025",
        "date_iso": "2025-11-18",
        "body": ART_BODY_DEVIS_NORMALISE,
    },
    {
        "slug": "une-journee-type-a-la-boutique",
        "category": "vie-boutique",
        "title": "Une journée type à la Maison Mikis",
        "meta_title": "Journée type chez un opticien indépendant | Maison Mikis",
        "meta_description": "Ouverture du rideau, essayages, ajustages de dernière minute : à quoi ressemble vraiment une journée ordinaire dans une boutique d'optique indépendante.",
        "excerpt": "Entre l'ouverture du rideau le matin et le dernier ajustage du soir, voici à quoi ressemble une journée chez nous.",
        "answer": "Une journée à la boutique commence un peu avant dix heures, par la remise en ordre des présentoirs et le point sur les rendez-vous. Elle se poursuit par des essayages, des mesures, des réparations et des visites sans rendez-vous, et s'achève souvent par un réglage de dernière minute.",
        "faq": [
            ("Quels sont vos jours et horaires d'ouverture ?",
             "La boutique accueille du mardi au samedi, de dix heures à dix-neuf heures trente. Les débuts de matinée et les fins d'après-midi sont généralement les moments les plus chargés. Si vous souhaitez du temps pour un essayage long, le milieu de journée en semaine reste le créneau le plus calme."),
            ("Combien de temps faut-il prévoir pour choisir des lunettes ?",
             "Cela dépend surtout de vous. Certaines personnes savent en dix minutes, d'autres reviennent deux fois avant de trancher, et les deux nous conviennent. Comptez une bonne demi-heure entre l'essayage, le choix des verres, les mesures et l'établissement du devis, sans obligation de décider le jour même."),
            ("Réparez-vous les lunettes achetées ailleurs ?",
             "Oui, dans la mesure du possible. Un resserrage, un changement de plaquettes ou un réalignement se font sur place en quelques minutes, quelle que soit l'origine de la paire. Certaines réparations dépendent en revanche de la disponibilité des pièces chez le fabricant, ce que nous vérifions avec vous."),
            ("Puis-je venir essayer sans avoir d'ordonnance ?",
             "Bien sûr. Beaucoup de visites commencent par une simple envie de changer de style, sans correction en tête. Nous pouvons faire un contrôle de la vue pour situer votre besoin, et vous indiquer si une consultation chez l'ophtalmologiste s'impose avant de commander quoi que ce soit."),
            ("Que se passe-t-il après la commande de mes lunettes ?",
             "Nous vous prévenons dès que la paire est prête, puis nous la réglons sur votre visage lors du retrait : galbe, inclinaison, appui derrière les oreilles. Un réajustement dans les jours qui suivent est fréquent et normal ; il est inclus, comme les réglages ultérieurs."),
        ],
        "sources": [
            ("Asnav — Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Assurance Maladie", "https://www.ameli.fr/"),
            ("Service-public.fr", "https://www.service-public.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/accueil/boutique-ambiance.jpg",
        "image_alt": "Intérieur chaleureux de la boutique Maison Mikis avec présentoirs de lunettes et comptoir en bois",
        "date_display": "27 novembre 2025",
        "date_iso": "2025-11-27",
        "body": ART_BODY_JOURNEE_TYPE,
    },
    {
        "slug": "novacel-celene-traitement-anti-reflet-teinte-nude",
        "category": "tech-verres",
        "title": "Célène de Novacel : quand le traitement anti-reflet devient un choix esthétique",
        "meta_title": "Célène de Novacel, l'antireflet nude | Maison Mikis",
        "meta_description": "Un antireflet peut-il devenir un choix esthétique ? Ce que propose Célène, le traitement à reflets nude du verrier français Novacel, et comment le juger.",
        "excerpt": "Le verrier français Novacel présente Célène, un traitement anti-reflet à la teinte nude, pensé pour sublimer le regard.",
        "answer": "Célène est un traitement de surface proposé par le verrier français Novacel. Il assume un reflet résiduel de teinte nude, légèrement rosée, plutôt que le vert ou le bleu habituels, tout en conservant les fonctions attendues d'un traitement moderne : dureté, surface hydrofuge, effet antistatique et protection contre les ultraviolets.",
        "faq": [
            ("Un antireflet coloré modifie-t-il ce que je vois ?",
             "Non. La teinte concerne le reflet renvoyé vers l'extérieur, pas la lumière qui traverse le verre jusqu'à votre œil. Vos couleurs restent fidèles. Ce qui change, c'est l'aspect de vos verres pour la personne en face de vous, surtout sous un éclairage direct ou au flash."),
            ("Peut-on ajouter ce traitement sur des verres déjà montés ?",
             "Non, il est appliqué en usine lors de la fabrication du verre, avant le montage. Il faut donc le choisir au moment de la commande. Si vos verres actuels vous conviennent par ailleurs, mieux vaut attendre le prochain renouvellement plutôt que de les remplacer uniquement pour cela."),
            ("Comment nettoyer des verres traités sans les abîmer ?",
             "Rincez-les à l'eau tiède, éventuellement avec une goutte de savon doux, puis séchez avec un tissu microfibre propre. Évitez le mouchoir en papier, le pan de chemise et les produits ménagers : ils créent un voile de micro-rayures qui use le traitement bien plus vite que l'usage normal."),
            ("Ce traitement convient-il aussi aux hommes ?",
             "Oui, rien dans le produit n'est spécifique à un genre. La teinte est discrète et se remarque surtout de trois quarts. Le vrai critère reste l'accord avec la couleur de la monture et le teint de peau, pas autre chose. Le mieux est de comparer deux verres de démonstration côte à côte."),
            ("À quoi voit-on qu'un traitement antireflet est usé ?",
             "Un voile grisâtre qui ne part plus au nettoyage, des craquelures fines visibles en lumière rasante, ou des reflets qui redeviennent gênants la nuit. Ce sont des signes d'usure de la couche de surface, pas de saleté. Passez nous voir : nous vérifions l'état des verres sans rendez-vous."),
        ],
        "sources": [
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Assurance Maladie - ameli.fr", "https://www.ameli.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/conseils/traitements-verres.jpg",
        "image_alt": "Gros plan sur des verres de lunettes montrant de légers reflets colorés sur la surface",
        "date_display": "20 janvier 2026",
        "date_iso": "2026-01-20",
        "body": ART_BODY_NOVACEL_CELENE,
    },
    {
        "slug": "presbytie-comprendre-ce-trouble-de-la-vision",
        "category": "sante-visuelle",
        "title": "Presbytie : comprendre ce trouble de la vision qui touche presque tout le monde après 45 ans",
        "meta_title": "Presbytie après 45 ans : signes et solutions | Maison Mikis",
        "meta_description": "Bras qui s'allonge pour lire, fatigue en fin de journée : comprendre la presbytie, un phénomène naturel, et faire le tri entre les solutions.",
        "excerpt": "Difficulté à lire de près, besoin d'éloigner son téléphone : la presbytie touche, tôt ou tard, la quasi-totalité des adultes.",
        "answer": "La presbytie n'est pas une maladie mais une évolution naturelle de l'œil : le cristallin perd peu à peu sa souplesse et la mise au point de près devient difficile, en général à partir de 44-45 ans. Elle se corrige très bien, en lunettes ou en lentilles, et se stabilise vers 60-65 ans.",
        "faq": [
            ("Porter des lunettes de lecture accélère-t-il la presbytie ?",
             "Non. C'est une crainte très répandue, mais le durcissement du cristallin suit son cours quoi que vous fassiez. Une correction adaptée ne fait que restituer un confort perdu. Ce qui change, c'est que l'on prend conscience de l'effort que l'on fournissait auparavant sans s'en rendre compte."),
            ("Un myope devient-il presbyte lui aussi ?",
             "Oui, le mécanisme est le même pour tout le monde. Un myope léger peut simplement retirer ses lunettes pour lire de près pendant quelques années, ce qui donne l'illusion d'être épargné. La correction de loin, elle, reste nécessaire, et un équipement combiné devient vite plus confortable."),
            ("La chirurgie peut-elle corriger la presbytie ?",
             "Des techniques existent et relèvent exclusivement d'un chirurgien ophtalmologiste, qui évalue l'indication au cas par cas. Ce n'est ni systématique ni adapté à tous les yeux. Cette question se discute en consultation médicale, avec un bilan complet : un opticien ne peut ni la recommander ni l'écarter."),
            ("Faut-il une ordonnance pour des lunettes de près ?",
             "Pour un équipement correcteur, oui : la prescription vient de l'ophtalmologiste. Dans les cas prévus par la réglementation, l'opticien peut renouveler ou adapter une correction sur présentation d'une ordonnance en cours de validité. Les loupes vendues en libre-service échappent à ce cadre, mais elles ne remplacent pas une correction sur mesure."),
            ("Combien de temps faut-il pour s'habituer à une première paire de progressifs ?",
             "Cela varie beaucoup : certains porteurs sont à l'aise en une journée, d'autres ont besoin de deux ou trois semaines. Le réflexe utile est de bouger la tête plutôt que les yeux pour viser la bonne zone. Si la gêne dure, revenez faire vérifier le centrage et le réglage."),
        ],
        "sources": [
            ("Assurance Maladie - ameli.fr", "https://www.ameli.fr/"),
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Organisation mondiale de la santé", "https://www.who.int/fr"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/sante/maladies-modele-oeil.jpg",
        "image_alt": "Personne d'une quarantaine d'années tenant un livre à bout de bras pour mieux lire",
        "date_display": "11 février 2026",
        "date_iso": "2026-02-11",
        "body": ART_BODY_PRESBYTIE,
    },
    {
        "slug": "nouvel-an-lunaire-triangle-de-choisy",
        "category": "vie-boutique",
        "title": "Le Nouvel An lunaire vu depuis notre vitrine du Triangle de Choisy",
        "meta_title": "Nouvel An lunaire : notre quartier en fête | Maison Mikis",
        "meta_description": "Vitrines rouge et or, allées qui se remplissent plus tôt : ce que le Nouvel An lunaire change autour de notre boutique, et ce que cela dit de notre métier.",
        "excerpt": "Chaque année, le Nouvel An lunaire redonne au quartier des couleurs et un rythme qui n'appartiennent qu'à lui.",
        "answer": "Le Nouvel An lunaire transforme chaque année le quartier autour de notre boutique : vitrines rouge et or, allées plus animées, commerces décorés. Pour nous, c'est une période de passage plus dense, de conversations plus longues au comptoir, et un rappel de ce qu'être un commerce de quartier veut dire.",
        "faq": [
            ("La boutique est-elle ouverte pendant le Nouvel An lunaire ?",
             "Oui, aux horaires habituels. Nous ne fermons pas et nous n'ouvrons pas non plus de créneaux exceptionnels. Les allées de la galerie étant plus fréquentées à cette période, préférez le milieu de journée en semaine si vous souhaitez du temps pour un essayage tranquille."),
            ("Peut-on venir sans rendez-vous à ce moment de l'année ?",
             "Pour un essayage, un ajustage, une réparation rapide, un devis ou un contrôle de la vue, oui, comme le reste de l'année. Seuls les bilans auditifs et les suivis d'appareillage demandent un créneau réservé, parce qu'ils nécessitent du temps et un environnement calme."),
            ("Parlez-vous d'autres langues que le français en boutique ?",
             "Nous nous débrouillons en anglais et nous prenons le temps qu'il faut quand l'échange est plus difficile. Beaucoup de personnes viennent accompagnées d'un proche qui traduit, et cela ne nous pose aucun problème : l'essentiel est que la personne concernée comprenne ce qu'elle achète et pourquoi."),
            ("Faites-vous des offres spéciales à l'occasion de la fête ?",
             "Non, et c'est un choix assumé. Nous ne pensons pas qu'une fête familiale soit un bon prétexte commercial. Ce que nous proposons à cette période est exactement ce que nous proposons le reste de l'année, y compris l'offre 100 % Santé qui figure sur tous nos devis."),
            ("Comment vous trouver dans la galerie ?",
             "Nous sommes installés Galerie Oslo, sur l'Esplanade des Olympiades, dans le 13e arrondissement. La galerie se rejoint depuis la dalle comme depuis la rue. Si vous hésitez, les commerçants voisins vous orienteront volontiers : tout le monde se connaît dans cette partie de la galerie."),
        ],
        "sources": [
            ("Ville de Paris", "https://www.paris.fr/"),
            ("Service-public.fr", "https://www.service-public.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/accueil/hero-boutique.jpg",
        "image_alt": "Rue commerçante animée du Triangle de Choisy près de l'esplanade des Olympiades à Paris",
        "date_display": "13 février 2026",
        "date_iso": "2026-02-13",
        "body": ART_BODY_NOUVEL_AN_LUNAIRE,
    },
    {
        "slug": "acouphenes-comprendre-bruit-qui-ne-sarrete-jamais",
        "category": "sante-auditive",
        "title": "Acouphènes : comprendre ce bruit qui ne s'arrête jamais",
        "meta_title": "Acouphènes : causes, gêne et quand consulter | Maison Mikis",
        "meta_description": "Sifflement, bourdonnement, grésillement : d'où viennent les acouphènes, pourquoi ils pèsent autant sur le quotidien et à quel moment il faut consulter.",
        "excerpt": "Sifflement, bourdonnement, grésillement : les acouphènes concernent des millions de Français, souvent en silence.",
        "answer": "Un acouphène est un son perçu par l'oreille sans source extérieure : sifflement, bourdonnement ou grésillement. Il fait souvent suite à un traumatisme sonore et peut exister sans baisse d'audition mesurable. Un acouphène qui persiste au-delà de quelques jours mérite toujours d'être évalué.",
        "faq": [
            ("Les acouphènes peuvent-ils disparaître tout seuls ?",
             "Oui, c'est fréquent après une exposition sonore isolée : le sifflement s'estompe alors en quelques heures à quelques jours. Au-delà de ce délai, la disparition spontanée devient moins probable, mais la gêne ressentie peut nettement diminuer avec le temps et avec un accompagnement adapté."),
            ("Le stress provoque-t-il des acouphènes ?",
             "Le stress n'est généralement pas la cause du phénomène, mais il en amplifie beaucoup la perception. Fatigue, anxiété et mauvais sommeil augmentent l'attention portée au bruit interne. Agir sur ces facteurs ne fait pas disparaître l'acouphène, cela le rend souvent plus supportable."),
            ("Existe-t-il un médicament contre les acouphènes ?",
             "Aucun traitement médicamenteux ne fait aujourd'hui disparaître un acouphène de façon fiable et durable. Seul un médecin peut évaluer l'intérêt d'un traitement dans une situation donnée, en particulier en phase aiguë. Méfiez-vous des produits vendus sur internet comme des solutions miracles."),
            ("Une aide auditive peut-elle aider en cas d'acouphène ?",
             "Lorsqu'une baisse d'audition est associée, l'appareillage améliore souvent le confort : l'oreille reçoit de nouveau les sons de l'environnement, ce qui réduit la place occupée par l'acouphène. Ce n'est pas un traitement de l'acouphène lui-même, et le bénéfice varie d'une personne à l'autre."),
            ("Faut-il éviter le silence complet quand on a des acouphènes ?",
             "Beaucoup de personnes constatent que le silence total accentue leur perception, faute d'autre son à écouter. Un fond sonore discret au coucher, une fenêtre entrouverte ou une musique très basse suffisent souvent à réduire la gêne au moment de l'endormissement."),
        ],
        "sources": [
            ("Journée Nationale de l'Audition", "https://www.journee-audition.org/"),
            ("Organisation mondiale de la santé", "https://www.who.int/fr"),
            ("Assurance Maladie - ameli.fr", "https://www.ameli.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/audition/parcours-audition.jpg",
        "image_alt": "Personne se tenant l'oreille, gênée par un bruit interne persistant",
        "date_display": "5 mars 2026",
        "date_iso": "2026-03-05",
        "body": ART_BODY_ACOUPHENES,
    },
    {
        "slug": "lunettes-engagees-matieres-durables-eco-responsables",
        "category": "mode-lunettes",
        "title": "Lunettes engagées : quand la mode optique mise sur les matières durables",
        "meta_title": "Lunettes éco-responsables : matières durables | Maison Mikis",
        "meta_description": "Acétate biosourcé, matériaux recyclés, réparabilité : ce que recouvrent vraiment les lunettes dites durables, et comment faire le tri.",
        "excerpt": "Acétate biosourcé, matériaux recyclés, réparabilité : la lunette durable n'est plus une niche mais une vraie tendance.",
        "answer": "Une lunette dite éco-responsable repose sur trois leviers : la matière employée, biosourcée ou recyclée, le lieu et le mode de fabrication, et la capacité de la monture à être réparée plutôt que remplacée. C'est le troisième critère, le plus vérifiable, qui pèse souvent le plus dans la durée.",
        "faq": [
            ("Une monture en acétate biosourcé est-elle plus fragile ?",
             "Non, ce n'est pas ce que nous observons. Les gammes biosourcées se travaillent et s'ajustent comme les acétates classiques, et leur tenue dans le temps dépend surtout de la qualité du montage et des charnières. La différence se joue sur l'origine de la matière, pas sur la solidité de la monture."),
            ("Peut-on faire recycler ses anciennes lunettes ?",
             "Des filières de collecte existent chez de nombreux opticiens et associations, avec des destinations variables selon l'état de la paire : réemploi solidaire pour les montures en bon état, valorisation des matières sinon. Apportez-nous vos anciennes paires, nous vous indiquerons ce qu'il est possible d'en faire."),
            ("Les lunettes durables coûtent-elles plus cher ?",
             "Cela dépend beaucoup plus de la marque, de la finition et du positionnement que de la matière elle-même. Certaines collections responsables se situent au niveau des montures classiques comparables, d'autres nettement au-dessus. Le devis remis en boutique détaille le prix de la monture et celui des verres, ce qui permet de comparer."),
            ("Existe-t-il un label officiel pour les lunettes écologiques ?",
             "Il n'existe pas de label unique reconnu qui s'appliquerait à l'ensemble de la lunetterie. Les marques s'appuient sur des certifications portant sur une matière ou un procédé précis, ce qui n'est pas la même chose. Demandez toujours sur quoi porte exactement la certification annoncée."),
            ("Vaut-il mieux réparer sa monture ou en acheter une neuve ?",
             "Réparer, chaque fois que c'est techniquement possible et que la monture vous plaît encore. Un changement de plaquettes, un resserrage ou un remplacement de branche coûte peu et prolonge la paire de plusieurs années. Nous vous dirons franchement quand une réparation n'a plus de sens."),
        ],
        "sources": [
            ("ADEME — Agence de la transition écologique", "https://www.ademe.fr/"),
            ("EssilorLuxottica", "https://www.essilorluxottica.com/"),
            ("Service-public.fr", "https://www.service-public.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/tendances-montures.jpg",
        "image_alt": "Gros plan élégant sur une paire de lunettes en acétate coloré posée sur un support en bois naturel",
        "date_display": "16 mars 2026",
        "date_iso": "2026-03-16",
        "body": ART_BODY_MATIERES_DURABLES,
    },
    {
        "slug": "renouveler-lunettes-sans-nouvelle-ordonnance-opticien",
        "category": "remboursements",
        "title": "Ordonnance de lunettes expirée ? Ce que l'opticien peut faire sans repasser par le médecin",
        "meta_title": "Renouveler ses lunettes sans ordonnance | Maison Mikis",
        "meta_description": "Votre ordonnance a quelques années ? L'opticien peut souvent renouveler et adapter votre correction sans nouvelle consultation. Durées, limites et exceptions.",
        "excerpt": "Il n'est pas toujours nécessaire de reprendre rendez-vous chez l'ophtalmologiste pour changer de lunettes.",
        "answer": "Une ordonnance de lunettes reste valable 1 an avant 16 ans, 5 ans entre 16 et 42 ans, et 3 ans au-delà. Dans ce délai, l'opticien peut renouveler l'équipement et adapter la correction, sauf opposition écrite du prescripteur ou situation particulière comme une presbytie découverte.",
        "faq": [
            ("J'ai perdu mon ordonnance, que faire ?",
             "Contactez le cabinet qui l'a établie : un duplicata est généralement délivré sans difficulté, parfois par simple appel ou par messagerie sécurisée. Si l'équipement a été réalisé chez nous, nous conservons la correction en dossier, mais un justificatif reste nécessaire pour toute prise en charge."),
            ("Le renouvellement par l'opticien est-il remboursé comme une consultation ?",
             "L'équipement est remboursé selon les règles habituelles, dès lors que la prescription est encore valable et que la périodicité de prise en charge est respectée. Le contrôle réalisé en magasin, lui, n'est pas un acte médical, ne donne lieu à aucun remboursement et n'est pas facturé chez nous."),
            ("Puis-je faire adapter une ordonnance obtenue dans un autre pays ?",
             "Cela dépend de sa forme et des mentions qu'elle comporte, qui varient beaucoup d'un pays à l'autre. Apportez-la : nous vérifions si elle répond aux exigences françaises. Dans le doute, une consultation en France reste la solution la plus sûre pour être correctement pris en charge."),
            ("Mon ophtalmologiste a coché une case interdisant l'adaptation, pourquoi ?",
             "Cette opposition est prévue par les textes et s'utilise lorsque le praticien souhaite revoir lui-même le patient, par exemple en cas de correction complexe ou de pathologie suivie de près. Elle s'impose à l'opticien, qui ne peut alors rien modifier et vous réoriente vers le cabinet."),
            ("Faut-il refaire un contrôle même si je vois bien ?",
             "C'est vivement recommandé. Une correction peut dériver très lentement sans que l'on s'en rende compte, et certaines pathologies oculaires débutent sans aucune gêne perceptible. Un contrôle régulier chez l'ophtalmologiste, complété entre deux consultations par une vérification chez nous, reste le bon réflexe."),
        ],
        "sources": [
            ("Service-public.fr", "https://www.service-public.fr/"),
            ("Assurance Maladie", "https://www.ameli.fr/"),
            ("Asnav", "https://www.asnav.org/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/conseils/lire-ordonnance.jpg",
        "image_alt": "Une ordonnance ophtalmologique posée à côté d'une paire de lunettes sur une table",
        "date_display": "25 mars 2026",
        "date_iso": "2026-03-25",
        "body": ART_BODY_RENOUVELER_ORDONNANCE,
    },
    {
        "slug": "otites-repetition-enfant-audition-langage",
        "category": "enfant",
        "title": "Otites à répétition chez le jeune enfant : quel impact sur l'audition et le langage ?",
        "meta_title": "Otites à répétition : audition et langage | Maison Mikis",
        "meta_description": "Les otites sont fréquentes avant 2 ans. Comprendre quand elles pèsent sur l'audition et le langage, et à quel moment faire vérifier l'ouïe de son enfant.",
        "excerpt": "Presque tous les enfants font une otite avant deux ans. Le plus souvent sans conséquence, parfois utile à surveiller.",
        "answer": "Une otite fait temporairement baisser l'audition, car du liquide s'accumule derrière le tympan. Isolée, elle est sans conséquence. Ce sont les épisodes qui se répètent ou l'épanchement qui persiste plusieurs semaines entre 1 et 3 ans qui méritent un contrôle de l'audition.",
        "faq": [
            ("Une otite laisse-t-elle des séquelles sur l'audition ?",
             "Dans l'immense majorité des cas, non : l'audition redevient normale une fois l'infection guérie et le liquide résorbé. Le risque concerne surtout les épisodes très répétés ou les épanchements qui persistent des mois, d'où l'intérêt d'un contrôle dans ces situations."),
            ("Mon fils fait quatre otites par hiver, est-ce anormal ?",
             "C'est fréquent chez les tout-petits en collectivité, mais ce rythme justifie d'en parler au médecin. Au-delà de trois à quatre épisodes en six mois, un avis ORL est généralement proposé afin de vérifier l'état du tympan et de mesurer l'audition."),
            ("Faut-il attendre la fin d'une otite pour tester l'audition ?",
             "Oui, sauf indication médicale contraire. Une mesure réalisée pendant l'épisode reflète la gêne du moment, pas l'audition habituelle de votre enfant. Le contrôle se fait donc à distance de la guérison, généralement quelques semaines après, pour obtenir un résultat vraiment interprétable."),
            ("Les bouchons d'oreilles ou l'eau favorisent-ils les otites ?",
             "L'otite moyenne concerne l'oreille moyenne, derrière le tympan, et n'est pas causée par l'eau du bain ou de la piscine. Les consignes de baignade dépendent de la situation, notamment après la pose d'aérateurs : seul le médecin qui suit l'enfant peut trancher."),
            ("À partir de quel âge peut-on mesurer l'audition d'un enfant ?",
             "Dès les premiers mois, avec des techniques adaptées et sans participation active. À partir de 2 ou 3 ans, l'examen prend la forme d'un jeu auquel l'enfant participe, ce qui donne des résultats fiables. Aucun âge n'est trop précoce en cas de doute."),
        ],
        "sources": [
            ("Assurance Maladie - ameli.fr", "https://www.ameli.fr/"),
            ("Ministère de la Santé", "https://sante.gouv.fr/"),
            ("Organisation mondiale de la santé", "https://www.who.int/fr"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/sante/myopie-enfant-signes.jpg",
        "image_alt": "Médecin réalisant un dépistage auditif chez un jeune enfant",
        "date_display": "30 mars 2026",
        "date_iso": "2026-03-30",
        "body": ART_BODY_OTITES_ENFANT,
    },
    {
        "slug": "essilor-varilux-immersia-verre-progressif-interieur",
        "category": "tech-verres",
        "title": "Varilux Immersia Mid et Room : le verre progressif Essilor pensé pour la vie à l'intérieur",
        "meta_title": "Varilux Immersia Mid et Room : le verre Essilor | Maison Mikis",
        "meta_description": "Varilux Immersia Mid (1,5 m) ou Room (3 m) : ce que change ce progressif d'intérieur Essilor, pour qui il est utile, et pourquoi il ne remplace pas votre paire.",
        "excerpt": "Essilor décline Varilux Immersia en deux versions, Mid et Room, pour les journées passées entre lecture, écrans et réunions.",
        "answer": "Varilux Immersia est un verre progressif d'Essilor conçu pour les distances proches et intermédiaires plutôt que pour la vision de loin. Il existe en deux versions : Immersia Mid, nette jusqu'à environ 1,5 mètre, pour la lecture et le travail sur plusieurs écrans ; Immersia Room, nette jusqu'à environ 3 mètres, pour se déplacer et échanger dans une pièce. Dans les deux cas, il complète une paire polyvalente et ne la remplace pas : il n'offre aucune vision de loin.",
        "faq": [
            ("Quelle est la différence entre Varilux Immersia Mid et Immersia Room ?",
             "La distance jusqu'à laquelle le verre reste net. La version Mid couvre environ 1,5 mètre, soit le rayon d'un bureau : écran, clavier, document papier, téléphone. La version Room va jusqu'à environ 3 mètres et permet de se déplacer dans une pièce et de voir les visages en réunion. Ce n'est pas un niveau de gamme mais un choix d'usage, qui se tranche en mesurant vos distances réelles de travail."),
            ("Varilux Immersia remplace-t-il le Varilux Digitime ?",
             "Immersia est la génération de progressifs d'intérieur qu'Essilor commercialise depuis avril 2026, dans la même logique que le Digitime qui l'a précédé : priorité aux distances proches et intermédiaires, pas de vision de loin. Si vous portez un Digitime et souhaitez renouveler, c'est vers cette gamme que votre opticien vous orientera. La comparaison utile se fait sur le confort ressenti et sur le devis, pas sur le nom commercial."),
            ("Qu'est-ce que la technologie AI Twinning ?",
             "C'est le nom qu'Essilor donne à la modélisation prédictive utilisée pour dessiner le verre : plutôt qu'une géométrie unique pour tous, le dessin est ajusté à partir d'une simulation du comportement visuel du porteur. Le verre intègre par ailleurs la technologie Wave 2.0, qui vise la netteté et les contrastes. Ces deux éléments sont présentés par le fabricant et décrivent une intention de conception, pas un résultat validé indépendamment."),
            ("Peut-on conduire avec ce type de verre ?",
             "Non. Un verre optimisé pour les distances proches et intermédiaires offre une vision de loin réduite, incompatible avec la conduite. Il s'utilise à l'intérieur, en complément d'une paire polyvalente que vous gardez pour les déplacements, l'extérieur et toute situation demandant une vision de loin nette."),
            ("Quelle différence avec un verre bureau classique ?",
             "Les verres dits bureau ou à faible dégression suivent la même logique de priorité aux courtes distances, avec des dessins et des gammes de prix très variés selon les fabricants. La comparaison se fait sur le champ de vision obtenu et sur le devis, pas sur le nom commercial."),
            ("Ce verre est-il pris en charge par l'Assurance Maladie ?",
             "Il relève des verres à prix libres, donc d'une prise en charge qui dépend de votre complémentaire santé. Une seconde paire est souvent moins bien couverte que la principale, et le renouvellement obéit à des règles de délai. Demandez un devis normalisé et interrogez votre mutuelle avant de commander."),
            ("Faut-il une nouvelle ordonnance pour l'essayer ?",
             "Une ordonnance en cours de validité est nécessaire. Si la vôtre date de plusieurs années ou si votre vision a changé, un nouvel examen s'impose. L'opticien peut ajuster une correction dans les cas prévus par la réglementation, mais la prescription initiale reste du ressort de l'ophtalmologiste."),
            ("L'adaptation est-elle plus facile qu'avec une paire polyvalente ?",
             "Souvent oui, parce que les zones utiles sont plus larges aux distances concernées. Cela reste variable d'une personne à l'autre. Portez la paire en continu dans son contexte d'usage plutôt que par intermittence, et revenez si la gêne persiste : un ajustement de monture règle beaucoup de cas."),
        ],
        "sources": [
            ("Essilor France", "https://www.essilor.fr/"),
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Institut national de recherche et de sécurité", "https://www.inrs.fr/"),
        ],
        "updated_display": "26 août 2026",
        "updated_iso": "2026-08-26",
        "image": "/images/actualites/tech-verres.jpg",
        "image_alt": "Personne travaillant sur un ordinateur portable avec des lunettes à verres correcteurs",
        "date_display": "14 avril 2026",
        "date_iso": "2026-04-14",
        "body": ART_BODY_VARILUX,
    },
]

# ---------------------------------------------------------------------------
# Articles ajoutes automatiquement par la veille hebdomadaire (GitHub Actions).
#
# Le fichier scripts/articles_auto.json contient une liste d'articles au meme
# format que ARTICLES ci-dessus. Il est ecrit par scripts/veille.py lors de
# l'execution hebdomadaire, puis relu ici : build.py reste ainsi le SEUL
# generateur du site, et un article ajoute automatiquement passe exactement par
# le meme gabarit, le meme maillage interne et le meme JSON-LD que les 24
# articles ecrits a la main.
#
# Les articles automatiques sont places EN TETE (les plus recents d'abord).
# L'ordre des 24 articles historiques n'est volontairement pas touche : il est
# curate, pas chronologique, et le reordonner changerait les 33 pages.
# ---------------------------------------------------------------------------
AUTO_ARTICLES_PATH = os.path.join(OUT_DIR, "scripts", "articles_auto.json")
AUTO_ARTICLE_FIELDS = (
    "slug", "category", "title", "meta_title", "meta_description", "excerpt",
    "answer", "faq", "sources", "image", "image_alt",
    "date_display", "date_iso", "body",
)


def load_auto_articles(path=AUTO_ARTICLES_PATH):
    """Relit les articles produits par la veille, en refusant tout ce qui est
    mal forme plutot que de generer une page bancale en production."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        raise SystemExit("articles_auto.json doit contenir une liste.")

    known = {a["slug"] for a in ARTICLES}
    out = []
    for entry in raw:
        missing = [k for k in AUTO_ARTICLE_FIELDS if k not in entry]
        if missing:
            raise SystemExit(f"article auto incomplet ({entry.get('slug')}) : {missing}")
        if entry["category"] not in ARTICLE_CATEGORIES:
            raise SystemExit(f"categorie inconnue : {entry['category']}")
        if entry["slug"] in known:
            raise SystemExit(f"slug deja utilise : {entry['slug']}")
        known.add(entry["slug"])
        entry = dict(entry)
        # JSON ne connait pas les tuples : on retablit la forme attendue.
        entry["faq"] = [tuple(x) for x in entry["faq"]]
        entry["sources"] = [tuple(x) for x in entry["sources"]]
        out.append(entry)

    out.sort(key=lambda a: a["date_iso"], reverse=True)
    return out


AUTO_ARTICLES = load_auto_articles()
ARTICLES = AUTO_ARTICLES + ARTICLES



def article_url(article):
    return f"actualites/{article['slug']}.html"


def article_jsonld(article):
    # BlogPosting plutot qu'Article : sous-type plus precis pour un blog,
    # toujours supporte par Google en 2026 (contrairement a FAQPage et HowTo,
    # dont les rich results ont ete supprimes). dateModified reflete la
    # reecriture SEO quand le champ `updated_iso` est renseigne.
    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": article["title"],
        "description": article["meta_description"],
        "image": f"{BASE_URL}{article['image']}",
        "datePublished": article["date_iso"],
        "dateModified": article.get("updated_iso", article["date_iso"]),
        "author": {"@type": "Organization", "name": "Maison Mikis"},
        "publisher": {
            "@type": "Organization",
            "name": "Maison Mikis",
            "logo": {"@type": "ImageObject", "url": f"{BASE_URL}/og-image.jpg"},
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{BASE_URL}/{article_url(article)}"},
    }
    return f'<script type="application/ld+json">\n{json.dumps(data, ensure_ascii=False, indent=2)}\n</script>'


def render_article_card(article):
    cat = ARTICLE_CATEGORIES[article["category"]]
    # Carte "bulle" : reste un vrai lien <a href> (fonctionne sans JS, SEO/partage
    # intacts — chaque article garde sa propre page), mais un clic normal est
    # intercepté en JS pour agrandir la bulle sur place plutôt que de naviguer
    # (voir le script "bulles Actualités" plus bas et .article-modal-* en CSS).
    return (
        f'      <a href="/{article_url(article)}" class="article-card reveal" data-category="{article["category"]}">\n'
        f'        <div class="article-img"><img src="{article["image"]}" alt="{article["image_alt"]}" loading="lazy"></div>\n'
        f'        <div class="article-card-body">\n'
        f'          <span class="article-tag" style="--accent:{cat["accent"]};--accent-bg:{cat["accent_bg"]};">{cat["label"]}</span>\n'
        f'          <h3>{article["title"]}</h3>\n'
        f'          <p>{article["excerpt"]}</p>\n'
        f'          <div class="article-meta"><span>{article["date_display"]}</span><span class="more">Lire l\'article <span aria-hidden="true">⤢</span></span></div>\n'
        f'        </div>\n'
        f'      </a>'
    )


# ============================================================================
# MAILLAGE INTERNE (31/07/2026)
# ----------------------------------------------------------------------------
# Constat avant travaux : sur 24 articles, seulement 2 liens contextuels vers
# le reste du site, et aucune page de service ne renvoyait vers un article.
# Trois mecanismes sont mis en place ici :
#   1. INLINE_LINKS  : liens contextuels poses dans le corps des articles, au
#      moment du rendu. Le plan est de la donnee, pas du HTML fige : les corps
#      ART_BODY_* restent lisibles et le plan est verifiable d'un coup d'oeil.
#   2. GO_FURTHER    : encadre "Pour aller plus loin" en fin d'article.
#   3. PAGE_ARTICLES : bloc "Nos articles sur le sujet" sur les pages de
#      service, insere juste avant le CTA final.
# Le bloc "A lire aussi" passe par ailleurs d'une rotation chronologique
# (idx+1, +2, +3 — souvent hors sujet) a une selection par categorie.
# ============================================================================

def _link_forbidden_spans(html):
    """Zones ou l'on n'insere jamais de lien : titres, liens existants, citations."""
    spans = []
    for m in re.finditer(r'<h[1-6][^>]*>.*?</h[1-6]>', html, re.S | re.I):
        spans.append(m.span())
    for m in re.finditer(r'<a\b.*?</a>', html, re.S | re.I):
        spans.append(m.span())
    for m in re.finditer(r'<(figcaption|blockquote)\b.*?</\1>', html, re.S | re.I):
        spans.append(m.span())
    return spans


def _link_candidates(html, phrase):
    bad = _link_forbidden_spans(html)
    out = []
    for m in re.finditer(re.escape(phrase), html):
        start, end = m.span()
        lt = html.rfind('<', 0, start)
        gt = html.rfind('>', 0, start)
        if lt > gt:            # position situee a l'interieur d'une balise
            continue
        if any(a <= start < b for a, b in bad):
            continue
        out.append((start, end))
    return out


LINK_WARNINGS = []


def apply_inline_links(html, plan, context=""):
    """plan : liste de (phrase, href) ou (phrase, href, occurrence)."""
    for item in plan:
        phrase, href = item[0], item[1]
        occ = item[2] if len(item) > 2 else 1
        cands = _link_candidates(html, phrase)
        if len(cands) < occ:
            LINK_WARNINGS.append(
                "%s : phrase %r introuvable (occurrence %d demandee, %d disponible(s))"
                % (context, phrase, occ, len(cands)))
            continue
        start, end = cands[occ - 1]
        html = html[:start] + '<a href="%s">%s</a>' % (href, html[start:end]) + html[end:]
    return html


# --- Liens contextuels, article par article --------------------------------
INLINE_LINKS = {
    "fatigue-oculaire-ecrans": [
        ("lumière bleue", "/nos-conseils.html#traitements-verres"),
        ("correction", "/espace-sante.html#defauts"),
        ("fatigue visuelle", "/actualites/ecrans-myopie-enfant-habitudes-protectrices.html"),
    ],
    "perte-auditive-signes-precoces": [
        ("bilan auditif", "/index.html#test-auditif"),
        ("acouphènes", "/actualites/acouphenes-comprendre-bruit-qui-ne-sarrete-jamais.html"),
        ("bilan auditif", "/espace-audition.html"),  # 2e occurrence : la 1re est deja liee
    ],
    "tendances-montures-2026": [
        ("écaille", "/marques.html"),
        ("métal", "/actualites/lunettes-engagees-matieres-durables-eco-responsables.html"),
        ("essayer", "/contact.html"),
    ],
    "nouvelles-technologies-verres-correcteurs": [
        ("verres progressifs", "/actualites/essilor-varilux-immersia-verre-progressif-interieur.html"),
        ("myopie", "/espace-sante.html#myopie-enfant"),
        ("traitements", "/nos-conseils.html#traitements-verres"),
    ],
    "nouvelles-technologies-lentilles-contact": [
        ("lentilles", "/nos-conseils.html#lunettes-ou-lentilles"),
        ("presbytie", "/actualites/presbytie-comprendre-ce-trouble-de-la-vision.html"),
        ("astigmatisme", "/espace-sante.html#defauts"),
    ],
    "100-pour-cent-sante-2026": [
        ("devis normalisé", "/actualites/comprendre-devis-normalise-lunettes-aides-auditives.html"),
        ("monture", "/marques.html"),
        ("classe A", "/nos-conseils.html#type-verres"),
    ],
    "pourquoi-sudaya-mikhael-ont-ouvert-maison-mikis": [
        ("Olympiades", "/contact.html"),
        ("quartier", "/actualites/nouvel-an-lunaire-triangle-de-choisy.html", 2),
    ],
    "signes-troubles-visuels-auditifs-enfant": [
        ("dépistage", "/espace-sante.html#myopie-enfant"),
        ("audition", "/espace-audition.html"),
    ],
    "lentilles-hebdomadaires-precision7-alcon": [
        ("lentilles", "/nos-conseils.html#lunettes-ou-lentilles"),
        ("Alcon", "/actualites/nouvelles-technologies-lentilles-contact.html", 2),
        ("entretien", "/nos-conseils.html#entretien-lunettes"),
    ],
    "proteger-yeux-soleil-uv": [
        ("lunettes de soleil", "/marques.html"),
        ("cataracte", "/espace-sante.html#maladies"),
        ("catégorie 3", "/nos-conseils.html#type-verres"),
    ],
    "lentilles-rigides-asana-bausch-lomb": [
        ("lentilles rigides", "/nos-conseils.html#lunettes-ou-lentilles"),
        ("kératocône", "/espace-sante.html#maladies"),
        ("opticien", "/contact.html"),
    ],
    "casques-ecouteurs-proteger-audition-jeunes": [
        ("bilan auditif", "/index.html#test-auditif"),
        ("volume", "/actualites/acouphenes-comprendre-bruit-qui-ne-sarrete-jamais.html", 2),
    ],
    "lunettes-connectees-ray-ban-meta-mode-tech": [
        ("Ray-Ban", "/marques.html#ray-ban", 2),
        ("monture", "/actualites/tendances-montures-2026.html", 2),
        ("opticien", "/nos-conseils.html#type-verres"),
    ],
    "ecrans-myopie-enfant-habitudes-protectrices": [
        ("myopie", "/espace-sante.html#myopie-enfant"),
        ("enfant", "/actualites/signes-troubles-visuels-auditifs-enfant.html", 2),
        ("montures", "/marques.html"),
    ],
    "comprendre-devis-normalise-lunettes-aides-auditives": [
        ("reste à charge", "/actualites/100-pour-cent-sante-2026.html"),
        ("aides auditives", "/espace-audition.html"),
        ("lentilles", "/nos-conseils.html#lunettes-ou-lentilles"),
    ],
    "une-journee-type-a-la-boutique": [
        ("monture", "/marques.html"),
        ("ordonnance", "/index.html#examen-de-vue"),
        ("rendez-vous", "/contact.html", 2),
    ],
    "novacel-celene-traitement-anti-reflet-teinte-nude": [
        ("anti-reflet", "/nos-conseils.html#traitements-verres"),
        ("monture", "/marques.html"),
        ("Novacel", "/actualites/nouvelles-technologies-verres-correcteurs.html", 2),
    ],
    "presbytie-comprendre-ce-trouble-de-la-vision": [
        ("verres progressifs", "/nos-conseils.html#type-verres"),
        ("opticien", "/index.html#examen-de-vue"),
        ("lentilles", "/actualites/nouvelles-technologies-lentilles-contact.html"),
    ],
    "nouvel-an-lunaire-triangle-de-choisy": [
        ("Triangle de Choisy", "/notre-histoire.html"),
        ("vitrine", "/contact.html", 2),
        ("montures", "/marques.html"),
    ],
    "acouphenes-comprendre-bruit-qui-ne-sarrete-jamais": [
        ("bilan auditif", "/index.html#test-auditif"),
        ("audition", "/espace-audition.html", 2),
        ("ORL", "/actualites/perte-auditive-signes-precoces.html", 2),
    ],
    "lunettes-engagees-matieres-durables-eco-responsables": [
        ("montures", "/marques.html"),
        ("marque", "/actualites/tendances-montures-2026.html", 2),
        ("recyclé", "/nos-conseils.html#choix-monture"),
    ],
    "renouveler-lunettes-sans-nouvelle-ordonnance-opticien": [
        ("examen de vue", "/index.html#examen-de-vue"),
        ("presbytie", "/actualites/presbytie-comprendre-ce-trouble-de-la-vision.html", 2),
        ("ordonnance", "/nos-conseils.html#lire-ordonnance", 3),
    ],
    "otites-repetition-enfant-audition-langage": [
        ("audiogramme", "/espace-audition.html"),
        ("langage", "/actualites/signes-troubles-visuels-auditifs-enfant.html", 2),
        ("enfant", "/espace-sante.html#myopie-enfant", 3),
    ],
    "essilor-varilux-immersia-verre-progressif-interieur": [
        ("verres progressifs", "/nos-conseils.html#type-verres"),
        ("presbyte", "/actualites/presbytie-comprendre-ce-trouble-de-la-vision.html"),
        ("Varilux", "/actualites/nouvelles-technologies-verres-correcteurs.html"),
    ],
}

# --- Encadre "Pour aller plus loin" ----------------------------------------
GO_FURTHER = {
    "fatigue-oculaire-ecrans": [
        ("/index.html#examen-de-vue", "Faire contrôler sa vue en boutique, sans rendez-vous",
         "Un examen de vue gratuit pour vérifier que votre correction est toujours la bonne."),
        ("/nos-conseils.html#traitements-verres", "Les traitements de verres, expliqués simplement",
         "Anti-reflet, anti-lumière bleue, anti-rayure : lesquels servent vraiment à quoi."),
        ("/actualites/presbytie-comprendre-ce-trouble-de-la-vision.html", "Presbytie : ce qui change après 45 ans",
         "Quand la fatigue de près n'est plus seulement une histoire d'écrans."),
    ],
    "perte-auditive-signes-precoces": [
        ("/espace-audition.html", "Découvrir notre Espace Audition",
         "Bilan, appareillage, réglages et suivi : comment nous vous accompagnons."),
        ("/index.html#test-auditif", "Le test auditif gratuit, sur rendez-vous",
         "Une heure en cabine isolée pour savoir précisément où vous en êtes."),
        ("/actualites/acouphenes-comprendre-bruit-qui-ne-sarrete-jamais.html", "Acouphènes : comprendre ce bruit permanent",
         "Souvent associés à une baisse d'audition, rarement pris au sérieux assez tôt."),
    ],
    "tendances-montures-2026": [
        ("/marques.html", "Voir toutes nos marques de montures",
         "Ray-Ban, Prada, Loewe, Celine, Miu Miu et une vingtaine d'autres, en boutique."),
        ("/nos-conseils.html#choix-monture", "Bien choisir sa monture",
         "Morphologie, teint, correction : les critères qui comptent vraiment."),
        ("/actualites/lunettes-engagees-matieres-durables-eco-responsables.html", "Les montures en matières durables",
         "Bio-acétate, métal recyclé : la mode optique change de matériaux."),
    ],
    "nouvelles-technologies-verres-correcteurs": [
        ("/nos-conseils.html#type-verres", "Quel type de verres pour quelle correction",
         "Unifocaux, progressifs, dégressifs : le repère avant de choisir."),
        ("/espace-sante.html#myopie-enfant", "La myopie de l'enfant",
         "Pourquoi elle progresse, et ce que les verres de freination peuvent faire."),
        ("/actualites/essilor-varilux-immersia-verre-progressif-interieur.html", "Varilux Immersia, le progressif d'intérieur",
         "Le dernier né des verres progressifs, pensé pour la vie en intérieur."),
    ],
    "nouvelles-technologies-lentilles-contact": [
        ("/nos-conseils.html#lunettes-ou-lentilles", "Lunettes ou lentilles : comment choisir",
         "Les avantages et les limites de chaque solution, sans idées reçues."),
        ("/actualites/lentilles-hebdomadaires-precision7-alcon.html", "Precision7 : la lentille hebdomadaire d'Alcon",
         "Un rythme de port inédit entre la journalière et la mensuelle."),
        ("/contact.html", "Venir en parler en boutique",
         "L'adaptation d'une lentille se fait toujours en essai accompagné."),
    ],
    "100-pour-cent-sante-2026": [
        ("/actualites/comprendre-devis-normalise-lunettes-aides-auditives.html", "Lire un devis normalisé",
         "Le document qui vous dit exactement ce que vous payez, et pourquoi."),
        ("/espace-audition.html", "Le 100 % Santé côté audition",
         "Appareils de classe 1, essai de 30 jours et suivi inclus pendant 4 ans."),
        ("/contact.html", "Faire le point sur vos droits avec nous",
         "Nous vérifions votre couverture et appliquons le tiers payant quand c'est possible."),
    ],
    "pourquoi-sudaya-mikhael-ont-ouvert-maison-mikis": [
        ("/notre-histoire.html", "Lire toute notre histoire",
         "De la rencontre au projet, jusqu'à l'ouverture Galerie Oslo."),
        ("/actualites/une-journee-type-a-la-boutique.html", "Une journée type à la boutique",
         "Ce qui se passe vraiment entre l'ouverture et la fermeture du rideau."),
        ("/contact.html", "Venir nous rencontrer",
         "Galerie Oslo, Esplanade des Olympiades, Paris 13e."),
    ],
    "signes-troubles-visuels-auditifs-enfant": [
        ("/espace-sante.html#myopie-enfant", "La vue de l'enfant, âge par âge",
         "Ce qu'il faut surveiller et à quel moment consulter."),
        ("/actualites/otites-repetition-enfant-audition-langage.html", "Otites à répétition et langage",
         "Quand une audition fluctuante freine l'apprentissage de la parole."),
        ("/actualites/ecrans-myopie-enfant-habitudes-protectrices.html", "Écrans, temps dehors et myopie",
         "Les habitudes qui protègent réellement les yeux d'un enfant."),
    ],
    "lentilles-hebdomadaires-precision7-alcon": [
        ("/nos-conseils.html#lunettes-ou-lentilles", "Lunettes ou lentilles : comment choisir",
         "Les deux solutions ne s'opposent pas, elles se complètent."),
        ("/actualites/nouvelles-technologies-lentilles-contact.html", "Les nouveautés en lentilles de contact",
         "Matériaux, rythmes de port, corrections complexes : où en est-on."),
        ("/contact.html", "Demander un essai en boutique",
         "Une lentille ne se choisit jamais sans essai ni contrôle d'adaptation."),
    ],
    "proteger-yeux-soleil-uv": [
        ("/marques.html", "Nos solaires, marque par marque",
         "Une sélection de solaires à verres correcteurs ou non."),
        ("/espace-sante.html#maladies", "Les maladies de l'œil liées au soleil",
         "Cataracte, DMLA, ptérygion : ce que les UV provoquent à long terme."),
        ("/nos-conseils.html#type-verres", "Choisir la bonne catégorie de verre solaire",
         "De la catégorie 0 à la catégorie 4 : à quel usage correspond chacune."),
    ],
    "lentilles-rigides-asana-bausch-lomb": [
        ("/espace-sante.html#maladies", "Kératocône et cornées irrégulières",
         "Pourquoi certaines cornées demandent une lentille rigide."),
        ("/actualites/nouvelles-technologies-lentilles-contact.html", "Les nouveautés en lentilles de contact",
         "Le panorama complet des matériaux et rythmes de port."),
        ("/contact.html", "Prendre rendez-vous pour une adaptation",
         "L'adaptation d'une lentille rigide demande plusieurs contrôles."),
    ],
    "casques-ecouteurs-proteger-audition-jeunes": [
        ("/index.html#test-auditif", "Le test auditif gratuit en boutique",
         "Un bilan complet, sur rendez-vous, sans aucun engagement."),
        ("/actualites/acouphenes-comprendre-bruit-qui-ne-sarrete-jamais.html", "Acouphènes : le signal d'alerte",
         "Le premier symptôme d'une exposition sonore trop forte, souvent ignoré."),
        ("/actualites/perte-auditive-signes-precoces.html", "Les signes précoces d'une perte auditive",
         "7 à 10 ans s'écoulent en moyenne avant la première consultation."),
    ],
    "lunettes-connectees-ray-ban-meta-mode-tech": [
        ("/marques.html#ray-ban", "Ray-Ban chez Maison Mikis",
         "Wayfarer, Aviator, Clubmaster : les modèles disponibles en boutique."),
        ("/actualites/tendances-montures-2026.html", "Les tendances montures 2026",
         "Formes, matières et couleurs qui marquent la saison."),
        ("/nos-conseils.html#type-verres", "Monter des verres correcteurs sur une solaire",
         "Ce qui est possible, et ce qui ne l'est pas, selon la correction."),
    ],
    "ecrans-myopie-enfant-habitudes-protectrices": [
        ("/espace-sante.html#myopie-enfant", "La myopie de l'enfant expliquée",
         "Mécanismes, facteurs de risque et solutions de freination."),
        ("/actualites/signes-troubles-visuels-auditifs-enfant.html", "Repérer un trouble visuel chez son enfant",
         "Les signes que les parents voient avant le dépistage scolaire."),
        ("/contact.html", "Faire contrôler la vue de votre enfant",
         "Avant 16 ans, le passage par l'ophtalmologiste reste nécessaire — nous vous guidons."),
    ],
    "comprendre-devis-normalise-lunettes-aides-auditives": [
        ("/actualites/100-pour-cent-sante-2026.html", "Le 100 % Santé en 2026",
         "Ce qui est réellement pris en charge, en optique comme en audition."),
        ("/nos-conseils.html#lire-ordonnance", "Savoir lire son ordonnance",
         "Sphère, cylindre, axe, addition : décoder les chiffres du prescripteur."),
        ("/contact.html", "Demander un devis gratuit",
         "Le devis normalisé est gratuit et sans engagement, avant tout achat."),
    ],
    "une-journee-type-a-la-boutique": [
        ("/notre-histoire.html", "Notre histoire, depuis le début",
         "Pourquoi Sudaya et Mikhael ont ouvert Maison Mikis en 2023."),
        ("/marques.html", "Les marques que nous sélectionnons",
         "Ce qui entre en vitrine, et selon quels critères."),
        ("/contact.html", "Passer nous voir",
         "Galerie Oslo, Esplanade des Olympiades — sans rendez-vous pour l'optique."),
    ],
    "novacel-celene-traitement-anti-reflet-teinte-nude": [
        ("/nos-conseils.html#traitements-verres", "Tous les traitements de verres",
         "Anti-reflet, hydrophobe, anti-rayure : à quoi sert chaque couche."),
        ("/actualites/nouvelles-technologies-verres-correcteurs.html", "Les innovations verres du moment",
         "Photochromiques, freination de la myopie, verres bureau."),
        ("/contact.html", "Voir le rendu en boutique",
         "Un traitement esthétique se juge à l'œil, sur votre monture."),
    ],
    "presbytie-comprendre-ce-trouble-de-la-vision": [
        ("/espace-sante.html#defauts", "Les défauts visuels expliqués",
         "Myopie, hypermétropie, astigmatisme, presbytie : les distinguer."),
        ("/nos-conseils.html#type-verres", "Progressifs, dégressifs ou double foyer",
         "Quel verre pour quel usage quand la vision de près baisse."),
        ("/actualites/essilor-varilux-immersia-verre-progressif-interieur.html", "Varilux Immersia",
         "Un progressif conçu pour les distances de la vie en intérieur."),
    ],
    "nouvel-an-lunaire-triangle-de-choisy": [
        ("/notre-histoire.html", "Notre histoire dans ce quartier",
         "Pourquoi nous avons choisi les Olympiades pour ouvrir."),
        ("/actualites/une-journee-type-a-la-boutique.html", "Une journée type à la boutique",
         "Le quotidien vu de l'intérieur, entre optique et audition."),
        ("/contact.html", "Venir nous voir Galerie Oslo",
         "Adresse, horaires et accès en métro, bus ou à pied."),
    ],
    "acouphenes-comprendre-bruit-qui-ne-sarrete-jamais": [
        ("/espace-audition.html", "Notre Espace Audition",
         "Bilan, appareillage et accompagnement, y compris en cas d'acouphènes."),
        ("/index.html#test-auditif", "Faire un bilan auditif gratuit",
         "Sur rendez-vous, en cabine isolée, sans engagement."),
        ("/actualites/casques-ecouteurs-proteger-audition-jeunes.html", "Protéger son audition au casque",
         "La première cause évitable d'acouphènes chez les moins de 35 ans."),
    ],
    "lunettes-engagees-matieres-durables-eco-responsables": [
        ("/marques.html", "Nos marques en boutique",
         "Une sélection où les démarches durables ont toute leur place."),
        ("/nos-conseils.html#choix-monture", "Bien choisir sa monture",
         "La matière n'est pas qu'un argument : elle change le confort au quotidien."),
        ("/actualites/tendances-montures-2026.html", "Les tendances 2026",
         "Formes et couleurs de la saison, matières durables comprises."),
    ],
    "renouveler-lunettes-sans-nouvelle-ordonnance-opticien": [
        ("/index.html#examen-de-vue", "L'examen de vue gratuit en boutique",
         "Sans rendez-vous : c'est lui qui permet d'adapter votre correction."),
        ("/nos-conseils.html#quand-changer", "Quand faut-il changer de lunettes",
         "Les signes qui indiquent qu'un équipement n'est plus adapté."),
        ("/actualites/100-pour-cent-sante-2026.html", "Vos remboursements en 2026",
         "Une ordonnance adaptée par l'opticien reste intégralement remboursable."),
    ],
    "otites-repetition-enfant-audition-langage": [
        ("/espace-audition.html", "Notre Espace Audition",
         "Nous réalisons les bilans auditifs de l'enfant comme de l'adulte."),
        ("/actualites/signes-troubles-visuels-auditifs-enfant.html", "Repérer un trouble auditif chez l'enfant",
         "Les signaux d'alerte, âge par âge, côté vue comme côté audition."),
        ("/contact.html", "Prendre rendez-vous pour un bilan",
         "Un bilan auditif enfant demande du temps et un environnement calme."),
    ],
    "essilor-varilux-immersia-verre-progressif-interieur": [
        ("/nos-conseils.html#type-verres", "Comprendre les verres progressifs",
         "Comment fonctionne un progressif et à qui il s'adresse."),
        ("/actualites/presbytie-comprendre-ce-trouble-de-la-vision.html", "La presbytie expliquée",
         "Pourquoi la vision de près baisse à partir de 45 ans."),
        ("/contact.html", "Essayer en boutique",
         "Un progressif se choisit après mesures précises et essai."),
    ],
}


# ============================================================================
# MAILLAGE INTERNE DES ARTICLES AUTOMATIQUES
#
# Les 24 articles ecrits a la main ont un plan de liens redige a la main
# (INLINE_LINKS et GO_FURTHER ci-dessus). Un article produit par la veille
# hebdomadaire n'en a pas : on le lui fabrique ici, de facon deterministe.
#
# Choix assume : les URL cibles sont ecrites EN DUR dans ce fichier, jamais
# proposees par le modele qui redige l'article. Un lien interne casse est
# invisible pour le visiteur jusqu'au clic, et couteux en referencement ; la
# seule facon de le rendre impossible est que la veille n'ait pas son mot a
# dire sur les adresses. Le modele ecrit le texte, build.py pose les liens.
# ============================================================================

# Ordre = priorite. On garde les trois premieres expressions trouvees dans le
# corps de l'article, une occurrence chacune, jamais dans un titre ni dans un
# lien existant (apply_inline_links s'en charge deja).
AUTO_INLINE_KEYWORDS = [
    ("bilan auditif", "/index.html#test-auditif"),
    ("aides auditives", "/espace-audition.html"),
    ("appareils auditifs", "/espace-audition.html"),
    ("audioprothesiste", "/espace-audition.html"),
    ("audioprothésiste", "/espace-audition.html"),
    ("acouphènes", "/actualites/acouphenes-comprendre-bruit-qui-ne-sarrete-jamais.html"),
    ("examen de vue", "/index.html#examen-de-vue"),
    ("verres progressifs", "/nos-conseils.html#type-verres"),
    ("presbytie", "/actualites/presbytie-comprendre-ce-trouble-de-la-vision.html"),
    ("myopie", "/espace-sante.html#myopie-enfant"),
    ("astigmatisme", "/espace-sante.html#defauts"),
    ("lumière bleue", "/nos-conseils.html#traitements-verres"),
    ("fatigue visuelle", "/actualites/fatigue-oculaire-ecrans.html"),
    ("100&nbsp;% Santé", "/actualites/100-pour-cent-sante-2026.html"),
    ("100 % Santé", "/actualites/100-pour-cent-sante-2026.html"),
    ("lentilles de contact", "/nos-conseils.html#lunettes-ou-lentilles"),
    ("verres", "/nos-conseils.html#traitements-verres"),
    ("monture", "/marques.html"),
    ("Olympiades", "/contact.html"),
]
AUTO_INLINE_MAX = 3

# Deux pages de service par categorie ; le troisieme lien de l'encadre "Pour
# aller plus loin" est calcule plus bas, en pointant vers l'article existant le
# plus recent de la meme categorie (donc toujours une URL qui existe).
AUTO_GO_FURTHER_PAGES = {
    "sante-visuelle": [
        ("/espace-sante.html", "Notre Espace Santé Visuelle",
         "Examen de vue, dépistage et suivi de la correction en boutique."),
        ("/index.html#examen-de-vue", "L'examen de vue gratuit",
         "Sans rendez-vous, une vingtaine de minutes."),
    ],
    "sante-auditive": [
        ("/espace-audition.html", "Notre Espace Audition",
         "Bilan auditif, appareillage et suivi, en cabine isolée."),
        ("/index.html#test-auditif", "Faire un bilan auditif gratuit",
         "Sur rendez-vous, sans engagement."),
    ],
    "mode-lunettes": [
        ("/marques.html", "Nos marques en boutique",
         "La sélection que nous portons et défendons."),
        ("/nos-conseils.html#choix-monture", "Bien choisir sa monture",
         "Forme, matière, proportions : ce qui change vraiment le confort."),
    ],
    "tech-verres": [
        ("/nos-conseils.html#type-verres", "Quel type de verre pour quel usage",
         "Unifocaux, progressifs, dégressifs : les distinguer."),
        ("/nos-conseils.html#traitements-verres", "Les traitements de verres",
         "Anti-reflet, durcissement, filtres : à quoi ils servent."),
    ],
    "tech-lentilles": [
        ("/nos-conseils.html#lunettes-ou-lentilles", "Lunettes ou lentilles",
         "Les critères qui font pencher d'un côté ou de l'autre."),
        ("/espace-sante.html", "Notre Espace Santé Visuelle",
         "Adaptation, contrôle et suivi des porteurs de lentilles."),
    ],
    "remboursements": [
        ("/actualites/100-pour-cent-sante-2026.html", "Vos remboursements en 2026",
         "Ce que couvre le 100&nbsp;% Santé, en optique comme en audition."),
        ("/contact.html", "Poser vos questions en boutique",
         "Nous établissons le devis normalisé et vérifions vos droits."),
    ],
    "vie-boutique": [
        ("/notre-histoire.html", "Notre histoire dans ce quartier",
         "Pourquoi nous avons choisi les Olympiades pour ouvrir."),
        ("/contact.html", "Venir nous voir Galerie Oslo",
         "Adresse, horaires et accès en métro, bus ou à pied."),
    ],
    "enfant": [
        ("/espace-sante.html#myopie-enfant", "Le dépistage chez l'enfant",
         "Repérer tôt, freiner la progression de la myopie."),
        ("/espace-audition.html", "Notre Espace Audition",
         "Nous réalisons aussi les bilans auditifs de l'enfant."),
    ],
}
AUTO_GO_FURTHER_FALLBACK = [
    ("/espace-sante.html", "Notre Espace Santé Visuelle",
     "Examen de vue, dépistage et suivi de la correction en boutique."),
    ("/contact.html", "Venir nous voir Galerie Oslo",
     "Adresse, horaires et accès en métro, bus ou à pied."),
]


def _auto_inline_plan(article):
    """Choisit jusqu'a AUTO_INLINE_MAX liens contextuels pour un article auto."""
    body = article["body"]
    own_url = "/%s" % article_url(article)
    plan, used_targets = [], set()
    for phrase, href in AUTO_INLINE_KEYWORDS:
        if len(plan) >= AUTO_INLINE_MAX:
            break
        if href in used_targets or href == own_url:
            continue
        if not _link_candidates(body, phrase):
            continue
        plan.append((phrase, href))
        used_targets.add(href)
    return plan


def _auto_go_further(article):
    """Deux pages de service + l'article existant le plus recent de la categorie."""
    items = list(AUTO_GO_FURTHER_PAGES.get(article["category"], AUTO_GO_FURTHER_FALLBACK))
    same = [a for a in ARTICLES
            if a["category"] == article["category"] and a["slug"] != article["slug"]]
    same.sort(key=lambda a: a["date_iso"], reverse=True)
    for candidate in same:
        href = "/%s" % article_url(candidate)
        if any(href == h for h, _l, _d in items):
            continue
        items.append((href, candidate["title"], candidate["excerpt"]))
        break
    return items[:3]


for _auto in AUTO_ARTICLES:
    if _auto["slug"] not in INLINE_LINKS:
        INLINE_LINKS[_auto["slug"]] = _auto_inline_plan(_auto)
    if _auto["slug"] not in GO_FURTHER:
        GO_FURTHER[_auto["slug"]] = _auto_go_further(_auto)


def render_go_further(article):
    items = GO_FURTHER.get(article["slug"])
    if not items:
        return ""
    lis = "\n".join(
        '        <li><span class="arrow" aria-hidden="true">→</span>'
        '<a href="%s">%s<span class="go-desc">%s</span></a></li>' % (href, label, desc)
        for href, label, desc in items
    )
    return """
    <div class="go-further">
      <span class="eyebrow">Pour aller plus loin</span>
      <h3>À lire et à voir sur le site</h3>
      <ul>
%s
      </ul>
    </div>
""" % lis


# --- Gabarit SEO : bloc reponse en tete + FAQ visible ----------------------
def render_answer_lead(article):
    """Reponse directe de 40-60 mots, juste sous le titre.

    Champ optionnel `answer` de l'article. Absent => rien n'est rendu, les
    anciens articles restent valides.
    """
    ans = article.get("answer")
    if not ans:
        return ""
    return """
    <div class="answer-lead">
      <span class="eyebrow">En bref</span>
      <p>%s</p>
    </div>
""" % ans


def render_faq(article):
    """FAQ visible en HTML (champ optionnel `faq` : liste de (question, reponse)).

    Volontairement sans balisage FAQPage : Google a supprime le rich result
    FAQ en mai-juin 2026. Le format garde sa valeur pour le lecteur et pour
    les moteurs de reponse, mais on n'attend plus d'affichage enrichi.
    """
    items = article.get("faq")
    if not items:
        return ""
    blocks = "\n".join(
        '      <div class="faq-item">\n'
        '        <h3>%s</h3>\n'
        '        <p>%s</p>\n'
        '      </div>' % (q, a)
        for q, a in items
    )
    return """
    <div class="article-faq">
      <h2>Questions fréquentes</h2>
      <p class="faq-intro">Les questions qu'on nous pose le plus souvent en boutique sur ce sujet.</p>
%s
    </div>
""" % blocks


def source_note(article):
    """Encart de sources en fin d'article.

    Si l'article renseigne `sources` (liste de (nom, url)), on les cite
    nommement avec un lien : c'est un signal E-E-A-T important sur un sujet
    sante, et c'est ce qui rend un contenu citable par les moteurs de reponse.
    Sinon on retombe sur la note generique historique.
    """
    srcs = article.get("sources")
    updated = article.get("updated_display")
    base = ("Contenu rédigé par l'équipe Maison Mikis à partir de sources "
            "professionnelles vérifiées (fabricants, presse spécialisée, "
            "autorités de santé)")
    if srcs:
        links = ", ".join('<a href="%s" rel="nofollow noopener" target="_blank">%s</a>' % (u, n)
                          for n, u in srcs)
        base = ("Contenu rédigé par l'équipe Maison Mikis. Sources consultées "
                "pour cet article : " + links)
    if updated:
        base += ". Mis à jour le %s" % updated
    return base + "."


def related_articles(article, count=3):
    """Selection thematique : meme categorie d'abord, puis les plus recents.

    Remplace la rotation chronologique d'origine (idx+1, +2, +3), qui pouvait
    faire suivre un article sur l'audition de trois articles sur les montures.
    """
    others = [a for a in ARTICLES if a["slug"] != article["slug"]]
    same = [a for a in others if a["category"] == article["category"]]
    rest = [a for a in others if a["category"] != article["category"]]
    same.sort(key=lambda a: a["date_iso"], reverse=True)
    rest.sort(key=lambda a: a["date_iso"], reverse=True)
    return (same + rest)[:count]


# --- Bloc "Nos articles sur le sujet" sur les pages de service -------------
PAGE_ARTICLES = {
    "espace-sante.html": (
        "Comprendre sa vue",
        ["presbytie-comprendre-ce-trouble-de-la-vision",
         "fatigue-oculaire-ecrans",
         "ecrans-myopie-enfant-habitudes-protectrices"],
    ),
    "espace-audition.html": (
        "Comprendre son audition",
        ["perte-auditive-signes-precoces",
         "acouphenes-comprendre-bruit-qui-ne-sarrete-jamais",
         "casques-ecouteurs-proteger-audition-jeunes"],
    ),
    "nos-conseils.html": (
        "Aller plus loin",
        ["nouvelles-technologies-verres-correcteurs",
         "renouveler-lunettes-sans-nouvelle-ordonnance-opticien",
         "comprendre-devis-normalise-lunettes-aides-auditives"],
    ),
    "marques.html": (
        "Mode & tendances",
        ["tendances-montures-2026",
         "lunettes-engagees-matieres-durables-eco-responsables",
         "lunettes-connectees-ray-ban-meta-mode-tech"],
    ),
    "notre-histoire.html": (
        "Vie de la boutique",
        ["pourquoi-sudaya-mikhael-ont-ouvert-maison-mikis",
         "une-journee-type-a-la-boutique",
         "nouvel-an-lunaire-triangle-de-choisy"],
    ),
}


def render_page_articles(path):
    entry = PAGE_ARTICLES.get(path)
    if not entry:
        return ""
    eyebrow, slugs = entry
    by_slug = {a["slug"]: a for a in ARTICLES}
    chosen = [by_slug[s] for s in slugs if s in by_slug]
    if not chosen:
        return ""
    return """
<section class="related-articles story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">%s</span>
      <h2>Nos articles sur le sujet</h2>
    </div>
    <div class="article-grid">
%s
    </div>
    <div class="block-more-center"><a href="/actualites.html" class="block-more">Voir toutes nos actualités →</a></div>
  </div>
</section>
""" % (eyebrow, chr(10).join(render_article_card(a) for a in chosen))


def with_page_articles(path, body):
    """Insere le bloc articles juste avant le CTA final de la page."""
    block = render_page_articles(path)
    if not block:
        return body
    marker = '<section class="cta-band">'
    idx = body.rfind(marker)
    if idx == -1:
        return body + block
    return body[:idx] + block + "\n" + body[idx:]


# ============================================================================
# PAGE 9 - mentions-legales.html
# Creee le 01/08/2026. Obligation legale (LCEN art. 6-III) : la page
# n'existait pas et renvoyait un 404. Elle n'est PAS dans NAV_ITEMS (pas
# d'onglet en haut) : on y accede uniquement par le pied de page, present
# sur les 33 pages. D'ou le breadcrumb_override explicite a l'appel.
# ============================================================================
BODY_MENTIONS = """
<section class="page-hero page-hero--compact">
  <div class="container">
    <span class="eyebrow">Informations légales</span>
    <h1>Mentions légales &amp; confidentialité</h1>
    <p>Qui édite ce site, qui l'héberge, ce que nous faisons — et surtout ce que nous ne faisons pas — de vos données.</p>
  </div>
</section>

<style>
/* Page mentions legales — creee le 01/08/2026.
   Mise en page volontairement sobre et autonome : aucun composant du reste du
   site n'est reutilisable pour du texte juridique long. Le CSS vit ici plutot
   que dans site.css, car il ne sert qu'a cette page. */
.legal{background:var(--cream);padding:86px 0 100px;}
.legal .container{max-width:820px;}
.legal h2{font-family:'Fraunces',serif;font-size:clamp(22px,2.6vw,28px);margin:52px 0 16px;color:var(--charcoal);}
.legal h2:first-of-type{margin-top:0;}
.legal h3{font-size:16px;margin:26px 0 10px;color:var(--charcoal);font-weight:600;}
.legal p{color:var(--charcoal-soft);font-size:15.5px;line-height:1.75;margin-bottom:15px;}
.legal ul{margin:0 0 18px;padding-left:0;list-style:none;}
.legal ul li{color:var(--charcoal-soft);font-size:15.5px;line-height:1.75;padding-left:18px;position:relative;margin-bottom:7px;}
.legal ul li::before{content:"—";position:absolute;left:0;color:var(--terracotta);}
.legal a{color:var(--terracotta);border-bottom:1px solid rgba(201,118,75,0.35);}
.legal a:hover{border-bottom-color:var(--terracotta);}
.legal .legal-card{background:var(--cream-2);border:1px solid var(--line);border-radius:14px;padding:28px 30px;margin-bottom:8px;}
.legal .legal-card p:last-child{margin-bottom:0;}
.legal .legal-maj{font-size:13.5px;color:var(--charcoal-soft);margin-top:56px;padding-top:22px;border-top:1px solid var(--line);}
</style>
<section class="legal">
  <div class="container">

    <h2>Éditeur du site</h2>
    <div class="legal-card">
      <p>Le site <strong>www.maisonmikis.fr</strong> est édité par la société <strong>OSLO OPTIQUE</strong>, exerçant sous le nom commercial <strong>Maison Mikis</strong>.</p>
      <ul>
        <li>Société par actions simplifiée (SAS) au capital de 1 000,00 €</li>
        <li>Siège social : 44 avenue d'Ivry, Galerie Oslo — Olympiades, 75013 Paris</li>
        <li>Immatriculée au RCS de Paris sous le numéro 919 964 197</li>
        <li>SIRET : 919 964 197 00017</li>
        <li>Numéro de TVA intracommunautaire : FR06 919 964 197</li>
        <li>Code APE / NAF : 47.78A — commerce de détail d'optique</li>
        <li>Téléphone : <a href="tel:0182280018">01 82 28 00 18</a></li>
        <li>Courriel : <a href="mailto:mikis75013@gmail.com">mikis75013@gmail.com</a></li>
      </ul>
    </div>

    <h2>Directeur de la publication</h2>
    <p>Monsieur Mikhael Saada, en qualité de président de la société OSLO OPTIQUE.</p>

    <h2>Hébergeur</h2>
    <p>Le site est hébergé par <strong>IONOS SARL</strong>, société à responsabilité limitée dont le siège social est situé 7 place de la Gare, 57200 Sarreguemines, France, immatriculée au RCS de Sarreguemines sous le numéro 431 303 775. Site : <a href="https://www.ionos.fr" target="_blank" rel="noopener">www.ionos.fr</a>.</p>

    <h2>Activité réglementée</h2>
    <p>La profession d'opticien-lunetier est une profession de santé réglementée en France, régie par les articles L. 4362-1 et suivants du code de la santé publique. Son exercice est subordonné à la détention d'un diplôme reconnu par l'État et à l'enregistrement auprès de l'autorité compétente. Il en va de même pour la profession d'audioprothésiste, régie par les articles L. 4361-1 et suivants du même code.</p>
    <p>À ce titre, l'établissement est enregistré au fichier national des établissements sanitaires et sociaux (FINESS), enregistrement qui conditionne la prise en charge par l'Assurance Maladie et les organismes complémentaires. Le numéro correspondant figure sur les devis normalisés et les factures remis en boutique.</p>
    <p>Les informations de santé publiées sur ce site, notamment dans les rubriques Espace Santé, Espace Audition et Actualités, ont une vocation strictement informative. Elles ne constituent en aucun cas un diagnostic, une prescription ou un avis médical, et ne remplacent pas une consultation auprès d'un ophtalmologiste, d'un médecin ORL ou de tout autre professionnel de santé compétent.</p>

    <h2>Propriété intellectuelle</h2>
    <p>L'ensemble des éléments composant ce site — structure, textes, articles, photographies, illustrations, logotypes et identité graphique — est la propriété de la société OSLO OPTIQUE ou fait l'objet d'une autorisation d'usage, et est protégé par le code de la propriété intellectuelle.</p>
    <p>Toute reproduction, représentation, adaptation ou exploitation, totale ou partielle, sur quelque support que ce soit, sans l'autorisation écrite préalable de l'éditeur, est interdite. Une courte citation reste possible dans les conditions prévues à l'article L. 122-5 du code de la propriété intellectuelle, à condition d'indiquer clairement la source et de renvoyer vers la page d'origine.</p>
    <p>Les marques et logotypes des fabricants cités sur ce site (notamment dans la rubrique Nos Marques) demeurent la propriété exclusive de leurs titulaires respectifs. Ils sont mentionnés à titre d'information, pour indiquer les collections disponibles en boutique.</p>

    <h2>Liens vers d'autres sites</h2>
    <p>Ce site comporte des liens vers des sites tiers — sites de fabricants, ressources institutionnelles citées en source d'articles, fiche Google de l'établissement. Ces liens sont proposés pour votre information. Nous n'exerçons aucun contrôle sur le contenu de ces sites et ne saurions être tenus responsables de leur contenu, de leurs pratiques ni de leur politique de confidentialité.</p>

    <h2 id="confidentialite">Données personnelles</h2>
    <p>Nous avons fait un choix simple : <strong>ce site ne collecte aucune donnée personnelle</strong>. Il ne comporte ni formulaire, ni espace client, ni inscription à une lettre d'information, ni outil de mesure d'audience. Vous pouvez le consulter intégralement sans nous transmettre quoi que ce soit.</p>

    <h3>Si vous nous contactez</h3>
    <p>Lorsque vous nous écrivez à mikis75013@gmail.com ou que vous nous appelez au 01 82 28 00 18, les informations que vous nous communiquez (nom, coordonnées, objet de votre demande) sont utilisées dans le seul but de vous répondre et, le cas échéant, d'organiser votre venue en boutique. Elles ne sont ni revendues, ni cédées, ni utilisées à des fins de prospection. La base légale de ce traitement est votre demande elle-même, au sens de l'article 6.1.b du RGPD. Ces échanges sont conservés le temps nécessaire au traitement de votre demande, puis au maximum trois ans à compter du dernier contact.</p>

    <h3>Les données de santé</h3>
    <p>Les données relatives à votre vue ou à votre audition (ordonnances, mesures, résultats de tests, dossier d'appareillage) sont recueillies <strong>en boutique uniquement</strong>, dans le cadre de notre activité de professionnels de santé, et jamais par l'intermédiaire de ce site. Elles sont traitées de manière confidentielle, conservées dans les conditions prévues par la réglementation applicable aux professionnels de santé, et ne sont transmises qu'aux organismes strictement nécessaires à la prise en charge de votre équipement — votre caisse d'assurance maladie et votre complémentaire santé, à votre demande.</p>

    <h3>Vos droits</h3>
    <p>Conformément au règlement (UE) 2016/679 (RGPD) et à la loi Informatique et Libertés, vous disposez d'un droit d'accès, de rectification, d'effacement, de limitation, d'opposition et de portabilité sur les données vous concernant. Pour l'exercer, écrivez-nous à <a href="mailto:mikis75013@gmail.com">mikis75013@gmail.com</a> ou passez à la boutique. Nous vous répondrons dans un délai d'un mois. Si notre réponse ne vous satisfait pas, vous pouvez introduire une réclamation auprès de la CNIL — 3 place de Fontenoy, TSA 80715, 75334 Paris Cedex 07, <a href="https://www.cnil.fr" target="_blank" rel="noopener">www.cnil.fr</a>.</p>

    <h2>Cookies et contenus tiers</h2>
    <p>Ce site ne dépose <strong>aucun cookie publicitaire ni aucun cookie de mesure d'audience</strong>. C'est la raison pour laquelle vous ne voyez pas de bandeau de consentement en arrivant : il n'y a rien à consentir.</p>
    <p>Une seule exception mérite d'être signalée. La page <a href="/contact.html">Nous rendre visite</a> affiche un plan Google Maps intégré, afin que vous puissiez situer la boutique dans la Galerie Oslo sans quitter le site. Ce plan est fourni par Google, et son affichage peut conduire Google à déposer des cookies ou à lire des identifiants sur votre terminal, selon des modalités qui lui sont propres et sur lesquelles nous n'avons pas la main. Si vous préférez l'éviter, il vous suffit de ne pas ouvrir cette page, ou de bloquer les cookies tiers dans les réglages de votre navigateur — le reste du site fonctionne à l'identique. La politique de confidentialité de Google est consultable à l'adresse <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">policies.google.com/privacy</a>.</p>
    <p>Notre hébergeur conserve par ailleurs, pour des raisons techniques et de sécurité, des journaux de connexion (adresse IP, date et heure d'appel, pages consultées) pendant la durée légale de conservation. Nous ne les exploitons pas à des fins statistiques ou commerciales.</p>

    <h2>Médiation de la consommation</h2>
    <p>Conformément aux articles L. 611-1 et suivants du code de la consommation, tout consommateur a le droit de recourir gratuitement à un médiateur de la consommation en vue de la résolution amiable d'un litige qui l'oppose à un professionnel, après avoir tenté au préalable de le résoudre directement auprès de celui-ci par une réclamation écrite.</p>
    <p>Avant toute démarche de médiation, nous vous invitons donc à nous adresser votre réclamation par courriel à <a href="mailto:mikis75013@gmail.com">mikis75013@gmail.com</a> ou par courrier à l'adresse de la boutique : nous nous efforçons de traiter chaque situation directement, et c'est presque toujours la voie la plus rapide.</p>
    <p>Si aucune solution n'a pu être trouvée dans un délai d'un an à compter de votre réclamation écrite, vous pouvez saisir gratuitement le médiateur dont relève l'établissement, en sa qualité d'adhérent de la Centrale des Opticiens (CDO) :</p>
    <div class="legal-card">
      <ul>
        <li><strong>Médiation du commerce coopératif et associé (MCCA)</strong></li>
        <li>77 rue de Lourmel, 75015 Paris</li>
        <li>Saisine en ligne : <a href="https://www.mcca-mediation.fr" target="_blank" rel="noopener">www.mcca-mediation.fr</a></li>
        <li>Courriel : <a href="mailto:mediateur@mcca-mediation.fr">mediateur@mcca-mediation.fr</a></li>
      </ul>
    </div>
    <p>Le recours au médiateur est gratuit pour le consommateur et n'est possible qu'après une réclamation écrite préalable restée sans réponse satisfaisante. Il ne vous prive à aucun moment de la faculté de saisir la juridiction compétente.</p>

    <h2>Droit applicable</h2>
    <p>Le présent site et les présentes mentions sont soumis au droit français. En cas de litige et à défaut de résolution amiable, les tribunaux français sont seuls compétents.</p>

    <p class="legal-maj">Dernière mise à jour : 1er août 2026. Ces mentions peuvent être modifiées à tout moment pour tenir compte d'une évolution du site ou de la réglementation.</p>

  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Une question sur ce site ou sur vos données ?</h2>
    <p>Écrivez-nous, ou passez simplement nous voir Galerie Oslo — 44 avenue d'Ivry.</p>
    <a href="/contact.html" class="btn btn-primary">Nous contacter</a>
  </div>
</section>
"""


def render_accueil_body():
    """Page d'accueil : injecte l'apercu des 3 actualites les plus recentes.

    Les cartes reutilisent render_article_card() donc exactement le meme markup
    (et le meme CSS) que la page Actualites. Le script "bulle" qui intercepte le
    clic n'existe que sur actualites.html : ici, les cartes restent de simples
    liens vers la page de l'article, ce qui est le comportement voulu.
    """
    latest = sorted(ARTICLES, key=lambda a: a["date_iso"], reverse=True)[:3]
    cards = "\n".join(render_article_card(a) for a in latest)
    teaser = f"""<section class="services alt">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Actualités</span>
      <h2>Nos derniers articles</h2>
      <p>Santé visuelle, santé auditive, tendances et innovations : nous publions régulièrement de quoi y voir plus clair.</p>
    </div>
    <div class="article-grid">
{cards}
    </div>
    <div style="text-align:center;margin-top:44px;">
      <a href="/actualites.html" class="btn btn-outline">Voir toutes les actualités</a>
    </div>
  </div>
</section>"""
    assert BODY_BOUTIQUE.count("<!--ACTUALITES_TEASER-->") == 1
    return BODY_BOUTIQUE.replace("<!--ACTUALITES_TEASER-->", teaser)


def render_actualites_index():
    filter_pills = ['      <button class="filter-pill active" data-filter="all">Tous</button>']
    for key, _ in CATEGORY_ORDER:
        filter_pills.append(f'      <button class="filter-pill" data-filter="{key}">{ARTICLE_CATEGORIES[key]["label"]}</button>')
    cards = "\n".join(render_article_card(a) for a in ARTICLES)
    filter_script = """
<script>
  const pills = document.querySelectorAll('.filter-pill');
  const cards = document.querySelectorAll('.article-card');
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const filter = pill.dataset.filter;
      cards.forEach(card => {
        card.style.display = (filter === 'all' || card.dataset.category === filter) ? '' : 'none';
      });
    });
  });
</script>"""
    return f"""
<section class="page-hero">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / Actualités</div>
    <span class="eyebrow">Le journal Maison Mikis</span>
    <h1>Actualités</h1>
    <p>Santé visuelle et auditive, mode, technologies, remboursements, vie de la boutique : nos conseils et décryptages, mis à jour régulièrement.</p>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="article-filter-bar">
{chr(10).join(filter_pills)}
    </div>
    <div class="article-grid">
{cards}
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Une question sur votre vue ou votre audition ?</h2>
    <p>Nos conseils en ligne ne remplacent pas un vrai échange avec l'équipe : venez nous en parler chez votre <a href="/opticien-paris-13.html">opticien à Paris 13e</a>, Galerie Oslo – Olympiades.</p>
    <a href="/contact.html" class="btn btn-primary">Prendre rendez-vous</a>
  </div>
</section>
{filter_script}
"""


def render_article_page(article):
    related = related_articles(article)
    cat = ARTICLE_CATEGORIES[article["category"]]
    breadcrumb = [
        ("La Boutique", f"{BASE_URL}/"),
        ("Actualités", f"{BASE_URL}/actualites.html"),
        (article["title"], f"{BASE_URL}/{article_url(article)}"),
    ]
    body = f"""
<section class="page-hero">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / <a href="/actualites.html">Actualités</a> / {article["title"]}</div>
    <span class="eyebrow">{cat["label"]}</span>
    <h1>{article["title"]}</h1>
    <div class="article-meta-row">
      <span class="article-tag" style="--accent:{cat["accent"]};--accent-bg:{cat["accent_bg"]};">{cat["label"]}</span>
      <span class="article-date">{article["date_display"]}</span>
    </div>
  </div>
</section>

<section class="article-prose story-block">
  <div class="container-narrow">
    <div class="arch-frame reveal" style="margin-bottom:40px;aspect-ratio:16/9;border-radius:24px;">
      <img src="{article["image"]}" alt="{article["image_alt"]}">
    </div>
    {render_answer_lead(article)}
    {apply_inline_links(article["body"], INLINE_LINKS.get(article["slug"], []), article["slug"])}
    {render_faq(article)}
    {render_go_further(article)}
    <div class="article-source-note">{source_note(article)}</div>
  </div>
</section>

<section class="related-articles story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">À lire aussi</span>
      <h2>D'autres articles qui pourraient vous intéresser</h2>
    </div>
    <div class="article-grid">
{chr(10).join(render_article_card(a) for a in related)}
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Envie d'en discuter avec nous ?</h2>
    <p>Maison Mikis est votre <a href="/opticien-paris-13.html">opticien et audioprothésiste à Paris 13e</a>, Galerie Oslo – Olympiades, 44 avenue d'Ivry. Prenez rendez-vous pour un conseil personnalisé.</p>
    <a href="/contact.html" class="btn btn-primary">Prendre rendez-vous</a>
  </div>
</section>
"""
    render_page(
        "actualites",
        article["meta_title"],
        article["meta_description"],
        article_url(article),
        body,
        hero_img=article["image"],
        extra_jsonld=article_jsonld(article),
        breadcrumb_override=breadcrumb,
    )


def sync_sitemap():
    """Ajoute au sitemap les articles qui n'y figurent pas encore.

    Volontairement additif : les <lastmod> deja en place ne sont jamais
    reecrits, pour ne pas signaler aux moteurs une modification qui n'a pas eu
    lieu. Sans effet si tous les articles sont deja references.
    """
    path = os.path.join(OUT_DIR, "sitemap.xml")
    if not os.path.exists(path):
        print("sitemap.xml absent : etape ignoree.")
        return 0
    with open(path, encoding="utf-8") as f:
        content = f.read()

    blocks = []
    for a in ARTICLES:
        loc = f"{BASE_URL}/{article_url(a)}"
        if f"<loc>{loc}</loc>" in content:
            continue
        blocks.append(
            "  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{a.get('updated_iso') or a['date_iso']}</lastmod>\n"
            "    <changefreq>monthly</changefreq>\n"
            "    <priority>0.6</priority>\n"
            "  </url>\n"
        )

    if not blocks:
        print("sitemap.xml : deja a jour.")
        return 0

    closing = "</urlset>"
    assert content.count(closing) == 1, "sitemap.xml : balise </urlset> introuvable ou dupliquee"
    content = content.replace(closing, "".join(blocks) + closing)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"sitemap.xml : {len(blocks)} URL ajoutee(s).")
    return len(blocks)


# ============================================================================
# PAGE "OPTICIEN A PARIS 13E" (creee le 06/08/2026)
# ----------------------------------------------------------------------------
# Raison d'etre : l'audit SERP du 06/08/2026 a montre que la fiche Google
# ressort bien sur "opticien paris 13 olympiades", mais que maisonmikis.fr
# n'apparait NULLE PART dans les resultats web de cette requete : aucune page
# du site ne ciblait la recherche. Cette page comble ce trou.
# Contrainte : page de contenu reel (services, quartiers, acces, FAQ), pas une
# page satellite. Aucune classe CSS nouvelle : tout reutilise SHARED_CSS.
# La page est referencee dans le FOOTER (donc depuis les 35 pages) et dans le
# cta-band commun aux articles. Elle doit etre ajoutee A LA MAIN au sitemap :
# sync_sitemap() ne traite que les articles.
# ============================================================================
BODY_OPTICIEN_PARIS_13 = """
<section class="page-hero page-hero--compact">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / Opticien à Paris 13e</div>
    <span class="eyebrow">Galerie Oslo — Olympiades · 44 avenue d'Ivry</span>
    <h1>Opticien à Paris 13e</h1>
    <p>Maison Mikis est un opticien et audioprothésiste indépendant installé dans le 13e arrondissement de Paris, au pied de la dalle des Olympiades. Lunettes de vue, solaires, lentilles de contact et solutions auditives, avec le temps qu'il faut pour bien faire.</p>
    <div class="hero-actions">
      <a href="/contact.html" class="btn btn-primary">Prendre rendez-vous</a>
      <a href="tel:0182280018" class="btn btn-ghost">01 82 28 00 18</a>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container-narrow">
    <div class="answer-lead">
      <p>Maison Mikis est un opticien indépendant du 13e arrondissement de Paris, situé 44 avenue d'Ivry dans la Galerie Oslo, à la sortie du métro Olympiades. La boutique est ouverte du mardi au samedi de 10h à 19h30 et réunit sous le même toit l'optique, les lentilles et un espace audition avec audioprothésiste.</p>
    </div>
    <p>Le 13e arrondissement ne manque pas d'opticiens : entre les enseignes de la place d'Italie, celles du centre commercial Italie Deux et les magasins des grandes avenues, le choix est large. Ce qui distingue une maison de quartier d'une chaîne, ce n'est ni le catalogue ni le prix affiché en vitrine, c'est le temps accordé à chaque personne et le fait de retrouver le même interlocuteur d'une visite à l'autre.</p>
    <p>Nous avons ouvert Maison Mikis avec cette idée simple : un opticien de quartier doit pouvoir vous recevoir sans rendez-vous pour resserrer une charnière, et vous consacrer une heure quand il s'agit de choisir un équipement que vous porterez tous les jours pendant deux ans. Les deux comptent autant l'un que l'autre.</p>
  </div>
</section>

<section class="dark-section">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Nos métiers</span>
      <h2>Ce que nous faisons en boutique</h2>
    </div>
    <div class="card-grid-3">
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><circle cx="7" cy="13" r="4"/><circle cx="17" cy="13" r="4"/><path d="M11 13h2"/></svg></div>
        <h3>Optique</h3>
        <p>Lunettes de vue et solaires, montures optiques et solaires à votre correction, verres unifocaux et progressifs, traitements antireflet, photochromiques et polarisants. Examen de vue en salle dédiée, adaptation de la correction sur ordonnance en cours de validité, ajustage et réparation, y compris sur des paires achetées ailleurs. Prise en charge Sécurité sociale, mutuelles et 100 % Santé.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg></div>
        <h3>Lentilles de contact</h3>
        <p>Lentilles journalières, bimensuelles et mensuelles, souples et rigides, toriques pour l'astigmatisme et multifocales pour la presbytie. Apprentissage de la pose et du retrait pour les premières fois, essais avant commande, renouvellement et produits d'entretien. Nous suivons l'ordonnance de votre ophtalmologiste et restons disponibles entre deux rendez-vous si quelque chose vous gêne.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><path d="M6 18a6 6 0 1 1 12-6c0 4-3 4-3 7a2 2 0 0 1-4 0"/><circle cx="12" cy="12" r="1.5"/></svg></div>
        <h3>Audition</h3>
        <p>Notre espace audition accueille un audioprothésiste dans une cabine dédiée : bilan auditif gratuit et sans engagement, essai d'appareils de trente jours minimum, réglages, entretien et suivi inclus sur toute la durée de vie de l'appareil. Là aussi, le 100 % Santé s'applique, avec une classe d'appareils intégralement prise en charge.</p>
      </div>
    </div>
    <div class="block-more-center"><a href="/espace-audition.html" class="block-more">Découvrir l'Espace Audition →</a></div>
  </div>
</section>

<section class="split story-block">
  <div class="container">
    <div class="split-grid">
      <div class="split-text reveal">
        <span class="eyebrow">Notre quartier</span>
        <h2>Du Triangle de Choisy à la Bibliothèque</h2>
        <p>La boutique se trouve au cœur du Triangle de Choisy, entre l'avenue d'Ivry, l'avenue de Choisy et le boulevard Masséna. C'est un quartier dense, très vivant en journée, où l'on croise autant de familles installées là depuis trente ans que d'étudiants et de jeunes actifs arrivés récemment.</p>
        <p>Nous recevons naturellement les habitants des Olympiades et des tours voisines, mais aussi ceux qui descendent de Tolbiac et de la place d'Italie, ceux du quartier Jeanne d'Arc, et de plus en plus de personnes qui travaillent avenue de France ou près de la Bibliothèque François-Mitterrand et passent en fin de journée.</p>
        <p>Beaucoup viennent aussi de la Porte d'Ivry et d'Ivry-sur-Seine, que quelques centaines de mètres séparent de la boutique. Le 13e est un arrondissement qui se traverse à pied plus qu'on ne le croit, et c'est très bien ainsi.</p>
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Y venir</span>
        <h2>Comment nous rejoindre</h2>
        <p>Le plus simple reste la ligne 14 : la station Olympiades est terminus, et sa sortie débouche avenue d'Ivry à quelques dizaines de mètres de la Galerie Oslo. Depuis Saint-Lazare, Châtelet ou Gare de Lyon, vous êtes chez nous sans changement.</p>
        <p>Par la ligne 7, les stations Tolbiac et Porte d'Ivry sont à une dizaine de minutes de marche, et Maison Blanche à un quart d'heure. Le tramway T3a s'arrête Porte d'Ivry et Porte de Choisy, à quelques minutes également.</p>
        <p>En voiture, le stationnement de surface est payant et souvent saturé en fin de journée ; les parkings souterrains autour de la dalle sont la solution la plus confortable, surtout le samedi. La galerie et la boutique sont de plain-pied, accessibles en fauteuil roulant et avec une poussette.</p>
        <ul class="check-list-grid">
          <li><span class="check">✓</span> Métro 14 — Olympiades, à 100 m</li>
          <li><span class="check">✓</span> Métro 7 — Tolbiac et Porte d'Ivry</li>
          <li><span class="check">✓</span> Tramway T3a — Porte d'Ivry</li>
          <li><span class="check">✓</span> Bus 27, 62, 83 et 183</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Sans rendez-vous</span>
        <h2>Passer nous voir</h2>
        <p>Vous n'avez pas besoin de prévenir pour essayer des montures, faire ajuster une paire, remplacer des plaquettes, commander des lentilles ou poser une question. Ces gestes-là ne se planifient pas et nous les faisons volontiers, même si vos lunettes viennent d'ailleurs.</p>
        <p>Le rendez-vous devient utile dès qu'il faut du temps : une vingtaine de minutes pour un <a href="/espace-sante.html">examen de vue</a>, une quarantaine pour un <a href="/espace-audition.html">bilan auditif</a>. Un appel au <a href="tel:0182280018">01 82 28 00 18</a> suffit, souvent pour un créneau dans la même semaine.</p>
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Nos horaires</span>
        <h2>Quand nous sommes ouverts</h2>
        <p>Du mardi au samedi, sans interruption entre midi et deux : vous pouvez passer sur votre pause déjeuner sans crainte de trouver porte close.</p>
        <table class="hours-table">
          <tr class="closed"><th scope="row">Lundi</th><td>Fermé</td></tr>
          <tr><th scope="row">Mardi</th><td>10h00 – 19h30</td></tr>
          <tr><th scope="row">Mercredi</th><td>10h00 – 19h30</td></tr>
          <tr><th scope="row">Jeudi</th><td>10h00 – 19h30</td></tr>
          <tr><th scope="row">Vendredi</th><td>10h00 – 19h30</td></tr>
          <tr><th scope="row">Samedi</th><td>10h00 – 19h30</td></tr>
          <tr class="closed"><th scope="row">Dimanche</th><td>Fermé</td></tr>
        </table>
        <p>Le samedi après-midi est de loin le moment le plus fréquenté. Pour prendre votre temps sur un choix de monture, préférez le milieu de semaine ou la matinée.</p>
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container-narrow">
    <div class="section-head center">
      <span class="eyebrow">Questions fréquentes</span>
      <h2>Ce qu'on nous demande le plus souvent</h2>
    </div>
    <div class="faq-list">
      <details class="faq-item reveal">
        <summary>Où se trouve exactement la boutique dans le 13e ?<span class="plus">+</span></summary>
        <p>Au 44 avenue d'Ivry, 75013 Paris, à l'intérieur de la Galerie Oslo, au pied de la dalle des Olympiades. La sortie du métro ligne 14 « Olympiades » se trouve à une centaine de mètres. Le point Plus code Google est R9F8+9C Paris si vous préférez viser directement l'entrée.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Faut-il une ordonnance pour venir chez l'opticien ?<span class="plus">+</span></summary>
        <p>Pour des lunettes correctrices, oui : une ordonnance d'ophtalmologiste est nécessaire. En revanche, si la vôtre est encore valable, nous pouvons y adapter votre correction après un examen de vue en boutique, sans repasser par le médecin. Pour des solaires non correctrices, un ajustage ou une réparation, aucune ordonnance n'est demandée.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Proposez-vous le 100 % Santé ?<span class="plus">+</span></summary>
        <p>Oui, en optique comme en audition. Le panier 100 % Santé donne accès à des équipements intégralement remboursés par la Sécurité sociale et votre complémentaire, sans reste à charge. Nous vous présentons systématiquement cette offre à côté des autres, sans pression et sans conditions cachées.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Y a-t-il un audioprothésiste sur place ?<span class="plus">+</span></summary>
        <p>Oui. L'espace audition dispose d'une cabine dédiée et d'un audioprothésiste diplômé. Le bilan auditif est gratuit et sans engagement, et tout appareillage passe par un essai de trente jours minimum avant décision. C'est encore rare de trouver les deux métiers réunis dans le même magasin à Paris 13e.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Vous réparez les lunettes achetées ailleurs ?<span class="plus">+</span></summary>
        <p>Oui, et sans que cela vous engage à quoi que ce soit. Plaquettes, vis, charnières, réglage d'un galbe ou d'une branche déformée : passez quand vous voulez pendant les horaires d'ouverture, c'est l'affaire de quelques minutes dans la grande majorité des cas.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Quels sont les quartiers du 13e que vous desservez ?<span class="plus">+</span></summary>
        <p>Nos clients viennent principalement des Olympiades, du Triangle de Choisy, de Tolbiac, de la place d'Italie et d'Italie Deux, du quartier Jeanne d'Arc, de l'avenue de France et de la Bibliothèque, de la Porte d'Ivry et de la Porte de Choisy. Ivry-sur-Seine et Le Kremlin-Bicêtre sont également à quelques minutes.</p>
      </details>
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Passez nous voir</h2>
    <p>Maison Mikis — Galerie Oslo, 44 avenue d'Ivry, 75013 Paris. Du mardi au samedi, 10h – 19h30. Métro 14, Olympiades.</p>
    <a href="/contact.html" class="btn btn-primary">Nous contacter</a>
  </div>
</section>
"""


if __name__ == "__main__":
    css_path = os.path.join(OUT_DIR, "site.css")
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(SHARED_CSS)
    print(f"wrote site.css ({len(SHARED_CSS)} bytes, v={CSS_VERSION})")

    render_page(
        "accueil",
        "Opticien et audioprothésiste à Paris 13e | Maison Mikis",
        "Opticien et audioprothésiste à Paris 13e, Maison Mikis vous accueille Galerie Oslo – Olympiades, 44 avenue d'Ivry : lunettes de vue, solaires, lentilles et audition.",
        "index.html",
        render_accueil_body(),
        hero_img="/images/accueil/hero-boutique.jpg",
    )
    render_page(
        "conseils",
        "Nos Conseils — Choisir monture et verres | Maison Mikis",
        "Choisir sa monture, ses verres et leurs traitements selon sa correction, lunettes ou lentilles, entretien et style : les conseils de Maison Mikis, Paris 13e.",
        "nos-conseils.html",
        BODY_CONSEILS,
        hero_img="/images/conseils/hero-conseils.jpg",
        # Photo remontee sur cette page : les lunettes etaient coupees en bas.
        hero_pos="50%",
    )
    render_page(
        "sante",
        "Espace Santé — Examen de vue à Paris 13e | Maison Mikis",
        "L'Espace Santé de Maison Mikis à Paris 13e : examen de vue, défauts visuels, myopie de l'enfant, maladies de l'œil et conseils pour prendre soin de votre vue.",
        "espace-sante.html",
        BODY_SANTE,
        # Version "elargie" de la photo (31/07/2026) : la photo d'origine est
        # recomposee sur un canevas 4.2:1 (extension floutee issue de la meme
        # image) pour donner du recul sans changer la hauteur du bandeau.
        hero_img="/images/sante/hero-sante-large.jpg",
        # 01/08/2026 — le balisage FAQPage a ete retire : Google a annonce le
        # 08/05/2026 la fin des resultats enrichis FAQ et retire la doc le
        # 15/06/2026. La FAQ reste VISIBLE dans la page (accordeons <details>),
        # seul le JSON-LD disparait. Ne pas le reintroduire.
    )
    render_page(
        "marques",
        "Nos Marques — Ray-Ban, Prada, Dior… | Maison Mikis",
        "Ray-Ban, Dior, Prada, Loewe, Celine, Miu Miu, LOOL, CHIMI : les 19 maisons sélectionnées par Maison Mikis, opticien à Paris 13e, en quatre familles.",
        "marques.html",
        BODY_MARQUES,
    )
    render_page(
        "audition",
        "Espace Audition — Bilan & Appareillage | Maison Mikis",
        "Bilan auditif gratuit, essai de 30 jours minimum et suivi inclus : l'Espace Audition de Maison Mikis, opticien-audioprothésiste à Paris 13e.",
        "espace-audition.html",
        BODY_AUDITION,
        # Voir commentaire equivalent sur l'Espace Sante (31/07/2026).
        hero_img="/images/audition/hero-audition-large.jpg",
        # Idem espace-sante : balisage FAQPage deprecie, retire le 01/08/2026.
    )
    render_page(
        "accueil",
        "Notre histoire | Maison Mikis, opticien à Paris 13e",
        "L'histoire de Maison Mikis : deux parcours qui se rejoignent en 2023 au 44 avenue d'Ivry, au cœur du Triangle de Choisy, dans le 13e arrondissement.",
        "notre-histoire.html",
        BODY_HISTOIRE,
        hero_img="/images/accueil/hero-boutique.jpg",
        hero_pos="42%",
        breadcrumb_override=[
            ("La Boutique", f"{BASE_URL}/"),
            ("Notre histoire", f"{BASE_URL}/notre-histoire.html"),
        ],
    )

    render_page(
        "accueil",
        "Opticien à Paris 13e — Olympiades, 44 av. d'Ivry | Maison Mikis",
        "Opticien et audioprothésiste à Paris 13e : Maison Mikis vous reçoit Galerie Oslo, 44 avenue d'Ivry, métro Olympiades. Lunettes, lentilles, audition, 100 % Santé.",
        "opticien-paris-13.html",
        BODY_OPTICIEN_PARIS_13,
        hero_img="/images/accueil/hero-boutique.jpg",
        hero_pos="42%",
        breadcrumb_override=[
            ("La Boutique", f"{BASE_URL}/"),
            ("Opticien à Paris 13e", f"{BASE_URL}/opticien-paris-13.html"),
        ],
    )

    render_page(
        "contact",
        "Contact — Opticien à Paris 13e, Olympiades | Maison Mikis",
        "Maison Mikis, 44 Avenue d'Ivry, Galerie Oslo – Olympiades, 75013 Paris. Ouvert du mardi au samedi, 10h-19h30. Métro ligne 14 — Olympiades.",
        "contact.html",
        BODY_CONTACT,
        # 31/07/2026 — remplace le dernier placeholder picsum du site.
        # Le client a demandé exactement la même photo et les mêmes réglages
        # que l'onglet "La Boutique" (index.html) : même fichier, pas de
        # hero_pos (donc le 15% par défaut), pas de hero_veil (voile standard).
        hero_img="/images/accueil/hero-boutique.jpg",
    )
    render_page(
        "accueil",
        "Mentions légales & confidentialité | Maison Mikis",
        "Mentions légales de maisonmikis.fr : éditeur SAS Oslo Optique, hébergeur, propriété intellectuelle, données personnelles et cookies.",
        "mentions-legales.html",
        BODY_MENTIONS,
        # Sans photo de bandeau, le titre du hero (texte creme) serait invisible
        # sur fond clair : on reprend la meme photo que l'accueil et le contact.
        hero_img="/images/accueil/hero-boutique.jpg",
        breadcrumb_override=[
            ("La Boutique", f"{BASE_URL}/"),
            ("Mentions légales", f"{BASE_URL}/mentions-legales.html"),
        ],
    )

    render_page(
        "actualites",
        "Actualités vue et audition — Paris 13e | Maison Mikis",
        "Le journal Maison Mikis : santé visuelle et auditive, mode lunettes, technologies verres et lentilles, remboursements et vie de la boutique, à Paris 13e.",
        "actualites.html",
        render_actualites_index(),
        # Photo fournie par le client le 31/07/2026 (lettres "NEWS" sur fond
        # corail). Cadrage centre : les lettres sont au milieu de la photo.
        hero_img="/images/actualites/hero-actualites-news.jpg",
        hero_pos="50%",
        # Voile allege sur cette page (choix client) : la photo est tres coloree
        # et le voile standard (0.62 -> 0.78) l'eteignait. Dosage retenu apres
        # mesure de contraste : 4.86:1 sur le paragraphe, 6.62:1 sur le titre,
        # soit au-dessus du seuil WCAG AA de 4.5:1.
        hero_veil="linear-gradient(180deg, rgba(43,38,33,0.44), rgba(43,38,33,0.60))",
    )
    for _article in ARTICLES:
        render_article_page(_article)
    print(f"wrote actualites.html + {len(ARTICLES)} article pages")
    sync_sitemap()
    print("Done.")
