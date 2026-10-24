#!/usr/bin/env python3
"""Update og.png and HTML meta tags to match the current seasonal theme."""
import json, os, re, shutil, time
from datetime import datetime
from pathlib import Path

_dir = Path(__file__).parent
_root = _dir.parent
THEMES_JSON = _root / "themes.json"

themes = json.loads(THEMES_JSON.read_text())


def detect_theme():
    now = datetime.now()
    m, d = now.month, now.day
    for key, t in themes.items():
        r = t.get("range")
        if not r:
            continue
        sm, sd = (int(x) for x in r["start"].split("-"))
        em, ed = (int(x) for x in r["end"].split("-"))
        if sm > em:  # year-wrap (e.g. Dec–Jan)
            if (m == sm and d >= sd) or m > sm or m < em or (m == em and d <= ed):
                return key
        else:
            if (m > sm or (m == sm and d >= sd)) and (m < em or (m == em and d <= ed)):
                return key
    return "default"


public = _root / "public"
index = public / "index.html"
theme = detect_theme()
meta = themes[theme]
ver = int(time.time())

# Update og.png
src = public / f"og-{theme}.png"
if src.exists():
    shutil.copy2(src, public / "og.png")

# Rewrite index.html meta tags
html = index.read_text()
img_url = f"https://popcorn.jawnhaas.xyz/og-{theme}.png?v={ver}"
title = meta["title"]
desc = "Fresh downloads, ready to watch. Made with love in Philadelphia."

html = re.sub(r"<title>[^<]*</title>", f"<title>{title}</title>", html)
html = re.sub(r'(<meta property="og:title" content=")[^"]*(")', rf"\g<1>{title}\2", html)
html = re.sub(r'(<meta property="og:description" content=")[^"]*(")', rf"\g<1>{desc}\2", html)
html = re.sub(r'(<meta property="og:image" content=")[^"]*(")', rf"\g<1>{img_url}\2", html)
html = re.sub(r'(<meta name="twitter:image" content=")[^"]*(")', rf"\g<1>{img_url}\2", html)

index.write_text(html)
print(f"Theme: {theme} | title: {title} | image: {img_url}")
