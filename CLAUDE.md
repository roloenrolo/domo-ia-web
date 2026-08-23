# domo-ia-web — sitio PÚBLICO en vivo (domo-ia.com)

## ⚠️ Repo PÚBLICO con deploy automático
Lo que se pushea acá **se publica en domo-ia.com** vía GitHub Pages. No hay staging.
Un error de sintaxis o un placeholder sin resolver queda visible para prospectos.

No entran: costos, márgenes, credenciales, datos de leads, ni rutas internas de la máquina.

## Esta ES la fuente de edición
Este repo público es la fuente de edición del sitio en vivo. Los cambios de la
landing se hacen acá, se verifican acá y se despliegan desde acá.

Nunca copiar contenido desde el repo privado hacia este repo. Si algo vive en el
repo privado, trátalo como material interno o histórico, no como fuente.

**Por qué cambió esta regla:** hasta agosto de 2026 el contrato decía lo contrario
(editar en `ConversIA-repo/landing-domo-ia/` y copiar acá). Ese flujo se rompió en
algún punto entre julio y agosto. Verificado el 21-ago-2026 y de nuevo el 23-ago-2026:
el privado está **285 líneas atrasado** respecto a este repo — le falta la sección
`#packs` completa, entre otras cosas. Copiar desde el privado **borraría secciones que
hoy están en vivo en domo-ia.com**. Queda pendiente que Rodrigo decida si se sincroniza
el privado en esta dirección o se retira de circulación.

## Antes de tocar diseño
El sistema de marca vive en el repo privado (`marca/DESIGN.md`): paleta, tipografía y tokens.
No improvisar colores. La paleta oficial es la editorial cálida; el morado está prohibido.

## Verificación antes de pushear
    python3 -m http.server     # abrir index.html y revisar en el navegador
    grep -rn "XXXXXXX\|TODO\|placeholder" .   # cero placeholders sin resolver
Revisar a mano: que los CTA apunten al calendario correcto y que no queden
referencias a dominios viejos.

## Qué NO hacer
- No copiar archivos desde el repo privado como si fueran la fuente.
- No pushear sin haber abierto la página localmente.
- No commitear media pesada sin confirmar (el repo sirve el sitio en vivo).
