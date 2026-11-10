#!/usr/bin/env python3
"""Gera os SVGs animados do README do perfil (fabricio-dev-front).

Paleta alinhada ao portfólio (fabricio-front.vercel.app): zinc escuro e monocromático,
com o verde só no status "Disponível".

Uso: python3 scripts/gen-assets.py assets
"""
import math
import os
import random
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "assets"
os.makedirs(OUT, exist_ok=True)
random.seed(7)

# ---- tokens do portfólio (app/globals.css, tema .dark)
BG = "#09090b"        # --background
CARD = "#121215"      # --card-bg
BORDER = "#27272a"    # --card-border
TAG = "#18181b"       # --tag-bg
FG = "#fafafa"        # --foreground
MUTED = "#a1a1aa"     # --muted-text
Z300 = "#d4d4d8"
Z500 = "#71717a"
Z600 = "#52525b"
Z700 = "#3f3f46"
GREEN = "#34d399"     # status "Disponível"

SANS = "'Geist','Inter','Segoe UI',system-ui,-apple-system,sans-serif"
MONO = "'Geist Mono','JetBrains Mono',ui-monospace,Consolas,'DejaVu Sans Mono',monospace"


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write(name, body):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    print(f"{name}: {os.path.getsize(path)/1024:.1f} KB")


def filters():
    return """
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="glowBig" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="14"/>
    </filter>
    <filter id="noise" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/>
      <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.05 0"/>
    </filter>"""


def stars(w, h, n, y0=0):
    out = []
    for i in range(n):
        x, y = random.uniform(0, w), random.uniform(y0, h)
        r = random.choice([0.5, 0.7, 0.9, 1.1])
        op = random.uniform(0.15, 0.6)
        if i % 3 == 0:
            d = random.uniform(2, 5)
            out.append(
                f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="{FG}" opacity="{op:.2f}">'
                f'<animate attributeName="opacity" values="{op:.2f};0.05;{op:.2f}" dur="{d:.1f}s" '
                f'begin="{random.uniform(0, 3):.1f}s" repeatCount="indefinite"/></circle>'
            )
        else:
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="{FG}" opacity="{op:.2f}"/>')
    return "".join(out)


def grid_floor(w, horizon, bottom, vp_x, n_h=14, dur=2.2, k=None, color=Z700):
    depth = bottom - horizon
    k = k or depth * 1.2
    out = []
    for i in range(-30, 31):
        xb = vp_x + i * 90
        out.append(f'<line x1="{f(vp_x)}" y1="{horizon}" x2="{f(vp_x + (xb - vp_x) * 4)}" y2="{f(horizon + depth * 4)}"/>')
    steps = 24
    for i in range(n_h):
        ys = []
        for s in range(steps + 1):
            z = (i + 1 - s / steps) + 0.35
            ys.append(f(min(horizon + k / z * 0.5, bottom + 60)))
        v = ";".join(ys)
        out.append(
            f'<line x1="0" x2="{w}" y1="{ys[0]}" y2="{ys[0]}">'
            f'<animate attributeName="y1" values="{v}" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y2" values="{v}" dur="{dur}s" repeatCount="indefinite"/></line>'
        )
    return f'<g stroke="{color}" stroke-width="1">' + "".join(out) + "</g>"


# ---------------------------------------------------------------- 3D
def rot(p, ax, ay, az=0.0):
    x, y, z = p
    c, s = math.cos(ay), math.sin(ay)
    x, z = x * c + z * s, -x * s + z * c
    c, s = math.cos(ax), math.sin(ax)
    y, z = y * c - z * s, y * s + z * c
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
        ax, ay, az = angle_fn(fi / frames)
        pts = [proj(rot((v[0] * size, v[1] * size, v[2] * size), ax, ay, az), cx, cy) for v in verts]
        pts_all.append(pts)
        ds.append(" ".join(f"M{f(pts[a][0])} {f(pts[a][1])}L{f(pts[b][0])} {f(pts[b][1])}" for a, b in edges))
    return ds, pts_all


