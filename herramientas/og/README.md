# Imagen Open Graph

Genera `assets/web/og-domo-ia.jpg` (1200×630) a partir de `og-domo-ia.html`:

```sh
./herramientas/og/generar.sh
```

Requiere Google Chrome en `/Applications`, `sips` y conexión para cargar Archivo e IBM Plex Mono desde Google Fonts. El script espera las webfonts mediante un presupuesto de tiempo virtual, fija el fondo de Chrome desde la línea de comandos, convierte la captura PNG a JPG y valida las dimensiones finales.

WhatsApp y otras redes guardan la preview por URL. Después de publicar puede ser necesario forzar el refresco con una herramienta como el depurador de contenido compartido de Facebook; de lo contrario, la imagen anterior puede seguir apareciendo durante un tiempo.
