"""Genera el portafolio a partir de src/template.html.

- index.html  -> sitio estático prerenderizado para Vercel (con SEO: metadatos, Open Graph y JSON-LD)
- img/avif/   -> variantes AVIF responsive de cada imagen
- Dossier-JoseLuis-Cuenca.pdf -> mismo contenido en modo impresión
- robots.txt, sitemap.xml, site.webmanifest, vercel.json
- --artifact RUTA -> versión sin <html>/<head> para publicar como Artifact de Claude

Uso:  python src/build.py [--artifact RUTA] [--look CARPETA]
"""
import datetime, json, sys
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PDF = "Dossier-JoseLuis-Cuenca.pdf"
WIDTHS = (480, 960, 1400)

cfg = json.loads((SRC / "config.json").read_text(encoding="utf-8"))
URL = cfg["portfolio_url"]
icons = json.loads((SRC / "icons.json").read_text(encoding="utf-8"))
tpl = (SRC / "template.html").read_text(encoding="utf-8")
import re as _re
_used = set(_re.findall(r'icon:"([\w]+)"', tpl)) | {"github"}
icons = {k: v for k, v in icons.items() if k in _used}

# ── Variantes AVIF ──
avif_dir = ROOT / "img" / "avif"
avif_dir.mkdir(parents=True, exist_ok=True)
avif_widths = {}
for img in sorted((ROOT / "img").glob("*.jpg")):
    name = img.stem
    with Image.open(img) as im:
        im = im.convert("RGB")
        ws = [w for w in WIDTHS if w < im.width] + [im.width]
        if name == "foto":
            ws = [400]
        avif_widths[name] = ws
        for w in ws:
            out = avif_dir / f"{name}-{w}.avif"
            if out.exists() and out.stat().st_mtime > img.stat().st_mtime:
                continue
            (im if w >= im.width else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)).save(out, quality=58, speed=6)
valid = {f"{n}-{w}.avif" for n, ws in avif_widths.items() for w in ws}
for old in avif_dir.glob("*.avif"):
    if old.name not in valid:
        old.unlink()

fl_links = []
if cfg.get("freelance_url"):
    fl_links.append({"label": "Ver sitio", "href": cfg["freelance_url"], "primary": True})
fl_links.append({"label": "Repositorio", "href": "https://github.com/JCuenca17/landing-page", "primary": not cfg.get("freelance_url")})

body = (tpl.replace("__ICONS__", json.dumps(icons, separators=(",", ":")))
           .replace("__GITHUB__", icons["github"]["d"])
           .replace("__AVIF_WIDTHS__", json.dumps(avif_widths, separators=(",", ":")))
           .replace("[__FREELANCE_LINKS__]", json.dumps(fl_links, ensure_ascii=False)))

args = sys.argv[1:]
if "--artifact" in args:
    dst = Path(args[args.index("--artifact") + 1]); dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(body, encoding="utf-8"); print("artifact:", dst)
look = Path(args[args.index("--look") + 1]) if "--look" in args else None

TITLE = "José Luis Cuenca | Desarrollador de Software en Arequipa · Portafolio"
DESC = ("Portafolio de José Luis Cuenca Gutiérrez, estudiante de Ingeniería de Sistemas (UNSA) y desarrollador de software en Arequipa, Perú: "
        "apps web y móviles, juegos con Unity y Phaser, extensiones de Chrome y automatización.")

