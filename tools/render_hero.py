"""Render the hero scene layers as realistic images.

Each layer lines up with the hero SVG's 1200x780 viewBox, so the existing
groups (and their parallax and drift) keep working; only the drawing inside
them changes.

    sky      opaque dusk sky with atmospheric glow
    sun      sun disk + bloom (transparent)
    clouds   lit stratus, wider than the frame so the drift never shows an edge
    trees    distant tree line silhouette, two depths of haze (transparent)
    roof     the roof corner: shingles, vent, fascia, gutter (transparent)

    python tools/render_hero.py   -> assets/img/hero-*.webp
"""

import os
import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "img")
SS = 3                 # render scale per viewBox unit
FINAL = 2              # output scale per viewBox unit
VW, VH = 1200, 780
SUN = (1004.0, 246.0)


def frac(a):
    return a - np.floor(a)


def h1(a):
    return frac(np.sin(a * 12.9898 + 78.233) * 43758.5453)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def low_noise(h, w, scale, seed, sx=1.0):
    rng = np.random.default_rng(seed)
    sh, sw = max(2, int(h / scale) + 3), max(2, int(w / (scale * sx)) + 3)
    small = rng.random((sh, sw)).astype(np.float32)
    img = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(img, np.float32) / 127.5 - 1.0


def fbm(h, w, seed, scales, weights, sx=1.0):
    out = np.zeros((h, w), np.float32)
    for i, (sc, wt) in enumerate(zip(scales, weights)):
        out += wt * low_noise(h, w, sc * SS, seed + i, sx)
    return out


def mix(a, b, t):
    if np.ndim(t) == 2:
        t = t[..., None]
    return a * (1 - t) + b * t


def rgb(*c):
    return np.array(c, np.float32)


def grid(x0, y0, x1, y1):
    """pixel centres in viewBox units for the region [x0,x1) x [y0,y1)"""
    w, h = int((x1 - x0) * SS), int((y1 - y0) * SS)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return x0 + (xx + 0.5) / SS, y0 + (yy + 0.5) / SS, h, w


def save(rgba, name, x0, y0, x1, y1, q=80):
    rgba = np.clip(rgba, 0, 255).astype(np.uint8)
    mode = "RGBA" if rgba.shape[2] == 4 else "RGB"
    im = Image.fromarray(rgba, mode)
    im = im.resize((int((x1 - x0) * FINAL), int((y1 - y0) * FINAL)), Image.LANCZOS)
    path = os.path.join(OUT, f"hero-{name}.webp")
    im.save(path, quality=q, method=6, alpha_quality=85)
    print(f"{name}: {im.size} {os.path.getsize(path) // 1024} KB")


# ---------------------------------------------------------------- sky

def sky():
    x, y, h, w = grid(0, 0, VW, VH)
    g = y / VH
    stops = [(0, (8, 12, 16)), (0.4, (21, 32, 42)), (0.7, (44, 58, 68)), (0.87, (93, 77, 67)), (1, (139, 98, 68))]
    img = np.zeros((h, w, 3), np.float32)
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        m = (g >= a) & (g <= b)
        t = ((g - a) / (b - a))[m]
        img[m] = rgb(*ca) * (1 - t[:, None]) + rgb(*cb) * t[:, None]
    # forward scatter around the sun, stronger toward the horizon
    d = np.hypot(x - SUN[0], (y - SUN[1]) * 1.25)
    glow = np.exp(-d / 260) * 0.55 + np.exp(-d / 90) * 0.35
    img = mix(img, rgb(232, 150, 96), np.clip(glow * (0.45 + 0.55 * g), 0, 0.85))
    # horizon band
    img = mix(img, rgb(196, 128, 84), smooth(0.62, 0.98, g) * 0.35 * np.exp(-np.abs(x - SUN[0]) / 700))
    # very faint high haze texture, then dither so the gradient never bands
    haze = fbm(h, w, 5, (180, 60), (0.7, 0.3), sx=4)
    img *= (1 + 0.03 * haze)[..., None]
    img += np.random.default_rng(1).uniform(-1.2, 1.2, img.shape).astype(np.float32)
    save(img, "sky", 0, 0, VW, VH, q=82)


