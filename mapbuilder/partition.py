"""Divide each territory outline into region cells around a point per region.

Region borders are not available as data: the wiki's regional maps are hand-drawn pictures.
Each region is therefore anchored at the position of its name label on that picture (read by
eye into map/region_labels.json) and the territory's real outline is split by nearest anchor.
Regions end up in the right place relative to each other; their borders are approximate.
"""
from __future__ import annotations

import json
import math
import re

import cv2
import numpy as np

from .geometry import MAP_DIR, territory_polygons
from .regions import territory_regions

SCALE = 4  # raster resolution relative to master-map pixels
COMPASS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}


def _mask(polys, x0, y0, w, h):
    mask = np.zeros((h, w), np.uint8)
    for poly in polys:
        pts = np.array([[(x - x0) * SCALE, (y - y0) * SCALE] for x, y in poly], np.int32)
        cv2.fillPoly(mask, [pts], 1)
    return mask


def _inside_point(mask, x, y):
    """Nearest pixel inside the mask to (x, y)."""
    h, w = mask.shape
    xi, yi = int(round(min(max(x, 0), w - 1))), int(round(min(max(y, 0), h - 1)))
    if mask[yi, xi]:
        return float(xi), float(yi)
    ys, xs = np.nonzero(mask)
    k = int(np.argmin((xs - x) ** 2 + (ys - y) ** 2))
    return float(xs[k]), float(ys[k])


def compass_hint(text: str):
    """(dx, dy) in -1..1 from direction words early in a region's description, or None."""
    head = " ".join(text.split()[:60]).lower()
    dx = dy = 0.0
    found = False
    for word, (vx, vy) in COMPASS.items():
        if re.search(rf"\b{word}(ern|-?east|-?west)?\b", head):
            dx += vx
            dy += vy
            found = True
    for a, b in (("north", "east"), ("north", "west"), ("south", "east"), ("south", "west")):
        if re.search(rf"\b{a}-?{b}", head):
            dx += COMPASS[b][0]
            found = True
    return (max(-1, min(1, dx)), max(-1, min(1, dy))) if found else None


