#!/usr/bin/env python3
"""Generate OG images and update the THEMES JS block in index.html from themes.json.

Usage: python3 generate_themes.py
To add a new theme: edit themes.json, add an og.style handler below if needed, re-run.
"""
import json, os, re, random, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

_dir = Path(__file__).parent
_root = _dir.parent
THEMES_JSON = _root / "themes.json"
INDEX_HTML = _root / "public" / "index.html"
PUBLIC = _root / "public"
FONT_PATH = "/usr/share/fonts/truetype/nunito-sans/NunitoSans-VariableFont_YTLC,opsz,wdth,wght.ttf"

W, H = 1200, 630


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def draw_stripes_and_drips(draw, stripe_a, stripe_b, seed=42):
    rng = random.Random(seed)
    stripe_w = 18
    for x in range(0, W, stripe_w):
        color = stripe_a if (x // stripe_w) % 2 == 0 else stripe_b
        draw.rectangle([x, 0, x + stripe_w - 1, 28], fill=color)
        draw.rectangle([x, H - 28, x + stripe_w - 1, H - 1], fill=color)

    # drips from top stripe
    for _ in range(18):
        dx = rng.randint(10, W - 10)
        dlen = rng.randint(18, 60)
        dw = rng.randint(4, 10)
        r = hex_to_rgb(stripe_a) if isinstance(stripe_a, str) else stripe_a
        draw.ellipse([dx - dw, 28 + dlen - dw, dx + dw, 28 + dlen + dw], fill=r)
        draw.rectangle([dx - dw//2, 28, dx + dw//2, 28 + dlen], fill=r)

    # drips from bottom stripe (upward)
    for _ in range(18):
        dx = rng.randint(10, W - 10)
        dlen = rng.randint(18, 60)
        dw = rng.randint(4, 10)
        r = hex_to_rgb(stripe_b) if isinstance(stripe_b, str) else stripe_b
        draw.ellipse([dx - dw, H - 28 - dlen - dw, dx + dw, H - 28 - dlen + dw], fill=r)
        draw.rectangle([dx - dw//2, H - 28 - dlen, dx + dw//2, H - 28], fill=r)


def draw_glow_bg(img, bg, glow_top, glow_bottom):
    bg_img = Image.new("RGB", (W, H), tuple(bg))
    gt = Image.new("RGB", (W, H), tuple(glow_top))
    gb = Image.new("RGB", (W, H), tuple(glow_bottom))
    # radial mask for top glow
    mask_top = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask_top)
    for r in range(320, 0, -1):
        alpha = int(180 * (1 - r / 320))
        md.ellipse([W//2 - r, -r, W//2 + r, r], fill=alpha)
    # flat gradient for bottom tint
    mask_bot = Image.new("L", (W, H), 0)
    md2 = ImageDraw.Draw(mask_bot)
    for y in range(H):
        alpha = int(100 * (y / H))
        md2.line([(0, y), (W, y)], fill=alpha)
    bg_img.paste(gt, mask=mask_top)
    bg_img.paste(gb, mask=mask_bot)
    img.paste(bg_img)


def draw_halloween(draw, og):
    acc = tuple(og["accentRGB"])
    dark = hex_to_rgb(og["accentDarkHex"])
    # bats in corners
    for bx, by in [(80, 80), (W-80, 80), (80, H-80), (W-80, H-80)]:
        draw.ellipse([bx-12, by-8, bx+12, by+8], fill=(30, 10, 30))
        draw.ellipse([bx-28, by-4, bx-10, by+10], fill=(30, 10, 30))
        draw.ellipse([bx+10, by-4, bx+28, by+10], fill=(30, 10, 30))
    # pumpkins on sides
    for px, py in [(120, H//2), (W-120, H//2)]:
        draw.ellipse([px-30, py-25, px+30, py+25], fill=acc)
        draw.rectangle([px-4, py-35, px+4, py-25], fill=(34, 85, 34))
        draw.line([(px-15, py-5), (px-5, py+5), (px+5, py-5), (px+15, py+5)], fill=(30,10,0), width=3)
    # spider webs in corners
    for wx, wy in [(0, 0), (W, 0)]:
        for ang in range(0, 90, 15):
            r = math.radians(ang)
            ex = wx + (1 if wx == 0 else -1) * int(80 * math.cos(r))
            ey = wy + int(80 * math.sin(r))
            draw.line([(wx, wy), (ex, ey)], fill=(180, 180, 180, 120), width=1)
        for rad in [25, 50, 75]:
            draw.arc([wx - rad, wy - rad, wx + rad, wy + rad], 0, 90, fill=(180, 180, 180, 80), width=1)
    # popcorn bucket center top
    cx, cy = W//2, 110
    draw.rectangle([cx-35, cy, cx+35, cy+55], fill=(220, 50, 50))
    for i in range(0, 70, 12):
        draw.rectangle([cx-35+i, cy, cx-35+i+6, cy+55], fill=(255, 255, 255))
    draw.rectangle([cx-38, cy-8, cx+38, cy+5], fill=dark)
    for ox, oy in [(-20, -12), (0, -18), (20, -12), (-10, -22), (10, -22)]:
        draw.ellipse([cx+ox-10, cy+oy-10, cx+ox+10, cy+oy+10], fill=(255, 235, 150))


def draw_thanksgiving(draw, og):
    acc = tuple(og["accentRGB"])
    cx, cy = W//2, 110
    # rainbow feather fan
    feather_colors = [(220,38,38),(249,115,22),(234,179,8),(34,197,94),(59,130,246),(168,85,247),(236,72,153)]
    for i, fc in enumerate(feather_colors):
        ang = math.radians(200 + i * 20)
        ex = cx + int(90 * math.cos(ang))
        ey = cy + int(90 * math.sin(ang))
        draw.line([(cx, cy+10), (ex, ey)], fill=fc, width=8)
        draw.ellipse([ex-10, ey-14, ex+10, ey+14], fill=fc)
    # turkey body
    draw.ellipse([cx-28, cy-10, cx+28, cy+45], fill=(139,90,43))
    draw.ellipse([cx-16, cy-28, cx+16, cy+2], fill=(180,120,60))
    draw.ellipse([cx-8, cy-26, cx+8, cy-12], fill=(230,180,100))
    draw.ellipse([cx-6, cy-32, cx+6, cy-22], fill=(220,50,50))
    draw.ellipse([cx+4, cy-28, cx+12, cy-20], fill=(255,200,0))
    # scattered leaf diamonds
    rng = random.Random(42)
    leaf_colors = [(217,119,6),(180,83,9),(234,179,8),(161,98,7)]
    for _ in range(8):
        lx = rng.randint(100, W-100)
        ly = rng.randint(80, H-80)
        lc = leaf_colors[rng.randint(0, 3)]
        ang = rng.uniform(0, math.pi)
        pts = [
            (lx + int(20*math.cos(ang)), ly + int(20*math.sin(ang))),
            (lx + int(10*math.cos(ang+math.pi/2)), ly + int(10*math.sin(ang+math.pi/2))),
            (lx - int(20*math.cos(ang)), ly - int(20*math.sin(ang))),
            (lx - int(10*math.cos(ang+math.pi/2)), ly - int(10*math.sin(ang+math.pi/2))),
        ]
        draw.polygon(pts, fill=lc)


def draw_christmas(draw, og):
    acc = tuple(og["accentRGB"])
    dark = hex_to_rgb(og["accentDarkHex"])
    cx, cy = W//2, 60
    # christmas tree (layered triangles)
    tree_layers = [(30, 0), (44, 28), (58, 56), (72, 84)]
    for i, (hw, yo) in enumerate(tree_layers):
        draw.polygon([(cx, cy+yo-10), (cx-hw, cy+yo+30), (cx+hw, cy+yo+30)], fill=acc)
    # trunk
    draw.rectangle([cx-10, cy+112, cx+10, cy+130], fill=(139,90,43))
    # star at top
    for ang in range(0, 360, 72):
        r = math.radians(ang - 90)
        sx = cx + int(14*math.cos(r))
        sy = (cy-10) + int(14*math.sin(r))
        r2 = math.radians(ang - 90 + 36)
        sx2 = cx + int(6*math.cos(r2))
        sy2 = (cy-10) + int(6*math.sin(r2))
        draw.line([(sx, sy), (sx2, sy2)], fill=(255,220,0), width=3)
    draw.ellipse([cx-6, cy-16, cx+6, cy-4], fill=(255,220,0))
    # ornament dots
    ornament_colors = [(220,38,38),(59,130,246),(255,220,0),(168,85,247),(249,115,22)]
    rng = random.Random(42)
    for i in range(12):
        oc = ornament_colors[i % len(ornament_colors)]
        ox = rng.randint(cx-70, cx+70)
        oy = rng.randint(cy+10, cy+110)
        draw.ellipse([ox-6, oy-6, ox+6, oy+6], fill=oc)
    # scattered snowflakes
    for _ in range(18):
        sx = rng.randint(50, W-50)
        sy = rng.randint(50, H-50)
        for ang in range(0, 360, 60):
            r = math.radians(ang)
            draw.line([(sx, sy), (sx+int(10*math.cos(r)), sy+int(10*math.sin(r)))], fill=(200,230,255), width=1)


def draw_hanukkah(draw, og):
    gold = (200, 168, 75)
    blue = (0, 56, 184)
    cream = (255, 250, 220)
    orange = (255, 160, 40)
    cx, cy = W // 2, 60

    # Menorah base: horizontal bar + vertical stem
    bar_y = cy + 105
    draw.rectangle([cx - 80, bar_y, cx + 80, bar_y + 10], fill=gold)
    draw.rectangle([cx - 6, cy + 70, cx + 6, bar_y], fill=gold)

    # 9 candle positions: 8 regular + 1 tall shamash in center (index 4)
    positions = list(range(-4, 5))  # -4 to 4
    arm_y = cy + 72
    for i, offset in enumerate(positions):
        candle_x = cx + offset * 18
        is_shamash = (offset == 0)
        arm_top = arm_y - (14 if is_shamash else 0)

        # Arm from stem to candle (horizontal + vertical)
        if offset != 0:
            mid_x = cx if offset < 0 else cx
            draw.line([(cx, arm_y), (candle_x, arm_y)], fill=gold, width=3)
            draw.line([(candle_x, arm_y), (candle_x, arm_top)], fill=gold, width=3)

        # Candle holder cup
        draw.rectangle([candle_x - 4, arm_top - 4, candle_x + 4, arm_top + 4], fill=gold)

        # Candle body
        candle_h = 28 if is_shamash else 22
        draw.rectangle([candle_x - 4, arm_top - 4 - candle_h, candle_x + 4, arm_top - 4], fill=cream)

        # Flame
        flame_base_y = arm_top - 4 - candle_h
        draw.ellipse([candle_x - 5, flame_base_y - 14, candle_x + 5, flame_base_y + 2], fill=orange)
        draw.ellipse([candle_x - 3, flame_base_y - 10, candle_x + 3, flame_base_y], fill=(255, 220, 80))

    # 8 small Stars of David scattered on sides
    rng = random.Random(42)
    star_positions = [
        (110, 120), (110, 280), (110, 440), (110, H - 100),
        (W - 110, 120), (W - 110, 280), (W - 110, 440), (W - 110, H - 100),
    ]
    for sx, sy in star_positions:
        r = 14
        # Two overlapping triangles
        for rot in [0, 60]:
            pts = []
            for ang in [90, 210, 330]:
                a = math.radians(ang + rot)
                pts.append((sx + int(r * math.cos(a)), sy + int(r * math.sin(a))))
            draw.polygon(pts, outline=gold, fill=None)


def draw_newyears(draw, og):
    gold = (212, 175, 55)
    silver = (192, 192, 192)
    cx, cy = W // 2, 110

    # Fireworks bursts at 3 points
    burst_centers = [(cx - 200, cy - 20), (cx + 200, cy - 30), (cx, cy - 50)]
    burst_colors = [gold, silver, gold]
    rng = random.Random(7)
    for (bx, by), bc in zip(burst_centers, burst_colors):
        for ang in range(0, 360, 18):
            r = math.radians(ang)
            length = rng.randint(28, 55)
            ex = bx + int(length * math.cos(r))
            ey = by + int(length * math.sin(r))
            draw.line([(bx, by), (ex, ey)], fill=bc, width=2)
            draw.ellipse([ex - 3, ey - 3, ex + 3, ey + 3], fill=bc)

    # Champagne glass at center
    gx, gy = cx, cy - 10
    # bowl (two lines forming a V-shape widened at top)
    bowl_pts = [(gx - 22, gy - 30), (gx + 22, gy - 30), (gx + 8, gy + 10), (gx - 8, gy + 10)]
    draw.polygon(bowl_pts, outline=gold, fill=None)
    # stem
    draw.line([(gx, gy + 10), (gx, gy + 40)], fill=gold, width=3)
    # base
    draw.line([(gx - 18, gy + 40), (gx + 18, gy + 40)], fill=gold, width=3)
    # bubbles
    for bub_x, bub_y in [(gx - 8, gy - 10), (gx, gy - 18), (gx + 8, gy - 8)]:
        draw.ellipse([bub_x - 3, bub_y - 3, bub_x + 3, bub_y + 3], outline=gold)

    # Scattered sparkle stars
    rng2 = random.Random(42)
    for _ in range(20):
        sx = rng2.randint(80, W - 80)
        sy = rng2.randint(60, H - 60)
        sc = gold if rng2.random() > 0.4 else silver
        for ang in [0, 45, 90, 135]:
            r = math.radians(ang)
            sz = rng2.randint(6, 14)
            draw.line([(sx - int(sz * math.cos(r)), sy - int(sz * math.sin(r))),
                       (sx + int(sz * math.cos(r)), sy + int(sz * math.sin(r)))], fill=sc, width=2)


def draw_ramadan(draw, og):
    teal = (0, 184, 148)
    gold = (212, 175, 55)
    cx, cy = W // 2, 85

    # Crescent moon: large circle minus offset circle
    moon_r = 48
    # Draw the full circle in gold
    draw.ellipse([cx - moon_r, cy - moon_r, cx + moon_r, cy + moon_r], fill=gold)
    # Mask it with bg color circle offset to right to create crescent
    bg = tuple(og["bgColor"])
    offset = 34
    draw.ellipse([cx - moon_r + offset, cy - moon_r + 4,
                  cx + moon_r + offset, cy + moon_r + 4], fill=bg)

    # Small star inside the crescent (upper right of moon)
    sx, sy = cx + 38, cy - 22
    star_r = 10
    star_pts = []
    for i in range(5):
        outer_a = math.radians(i * 72 - 90)
        inner_a = math.radians(i * 72 - 90 + 36)
        star_pts.append((sx + int(star_r * math.cos(outer_a)), sy + int(star_r * math.sin(outer_a))))
        star_pts.append((sx + int(star_r * 0.4 * math.cos(inner_a)), sy + int(star_r * 0.4 * math.sin(inner_a))))
    draw.polygon(star_pts, fill=teal)

    # Simple lantern below the moon
    lx, ly = cx, cy + 85
    draw.rectangle([lx - 18, ly - 30, lx + 18, ly + 30], fill=teal, outline=gold, width=2)
    # Pointed top
    draw.polygon([(lx - 18, ly - 30), (lx + 18, ly - 30), (lx, ly - 50)], fill=teal, outline=gold, width=2)
    # Horizontal lines (panes)
    for offset in [-15, 0, 15]:
        draw.line([(lx - 18, ly + offset), (lx + 18, ly + offset)], fill=gold, width=1)
    # Vertical center line
    draw.line([(lx, ly - 30), (lx, ly + 30)], fill=gold, width=1)
    # Handle at top
    draw.line([(lx, ly - 50), (lx, ly - 60)], fill=gold, width=2)
    draw.arc([lx - 8, ly - 68, lx + 8, ly - 52], 180, 0, fill=gold, width=2)

    # Scattered 5-pointed stars on sides
    star_positions = [
        (110, 130), (110, 260), (110, 390), (110, H - 120),
        (W - 110, 130), (W - 110, 260), (W - 110, 390), (W - 110, H - 120),
    ]
    for spx, spy in star_positions:
        r = 12
        pts = []
        for i in range(5):
            oa = math.radians(i * 72 - 90)
            ia = math.radians(i * 72 - 90 + 36)
            pts.append((spx + int(r * math.cos(oa)), spy + int(r * math.sin(oa))))
            pts.append((spx + int(r * 0.4 * math.cos(ia)), spy + int(r * 0.4 * math.sin(ia))))
        draw.polygon(pts, fill=teal)


def draw_default(draw, og):
    acc = tuple(og["accentRGB"])
    cx, cy = W//2, 110
    # popcorn bucket
    draw.rectangle([cx-35, cy, cx+35, cy+55], fill=(220, 50, 50))
    for i in range(0, 70, 12):
        draw.rectangle([cx-35+i, cy, cx-35+i+6, cy+55], fill=(255, 255, 255))
    draw.rectangle([cx-38, cy-8, cx+38, cy+5], fill=hex_to_rgb(og["accentDarkHex"]))
    for ox, oy in [(-20, -12), (0, -18), (20, -12), (-10, -22), (10, -22)]:
        draw.ellipse([cx+ox-10, cy+oy-10, cx+ox+10, cy+oy+10], fill=(255, 235, 150))
    # film reel shapes in corners
    for fx, fy in [(100, 130), (W-100, 130), (100, H-130), (W-100, H-130)]:
        draw.ellipse([fx-22, fy-22, fx+22, fy+22], fill=(40, 40, 60))
        draw.ellipse([fx-14, fy-14, fx+14, fy+14], fill=(60, 60, 80))
        draw.ellipse([fx-5, fy-5, fx+5, fy+5], fill=(20, 20, 40))
        for ang in range(0, 360, 60):
            r = math.radians(ang)
            draw.ellipse([fx+int(9*math.cos(r))-4, fy+int(9*math.sin(r))-4,
                          fx+int(9*math.cos(r))+4, fy+int(9*math.sin(r))+4], fill=(20, 20, 40))


STYLE_DRAWERS = {
    "halloween": draw_halloween,
    "thanksgiving": draw_thanksgiving,
    "ramadan": draw_ramadan,
    "hanukkah": draw_hanukkah,
    "newyears": draw_newyears,
    "christmas": draw_christmas,
    "default": draw_default,
}


def generate_og(key, theme):
    og = theme["og"]
    img = Image.new("RGB", (W, H), tuple(og["bgColor"]))
    draw_glow_bg(img, og["bgColor"], og["glowTop"], og["glowBottom"])
    draw = ImageDraw.Draw(img)

    stripe_a = hex_to_rgb(og["stripeA"]) if og["stripeA"].startswith("#") else og["stripeA"]
    stripe_b = hex_to_rgb(og["stripeB"]) if og["stripeB"].startswith("#") else og["stripeB"]
    draw_stripes_and_drips(draw, stripe_a, stripe_b)

    style_fn = STYLE_DRAWERS.get(og["style"])
    if style_fn:
        style_fn(draw, og)

    try:
        font_title = ImageFont.truetype(FONT_PATH, 110)
        font_tag   = ImageFont.truetype(FONT_PATH, 28)
        font_sub   = ImageFont.truetype(FONT_PATH, 28)
    except Exception:
        font_title = font_tag = font_sub = ImageFont.load_default()

    title_color = tuple(og["titleColor"])
    tag_color   = tuple(og["tagColor"])
    sub_color   = tuple(og["subColor"])

    # Title centered
    bbox = draw.textbbox((0, 0), theme["title"], font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, 240), theme["title"], font=font_title, fill=title_color)

    # Tagline
    tagline = "Fresh downloads, ready to watch."
    bbox2 = draw.textbbox((0, 0), tagline, font=font_tag)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((W - tw2) // 2, 380), tagline, font=font_tag, fill=tag_color)

    # Sub
    sub = og["sub"]
    bbox3 = draw.textbbox((0, 0), sub, font=font_sub)
    tw3 = bbox3[2] - bbox3[0]
    draw.text(((W - tw3) // 2, 430), sub, font=font_sub, fill=sub_color)

    out = PUBLIC / f"og-{key}.png"
    img.save(out, "PNG")
    print(f"  Generated {out.name}")


def parse_range(r):
    if r is None:
        return "null"
    sm, sd = (int(x) for x in r["start"].split("-"))
    em, ed = (int(x) for x in r["end"].split("-"))
    return f"[[{sm},{sd}],[{em},{ed}]]"


def js_string(s):
    return json.dumps(s, ensure_ascii=False)


def generate_themes_js(themes):
    lines = [
        "    // THEMES_START (auto-generated from themes.json — edit themes.json, not this block)",
        "    const THEMES = {",
    ]
    for key, t in themes.items():
        r = parse_range(t.get("range"))
        em = t["emoji"]
        css_str = json.dumps(t["css"], ensure_ascii=False)
        dp_str = json.dumps(t["deleteParticles"], ensure_ascii=False)
        floater = "null" if t["floater"] is None else js_string(t["floater"])
        lines.append(f"      {key}: {{")
        lines.append(f"        range: {r},")
        lines.append(f"        title: {js_string(t['title'])},")
        lines.append(f"        headerEmoji: {js_string(em['header'])},")
        lines.append(f"        taglineEmojiL: {js_string(em['taglineL'])}, taglineEmojiR: {js_string(em['taglineR'])},")
        lines.append(f"        tagline: {js_string(t['tagline'])},")
        lines.append(f"        summonEmojiL: {js_string(em['summonL'])}, summonEmojiR: {js_string(em['summonR'])},")
        lines.append(f"        summonLabel: {js_string(t['summonLabel'])},")
        lines.append(f"        emptyEmoji: {js_string(t['emptyEmoji'])}, emptyTitle: {js_string(t['emptyTitle'])}, emptySub: {js_string(t['emptySub'])},")
        lines.append(f"        pastEmojiL: {js_string(em['pastL'])}, pastEmojiR: {js_string(em['pastR'])}, pastLabel: 'Past Showings',")
        lines.append(f"        footerText: {js_string(t['footerText'])}, footerTextColor: {js_string(t['footerTextColor'])},")
        lines.append(f"        og: 'og-{key}.png',")
        lines.append(f"        css: {css_str},")
        fe_str = json.dumps(t.get("floaterEmoji", []), ensure_ascii=False)
        lines.append(f"        floater: {floater},")
        lines.append(f"        floaterEmoji: {fe_str},")
        lines.append(f"        deleteParticles: {dp_str},")
        lines.append(f"      }},")
    lines.append("    };")
    lines.append("    // THEMES_END")
    return "\n".join(lines)


def update_index_html(themes_js):
    html = INDEX_HTML.read_text()

    # Try marked region first
    marked = re.search(r'// THEMES_START.*?// THEMES_END', html, re.DOTALL)
    if marked:
        html = html[:marked.start()] + themes_js + html[marked.end():]
        INDEX_HTML.write_text(html)
        print("  Updated THEMES block (marked region)")
        return

    # Fall back: find `const THEMES = {` and matching `};`
    start_m = re.search(r'    const THEMES = \{', html)
    if not start_m:
        print("  WARNING: could not find THEMES block in index.html")
        return

    # Walk forward to find the closing `};` at indentation level 0 (4 spaces)
    search_from = start_m.end()
    depth = 1
    pos = search_from
    while pos < len(html) and depth > 0:
        c = html[pos]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        pos += 1
    # pos is now just after the closing }
    # find the `;` immediately after
    semi = html.index(';', pos - 1)
    end_pos = semi + 1
    html = html[:start_m.start()] + themes_js + html[end_pos:]
    INDEX_HTML.write_text(html)
    print("  Updated THEMES block (first-run replacement)")


def main():
    themes = json.loads(THEMES_JSON.read_text())

    print("Generating OG images...")
    for key, theme in themes.items():
        generate_og(key, theme)

    print("Updating index.html THEMES block...")
    js = generate_themes_js(themes)
    update_index_html(js)

    print("Done.")
    print("\nTo add a new theme:")
    print("  1. Add an entry to themes.json")
    print("  2. Add a draw_<style> function to this script if it's a new style")
    print("  3. Re-run: python3 scripts/generate_themes.py")


if __name__ == "__main__":
    main()