# ---------------------------------------------------------------- sun

def sun():
    x0, y0, x1, y1 = SUN[0] - 260, SUN[1] - 260, SUN[0] + 260, SUN[1] + 260
    x, y, h, w = grid(x0, y0, x1, y1)
    r = np.hypot(x - SUN[0], y - SUN[1])
    R = 57
    disk = smooth(R + 0.8, R - 0.8, r)
    mu = np.sqrt(np.clip(1 - (r / R) ** 2, 0, 1))
    limb = 0.62 + 0.38 * mu                                    # limb darkening
    core = mix(rgb(240, 150, 92), rgb(255, 222, 180), mu ** 0.6) * limb[..., None]
    # thin haze strands crossing the lower disk
    strands = smooth(0.15, 0.6, fbm(h, w, 41, (14, 5), (0.7, 0.3), sx=9)) * smooth(SUN[1] - 10, SUN[1] + 45, y)
    core = mix(core, rgb(226, 132, 84), strands * 0.22)
    bloom = (np.exp(-np.clip(r - R, 0, None) / 22) * 0.7 + np.exp(-np.clip(r - R, 0, None) / 80) * 0.3) * smooth(255, 150, r)
    bloom_col = rgb(246, 172, 118)
    a = np.clip(np.maximum(disk, bloom * (1 - disk)), 0, 1)
    col = mix(bloom_col * np.ones_like(core), core, disk)
    rgba = np.concatenate([col, (a * 255)[..., None]], axis=2)
    save(rgba, "sun", x0, y0, x1, y1)
    return x0, y0, x1, y1


# ---------------------------------------------------------------- clouds

def clouds():
    x0, y0, x1, y1 = -60, 0, VW + 60, 470
    x, y, h, w = grid(x0, y0, x1, y1)
    n = fbm(h, w, 61, (150, 60, 24, 9, 4), (0.42, 0.28, 0.16, 0.09, 0.05), sx=3.2)
    bands = (np.exp(-((y - 120) / 42) ** 2) * 0.55 + np.exp(-((y - 300) / 55) ** 2) * 0.5
             + np.exp(-((y - 210) / 30) ** 2) * 0.25)
    dens = np.clip((n + 0.18) * 1.6 * bands - 0.08, 0, 1)
    dens = smooth(0.0, 0.55, dens)
    # light from the sun: edges facing it glow, the rest sits in shadow
    shift = int(5 * SS)
    below = np.roll(dens, -shift, axis=0)              # density a little further down
    above = np.roll(dens, shift, axis=0)
    toward = np.where(y < SUN[1], below, above)        # edge that faces the sun
    side = np.roll(dens, -shift, axis=1)               # sun is to the right of most cloud
    lit = np.clip(dens - 0.6 * toward - 0.4 * side, 0, 1) * 2.4
    near = np.exp(-np.hypot(x - SUN[0], (y - SUN[1]) * 1.6) / 380)
    base = mix(rgb(34, 44, 56), rgb(70, 76, 84), smooth(0, 1, 1 - y / 470))
    warm = rgb(244, 168, 112)
    col = mix(base, warm, np.clip(lit * (0.35 + 0.9 * near) + near * 0.35 * dens, 0, 1))
    col *= (1 + 0.05 * low_noise(h, w, 2 * SS, 64))[..., None]
    a = np.clip(dens * (0.55 + 0.35 * near), 0, 0.92)
    a *= smooth(x0, x0 + 40, x) * smooth(x1, x1 - 40, x)   # feathered sides
    rgba = np.concatenate([col, (a * 255)[..., None]], axis=2)
    save(rgba, "clouds", x0, y0, x1, y1)


# ---------------------------------------------------------------- trees

