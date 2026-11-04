"""Genera index.html del portafolio a partir de src/site.html.

- Las imágenes se referencian como archivos en img/ (las capturas nuevas se copian desde src/capturas/).
- Los logos salen de src/icons.json + src/icons-extra.json (Simple Icons).
- Conserva el SEO: título, descripción, Open Graph, verificación de Google y datos estructurados.

Uso:  python src/build_site.py
"""
import datetime, json, re, shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
IMG = ROOT / "img"
cfg = json.loads((SRC / "config.json").read_text(encoding="utf-8"))
URL = cfg["portfolio_url"]

body = (SRC / "site.html").read_text(encoding="utf-8")
# quitar la cabecera propia de la maqueta (título, meta de vista y fuentes): van en <head>
body = re.sub(r"\A.*?(?=<style>)", "", body, flags=re.S)

# ── imágenes ──
for f in (SRC / "capturas").glob("*.jpg"):
    dst = IMG / f.name
    if not dst.exists() or dst.stat().st_mtime < f.stat().st_mtime:
        im = Image.open(f).convert("RGB")
        if im.width > 1600:
            im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
        im.save(dst, "JPEG", quality=84, optimize=True, progressive=True)
files = {p.stem: p.name for p in IMG.iterdir() if p.suffix.lower() in (".jpg", ".png")}
def img(m):
    key = m.group(1)
    if key not in files: raise SystemExit(f"Falta la imagen: {key}")
    return "img/" + files[key]
body = re.sub(r"%%IMG:([\w-]+)%%", img, body)

# ── logos ──
icons = json.loads((SRC / "icons.json").read_text(encoding="utf-8"))
extra = json.loads((SRC / "icons-extra.json").read_text(encoding="utf-8"))
HEX = {"vuedotjs":"4FC08D","fastapi":"009688","flask":"000000","sqlalchemy":"D71F00","vitest":"6E9F18","googleappsscript":"4285F4","opentofu":"E8B400",
       "amazonwebservices":"232F3E","mermaid":"FF3670","sonarqube":"4E9BCD","whatsapp":"25D366","selenium":"43B02A","googlesheets":"34A853","cisco":"1BA0D7",
       "google":"4285F4","sqlite":"003B57","openjdk":"E76F00","nodedotjs":"5FA04E"}
for slug, d in extra.items():
    icons[slug] = {"d": d, "hex": HEX.get(slug, "111413")}
used = set(re.findall(r'\["[^"\]]+","(\w+)"\]', body)) | {"github", "googlecloud"}
missing = sorted(k for k in used if k not in icons and not k.startswith("c_") and k in HEX)
if missing: raise SystemExit(f"Faltan logos: {missing}")
body = (body.replace("%%ICONS%%", json.dumps({k: icons[k] for k in used if k in icons}, separators=(",", ":")))
            .replace("%%GITHUB%%", icons["github"]["d"]).replace("%%GCLOUD%%", icons["googlecloud"]["d"]))
assert "%%" not in body, "Quedó un marcador sin reemplazar"

# ── SEO ──
TITLE = "José Luis Cuenca | Desarrollador full stack en Arequipa · Portafolio"
DESC = ("Portafolio de José Luis Cuenca Gutiérrez, desarrollador full stack y estudiante de Ingeniería de Sistemas (UNSA) en Arequipa, Perú: "
        "apps web y móviles, automatización y un videojuego de tesis con visión computacional.")
proj = re.findall(r't:"([^"]+)", d:"([^"]+)"', body)
creds = re.findall(r'<a class="badge" href="([^"]+)"[^>]*>.*?<small>([^<]+)</small><b>([^<]+)</b>', body)
ld = {"@context": "https://schema.org", "@graph": [
    {"@type": "Person", "@id": URL + "#persona", "name": "José Luis Cuenca Gutiérrez", "givenName": "José Luis", "familyName": "Cuenca Gutiérrez",
     "url": URL, "image": URL + "img/foto.jpg", "jobTitle": "Desarrollador full stack", "description": DESC,
     "address": {"@type": "PostalAddress", "addressLocality": "Arequipa", "addressCountry": "PE"},
     "alumniOf": [{"@type": "CollegeOrUniversity", "name": "Universidad Nacional de San Agustín de Arequipa"},
                  {"@type": "EducationalOrganization", "name": "Oracle Next Education"}],
     "knowsAbout": sorted(set(re.findall(r'\["([^"\]]+)","(?:\w+)"\]', body))),
     "hasCredential": [{"@type": "EducationalOccupationalCredential", "name": b, "credentialCategory": "badge",
                        "recognizedBy": {"@type": "Organization", "name": o}, "url": u} for u, o, b in creds if "credly.com/users" not in u],
     "sameAs": ["https://github.com/JCuenca17", "https://www.linkedin.com/in/josecuencag/", cfg.get("freelance_url", ""),
                "https://www.credly.com/users/jose-luis-cuenca-gutierrez", "https://abduzcan17.itch.io/"]},
    {"@type": "ProfilePage", "@id": URL + "#pagina", "url": URL, "name": TITLE, "inLanguage": "es-PE", "mainEntity": {"@id": URL + "#persona"},
     "dateModified": datetime.date.today().isoformat(), "primaryImageOfPage": URL + "og.jpg"},
    {"@type": "ItemList", "name": "Proyectos", "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {"@type": "CreativeWork", "name": t, "description": d}} for i, (t, d) in enumerate(proj)]}]}
ld["@graph"][0]["sameAs"] = [x for x in ld["@graph"][0]["sameAs"] if x]
gsv = f'\n<meta name="google-site-verification" content="{cfg["google_verification"]}">' if cfg.get("google_verification") else ""
head = f"""<!doctype html>
<html lang="es-PE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<meta name="robots" content="index, follow, max-image-preview:large">{gsv}
<meta name="author" content="José Luis Cuenca Gutiérrez">
<meta name="theme-color" content="#F6F6F3">
<link rel="canonical" href="{URL}">
<link rel="icon" href="favicon.ico" sizes="48x48">
<link rel="icon" href="icons/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="manifest" href="site.webmanifest">
<meta property="og:type" content="profile">
<meta property="og:locale" content="es_PE">
<meta property="og:site_name" content="Portafolio · José Luis Cuenca">
<meta property="og:title" content="José Luis Cuenca · Desarrollador full stack">
<meta property="og:description" content="Apps web y móviles, automatización y un videojuego de tesis. Estudiante de Ingeniería de Sistemas en la UNSA, Arequipa.">
<meta property="og:url" content="{URL}">
<meta property="og:image" content="{URL}og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="José Luis Cuenca · Desarrollador full stack">
<meta name="twitter:image" content="{URL}og.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anton&family=Sora:wght@400;500;600;700&display=swap">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}</script>
<style>body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
</head>
<body>
"""
(ROOT / "index.html").write_text(head + body + "\n</body>\n</html>\n", encoding="utf-8")
today = datetime.date.today().isoformat()
imgs = ["img/foto.jpg"] + [m for m in dict.fromkeys(re.findall(r'img:"(img/[^"]+)"', body))]
(ROOT / "sitemap.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>{URL}</loc>
    <lastmod>{today}</lastmod>
""" + "".join(f"    <image:image><image:loc>{URL}{i}</image:loc></image:image>\n" for i in imgs) + """  </url>
</urlset>
""", encoding="utf-8")
print("index.html:", (ROOT / "index.html").stat().st_size // 1024, "KB ·", len(proj), "proyectos ·", len(creds), "insignias")
