#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import OrderedDict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "index.html"
TRANSLATIONS = ROOT / "_fuente" / "i18n" / "traducciones.json"
BASE = "https://domo-ia.com"
LANGS = {
    "es": {"html": "es-CL", "url": f"{BASE}/", "locale": "es_CL"},
    "en": {"html": "en", "url": f"{BASE}/en/", "locale": "en_US"},
    "it": {"html": "it", "url": f"{BASE}/it/", "locale": "it_IT"},
}
TEXT_TAGS = {"title", "p", "h1", "h2", "h3", "li", "summary", "span", "a", "video"}
INLINE_TAGS = {
    "a", "abbr", "b", "br", "cite", "code", "em", "i", "small", "span", "strong",
    "sub", "sup", "svg", "path", "circle", "source",
}
SKIP_TAGS = {"script", "style"}
TRANSLATABLE_META = {
    ("name", "description"),
    ("property", "og:title"),
    ("property", "og:description"),
    ("name", "twitter:title"),
    ("name", "twitter:description"),
}
PROPER_EQUAL = {
    "Domo IA", "domo IA", "domo-ia", "DOMO IA", "Antonia", "Matías", "Sofía",
    "Clara", "Amanda", "Lucas", "Laura", "Diego", "Sebastián",
    "Rodrigo González Villalobos", "Rodolfo Alfaro", "Damián Roba Jesset",
    "WhatsApp", "LinkedIn", "Método DOMO", "Universidad Central de Chile",
    "Universitat Politècnica de Catalunya", "Universidad de Valparaíso",
    "Universidad de Chile", "Duoc UC", "Université Toulouse – Jean Jaurès",
    "MBA",
    "ES", "EN", "IT",
}


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.tokens: list[dict] = []
        self.stack: list[int] = []

    def handle_decl(self, decl: str) -> None:
        self.tokens.append({"type": "decl", "raw": f"<!{decl}>"})

    def handle_comment(self, data: str) -> None:
        self.tokens.append({"type": "comment", "raw": f"<!--{data}-->"})

    def handle_pi(self, data: str) -> None:
        self.tokens.append({"type": "pi", "raw": f"<?{data}>"})

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        idx = len(self.tokens)
        self.tokens.append({
            "type": "start", "tag": tag.lower(), "attrs": list(attrs),
            "raw": self.get_starttag_text(), "end": None, "parent": self.stack[-1] if self.stack else None,
        })
        if tag.lower() not in {"meta", "link", "img", "source", "br", "input"}:
            self.stack.append(idx)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tokens.append({
            "type": "startend", "tag": tag.lower(), "attrs": list(attrs),
            "raw": self.get_starttag_text(), "parent": self.stack[-1] if self.stack else None,
        })

    def handle_endtag(self, tag: str) -> None:
        idx = len(self.tokens)
        tag = tag.lower()
        self.tokens.append({"type": "end", "tag": tag, "raw": f"</{tag}>", "start": None})
        for pos in range(len(self.stack) - 1, -1, -1):
            start = self.stack[pos]
            if self.tokens[start]["tag"] == tag:
                self.tokens[start]["end"] = idx
                self.tokens[idx]["start"] = start
                del self.stack[pos:]
                break

    def handle_data(self, data: str) -> None:
        self.tokens.append({"type": "data", "raw": data, "parent": self.stack[-1] if self.stack else None})

    def handle_entityref(self, name: str) -> None:
        self.handle_data(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.handle_data(f"&#{name};")


def parse_html(text: str) -> list[dict]:
    parser = Parser()
    parser.feed(text)
    parser.close()
    return parser.tokens


def attrs_dict(token: dict) -> dict[str, str | None]:
    return {k.lower(): v for k, v in token.get("attrs", [])}


def set_attr(attrs: list[tuple[str, str | None]], name: str, value: str) -> list[tuple[str, str | None]]:
    out: list[tuple[str, str | None]] = []
    done = False
    for key, val in attrs:
        if key.lower() == name.lower():
            out.append((key, value))
            done = True
        else:
            out.append((key, val))
    if not done:
        out.append((name, value))
    return out


def render_tag(tag: str, attrs: list[tuple[str, str | None]], close: bool = False) -> str:
    bits = [tag]
    for key, value in attrs:
        if value is None:
            bits.append(key)
        else:
            bits.append(f'{key}="{html.escape(value, quote=True)}"')
    return "<" + " ".join(bits) + ("/>" if close else ">")


def text_between(tokens: list[dict], start: int, end: int) -> str:
    return "".join(t["raw"] for t in tokens[start + 1:end] if t["type"] == "data")


def has_non_ws_text(tokens: list[dict], start: int, end: int) -> bool:
    return bool(re.search(r"\S", text_between(tokens, start, end)))


def inline_only(tokens: list[dict], start: int, end: int) -> bool:
    for i in range(start + 1, end):
        t = tokens[i]
        if t["type"] in {"start", "startend"} and t["tag"] not in INLINE_TAGS:
            return False
    return True


def unit_key(tokens: list[dict], start: int, end: int) -> tuple[str, list[str]]:
    markers: list[str] = []
    parts: list[str] = []
    i = start + 1
    while i < end:
        t = tokens[i]
        if t["type"] == "data":
            parts.append(t["raw"])
        elif t["type"] == "start":
            n = len(markers)
            parts.append("{" + str(n) + "}")
            markers.append(render_token(t))
        elif t["type"] == "end":
            n = len(markers)
            parts.append("{" + str(n) + "}")
            markers.append(t["raw"])
        elif t["type"] == "startend":
            n = len(markers)
            parts.append("{" + str(n) + "}")
            markers.append(render_token(t))
        else:
            parts.append(t["raw"])
        i += 1
    return "".join(parts), markers


def is_text_unit(tokens: list[dict], idx: int) -> bool:
    t = tokens[idx]
    classes = (attrs_dict(t).get("class") or "").split()
    return (
        t["type"] == "start"
        and t["tag"] in TEXT_TAGS
        and t["tag"] not in SKIP_TAGS
        and attrs_dict(t).get("aria-hidden") != "true"
        and "mark" not in classes
        and "lang-switch" not in classes
        and t.get("end") is not None
        and has_non_ws_text(tokens, idx, t["end"])
        and inline_only(tokens, idx, t["end"])
    )


def discover_units(tokens: list[dict]) -> dict[int, tuple[int, str, list[str]]]:
    units: dict[int, tuple[int, str, list[str]]] = {}

    def walk(start: int, end: int) -> None:
        i = start
        while i < end:
            t = tokens[i]
            if t["type"] == "start" and t.get("end") is not None:
                classes = (attrs_dict(t).get("class") or "").split()
                if attrs_dict(t).get("aria-hidden") == "true" or "mark" in classes or "lang-switch" in classes:
                    i = t["end"] + 1
                    continue
                if is_text_unit(tokens, i):
                    key, markers = unit_key(tokens, i, t["end"])
                    units[i] = (t["end"], key, markers)
                    i = t["end"] + 1
                else:
                    walk(i + 1, t["end"])
                    i = t["end"] + 1
            else:
                i += 1

    walk(0, len(tokens))
    return units


def is_excluded_text(tokens: list[dict], idx: int) -> bool:
    parent = tokens[idx].get("parent")
    while parent is not None:
        token = tokens[parent]
        attrs = attrs_dict(token)
        classes = (attrs.get("class") or "").split()
        if token["tag"] in SKIP_TAGS:
            return True
        if attrs.get("aria-hidden") == "true":
            return True
        if "mark" in classes or "lang-switch" in classes:
            return True
        parent = token.get("parent")
    return False


def assert_complete_text_coverage(tokens: list[dict], units: dict[int, tuple[int, str, list[str]]]) -> list[tuple[str, str]]:
    covered = set()
    for start, (end, _key, _markers) in units.items():
        covered.update(range(start + 1, end))
    orphans: list[tuple[str, str]] = []
    for idx, token in enumerate(tokens):
        if token["type"] != "data" or not re.search(r"\S", token["raw"]):
            continue
        if idx in covered or is_excluded_text(tokens, idx):
            continue
        parent = token.get("parent")
        tag = tokens[parent]["tag"] if parent is not None else "(document)"
        text = " ".join(html.unescape(token["raw"]).split())
        orphans.append((tag, text))
    return orphans


def abort_on_orphan_text(orphans: list[tuple[str, str]]) -> None:
    if not orphans:
        return
    print("build abortado: nodos de texto sin unidad i18n", file=sys.stderr)
    for tag, text in orphans:
        print(f"- <{tag}>: {text}", file=sys.stderr)
    raise SystemExit(1)


def render_token(token: dict, attrs: list[tuple[str, str | None]] | None = None) -> str:
    if token["type"] == "start":
        return render_tag(token["tag"], attrs if attrs is not None else token["attrs"])
    if token["type"] == "startend":
        return render_tag(token["tag"], attrs if attrs is not None else token["attrs"], True)
    return token["raw"]


def add_key(keys: OrderedDict[str, None], key: str) -> None:
    if key and re.search(r"\S", key) and key not in keys:
        keys[key] = None


def collect_keys(tokens: list[dict]) -> OrderedDict[str, None]:
    keys: OrderedDict[str, None] = OrderedDict()
    units = discover_units(tokens)
    abort_on_orphan_text(assert_complete_text_coverage(tokens, units))
    starts = set(units)
    for i, token in enumerate(tokens):
        if i in starts:
            add_key(keys, units[i][1])
        if token["type"] not in {"start", "startend"}:
            continue
        attrs = attrs_dict(token)
        for attr in ("alt", "aria-label"):
            value = attrs.get(attr)
            if value:
                add_key(keys, value)
        if token["tag"] == "meta":
            spec = ("name", attrs.get("name")) if attrs.get("name") else ("property", attrs.get("property"))
            if spec in TRANSLATABLE_META and attrs.get("content"):
                add_key(keys, attrs["content"])
        href = attrs.get("href")
        if href and "wa.me/" in href:
            msg = whatsapp_text(href)
            if msg:
                add_key(keys, msg)
    for key in jsonld_keys(tokens):
        add_key(keys, key)
    return keys


def jsonld_token_indexes(tokens: list[dict]) -> list[int]:
    indexes: list[int] = []
    for i, token in enumerate(tokens):
        if token["type"] == "start" and token["tag"] == "script":
            attrs = attrs_dict(token)
            if attrs.get("type") == "application/ld+json" and token.get("end"):
                for j in range(i + 1, token["end"]):
                    if tokens[j]["type"] == "data":
                        indexes.append(j)
    return indexes


def jsonld_keys(tokens: list[dict]) -> list[str]:
    keys: list[str] = []
    for idx in jsonld_token_indexes(tokens):
        data = json.loads(tokens[idx]["raw"])
        for item in data.get("@graph", []):
            if item.get("@type") == "Service":
                keys.extend([item.get("name", ""), item.get("description", "")])
            elif item.get("@type") == "FAQPage":
                for q in item.get("mainEntity", []):
                    keys.append(q.get("name", ""))
                    keys.append(q.get("acceptedAnswer", {}).get("text", ""))
    return keys


def load_translations(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def translate(key: str, lang: str, translations: dict, pending: list[str], missing: list[str]) -> str:
    if key not in translations:
        missing.append(key)
        return key
    value = translations[key].get(lang)
    if value is None:
        pending.append(key)
        return key
    if value == "=":
        return key
    if not isinstance(value, str):
        pending.append(key)
        return key
    return value


def apply_markers(value: str, markers: list[str]) -> str:
    def repl(match: re.Match[str]) -> str:
        idx = int(match.group(1))
        if idx >= len(markers):
            raise ValueError(f"marcador fuera de rango: {{{idx}}}")
        return markers[idx]
    return re.sub(r"\{(\d+)\}", repl, value)


def whatsapp_text(href: str) -> str | None:
    parts = urlsplit(href)
    if "wa.me" not in parts.netloc:
        return None
    params = dict(parse_qsl(parts.query, keep_blank_values=True))
    return params.get("text")


def replace_whatsapp_text(href: str, text: str) -> str:
    parts = urlsplit(href)
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    done = False
    out = []
    for key, value in pairs:
        if key == "text":
            out.append((key, text))
            done = True
        else:
            out.append((key, value))
    if not done:
        out.append(("text", text))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(out), parts.fragment))


