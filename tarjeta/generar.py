#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import quote

import segno


ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "datos.json"
TOKENS_SOURCE = ROOT.parent / "ConversIA-repo" / "marca" / "tokens.css"

SITE_URL = "https://domo-ia.com"
ORG = "domo IA"
LINKEDIN = "https://www.linkedin.com/company/domoia/"
INSTAGRAM = "https://instagram.com/domoia.cl"
FONT_LINKS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">"""


def read_json() -> dict[str, dict[str, str]]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def write_text_if_changed(path: Path, content: str, newline: str = "\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline=newline) as f:
        f.write(content)


def slug_initials(name: str) -> str:
    return "".join(part[0] for part in name.split()[:2]).upper()


def tel_human(tel: str) -> str:
    digits = re.sub(r"\D", "", tel)
    if digits.startswith("56") and len(digits) == 11:
        return f"+56 {digits[2]} {digits[3:7]} {digits[7:]}"
    return tel


def wa_url(person: dict[str, str]) -> str:
    digits = re.sub(r"\D", "", person["tel"])
    msg = f"Hola {person['nombre'].split()[0]}, vi tu tarjeta de domo IA y quiero conversar."
    return f"https://wa.me/{digits}?text={quote(msg)}"


def vcard_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def family_name(name: str) -> tuple[str, str]:
    parts = name.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[-1], " ".join(parts[:-1])


def vcard(person: dict[str, str]) -> str:
    family, given = family_name(person["nombre"])
    note = f"{person['linea']} Sitio: {SITE_URL}"
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{vcard_escape(family)};{vcard_escape(given)};;;",
        f"FN:{vcard_escape(person['nombre'])}",
        f"ORG:{vcard_escape(ORG)}",
        f"TITLE:{vcard_escape(person['cargo'])}",
        f"TEL;TYPE=CELL,VOICE:{person['tel']}",
        f"EMAIL;TYPE=INTERNET:{person['email']}",
        f"URL:{SITE_URL}",
        f"NOTE:{vcard_escape(note)}",
        "END:VCARD",
    ]
    return "\r\n".join(lines) + "\r\n"


def token_css() -> str:
    raw = TOKENS_SOURCE.read_text(encoding="utf-8")
    dark = re.search(r'\[data-theme="dark"\]\s*\{(?P<body>.*?)\n\}', raw, re.S)
    if not dark:
        raise RuntimeError("No se encontro el bloque de tokens dark.")
    return raw + "\n@media (prefers-color-scheme: dark) {\n  :root {" + dark.group("body") + "\n  }\n}\n"


def mark_svg() -> str:
    return """<svg width="32" height="32" viewBox="0 0 100 100" fill="none" aria-hidden="true">
        <path d="M 15 78 A 42 42 0 1 1 85 78" stroke="var(--text)" stroke-width="17" stroke-linecap="round" fill="none"/>
        <circle cx="50" cy="74" r="13" fill="var(--brand2)"/>
      </svg>"""


