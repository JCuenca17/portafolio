# Portafolio · José Luis Cuenca Gutiérrez

Estudiante de Ingeniería de Sistemas (UNSA) y desarrollador de software. Sitio estático con mis proyectos, sus características, funcionalidades y tecnologías, y el dossier descargable en PDF.

## Estructura

- `index.html`: el sitio (generado, no editar a mano).
- `img/`: capturas, foto y logos.
- `Dossier-JoseLuis-Cuenca.pdf`: dossier generado desde la misma página en modo impresión.
- `src/template.html`: plantilla con estilos, datos de los proyectos y lógica.
- `src/build.py`: genera `index.html` y el PDF (Python + Playwright + Chrome).
- `src/config.json`: URLs públicas del portafolio y del perfil freelance.

## Regenerar

```bash
python src/build.py
```

Se despliega en Vercel como sitio estático, sin build step.