def localized_url(lang: str, fragment: str = "") -> str:
    base = LANGS[lang]["url"]
    return base + fragment


def localize_absolute_url(value: str, lang: str) -> str:
    if not value.startswith(BASE + "/#"):
        return value
    return localized_url(lang, value.split("/", 3)[-1])


def localize_jsonld(raw: str, lang: str, translations: dict, pending: list[str], missing: list[str]) -> str:
    data = json.loads(raw)
    for item in data.get("@graph", []):
        for field in ("@id", "url"):
            if isinstance(item.get(field), str):
                item[field] = localize_absolute_url(item[field], lang)
        if item.get("@type") == "Organization":
            item["url"] = LANGS[lang]["url"]
            langs = item.get("knowsLanguage", [])
            for code in ("en", "it"):
                if code not in langs:
                    langs.append(code)
            item["knowsLanguage"] = langs
        if item.get("@type") == "WebSite":
            item["url"] = LANGS[lang]["url"]
            item["inLanguage"] = LANGS[lang]["html"]
        if item.get("@type") == "Service":
            item["name"] = translate(item["name"], lang, translations, pending, missing)
            item["description"] = translate(item["description"], lang, translations, pending, missing)
        if item.get("@type") == "FAQPage":
            item["inLanguage"] = LANGS[lang]["html"]
            for q in item.get("mainEntity", []):
                q["name"] = translate(q["name"], lang, translations, pending, missing)
                ans = q.get("acceptedAnswer", {})
                ans["text"] = translate(ans["text"], lang, translations, pending, missing)
    return json.dumps(data, ensure_ascii=False, indent=2)