def html_page(slug: str, person: dict[str, str]) -> str:
    safe_name = html.escape(person["nombre"])
    safe_cargo = html.escape(person["cargo"])
    safe_line = html.escape(person["linea"])
    safe_email = html.escape(person["email"])
    human_tel = html.escape(tel_human(person["tel"]))
    initials = html.escape(slug_initials(person["nombre"]))
    photo = person.get("foto", "").strip()
    if photo:
        avatar = f'<div class="avatar"><img src="../../assets/web/{html.escape(photo)}" alt="Retrato de {safe_name}" width="132" height="132"></div>'
    else:
        avatar = f'<div class="avatar avatar-mark" aria-hidden="true">{mark_svg()}<span>{initials}</span></div>'

    agenda = ""
    if person.get("agenda", "").strip():
        agenda = f'<a class="action secondary" href="{html.escape(person["agenda"])}" target="_blank" rel="noopener">Agendar</a>'

    return f"""<!DOCTYPE html>
<html lang="es-CL">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{safe_name} — tarjeta domo IA</title>
<meta name="description" content="{safe_name}, {safe_cargo} en domo IA. WhatsApp, correo y contacto descargable.">
<link rel="canonical" href="{SITE_URL}/tarjeta/{slug}/">
<meta property="og:type" content="profile">
<meta property="og:site_name" content="domo IA">
<meta property="og:locale" content="es_CL">
<meta property="og:title" content="{safe_name} — domo IA">
<meta property="og:description" content="{safe_line}">
<meta name="theme-color" content="#F6F3EC">
{FONT_LINKS}
<style>
{token_css()}
*{{box-sizing:border-box}}
html{{background:var(--bg);color:var(--text)}}
body{{margin:0;min-width:0;background:var(--bg);color:var(--text);font-family:var(--font-text);font-size:16px;line-height:1.6}}
a{{color:inherit}}
.shell{{min-height:100svh;display:grid;grid-template-rows:auto 1fr auto}}
.wrap{{width:min(100% - 40px,720px);margin:0 auto}}
.top{{padding:20px 0;border-bottom:var(--border-w) solid var(--border)}}
.mark{{display:inline-flex;align-items:center;gap:9px;font-family:var(--font-display);font-variation-settings:"wdth" 125;font-weight:800;letter-spacing:.02em;font-size:18px;text-decoration:none;color:var(--text)}}
.mark svg{{flex:none}}
.mark .ia{{color:var(--brand2)}}
main{{display:grid;align-items:center;padding:36px 0}}
.card{{background:var(--surface);border:var(--border-w) solid var(--border);border-radius:var(--radius-card);box-shadow:var(--shadow);padding:28px;display:grid;gap:24px}}
.identity{{display:grid;gap:20px;grid-template-columns:auto 1fr;align-items:center}}
.avatar,.avatar-mark{{width:132px;height:132px;border-radius:var(--radius-card);border:var(--border-w) solid var(--border);background:var(--surface2);overflow:hidden}}
.avatar img{{width:100%;height:100%;object-fit:cover;display:block}}
.avatar-mark{{display:grid;place-items:center;position:relative}}
.avatar-mark svg{{width:76px;height:76px}}
.avatar-mark span{{position:absolute;bottom:12px;right:12px;font-family:var(--font-data);font-weight:600;color:var(--brand2);background:var(--chip);border:var(--border-w) solid var(--border);border-radius:var(--radius-pill);padding:2px 8px;font-size:13px}}
.eyebrow{{margin:0 0 8px;font-family:var(--font-data);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--brand2)}}
h1{{margin:0;font-family:var(--font-display);font-variation-settings:"wdth" 118;font-weight:800;letter-spacing:0;font-size:clamp(32px,8vw,48px);line-height:1.04}}
.linea{{margin:12px 0 0;color:var(--muted);max-width:34ch}}
.actions{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.action{{min-height:50px;border-radius:var(--radius-sm);border:var(--border-w) solid var(--border);display:inline-flex;align-items:center;justify-content:center;text-align:center;text-decoration:none;font-weight:600;padding:12px 14px;transition:transform var(--dur-hover) var(--ease),border-color var(--dur-hover) var(--ease),background var(--dur-hover) var(--ease);overflow-wrap:anywhere}}
button.action{{font:inherit;cursor:pointer}}
.action:hover{{transform:translateY(-3px);border-color:var(--brand)}}
.primary{{grid-column:1/-1;background:var(--brand);border-color:var(--brand);color:var(--surface)}}
.secondary{{background:var(--surface2);color:var(--text)}}
.ghost{{background:transparent;color:var(--brand)}}
.contact{{display:grid;gap:8px;border-top:var(--border-w) solid var(--border);padding-top:20px}}
.row{{display:flex;justify-content:space-between;gap:16px;align-items:baseline;color:var(--muted)}}
.row b{{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--text)}}
.mono{{font-family:var(--font-data);font-variant-numeric:tabular-nums}}
.qr-overlay{{position:fixed;inset:0;z-index:20;display:grid;place-items:center;padding:20px;background:color-mix(in srgb,var(--text) 64%,transparent);opacity:0;pointer-events:none;transition:opacity var(--dur-enter) var(--ease)}}
.qr-overlay[hidden]{{display:none}}
.qr-overlay.is-open{{opacity:1;pointer-events:auto}}
.qr-dialog{{position:relative;width:min(100%,440px);display:grid;gap:16px;justify-items:center;background:#FFFFFF;color:#1C2340;border:var(--border-w) solid #E2DCCC;border-radius:var(--radius-card);box-shadow:var(--shadow);padding:28px}}
.qr-close{{position:absolute;top:12px;right:12px;width:40px;height:40px;border-radius:var(--radius-pill);border:var(--border-w) solid #E2DCCC;background:#F0EBE0;color:#1C2340;font:inherit;font-size:28px;line-height:1;cursor:pointer}}
.qr-frame{{width:min(100%,340px);background:#FFFFFF;border:var(--border-w) solid #E2DCCC;border-radius:var(--radius-sm);padding:14px}}
.qr-frame img{{display:block;width:100%;height:auto;background:#FFFFFF}}
.qr-name{{margin:0;font-family:var(--font-display);font-variation-settings:"wdth" 112;font-weight:800;font-size:24px;line-height:1.1;text-align:center}}
footer{{padding:20px 0 32px;color:var(--muted);font-size:13px}}
footer .wrap{{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}}
footer a{{color:var(--muted);text-underline-offset:3px}}
@media (prefers-color-scheme:dark){{html:not([data-theme="light"]){{color-scheme:dark}}html:not([data-theme="light"]) body{{background:var(--bg)}}}}
@media (max-width:520px){{
  .wrap{{width:min(100% - 28px,720px)}}
  main{{padding:20px 0}}
  .card{{padding:20px;gap:20px}}
  .identity{{grid-template-columns:1fr;text-align:left}}
  .avatar,.avatar-mark{{width:112px;height:112px}}
  .actions{{grid-template-columns:1fr}}
  .row{{display:grid;gap:2px}}
}}
</style>
</head>
<body>
<div class="shell">
  <header class="top">
    <div class="wrap">
      <a class="mark" href="{SITE_URL}/" aria-label="domo IA">
        {mark_svg()}
        <span>DOMO<span class="ia">&nbsp;IA</span></span>
      </a>
    </div>
  </header>
  <main>
    <div class="wrap">
      <article class="card" aria-label="Tarjeta de contacto">
        <div class="identity">
          {avatar}
          <div>
            <p class="eyebrow">{safe_cargo}</p>
            <h1>{safe_name}</h1>
            <p class="linea">{safe_line}</p>
          </div>
        </div>
        <nav class="actions" aria-label="Acciones de contacto">
          <a class="action primary" href="../{slug}.vcf" download>Guardar contacto</a>
          <button class="action secondary" type="button" data-qr-open>Mostrar mi QR</button>
          <a class="action secondary" href="{html.escape(wa_url(person))}" target="_blank" rel="noopener">WhatsApp</a>
          <a class="action secondary mono" href="mailto:{safe_email}">Correo</a>
          {agenda}
          <a class="action secondary" href="{SITE_URL}/">Sitio</a>
          <a class="action secondary" href="{LINKEDIN}" target="_blank" rel="noopener">LinkedIn</a>
          <a class="action secondary" href="{INSTAGRAM}" target="_blank" rel="noopener">Instagram</a>
        </nav>
        <div class="contact">
          <div class="row"><b>Telefono</b><span class="mono">{human_tel}</span></div>
          <div class="row"><b>Correo</b><span class="mono">{safe_email}</span></div>
        </div>
      </article>
    </div>
  </main>
  <footer>
    <div class="wrap">
      <span>domo IA SpA · Santiago de Chile</span>
      <a href="/privacidad/">Privacidad</a>
    </div>
  </footer>
</div>
<div class="qr-overlay" id="qr-dialog-{slug}" role="dialog" aria-modal="true" aria-labelledby="qr-title-{slug}" hidden>
  <div class="qr-dialog">
    <button class="qr-close" type="button" aria-label="Cerrar QR" data-qr-close>×</button>
    <div class="qr-frame">
      <img src="../qr/qr-{slug}-web.svg" alt="QR web de {safe_name}" width="340" height="340">
    </div>
    <p class="qr-name" id="qr-title-{slug}">{safe_name}</p>
  </div>
</div>
<script>
(() => {{
  const openButton = document.querySelector("[data-qr-open]");
  const dialog = document.getElementById("qr-dialog-{slug}");
  if (!openButton || !dialog) return;

  const closeButton = dialog.querySelector("[data-qr-close]");
  let previousFocus = null;

  function focusableElements() {{
    return Array.from(dialog.querySelectorAll("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"))
      .filter((element) => !element.disabled && element.offsetParent !== null);
  }}

  function closeDialog() {{
    dialog.classList.remove("is-open");
    dialog.hidden = true;
    document.removeEventListener("keydown", onKeydown);
    if (previousFocus && typeof previousFocus.focus === "function") {{
      previousFocus.focus({{ preventScroll: true }});
    }}
  }}

  function onKeydown(event) {{
    if (event.key === "Escape") {{
      closeDialog();
      return;
    }}

    if (event.key !== "Tab") return;

    const focusable = focusableElements();
    if (!focusable.length) return;

    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {{
      event.preventDefault();
      last.focus();
    }} else if (!event.shiftKey && document.activeElement === last) {{
      event.preventDefault();
      first.focus();
    }}
  }}

  function openDialog() {{
    previousFocus = document.activeElement;
    dialog.hidden = false;
    dialog.classList.add("is-open");
    document.addEventListener("keydown", onKeydown);
    closeButton.focus({{ preventScroll: true }});
  }}

  openButton.addEventListener("click", openDialog);
  closeButton.addEventListener("click", closeDialog);
  dialog.addEventListener("click", (event) => {{
    if (event.target === dialog) closeDialog();
  }});
}})();
</script>
</body>
</html>
"""