def sphere_wire(cx, cy, R, dur, color, op=0.5):
    """Esfera wireframe girando (meridianos animados + paralelos fixos)."""
    mer = "".join(
        f'<ellipse cx="{cx}" cy="{cy}" ry="{R}" rx="{R}" fill="none" stroke="{color}" stroke-width="1" opacity="{op}">'
        f'<animate attributeName="rx" values="{";".join(f(abs(R * math.cos(k * math.pi / 6 + 2 * math.pi * i / 36))) for i in range(37))}" dur="{dur}s" repeatCount="indefinite"/></ellipse>'
        for k in range(6)
    )
    par = "".join(
        f'<ellipse cx="{cx}" cy="{f(cy + R * math.sin(a))}" rx="{f(R * math.cos(a))}" ry="{f(R * math.cos(a) * 0.2)}" fill="none" stroke="{color}" stroke-width="1" opacity="{op * 0.8:.2f}"/>'
        for a in (-1.0, -0.55, -0.2, 0.2, 0.55, 1.0)
    )
    return par + mer


# ================================================================ HERO
def hero():
    W, H, HZ = 1200, 420, 300
    cx, cy = 900, 160
    frames, dur = 72, 12

    cube_d, cube_pts = wire_frames(CUBE_V, CUBE_E, 64, cx, cy, frames,
                                   lambda t: (0.55 + 0.18 * math.sin(2 * math.pi * t), 2 * math.pi * t, 0.15))
    octa_d, _ = wire_frames(OCTA_V, OCTA_E, 40, cx, cy, frames,
                            lambda t: (0.3, -4 * math.pi * t, 0.35 * math.sin(2 * math.pi * t)))
    corners = "".join(
        f'<circle r="2.2" fill="{MUTED}"><animate attributeName="cx" values="{";".join(f(p[vi][0]) for p in cube_pts)}" dur="{dur}s" repeatCount="indefinite"/>'
        f'<animate attributeName="cy" values="{";".join(f(p[vi][1]) for p in cube_pts)}" dur="{dur}s" repeatCount="indefinite"/></circle>'
        for vi in range(8)
    )

    # digitação
    phrases = ["Engenharia de Software & IA", "Next.js · TypeScript · Tailwind", "IA Engineer — Full Stack",
               "Do problema ao produto em produção"]
    cw, fs = 12.6, 21
    tx, ty = 72, 214
    slot = 4.2
    total = slot * len(phrases)
    step = 0.05
    nfr = int(round(total / step))
    widths = []
    for k, p in enumerate(phrases):
        n = len(p)
        row = []
        for i in range(nfr + 1):
            tt = i * step - k * slot
            erase_at = slot - n * 0.022 - 0.15
            if tt < 0 or tt >= slot:
                w = 0
            elif tt < n * 0.055:
                w = int(tt / 0.055) + 1
            elif tt < erase_at:
                w = n
            else:
                w = max(0, n - int((tt - erase_at) / 0.022) - 1)
            row.append(min(w, n) * cw)
        widths.append(row)
    off = 2 * cw

    def discrete(series):
        kt, vals, prev = [], [], None
        for i, v in enumerate(series):
            if v != prev:
                kt.append(f"{i / nfr:.4f}")
                vals.append(f(v))
                prev = v
        return ";".join(kt), ";".join(vals)

    clips, texts = [], []
    for k, p in enumerate(phrases):
        kt, vals = discrete(widths[k])
        clips.append(
            f'<clipPath id="tc{k}"><rect x="{f(tx + off)}" y="{ty - 24}" height="34" width="0">'
            f'<animate attributeName="width" values="{vals}" keyTimes="{kt}" calcMode="discrete" dur="{total}s" repeatCount="indefinite"/></rect></clipPath>'
        )
        texts.append(
            f'<text clip-path="url(#tc{k})" x="{f(tx + off)}" y="{ty}" textLength="{f(len(p) * cw)}" '
            f'lengthAdjust="spacingAndGlyphs" font-size="{fs}" fill="{MUTED}">{esc(p)}</text>'
        )
    kt, vals = discrete([tx + off + max(widths[k][i] for k in range(len(phrases))) for i in range(nfr + 1)])
    cursor = (
        f'<rect y="{ty - 18}" width="10" height="22" fill="{Z500}" x="{f(tx + off)}">'
        f'<animate attributeName="x" values="{vals}" keyTimes="{kt}" calcMode="discrete" dur="{total}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" repeatCount="indefinite"/></rect>'
    )

    name = "Fabricio Pereira"
    glitch = (f'<animateTransform attributeName="transform" type="translate" dur="6s" repeatCount="indefinite" '
              f'values="0 0;3 0;-2 0;0 0;0 0" keyTimes="0;0.02;0.04;0.06;1" calcMode="discrete"/>')

    tags = ["Next.js", "TypeScript", "AI Agents", "MCP"]
    tag_svg, x = [], 72
    for t in tags:
        w = len(t) * 8.6 + 28
        tag_svg.append(
            f'<rect x="{f(x)}" y="244" width="{f(w)}" height="28" rx="6" fill="{TAG}" stroke="{BORDER}"/>'
            f'<text x="{f(x + w / 2)}" y="263" text-anchor="middle" font-size="13" fill="{Z300}">{t}</text>'
        )
        x += w + 10

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Fabricio Pereira — Engenharia de Software &amp; IA">
  <defs>{filters()}
    <radialGradient id="spot" cx="0.75" cy="0.38" r="0.55">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.07"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="nameGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{FG}"/><stop offset="0.45" stop-color="{FG}"/><stop offset="0.5" stop-color="{Z300}"/><stop offset="0.55" stop-color="{FG}"/><stop offset="1" stop-color="{Z500}"/>
    </linearGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="fadeFloor" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{BG}" stop-opacity="1"/><stop offset="0.35" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}" stop-opacity="0.6"/>
    </linearGradient>
    <linearGradient id="fadeSides" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{BG}"/><stop offset="0.25" stop-color="{BG}" stop-opacity="0"/><stop offset="0.75" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}"/>
    </linearGradient>
    <linearGradient id="horizon" gradientUnits="userSpaceOnUse" x1="0" x2="{W}" y1="0" y2="0">
      <stop offset="0" stop-color="{FG}" stop-opacity="0"/><stop offset="0.75" stop-color="{MUTED}" stop-opacity="0.35"/><stop offset="1" stop-color="{FG}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
    <clipPath id="floorClip"><rect y="{HZ}" width="{W}" height="{H - HZ}"/></clipPath>
    <clipPath id="nameClip"><text x="70" y="160" font-family="{SANS}" font-weight="700" font-size="62" letter-spacing="-1.5" textLength="540" lengthAdjust="spacingAndGlyphs">{name}</text></clipPath>
    {''.join(clips)}
  </defs>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="{BG}"/>
    <rect width="{W}" height="{H}" fill="url(#spot)"/>
    <g>{stars(W, HZ - 10, 90)}</g>

    <!-- chão em perspectiva -->
    <g clip-path="url(#floorClip)">{grid_floor(W, HZ, H, cx)}
      <rect y="{HZ}" width="{W}" height="{H - HZ}" fill="url(#fadeFloor)"/>
    </g>
    <rect width="{W}" height="{H}" fill="url(#fadeSides)" opacity="0.7"/>
    <line x1="0" x2="{W}" y1="{HZ}" y2="{HZ}" stroke="url(#horizon)" stroke-width="1"/>

    <!-- planeta wireframe ao fundo -->
    <g opacity="0.55">{sphere_wire(cx, cy, 128, 30, Z700, 0.9)}</g>

    <!-- objeto 3D -->
    <ellipse cx="{cx}" cy="{HZ + 14}" rx="80" ry="7" fill="{Z500}" opacity="0.15" filter="url(#glowBig)">
      <animate attributeName="rx" values="80;62;80" dur="5s" repeatCount="indefinite"/>
    </ellipse>
    <g>
      <animateTransform attributeName="transform" type="translate" values="0 0;0 -9;0 0" dur="5s" repeatCount="indefinite"/>
      <circle cx="{cx}" cy="{cy}" r="70" fill="{Z500}" opacity="0.08" filter="url(#glowBig)"/>
      <ellipse cx="{cx}" cy="{cy}" rx="168" ry="30" fill="none" stroke="{Z600}" stroke-width="1" stroke-dasharray="2 8" transform="rotate(-10 {cx} {cy})">
        <animate attributeName="stroke-dashoffset" values="0;-100" dur="4s" repeatCount="indefinite"/>
      </ellipse>
      <path d="{octa_d[0]}" fill="none" stroke="{Z600}" stroke-width="1.1">
        <animate attributeName="d" values="{';'.join(octa_d)}" dur="{dur}s" repeatCount="indefinite"/>
      </path>
      <path d="{cube_d[0]}" fill="none" stroke="{Z300}" stroke-width="1.4" stroke-linecap="round" stroke-opacity="0.75" filter="url(#glow)">
        <animate attributeName="d" values="{';'.join(cube_d)}" dur="{dur}s" repeatCount="indefinite"/>
      </path>
      {corners}
    </g>

    <!-- texto -->
    <g font-family="{SANS}">
      <rect x="70" y="72" width="206" height="28" rx="14" fill="{TAG}" stroke="{BORDER}"/>
      <circle cx="88" cy="86" r="4" fill="{GREEN}"><animate attributeName="opacity" values="1;0.4;1" dur="2s" repeatCount="indefinite"/></circle>
      <circle cx="88" cy="86" r="4" fill="none" stroke="{GREEN}"><animate attributeName="r" values="4;9" dur="2s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.8;0" dur="2s" repeatCount="indefinite"/></circle>
      <text x="101" y="91" font-size="13" fill="{Z300}">Disponível para projetos</text>

      <text x="70" y="160" font-weight="700" font-size="62" letter-spacing="-1.5" textLength="540" lengthAdjust="spacingAndGlyphs" fill="{Z600}" opacity="0.6">{name}{glitch}</text>
      <text x="70" y="160" font-weight="700" font-size="62" letter-spacing="-1.5" textLength="540" lengthAdjust="spacingAndGlyphs" fill="url(#nameGrad)">{name}</text>
      <g clip-path="url(#nameClip)">
        <rect y="90" width="120" height="90" fill="url(#shine)" opacity="0.18" transform="skewX(-20)">
          <animate attributeName="x" values="-200;900;900" keyTimes="0;0.4;1" dur="5s" repeatCount="indefinite"/>
        </rect>
      </g>
    </g>
    <g font-family="{MONO}">
      <text x="{tx}" y="{ty}" font-size="{fs}" fill="{Z600}" textLength="{f(cw)}" lengthAdjust="spacingAndGlyphs">&gt;</text>
      {''.join(texts)}
      {cursor}
      {''.join(tag_svg)}
    </g>
    <rect width="{W}" height="{H}" filter="url(#noise)"/>
  </g>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{BORDER}"/>
