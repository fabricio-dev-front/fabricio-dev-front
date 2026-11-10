#!/usr/bin/env python3
"""Gera os SVGs animados do README do perfil (fabricio-dev-front).

Uso: python3 gen.py <pasta_de_saida>
"""
import math
import os
import random
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "assets"
os.makedirs(OUT, exist_ok=True)
random.seed(7)

CYAN = "#22d3ee"
MAGENTA = "#e879f9"
VIOLET = "#8b5cf6"
PINK = "#f472b6"
ORANGE = "#fb923c"
MONO = "'JetBrains Mono','Fira Code',Consolas,'DejaVu Sans Mono','Courier New',monospace"


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write(name, body):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    print(f"{name}: {os.path.getsize(path)/1024:.1f} KB")


# ---------------------------------------------------------------- comuns
def glow_filters():
    return f"""
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="glowBig" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="10" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>"""


def stars(w, h, n, ymax=None):
    ymax = ymax or h
    out = []
    for i in range(n):
        x, y = random.uniform(0, w), random.uniform(0, ymax)
        r = random.choice([0.6, 0.8, 1, 1.2, 1.6])
        op = random.uniform(0.25, 0.9)
        if i % 3 == 0:
            d = random.uniform(1.5, 4)
            out.append(
                f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="#fff" opacity="{op:.2f}">'
                f'<animate attributeName="opacity" values="{op:.2f};0.1;{op:.2f}" dur="{d:.1f}s" '
                f'begin="{random.uniform(0, 3):.1f}s" repeatCount="indefinite"/></circle>'
            )
        else:
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="#fff" opacity="{op:.2f}"/>')
    return "\n".join(out)


def synth_grid(w, horizon, bottom, color=MAGENTA, n_h=14, dur=1.4, k=None, vp_x=None, flip=False):
    """Chão em perspectiva com linhas que andam em direção à câmera.
    flip=True desenha como teto (horizonte embaixo)."""
    vp_x = vp_x if vp_x is not None else w / 2
    depth = bottom - horizon
    k = k or depth * 1.2
    sign = -1 if flip else 1
    lines = []
    # verticais convergindo no ponto de fuga
    for i in range(-30, 31):
        xb = vp_x + i * 90
        lines.append(
            f'<line x1="{f(vp_x)}" y1="{horizon}" x2="{f(vp_x + (xb - vp_x) * 4)}" '
            f'y2="{f(horizon + sign * depth * 4)}"/>'
        )
    # horizontais em movimento
    dz = 1.0
    steps = 24
    for i in range(n_h):
        ys = []
        for s in range(steps + 1):
            t = s / steps
            z = (i + 1 - t) * dz + 0.35
            y = horizon + sign * k / (z * 1.0) * 0.5
            y = max(min(y, bottom + 60), horizon - 60) if not flip else y
            ys.append(f(y))
        vals = ";".join(ys)
        lines.append(
            f'<line x1="0" x2="{w}" y1="{ys[0]}" y2="{ys[0]}">'
            f'<animate attributeName="y1" values="{vals}" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y2" values="{vals}" dur="{dur}s" repeatCount="indefinite"/></line>'
        )
    return f'<g stroke="{color}" stroke-width="1.2" opacity="0.75">' + "\n".join(lines) + "</g>"


# ---------------------------------------------------------------- 3D util
def rot(p, ax, ay, az=0.0):
    x, y, z = p
    # Y
    c, s = math.cos(ay), math.sin(ay)
    x, z = x * c + z * s, -x * s + z * c
    # X
    c, s = math.cos(ax), math.sin(ax)
    y, z = y * c - z * s, y * s + z * c
    # Z
    c, s = math.cos(az), math.sin(az)
    x, y = x * c - y * s, x * s + y * c
    return x, y, z


def proj(p, cx, cy, fov=520, dist=420):
    x, y, z = p
    s = fov / (dist + z)
    return cx + x * s, cy + y * s


CUBE_V = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
CUBE_E = [(a, b) for a in range(8) for b in range(a + 1, 8)
          if sum(1 for i in range(3) if CUBE_V[a][i] != CUBE_V[b][i]) == 1]
