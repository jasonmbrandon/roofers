"""Render the before/after roof images for the comparison slider.

Same roof, same camera, two states:
  before  worn 3-tab shingles: faded, algae streaks, moss, curled and missing
          tabs, a mismatched patch, cracked vent boot, sagging dirty gutter
  after   new architectural (laminated) shingles, new boot, clean trim

Procedural, deterministic (fixed seeds), no photography.

    python tools/render_roof.py        -> assets/img/roof-{before,after}[-1100].webp
"""

import os
import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "img")
S = 2                      # supersample, downscaled at the end
W, H = 1800 * S, 1200 * S
Y_RIDGE = 175 * S          # top of the shingle field
Y_EAVE = 965 * S           # drip edge
CX = W * 0.5
K = 0.42                   # perspective strength
V_TOTAL = 88.0             # inches of slope visible
E = 5.625                  # course exposure, inches
PX_IN = 17.5 * S           # horizontal px per inch at the eave

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


# ---------------------------------------------------------------- helpers

def frac(a):
    return a - np.floor(a)


def h1(a):
    return frac(np.sin(a * 12.9898 + 78.233) * 43758.5453)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def low_noise(scale, seed, h=H, w=W):
    rng = np.random.default_rng(seed)
    sh, sw = max(2, h // scale + 3), max(2, w // scale + 3)
    small = rng.random((sh, sw)).astype(np.float32)
    img = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(img, dtype=np.float32) / 127.5 - 1.0


def fbm(seed, scales=(220, 90, 36, 14), weights=(0.5, 0.28, 0.15, 0.07)):
    out = np.zeros((H, W), np.float32)
    for i, (sc, wt) in enumerate(zip(scales, weights)):
        out += wt * low_noise(sc * S // 2, seed + i)
    return out


def mix(a, b, t):
    t = t[..., None] if np.ndim(t) == 2 else t
    return a * (1 - t) + b * t


def rgb(*c):
    return np.array(c, np.float32)


# ---------------------------------------------------------------- geometry

s = np.clip((Y_EAVE - yy) / (Y_EAVE - Y_RIDGE), 0, 1)
v = V_TOTAL * s / (1 + K - K * s)                 # inches up-slope from eave
wscale = (1 + K - K * s) / (1 + K)
u = (xx - CX) / (PX_IN * wscale)                  # inches across, 0 = centre
roof = (yy >= Y_RIDGE) & (yy < Y_EAVE)

course = np.floor(v / E).astype(np.int32)
t = v / E - course                                # 0 = butt edge, 1 = under next butt

rng_fine = np.random.default_rng(7)
grain = rng_fine.standard_normal((H, W)).astype(np.float32)
grain2 = low_noise(3 * S, 11)
speck = rng_fine.random((H, W)).astype(np.float32)

light = (1.06 - 0.22 * (xx / W) - 0.10 * (yy / H)).astype(np.float32)   # sun upper-left


def screen_y(v_in):
    ss = v_in * (1 + K) / (V_TOTAL + K * v_in)
    return Y_EAVE - ss * (Y_EAVE - Y_RIDGE), ss


def screen_x(u_in, ss):
    return CX + u_in * PX_IN * (1 + K - K * ss) / (1 + K)


# vent location (roof coordinates)
VENT_U, VENT_V = 30.0, 47.0


# ---------------------------------------------------------------- sky + wall

def sky_and_wall(worn):
    img = np.zeros((H, W, 3), np.float32)
    g = np.clip(yy / Y_RIDGE, 0, 1)
    top, hor = rgb(34, 50, 68), rgb(214, 160, 120)
    img[:] = mix(top, hor, g ** 1.6)
    cn = 0.6 * low_noise(70 * S, 91, H, W // 5) + 0.3 * low_noise(24 * S, 92, H, W // 5) + 0.1 * low_noise(8 * S, 93, H, W // 5)
    cn = np.asarray(Image.fromarray(((cn + 1) * 127.5).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 127.5 - 1
    clouds = smooth(0.1, 0.55, cn) * smooth(0.0, 0.5, g)
    img = mix(img, rgb(236, 196, 160), clouds * 0.25 * (yy < Y_RIDGE))
    # distant tree line on the horizon
    tl = Y_RIDGE - (34 + 22 * low_noise(60 * S, 5, 1, W)[0] + 10 * low_noise(14 * S, 6, 1, W)[0]) * S
    trees = yy > tl[None, :]
    img[trees] = rgb(52, 58, 52) * 0.85
    # wall below the gutter: dark lap siding in shade
    wall = yy >= Y_EAVE
    lap = frac((yy - Y_EAVE) / (26 * S))
    sid = rgb(54, 58, 60) * (0.82 + 0.18 * smooth(0.0, 0.12, lap))[..., None]
    sid *= (1 - 0.55 * smooth(Y_EAVE + 260 * S, Y_EAVE, yy))[..., None] * 0.9 + 0.1
    if worn:
        streak = smooth(0.25, 0.7, low_noise(18 * S, 44, 1, W)[0])[None, :]
        fade = smooth(Y_EAVE + 240 * S, Y_EAVE + 60 * S, yy)
        sid *= (1 - 0.35 * streak * fade)[..., None]
        sid = mix(sid, rgb(70, 62, 48), 0.25 * streak * fade)
    img[wall] = sid[wall]
    return img


# ---------------------------------------------------------------- shingles

def architectural():
    """New laminated shingles: random-width tabs, darker shadow layer in the cut-outs."""
    col = np.zeros((H, W, 3), np.float32)
    shade = np.ones((H, W), np.float32)
    palette = [rgb(60, 63, 67), rgb(54, 57, 61), rgb(66, 68, 71), rgb(61, 59, 57), rgb(50, 53, 57)]
    under = rgb(30, 32, 35)
    rng = np.random.default_rng(21)
    for c in range(-1, int(V_TOTAL / E) + 2):
        m = roof & (course == c)
        if not m.any():
            continue
        widths = rng.uniform(4.5, 10.5, 60)
        bounds = np.cumsum(widths) - 140 + rng.uniform(0, 30)
        idx = np.searchsorted(bounds, u[m])
        tid = c * 997 + idx
        r1, r2, r3 = h1(tid * 1.0), h1(tid * 1.7 + 3.1), h1(tid * 2.3 + 9.4)
        drop = np.where(r2 < 0.5, 0.14 + 0.3 * r3, 0.0)
        tt = t[m]
        base = np.stack([palette[i] for i in range(5)])[(r1 * 5).astype(int) % 5]
        base *= (0.96 + 0.08 * r3)[:, None]
        base *= (1.0 + 0.06 * (tt - 0.5))[:, None]           # slight blend within tab
        cut = tt < drop
        c_m = np.where(cut[:, None], under * (0.9 + 0.2 * r3[:, None]), base)
        sh = np.ones_like(tt)
        sh *= 1 - 0.7 * smooth(0.74, 1.0, tt) ** 1.4               # shadow under the next butt
        sh *= np.where(cut, 1 - 0.45 * smooth(drop - 0.12, drop, tt), 1.0)
        edge = (~cut) & (tt - drop < 0.028)
        sh = np.where(edge, sh * 1.22, sh)
        bnd = np.concatenate([[-1e9], bounds])
        left = u[m] - bnd[idx]
        sh *= np.where(left < 0.18, 0.62, 1.0)               # tab gaps
        col[m] = c_m
        shade[m] = sh
    g = 1 + 0.16 * grain + 0.07 * grain2
    col *= g[..., None]
    sp = speck > 0.985
    col[sp] = col[sp] * 1.5 + rgb(10, 9, 8)
    return col, shade


def three_tab(seed=33):
    """Worn 3-tab shingles with weather, algae, moss and damage."""
    col = np.zeros((H, W, 3), np.float32)
    shade = np.ones((H, W), np.float32)
    rng = np.random.default_rng(seed)
    jitter = rng.uniform(-0.8, 0.8, 40)
    c = course
    off = ((c * 6) % 36).astype(np.float32) + jitter[np.clip(c + 2, 0, 39)]
    uu = u - off
    sh_i = np.floor(uu / 36)
    within = uu - sh_i * 36
    tab = np.floor(within / 12)
    p = within - tab * 12
    tid = c * 1013 + sh_i * 3 + tab
    r1, r2, r3, r4 = h1(tid), h1(tid * 1.9 + 4.2), h1(tid * 3.1 + 1.3), h1(sh_i * 7.7 + c * 2.1)

    faded_a, faded_b = rgb(116, 105, 87), rgb(94, 88, 76)
    base = mix(faded_a, faded_b, 0.35 * r4 + 0.65 * r1)

    # granule loss: smoother, darker asphalt showing through
    loss = smooth(0.18, 0.42, fbm(51)) * (0.55 + 0.45 * smooth(0.3, 0.0, t))
    loss = np.maximum(loss, smooth(0.10, 0.0, t) * 0.55)       # eroded butt edges
    base = mix(base, rgb(66, 60, 52), loss * 0.85)

    g = 1 + (0.20 * (1 - 0.6 * loss)) * grain + 0.09 * grain2
    base *= g[..., None]

    # algae streaks running down the slope
    wob = 5 * S * low_noise(60 * S, 63)
    xi = np.clip((xx + wob).astype(np.int32), 0, W - 1)
    col_noise = low_noise(20 * S, 61, 1, W)[0][xi]
    streak = smooth(0.05, 0.6, col_noise) * smooth(-0.3, 0.5, low_noise(140 * S, 62))
    streak *= (0.35 + 0.65 * (1 - s))
    base = mix(base, rgb(42, 44, 38), np.clip(streak * 0.75, 0, 0.8))

    sh = np.ones((H, W), np.float32)
    sh *= 1 - 0.58 * smooth(0.80, 1.0, t)
    sh *= np.where(t < 0.02, 1.12, 1.0)

    # keyways and joints
    key = ((tab > 0) & (p < 0.32) & (t < 0.9))
    joint = (tab == 0) & (p < 0.14)
    slot = key | joint
    base = np.where(slot[..., None], rgb(40, 36, 31) * (0.9 + 0.2 * grain2[..., None]), base)
    sh = np.where(slot, 0.85, sh)

    # curled tabs: corners lifted, dark gap underneath
    curl = (r2 < 0.16) & (c > 0)
    cup = ((p - 6) / 6) ** 2
    gap = 0.07 + 0.13 * cup
    in_gap = curl & (t < gap)
    base = np.where(in_gap[..., None], rgb(22, 20, 18), base)
    lip = curl & (t >= gap) & (t < gap + 0.035)
    sh = np.where(lip, sh * 1.35, sh)

    # missing tabs: fresher shingle underneath, sealant strip, nail heads
    miss = (r2 > 0.16) & (r2 < 0.205) & (c > 1) & (c < 13)
    under = rgb(84, 76, 64) * (1 + 0.12 * grain[..., None])
    seal = (t > 0.54) & (t < 0.6)
    under = np.where(seal[..., None], rgb(28, 26, 24), under)
    for px in (1.6, 10.4):
        nail = ((p - px) * 2.2) ** 2 + ((t - 0.72) * E * 2.2) ** 2 < 0.55
        under = np.where(nail[..., None], rgb(150, 146, 136), under)
        ring = (((p - px) * 2.2) ** 2 + ((t - 0.72) * E * 2.2) ** 2 < 1.1) & ~nail
        under = np.where(ring[..., None], rgb(96, 62, 38), under)
    base = np.where(miss[..., None], under, base)
    sh = np.where(miss & (t < 0.06), 0.55, sh)

    # mismatched patch from an old repair
    patch = (u > -40) & (u < -12) & (c >= 9) & (c <= 10)
    base = np.where(patch[..., None], rgb(68, 70, 72) * (1 + 0.16 * grain[..., None]) * (0.95 + 0.1 * r3[..., None]), base)
    seam = smooth(2.2, 0.0, np.minimum(np.abs(u + 40), np.abs(u + 12))) + smooth(1.0, 0.0, np.abs(v - 9 * E)) * ((u > -42) & (u < -10))
    cement = smooth(0.42, 0.5, fbm(71, (40, 18, 8), (0.6, 0.3, 0.1)) * 0.6 + 0.45 * seam)
    cement *= (((u + 26) / 18) ** 2 + ((v - 9.6 * E) / 9) ** 2 < 1)
    base = mix(base, rgb(18, 17, 16), cement)
    gloss = cement * (speck > 0.94) * 0.6
    base = mix(base, rgb(120, 120, 118), gloss)

    # moss: in the shade line under the butts and along keyways, mostly low
    m_n = fbm(81, (34, 14, 6, 3), (0.5, 0.28, 0.14, 0.08))
    zone = smooth(36, 4, v) * (0.6 + 0.4 * smooth(0.3, 0.95, t)) + 0.3 * key * smooth(30, 6, v)
    body = m_n * 0.75 + zone * 0.75 - 0.42
    moss = smooth(0.0, 0.10, body)
    fuzz = smooth(-0.02, 0.04, body + 0.06 * grain)
    moss = np.maximum(moss * 0.95, fuzz * 0.5 * smooth(-0.05, 0.0, body))
    tuft = low_noise(2 * S, 84)
    tone = smooth(-0.6, 0.9, 0.5 * tuft + 0.3 * grain + 0.6 * smooth(0.0, 0.25, body) - 0.2)
    moss_col = mix(rgb(44, 56, 30), rgb(104, 118, 58), tone)
    moss_col *= (1 + 0.22 * grain[..., None])
    base = mix(base, moss_col, moss)
    # cushion shading: lit on the up-slope side, dark rim where it meets the shingle
    rim = smooth(0.0, 0.05, body) * (1 - smooth(0.05, 0.14, body))
    sh = sh * (1 - moss) + moss * (0.72 + 0.4 * smooth(0.02, 0.2, body) - 0.25 * rim)

    col[:] = base
    shade[:] = sh
    return col, shade


# ---------------------------------------------------------------- vent

def vent(img, worn):
    # flashing flange, in roof coordinates
    du, dv = u - VENT_U, v - VENT_V
    fl = roof & (np.abs(du) < 6.5) & (dv > -5.5) & (v < (np.floor((VENT_V + 1.2) / E) + 1) * E - 0.01) & (dv < 3.5)
    if worn:
        fc = mix(rgb(112, 106, 96), rgb(118, 72, 42), smooth(0.0, 0.5, fbm(101, (30, 12, 5), (0.5, 0.3, 0.2))))
        blob = smooth(0.0, 0.25, 1 - ((du / 6) ** 2 + ((dv + 1.5) / 4.5) ** 2) + 0.25 * low_noise(5 * S, 102))
        fc = mix(fc, rgb(20, 19, 18), blob)
    else:
        fc = mix(rgb(108, 114, 118), rgb(132, 138, 142), smooth(-5.5, 2, dv))
    fc = fc * (1 + 0.04 * grain[..., None])
    tuck = (1 - 0.65 * smooth(0.72, 1.0, t)) * light
    img[fl] = (fc * tuck[..., None])[fl] if fc.ndim == 3 else fc * tuck[fl][:, None]
    # shadow of the pipe falling down-right
    by, bs = screen_y(VENT_V)
    bx = screen_x(VENT_U, bs)
    r = 1.75 * PX_IN * (1 + K - K * bs) / (1 + K)
    sh = (((xx - bx - 2.6 * r) / (2.4 * r)) ** 2 + ((yy - by - 0.5 * r) / (0.8 * r)) ** 2) < 1
    img[sh & roof] *= 0.62
    # pipe: shaded cylinder standing up off the roof
    top = by - 5.2 * r
    cyl = (np.abs(xx - bx) < r) & (yy > top) & (yy < by)
    nx = np.clip((xx - bx) / r, -1, 1)
    lam = 0.35 + 0.75 * np.clip(np.sqrt(1 - nx ** 2) * 0.8 - nx * 0.45, 0, 1)
    pc = rgb(176, 178, 174) if not worn else rgb(146, 142, 130)
    pipe = pc * lam[..., None] * (1 + 0.02 * grain[..., None])
    if worn:
        dirt = smooth(top + 2 * r, by, yy) * 0.35
        pipe = mix(pipe, rgb(70, 62, 50), dirt)
    img[cyl] = pipe[cyl]
    rim = (((xx - bx) / r) ** 2 + ((yy - top) / (0.36 * r)) ** 2) < 1
    img[rim] = (pc * 0.92)[None, :]
    inner = (((xx - bx) / (0.78 * r)) ** 2 + ((yy - top) / (0.27 * r)) ** 2) < 1
    img[inner] = rgb(24, 22, 20)
    # rubber boot collar
    bt = (np.abs(xx - bx) < r * (1.55 - 0.45 * smooth(by, by - 1.4 * r, yy))) & (yy > by - 1.4 * r) & (yy < by + 0.25 * r)
    bcol = rgb(28, 29, 31) * lam[..., None] * 1.3
    if worn:
        bcol = rgb(52, 48, 42) * lam[..., None] * 1.3
        crack = (np.abs(low_noise(3 * S, 103)) < 0.05) & bt
        bcol = np.where(crack[..., None], rgb(150, 140, 120), bcol)
    img[bt] = bcol[bt]
    return img


# ---------------------------------------------------------------- ridge + eave

def ridge(img, worn):
    top = Y_RIDGE - 30 * S
    band = (yy >= top) & (yy < Y_RIDGE)
    u_top = (xx - CX) / (PX_IN / (1 + K))
    seg = frac((u_top + 3) / 12)
    tt = (yy - top) / (Y_RIDGE - top)
    base = rgb(98, 90, 76) if worn else rgb(56, 59, 63)
    c = base * (1 + (0.18 if worn else 0.14) * grain[..., None])
    sh = 1 - 0.5 * smooth(0.0, 0.35, 1 - tt)[..., None] * 0 - 0.0
    sh = (0.75 + 0.35 * tt)[..., None] * np.where((seg < 0.02)[..., None], 0.6, 1.0)
    c = c * sh
    if worn:
        miss = (h1(np.floor((u_top + 3) / 12)) < 0.12)
        c = np.where(miss[..., None], rgb(30, 28, 25), c)
    img[band] = (c * light[..., None])[band]
    # the cap casts a shadow on the top course
    img[(yy >= Y_RIDGE) & (yy < Y_RIDGE + 10 * S)] *= 0.6
    return img


def eave(img, worn):
    sag = (10 * S * np.sin(np.pi * np.clip((xx - 200 * S) / (900 * S), 0, 1)) * (xx > 200 * S) * (xx < 1100 * S)) if worn else 0
    d_top = Y_EAVE
    drip = (yy >= d_top) & (yy < d_top + 8 * S)
    img[drip] = (rgb(150, 150, 146) if not worn else rgb(92, 86, 74))
    g_top = d_top + 8 * S + sag
    g_bot = g_top + 86 * S
    gut = (yy >= g_top) & (yy < g_bot)
    gt = (yy - g_top) / (86 * S)
    prof = 0.9 + 0.22 * smooth(0.04, 0.0, gt) - 0.18 * smooth(0.18, 0.32, gt) * smooth(0.6, 0.42, gt) + 0.1 * smooth(0.45, 0.6, gt) - 0.12 * smooth(0.85, 1.0, gt)
    if worn:
        gc = rgb(150, 144, 128) * prof[..., None]
        tiger = smooth(0.2, 0.6, low_noise(7 * S, 121, 1, W)[0])[None, :] * smooth(0.1, 0.9, gt)
        gc = mix(gc, rgb(84, 72, 56), tiger * 0.6)
        gc *= (1 + 0.05 * grain[..., None])
    else:
        gc = rgb(236, 232, 224) * prof[..., None] * (1 + 0.012 * grain[..., None])
        hang = (frac((xx - 60 * S) / (230 * S)) < 0.012) & (gt > 0.08) & (gt < 0.16)
        gc = np.where(hang[..., None], rgb(150, 150, 146), gc)
    img[gut] = (gc * (light[..., None] * 0.9 + 0.1))[gut]
    # shadow the gutter throws on the wall
    sh = (yy >= g_bot) & (yy < g_bot + 40 * S)
    img[sh] *= (0.35 + 0.65 * smooth(g_bot, g_bot + 40 * S, yy))[..., None][sh]
    if worn:
        # debris and moss poking over the lip
        lip = (yy < g_top) & (yy > g_top - 14 * S) & (smooth(0.35, 0.55, low_noise(5 * S, 131)) * smooth(g_top - 14 * S, g_top, yy) > 0.3)
        img[lip] = mix(rgb(78, 92, 48), rgb(90, 70, 46), smooth(-1, 1, grain2))[lip]
    return img


# ---------------------------------------------------------------- compose

def finish(img):
    vy, vx = (yy / H - 0.45), (xx / W - 0.5)
    vig = 1 - 0.38 * smooth(0.25, 0.85, np.sqrt(vx ** 2 * 0.8 + vy ** 2 * 1.2))
    img *= vig[..., None]
    img = np.clip(img, 0, 255).astype(np.uint8)
    im = Image.fromarray(img).resize((W // S, H // S), Image.LANCZOS)
    return im


def render(worn):
    img = sky_and_wall(worn)
    col, shade = three_tab() if worn else architectural()
    rf = col * (shade * light)[..., None]
    if not worn:
        # faint sheen on new granules
        rf *= (1 + 0.05 * smooth(0.0, 1.0, 1 - (xx / W) * 0.8 - s * 0.3))[..., None]
    img[roof] = rf[roof]
    img = ridge(img, worn)
    img = vent(img, worn)
    img = eave(img, worn)
    return finish(img)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, worn in (("before", True), ("after", False)):
        im = render(worn)
        im.save(os.path.join(OUT, f"roof-{name}.webp"), quality=82, method=6)
        im.resize((1100, 733), Image.LANCZOS).save(os.path.join(OUT, f"roof-{name}-1100.webp"), quality=80, method=6)
        print(name, "done")
