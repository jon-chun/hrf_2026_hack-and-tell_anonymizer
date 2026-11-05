#!/usr/bin/env python3
"""Build the manual's two charts as SVG. Edit priorities are read from the saved report; test results are listed below."""
import html, re
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPORT = HERE.parents[1] / "revisions/version_20261104-1652/DIFF_REPORT.md"
INK, MUTED, GRID, BG, BLUE, GRAY = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff", "#2a78d6", "#a9a8a2"
FONT = "Helvetica, Arial, sans-serif"

def text(x, y, s, size=15, fill=INK, anchor="start", weight="normal"):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{html.escape(s)}</text>')

def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<rect width="{w}" height="{h}" fill="{BG}"/>' + "".join(body) + "</svg>\n")

def bar(x, y, value, scale, height, color):
    width = max(value * scale, 2)
    return (f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="4" fill="{color}"/>', x + width)

def leak_chart():
    # (group, stage, leaked, known). Measured on synthetic documents; see docs/MANUAL.md section 2.11.
    groups = [("Blind set 2: final rules, the result to trust", BLUE, [("Layers 1 and 2", 10, 81), ("After one audit round", 0, 81)]),
              ("Blind set 1: tuned on this set, so not blind", GRAY, [("Layers 1 and 2", 21, 194), ("After audit rounds", 2, 194)]),
              ("Blind set 1: before any tuning", GRAY, [("Layers 1 and 2", 59, 194)])]
    w, left, scale = 860, 210, 13.0
    body, y = [text(24, 36, "Share of known sensitive values still leaked", 20, weight="bold"),
               text(24, 60, "Lower is better. Small synthetic tests, not a guarantee.", 14, MUTED)], 92
    for title, color, rows in groups:
        body.append(text(24, y, title, 15, weight="bold")); y += 12
        for label, leaked, known in rows:
            r, end = bar(left, y, 100 * leaked / known, scale, 24, color)
            body += [text(40, y + 17, label, 14, MUTED), r,
                     text(end + 10, y + 17, f"{leaked} of {known} ({100 * leaked / known:.0f}%)", 14)]
            y += 34
        y += 22
    return svg(w, y - 12, body)

def priority_chart():
    edits = re.findall(r"^### \d+\. (.+?) — ([\d.]+)$", REPORT.read_text(encoding="utf-8"), re.M)
    assert len(edits) == 7, len(edits)
    w, left, scale = 860, 370, 40.0
    body, y = [text(24, 36, "Ranked edits for the fictional proposal", 20, weight="bold"),
               text(24, 60, "Higher means fix sooner. These are editorial priorities, not funding probabilities.", 14, MUTED)], 90
    for title, score in edits:
        r, end = bar(left, y, float(score), scale, 24, BLUE)
        body += [text(24, y + 17, title, 14), r, text(end + 10, y + 17, score, 14)]
        y += 36
    return svg(w, y + 10, body)

(HERE / "leak-results.svg").write_text(leak_chart(), encoding="utf-8")
(HERE / "edit-priorities.svg").write_text(priority_chart(), encoding="utf-8")
