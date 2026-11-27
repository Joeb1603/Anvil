"""Checks on the built atlas for the kinds of mistake that leave it wrong or incomplete.

The build runs these and writes the results to map/checks.md (to read) and map/checks.json (for
the workflows). A failure means the map is probably showing something wrong; a warning means
something may be missing or worth a second look.

    python3 -m mapbuilder.checks                    # rebuild in memory and print the results
    python3 -m mapbuilder.checks --compare OLD.json  # exit 1 if map/checks.json has failures OLD.json lacks

Known, explained exceptions live in map/checks_accepted.json as {check: {key: reason}}.
"""
from __future__ import annotations

import collections
import json
import re
import sys

from scraper.common import DATA, read_json

from .geometry import MAP_DIR

ACCEPTED = MAP_DIR / "checks_accepted.json"
SEASONS = ["Spring", "Summer", "Autumn", "Winter"]


def _season_range(first, last):
    """Every season from first to last inclusive, in play order."""
    y, s = int(first[:3]), SEASONS.index(first.split()[1])
    out = []
    while True:
        name = f"{y}YE {SEASONS[s]}"
        out.append(name)
        if name == last or y > int(last[:3]):
            return out
        s += 1
        if s == 4:
            y, s = y + 1, 0


def run(data, ctl, pages=None):
    """{"failures": [...], "warnings": [...], "accepted": [...]}, each item {check, key, msg}."""
    from .build import IMPERIAL, RENAMED, canon  # here, so build can import this module

    pages = pages or read_json(DATA / "pages.json")
    accepted = json.loads(ACCEPTED.read_text()) if ACCEPTED.exists() else {}
    S = data["seasons"]
    idx = {s: i for i, s in enumerate(S)}
    out = {"failures": [], "warnings": [], "accepted": []}

    def add(level, check, key, msg):
        reason = accepted.get(check, {}).get(key)
        if reason:
            out["accepted"].append({"check": check, "key": key, "msg": msg, "reason": reason})
        else:
            out[level].append({"check": check, "key": key, "msg": msg})

    fail = lambda *a: add("failures", *a)
    warn = lambda *a: add("warnings", *a)

    # 1. Control records naming a territory or region the map doesn't have, or that couldn't be read.
    for issue in ctl["issues"]:
        fail("control-record", issue, issue)

    # 2. Holders: every place has someone (or "uncontrolled") in every season, under a known name.
    names = {h["id"] for h in data["holders"]}
    timeline = data["control"]["timeline"]
    for t in data["territories"]:
        if t["sea"]:
            continue
        rows = timeline.get(t["name"], {})
        if all(h == "unknown" for seq in rows.values() for _, h in seq):
            fail("never-held", t["name"], f"{t['name']} has no known holder in any season.")
            continue
        for r, seq in rows.items():
            place = f"{r}, {t['name']}" if r else t["name"]
            if seq[-1][1] == "unknown":
                fail("unknown-today", place, f"{place}: no known holder in {S[-1]}.")
            for s, h in seq:
                if h == "unknown" and s > 0:
                    warn("holder-gap", f"{place}@{S[s]}", f"{place}: holder becomes unknown from {S[s]}.")
                elif h != "unknown" and h not in names:
                    fail("unknown-holder", f"{place}:{h}", f"{place}: holder {h!r} has no colour or legend entry.")
                elif h == "The Empire" and ctl["nation_at"](t["name"], s) in IMPERIAL:
                    warn("vague-holder", f"{place}@{S[s]}", f"{place}: held by 'The Empire' from {S[s]}, though "
                         f"{t['name']} belongs to {ctl['nation_at'](t['name'], s)} then.")

    # 3. The map's holder just before each place's first region report agrees with that report.
    state = ctl["state"]
    first = {}
    raw = [c for f in sorted((MAP_DIR / "control_raw").glob("[A-Z].json")) for c in json.loads(f.read_text())
           if c.get("event") in idx]
    for c in sorted(raw, key=lambda c: idx[c["event"]]):
        t, r = c.get("territory"), RENAMED.get((c.get("territory"), c.get("region")), c.get("region"))
        if r and t in state and r in state[t]:
            first.setdefault((t, r), c)
    for (t, r), c in first.items():
        i = idx[c["event"]]
        before = state[t][r][max(i - 1, 0)]
        exp = c.get("holder") if c.get("kind") == "status" else c.get("previous_holder")
        if not exp or "unspecified" in exp.lower():
            continue
        exp = canon(exp, ctl["nation_at"](t, max(i - 1, 0)))
        if exp != before and not (exp == "The Empire" and before in IMPERIAL):
            fail("start-holder", f"{t}/{r}@{c['event']}",
                 f"{r}, {t}: the map has {before} before {c['event']}, but that season's report "
                 f"({c.get('source', '?')}) has {exp}.")

    # 3b. Every change a report describes says who held the region just before: the map should agree.
    for c in ctl["changes"]:
        if c.get("np") or not c["r"] or c["kind"] == "status" or not c.get("ph") or c["s"] == 0:
            continue
        if "unspecified" in c["ph"].lower() or c["ph"] == "Unknown":
            continue
        before = state[c["t"]][c["r"]][c["s"] - 1]
        if before != c["ph"] and not (c["ph"] == "The Empire" and before in IMPERIAL):
            fail("previous-holder", f"{c['t']}/{c['r']}@{S[c['s']]}",
                 f"{c['r']}, {c['t']}: {c['src']} says {c['ph']} held it before {S[c['s']]}, "
                 f"but the map has {before}.")

    # ...and for a change to a whole territory, someone in it should have been the previous holder.
    for c in ctl["changes"]:
        if c.get("np") or c["r"] or c["kind"] == "status" or c.get("as") or not c.get("ph") or c["s"] == 0:
            continue
        if "unspecified" in c["ph"].lower() or c["ph"] == "Unknown":
            continue
        rows = state[c["t"]]
        held = {rows[r][c["s"] - 1] for r in ([r for r in rows if r] or [""])}
        if c["ph"] not in held and not (c["ph"] == "The Empire" and held & set(IMPERIAL)):
            fail("previous-holder", f"{c['t']}@{S[c['s']]}",
                 f"{c['t']}: {c['src']} says {c['ph']} held it before {S[c['s']]}, but the map has "
                 f"{', '.join(sorted(held))}.")

    # 3c. Two campaign reports giving the same region different holders in the same season.
    said = collections.defaultdict(set)
    for c in ctl["changes"]:
        if c["r"] and not c.get("np") and c.get("from") == "winds of war":
            said[(c["t"], c["r"], c["s"])].add(c["h"])
    for (t, r, s), hs in sorted(said.items()):
        if len(hs) > 1:
            fail("conflict", f"{t}/{r}@{S[s]}", f"{r}, {t}: reports for {S[s]} disagree ({', '.join(sorted(hs))}).")

    # 3d. Map shapes: no slit inside any power's or territory's outline (it would draw as a stray line).
    for x in ctl.get("seams", []):
        fail("seam", f"{x['holder']}@{x['season']}@{x['where']}",
             f"{x['holder']} ({x['season']}): a slit {x['length']}px long inside its outline at {x['where']} "
             "would draw as a stray line.")

    # 4. Seasons: none missing between the first and the last, and every dated page falls inside them.
    expected = _season_range(S[0], S[-1])
    for s in expected:
        if s not in idx:
            fail("season-missing", s, f"{s} is missing from the timeline.")
    latest = max((p["event"] for p in pages.values() if p.get("event")),
                 key=lambda e: (int(e[:3]), SEASONS.index(e.split()[1])), default=None)
    if latest and latest not in idx:
        fail("season-missing", latest, f"Pages are dated {latest}, which is not on the timeline.")

    # 5. Regions: each has a shape, and a position read from a wiki map rather than guessed.
    for t in data["territories"]:
        for r in t["regions"]:
            place = f"{r['name']}, {t['name']}"
            if not r["polys"]:
                fail("region-shape", place, f"{place} has no shape on the map.")
            elif r["placed"] not in ("label", "part") and not t["approx"]:
                warn("region-position", place, f"{place}: position {r['placed']!r}, not read from a wiki map.")

    # 6. A Wind of War that is attached to no place. (Many Winds of Fortune are about foreign nations, faiths
    #    or magic rather than a place, so those are not flagged.)
    placed = {e["ti"] for e in data["events"]}
    for title, p in sorted(pages.items()):
        if p.get("event") and p["ns"] != 14 and title not in placed and p["class"] == "in-character" \
                and "Winds of War" in p["categories"]:
            warn("unplaced-report", title, f"{title} ({p['event']}) is not attached to any place.")

    # 7. Holders known only from today's territory page: a dated report was probably missed.
    for c in ctl["changes"]:
        if c.get("from") == "territory page" and c.get("note", "").startswith("Holder today"):
            place = f"{c['r']}, {c['t']}" if c["r"] else c["t"]
            warn("undated-change", place, f"{place}: now {c['h']} per its territory page, "
                                          "but no report says when it changed.")

    # 7b. Region changes a territory page dates only by year: not painted until a season is found.
    for c in ctl["changes"]:
        if c.get("np") and c["r"] and "Season within the year not stated" in c.get("note", ""):
            dated = [x for x in ctl["changes"] if x["t"] == c["t"] and x["r"] in (c["r"], None) and x["h"] == c["h"]
                     and not x.get("np") and abs(x["s"] - c["s"]) <= 4]
            if not dated:
                warn("year-only", f"{c['r']}, {c['t']}@{S[c['s']][:5]}",
                     f"{c['r']}, {c['t']}: passes to {c['h']} in {S[c['s']][:5]} per its territory page, season "
                     "unknown, so the map doesn't show it. Find the season and add it to corrections.json.")

    # 8. Territories that change nation must say when (map/nation_history.json).
    hist = MAP_DIR / "nation_history.json"
    for t, entries in (json.loads(hist.read_text()) if hist.exists() else {}).items():
        if t.startswith("_"):
            continue
        for e in entries:
            if e["from"] not in idx:
                fail("nation-history", f"{t}@{e['from']}", f"nation_history.json: {t} uses unknown season {e['from']}.")

    # 8b. Written summaries: every event should have one, naming only the places the atlas gives it.
    sp = MAP_DIR / "summaries.json"
    summ = json.loads(sp.read_text()) if sp.exists() else {}
    missing = [e["ti"] for e in data["events"] if e["ti"] not in summ]
    if missing:
        warn("summary-missing", "count", f"{len(missing)} of {len(data['events'])} events have no written summary yet "
             f"(e.g. {', '.join(missing[:3])}); run the 'Summarise events' workflow.")
    for e in data["events"]:
        x = summ.get(e["ti"])
        if not x:
            continue
        extra = set(x.get("t", {})) - set(e["pl"])
        if extra:
            warn("summary-stale", e["ti"], f"{e['ti']}: summary covers {', '.join(sorted(extra))}, which the atlas no "
                 "longer attaches to it; it will be rewritten on the next run.")

    # 9. Archive pages with no classification.
    for title, p in pages.items():
        if p["ns"] != 14 and not p.get("class"):
            warn("unclassified", title, f"{title} has no in-character / out-of-character class.")

    for k in out:
        out[k].sort(key=lambda x: (x["check"], x["key"]))
    return out


