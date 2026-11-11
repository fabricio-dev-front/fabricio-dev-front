#!/usr/bin/env python3
"""Ajustes nos SVGs gerados pelas Actions.

- Calendário 3D: remove o donut de linguagens (o README tem um gráfico próprio)
  e adiciona uma entrada suave (fade).
- Cobrinha: remove a barra de progresso e reduz a altura.
"""
import re
import sys


def remove_group(s, opening):
    """Remove o <g> que começa com `opening`, incluindo os <g> aninhados."""
    start = s.find(opening)
    if start < 0:
        return s, False
    depth, i = 0, start
    tag = re.compile(r"<g[\s>]|</g>")
    while True:
        m = tag.search(s, i)
        if not m:
            return s, False
        if m.group(0) == "</g>":
            depth -= 1
            if depth == 0:
                return s[:start] + s[m.end():], True
        else:
            depth += 1
        i = m.end()


FADE = ('<g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.8s" begin="0.1s" fill="freeze"/>'
        '<animateTransform attributeName="transform" type="translate" values="0 16;0 0" dur="0.8s" begin="0.1s" '
        'fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1"/>')


def wrap_body(s):
    """Envolve todo o conteúdo do <svg> (exceto <style>/<defs>) num grupo com fade de entrada."""
    m = re.match(r"(<svg[^>]*>)((?:\s*<style>.*?</style>)?(?:\s*<defs>.*?</defs>)?)", s, re.S)
    if not m or "data-enter" in s:
        return s
    head = m.group(0)
    body_end = s.rfind("</svg>")
    return head + FADE.replace("<g ", '<g data-enter="1" ', 1) + s[len(head):body_end] + "</g></svg>"


def calendar(path):
    s = open(path, encoding="utf-8").read()
    s, ok = remove_group(s, '<g transform="translate(40, 520)">')
    print("donut removido" if ok else "aviso: donut não encontrado")
    s = wrap_body(s)
    open(path, "w", encoding="utf-8").write(s)


def snake(path):
    s = open(path, encoding="utf-8").read()
    s = re.sub(r'<rect class="u [^"]*"[^>]*/>', "", s)
    m = re.search(r'viewBox="(-?[\d.]+) (-?[\d.]+) ([\d.]+) ([\d.]+)" width="([\d.]+)" height="([\d.]+)"', s)
    if m and float(m.group(4)) > 170:
        x, y, w, h = map(float, m.groups()[:4])
        nh = h - 36
        s = s.replace(m.group(0), f'viewBox="{x:g} {y:g} {w:g} {nh:g}" width="{w:g}" height="{nh:g}"', 1)
    open(path, "w", encoding="utf-8").write(s)
    print("barra da cobrinha removida")


if __name__ == "__main__":
    snake(sys.argv[1] if len(sys.argv) > 1 else "dist/snake-green.svg")
