#!/usr/bin/env python3
"""Fetch real contribution data (no token) and render the animated heatmap SVG.
Used once locally and daily by the GitHub Actions workflow."""
import os
import re
import sys

import requests

USERNAME = os.environ.get("GH_USERNAME", "RehmatUllah-khan")
OUT = os.environ.get("HEATMAP_OUT", "contrib-heatmap.svg")

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
CELL, GAP, RX = 11, 3, 2.5
BG = "#0d1117"
FG = "#c9d1d9"
DIM = "#8b949e"


def fetch_grid(username):
    url = f"https://github.com/users/{username}/contributions"
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).text
    rows = re.findall(r'<tr style="height: 11px">(.*?)</tr>', html, re.S)
    grid = []  # grid[weekday] = list of (date, level)
    for r in rows[:7]:
        grid.append(re.findall(r'data-date="([^"]+)"[^>]*data-level="(\d+)"', r))
    return grid


def render(grid, out):
    weeks = max(len(g) for g in grid)
    W = weeks * (CELL + GAP) + 2 * GAP + 8
    H = 7 * (CELL + GAP) + 64
    top = 14
    active = sum(1 for g in grid for _, lv in g if int(lv) > 0)

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="contribution heatmap">',
        "<style>",
        "@keyframes drop { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }",
        ".cell { opacity: 0; animation: drop 0.35s ease-out forwards; }",
        "</style>",
        f'<rect x="0" y="0" width="{W}" height="{H}" rx="8" fill="{BG}"/>',
    ]
    for wd in range(7):
        for wi, (date, lv) in enumerate(grid[wd]):
            x = 8 + wi * (CELL + GAP)
            y = top + wd * (CELL + GAP)
            delay = (wi + wd) * 0.018
            color = PALETTE[min(int(lv), 4)]
            p.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{RX}" '
                f'fill="{color}" style="animation-delay: {delay:.3f}s"><title>{date}</title></rect>'
            )
    # legend
    lx = W - 150
    ly = H - 34
    p.append(f'<text x="{lx}" y="{ly + 9}" fill="{DIM}" font-size="11" font-family="ui-monospace, monospace">Less</text>')
    for i, c in enumerate(PALETTE):
        p.append(f'<rect x="{lx + 36 + i * 15}" y="{ly}" width="11" height="11" rx="2.5" fill="{c}"/>')
    p.append(f'<text x="{lx + 36 + 5 * 15 + 6}" y="{ly + 9}" fill="{DIM}" font-size="11" font-family="ui-monospace, monospace">More</text>')
    day_word = "day" if active == 1 else "days"
    p.append(
        f'<text x="12" y="{H - 24}" fill="{FG}" font-size="12" font-family="ui-monospace, monospace">'
        f"{active} active {day_word} in the last year · refreshes daily</text>"
    )
    p.append("</svg>")
    open(out, "w").write("\n".join(p))
    print(f"wrote {out} ({weeks} weeks, {active} active days)")


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    render(fetch_grid(username), OUT)


if __name__ == "__main__":
    main()
