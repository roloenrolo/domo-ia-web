# Tarjetas QR domo IA

Genera las tarjetas virtuales de Rodrigo y Rodolfo, los vCard 3.0 y los QR para web y contacto directo.

```sh
python3 tarjeta/generar.py
```

Dependencias locales:

- `segno` para generar QR SVG/PNG.
- `opencv-python-headless` solo para verificar decodificacion de los PNG.

Los datos editables viven en `tarjeta/datos.json`. El campo opcional `foto` espera un archivo existente bajo `assets/web/`, por ejemplo `retrato-rodrigo.jpg`.

`en_hoja` controla quién sale en `imprimir.html` (si falta, se asume `true`). Su tarjeta web se genera y publica igual: lo único que cambia es si sus QR entran en la hoja para imprimir. Sirve para no repartir en papel una tarjeta que todavía no está lista — hoy Rodolfo está en `false` porque no tiene foto y su cargo está sin confirmar.
