"""One clean, gap-free set of shapes for every piece of land, so all the map's lines agree.

The wiki's territory outlines (an image map) don't quite meet: there are slivers between neighbours and
small overlaps. Drawn as they are, close up you get doubled or offset lines. Here every land cell (a
region, or a whole territory that has no regions) is:
  1. made disjoint from the cells already placed (overlaps go to one side only);
  2. grown into the slivers next to it: the gaps that closing the land surface fills are triangulated
     and each triangle given to the nearest cell.
Neighbouring cells then share exactly the same edge, and territory outlines and each holder's border
are unions of the same cells.

Some map features change the land itself. The Great Sinkhole opened in 381YE Summer where four
territories met; before that the pit's ground is shared out among the neighbouring cells, and from
then on it is a hole that belongs to no one. That gives two eras of geometry.
"""
from __future__ import annotations

import collections

import shapely
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

GAP = 4.0  # master-map pixels: slivers up to twice this wide between land cells are closed


def _poly(rings):
    ps = [Polygon(r).buffer(0) for r in rings if len(r) >= 3]
    return unary_union([p for p in ps if not p.is_empty])


def _rings(geom, nd=1):
    """Polygon/MultiPolygon -> [[[x, y], ...], ...] (exteriors and holes, as the page draws them)."""
    out = []
    geoms = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    for g in geoms:
        if g.is_empty or g.area < 6:  # specks left by the shape operations
            continue
        for ring in [g.exterior, *[h for h in g.interiors if Polygon(h).area >= 6]]:
            pts = [[round(x, nd), round(y, nd)] for x, y in list(ring.coords)[:-1]]
            if len(pts) >= 3:
                out.append(pts)
    return out


def _fill_gaps(cells: dict, extra_free=None) -> dict:
    """cells: {key: geometry}. Returns disjoint cells grown into the slivers between them (and into
    extra_free, ground that belongs to no cell yet)."""
    keys = list(cells)
    placed, acc = {}, None
    for k in keys:  # disjoint: overlaps go to the cell placed first
        g = cells[k] if acc is None else cells[k].difference(acc)
        placed[k] = g.buffer(0)
        acc = g if acc is None else unary_union([acc, g])
    land = unary_union(list(placed.values()))
    closed = land.buffer(GAP, join_style="mitre", mitre_limit=3).buffer(-GAP, join_style="mitre", mitre_limit=3)
    free = closed.difference(land)
    if extra_free is not None:
        free = unary_union([free, extra_free.difference(land)])
    if free.is_empty:
        return placed
    tree_keys = [k for k in keys if not placed[k].is_empty]
    tree = STRtree([placed[k] for k in tree_keys])
    grow = {k: [] for k in keys}
    tris = shapely.constrained_delaunay_triangles(free)
    for tri in getattr(tris, "geoms", [tris]):
        if tri.is_empty or tri.area < 1e-6:
            continue
        i = tree.nearest(tri.centroid)
        grow[tree_keys[int(i)]].append(tri)
    return {k: unary_union([placed[k], *grow[k]]).buffer(0) if grow[k] else placed[k] for k in keys}


def build(terr: dict, shapes: dict, seas: set, pit=None):
    """Returns {"after": {(t, r): geom}, "before": {...}} with r == "" for territories without regions.
    pit: the Great Sinkhole's geometry (or None). "after" is the map with the pit as a hole; "before"
    shares the pit's ground out among its neighbours."""
    base = {}
    for t, info in sorted(terr.items()):
        if t in seas:
            continue
        if shapes.get(t):
            for r, c in shapes[t].items():
                base[(t, r)] = _poly(c["polys"])
        else:
            base[(t, "")] = _poly(info["polys"])
    if pit is None or pit.is_empty:
        g = _fill_gaps(base)
        return {"after": g, "before": g}
    after = _fill_gaps({k: v.difference(pit) for k, v in base.items()})
    after = {k: v.difference(pit).buffer(0) for k, v in after.items()}
    # before the pit opened: the territories met where it is now. Walk round the pit's rim, give each
    # stretch of rim to the neighbouring cell it touches, and cut the pit into straight wedges from its
    # centre, so each neighbour just extends inward to meet the others in the middle.
    near = pit.buffer(2.0)
    cand = [k for k, g in after.items() if not g.is_empty and g.intersects(near)]
    grow = collections.defaultdict(list)
    if cand:
        ring = pit.exterior if pit.geom_type == "Polygon" else max(pit.geoms, key=lambda g: g.area).exterior
        n = max(60, int(ring.length * 2))
        pts = [ring.interpolate(i / n, normalized=True) for i in range(n)]
        own = [min(cand, key=lambda k: after[k].distance(q)) for q in pts]
        st0 = next((i for i in range(n) if own[i] != own[i - 1]), 0)  # count from where an owner's stretch begins
        own, pts = own[st0:] + own[:st0], pts[st0:] + pts[:st0]
        # a neighbour touching only a short stretch of rim (under an eighth of it) gets no wedge: its
        # stretch joins the stretch before it, so there are no thin slivers reaching the centre
        for _ in range(4):
            runs, i0 = [], 0
            for i in range(1, n + 1):
                if i == n or own[i] != own[i0]:
                    runs.append((i0, i)); i0 = i
            short = [r for r in runs if r[1] - r[0] < n / 8]
            if not short or len(runs) <= 1:
                break
            a0, a1 = short[0]
            for i in range(a0, a1):
                own[i] = own[(a0 - 1) % n]
        c = pit.centroid
        start = next((i for i in range(n) if own[i] != own[i - 1]), 0)  # begin at a change of owner
        arc, k0 = [pts[start]], own[start]
        for j in range(1, n + 1):
            i = (start + j) % n
            arc.append(pts[i])
            if own[i] != k0 or j == n:
                wedge = Polygon([(c.x, c.y)] + [(q.x, q.y) for q in arc]).buffer(0).intersection(pit)
                if not wedge.is_empty:
                    grow[k0].append(wedge)
                arc, k0 = [pts[i]], own[i]
    before = {k: (unary_union([v, *grow[k]]).buffer(0) if grow.get(k) else v) for k, v in after.items()}
    return {"after": after, "before": before}


def rings(geom):
    return _rings(geom)


def union(geoms):
    return unary_union([g for g in geoms if g is not None and not g.is_empty])


def path(geom) -> str:
    """SVG path data for a geometry's rings."""
    parts = []
    for ring in _rings(geom):
        parts.append("M" + "L".join(f"{x} {y}" for x, y in ring) + "Z")
    return "".join(parts)
