#!/usr/bin/env python3
"""Hustle Mate social card maker.

Usage:  python3 render.py spec.json [more.json ...]
Writes: cards/<post_id>-<n>.jpg  (1080 x 1350, JPEG, safe for TikTok, Instagram, Facebook)

Needs only Pillow. Fonts and logo are in this repo. See README.md for the spec format.
Exits with code 2 and a clear message if any text does not fit: shorten the text and run again.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, M = 1080, 1350, 84            # canvas and outer margin
MUSTARD, INK, PAPER, WHITE = "#ffbd59", "#1f1b14", "#fbf8f1", "#ffffff"
MUTED, LINE, SOFT, CREAM = "#6f6758", "#e7dfcf", "#fff1d6", "#f3ecdf"

THEMES = {  # bg, text, muted text, accent, panel, text on accent
    "mustard": dict(bg=MUSTARD, fg=INK, mut="#5c4410", acc=INK, panel=WHITE, on_acc=MUSTARD),
    "paper":   dict(bg=PAPER, fg=INK, mut=MUTED, acc=MUSTARD, panel=WHITE, on_acc=INK),
    "ink":     dict(bg=INK, fg=CREAM, mut="#a99f8c", acc=MUSTARD, panel="#2b261d", on_acc=INK),
}
INNER = {"mustard": "paper", "paper": "paper", "ink": "ink"}   # look of the middle slides


class Overflow(Exception):
    pass


def font(kind, size):
    name = {"display": "Bricolage-ExtraBold.ttf", "bold": "Figtree-Bold.ttf", "body": "Figtree-Medium.ttf"}[kind]
    return ImageFont.truetype(os.path.join(HERE, "fonts", name), size)


def wrap(d, text, f, maxw):
    lines = []
    for para in str(text).split("\n"):
        cur = ""
        for word in para.split():
            trial = (cur + " " + word).strip()
            if d.textlength(trial, font=f) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def fit(d, text, kind, maxw, maxh, start, floor, lead=1.14):
    """Largest size from start down to floor where the wrapped text fits the box."""
    size = start
    while size >= floor:
        f = font(kind, size)
        lines = wrap(d, text, f, maxw)
        widest = max(d.textlength(l, font=f) for l in lines)
        if len(lines) * size * lead <= maxh and widest <= maxw:
            return f, lines, size, int(size * lead)
        size -= 2
    raise Overflow(f'text too long for its box, shorten it: "{str(text)[:70]}"')


def put(d, x, y, lines, f, step, fill, align="left", maxw=0):
    for l in lines:
        dx = (maxw - d.textlength(l, font=f)) / 2 if align == "centre" else 0
        d.text((x + dx, y), l, font=f, fill=fill)
        y += step
    return y


def logo(img, d, t):
    """The real logo: mustard square with the hand-drawn lettering."""
    size, x, y = 150, M, M - 14
    d.rounded_rectangle([x, y, x + size, y + size], 22, fill=MUSTARD,
                        outline=INK if t["bg"] == MUSTARD else None, width=4)
    art = Image.open(os.path.join(HERE, "assets", "hm-lettering.png")).convert("RGBA")
    w = size - 34
    art = art.resize((w, int(art.height * w / art.width)), Image.LANCZOS)
    img.paste(art, (x + 17, y + (size - art.height) // 2), art)


def footer(d, t, n, total):
    y = H - M - 6
    d.text((M, y - 30), "@hustlemateuk", font=font("bold", 32), fill=t["mut"])
    if total > 1 and n < total:                       # swipe pill on all but the last slide
        f = font("bold", 30)
        label = "Swipe"
        pw = int(d.textlength(label, font=f)) + 104
        x0 = W - M - pw
        d.rounded_rectangle([x0, y - 50, W - M, y + 14], 32, fill=t["acc"])
        d.text((x0 + 32, y - 37), label, font=f, fill=t["on_acc"])
        ax = W - M - 56
        d.line([ax, y - 18, ax + 26, y - 18], fill=t["on_acc"], width=5)
        d.polygon([(ax + 22, y - 30), (ax + 36, y - 18), (ax + 22, y - 6)], fill=t["on_acc"])
    elif total > 1:
        d.text((W - M - d.textlength(f"{n}/{total}", font=font("bold", 30)), y - 28),
               f"{n}/{total}", font=font("bold", 30), fill=t["mut"])


def kicker(d, t, text, y):
    f = font("bold", 30)
    text = str(text).upper()
    w = int(d.textlength(text, font=f)) + 44
    d.rounded_rectangle([M, y, M + w, y + 56], 28, fill=t["acc"])
    d.text((M + 22, y + 10), text, font=f, fill=t["on_acc"])
    return y + 56 + 40


def body_lines(d, t, items, y, maxh, start=46, floor=34):
    """One short sentence per line, roomy spacing."""
    items = [str(i) for i in (items or [])]
    if not items:
        return y
    size = start
    while size >= floor:
        f = font("body", size)
        wrapped = [wrap(d, i, f, W - 2 * M) for i in items]
        gap = int(size * 0.62)
        total = sum(len(w) * int(size * 1.3) for w in wrapped) + gap * (len(items) - 1)
        if total <= maxh:
            for w in wrapped:
                y = put(d, M, y, w, f, int(size * 1.3), t["fg"]) + gap
            return y
        size -= 2
    raise Overflow(f'body text too long, use fewer or shorter lines: "{items[0][:60]}"')


def slide_cover(img, d, t, s):
    top, bottom = M + 220, H - M - 110
    y = kicker(d, t, s["kicker"], top) if s.get("kicker") else top
    sub_h = 190 if s.get("sub") else 0
    badge_h = 90 if s.get("badge") else 0
    f, lines, size, step = fit(d, s["title"], "display", W - 2 * M, bottom - y - sub_h - badge_h, 124, 64, 1.06)
    y = put(d, M, y, lines, f, step, t["fg"]) + 34
    if s.get("sub"):
        f2, l2, _, st2 = fit(d, s["sub"], "body", W - 2 * M, sub_h - 34, 48, 34, 1.28)
        y = put(d, M, y, l2, f2, st2, t["mut"])
    if s.get("badge"):
        fb = font("bold", 30)
        by = bottom - 62
        bw = int(d.textlength(s["badge"], font=fb)) + 78
        if bw > W - 2 * M:
            raise Overflow(f'badge too long: "{s["badge"]}"')
        d.rounded_rectangle([M, by, M + bw, by + 62], 31, outline=t["fg"], width=3)
        d.ellipse([M + 22, by + 22, M + 40, by + 40], fill=t["acc"] if t["bg"] != MUSTARD else INK)
        d.text((M + 54, by + 13), s["badge"], font=fb, fill=t["fg"])


def slide_point(img, d, t, s):
    top, bottom = M + 220, H - M - 110
    y = top
    if s.get("number") not in (None, ""):
        fn = font("display", 92)
        d.rounded_rectangle([M, y, M + 132, y + 132], 30, fill=t["acc"])
        num = str(s["number"])
        d.text((M + (132 - d.textlength(num, font=fn)) / 2, y + 10), num, font=fn, fill=t["on_acc"])
        y += 132 + 44
    if s.get("title"):
        f, lines, size, step = fit(d, s["title"], "display", W - 2 * M, 330, 78, 50, 1.1)
        y = put(d, M, y, lines, f, step, t["fg"]) + 44      # blank line between heading and body
    body_lines(d, t, s.get("body"), y, bottom - y)


def slide_example(img, d, t, s):
    top, bottom = M + 220, H - M - 110
    y = top
    f, lines, size, step = fit(d, s.get("title", "Worked example"), "display", W - 2 * M, 190, 68, 46, 1.1)
    y = put(d, M, y, lines, f, step, t["fg"]) + 36
    # rows may be [label, value] pairs or {"label": ..., "value": ...} objects
    rows = [(r["label"], r["value"]) if isinstance(r, dict) else tuple(r) for r in s.get("rows", [])]
    rh = 96 if len(rows) <= 4 else 80
    fr, fb = font("body", 42 if rh == 96 else 36), font("bold", 44 if rh == 96 else 38)
    ph = rh * len(rows) + 28
    d.rounded_rectangle([M, y, W - M, y + ph], 30, fill=t["panel"], outline=LINE if t["bg"] != INK else None, width=2)
    ry = y + 14
    for i, (label, value) in enumerate(rows):
        if d.textlength(str(label), font=fr) + d.textlength(str(value), font=fb) > W - 2 * M - 110:
            raise Overflow(f'example row too long: "{label} {value}"')
        d.text((M + 36, ry + (rh - fr.size) / 2 - 6), str(label), font=fr, fill=t["fg"])
        d.text((W - M - 36 - d.textlength(str(value), font=fb), ry + (rh - fb.size) / 2 - 6), str(value), font=fb, fill=t["fg"])
        if i < len(rows) - 1:
            d.line([M + 36, ry + rh, W - M - 36, ry + rh], fill=LINE if t["bg"] != INK else "#3a3326", width=2)
        ry += rh
    y += ph + 34
    if s.get("result"):
        fr2, l2, sz, st = fit(d, s["result"], "bold", W - 2 * M - 72, 170, 46, 32, 1.25)
        bh = len(l2) * st + 52
        d.rounded_rectangle([M, y, W - M, y + bh], 30, fill=t["acc"])
        put(d, M + 36, y + 24, l2, fr2, st, t["on_acc"])
        y += bh + 30
    if s.get("note"):
        fn, ln, _, stn = fit(d, s["note"], "body", W - 2 * M, max(60, bottom - y), 32, 24, 1.3)
        put(d, M, y, ln, fn, stn, t["mut"])


def slide_cta(img, d, t, s):
    top, bottom = M + 220, H - M - 110
    f, lines, size, step = fit(d, s["title"], "display", W - 2 * M, 420, 100, 58, 1.08)
    y = put(d, M, top + 20, lines, f, step, t["fg"]) + 44
    y = body_lines(d, t, s.get("body"), y, 300) + 20
    if s.get("button"):
        fb = font("bold", 44)
        bw = int(d.textlength(s["button"], font=fb)) + 96
        if bw > W - 2 * M:
            raise Overflow(f'button text too long: "{s["button"]}"')
        d.rounded_rectangle([M, y, M + bw, y + 104], 52, fill=t["acc"])
        d.text((M + 48, y + 26), s["button"], font=fb, fill=t["on_acc"])
    small = s.get("small", "General information, not personal tax advice.")
    fs, ls, _, sts = fit(d, small, "body", W - 2 * M, 80, 28, 22, 1.3)
    put(d, M, bottom - len(ls) * sts, ls, fs, sts, t["mut"])


KINDS = {"cover": slide_cover, "point": slide_point, "example": slide_example, "cta": slide_cta}


def render(spec, outdir):
    theme = spec.get("theme", "paper")
    if theme not in THEMES:
        raise Overflow(f'unknown theme "{theme}": use mustard, paper or ink')
    slides, paths = spec["slides"], []
    for n, s in enumerate(slides, 1):
        kind = s.get("type")
        if kind not in KINDS:
            raise Overflow(f'slide {n}: unknown type "{kind}": use cover, point, example or cta')
        t = THEMES[theme if kind in ("cover", "cta") else INNER[theme]]
        img = Image.new("RGB", (W, H), t["bg"])
        d = ImageDraw.Draw(img)
        try:
            KINDS[kind](img, d, t, s)
        except Overflow as e:
            raise Overflow(f"slide {n} ({kind}): {e}")
        logo(img, d, t)
        footer(d, t, n, len(slides))
        path = os.path.join(outdir, f'{spec["post_id"]}-{n}.jpg')
        img.save(path, "JPEG", quality=90, optimize=True)
        paths.append(path)
    return paths


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = os.path.join(HERE, "cards")
    os.makedirs(out, exist_ok=True)
    bad = 0
    for p in sys.argv[1:]:
        try:
            with open(p) as fh:
                spec = json.load(fh)
            for path in render(spec, out):
                print(os.path.relpath(path, HERE))
        except (Overflow, KeyError, ValueError) as e:
            bad += 1
            print(f"ERROR in {p}: {e}", file=sys.stderr)
    sys.exit(2 if bad else 0)