</svg>"""
    write("hero.svg", svg)


# ================================================================ HEADERS
def header(file, idx, title):
    W, H = 1200, 64
    tw = len(title) * 15.4
    x0 = 92
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(title)}">
  <defs>{filters()}
    <linearGradient id="ln" gradientUnits="userSpaceOnUse" x1="{f(x0 + tw + 20)}" x2="{W - 24}" y1="0" y2="0">
      <stop offset="0" stop-color="{Z700}"/><stop offset="1" stop-color="{Z700}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="12" fill="{BG}"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{BORDER}"/>
  <text x="24" y="40" font-family="{MONO}" font-size="15" fill="{Z600}">{idx}</text>
  <text x="56" y="40" font-family="{MONO}" font-size="15" fill="{Z600}">/</text>
  <text x="{x0 - 20}" y="42" font-family="{SANS}" font-weight="600" font-size="26" letter-spacing="-0.5" fill="{FG}" textLength="{f(tw)}" lengthAdjust="spacingAndGlyphs">{esc(title)}
    <animate attributeName="opacity" values="1;0.55;1;1" keyTimes="0;0.02;0.04;1" dur="5s" repeatCount="indefinite"/>
  </text>
  <line x1="{f(x0 + tw + 20)}" x2="{W - 24}" y1="33" y2="33" stroke="url(#ln)"/>
  <circle cy="33" r="2.5" fill="{Z500}" filter="url(#glow)">
    <animate attributeName="cx" values="{f(x0 + tw + 20)};{W - 24}" dur="3.5s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="1;0" dur="3.5s" repeatCount="indefinite"/>
  </circle>
</svg>"""
    write(file, svg)


