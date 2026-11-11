#!/usr/bin/env python3
"""Gera dist/languages.svg com TODAS as linguagens usadas nos repositórios do usuário.

Soma os bytes por linguagem (API de linguagens do GitHub) de todos os repositórios
públicos do usuário (sem forks) e dos repositórios de organizações em que ele
contribuiu, e desenha um donut animado + legenda no tema dark do README.

Uso (no GitHub Actions):
  GITHUB_TOKEN=... USERNAME=fabricio-dev-front python3 scripts/gen-languages.py dist/languages.svg
Para testar sem rede:
  python3 scripts/gen-languages.py out.svg --mock
"""
import json
import math
import os
import re
import sys
import urllib.request

OUT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "dist/languages.svg"
MOCK = "--mock" in sys.argv
USER = os.environ.get("USERNAME", "fabricio-dev-front")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
EXTRA_REPOS = [r for r in os.environ.get("EXTRA_REPOS", "").split(",") if r.strip()]
IGNORE = {"Procfile", "Dockerfile", "Makefile"}  # arquivos de infra, não linguagens

BG, CARD, BORDER, TAG = "#09090b", "#121215", "#27272a", "#18181b"
FG, MUTED, Z500, Z600 = "#fafafa", "#a1a1aa", "#71717a", "#52525b"
SANS = "'Geist','Inter','Segoe UI',system-ui,-apple-system,sans-serif"
MONO = "'Geist Mono','JetBrains Mono',ui-monospace,Consolas,monospace"


def get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-languages"})
    if TOKEN and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {TOKEN}")
        req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read().decode("utf-8")
    return data if raw else json.loads(data)


def linguist_colors():
    try:
        yml = get("https://raw.githubusercontent.com/github-linguist/linguist/main/lib/linguist/languages.yml", raw=True)
    except Exception as e:  # sem cores oficiais, usa cinza
        print("aviso: não consegui baixar as cores do linguist:", e)
        return {}
    colors, name = {}, None
    for line in yml.splitlines():
        m = re.match(r'^([^\s#][^:]*):\s*$', line)
        if m:
            name = m.group(1).strip().strip('"')
            continue
        m = re.match(r'^\s+color:\s*"(#[0-9a-fA-F]{6})"', line)
        if m and name:
            colors[name] = m.group(1)
    return colors