def attrs_for_language(token: dict, lang: str, translations: dict, pending: list[str], missing: list[str]) -> list[tuple[str, str | None]] | None:
    attrs = list(token.get("attrs", []))
    ad = attrs_dict(token)
    changed = False
    if token["tag"] == "html":
        attrs = set_attr(attrs, "lang", LANGS[lang]["html"])
        changed = True
    if token["tag"] == "link" and ad.get("rel") == "canonical":
        attrs = set_attr(attrs, "href", LANGS[lang]["url"])
        changed = True
    if token["tag"] == "meta" and ad.get("property") == "og:url":
        attrs = set_attr(attrs, "content", LANGS[lang]["url"])
        changed = True
    if token["tag"] == "meta" and ad.get("property") == "og:locale":
        attrs = set_attr(attrs, "content", LANGS[lang]["locale"])
        changed = True
    if token["tag"] == "meta" and ad.get("property") == "og:locale:alternate":
        alternates = [info["locale"] for code, info in LANGS.items() if code != lang]
        idx = token.get("_alternate_locale_index", 0)
        attrs = set_attr(attrs, "content", alternates[idx])
        changed = True
    for attr in ("alt", "aria-label"):
        value = ad.get(attr)
        if value:
            attrs = set_attr(attrs, attr, translate(value, lang, translations, pending, missing))
            changed = True
    if token["tag"] == "meta":
        spec = ("name", ad.get("name")) if ad.get("name") else ("property", ad.get("property"))
        if spec in TRANSLATABLE_META and ad.get("content"):
            attrs = set_attr(attrs, "content", translate(ad["content"], lang, translations, pending, missing))
            changed = True
    if ad.get("href") and "wa.me/" in ad["href"]:
        text = whatsapp_text(ad["href"])
        if text:
            attrs = set_attr(attrs, "href", replace_whatsapp_text(ad["href"], translate(text, lang, translations, pending, missing)))
            changed = True
    if token["tag"] in {"a", "span"} and closest_lang_switch(token):
        code = visible_lang_code(token)
        if code:
            if code == lang.upper():
                attrs = [(k, v) for k, v in attrs if k.lower() not in {"href", "lang", "hreflang"}]
                attrs = set_attr(attrs, "aria-current", "true")
            else:
                attrs = [(k, v) for k, v in attrs if k.lower() != "aria-current"]
                attrs = set_attr(attrs, "href", "/" if code == "ES" else f"/{code.lower()}/")
                attrs = set_attr(attrs, "lang", "es" if code == "ES" else code.lower())
                attrs = set_attr(attrs, "hreflang", "es" if code == "ES" else code.lower())
            changed = True
    return attrs if changed else None


