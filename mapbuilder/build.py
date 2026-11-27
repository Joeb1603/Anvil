"""Assemble map/data.json and the page (standalone map/index.html plus an artifact copy)."""
from __future__ import annotations

import collections
import itertools
import json
import re
import sys

import cv2
import numpy as np

from scraper.common import DATA, ROOT, read_json

from . import frontiers
from .events import BREAK_BEFORE
from .geometry import MAP_DIR, extra_territories, territory_polygons

SEAS = {"Bay of Catazar", "Sea of Snow", "The Semmerlak"}
IMPERIAL = ["Dawn", "Highguard", "Imperial Orcs", "Navarr", "The Brass Coast", "The League", "The Marches",
            "Urizen", "Varushka", "Wintermark"]
BARBARIAN = ["Jotun", "Druj", "Grendel", "Thule"]
BARBARIAN_OTHER = {"Lasambrian orcs", "Barrens orcs", "Great Forest Orcs"}  # barbarian orc bands with no colour of their own


def control_files():
    """Campaign-report readings in map/control_raw/, oldest first. territories.json (territory pages)
    and meta.json are handled separately; later files are named after the season they start at."""
    files = [f for f in (MAP_DIR / "control_raw").glob("*.json") if f.stem not in ("territories", "meta")]
    return sorted(files, key=lambda f: (len(f.stem) > 1, f.stem))


def side_of(holder):
    if holder in IMPERIAL or holder == "The Empire":
        return "imp"
    if holder in BARBARIAN or holder in BARBARIAN_OTHER:
        return "barb"
    return None
SLOTS = ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]
# sRGB values of the categorical slots (light theme), used only to keep neighbours apart
SLOT_RGB = {"s1": "257de0", "s2": "f47230", "s3": "00b894", "s4": "f2a600", "s5": "ee7fac", "s6": "008a17",
            "s7": "6a4ce2", "s8": "ec4647"}
ALIASES = {
    "the jotun": "Jotun", "jotun": "Jotun", "the druj": "Druj", "druj": "Druj", "the grendel": "Grendel",
    "grendel": "Grendel", "the thule": "Thule", "thule": "Thule", "brass coast": "The Brass Coast",
    "the brass coast": "The Brass Coast", "league": "The League", "the league": "The League",
    "marches": "The Marches", "the marches": "The Marches", "imperial orcs": "Imperial Orcs",
    "the imperial orcs": "Imperial Orcs", "vallorn": "Vallorn", "the vallorn": "Vallorn",
    "beoraidh (neutral city-state)": "Beoraidh", "beoraidh (city-state)": "Beoraidh",
    "nesustak forest rebels": "Sarangrave rebels", "llofir (eternal)": "Llofir",
}
# colours the wiki's own maps use for each power, taken when no neighbour already has them
PREFERRED = {"Navarr": "s6", "The League": "s4", "The Brass Coast": "s2", "Dawn": "s1", "Wintermark": "s3",
             "Varushka": "s8", "Urizen": "s7", "Highguard": "s5", "Druj": "s5", "Jotun": "s8", "Grendel": "s3",
             "Thule": "s7"}
EMPIRE_WORDS = {"the empire", "empire", "imperial", "imperials", "the imperials"}


def canon(name, nation=None):
    """Normalise a holder name; a bare 'the Empire' becomes the territory's own nation."""
    if not name:
        return None
    key = re.sub(r"\s+", " ", str(name)).strip()
    low = key.lower()
    if low in EMPIRE_WORDS:
        return nation if nation in IMPERIAL else "The Empire"
    for n in IMPERIAL + BARBARIAN:
        if low == n.lower():
            return n
    if low in ALIASES:
        return ALIASES[low]
    for n in BARBARIAN:  # "Jotun (Hierro clan)" and the like
        if re.match(rf"(the )?{n.lower()}\b", low):
            return n
    if low == "unknown":
        return "Unknown"
    if re.match(r"(none|nobody|no one|unclaimed|uninhabited|uncontrolled|contested|disputed|neutral)\b", low):
        return "Uncontrolled"
    return key[:1].upper() + key[1:]


