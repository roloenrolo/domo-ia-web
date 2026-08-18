# domo-ia-web — sitio PÚBLICO en vivo (domo-ia.com)

## ⚠️ Repo PÚBLICO con deploy automático
Lo que se pushea acá **se publica en domo-ia.com** vía GitHub Pages. No hay staging.
Un error de sintaxis o un placeholder sin resolver queda visible para prospectos.

No entran: costos, márgenes, credenciales, datos de leads, ni rutas internas de la máquina.

## Esta NO es la fuente de edición
La landing se trabaja en el repo privado (`ConversIA-repo/landing-domo-ia/`) y se **copia**
acá para desplegar. Editar directo acá desincroniza las dos copias en silencio.

Flujo correcto: editar en el privado → verificar local → copiar acá → pushear.

## Antes de tocar diseño
El sistema de marca vive en el repo privado (`marca/DESIGN.md`): paleta, tipografía y tokens.
No improvisar colores. La paleta oficial es la editorial cálida; el morado está prohibido.

## Verificación antes de pushear
    python3 -m http.server     # abrir index.html y revisar en el navegador
    grep -rn "XXXXXXX\|TODO\|placeholder" .   # cero placeholders sin resolver
Revisar a mano: que los CTA apunten al calendario correcto y que no queden
referencias a dominios viejos.

## Qué NO hacer
- No editar acá como fuente. Es un destino de deploy.
- No pushear sin haber abierto la página localmente.
- No commitear media pesada sin confirmar (el repo sirve el sitio en vivo).