OCTA_V = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
OCTA_E = [(a, b) for a in range(6) for b in range(a + 1, 6) if a // 2 != b // 2]


def wire_frames(verts, edges, size, cx, cy, frames, angle_fn):
    ds, pts_all = [], []
    for fi in range(frames + 1):
        t = fi / frames
        ax, ay, az = angle_fn(t)
        pts = [proj(rot((v[0] * size, v[1] * size, v[2] * size), ax, ay, az), cx, cy) for v in verts]
        pts_all.append(pts)
        ds.append(" ".join(f"M{f(pts[a][0])} {f(pts[a][1])}L{f(pts[b][0])} {f(pts[b][1])}" for a, b in edges))
    return ds, pts_all


# ================================================================ HERO
def hero():
    W, H, HZ = 1200, 420, 300
    cx, cy = 900, 165
    frames, dur = 72, 10

    cube_d, cube_pts = wire_frames(CUBE_V, CUBE_E, 62, cx, cy, frames,
                                   lambda t: (0.55 + 0.2 * math.sin(2 * math.pi * t), 2 * math.pi * t, 0.15))
    octa_d, _ = wire_frames(OCTA_V, OCTA_E, 40, cx, cy, frames,
                            lambda t: (0.3, -4 * math.pi * t, 0.4 * math.sin(2 * math.pi * t)))
    cube_vals = ";".join(cube_d)
    octa_vals = ";".join(octa_d)

    corners = []
    for vi in range(8):
        xs = ";".join(f(p[vi][0]) for p in cube_pts)
        ys = ";".join(f(p[vi][1]) for p in cube_pts)
        corners.append(
            f'<circle r="3.2" fill="#fff"><animate attributeName="cx" values="{xs}" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="cy" values="{ys}" dur="{dur}s" repeatCount="indefinite"/></circle>'
        )

    # --- digitação
    phrases = ["Software Engineer & AI", "Next.js · TypeScript · Tailwind", "IA Engineer — Full Stack",
               "Transformando ideias em produto"]
    cw, fs = 13.2, 22
    tx, ty = 72, 212
    slot = 4.0
    total = slot * len(phrases)
    step = 0.05
    nfr = int(total / step)
    widths = [[0.0] * (nfr + 1) for _ in phrases]
    for k, p in enumerate(phrases):
        start = k * slot
        n = len(p)
        for i in range(nfr + 1):
            tt = i * step - start
            if tt < 0 or tt >= slot:
                w = 0
            elif tt < n * 0.06:
                w = int(tt / 0.06) + 1
            elif tt < slot - n * 0.025 - 0.15:
                w = n
            else:
                w = max(0, n - int((tt - (slot - n * 0.025 - 0.15)) / 0.025) - 1)
            widths[k][i] = min(w, n) * cw
    off = 2 * cw  # "> "

    def discrete(series):
        kt, vals = [], []
        prev = None
        for i, v in enumerate(series):
            if v != prev:
                kt.append(f"{i / nfr:.4f}")
                vals.append(f(v))
                prev = v
        return ";".join(kt), ";".join(vals)

    typing = []
    for k, p in enumerate(phrases):
        kt, vals = discrete(widths[k])
        typing.append(
            f'<clipPath id="tc{k}"><rect x="{f(tx + off)}" y="{ty - 24}" height="34" width="0">'
            f'<animate attributeName="width" values="{vals}" keyTimes="{kt}" calcMode="discrete" dur="{total}s" repeatCount="indefinite"/>'
            f'</rect></clipPath>'
        )
    texts = []
    for k, p in enumerate(phrases):
        texts.append(
            f'<text clip-path="url(#tc{k})" x="{f(tx + off)}" y="{ty}" textLength="{f(len(p) * cw)}" '
            f'lengthAdjust="spacingAndGlyphs" font-size="{fs}" fill="#e2e8f0">{esc(p)}</text>'
        )
    cur_series = [tx + off + max(widths[k][i] for k in range(len(phrases))) for i in range(nfr + 1)]
    kt, vals = discrete(cur_series)
    cursor = (
        f'<rect y="{ty - 19}" width="11" height="23" fill="{CYAN}" x="{f(tx + off)}">'
        f'<animate attributeName="x" values="{vals}" keyTimes="{kt}" calcMode="discrete" dur="{total}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="0.9s" repeatCount="indefinite"/></rect>'
    )

    # --- glitch do nome
    name = "FABRICIO PEREIRA"
    nfs, nlen = 58, 560

    def jitter(dx):
        return (f'<animateTransform attributeName="transform" type="translate" dur="5s" repeatCount="indefinite" '
                f'values="0 0;0 0;{dx} 0;{-dx} 1;0 0;0 0;{dx * 1.6} -1;0 0" keyTimes="0;0.6;0.62;0.64;0.66;0.9;0.92;1" calcMode="discrete"/>')

    name_svg = f"""
    <g font-family="{MONO}" font-weight="800" font-size="{nfs}" letter-spacing="2">
      <text x="70" y="160" textLength="{nlen}" lengthAdjust="spacingAndGlyphs" fill="{CYAN}" opacity="0.8">{name}{jitter(-4)}</text>
      <text x="70" y="160" textLength="{nlen}" lengthAdjust="spacingAndGlyphs" fill="{MAGENTA}" opacity="0.8">{name}{jitter(4)}</text>
      <text x="70" y="160" textLength="{nlen}" lengthAdjust="spacingAndGlyphs" fill="url(#nameGrad)" filter="url(#glow)">{name}</text>
    </g>"""

    # --- tags
    tags = [("NEXT.JS", CYAN), ("TYPESCRIPT", VIOLET), ("AI AGENTS", MAGENTA), ("MCP", ORANGE)]
    tag_svg, x = [], 72
    for i, (t, c) in enumerate(tags):
        w = len(t) * 9.6 + 26
        tag_svg.append(
            f'<g><rect x="{f(x)}" y="242" width="{f(w)}" height="28" rx="4" fill="{c}" fill-opacity="0.08" stroke="{c}" stroke-opacity="0.7"/>'
            f'<text x="{f(x + w / 2)}" y="261" text-anchor="middle" font-size="14" fill="{c}" letter-spacing="1">{t}</text>'
            f'<animate attributeName="opacity" values="0.55;1;0.55" dur="3s" begin="{i * 0.4}s" repeatCount="indefinite"/></g>'
        )
        x += w + 12

    sun_stripes = "".join(
        f'<rect x="700" width="400" height="{3 + i * 1.3:.1f}" y="{HZ - 12 - i * 14}">'
        f'<animate attributeName="y" values="{HZ - 12 - i * 14};{HZ - 26 - i * 14}" dur="2s" repeatCount="indefinite"/></rect>'
        for i in range(7)
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Fabricio Pereira — Software Engineer &amp; AI">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#02000a"/><stop offset="0.55" stop-color="#0d0326"/><stop offset="0.72" stop-color="#2a0b4a"/><stop offset="1" stop-color="#05010f"/>
    </linearGradient>
    <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#1a0638"/><stop offset="1" stop-color="#05010f"/>
    </linearGradient>
    <linearGradient id="sun" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fde047"/><stop offset="0.45" stop-color="{ORANGE}"/><stop offset="1" stop-color="#db2777"/>
    </linearGradient>
    <linearGradient id="nameGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#ffffff"/><stop offset="0.5" stop-color="#cffafe"/><stop offset="1" stop-color="#f5d0fe"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-1 0;1 0" dur="4s" repeatCount="indefinite"/>
    </linearGradient>
    <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0.12"/>
    </linearGradient>
    <linearGradient id="fadeFloor" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#000" stop-opacity="1"/><stop offset="0.25" stop-color="#000" stop-opacity="0"/>
    </linearGradient>
    <mask id="sunMask"><rect x="700" y="0" width="400" height="{HZ}" fill="#fff"/><g fill="#000">{sun_stripes}</g></mask>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
    <clipPath id="floorClip"><rect y="{HZ}" width="{W}" height="{H - HZ}"/></clipPath>
    <pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity="0.35"/></pattern>
    {glow_filters()}
    {''.join(typing)}
  </defs>
  <g clip-path="url(#frame)" font-family="{MONO}">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    <g>{stars(W, H, 110, HZ - 20)}</g>

    <!-- sol retrô -->
    <circle cx="{cx}" cy="{HZ}" r="150" fill="url(#sun)" opacity="0.18" filter="url(#glowBig)"/>
    <circle cx="{cx}" cy="{HZ}" r="128" fill="url(#sun)" mask="url(#sunMask)" opacity="0.92"/>

    <!-- chão synthwave -->
    <rect y="{HZ}" width="{W}" height="{H - HZ}" fill="url(#floor)"/>
    <g clip-path="url(#floorClip)">{synth_grid(W, HZ, H, MAGENTA, vp_x=cx)}
      <rect y="{HZ}" width="{W}" height="{H - HZ}" fill="url(#fadeFloor)" opacity="0.9"/>
    </g>
    <line x1="0" x2="{W}" y1="{HZ}" y2="{HZ}" stroke="{PINK}" stroke-width="2" filter="url(#glow)"/>

    <!-- objeto 3D -->
    <ellipse cx="{cx}" cy="{HZ + 18}" rx="90" ry="10" fill="{CYAN}" opacity="0.25" filter="url(#glowBig)">
      <animate attributeName="rx" values="90;70;90" dur="4s" repeatCount="indefinite"/>
    </ellipse>
    <g>
      <animateTransform attributeName="transform" type="translate" values="0 0;0 -10;0 0" dur="4s" repeatCount="indefinite"/>
      <ellipse cx="{cx}" cy="{cy}" rx="165" ry="34" fill="none" stroke="{VIOLET}" stroke-width="1.5" stroke-dasharray="6 10" opacity="0.8" transform="rotate(-12 {cx} {cy})">
        <animate attributeName="stroke-dashoffset" values="0;-160" dur="4s" repeatCount="indefinite"/>
      </ellipse>
      <path d="{octa_d[0]}" fill="none" stroke="{MAGENTA}" stroke-width="1.6" filter="url(#glow)" opacity="0.9">
        <animate attributeName="d" values="{octa_vals}" dur="{dur}s" repeatCount="indefinite"/>
      </path>
      <path d="{cube_d[0]}" fill="none" stroke="{CYAN}" stroke-width="2.4" stroke-linecap="round" filter="url(#glow)">
        <animate attributeName="d" values="{cube_vals}" dur="{dur}s" repeatCount="indefinite"/>
      </path>
      <g filter="url(#glow)">{''.join(corners)}</g>
    </g>

    <!-- HUD texto -->
    <g font-size="14" letter-spacing="3" fill="{CYAN}">
      <circle cx="78" cy="88" r="5" fill="#4ade80"><animate attributeName="opacity" values="1;0.2;1" dur="1.4s" repeatCount="indefinite"/></circle>
      <text x="92" y="93">PLAYER_01 · ONLINE</text>
      <text x="330" y="93" fill="{MAGENTA}" opacity="0.8">// LVL 3.5 YRS</text>
    </g>
    {name_svg}
    <g font-family="{MONO}">
      <text x="{tx}" y="{ty}" font-size="{fs}" fill="{MAGENTA}" textLength="{f(cw)}" lengthAdjust="spacingAndGlyphs">&gt;</text>
      {''.join(texts)}
      {cursor}
    </g>
    <g font-family="{MONO}">{''.join(tag_svg)}</g>

    <!-- efeitos de tela -->
    <rect width="{W}" height="{H}" fill="url(#scanlines)" opacity="0.5"/>
    <rect width="{W}" height="90" fill="url(#scan)">
      <animate attributeName="y" values="-90;{H}" dur="5s" repeatCount="indefinite"/>
    </rect>
    <g fill="none" stroke="{CYAN}" stroke-width="2" opacity="0.8">
      <path d="M20 50 V20 H50"/><path d="M{W - 50} 20 H{W - 20} V50"/>
      <path d="M20 {H - 50} V{H - 20} H50"/><path d="M{W - 50} {H - 20} H{W - 20} V{H - 50}"/>
    </g>
  </g>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="none" stroke="{VIOLET}" stroke-opacity="0.5" stroke-width="2"/>
</svg>"""
    write("hero.svg", svg)


# ================================================================ SECTION HEADERS
def header(file, title, color):
    W, H = 1200, 64
    tw = len(title) * 19.8
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(title)}">
  <defs>{glow_filters()}
    <linearGradient id="ln" gradientUnits="userSpaceOnUse" x1="{f(84 + tw)}" x2="{W - 20}" y1="0" y2="0"><stop offset="0" stop-color="{color}"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="12" fill="#0b0620"/>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12" fill="none" stroke="{color}" stroke-opacity="0.3"/>
  <g font-family="{MONO}" font-weight="800" transform="translate(16 0)">
    <path d="M6 14 L26 32 L6 50" fill="none" stroke="{color}" stroke-width="4" filter="url(#glow)">
      <animate attributeName="opacity" values="1;0.3;1" dur="1.6s" repeatCount="indefinite"/>
    </path>
    <text x="44" y="43" font-size="33" fill="{MAGENTA if color == CYAN else CYAN}" opacity="0.7" textLength="{f(tw)}" lengthAdjust="spacingAndGlyphs">{esc(title)}
      <animateTransform attributeName="transform" type="translate" values="0 0;3 0;-2 0;0 0;0 0" keyTimes="0;0.04;0.08;0.12;1" calcMode="discrete" dur="3.5s" repeatCount="indefinite"/>
    </text>
    <text x="44" y="43" font-size="33" fill="#f8fafc" filter="url(#glow)" textLength="{f(tw)}" lengthAdjust="spacingAndGlyphs">{esc(title)}
      <animate attributeName="opacity" values="1;0.4;1;1" keyTimes="0;0.03;0.06;1" dur="3.5s" repeatCount="indefinite"/>
    </text>
  </g>
  <line x1="{f(84 + tw)}" x2="{W - 20}" y1="33" y2="33" stroke="url(#ln)" stroke-width="2"/>
  <circle cy="33" r="4" fill="{color}" filter="url(#glow)">
    <animate attributeName="cx" values="{f(84 + tw)};{W - 20}" dur="2.8s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="1;0" dur="2.8s" repeatCount="indefinite"/>
  </circle>
</svg>"""
    write(file, svg)


# ================================================================ CARDS (O que eu faço)
def cards():
    items = [
        ("01", "PRODUTOS WEB", ["Produtos web completos", "e escaláveis, do zero", "ao deploy."], CYAN),
        ("02", "INTERFACES", ["UI moderna, responsiva", "e orientada à experiência", "do usuário."], MAGENTA),
        ("03", "FULL STACK", ["Arquitetura com foco em", "qualidade e manutenção", "a longo prazo."], VIOLET),
        ("04", "IA & AGENTS", ["Integração de IA, AI Agents", "e MCP dentro de produtos", "reais."], ORANGE),
        ("05", "AUTOMAÇÃO", ["Automação de fluxos de", "desenvolvimento e", "operações."], "#4ade80"),
        ("06", "PERFORMANCE", ["Code review, refatoração", "e otimização de", "performance."], PINK),
    ]
    W, cwid, chei, gap, m = 1200, 370, 200, 25, 15
    H = 2 * chei + gap + 2 * m
    per = 2 * (cwid + chei)
    out = []
    for i, (num, title, lines, c) in enumerate(items):
        col, row = i % 3, i // 3
        x = m + col * (cwid + gap)
        y = m + row * (chei + gap)
        icx, icy = x + cwid - 46, y + 46
        out.append(f"""
  <g>
    <rect x="{x}" y="{y}" width="{cwid}" height="{chei}" rx="14" fill="#0b0620" stroke="{c}" stroke-opacity="0.25"/>
    <rect x="{x}" y="{y}" width="{cwid}" height="{chei}" rx="14" fill="none" stroke="{c}" stroke-width="2.5" stroke-dasharray="140 {per - 140}" filter="url(#glow)">
      <animate attributeName="stroke-dashoffset" values="0;-{per}" dur="5s" begin="{i * 0.6}s" repeatCount="indefinite"/>
    </rect>
    <text x="{x + 26}" y="{y + 64}" font-size="48" font-weight="800" fill="none" stroke="{c}" stroke-width="1.4" opacity="0.9">{num}</text>
    <text x="{x + 104}" y="{y + 58}" font-size="23" font-weight="800" fill="#f8fafc" letter-spacing="1.5">{esc(title)}</text>
    <g font-size="17" fill="#cbd5e1">
      {''.join(f'<text x="{x + 26}" y="{y + 108 + j * 26}">{esc(l)}</text>' for j, l in enumerate(lines))}
    </g>
    <g transform="translate({icx} {icy})" fill="none" stroke="{c}">
      <circle r="18" stroke-dasharray="4 6" stroke-width="2"><animateTransform attributeName="transform" type="rotate" values="0;360" dur="{6 + i}s" repeatCount="indefinite"/></circle>
      <circle r="9" stroke-width="2" filter="url(#glow)"><animate attributeName="r" values="7;10;7" dur="2s" begin="{i * 0.3}s" repeatCount="indefinite"/></circle>
    </g>
    <rect x="{x + 26}" y="{y + chei - 22}" width="{cwid - 52}" height="4" rx="2" fill="{c}" opacity="0.15"/>
    <rect x="{x + 26}" y="{y + chei - 22}" width="0" height="4" rx="2" fill="{c}" filter="url(#glow)">
      <animate attributeName="width" values="0;{cwid - 52};{cwid - 52};0" keyTimes="0;0.45;0.8;1" dur="4s" begin="{i * 0.5}s" repeatCount="indefinite"/>
    </rect>
  </g>""")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Produtos web, Interfaces, Full Stack, IA e Agents, Automação, Performance">
  <defs>{glow_filters()}</defs>
  <g font-family="{MONO}">{''.join(out)}</g>
</svg>"""
    write("services.svg", svg)


# ================================================================ ORBIT (stack)
def orbit():
    W, H = 1200, 440
    cx, cy = 600, 220
    orbits = [
        dict(r=260, tilt=0.36, zrot=-0.14, period=18, dirn=1,
             labels=[("React", "#61dafb"), ("Next.js", "#f8fafc"), ("TypeScript", "#3178c6"),
                     ("Tailwind", "#38bdf8"), ("Node.js", "#5fa04e")]),
        dict(r=440, tilt=0.30, zrot=0.10, period=26, dirn=-1,
             labels=[("AI Agents", MAGENTA), ("MCP", "#d97757"), ("SQL", "#4169e1"),
                     ("Git", "#f05032"), ("Vercel", "#f8fafc"), ("Claude Code", ORANGE)]),
    ]
    frames = 96

    def point(o, a):
        p = (o["r"] * math.cos(a), 0, o["r"] * math.sin(a))
        p = rot(p, o["tilt"], 0, o["zrot"])
        x, y, z = p
        s = 1700 / (1700 + z)
        return cx + x * s, cy + y * s, z, s

    back_rings, front_rings, back_lbl, front_lbl = [], [], [], []
    for oi, o in enumerate(orbits):
        pts = [point(o, 2 * math.pi * i / 180) for i in range(181)]
        segs_b, segs_f = [], []
        for i in range(180):
            a, b = pts[i], pts[i + 1]
            seg = f"M{f(a[0])} {f(a[1])}L{f(b[0])} {f(b[1])}"
            (segs_b if (a[2] + b[2]) / 2 > 0 else segs_f).append(seg)
        col = CYAN if oi == 0 else VIOLET
        back_rings.append(f'<path d="{"".join(segs_b)}" fill="none" stroke="{col}" stroke-width="1.2" opacity="0.3"/>')
        front_rings.append(f'<path d="{"".join(segs_f)}" fill="none" stroke="{col}" stroke-width="1.8" opacity="0.75" filter="url(#glow)"/>')
        n = len(o["labels"])
        dur = o["period"]
        for li, (txt, c) in enumerate(o["labels"]):
            a0 = 2 * math.pi * li / n
            tr, sc, op_b, op_f = [], [], [], []
            for fi in range(frames + 1):
                a = a0 + o["dirn"] * 2 * math.pi * fi / frames
                x, y, z, s = point(o, a)
                tr.append(f"{f(x)} {f(y)}")
                sc.append(f"{s:.3f}")
                depth = max(0.4, min(1, 0.95 - z / 900))
                op_b.append(f"{depth * 0.55:.2f}" if z > 0 else "0")
                op_f.append(f"{depth:.2f}" if z <= 0 else "0")
            w = len(txt) * 10.5 + 34
            body = (
                f'<rect x="{f(-w / 2)}" y="-17" width="{f(w)}" height="34" rx="17" fill="#0b0620" stroke="{c}" stroke-width="1.8"/>'
                f'<circle cx="{f(-w / 2 + 15)}" cy="0" r="4" fill="{c}"/>'
                f'<text x="{f(7)}" y="6" text-anchor="middle" font-size="16" font-weight="700" fill="#f1f5f9">{esc(txt)}</text>'
            )
            anim = (
                f'<animateTransform attributeName="transform" type="translate" values="{";".join(tr)}" dur="{dur}s" repeatCount="indefinite"/>'
                f'<animateTransform attributeName="transform" type="scale" additive="sum" values="{";".join(sc)}" dur="{dur}s" repeatCount="indefinite"/>'
            )
            back_lbl.append(f'<g opacity="0">{body}{anim}<animate attributeName="opacity" values="{";".join(op_b)}" dur="{dur}s" repeatCount="indefinite"/></g>')
            front_lbl.append(f'<g opacity="0">{body}{anim}<animate attributeName="opacity" values="{";".join(op_f)}" dur="{dur}s" repeatCount="indefinite"/></g>')

    R = 62
    meridians = "".join(
        f'<ellipse cx="{cx}" cy="{cy}" ry="{R}" rx="{R}" fill="none" stroke="{CYAN}" stroke-width="1" opacity="0.55">'
        f'<animate attributeName="rx" values="{";".join(f(abs(R * math.cos(k * math.pi / 4 + 2 * math.pi * i / 24))) for i in range(25))}" dur="6s" repeatCount="indefinite"/></ellipse>'
        for k in range(4)
    )
    parallels = "".join(
        f'<ellipse cx="{cx}" cy="{f(cy + R * math.sin(a))}" rx="{f(R * math.cos(a))}" ry="{f(R * math.cos(a) * 0.18)}" fill="none" stroke="{CYAN}" stroke-width="1" opacity="0.45"/>'
        for a in (-0.9, -0.45, 0, 0.45, 0.9)
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Stack: React, Next.js, TypeScript, Tailwind, Node.js, AI Agents, MCP, SQL, Git, Vercel, Claude Code">
  <defs>{glow_filters()}
    <radialGradient id="core" cx="0.38" cy="0.35" r="0.75">
      <stop offset="0" stop-color="#a5f3fc"/><stop offset="0.35" stop-color="{VIOLET}"/><stop offset="1" stop-color="#1e0a3c"/>
    </radialGradient>
    <radialGradient id="bg" cx="0.5" cy="0.5" r="0.6">
      <stop offset="0" stop-color="#1e0a3c"/><stop offset="1" stop-color="#05010f"/>
    </radialGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  </defs>
  <g clip-path="url(#frame)" font-family="{MONO}">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <g>{stars(W, H, 70)}</g>
    <text x="28" y="40" font-size="14" letter-spacing="3" fill="{CYAN}" opacity="0.8">// TECH_STACK.SYS</text>
    <text x="{W - 28}" y="{H - 24}" text-anchor="end" font-size="13" letter-spacing="2" fill="{MAGENTA}" opacity="0.7">ORBIT: STABLE ◉</text>
    {''.join(back_rings)}
    {''.join(back_lbl)}
    <circle cx="{cx}" cy="{cy}" r="{R + 30}" fill="{VIOLET}" opacity="0.35" filter="url(#glowBig)">
      <animate attributeName="r" values="{R + 22};{R + 36};{R + 22}" dur="3s" repeatCount="indefinite"/>
    </circle>
    <circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#core)"/>
    {parallels}{meridians}
    <text x="{cx}" y="{cy + 10}" text-anchor="middle" font-size="30" font-weight="800" fill="#fff" filter="url(#glow)">&lt;/&gt;</text>
    {''.join(front_rings)}
    {''.join(front_lbl)}
  </g>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="none" stroke="{VIOLET}" stroke-opacity="0.45" stroke-width="2"/>
</svg>"""
    write("stack-orbit.svg", svg)


# ================================================================ CTA
def cta():
    W, H = 1200, 160
    bw, bh = 520, 76
    bx, by = (W - bw) / 2, (H - bh) / 2
    per = 2 * (bw + bh)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Entrar em contato">
  <defs>{glow_filters()}
    <linearGradient id="btn" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}"/><stop offset="0.5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{MAGENTA}"/>
      <animateTransform attributeName="gradientTransform" type="rotate" values="0 .5 .5;360 .5 .5" dur="6s" repeatCount="indefinite"/>
    </linearGradient>
    <linearGradient id="side" gradientUnits="userSpaceOnUse" x1="60" x2="{f(bx - 20)}" y1="0" y2="0"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>
    <linearGradient id="side2" gradientUnits="userSpaceOnUse" x1="{W - 60}" x2="{f(bx + bw + 20)}" y1="0" y2="0"><stop offset="0" stop-color="{MAGENTA}" stop-opacity="0"/><stop offset="1" stop-color="{MAGENTA}"/></linearGradient>
  </defs>
  <line x1="60" x2="{f(bx - 20)}" y1="{H / 2}" y2="{H / 2}" stroke="url(#side)" stroke-width="2"/>
  <line x1="{f(bx + bw + 20)}" x2="{W - 60}" y1="{H / 2}" y2="{H / 2}" stroke="url(#side2)" stroke-width="2"/>
  <rect x="{f(bx)}" y="{f(by)}" width="{bw}" height="{bh}" rx="38" fill="url(#btn)" opacity="0.35" filter="url(#glowBig)">
    <animate attributeName="opacity" values="0.2;0.6;0.2" dur="2.4s" repeatCount="indefinite"/>
  </rect>
  <rect x="{f(bx)}" y="{f(by)}" width="{bw}" height="{bh}" rx="38" fill="#0b0620" stroke="url(#btn)" stroke-width="3"/>
  <rect x="{f(bx)}" y="{f(by)}" width="{bw}" height="{bh}" rx="38" fill="none" stroke="#fff" stroke-width="3" stroke-dasharray="90 {per}" filter="url(#glow)">
    <animate attributeName="stroke-dashoffset" values="0;-{per}" dur="3s" repeatCount="indefinite"/>
  </rect>
  <text x="{W / 2}" y="{H / 2 + 9}" text-anchor="middle" font-family="{MONO}" font-size="26" font-weight="800" letter-spacing="4" fill="#fff" filter="url(#glow)">ENTRAR EM CONTATO
    <tspan fill="{CYAN}">▸<animate attributeName="opacity" values="1;0.2;1" dur="1s" repeatCount="indefinite"/></tspan>
  </text>
</svg>"""
    write("cta.svg", svg)


# ================================================================ FOOTER
def footer():
    W, H, HZ = 1200, 200, 70
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Construindo software com intenção, qualidade e impacto">
  <defs>{glow_filters()}
    <linearGradient id="fl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a0b4a"/><stop offset="1" stop-color="#05010f"/></linearGradient>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05010f" stop-opacity="1"/><stop offset="0.3" stop-color="#05010f" stop-opacity="0"/></linearGradient>
    <clipPath id="c"><rect width="{W}" height="{H}" rx="18"/></clipPath>
    <clipPath id="fc"><rect y="{HZ}" width="{W}" height="{H - HZ}"/></clipPath>
  </defs>
  <g clip-path="url(#c)" font-family="{MONO}">
    <rect width="{W}" height="{H}" fill="#05010f"/>
    <g>{stars(W, HZ, 40)}</g>
    <rect y="{HZ}" width="{W}" height="{H - HZ}" fill="url(#fl)"/>
    <g clip-path="url(#fc)">{synth_grid(W, HZ, H, CYAN, n_h=12, dur=1.8, k=110)}<rect y="{HZ}" width="{W}" height="{H - HZ}" fill="url(#fade)"/></g>
    <line x1="0" x2="{W}" y1="{HZ}" y2="{HZ}" stroke="{CYAN}" stroke-width="2" filter="url(#glow)"/>
    <text x="{W / 2}" y="44" text-anchor="middle" font-size="19" fill="#e2e8f0" letter-spacing="1">Construindo software com intenção, qualidade e impacto.</text>
    <rect x="{W / 2 - 170}" y="{H - 52}" width="340" height="30" rx="6" fill="#05010f" opacity="0.75"/>
    <text x="{W / 2}" y="{H - 32}" text-anchor="middle" font-size="13" letter-spacing="4" fill="{MAGENTA}">END_OF_TRANSMISSION
      <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/></text>
  </g>
</svg>"""
    write("footer.svg", svg)


hero()
cards()
orbit()
cta()
footer()
for file, title, color in [
    ("h-sobre.svg", "SOBRE_MIM", CYAN),
    ("h-servicos.svg", "O_QUE_EU_FAÇO", MAGENTA),
    ("h-stack.svg", "STACK_PRINCIPAL", CYAN),
    ("h-atividade.svg", "ATIVIDADE_3D", MAGENTA),
    ("h-contato.svg", "VAMOS_CONSTRUIR_JUNTOS?", CYAN),
]:
    header(file, title, color)
