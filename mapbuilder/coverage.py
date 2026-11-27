"""One clean set of land shapes, built top-down so every edge exists once and is shared exactly.

1. Land: the union of every territory outline from the wiki's map, with the thin slivers between
   neighbouring outlines closed.
2. Territories: each outline keeps its own ground (overlaps go to one side); each sliver between
   neighbours is split down its middle (a Voronoi split from points along both edges), so the
   territories tile the land with no gaps or overlaps.
3. Regions: each territory is cut into its regions with straight lines halfway between the regions'
   anchor points (the label positions read from the wiki's region maps), a Voronoi split clipped to
   the territory. Regions therefore tile their territory exactly. A territory drawn as separate parts
   with one region per part (Otkodov) gives each region its part.

The Great Sinkhole (opened 381YE Summer) is a hole in the land from then on. Before that its ground is
shared between the neighbouring territories in straight wedges from its centre, and those territories'
regions are cut again, so only the territories around the pit differ between the two eras.
"""
from __future__ import annotations

import collections

import shapely
import shapely.ops
from shapely.geometry import MultiPoint, Point, Polygon
from shapely.ops import unary_union

GAP = 4.0     # master-map pixels: slivers up to twice this wide between territories are closed
GRID = 0.01   # coordinates are snapped to this grid so shared edges match exactly
SPECK = 6.0   # pieces and holes smaller than this (square master pixels) are dropped
SIMPLIFY = 0.35  # master pixels: how far a simplified edge may move


def _poly(rings):
    ps = [Polygon(r).buffer(0) for r in rings if len(r) >= 3]
    return unary_union([p for p in ps if not p.is_empty])


def _clean(g, speck=SPECK):
    """Snap to the grid, drop specks and tiny holes (speck=0 keeps every piece)."""
    if g is None or g.is_empty:
        return Polygon()
    g = shapely.set_precision(g.buffer(0), GRID)
    parts = []
    for p in getattr(g, "geoms", [g]):
        if p.geom_type != "Polygon" or p.area < max(speck, 1e-4):
            continue
        parts.append(Polygon(p.exterior, [h for h in p.interiors if Polygon(h).area >= speck]))
    return unary_union(parts) if parts else Polygon()


def _edge_points(owners: dict, zone, step=0.75):
    """Points every `step` px along each owner's edge inside `zone`: ([Point], [owner])."""
    pts, own, seen = [], [], set()
    for k, g in owners.items():
        if g.is_empty or not g.intersects(zone):
            continue
        edge = g.boundary.intersection(zone)
        for seg in getattr(edge, "geoms", [edge]):
            if seg.is_empty or seg.length == 0:
                continue
            n = max(1, int(seg.length / step))
            for i in range(n + 1):
                q = seg.interpolate(i / n, normalized=True)
                key = (round(q.x, 2), round(q.y, 2))
                if key not in seen:
                    seen.add(key); pts.append(q); own.append(k)
    return pts, own


def _split_medial(area, owners: dict) -> dict:
    """Share `area` (slivers between owners) out so each bit goes to the owner whose edge is nearest:
    a split down the middle of every sliver."""
    out = collections.defaultdict(list)
    if area.is_empty:
        return out
    pts, own = _edge_points(owners, area.buffer(1.5))
    if not pts:
        return out
    cells = shapely.voronoi_polygons(MultiPoint(pts), extend_to=area.envelope.buffer(10), ordered=True)
    parts = list(getattr(area, "geoms", [area]))
    tree = shapely.STRtree(parts)
    for k, cell in zip(own, cells.geoms):
        for i in tree.query(cell):
            piece = cell.intersection(parts[int(i)])
            if not piece.is_empty and piece.area > 0:
                out[k].append(piece)
    return out


def _split_wedges(hole, owners: dict) -> dict:
    """Share `hole` out among the owners around its rim, as straight wedges from its centre."""
    out = collections.defaultdict(list)
    near = hole.buffer(2.0)
    cand = [k for k, g in owners.items() if not g.is_empty and g.intersects(near)]
    if not cand:
        return out
    ring = (hole if hole.geom_type == "Polygon" else max(hole.geoms, key=lambda g: g.area)).exterior
    n = max(60, int(ring.length * 2))
    pts = [ring.interpolate(i / n, normalized=True) for i in range(n)]
    own = [min(cand, key=lambda k: owners[k].distance(q)) for q in pts]
    s0 = next((i for i in range(n) if own[i] != own[i - 1]), 0)
    own, pts = own[s0:] + own[:s0], pts[s0:] + pts[:s0]
    for _ in range(6):  # a neighbour touching under an eighth of the rim gets no wedge (no thin slivers)
        runs, i0 = [], 0
        for i in range(1, n + 1):
            if i == n or own[i] != own[i0]:
                runs.append((i0, i)); i0 = i
        short = [r for r in runs if r[1] - r[0] < n / 8]
        if not short or len(runs) <= 1:
            break
        for i in range(*short[0]):
            own[i] = own[(short[0][0] - 1) % n]
    c = hole.centroid
    arc, k0 = [pts[0]], own[0]
    for j in range(1, n + 1):
        i = j % n
        arc.append(pts[i])
        if own[i] != k0 or j == n:
            wedge = Polygon([(c.x, c.y)] + [(q.x, q.y) for q in arc]).buffer(0).intersection(hole)
            if not wedge.is_empty:
                out[k0].append(wedge)
            arc, k0 = [pts[i]], own[i]
    return out


