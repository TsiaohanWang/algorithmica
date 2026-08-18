#!/usr/bin/env python3
"""Rewrite root-relative URLs in the built site to work under a GitHub Pages subpath.

Pass 1 (all html/js/css/xml): prefix bare root-relative URLs (e.g. /hpc/...)
with the base path (/algorithmica), skipping protocol-relative (//) and
already-prefixed URLs.

Pass 2 (html under language dirs en/ru/zh): insert the language into
unresolved content links (e.g. /algorithmica/cs/... -> /algorithmica/ru/cs/...)
when that page exists for the page's language (falling back to ru, which has
the full content tree).
"""
import os
import re

ROOT = os.environ.get("PUBLIC_DIR", "public")
BASE = os.environ.get("BASE_PATH", "/algorithmica")
LANGS = ("en", "ru", "zh")

ATTR_RE = re.compile(r"""\b(href|src|action|poster|data-src)\s*=\s*("([^"]*)"|'([^']*)'|([^\s>]+))""")


def url_of(m):
    return next((g for g in m.groups()[2:] if g), "")


def target_exists(path_part, lang):
    p = os.path.join(ROOT, lang, path_part)
    return os.path.isdir(p) or os.path.isfile(p)


def rewrite_file(path, page_lang):
    with open(path, encoding="utf-8") as f:
        text = f.read()

    def repl(m):
        url = url_of(m)
        if not url.startswith("/"):
            return m.group(0)
        if url.startswith("//") or url.startswith(BASE + "/"):
            return m.group(0)
        clean = url.split("#", 1)[0].split("?", 1)[0]
        path_part = clean.lstrip("/")
        if not path_part:
            return m.group(0)
        if page_lang and path_part.split("/", 1)[0] not in LANGS:
            for lang in (page_lang, *[l for l in LANGS if l != page_lang]):
                if target_exists(path_part, lang):
                    return m.group(0).replace(url, f"{BASE}/{lang}/{path_part}")
        return m.group(0).replace(url, f"{BASE}/{path_part}")

    out = ATTR_RE.sub(repl, text)
    if out != text:
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)


def main():
    for dirpath, _dirs, files in os.walk(ROOT):
        for name in files:
            if not name.endswith((".html", ".js", ".css", ".xml")):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, ROOT)
            page_lang = rel.split(os.sep, 1)[0] if os.sep in rel else None
            rewrite_file(path, page_lang if page_lang in LANGS else None)


if __name__ == "__main__":
    main()