def partition(polys, seeds):
    """polys: territory polygons (master px). seeds: {name: (x, y)} in master px.
    Returns {name: {"polys": [[[x, y], ...]], "centre": [x, y]}}."""
    xs = [p[0] for poly in polys for p in poly]
    ys = [p[1] for poly in polys for p in poly]
    x0, y0 = min(xs) - 2, min(ys) - 2
    w, h = int((max(xs) - x0 + 4) * SCALE), int((max(ys) - y0 + 4) * SCALE)
    mask = _mask(polys, x0, y0, w, h)
    names = list(seeds)
    pts = []
    for n in names:
        sx, sy = _inside_point(mask, (seeds[n][0] - x0) * SCALE, (seeds[n][1] - y0) * SCALE)
        pts.append((sx, sy))
    # nudge coincident anchors apart so every region gets a cell
    for i in range(len(pts)):
        for j in range(i):
            if abs(pts[i][0] - pts[j][0]) + abs(pts[i][1] - pts[j][1]) < 3:
                pts[i] = _inside_point(mask, pts[i][0] + 6 * (i + 1), pts[i][1] + 4 * (i + 1))
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.stack([(xx - px) ** 2 + (yy - py) ** 2 for px, py in pts])
    owner = np.argmin(dist, axis=0)
    out = {}
    for k, n in enumerate(names):
        cell = ((owner == k) & (mask == 1)).astype(np.uint8)
        contours, _ = cv2.findContours(cell, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        shapes = []
        for c in sorted(contours, key=cv2.contourArea, reverse=True):
            if cv2.contourArea(c) < 12 * SCALE * SCALE and shapes:
                continue
            c = cv2.approxPolyDP(c, 0.45 * SCALE, True)
            if len(c) >= 3:
                shapes.append([[round(float(p[0][0]) / SCALE + x0, 1), round(float(p[0][1]) / SCALE + y0, 1)] for p in c])
        ys_, xs_ = np.nonzero(cell)
        centre = [round(float(xs_.mean()) / SCALE + x0, 1), round(float(ys_.mean()) / SCALE + y0, 1)] if len(xs_) else None
        out[n] = {"polys": shapes, "centre": centre, "area": int(cell.sum() / SCALE / SCALE)}
    return out


def region_shapes(labels: dict | None = None) -> dict:
    """{territory: {region: {"polys", "centre", "placed"}}} for every territory with regions."""
    terr = territory_polygons()
    regions = territory_regions()
    labels = labels or {}
    from scraper.common import DATA, read_json
    from .regions import page_body
    pages = read_json(DATA / "pages.json")
    result = {}
    for t, rs in regions.items():
        if not rs:
            continue
        polys = terr[t]["polys"]
        xs = [p[0] for poly in polys for p in poly]
        ys = [p[1] for poly in polys for p in poly]
        bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
        cx, cy, hw, hh = (bx0 + bx1) / 2, (by0 + by1) / 2, (bx1 - bx0) / 2, (by1 - by0) / 2
        lab = labels.get(t, {})
        pts = {n: p for n, p in (lab.get("regions") or {}).items() if p}
        seeds, placed = {}, {}
        if len(pts) >= 2:
            # map the picture's label cloud onto the outline's box, with a margin
            lx = [p[0] for p in pts.values()]
            ly = [p[1] for p in pts.values()]
            ext = lab.get("extent") if not lab.get("cropped") else None
            if ext and ext[2] - ext[0] > 5 and ext[3] - ext[1] > 5:
                l, tp, r, b = ext
                fx = lambda x: bx0 + (x - l) / (r - l) * (bx1 - bx0)
                fy = lambda y: by0 + (y - tp) / (b - tp) * (by1 - by0)
            else:
                sx = (max(lx) - min(lx)) or 1
                sy = (max(ly) - min(ly)) or 1
                fx = lambda x: cx + ((x - min(lx)) / sx - 0.5) * 2 * hw * 0.68
                fy = lambda y: cy + ((y - min(ly)) / sy - 0.5) * 2 * hh * 0.68
            for n, p in pts.items():
                seeds[n] = (fx(p[0]), fy(p[1]))
                placed[n] = "label"
        body = page_body(pages[t])
        sec = re.search(r"^## Regions[^\n]*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
        texts = {}
        if sec:
            for s in re.split(r"^### ", sec.group(1), flags=re.M)[1:]:
                head, _, rest = s.partition("\n")
                texts[re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", head).strip()] = rest
        missing = [r["name"] for r in rs if r["name"] not in seeds]
        for k, n in enumerate(missing):
            hint = compass_hint(texts.get(n, ""))
            if hint:
                seeds[n] = (cx + hint[0] * hw * 0.55, cy + hint[1] * hh * 0.55)
                placed[n] = "compass"
            else:  # spread the rest on a ring so each gets a cell
                ang = 2 * math.pi * (k + 0.5) / max(1, len(missing))
                seeds[n] = (cx + math.cos(ang) * hw * 0.4, cy + math.sin(ang) * hh * 0.4)
                placed[n] = "even"
        cells = partition(polys, seeds)
        for n in cells:
            cells[n]["placed"] = placed[n]
        result[t] = cells
    return result


if __name__ == "__main__":
    lab_path = MAP_DIR / "region_labels.json"
    labels = json.loads(lab_path.read_text()) if lab_path.exists() else {}
    shapes = region_shapes(labels)
    (MAP_DIR / "region_shapes.json").write_text(json.dumps(shapes, ensure_ascii=False))
    import collections
    how = collections.Counter(c["placed"] for t in shapes.values() for c in t.values())
    empty = [(t, n) for t, cs in shapes.items() for n, c in cs.items() if not c["polys"]]
    print("territories:", len(shapes), "| regions:", sum(len(v) for v in shapes.values()), "| placed by:", dict(how), "| regions with no cell:", empty)
