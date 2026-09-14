"""Genera el portafolio a partir de src/template.html.

- index.html            -> sitio estático para Vercel
- Dossier-JoseLuis-Cuenca.pdf -> mismo contenido en modo impresión
- (opcional) --artifact RUTA  -> versión sin <html>/<head> para publicar como Artifact

Uso:  python src/build.py [--artifact RUTA] [--look CARPETA]
"""
import json, shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PDF = "Dossier-JoseLuis-Cuenca.pdf"

cfg = json.loads((SRC / "config.json").read_text(encoding="utf-8"))
icons = json.loads((SRC / "icons.json").read_text(encoding="utf-8"))
tpl = (SRC / "template.html").read_text(encoding="utf-8")

fl_links = []
if cfg.get("freelance_url"):
    fl_links.append({"label": "Ver sitio", "href": cfg["freelance_url"], "primary": True})
fl_links.append({"label": "Repositorio", "href": "https://github.com/JCuenca17/landing-page", "primary": not cfg.get("freelance_url")})

body = (tpl.replace("__ICONS__", json.dumps(icons, separators=(",", ":")))
           .replace("__GITHUB__", icons["github"]["d"])
           .replace("[__FREELANCE_LINKS__]", json.dumps(fl_links, ensure_ascii=False)))

head, rest = body.split("</style>", 1)
favicon = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%2300FFE7'/%3E"
           "%3Ctext x='32' y='43' font-family='Arial' font-weight='700' font-size='28' text-anchor='middle' fill='%230D1B1E'%3EJL%3C/text%3E%3C/svg%3E")
site_url = cfg.get("portfolio_url", "")
standalone = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="{favicon}">
<meta property="og:title" content="Portafolio · José Luis Cuenca">
<meta property="og:description" content="Proyectos web, móviles, juegos y automatización de José Luis Cuenca Gutiérrez.">
<meta property="og:type" content="website">
{f'<meta property="og:url" content="{site_url}">' if site_url else ''}
{head}</style>
</head>
<body>
{rest}
</body>
</html>
"""
(ROOT / "index.html").write_text(standalone, encoding="utf-8")
print("index.html listo")

args = sys.argv[1:]
if "--artifact" in args:
    dst = Path(args[args.index("--artifact") + 1])
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(body, encoding="utf-8")
    print("artifact:", dst)
look = Path(args[args.index("--look") + 1]) if "--look" in args else None

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 860})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto((ROOT / "index.html").as_uri(), wait_until="networkidle")
    pg.wait_for_timeout(1500)
    if look:
        look.mkdir(parents=True, exist_ok=True)
        pg.evaluate("document.querySelector('#habilidades').scrollIntoView()"); pg.wait_for_timeout(400)
        pg.screenshot(path=str(look / "skills.png"))
        pg.evaluate("document.querySelector('#proyectos').scrollIntoView()"); pg.wait_for_timeout(400)
        pg.screenshot(path=str(look / "projects.png"))
    pg.emulate_media(media="print"); pg.wait_for_timeout(400)
    pg.pdf(path=str(ROOT / PDF), format="A4", print_background=True, prefer_css_page_size=True)
    b.close()
print("errores:", errs)
print("PDF listo")