def write(result):
    (MAP_DIR / "checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# Atlas checks", "",
             "Written by every build (`python3 -m mapbuilder.run`). Failures mean the map probably shows "
             "something wrong; warnings mean something may be missing. Explained exceptions go in "
             "`checks_accepted.json`.", "",
             f"**{len(result['failures'])} failures, {len(result['warnings'])} warnings, "
             f"{len(result['accepted'])} accepted.**", ""]
    for level in ("failures", "warnings"):
        if not result[level]:
            continue
        lines += [f"## {level.capitalize()}", ""]
        for check, items in itertools_groupby(result[level]):
            lines += [f"### {check} ({len(items)})", ""] + [f"- {x['msg']}" for x in items[:200]]
            if len(items) > 200:
                lines.append(f"- ... and {len(items) - 200} more (see checks.json)")
            lines.append("")
    if result["accepted"]:
        lines += ["## Accepted", ""] + [f"- {x['msg']} *Accepted: {x['reason']}*" for x in result["accepted"]] + [""]
    (MAP_DIR / "checks.md").write_text("\n".join(lines), encoding="utf-8")


def itertools_groupby(items):
    groups = collections.defaultdict(list)
    for x in items:
        groups[x["check"]].append(x)
    return sorted(groups.items())


def summary(result):
    by = collections.Counter(x["check"] for x in result["failures"])
    wb = collections.Counter(x["check"] for x in result["warnings"])
    return (f"checks: {len(result['failures'])} failures {dict(by)} | {len(result['warnings'])} warnings "
            f"{dict(wb)} | {len(result['accepted'])} accepted (details in map/checks.md)")


def compare(old_path):
    """Exit 1 if the current checks have failures the old ones did not."""
    new = json.loads((MAP_DIR / "checks.json").read_text())
    try:
        old = json.loads(open(old_path).read())
    except (OSError, ValueError):
        old = {"failures": []}
    seen = {(x["check"], x["key"]) for x in old.get("failures", [])}
    added = [x for x in new["failures"] if (x["check"], x["key"]) not in seen]
    for x in added:
        print(f"::error::new atlas check failure: {x['msg']}")
    fixed = len(seen - {(x["check"], x["key"]) for x in new["failures"]})
    print(f"{len(added)} new failures, {fixed} fixed, {len(new['failures'])} remaining")
    return 1 if added else 0


if __name__ == "__main__":
    if "--compare" in sys.argv:
        sys.exit(compare(sys.argv[sys.argv.index("--compare") + 1]))
    from .build import build
    d, c = build()
    res = run(d, c)
    write(res)
    print(summary(res))