def oklab(hexv):
    r, g, b = (int(hexv[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    l = (0.4122214708 * lin[0] + 0.5363325363 * lin[1] + 0.0514459929 * lin[2]) ** (1 / 3)
    m = (0.2119034982 * lin[0] + 0.6806995451 * lin[1] + 0.1073969566 * lin[2]) ** (1 / 3)
    s = (0.0883024619 * lin[0] + 0.2817188376 * lin[1] + 0.6299787005 * lin[2]) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def delta(a, b):
    return 100 * sum((x - y) ** 2 for x, y in zip(oklab(SLOT_RGB[a]), oklab(SLOT_RGB[b]))) ** 0.5


def adjacency(terr):
    """Pairs of territories whose outlines touch."""
    masks = {}
    for name, t in terr.items():
        m = np.zeros((1700, 1750), np.uint8)
        for poly in t["polys"]:
            cv2.fillPoly(m, [np.array(poly, np.int32)], 1)
        masks[name] = cv2.dilate(m, np.ones((7, 7), np.uint8))
    pairs = set()
    for a, b in itertools.combinations(sorted(masks), 2):
        if (masks[a] & masks[b]).any():
            pairs.add((a, b))
    return pairs


def centre_of(polys):
    xs = [p[0] for poly in polys for p in poly]
    ys = [p[1] for poly in polys for p in poly]
    x0, y0 = min(xs), min(ys)
    m = np.zeros((max(ys) - y0 + 3, max(xs) - x0 + 3), np.uint8)
    for poly in polys:
        cv2.fillPoly(m, [np.array([[x - x0 + 1, y - y0 + 1] for x, y in poly], np.int32)], 1)
    dist = cv2.distanceTransform(m, cv2.DIST_L2, 5)  # the point deepest inside the outline
    y, x = np.unravel_index(int(np.argmax(dist)), dist.shape)
    return [float(x + x0 - 1), float(y + y0 - 1)], [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]


def assign_slots(holder_pairs, imperial_used, barbarian_used):
    """Give holders colour slots so that holders who border each other look different."""
    weight = collections.Counter(holder_pairs)
    slot = {}
    order = sorted(imperial_used, key=lambda n: -sum(w for (a, b), w in weight.items() if n in (a, b)))
    for group, pattern_after in ((order, 8), (sorted(barbarian_used), 0)):
        for i, n in enumerate(group):
            best, best_score = None, None
            for s in SLOTS:
                same = [o for o, (os_, _) in slot.items() if os_ == s]
                # never share a colour with a neighbour; prefer unused colours, then distance from neighbours
                clash = any(weight.get(tuple(sorted((n, o))), 0) for o in same)
                near = [delta(s, slot[o][0]) for o in slot if weight.get(tuple(sorted((n, o))), 0) and slot[o][0] != s]
                score = (not clash, PREFERRED.get(n) == s, -len(same), min(near) if near else 99)
                if best_score is None or score > best_score:
                    best, best_score = s, score
            slot[n] = (best, "dots" if (group is order and any(o for o in slot if slot[o][0] == best and o in imperial_used)) else None)
        if group is order:
            for n in order:  # the second Imperial nation on a colour carries dots
                pass
    for n in barbarian_used:
        slot[n] = (slot[n][0], "hatch")
    return slot


RENAMED = {("Madruga", "Siroc Plains"): "Siroc Bayou", ("Madruga", "Great Grasses"): "Quiet Grasses",
           ("Madruga", "Blightheart"): "Quiet Grasses"}
SEASON_RE = re.compile(r"(\d{3})YE (Spring|Summer|Autumn|Winter)")


def load_control(terr, regions, seasons, pages):
    """Merge the reading results in map/control_raw/ into start holders and dated changes.

    Flags on a change: "np" = shown in the history but not painted (a statement about the
    territory as a whole while its regions are split); "as" = a Senate assignment, which
    re-colours only regions already in Imperial hands.
    """
    raw = MAP_DIR / "control_raw"
    idx = {s: i for i, s in enumerate(seasons)}
    nation, imperial, start, changes, history, issues, now = {}, {}, {}, [], [], [], {}
    for name in terr:
        cats = pages.get(name, {}).get("categories", [])
        imp = [n for n in IMPERIAL if n in cats]
        barb = [n for n in BARBARIAN if n in cats]
        nation[name] = imp[0] if imp else (barb[0] if barb else None)
        imperial[name] = "Imperial Territory" in cats
        start[name] = nation[name] or "Unknown"
    for name, extra in extra_territories().items():
        start[name] = extra.get("holder", "Unknown")

    hist_path = MAP_DIR / "nation_history.json"
    nation_hist = {k: v for k, v in json.loads(hist_path.read_text()).items() if not k.startswith("_")} if hist_path.exists() else {}

    def nation_at(name, s):
        """The Imperial nation a territory belonged to at season index s (see map/nation_history.json)."""
        out = nation[name]
        for entry in nation_hist.get(name, []):
            if idx[entry["from"]] <= s:
                out = entry["nation"]
        return out
    ctl_nation_at = nation_at

    def region_of(name, region):
        region = RENAMED.get((name, region), region)
        return region if region in regions.get(name, []) else None

    tfile = raw / "territories.json"
    if tfile.exists():
        for t in json.loads(tfile.read_text()):
            name = t.get("territory")
            if name not in terr:
                issues.append(f"territory reader: unknown territory {name!r}")
                continue
            if t.get("nation") and canon(t["nation"]) not in ("Uncontrolled", "Unknown"):
                nation[name] = canon(t["nation"])
            if isinstance(t.get("imperial"), bool):
                imperial[name] = t["imperial"]
            last = len(seasons) - 1
            first = canon(t.get("holder_376"), nation_at(name, 0))
            if not first:  # the page gives no history: assume today's holder held it throughout
                first = canon(t.get("holder_now"), nation_at(name, last)) or start[name]
            start[name] = first
            now[name] = {"": canon(t.get("holder_now"), nation_at(name, last))}
            for r, hname in (t.get("regions_now") or {}).items():
                if region_of(name, r):
                    now[name][region_of(name, r)] = canon(hname, nation_at(name, last))
            for c in t.get("changes") or []:
                when = str(c.get("when") or "")
                m = SEASON_RE.search(when)
                y = re.search(r"(\d{1,3})\s?YE", when)
                region = region_of(name, c.get("region")) if c.get("region") else None
                if c.get("region") and not region:
                    issues.append(f"territory reader: unknown region {c['region']!r} in {name}")
                    continue
                at = idx.get(m.group(0)) if m and m.group(0) in idx else (
                    idx.get(f"{y.group(1)}YE Spring", 0) if y and int(y.group(1)) >= 376 else 0)
                entry = {"t": name, "r": region, "h": canon(c.get("holder"), nation_at(name, at)),
                         "ph": canon(c.get("previous_holder"), nation_at(name, max(at - 1, 0))),
                         "kind": c.get("kind") or "other", "note": c.get("note") or "",
                         "conf": c.get("confidence") or "medium", "src": name + " (territory page)",
                         "u": pages.get(name, {}).get("source"), "from": "territory page"}
                if not entry["h"]:
                    continue
                if m and m.group(0) in idx:
                    changes.append({**entry, "s": idx[m.group(0)]})
                elif y and int(y.group(1)) < 376:
                    where = f"{region}, {name}" if region else name
                    history.append({"y": int(y.group(1)), "t": name, "u": entry["u"],
                                    "tx": f"{where} passes to {entry['h']}. {entry['note']}".strip()})
                elif y and f"{y.group(1)}YE Spring" in idx:  # year known, season not: listed, not painted
                    changes.append({**entry, "s": idx[f"{y.group(1)}YE Spring"], "np": 1, "conf": "low",
                                    "note": (entry["note"] + " Season within the year not stated.").strip()})
    for f in control_files():
        era = f.stem
        for c in json.loads(f.read_text()):
            name = c.get("territory")
            if name not in terr or c.get("event") not in idx:
                issues.append(f"era {era}: skipped {name!r} at {c.get('event')!r}")
                continue
            region = None
            if c.get("region"):
                region = region_of(name, c["region"])
                if not region:
                    issues.append(f"era {era}: unknown region {c['region']!r} in {name}")
                    continue
            src = c.get("source") or ""
            at = idx[c["event"]]
            holder = canon(c.get("holder"), nation_at(name, at))
            prev_holder = canon(c.get("previous_holder"), nation_at(name, max(at - 1, 0)))
            if not holder:
                continue
            changes.append({"t": name, "r": region, "h": holder, "ph": prev_holder, "s": idx[c["event"]],
                            "kind": c.get("kind") or "other", "note": c.get("note") or "",
                            "conf": c.get("confidence") or "medium", "src": src,
                            "u": pages.get(src, {}).get("source"), "from": "winds of war"})
    for c in changes:
        note = c["note"].lower()
        if c["kind"] == "status" and c["h"] == "Unknown":  # "controller unclear" adds nothing: keep the last known
            c["np"] = 1
        elif c["r"] is None and c["kind"] == "assigned":
            c["as"] = 1
        elif c["r"] is None and (note.startswith("territory control only") or note.startswith("territory-level only")):
            c["np"] = 1
    # the campaign reports are the primary record; drop territory-page entries they already cover
    primary = collections.defaultdict(list)
    for c in changes:
        if c["from"] == "winds of war":
            primary[(c["t"], c["r"], c["h"])].append(c["s"])
    changes = [c for c in changes if c["from"] == "winds of war"
               or not any(abs(c["s"] - s) <= 4 for s in primary.get((c["t"], c["r"], c["h"]), []))]
    changes.sort(key=lambda c: (c["s"], c["r"] is not None, c["from"] == "winds of war", c["kind"] != "status"))
    return {"nation": nation, "nation_at": nation_at, "imperial": imperial, "start": start, "startRegions": {},
            "changes": changes, "history": history, "now": now, "issues": issues,
            "nation_hist": nation_hist}


def start_regions(terr, regions, seasons, ctl):
    """Starting holder per region, taken from its first region-specific report.

    A change states who held the region before it; a plain statement of who holds it says the same
    for the time before it. Used only where no earlier painted change touches that territory, so it
    never contradicts the record.
    """
    idx = {s: i for i, s in enumerate(seasons)}
    raw = []
    for f in control_files():
        raw += [c for c in json.loads(f.read_text()) if c.get("event") in idx]
    # territory pages' dated region records count too ("the last Highborn-held regions fell in 377YE")
    raw += [{"event": seasons[c["s"]], "territory": c["t"], "region": c["r"], "holder": c["h"],
             "previous_holder": c.get("ph"), "kind": c["kind"], "_canon": True}
            for c in ctl["changes"] if c.get("from") == "territory page" and c["r"] and not c.get("np")]
    raw.sort(key=lambda c: idx[c["event"]])
    first_touch = {}  # earliest painted entry that touches a region: its own, or a whole-territory change
    for c in ctl["changes"]:
        if c.get("np"):
            continue
        targets = [c["r"]] if c["r"] else ([] if c["kind"] == "status" else regions.get(c["t"], []))
        for r in targets:
            first_touch[(c["t"], r)] = min(first_touch.get((c["t"], r), 99), c["s"])
    out, seen = {}, set()
    for c in raw:
        t, r = c.get("territory"), c.get("region")
        if not r or t not in terr or (t, r) in seen:
            continue
        r = RENAMED.get((t, r), r)
        if r not in regions.get(t, []):
            continue
        seen.add((t, r))
        before = c.get("holder") if c.get("kind") == "status" else c.get("previous_holder")
        h = (before if c.get("_canon") else canon(before, ctl["nation_at"](t, max(idx[c["event"]] - 1, 0)))) if before else None
        if not h or "unspecified" in h.lower() or h == "Unknown":
            continue
        # a status or change only speaks for the time before it if nothing earlier touched the territory
        if first_touch.get((t, r), 99) < idx[c["event"]]:
            continue
        out.setdefault(t, {})[r] = h  # recorded even when equal to the territory's, so loose statements skip it
    return out


def timeline(state):
    """{territory: {region or "": [[season index, holder], ...]}}: only the seasons where the holder changes."""
    out = {}
    for t, rows in state.items():
        out[t] = {}
        for r, v in rows.items():
            runs = []
            for i, h in enumerate(v):
                h = "unknown" if h == "Unknown" else h
                if not runs or runs[-1][1] != h:
                    runs.append([i, h])
            out[t][r] = runs
    return out


def apply_changes(terr, regions, seasons, ctl):
    """Holder of every region (and "" for the territory as a whole) at every season."""
    imperial = set(IMPERIAL) | {"The Empire"}
    sr = ctl.get("startRegions") or {}
    state = {t: {r: [sr.get(t, {}).get(r, ctl["start"][t])] * len(seasons) for r in ([""] + regions.get(t, []))} for t in terr}
    for c in ctl["changes"]:
        if c.get("np"):
            continue
        rows = state[c["t"]]
        own = sr.get(c["t"], {})
        for r in ([c["r"]] if c["r"] else list(rows)):
            if r not in rows or (c.get("as") and rows[r][c["s"]] not in imperial):
                continue
            if not c["r"] and c["kind"] == "status" and r in own:  # a loose whole-territory statement
                continue                                         # does not override a region's own record
            for i in range(c["s"], len(seasons)):
                rows[r][i] = c["h"]
    # Continuity: when a region's own reports give the same holder before and after a stretch, and nothing
    # specific to that region says otherwise in between, a vague whole-territory statement in that stretch
    # did not change it.
    own = collections.defaultdict(list)
    for c in ctl["changes"]:
        if c["r"] and not c.get("np"):
            own[(c["t"], c["r"])].append(c)
    for (t, r), recs in own.items():
        recs.sort(key=lambda c: c["s"])
        for a, b in zip(recs, recs[1:]):
            held_before_b = b["h"] if b["kind"] == "status" else b.get("ph")
            if a["h"] and held_before_b == a["h"] and b["s"] > a["s"]:
                for i in range(a["s"], b["s"]):
                    state[t][r][i] = a["h"]
    # Handover: when the Senate gives a territory to a nation (map/nation_history.json), the regions the
    # Empire already holds there become that nation's from that season.
    idx = {x: i for i, x in enumerate(seasons)}
    for t, entries in ctl.get("nation_hist", {}).items():
        for e in entries:
            f = idx[e["from"]]
            if not e["nation"] or f == 0 or t not in state:
                continue
            before = {"The Empire", ctl["nation_at"](t, f - 1)}
            for r, row in state[t].items():
                # up to the region's next own report, which says for itself who holds it
                stop = min([c["s"] for c in own.get((t, r), []) if c["s"] >= f] + [len(seasons)])
                for i in range(f, stop):
                    if row[i] in before:
                        row[i] = e["nation"]
    return state


# The archive's markdown on GitHub. Archive links must be absolute: the published site holds only map/,
# so a relative "../wiki/..." link would resolve against the site's own domain and break.
ARCHIVE_BASE = "https://github.com/Joeb1603/Anvil/blob/main/"


def archive_url(rel_path):
    from urllib.parse import quote
    path = rel_path[3:] if rel_path.startswith("../") else rel_path
    return ARCHIVE_BASE + quote(path)


def build(archive_links=True):
    pages = read_json(DATA / "pages.json")
    manifest = read_json(DATA / "manifest.json")
    terr = territory_polygons()
    shapes = json.loads((MAP_DIR / "region_shapes.json").read_text())
    ev = json.loads((MAP_DIR / "events.json").read_text())
    seasons = ev["seasons"]
    regions = {t: list(cs) for t, cs in shapes.items()}
    ctl = load_control(terr, regions, seasons, pages)
    ctl["startRegions"] = start_regions(terr, regions, seasons, ctl)
    ctl["state"] = apply_changes(terr, regions, seasons, ctl)
    ctl["reconciled"] = reconcile(ctl, regions, seasons, pages)
    ctl["changes"] += ctl["reconciled"]

    state = apply_changes(terr, regions, seasons, ctl)
    pairs = adjacency(terr)
    used = collections.Counter(h for t in terr if t not in SEAS for hs in state[t].values() for h in hs)
    holder_pairs = []
    for a, b in pairs:
        if a in SEAS or b in SEAS:
            continue
        for i in range(len(seasons)):
            for ha in {hs[i] for hs in state[a].values()}:
                for hb in {hs[i] for hs in state[b].values()}:
                    if ha != hb:
                        holder_pairs.append(tuple(sorted((ha, hb))))
    for t in terr:  # holders sharing a territory are neighbours too
        for i in range(len(seasons)):
            hs = sorted({v[i] for v in state[t].values()})
            holder_pairs += list(itertools.combinations(hs, 2))
    imp_used = [n for n in IMPERIAL if used[n]]
    barb_used = [n for n in BARBARIAN if used[n]]
    slots = assign_slots(holder_pairs, imp_used, barb_used)
    seen_slot = set()
    holders = []
    for n in imp_used:
        s, _ = slots[n]
        holders.append({"id": n, "name": n, "group": "Imperial nations", "slot": s, "pattern": "dots" if s in seen_slot else None})
        seen_slot.add(s)
    for n in barb_used:
        holders.append({"id": n, "name": n, "group": "Barbarian powers", "slot": slots[n][0], "pattern": "hatch"})
    if used["The Empire"]:
        holders.append({"id": "The Empire", "name": "The Empire (no nation assigned)", "group": "Imperial nations",
                        "slot": "n1", "pattern": "dots"})
    others = [h for h in used if h not in IMPERIAL and h not in BARBARIAN and h not in ("Unknown", "The Empire")]
    for k, n in enumerate(sorted(others, key=lambda h: -used[h])):
        holders.append({"id": n, "name": n, "group": "Barbarian powers" if n in BARBARIAN_OTHER else "Others",
                        "slot": "n1", "pattern": "hatch" if k % 2 == 0 else "dots"})
    holders.append({"id": "unknown", "name": "Unknown", "group": "Others", "slot": "n2", "pattern": None})
    # Keep every holder's colour stable across rebuilds: reuse map/holder_colours.json, add new holders to it.
    lock_path = MAP_DIR / "holder_colours.json"
    lock = json.loads(lock_path.read_text()) if lock_path.exists() else {}
    # colours of their own for the holders that matter on the map, so only minor foreign powers are grey
    # Imperial nations are solid colours; everyone else (barbarians, foreign powers) is hatched. Imperial
    # Orcs and Urizen get colours of their own (s9, s10) rather than sharing one with a dot pattern.
    special = {"Vallorn": ["vallorn", "hatch"], "Druj": ["s11", "hatch"], "Uncontrolled": ["free", None], "The Empire": ["emp", None],
               "Imperial Orcs": ["s9", None], "Urizen": ["s10", None]}
    for hd in holders:
        if hd["id"] in special:
            lock[hd["id"]] = special[hd["id"]]
        if hd["id"] in lock:
            hd["slot"], hd["pattern"] = lock[hd["id"]]
        if hd["group"] != "Imperial nations" and hd["id"] not in ("Uncontrolled", "unknown"):
            hd["pattern"] = "hatch"
            lock[hd["id"]] = [hd["slot"], "hatch"]
        else:
            lock[hd["id"]] = [hd["slot"], hd["pattern"]]
    lock_path.write_text(json.dumps(lock, indent=1, ensure_ascii=False) + "\n")
    fix = lambda h: "unknown" if h == "Unknown" else h

    # territory colours for the by-territory view: neighbours never share one
    tslot, graph = {}, collections.defaultdict(set)
    for a, b in pairs:
        graph[a].add(b)
        graph[b].add(a)
    for t in sorted(terr, key=lambda n: -len(graph[n])):
        taken = {tslot[n] for n in graph[t] if n in tslot}
        free = [s for s in SLOTS if s not in taken] or SLOTS
        tslot[t] = min(free, key=lambda s: sum(1 for v in tslot.values() if v == s))

    territories = []
    extras = extra_territories()
    sidx0 = {s: i for i, s in enumerate(seasons)}
    for name, t in sorted(terr.items()):
        centre, bbox = centre_of(t["polys"])
        info = pages.get(name, {})
        extra = extras.get(name)
        if extra:  # no wiki page of its own: link to the report that introduces it
            info = {"source": pages.get(extra.get("source"), {}).get("source")}
        territories.append({
            "name": name, "polys": t["polys"], "centre": centre, "bbox": bbox, "sea": name in SEAS,
            "nation": ctl["nation"].get(name), "imperial": ctl["imperial"].get(name, False), "tslot": tslot[name],
            "u": info.get("source"),
            "approx": bool(extra), "note": extra.get("note") if extra else None,
            "log": [{"s": sidx0[x["season"]], "r": x.get("region"), "tx": x["text"], "src": x["source"],
                     "u": pages.get(x["source"], {}).get("source")} for x in (extra or {}).get("log", [])],
            "regions": [{"name": r, "polys": c["polys"], "centre": c["centre"], "placed": c["placed"]}
                        for r, c in shapes.get(name, {}).items()],
        })
    sidx = {s: i for i, s in enumerate(seasons)}
    events = [{"ti": e["title"], "s": sidx[e["event"]], "ty": e["type"], "pl": e["places"], "ex": e["excerpt"],
               "u": e["source"], "p": archive_url(e["path"]) if archive_links else None} for e in ev["events"]]
    history = [{"y": h["year"], "t": h["territory"], "tx": h["text"], "u": h["source"]} for h in ev["history"]] + ctl["history"]
    history.sort(key=lambda h: (h["y"], h["t"]))
    xs = [p[0] for t in terr.values() for poly in t["polys"] for p in poly]
    ys = [p[1] for t in terr.values() for poly in t["polys"] for p in poly]
    view = [min(xs) - 20, min(ys) - 20, max(xs) - min(xs) + 40, max(ys) - min(ys) + 40]
    front, nlabels = frontiers.compute(terr, shapes, state, seasons, SEAS, side_of, view,
                                       lambda h: None if h in ("Unknown", "Uncontrolled") else h)
    data_contested = contested(state, seasons, ev["events"], side_of)
    data = {
        "contested": data_contested,
        "meta": {"snapshot": manifest["snapshot"], "archiveLinks": archive_links},
        "view": view, "frontiers": front,
        "nlabels": [[[fix(r[0])] + r[1:4] for r in season] for season in nlabels],
        "seasons": seasons, "territories": territories, "holders": holders,
        "control": {"timeline": timeline(state), "start": {t: fix(h) for t, h in ctl["start"].items()}, "startRegions": {t: {r: fix(h) for r, h in rs.items()} for t, rs in ctl["startRegions"].items()},
                    "changes": [{k: (fix(v) if k == "h" else v) for k, v in c.items() if k != "from"} for c in ctl["changes"]]},
        "events": events, "history": history, "real": ev["real"],
        "breaks": [{"i": sidx[BREAK_BEFORE], "label": "Lockdown",
                    "note": (f"The Covid lockdown fell between {seasons[sidx[BREAK_BEFORE] - 1]} "
                             f"({ev['real'][sidx[BREAK_BEFORE] - 1]['n']}) and {BREAK_BEFORE}. "
                             "Its Winds of War were written in March 2020, weeks before lockdown, and the "
                             f"summit finally ran as {ev['real'][sidx[BREAK_BEFORE]]['n']}. "
                             "No events ran in 2020 or 2021 and in-game time paused across the gap.")}],
    }
    ctl["state"] = state
    return data, ctl


def contested(state, seasons, events, side_of):
    """{territory: {region: {season index: [report titles]}}}: regions where fighting is reported.

    A region counts as contested in a season when a Wind of War that season names it, and either it
    changes hands this season or next, or its territory is split between the Empire and its enemies.
    """
    idx = {s: i for i, s in enumerate(seasons)}
    out = {}
    for e in events:
        if e["type"] != "Wind of War":
            continue
        i = idx[e["event"]]
        for t, rs in e["places"].items():
            rows = state.get(t, {})
            sides = {side_of(v[i]) for r, v in rows.items() if r}
            split = "imp" in sides and "barb" in sides
            for r in rs:
                v = rows.get(r)
                if not v:
                    continue
                moves = (i > 0 and v[i] != v[i - 1]) or (i + 1 < len(v) and v[i + 1] != v[i])
                if moves or split:
                    out.setdefault(t, {}).setdefault(r, {}).setdefault(i, []).append(e["title"])
    return out


def reconcile(ctl, regions, seasons, pages):
    """Where a territory page states today's holder and no dated change explains it, record the
    change at the final season, marked as undated."""
    added = []
    state = ctl["state"]
    for t, now in ctl["now"].items():
        for r in [x for x in state[t] if x] or [""]:
            want = now.get(r, now.get(""))
            if want and want != state[t][r][-1]:
                added.append({"t": t, "r": r or None, "h": want, "s": len(seasons) - 1, "kind": "other", "conf": "low",
                              "note": "Holder today according to the territory page. When it changed is not recorded.",
                              "src": t + " (territory page)", "u": pages.get(t, {}).get("source"), "from": "territory page"})
    return added


def write(data):
    template = (ROOT / "mapbuilder" / "template.html").read_text(encoding="utf-8")
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    (MAP_DIR / "data.json").write_text(blob, encoding="utf-8")
    inline = "<script>window.__ATLAS__=" + blob.replace("</", "<\\/") + ";</script>"
    page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n</head>\n<body>\n'
            + template.replace("<!--DATA-->", inline) + "\n</body>\n</html>\n")
    (MAP_DIR / "index.html").write_text(page, encoding="utf-8")
    return len(blob), len(page)


if __name__ == "__main__":
    data, ctl = build()
    nb, npg = write(data)
    print(f"data.json {nb / 1e6:.2f} MB | index.html {npg / 1e6:.2f} MB")
    print("territories:", len(data["territories"]), "| regions:", sum(len(t["regions"]) for t in data["territories"]),
          "| events:", len(data["events"]), "| history:", len(data["history"]),
          "| control changes:", len(data["control"]["changes"]))
    print("holders:", [(h["name"], h["slot"], h["pattern"]) for h in data["holders"]])
    if ctl["issues"]:
        print("issues:", len(ctl["issues"]), ctl["issues"][:8])
    from . import checks
    result = checks.run(data, ctl)
    checks.write(result)
    print(checks.summary(result))
    if "--artifact" in sys.argv:
        out = sys.argv[sys.argv.index("--artifact") + 1]
        import pathlib
        pathlib.Path(out).mkdir(parents=True, exist_ok=True)
        d2, _ = build()
        (pathlib.Path(out) / "data.json").write_text(json.dumps(d2, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        (pathlib.Path(out) / "empire-atlas.html").write_text(
            (ROOT / "mapbuilder" / "template.html").read_text(encoding="utf-8").replace("<!--DATA-->", ""), encoding="utf-8")
        print("artifact copy written to", out)
