# Portafolio · José Luis Cuenca Gutiérrez

Desarrollador full stack y estudiante de Ingeniería de Sistemas (UNSA). Sitio estático con mis habilidades, proyectos, cursos e insignias verificadas.

## Estructura

- `index.html`: el sitio (generado, no editar a mano).
- `img/`: capturas, foto, logos e insignias.
- `src/site.html`: diseño, estilos, datos de los proyectos y lógica de la página.
- `src/capturas/`: capturas nuevas que el build copia a `img/`.
- `src/icons.json` y `src/icons-extra.json`: logos de las tecnologías (Simple Icons).
- `src/build_site.py`: genera `index.html` y `sitemap.xml`, con el SEO y los datos estructurados.
- `src/config.json`: URLs públicas del portafolio y del perfil freelance.
- `src/legacy/`: la versión anterior del sitio (plantilla y build con el dossier en PDF).

## Regenerar

```bash
python src/build_site.py
```

Se despliega en Vercel como sitio estático, sin build step.

© 2026 José Luis Cuenca Gutiérrez. Todos los derechos reservados.