def visible_lang_code(token: dict) -> str | None:
    raw = token.get("_unit_key", "")
    text = re.sub(r"\{\d+\}", "", raw).strip()
    return text if text in {"ES", "EN", "IT"} else None


def closest_lang_switch(token: dict) -> bool:
    return bool(token.get("_in_lang_switch"))


def annotate_lang_switch(tokens: list[dict]) -> None:
    stack: list[bool] = []
    for token in tokens:
        if token["type"] == "start":
            cls = attrs_dict(token).get("class") or ""
            in_switch = (stack[-1] if stack else False) or "lang-switch" in cls.split()
            token["_in_lang_switch"] = in_switch
            stack.append(in_switch)
        elif token["type"] == "end" and stack:
            stack.pop()
        else:
            token["_in_lang_switch"] = stack[-1] if stack else False


def render_language(tokens: list[dict], lang: str, translations: dict) -> tuple[str, list[str], list[str]]:
    annotate_lang_switch(tokens)
    annotate_locale_alternates(tokens)
    units = discover_units(tokens)
    for start, (_end, key, _markers) in units.items():
        tokens[start]["_unit_key"] = key
    pending: list[str] = []
    missing: list[str] = []
    out: list[str] = []
    skip_until = -1
    for i, token in enumerate(tokens):
        if i <= skip_until:
            continue
        if token["type"] == "start" and token["tag"] == "div" and "lang-switch" in (attrs_dict(token).get("class") or "").split():
            attrs = attrs_for_language(token, lang, translations, pending, missing)
            out.append(render_token(token, attrs))
            out.append(lang_switch_html(lang))
            out.append(tokens[token["end"]]["raw"])
            skip_until = token["end"]
            continue
        if i in units:
            end, key, markers = units[i]
            attrs = attrs_for_language(token, lang, translations, pending, missing)
            out.append(render_token(token, attrs))
            translated = translate(key, lang, translations, pending, missing)
            out.append(apply_markers(translated, markers))
            out.append(tokens[end]["raw"])
            skip_until = end
            continue
        if token["type"] in {"start", "startend"}:
            attrs = attrs_for_language(token, lang, translations, pending, missing)
            out.append(render_token(token, attrs))
        elif i in jsonld_token_indexes(tokens):
            out.append(localize_jsonld(token["raw"], lang, translations, pending, missing))
        else:
            out.append(token["raw"])
    return "".join(out), pending, missing