# ================================================================ CARDS
ICONS = {
    # glifos simples (traço) desenhados em torno de (0,0), ~36px
    "web": '<rect x="-16" y="-12" width="32" height="24" rx="3"/><path d="M-16 -5 H16"/><circle cx="-11" cy="-8.5" r="1"/><circle cx="-7" cy="-8.5" r="1"/>',
    "ui": '<rect x="-16" y="-14" width="13" height="28" rx="2"/><rect x="1" y="-14" width="15" height="12" rx="2"/><rect x="1" y="2" width="15" height="12" rx="2"/>',
    "stack": '<path d="M0 -15 L16 -7 L0 1 L-16 -7 Z"/><path d="M-16 0 L0 8 L16 0"/><path d="M-16 7 L0 15 L16 7"/>',
    "ai": '<circle r="5"/><circle cx="-13" cy="-10" r="2.5"/><circle cx="13" cy="-10" r="2.5"/><circle cx="-13" cy="10" r="2.5"/><circle cx="13" cy="10" r="2.5"/><path d="M-4 -3 L-11 -8 M4 -3 L11 -8 M-4 3 L-11 8 M4 3 L11 8"/>',
    "auto": '<circle r="6"/><path d="M0 -15 V-10 M0 10 V15 M-15 0 H-10 M10 0 H15 M-10.6 -10.6 L-7 -7 M7 7 L10.6 10.6 M10.6 -10.6 L7 -7 M-7 7 L-10.6 10.6"/>',
    "perf": '<path d="M-15 10 A16 16 0 1 1 15 10"/><path d="M0 4 L8 -7"/><circle cy="4" r="2"/>',
}