def collect():
    if MOCK:
        return {"TypeScript": 2_400_000, "JavaScript": 610_000, "CSS": 380_000, "HTML": 300_000,
                "Python": 210_000, "C": 160_000, "Java": 90_000, "SCSS": 40_000, "Shell": 9_000,
                "C++": 8_000, "PLpgSQL": 6_000, "Dart": 4_000, "MDX": 1_500}
    repos, page = [], 1
    while True:
        batch = get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos += [r["full_name"] for r in batch if not r.get("fork")]
        if len(batch) < 100:
            break
        page += 1
    # repositórios de organizações onde o usuário fez push (eventos públicos recentes)
    try:
        for ev in get(f"https://api.github.com/users/{USER}/events/public?per_page=100"):
            name = ev.get("repo", {}).get("name", "")
            if ev.get("type") in ("PushEvent", "PullRequestEvent") and name and not name.startswith(USER + "/"):
                repos.append(name)
    except Exception as e:
        print("aviso: eventos indisponíveis:", e)
    repos += EXTRA_REPOS
    totals = {}
    for full in sorted(set(repos)):
        try:
            for lang, size in get(f"https://api.github.com/repos/{full}/languages").items():
                if lang not in IGNORE:
                    totals[lang] = totals.get(lang, 0) + size
        except Exception as e:
            print(f"aviso: {full}: {e}")
    print(f"{len(set(repos))} repositórios, {len(totals)} linguagens")
    return totals


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(totals, colors):
    items = sorted(totals.items(), key=lambda kv: -kv[1])
    total = sum(v for _, v in items) or 1
    MAX = 20
    if len(items) > MAX:
        rest = sum(v for _, v in items[MAX - 1:])
        items = items[:MAX - 1] + [("Outras", rest)]
    n = len(items)

    cols = 1 if n <= 7 else 2
    rows = math.ceil(n / cols)
    row_h = 38
    W = 1200
    H = max(360, 90 + rows * row_h + 40)
    cx, cy, R, sw = 230, H / 2 + 10, 120, 34
    circ = 2 * math.pi * R
    gap = 2.5 if n > 1 else 0

    segs, acc = [], 0.0
    for i, (lang, v) in enumerate(items):
        frac = v / total
        length = max(frac * circ - gap, 0.6)
        color = colors.get(lang, "#6e7681") if lang != "Outras" else Z600
        delay = 0.15 + i * 0.08
        segs.append(
            f'<circle cx="{cx}" cy="{f(cy)}" r="{R}" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-dasharray="0 {f(circ)}" stroke-dashoffset="{f(-acc)}" transform="rotate(-90 {cx} {f(cy)})">'
            f'<animate attributeName="stroke-dasharray" values="0 {f(circ)};{f(length)} {f(circ)}" dur="0.9s" begin="{f(delay)}s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1"/>'
            f'</circle>'
        )
        acc += frac * circ

    legend = []
    lx0, col_w = 450, 360
    bar_w = 140 if cols == 2 else 420
    for i, (lang, v) in enumerate(items):
        col, row = (i // rows, i % rows) if cols == 2 else (0, i)
        x = lx0 + col * col_w
        y = 96 + row * row_h + (0 if cols == 2 else (H - 96 - rows * row_h - 30) / 2)
        pct = v / total * 100
        color = colors.get(lang, "#6e7681") if lang != "Outras" else Z600
        pct_txt = f"{pct:.1f}%" if pct >= 0.1 else "<0.1%"
        bw = max(bar_w * pct / 100 * (100 / (items[0][1] / total * 100)), 2)  # relativo à maior
        delay = 0.3 + i * 0.06
        legend.append(f"""
    <g opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.4s" begin="{f(delay)}s" fill="freeze"/>
      <circle cx="{x + 6}" cy="{f(y - 5)}" r="6" fill="{color}"/>
      <text x="{x + 22}" y="{f(y)}" font-family="{SANS}" font-size="16" fill="#e4e4e7">{esc(lang)}</text>
      <rect x="{x + 150}" y="{f(y - 9)}" width="{bar_w}" height="6" rx="3" fill="{TAG}"/>
      <rect x="{x + 150}" y="{f(y - 9)}" width="0" height="6" rx="3" fill="{color}">
        <animate attributeName="width" values="0;{f(bw)}" dur="0.9s" begin="{f(delay + 0.1)}s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1"/>
      </rect>
      <text x="{x + 150 + bar_w + 12}" y="{f(y)}" font-family="{MONO}" font-size="13" fill="{MUTED}">{esc(pct_txt)}</text>
    </g>""")

    top = items[0][0]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Linguagens: {esc(', '.join(k for k, _ in items))}">
  <defs>
    <filter id="glowBig" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="18"/></filter>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="{BG}"/>
    <text x="32" y="44" font-family="{MONO}" font-size="13" letter-spacing="2" fill="{Z500}">LINGUAGENS · TODOS OS REPOSITÓRIOS</text>
    <circle cx="{cx}" cy="{f(cy)}" r="{R}" fill="none" stroke="{colors.get(top, FG)}" stroke-width="{sw}" opacity="0.12" filter="url(#glowBig)"/>
    <circle cx="{cx}" cy="{f(cy)}" r="{R}" fill="none" stroke="{TAG}" stroke-width="{sw}"/>
    {''.join(segs)}
    <g>
      <animateTransform attributeName="transform" type="rotate" values="0 {cx} {f(cy)};360 {cx} {f(cy)}" dur="40s" repeatCount="indefinite"/>
      <circle cx="{cx}" cy="{f(cy)}" r="{R + sw / 2 + 12}" fill="none" stroke="{BORDER}" stroke-dasharray="2 9"/>
    </g>
    <text x="{cx}" y="{f(cy + 2)}" text-anchor="middle" font-family="{SANS}" font-size="46" font-weight="700" fill="{FG}">{len(totals)}</text>
    <text x="{cx}" y="{f(cy + 28)}" text-anchor="middle" font-family="{SANS}" font-size="15" fill="{MUTED}">linguagens</text>
    <line x1="410" x2="410" y1="70" y2="{H - 40}" stroke="{BORDER}"/>
    {''.join(legend)}
  </g>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{BORDER}"/>
</svg>"""
    return svg


if __name__ == "__main__":
    totals = collect()
    if not totals:
        print("nenhuma linguagem encontrada; mantendo o arquivo anterior")
        sys.exit(0)
    colors = {} if MOCK else linguist_colors()
    if MOCK:
        colors = {"TypeScript": "#3178c6", "JavaScript": "#f1e05a", "CSS": "#663399", "HTML": "#e34c26",
                  "Python": "#3572A5", "C": "#555555", "Java": "#b07219", "SCSS": "#c6538c", "Shell": "#89e051",
                  "C++": "#f34b7d", "PLpgSQL": "#336790", "Dart": "#00B4AB", "MDX": "#fcb32c"}
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(render(totals, colors))
    print("gerado:", OUT)