def head_html(projects, skills):
    ld_projects = []
    for p in projects:
        item = {"@type": "CreativeWork", "name": p["title"], "description": p["summary"], "about": p["kicker"],
                "image": URL + p["images"][0]["src"], "dateCreated": p["year"], "creator": {"@id": URL + "#persona"},
                "keywords": ", ".join(p["tec"])}
        if p["id"] == "market":
            item.update({"@type": "MobileApplication", "operatingSystem": "Android", "applicationCategory": "ShoppingApplication",
                         "installUrl": "https://play.google.com/store/apps/details?id=com.unsa.market",
                         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "PEN"}})
        elif p["id"] in ("yachay", "boehm"):
            item.update({"@type": "VideoGame", "gamePlatform": "Navegador web", "genre": "Educativo"})
        elif p["id"] == "pro":
            item.update({"@type": "SoftwareApplication", "applicationCategory": "BrowserApplication", "operatingSystem": "Google Chrome"})
        elif p["type"] == "web":
            item.update({"@type": "WebApplication", "applicationCategory": "BusinessApplication", "operatingSystem": "Web"})
        links = [l["href"] for l in p["links"]]
        if links:
            item["url"] = links[0]
            if len(links) > 1: item["sameAs"] = links[1:]
        ld_projects.append(item)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Person", "@id": URL + "#persona", "name": "José Luis Cuenca Gutiérrez", "givenName": "José Luis", "familyName": "Cuenca Gutiérrez",
         "url": URL, "image": URL + "img/foto.jpg", "email": "mailto:jlcg17042001@gmail.com",
         "jobTitle": "Desarrollador de Software", "description": DESC,
         "address": {"@type": "PostalAddress", "addressLocality": "Arequipa", "addressCountry": "PE"},
         "alumniOf": [{"@type": "CollegeOrUniversity", "name": "Universidad Nacional de San Agustín de Arequipa"},
                      {"@type": "EducationalOrganization", "name": "Oracle Next Education"}],
         "knowsAbout": skills,
         "sameAs": ["https://github.com/JCuenca17", "https://www.linkedin.com/in/josecuencag/", cfg.get("freelance_url", ""), "https://abduzcan17.itch.io/"]},
        {"@type": "ProfilePage", "@id": URL + "#pagina", "url": URL, "name": TITLE, "inLanguage": "es-PE", "mainEntity": {"@id": URL + "#persona"},
         "dateModified": datetime.date.today().isoformat(), "primaryImageOfPage": URL + "og.jpg"},
        {"@type": "ItemList", "name": "Proyectos", "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": it} for i, it in enumerate(ld_projects)]},
    ]}
    ld["@graph"][0]["sameAs"] = [x for x in ld["@graph"][0]["sameAs"] if x]
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="author" content="José Luis Cuenca Gutiérrez">
<meta name="theme-color" content="#F5F9F9">
<link rel="canonical" href="{URL}">
<link rel="icon" href="favicon.ico" sizes="48x48">
<link rel="icon" href="icons/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="manifest" href="site.webmanifest">
<meta property="og:type" content="profile">
<meta property="og:locale" content="es_PE">
<meta property="og:site_name" content="Portafolio · José Luis Cuenca">
<meta property="og:title" content="José Luis Cuenca · Desarrollador de Software">
<meta property="og:description" content="Proyectos web, móviles, juegos y automatización. Estudiante de Ingeniería de Sistemas en la UNSA, Arequipa.">
<meta property="og:url" content="{URL}">
<meta property="og:image" content="{URL}og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="José Luis Cuenca, desarrollador de software. Portafolio.">
<meta property="profile:first_name" content="José Luis">
<meta property="profile:last_name" content="Cuenca Gutiérrez">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="José Luis Cuenca · Desarrollador de Software">
<meta name="twitter:description" content="Proyectos web, móviles, juegos y automatización.">
<meta name="twitter:image" content="{URL}og.jpg">
<link rel="preload" as="image" type="image/avif" href="img/avif/foto-400.avif" fetchpriority="high">
<link rel="preload" as="font" type="font/woff2" href="fonts/p-bricolage-grotesque-normal-500_800.woff2" crossorigin>
<link rel="preload" as="font" type="font/woff2" href="fonts/p-figtree-normal-400_700.woff2" crossorigin>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
"""

head, rest = body.split("</style>", 1)
head = head.replace("<title>Portafolio José Luis Cuenca</title>", "")
head = "\n".join(l for l in head.splitlines() if not l.startswith('<meta name="description"'))

def standalone(extra_head):
    return f"<!doctype html>\n<html lang=\"es-PE\">\n<head>\n{extra_head}{head}</style>\n</head>\n<body>\n{rest}\n</body>\n</html>\n"

index = ROOT / "index.html"
index.write_text(standalone(""), encoding="utf-8")

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 860})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(index.as_uri(), wait_until="networkidle"); pg.wait_for_timeout(800)
    projects = pg.evaluate("PROJECTS")
    skills = pg.evaluate("SKILL_ORDER.map(k => TECH[k].name).concat(ALSO.map(a => a.name))")
    # Prerender: el HTML final ya trae habilidades, filtros y tarjetas
    pg.evaluate("document.querySelectorAll('.nav-links a.on').forEach(a => a.classList.remove('on')); document.getElementById('nav').classList.remove('scrolled')")
    grid = pg.evaluate("document.getElementById('grid').outerHTML")
    skl = pg.evaluate("document.getElementById('skills').outerHTML")
    flt = pg.evaluate("document.getElementById('filters').outerHTML")
    als = pg.evaluate("document.getElementById('also').outerHTML")
    b.close()

pre = rest
for sel_open, html in [('<div class="grid" id="grid"></div>', grid), ('<div class="skills" id="skills"></div>', skl),
                       ('<div class="filters" id="filters" role="toolbar" aria-label="Filtrar proyectos"></div>', flt),
                       ('<div class="also" id="also"><span class="also-t">También con formación en</span></div>', als)]:
    assert sel_open in pre, sel_open
    pre = pre.replace(sel_open, html, 1)
rest = pre
index.write_text(standalone(head_html(projects, skills)), encoding="utf-8")
print("index.html prerenderizado:", index.stat().st_size // 1024, "KB")

# ── Archivos de rastreo y despliegue ──
today = datetime.date.today().isoformat()
(ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {URL}sitemap.xml\n", encoding="utf-8")
(ROOT / "sitemap.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>{URL}</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>1.0</priority>
    <image:image><image:loc>{URL}img/foto.jpg</image:loc></image:image>
{chr(10).join(f'    <image:image><image:loc>{URL}{p["images"][0]["src"]}</image:loc></image:image>' for p in projects)}
  </url>
  <url><loc>{URL}{PDF}</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>
</urlset>
""", encoding="utf-8")
(ROOT / "site.webmanifest").write_text(json.dumps({
    "name": "Portafolio · José Luis Cuenca", "short_name": "JL Portafolio", "lang": "es-PE", "start_url": "/",
    "display": "standalone", "background_color": "#F5F9F9", "theme_color": "#F5F9F9",
    "icons": [{"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
              {"src": "icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]},
    ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "vercel.json").write_text(json.dumps({"headers": [
    {"source": "/fonts/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]},
    {"source": "/(img|icons)/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=604800, stale-while-revalidate=86400"}]},
    {"source": "/(.*)", "headers": [
        {"key": "X-Content-Type-Options", "value": "nosniff"},
        {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"},
        {"key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()"}]}]}, indent=2), encoding="utf-8")

# ── PDF y revisión ──
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 860})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(index.as_uri(), wait_until="networkidle"); pg.wait_for_timeout(1000)
    if look:
        look.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(look / "top.png"))
        pg.evaluate("document.querySelector('#proyectos').scrollIntoView()"); pg.wait_for_timeout(1200)
        pg.screenshot(path=str(look / "projects.png"))
        pg.click(".card[data-i='1']"); pg.wait_for_timeout(900)
        pg.screenshot(path=str(look / "modal.png")); pg.keyboard.press("Escape")
    dup = pg.evaluate("[document.querySelectorAll('.card').length, document.querySelectorAll('.skill').length, document.querySelectorAll('#also .c').length]")
    pg.evaluate("renderPrint()")
    pg.evaluate("document.querySelectorAll('#print-doc img').forEach(i => i.loading = 'eager')")
    pg.emulate_media(media="print"); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(800)
    pg.pdf(path=str(ROOT / PDF), format="A4", print_background=True, prefer_css_page_size=True)
    b.close()
print("tarjetas/habilidades/formación tras cargar:", dup)
print("errores:", errs)
print("PDF listo")
