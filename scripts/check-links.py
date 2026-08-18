#!/usr/bin/env python3
"""Check that every local (root-relative or relative) URL in built HTML resolves to a real file."""
import os
import re
import sys
from urllib.parse import urlparse

ROOT = sys.argv[1] if len(sys.argv) > 1 else "public"
BASE = sys.argv[2] if len(sys.argv) > 2 else "/algorithmica"
SKIP_DIRS = ("reveal-js",)

ATTR_RE = re.compile(r"""(?:href|src|action|poster|data-src)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""")
META_RE = re.compile(r"""<meta\s+http-equiv=["']?refresh["']?[^>]*url=([^"'>\s]+)""")
SCRIPT_RE = re.compile(r"<script.*?</script>", re.DOTALL)
STYLE_RE = re.compile(r"<style.*?</style>", re.DOTALL)

SKIP_SCHEMES = ("http:", "https:", "mailto:", "javascript:", "tel:", "data:", "blob:", "ftp:")

errors = 0
checked = 0
seen = set()


def resolve_local(url, page_dir):
    if url.startswith("//"):
        return None  # protocol-relative, external
    path = urlparse(url).path
    if not path or path.startswith("#"):
        return None
    if path.startswith(BASE):
        path = path[len(BASE):]
        full = os.path.normpath(os.path.join(ROOT, path.lstrip("/")))
    elif path.startswith("/"):
        return None  # unexpected root-relative not under base path
    else:
        full = os.path.normpath(os.path.join(page_dir, path))
    return full


def check(target, page_file, what):
    global errors, checked
    if not target:
        return
    if target in seen:
        return
    seen.add(target)
    checked += 1
    if os.path.isdir(target):
        target = os.path.join(target, "index.html")
    if not os.path.isfile(target):
        errors += 1
        print(f"MISSING {what}: {target}  (referenced from {page_file})")


for dirpath, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for name in files:
        if not name.endswith(".html"):
            continue
        page = os.path.join(dirpath, name)
        try:
            text = open(page, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        text = SCRIPT_RE.sub("", text)
        text = STYLE_RE.sub("", text)
        for match in ATTR_RE.finditer(text):
            url = next((g for g in match.groups() if g), "")
            if not url or url.startswith(SKIP_SCHEMES) or url.startswith(("//", "#")):
                continue
            target = resolve_local(url, dirpath)
            if target:
                check(target, page, url)
        for match in META_RE.finditer(text):
            url = match.group(1)
            if url and not url.startswith(("http", "//")):
                target = resolve_local(url, dirpath)
                if target:
                    check(target, page, url)

print(f"checked {checked} unique local URLs, {errors} missing")
sys.exit(1 if errors else 0)