def print_page(data: dict[str, dict[str, str]]) -> str:
    # Solo entran a la hoja de imprimir quienes estén listos para repartir.
    # Una tarjeta sin foto no se imprime: en papel el monograma no sostiene la pieza.
    cards = []
    for slug, person in data.items():
        if not person.get("en_hoja", True):
            continue
        safe_name = html.escape(person["nombre"])
        cards.append(f"""
        <section class="qr-card">
          <h2>{safe_name}</h2>
          <div class="qr-grid">
            <figure><img src="qr/qr-{slug}-web.svg" alt="QR web {safe_name}"><figcaption>Tarjeta web</figcaption></figure>
            <figure><img src="qr/qr-{slug}-vcard.svg" alt="QR vCard {safe_name}"><figcaption>Guardar contacto</figcaption></figure>
          </div>
        </section>""")
    return f"""<!DOCTYPE html>
<html lang="es-CL">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QR para imprimir — domo IA</title>
{FONT_LINKS}
<style>
{token_css()}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--text);font-family:var(--font-text);line-height:1.45}}
.sheet{{width:min(100% - 40px,960px);margin:0 auto;padding:36px 0 48px}}
.mark{{display:inline-flex;align-items:center;gap:9px;font-family:var(--font-display);font-variation-settings:"wdth" 125;font-weight:800;letter-spacing:.02em;font-size:18px;text-decoration:none;color:var(--text)}}
.mark .ia{{color:var(--brand2)}}
h1{{font-family:var(--font-display);font-variation-settings:"wdth" 118;font-weight:800;letter-spacing:0;font-size:34px;line-height:1.1;margin:24px 0 8px}}
.intro{{color:var(--muted);margin:0 0 28px}}
.cards{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.qr-card{{background:var(--surface);border:var(--border-w) solid var(--border);border-radius:var(--radius-card);padding:20px;break-inside:avoid}}
h2{{font-family:var(--font-display);font-variation-settings:"wdth" 112;font-size:22px;margin:0 0 16px}}
.qr-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
figure{{margin:0;border:var(--border-w) solid var(--border);border-radius:var(--radius-sm);padding:12px;background:var(--surface2);text-align:center}}
img{{width:100%;height:auto;display:block;background:var(--surface);border-radius:var(--radius-xs)}}
figcaption{{font-family:var(--font-data);font-size:12px;color:var(--muted);margin-top:8px}}
@media (max-width:700px){{.cards,.qr-grid{{grid-template-columns:1fr}}.sheet{{width:min(100% - 28px,960px)}}}}
@media print{{body{{background:var(--surface)}}.sheet{{width:auto;padding:0}}.cards{{gap:12mm}}.qr-card{{box-shadow:none;page-break-inside:avoid}}}}
</style>
</head>
<body>
<main class="sheet">
  <a class="mark" href="{SITE_URL}/" aria-label="domo IA">
    {mark_svg()}
    <span>DOMO<span class="ia">&nbsp;IA</span></span>
  </a>
  <h1>QR para tarjetas domo IA</h1>
  <p class="intro">Cada persona tiene un QR para abrir la tarjeta web y otro para guardar el contacto directo.</p>
  <div class="cards">
    {''.join(cards)}
  </div>
</main>
</body>
</html>
"""


def generate_qr(path_base: Path, payload: str) -> None:
    qr = segno.make(payload, error="m")
    path_base.parent.mkdir(parents=True, exist_ok=True)
    svg_path = path_base.with_suffix(".svg")
    qr.save(svg_path, scale=8, border=4, dark="#1C2340", light="#FFFFFF")
    svg_path.write_text(re.sub(r"#[fF]{3}\b", "#FFFFFF", svg_path.read_text(encoding="utf-8")), encoding="utf-8")
    qr.save(path_base.with_suffix(".png"), scale=10, border=4, dark="#1C2340", light="#FFFFFF")


def main() -> None:
    data = read_json()
    for slug, person in data.items():
        page_dir = HERE / slug
        write_text_if_changed(page_dir / "index.html", html_page(slug, person))
        vcf = vcard(person)
        write_text_if_changed(HERE / f"{slug}.vcf", vcf, newline="")
        generate_qr(HERE / "qr" / f"qr-{slug}-web", f"{SITE_URL}/tarjeta/{slug}/")
        generate_qr(HERE / "qr" / f"qr-{slug}-vcard", vcf)
    write_text_if_changed(HERE / "imprimir.html", print_page(data))


if __name__ == "__main__":
    main()
