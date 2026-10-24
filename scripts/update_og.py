#!/usr/bin/env python3
"""Update og.png and HTML meta tags to match the current seasonal theme."""
import os, re, shutil, time
from datetime import datetime

THEMES = {
    'halloween':    {'title': 'Ghoulish Jawn',  'desc': 'Fresh frights, ready to watch. Made with love in Philadelphia.'},
    'thanksgiving': {'title': 'Gobbler Jawn',   'desc': 'Fresh downloads, ready to watch. Made with love in Philadelphia.'},
    'christmas':    {'title': 'Fat Santa Jawn', 'desc': 'Fresh downloads, ready to watch. Made with love in Philadelphia.'},
    'default':      {'title': 'Popcorn Jawn',   'desc': 'Fresh downloads, ready to watch. Made with love in Philadelphia.'},
}

def detect_theme():
    now = datetime.now()
    m, d = now.month, now.day
    if m == 10: return 'halloween'
    if m == 11: return 'thanksgiving'
    if m == 12 or (m == 1 and d <= 7): return 'christmas'
    return 'default'

public = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public')
index  = os.path.join(public, 'index.html')
theme  = detect_theme()
meta   = THEMES[theme]
ver    = int(time.time())

# Update og.png
src = os.path.join(public, f'og-{theme}.png')
if os.path.exists(src):
    shutil.copy2(src, os.path.join(public, 'og.png'))

# Rewrite index.html meta tags
html = open(index).read()

img_url = f'https://popcorn.jawnhaas.xyz/og-{theme}.png?v={ver}'

html = re.sub(r'<title>[^<]*</title>', f'<title>{meta["title"]}</title>', html)
html = re.sub(r'(<meta property="og:title" content=")[^"]*(")', rf'\g<1>{meta["title"]}\2', html)
html = re.sub(r'(<meta property="og:description" content=")[^"]*(")', rf'\g<1>{meta["desc"]}\2', html)
html = re.sub(r'(<meta property="og:image" content=")[^"]*(")', rf'\g<1>{img_url}\2', html)
html = re.sub(r'(<meta name="twitter:image" content=")[^"]*(")', rf'\g<1>{img_url}\2', html)

open(index, 'w').write(html)
print(f'Theme: {theme} | title: {meta["title"]} | image: {img_url}')