def _regions(shape, cells: dict) -> dict:
    """Cut a territory shape into its regions. cells: {region: {"seed", "per_part", ...}}."""
    names = list(cells)
    if len(names) == 1:
        return {names[0]: shape}
    parts = list(getattr(shape, "geoms", [shape]))
    if any(c.get("per_part") for c in cells.values()) and len(parts) >= len(names):
        out = {n: [] for n in names}  # one region per part: each part goes to the region whose seed is nearest
        for p in parts:
            n = min(names, key=lambda n: p.distance(Point(cells[n]["seed"])))
            out[n].append(p)
        return {n: _clean(unary_union(v), 0) for n, v in out.items()}
    inner = shape.buffer(-1)
    inner = inner if not inner.is_empty else shape
    seeds, used = [], set()
    for n in names:
        x, y = cells[n].get("seed") or cells[n].get("centre") or shape.representative_point().coords[0]
        q = Point(x, y)
        if not shape.contains(q):  # a seed outside the outline: pull it just inside
            q = shapely.ops.nearest_points(inner, q)[0]
        key = (round(q.x, 1), round(q.y, 1))
        while key in used:  # coincident anchors: nudge apart
            q = Point(q.x + 1.3, q.y + 0.9)
            key = (round(q.x, 1), round(q.y, 1))
        used.add(key)
        seeds.append(q)
    vor = shapely.voronoi_polygons(MultiPoint(seeds), extend_to=shape.envelope.buffer(50), ordered=True)
    return {n: _clean(cell.intersection(shape), 0) for n, cell in zip(names, vor.geoms)}


def _territories(terr: dict, seas: set, pit=None):
    """{territory: shape} tiling the land (the pit cut out, if given)."""
    raw = {t: _poly(info["polys"]) for t, info in sorted(terr.items()) if t not in seas}
    placed, acc = {}, Polygon()
    for t in sorted(raw, key=lambda t: -raw[t].area):  # overlaps stay with the bigger territory
        placed[t] = raw[t].difference(acc).buffer(0)
        acc = unary_union([acc, placed[t]])
    land = unary_union(list(placed.values()))
    closed = land.buffer(GAP, join_style="mitre", mitre_limit=3).buffer(-GAP, join_style="mitre", mitre_limit=3)
    gaps = closed.difference(land)
    if pit is not None:
        gaps = gaps.difference(pit)
    grow = _split_medial(gaps, placed)
    out = {t: unary_union([g, *grow.get(t, [])]) for t, g in placed.items()}
    if pit is not None:
        out = {t: g.difference(pit) for t, g in out.items()}
    out = {t: _clean(g) for t, g in out.items()}
    # thin out the vertices the gap splitting adds, keeping shared edges identical on both sides
    names = list(out)
    simple = shapely.coverage_simplify([out[t] for t in names], tolerance=SIMPLIFY)
    return {t: _clean(g) for t, g in zip(names, simple)}


def build(terr: dict, shapes: dict, seas: set, pit=None):
    """{"after": {(t, r): shape}, "before": {...}}, r == "" for territories without regions.
    "after" has the pit as a hole; "before" shares its ground among the neighbouring territories."""
    after_t = _territories(terr, seas, pit)
    before_t = dict(after_t)
    if pit is not None and not pit.is_empty:
        for t, pieces in _split_wedges(pit, after_t).items():
            before_t[t] = _clean(unary_union([after_t[t], *pieces]))

    def cut(tshapes, reuse=None):
        out = {}
        for t, g in tshapes.items():
            if reuse is not None and reuse[0][t] is g:  # unchanged territory: same regions
                out.update({k: v for k, v in reuse[1].items() if k[0] == t})
            elif shapes.get(t):
                for r, cell in _regions(g, shapes[t]).items():
                    out[(t, r)] = cell
            else:
                out[(t, "")] = g
        return out

    after = cut(after_t)
    before = cut(before_t, (after_t, after))
    return {"after": after, "before": before}


def rings(geom, nd=1):
    """Polygon/MultiPolygon -> [[[x, y], ...], ...] (exteriors and holes, as the page draws them)."""
    out = []
    for g in getattr(geom, "geoms", [geom]):
        if g.is_empty or g.geom_type != "Polygon" or g.area < 0.05:
            continue
        for ring in [g.exterior, *[h for h in g.interiors if Polygon(h).area >= 0.05]]:
            pts = [[round(x, nd), round(y, nd)] for x, y in list(ring.coords)[:-1]]
            if len(pts) >= 3:
                out.append(pts)
    return out


def union(geoms):
    return _clean(unary_union([g for g in geoms if g is not None and not g.is_empty]), 0)


def path(geom) -> str:
    """SVG path data for a geometry's rings."""
    return "".join("M" + "L".join(f"{x} {y}" for x, y in ring) + "Z" for ring in rings(geom))
