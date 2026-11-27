"""Per-season border outlines (Imperial, barbarian and neutral lands) and nation label positions.

Both are computed from a raster of the map's cells (regions, or whole territories that have
no regions). Small slivers between neighbouring territories, left by the wiki's image-map
polygons not quite meeting, are closed first so that one power's adjacent lands join up.
"""
from __future__ import annotations

import cv2
import numpy as np

S = 2            # raster pixels per master-map pixel for outlines
GAP = 4          # master pixels: slivers narrower than this between territories are closed
MIN_RING = 40    # raster pixels: smaller outline rings are dropped
MIN_LABEL = 900  # master pixels: smaller blocks of land get no nation label


def _cells(terr, shapes, seas):
    """[(territory, region or "", polys)] for every land cell."""
    out = []
    for t, info in sorted(terr.items()):
        if t in seas:
            continue
        if shapes.get(t):
            out += [(t, r, c["polys"]) for r, c in shapes[t].items()]
        else:
            out.append((t, "", info["polys"]))
    return out


def _raster(cells, origin, size, scale):
    x0, y0 = origin
    ids = np.zeros(size, np.int32)
    for k, (_, _, polys) in enumerate(cells, 1):
        pts = [np.round((np.array(p, float) - (x0, y0)) * scale).astype(np.int32) for p in polys]
        cv2.fillPoly(ids, pts, k)
    land = (ids > 0).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (GAP * scale * 2 + 1,) * 2)
    closed = cv2.morphologyEx(land, cv2.MORPH_CLOSE, kernel)
    gaps = (closed == 1) & (land == 0)
    if gaps.any():  # give each sliver pixel the nearest cell's id
        _, lab = cv2.distanceTransformWithLabels((land == 0).astype(np.uint8), cv2.DIST_L2, 5,
                                                 labelType=cv2.DIST_LABEL_PIXEL)
        zy, zx = np.nonzero(land)  # cell pixels: each carries its own label
        lut = np.zeros(lab.max() + 1, np.int32)
        lut[lab[zy, zx]] = ids[zy, zx]
        ids[gaps] = lut[lab[gaps]]
    return ids


def _path(contours, hierarchy, origin, scale):
    x0, y0 = origin
    parts = []
    for c in contours:
        if cv2.contourArea(c) < MIN_RING:
            continue
        c = cv2.approxPolyDP(c, 0.9, True)
        if len(c) < 3:
            continue
        pts = [f"{p[0][0] / scale + x0:.1f} {p[0][1] / scale + y0:.1f}" for p in c]
        parts.append("M" + "L".join(pts) + "Z")
    return "".join(parts)


def compute(terr, shapes, state, seasons, seas, side_of, view, short_name):
    """Return ({"states": [...], "season": [...]}, nation labels per season)."""
    cells = _cells(terr, shapes, seas)
    origin = (view[0], view[1])
    size2 = (int(view[3] * S) + 2, int(view[2] * S) + 2)
    size1 = (int(view[3]) + 2, int(view[2]) + 2)
    ids2 = _raster(cells, origin, size2, S)
    ids1 = _raster(cells, origin, size1, 1)

    holder_at = [[state[t][r][i] for (t, r, _) in cells] for i in range(len(seasons))]
    states, season_state, seen = [], [], {}
    labels, label_cache = [], {}
    for i in range(len(seasons)):
        hs = holder_at[i]
        # ---- frontier outlines
        # every piece of land is Imperial, barbarian or neutral (the vallorn, uncontrolled land, other powers)
        sides = tuple(side_of(h) or (None if h in ("Unknown", "unknown") else "neu") for h in hs)
        key = tuple(hs)
        if key not in seen:
            lut = np.array([0] + [{"imp": 1, "barb": 2, "neu": 3}.get(s, 0) for s in sides], np.uint8)
            grp = lut[ids2]
            st = {}
            for code, key in ((1, "imp"), (2, "barb"), (3, "neu")):
                m = (grp == code).astype(np.uint8)
                cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
                st[key] = _path(cs, hier, origin, S)
            # every holder's own outline, so neighbouring nations on the same side are divided too
            # ("impAll" etc.; the side outlines above are the clip that keeps each colour on its side)
            hidx = {}
            for h, sd in zip(hs, sides):
                if sd:
                    hidx.setdefault(h, (len(hidx) + 1, sd))
            hl = np.array([0] + [hidx[h][0] if h in hidx else 0 for h in hs], np.int32)[ids2]
            parts = {"imp": [], "barb": [], "neu": []}
            for h, (k, sd) in hidx.items():
                cs, hier = cv2.findContours((hl == k).astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
                parts[sd].append(_path(cs, hier, origin, S))
            for sd, ps in parts.items():
                st[sd + "All"] = "".join(ps)
            seen[key] = len(states)
            states.append(st)
        season_state.append(seen[key])
        # ---- nation labels: one per connected block of a holder's land
        key = tuple(hs)
        if key not in label_cache:
            names = sorted({h for h in hs if short_name(h)})
            index = {h: k for k, h in enumerate(names, 1)}
            lut = np.array([0] + [index.get(h, 0) for h in hs], np.int32)
            hr = lut[ids1]
            out = []
            for h, k in index.items():
                m = (hr == k).astype(np.uint8)
                n, comp, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
                for c in range(1, n):
                    x, y, w, hgt, area = stats[c]
                    if area < MIN_LABEL:
                        continue
                    crop = (comp[y:y + hgt, x:x + w] == c).astype(np.uint8)
                    crop = cv2.copyMakeBorder(crop, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
                    dist = cv2.distanceTransform(crop, cv2.DIST_L2, 5)
                    py, px = np.unravel_index(int(np.argmax(dist)), dist.shape)
                    out.append([h, round(float(px - 1 + x + origin[0]), 1), round(float(py - 1 + y + origin[1]), 1),
                                round(float(dist.max()), 1), int(area), int(w)])
            out.sort(key=lambda r: -r[4])
            label_cache[key] = out
        labels.append(label_cache[key])
    return {"states": states, "season": season_state}, labels