def tree_profile(xs, seed, base_y, scale):
    """skyline height (viewBox y of the top edge) for a row of trees"""
    rng = np.random.default_rng(seed)
    top = np.full_like(xs, base_y + 40 * scale)
    pos = -40.0
    while pos < VW + 40:
        kind = rng.random()
        if kind < 0.18:                                       # conifer
            hgt, half = rng.uniform(50, 85) * scale, rng.uniform(16, 24) * scale
            prof = base_y - hgt + hgt * np.abs(xs - pos) / half
            # ragged branch tiers
            prof += 5 * scale * np.abs(np.sin((xs - pos) * 0.9 + rng.uniform(0, 6))) * (np.abs(xs - pos) < half)
            prof = np.where(np.abs(xs - pos) < half, prof, 1e9)
            pos += rng.uniform(10, 24) * scale
        else:                                                 # broadleaf crown
            rad = rng.uniform(20, 40) * scale
            hgt = rng.uniform(26, 58) * scale
            prof = np.full_like(xs, 1e9)
            for _ in range(rng.integers(3, 6)):                # a crown is several lobes
                lx = pos + rng.uniform(-0.6, 0.6) * rad
                lr = rad * rng.uniform(0.45, 0.8)
                ly = base_y - hgt + rng.uniform(0, 0.5) * rad + lr
                dx = (xs - lx) / lr
                prof = np.minimum(prof, np.where(np.abs(dx) < 1, ly - lr * np.sqrt(np.clip(1 - dx ** 2, 0, 1)), 1e9))
            pos += rng.uniform(0.7, 1.2) * rad
        top = np.minimum(top, prof)
    return top


def trees():
    x0, y0, x1, y1 = 0, 470, VW, 860
    x, y, h, w = grid(x0, y0, x1, y1)
    xs = x[0]
    rgba = np.zeros((h, w, 4), np.float32)
    for layer, (seed, base, sc, col, haze) in enumerate([
        (71, 612, 0.75, rgb(38, 44, 50), 0.55),               # far row, hazy
        (72, 640, 1.0, rgb(13, 21, 27), 0.0),                 # near row
    ]):
        top = tree_profile(xs, seed, base, sc)
        leaf = low_noise(h, w, 6 * SS, 70 + layer) * 6 * sc + low_noise(h, w, 2.2 * SS, 80 + layer) * 3.5 * sc + low_noise(h, w, 0.8 * SS, 90 + layer) * 2.0 * sc
        inside = smooth(-0.6, 0.6, y - (top[None, :] + leaf))
        c = col * np.ones((h, w, 1), np.float32)
        # warm rim on crown tops near the sun, cool sky bounce elsewhere
        edge = smooth(4 * sc, 0, y - (top[None, :] + leaf)) * inside
        sunward = np.exp(-np.abs(x - SUN[0]) / 260)
        c = mix(c, rgb(150, 92, 60), edge * sunward * (0.55 if layer else 0.35))
        c = mix(c, rgb(60, 72, 82), edge * (1 - sunward) * 0.25)
        c *= (1 + 0.08 * low_noise(h, w, 1.2 * SS, 95 + layer))[..., None]
        if haze:
            c = mix(c, rgb(110, 92, 80), haze * 0.35)
        a = inside
        rgba[..., :3] = rgba[..., :3] * (1 - a[..., None]) + c * a[..., None]
        rgba[..., 3] = np.maximum(rgba[..., 3], a * 255)
    # unpremultiplied colour for the far row where the near row doesn't cover
    save(rgba, "trees", x0, y0, x1, y1)


# ---------------------------------------------------------------- roof

P0 = np.array([560.0, 780.0])      # eave line, from the SVG
P1 = np.array([1200.0, 432.0])