def cards():
    items = [
        ("01", "Produtos Web", ["Produtos web completos e", "escaláveis, do zero ao deploy."], "web"),
        ("02", "Interfaces", ["UI moderna, responsiva e", "orientada à experiência."], "ui"),
        ("03", "Full Stack", ["Arquitetura com foco em", "qualidade e manutenção."], "stack"),
        ("04", "IA & Agents", ["Integração de IA, AI Agents", "e MCP em produtos reais."], "ai"),
        ("05", "Automação", ["Automação de fluxos de", "desenvolvimento e operações."], "auto"),
        ("06", "Performance", ["Code review, refatoração", "e otimização de performance."], "perf"),
    ]
    W, cwid, chei, gap, m = 1200, 380, 190, 20, 0
    H = 2 * chei + gap
    per = 2 * (cwid + chei)
    out = []
    for i, (num, title, lines, icon) in enumerate(items):
        x = (i % 3) * (cwid + gap)
        y = (i // 3) * (chei + gap)
        out.append(f"""
  <g>
    <rect x="{x + 0.5}" y="{y + 0.5}" width="{cwid - 1}" height="{chei - 1}" rx="14" fill="{CARD}" stroke="{BORDER}"/>
    <rect x="{x + 0.5}" y="{y + 0.5}" width="{cwid - 1}" height="{chei - 1}" rx="14" fill="none" stroke="{Z500}" stroke-width="1.2" stroke-dasharray="110 {per - 110}" opacity="0.8">
      <animate attributeName="stroke-dashoffset" values="0;-{per}" dur="7s" begin="{i * 0.9}s" repeatCount="indefinite"/>
    </rect>
    <rect x="{x + 26}" y="{y + 26}" width="52" height="52" rx="12" fill="{TAG}" stroke="{BORDER}"/>
    <g transform="translate({x + 52} {y + 52})" fill="none" stroke="{Z300}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
      {ICONS[icon]}
      <animateTransform attributeName="transform" type="translate" additive="sum" values="0 0;0 -2;0 0" dur="3s" begin="{i * 0.4}s" repeatCount="indefinite"/>
    </g>
    <text x="{x + cwid - 26}" y="{y + 50}" text-anchor="end" font-family="{MONO}" font-size="14" fill="{Z600}">{num}</text>
    <text x="{x + 26}" y="{y + 118}" font-family="{SANS}" font-weight="600" font-size="22" fill="{FG}">{esc(title)}</text>
    {''.join(f'<text x="{x + 26}" y="{y + 148 + j * 22}" font-family="{SANS}" font-size="16" fill="{MUTED}">{esc(l)}</text>' for j, l in enumerate(lines))}
  </g>""")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Produtos web, Interfaces, Full Stack, IA e Agents, Automação, Performance">
  <defs>{filters()}</defs>
  {''.join(out)}
</svg>"""
    write("services.svg", svg)


# ================================================================ ORBIT
def orbit():
    W, H = 1200, 440
    cx, cy = 600, 220
    orbits = [
        dict(r=260, tilt=0.36, zrot=-0.14, period=22, dirn=1,
             labels=["React", "Next.js", "TypeScript", "Tailwind", "Node.js"]),
        dict(r=440, tilt=0.30, zrot=0.10, period=32, dirn=-1,
             labels=["AI Agents", "MCP", "SQL", "Git", "Vercel", "Claude Code"]),
    ]
    frames = 96

    def point(o, a):
        x, y, z = rot((o["r"] * math.cos(a), 0, o["r"] * math.sin(a)), o["tilt"], 0, o["zrot"])
        s = 1700 / (1700 + z)
        return cx + x * s, cy + y * s, z, s

    back_r, front_r, back_l, front_l = [], [], [], []
    for o in orbits:
        pts = [point(o, 2 * math.pi * i / 180) for i in range(181)]
        sb, sf = [], []
        for i in range(180):
            a, b = pts[i], pts[i + 1]
            (sb if (a[2] + b[2]) / 2 > 0 else sf).append(f"M{f(a[0])} {f(a[1])}L{f(b[0])} {f(b[1])}")
        back_r.append(f'<path d="{"".join(sb)}" fill="none" stroke="{BORDER}" stroke-width="1"/>')
        front_r.append(f'<path d="{"".join(sf)}" fill="none" stroke="{Z600}" stroke-width="1.2"/>')
        n, dur = len(o["labels"]), o["period"]
        for li, txt in enumerate(o["labels"]):
            a0 = 2 * math.pi * li / n
            tr, sc, ob, of = [], [], [], []
            for fi in range(frames + 1):
                x, y, z, s = point(o, a0 + o["dirn"] * 2 * math.pi * fi / frames)
                tr.append(f"{f(x)} {f(y)}")
                sc.append(f"{s:.3f}")
                d = max(0.35, min(1, 0.95 - z / 900))
                ob.append(f"{d * 0.5:.2f}" if z > 0 else "0")
                of.append(f"{d:.2f}" if z <= 0 else "0")
            w = len(txt) * 9.4 + 30
            body = (
                f'<rect x="{f(-w / 2)}" y="-16" width="{f(w)}" height="32" rx="8" fill="{CARD}" stroke="{Z700}"/>'
                f'<text y="5.5" text-anchor="middle" font-family="{SANS}" font-size="15" font-weight="500" fill="{Z300}">{esc(txt)}</text>'
            )
            anim = (
                f'<animateTransform attributeName="transform" type="translate" values="{";".join(tr)}" dur="{dur}s" repeatCount="indefinite"/>'
                f'<animateTransform attributeName="transform" type="scale" additive="sum" values="{";".join(sc)}" dur="{dur}s" repeatCount="indefinite"/>'
            )
            back_l.append(f'<g opacity="0">{body}{anim}<animate attributeName="opacity" values="{";".join(ob)}" dur="{dur}s" repeatCount="indefinite"/></g>')
            front_l.append(f'<g opacity="0">{body}{anim}<animate attributeName="opacity" values="{";".join(of)}" dur="{dur}s" repeatCount="indefinite"/></g>')

    R = 64
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Stack: React, Next.js, TypeScript, Tailwind, Node.js, AI Agents, MCP, SQL, Git, Vercel, Claude Code">
  <defs>{filters()}
    <radialGradient id="core" cx="0.35" cy="0.3" r="0.8">
      <stop offset="0" stop-color="#3f3f46"/><stop offset="0.6" stop-color="#18181b"/><stop offset="1" stop-color="{BG}"/>
    </radialGradient>
    <radialGradient id="bg" cx="0.5" cy="0.5" r="0.6">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.05"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="{BG}"/>
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <g>{stars(W, H, 60)}</g>
    {''.join(back_r)}
    {''.join(back_l)}
    <circle cx="{cx}" cy="{cy}" r="{R + 20}" fill="{Z500}" opacity="0.08" filter="url(#glowBig)">
      <animate attributeName="opacity" values="0.04;0.1;0.04" dur="4s" repeatCount="indefinite"/>
    </circle>
    <circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#core)" stroke="{Z700}"/>
    {sphere_wire(cx, cy, R, 8, Z500, 0.45)}
    <text x="{cx}" y="{cy + 9}" text-anchor="middle" font-family="{MONO}" font-size="26" font-weight="600" fill="{FG}">&lt;/&gt;</text>
    {''.join(front_r)}
    {''.join(front_l)}
    <rect width="{W}" height="{H}" filter="url(#noise)"/>
  </g>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{BORDER}"/>
</svg>"""
    write("stack-orbit.svg", svg)


# ================================================================ CTA
def cta():
    W, H = 1200, 150
    bw, bh = 380, 64
    bx, by = (W - bw) / 2, (H - bh) / 2
    per = 2 * (bw + bh)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Entrar em contato">
  <defs>{filters()}
    <linearGradient id="l" gradientUnits="userSpaceOnUse" x1="120" x2="{f(bx - 24)}" y1="0" y2="0"><stop offset="0" stop-color="{Z700}" stop-opacity="0"/><stop offset="1" stop-color="{Z700}"/></linearGradient>
    <linearGradient id="r" gradientUnits="userSpaceOnUse" x1="{W - 120}" x2="{f(bx + bw + 24)}" y1="0" y2="0"><stop offset="0" stop-color="{Z700}" stop-opacity="0"/><stop offset="1" stop-color="{Z700}"/></linearGradient>
    <linearGradient id="btn" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1c1c20"/><stop offset="1" stop-color="{CARD}"/></linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="16" fill="{BG}"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{BORDER}"/>
  <line x1="120" x2="{f(bx - 24)}" y1="{H / 2}" y2="{H / 2}" stroke="url(#l)"/>
  <line x1="{f(bx + bw + 24)}" x2="{W - 120}" y1="{H / 2}" y2="{H / 2}" stroke="url(#r)"/>
  <rect x="{f(bx)}" y="{f(by)}" width="{bw}" height="{bh}" rx="12" fill="{Z500}" filter="url(#glowBig)">
    <animate attributeName="opacity" values="0.05;0.18;0.05" dur="3s" repeatCount="indefinite"/>
  </rect>
  <rect x="{f(bx + 0.5)}" y="{f(by + 0.5)}" width="{bw - 1}" height="{bh - 1}" rx="12" fill="url(#btn)" stroke="{Z700}"/>
  <rect x="{f(bx + 0.5)}" y="{f(by + 0.5)}" width="{bw - 1}" height="{bh - 1}" rx="12" fill="none" stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="80 {per}" opacity="0.7">
    <animate attributeName="stroke-dashoffset" values="0;-{per + 80}" dur="4s" repeatCount="indefinite"/>
  </rect>
  <circle cx="{f(bx + 34)}" cy="{H / 2}" r="4" fill="{GREEN}"><animate attributeName="opacity" values="1;0.4;1" dur="2s" repeatCount="indefinite"/></circle>
  <text x="{W / 2 + 2}" y="{H / 2 + 6.5}" text-anchor="middle" font-family="{SANS}" font-size="19" font-weight="600" fill="{Z300}">Entrar em contato</text>
  <g transform="translate({f(W / 2 + 106)} {H / 2})" fill="none" stroke="{MUTED}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M-6 0 H6 M1 -5 L6 0 L1 5"/>
    <animateTransform attributeName="transform" type="translate" additive="sum" values="0 0;4 0;0 0" dur="1.4s" repeatCount="indefinite"/>
  </g>
</svg>"""
    write("cta.svg", svg)


# ================================================================ FOOTER
def footer():
    W, H, HZ = 1200, 190, 72
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Construindo software com intenção, qualidade e impacto">
  <defs>{filters()}
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="0.45" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}" stop-opacity="0.5"/></linearGradient>
    <linearGradient id="sides" x1="0" x2="1"><stop offset="0" stop-color="{BG}"/><stop offset="0.3" stop-color="{BG}" stop-opacity="0"/><stop offset="0.7" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}"/></linearGradient>
    <linearGradient id="hz" gradientUnits="userSpaceOnUse" x1="0" x2="{W}" y1="0" y2="0"><stop offset="0" stop-color="{FG}" stop-opacity="0"/><stop offset="0.5" stop-color="{MUTED}" stop-opacity="0.3"/><stop offset="1" stop-color="{FG}" stop-opacity="0"/></linearGradient>
    <clipPath id="c"><rect width="{W}" height="{H}" rx="16"/></clipPath>
    <clipPath id="fc"><rect y="{HZ}" width="{W}" height="{H - HZ}"/></clipPath>
  </defs>
  <g clip-path="url(#c)">
    <rect width="{W}" height="{H}" fill="{BG}"/>
    <g>{stars(W, HZ, 30)}</g>
    <g clip-path="url(#fc)">{grid_floor(W, HZ, H, W / 2, n_h=12, dur=2.6, k=110)}<rect y="{HZ}" width="{W}" height="{H - HZ}" fill="url(#fade)"/></g>
    <rect width="{W}" height="{H}" fill="url(#sides)"/>
    <line x1="0" x2="{W}" y1="{HZ}" y2="{HZ}" stroke="url(#hz)"/>
    <text x="{W / 2}" y="44" text-anchor="middle" font-family="{SANS}" font-size="18" fill="{MUTED}">Construindo software com intenção, qualidade e impacto.</text>
    <text x="{W / 2}" y="{H - 26}" text-anchor="middle" font-family="{MONO}" font-size="12" letter-spacing="2" fill="{Z500}">© 2026 FABRICIO PEREIRA</text>
  </g>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{BORDER}"/>
</svg>"""
    write("footer.svg", svg)


hero()
cards()
orbit()
cta()
footer()
for file, idx, title in [
    ("h-sobre.svg", "01", "Sobre mim"),
    ("h-servicos.svg", "02", "O que eu faço"),
    ("h-stack.svg", "03", "Stack principal"),
    ("h-atividade.svg", "04", "Atividade"),
    ("h-contato.svg", "05", "Vamos construir juntos?"),
]:
    header(file, idx, title)