def annotate_locale_alternates(tokens: list[dict]) -> None:
    idx = 0
    for token in tokens:
        if token["type"] in {"start", "startend"} and token["tag"] == "meta":
            if attrs_dict(token).get("property") == "og:locale:alternate":
                token["_alternate_locale_index"] = idx
                idx += 1


def lang_switch_html(active: str) -> str:
    parts = []
    for code in ("ES", "EN", "IT"):
        lang = code.lower()
        if lang == active:
            parts.append(f'<span aria-current="true">{code}</span>')
        else:
            href = "/" if code == "ES" else f"/{lang}/"
            parts.append(f'<a href="{href}" lang="{lang}" hreflang="{lang}">{code}</a>')
    return "".join(parts)


def write_census(tokens: list[dict], path: Path) -> None:
    keys = collect_keys(tokens)
    old = load_translations(path) if path.exists() else {}
    data = OrderedDict()
    for key in keys:
        if key in old:
            data[key] = old[key]
        else:
            value = "=" if key in PROPER_EQUAL else None
            data[key] = {"en": value, "it": value}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{path}: {len(data)} claves")


def build(translations_path: Path, out_root: Path) -> int:
    tokens = parse_html(SOURCE.read_text(encoding="utf-8"))
    units = discover_units(tokens)
    abort_on_orphan_text(assert_complete_text_coverage(tokens, units))
    translations = load_translations(translations_path)
    had_errors = False
    for lang in ("en", "it"):
        rendered, pending, missing = render_language(tokens, lang, translations)
        if missing or pending:
            had_errors = True
            print(f"{lang}: build abortado", file=sys.stderr)
            if missing:
                print("claves ausentes:", file=sys.stderr)
                for key in sorted(set(missing)):
                    print(f"- {key}", file=sys.stderr)
            if pending:
                print("claves pendientes:", file=sys.stderr)
                for key in sorted(set(pending)):
                    print(f"- {key}", file=sys.stderr)
    if had_errors:
        return 1
    for lang in ("en", "it"):
        rendered, _pending, _missing = render_language(tokens, lang, translations)
        folder = out_root / lang
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(rendered, encoding="utf-8")
        print(f"escrito {folder / 'index.html'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--translations", type=Path, default=TRANSLATIONS)
    ap.add_argument("--out-root", type=Path, default=ROOT)
    args = ap.parse_args()
    tokens = parse_html(SOURCE.read_text(encoding="utf-8"))
    if args.extract:
        write_census(tokens, args.translations)
        return 0
    return build(args.translations, args.out_root)


if __name__ == "__main__":
    raise SystemExit(main())