def roof():
    x0, y0, x1, y1 = 500, 370, VW, VH
    x, y, h, w = grid(x0, y0, x1, y1)
    e = (P1 - P0) / np.linalg.norm(P1 - P0)
    nrm = np.array([-e[1], e[0]])                 # points down-right, into the roof
    if nrm[0] < 0:
        nrm = -nrm
    along = (x - P0[0]) * e[0] + (y - P0[1]) * e[1]
    d = (x - P0[0]) * nrm[0] + (y - P0[1]) * nrm[1]   # 0 on the eave line, + into roof

    rgba = np.zeros((h, w, 4), np.float32)
    rng = np.random.default_rng(3)
    grain = rng.standard_normal((h, w)).astype(np.float32)
    g2 = low_noise(h, w, 1.4 * SS, 4)

    # ---- shingle field: courses parallel to the eave, slightly larger toward the camera
    a_p = 0.0028
    cu = np.log1p(a_p * np.clip(d - 8, 0, None)) / (a_p * 21.0)
    course = np.floor(cu).astype(np.int32)
    t = cu - course
    scale_al = (1 + a_p * np.clip(d, 0, None))
    al = along / scale_al
    col = np.zeros((h, w, 3), np.float32)
    shade = np.ones((h, w), np.float32)
    pal = np.stack([rgb(52, 56, 61), rgb(48, 52, 57), rgb(56, 59, 63), rgb(53, 52, 51), rgb(45, 49, 54)])
    under = rgb(28, 30, 33)
    for c in range(0, int(course.max()) + 1):
        m = course == c
        if not m.any():
            continue
        widths = rng.uniform(18, 40, 110)
        bounds = np.cumsum(widths) - 80 + rng.uniform(0, 40)
        idx = np.searchsorted(bounds, al[m])
        tid = c * 997 + idx
        r1, r2, r3 = h1(tid * 1.0), h1(tid * 1.7 + 3.1), h1(tid * 2.3 + 9.4)
        drop = np.where(r2 < 0.5, 0.14 + 0.28 * r3, 0.0)
        tt = t[m]
        base = pal[(r1 * 5).astype(int) % 5] * (0.95 + 0.1 * r3)[:, None]
        cut = tt < drop
        cm = np.where(cut[:, None], under * (0.9 + 0.2 * r3[:, None]), base)
        s = 1 - 0.7 * smooth(0.72, 1.0, tt) ** 1.4
        s = s * np.where(cut, 1 - 0.45 * smooth(drop - 0.12, drop, tt), 1.0)
        s = np.where((~cut) & (tt - drop < 0.04), s * 1.3, s)        # butt edge catching light
        left = al[m] - np.concatenate([[-1e9], bounds])[idx]
        s = s * np.where(left < 1.1, 0.6, 1.0)
        col[m] = cm
        shade[m] = s
    col *= (1 + 0.16 * grain + 0.07 * g2)[..., None]
    sp = rng.random((h, w)) > 0.987
    col[sp] = col[sp] * 1.45 + 8

    # sunset raking light: warm on the up-sun end, falling off into the corner
    sunlit = np.exp(-np.hypot(x - SUN[0], y - SUN[1]) / 520)
    warm = rgb(255, 170, 110)
    col = col * (0.55 + 0.45 * sunlit)[..., None]
    col = mix(col, col * warm / 200, 0.25 * sunlit)
    # butt edges pick up the copper rim more strongly
    rimband = (shade > 1.1).astype(np.float32)
    col = mix(col, rgb(190, 120, 80), rimband * 0.28 * sunlit)
    col *= shade[..., None]
    # depth: darker into the bottom-right corner, matching the old shade gradient
    col *= (1 - 0.45 * smooth(200, 520, d))[..., None]

    plane = smooth(-0.4, 0.4, d)
    rgba[..., :3] = col
    rgba[..., 3] = plane * 255

    # ---- vent pipe, same place and size as before (x 854..882, top ~630, base 716)
    cx, top_y, base_y, rad = 868.0, 636.0, 716.0, 14.0
    sh = (((x - cx - 18) / 40) ** 2 + ((y - base_y - 2) / 9) ** 2) < 1
    rgba[sh, :3] *= 0.5
    # flashing boot
    boot = (np.abs(x - cx) < rad * (1.7 - 0.6 * smooth(base_y, base_y - 16, y))) & (y > base_y - 16) & (y < base_y + 4)
    nx = np.clip((x - cx) / (rad * 1.7), -1, 1)
    lam_b = 0.35 + 0.7 * np.clip(np.sqrt(1 - nx ** 2) * 0.7 + nx * 0.5, 0, 1)
    bc = rgb(34, 35, 37) * lam_b[..., None] * 1.4
    rgba[boot, :3] = bc[boot]
    rgba[boot, 3] = 255
    pipe = (np.abs(x - cx) < rad) & (y > top_y) & (y < base_y - 10)
    nx = np.clip((x - cx) / rad, -1, 1)
    lam = 0.28 + 0.8 * np.clip(np.sqrt(1 - nx ** 2) * 0.55 + nx * 0.6, 0, 1)
    pc = mix(rgb(96, 104, 108), rgb(240, 176, 128), smooth(0.2, 1.0, nx) * 0.5) * lam[..., None]
    pc *= (1 + 0.025 * grain)[..., None]
    rgba[pipe, :3] = pc[pipe]
    rgba[pipe, 3] = 255
    rim = (((x - cx) / rad) ** 2 + ((y - top_y) / 5) ** 2) < 1
    rgba[rim, :3] = rgb(150, 150, 146)
    rgba[rim, 3] = 255
    inner = (((x - cx) / (rad * 0.8)) ** 2 + ((y - top_y) / 3.6) ** 2) < 1
    rgba[inner, :3] = rgb(16, 16, 16)

    # ---- eave: shadow, fascia, gutter (bands measured from the eave line)
    def band(lo, hi, soft=0.6):
        return smooth(lo - soft, lo + soft, d) * smooth(hi + soft, hi - soft, d)

    # gutter centre line is ~ -18.5 units from the eave line (from the SVG strokes)
    shadow = smooth(22, 2, d)
    rgba[..., :3] *= (1 - 0.6 * shadow * (d > 0))[..., None]
    fascia = band(-14, 1.5)
    fc = mix(rgb(30, 38, 44), rgb(58, 66, 72), smooth(-14, 1, d))
    fc *= (1 + 0.03 * grain)[..., None]
    drip = band(-1.0, 1.5, 0.3)
    fc = mix(fc, rgb(92, 102, 108), drip)
    gut = band(-31.5, -19.5, 0.5)
    gt = np.clip((d + 31.5) / 12, 0, 1)                     # 0 outer lip .. 1 back
    prof = 0.55 + 0.6 * np.exp(-((gt - 0.18) / 0.09) ** 2) + 0.25 * np.exp(-((gt - 0.55) / 0.2) ** 2) - 0.25 * smooth(0.75, 1.0, gt)
    sunlit_g = 0.5 + 0.8 * np.exp(-np.hypot(x - SUN[0], y - SUN[1]) / 500)
    gc = rgb(150, 160, 166) * (prof * sunlit_g)[..., None]
    gc = mix(gc, rgb(255, 196, 150), np.exp(-((gt - 0.18) / 0.06) ** 2) * 0.45 * sunlit_g)
    gc *= (1 + 0.015 * grain)[..., None]
    # hangers
    hang_pos = np.array([615, 719, 823, 927, 1031, 1135], np.float32)
    for hx in hang_pos:
        ha = ((hx - P0[0]) * e[0] + ((780 - (hx - 560) * 348 / 640) - P0[1]) * e[1])
        hm = (np.abs(along - ha) < 1.4) & (gt > 0.1) & (gt < 0.95)
        gc = np.where(hm[..., None], gc * 0.55, gc)
    for m, c in ((fascia, fc), (gut, gc)):
        rgba[..., :3] = rgba[..., :3] * (1 - m[..., None]) + c * m[..., None]
        rgba[..., 3] = np.maximum(rgba[..., 3], m * 255)
    # soft dark halo under the gutter to seat it against the sky
    halo = smooth(-46, -32, d) * smooth(-30, -32, d)
    ha_a = halo * 0.55
    rgba[..., :3] = rgba[..., :3] * (1 - ha_a[..., None] * (rgba[..., 3:] < 1)) + rgb(8, 12, 16) * (ha_a[..., None] * (rgba[..., 3:] < 1))
    rgba[..., 3] = np.maximum(rgba[..., 3], ha_a * 255)
    # round off the gutter's far end at the frame edge
    save(rgba, "roof", x0, y0, x1, y1, q=82)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sky()
    sun()
    clouds()
    trees()
    roof()
