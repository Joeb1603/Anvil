"""To-do list for the scheduled task: everything the atlas should pick up that a machine cannot read.

    python3 -m mapbuilder.audit            # write .cache/audit.json and print a readable list
    python3 -m mapbuilder.audit --record   # after acting on it: remember the current map images and uploads

Sections:
  reports    Winds of War newer than map/control_raw/meta.json "processed_through"
  regions    regions listed on territory pages with no position in map/region_labels.json, and
             stale positions for regions that no longer exist
  maps       territory region maps redrawn since they were last read (map/image_state.json)
  uploads    images uploaded to the wiki since the last check, with the pages that use them
  places     unfamiliar capitalised names that keep turning up in recent reports, for possible
             new places to add to map/extra_territories.json (like Tsirku)
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import re
import sys

from scraper.classify import event_key
from scraper.common import CACHE, DATA, Api, read_json

from .geometry import MAP_DIR, extra_territories, territory_polygons
from .imagetools import image_info, region_map_titles
from .regions import page_body, plain, territory_regions

META = MAP_DIR / "control_raw" / "meta.json"
IMAGE_STATE = MAP_DIR / "image_state.json"
LABELS = MAP_DIR / "region_labels.json"


def _json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def audit(api: Api) -> dict:
    pages = read_json(DATA / "pages.json")
    meta = _json(META, {})
    state = _json(IMAGE_STATE, {"maps": {}, "uploads_checked_through": None})
    labels = _json(LABELS, {})
    report: dict = {}

    # ---- new campaign reports
    done = meta.get("processed_through")
    new = [i for i in pages.values() if "Winds of War" in i["categories"] and i["event"]
           and (not done or event_key(i["event"]) > event_key(done))]
    new.sort(key=lambda i: (event_key(i["event"]), i["title"]))
    report["reports"] = [{"event": i["event"], "title": i["title"], "path": "wiki/" + i["path"],
                          "words": i["words"]} for i in new]

    # ---- regions without a position, and stale positions
    regions = territory_regions()
    missing, stale = [], []
    for t, rs in regions.items():
        names = [r["name"] for r in rs]
        have = (labels.get(t) or {}).get("regions") or {}
        missing += [{"territory": t, "region": n} for n in names if n not in have]
        stale += [{"territory": t, "region": n} for n in have if n not in names]
    report["regions"] = {"missing": missing, "stale": stale}

    # ---- region maps redrawn since last read
    terrs = [t for t, rs in regions.items() if rs]
    maps = region_map_titles(api, terrs)
    info = image_info(api, sorted(set(maps.values())))
    changed = []
    for t, f in sorted(maps.items()):
        cur = (info.get(f) or {}).get("sha1")
        seen = state["maps"].get(t)
        if seen is None or seen.get("file") != f or seen.get("sha1") != cur:
            changed.append({"territory": t, "file": f, "uploaded": (info.get(f) or {}).get("timestamp"),
                            "first_time": seen is None})
    report["maps"] = changed
    report["_maps_now"] = {t: {"file": f, "sha1": (info.get(f) or {}).get("sha1")} for t, f in maps.items()}

    # ---- uploads since the last check
    since = state.get("uploads_checked_through") or (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ups = []
    for data in api.query_all(list="logevents", letype="upload", leend=since, lelimit="500", leprop="title|timestamp|comment"):
        ups += data["query"]["logevents"]
    files = sorted({u["title"] for u in ups})
    usage = collections.defaultdict(list)
    for i in range(0, len(files), 40):
        for data in api.query_all(prop="fileusage", titles="|".join(files[i:i + 40]), fulimit="500", funamespace="0"):
            for p in data["query"]["pages"]:
                usage[p["title"]] += [u["title"] for u in p.get("fileusage", [])]
    when = {u["title"]: u["timestamp"] for u in ups}
    report["uploads"] = [{"file": f, "uploaded": when[f],
                          "used_on": [{"title": t, "class": pages.get(t, {}).get("class"), "topic": pages.get(t, {}).get("topic")}
                                      for t in usage.get(f, [])][:8]}
                         for f in files]
    report["_uploads_now"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ---- unfamiliar names in recent reports (possible new places)
    known = set(territory_polygons()) | {r["name"] for rs in regions.values() for r in rs} | set(extra_territories())
    known |= {w for t in known for w in t.split()}
    recent = sorted((i for i in pages.values() if i["event"] and i["topic"] in ("winds-of-war", "winds-of-fortune")),
                    key=lambda i: event_key(i["event"]))
    if recent:
        last = event_key(recent[-1]["event"])
        recent = [i for i in recent if event_key(i["event"]) >= (last[0] - 1, last[1])]
    place_topics = ("world", "foreign-nations", "barbarians", "history") + tuple(t for t in {i["topic"] for i in pages.values()} if t.startswith("nations/"))
    place_words = {w for t, i in pages.items() if i["topic"] in place_topics for w in re.findall(r"[A-Z][a-z]{3,}(?:\s[A-Z][a-z]{3,})?", t)}
    place_words |= {"Hall", "City", "House", "Night", "Virtue", "Known World", "Liberty Pact", "Black Gate"}
    counts, where = collections.Counter(), collections.defaultdict(set)
    # a name right after a place word ("into Tsirku", "north of Sermersuaq"), with no wiki page of its own
    near = re.compile(r"\b(?:in|into|to|from|across|beyond|through|towards?|near|reach(?:es|ed)?|explor\w+|of the (?:north|south|east|west)|(?:north|south|east|west) of)\s+(?:the\s+)?([A-Z][a-z]{3,}(?:\s[A-Z][a-z]{3,})?)\b")
    skip = {"Spring", "Summer", "Autumn", "Winter", "Empire", "Imperial", "Senate", "Synod", "Conclave", "Bourse",
            "Military", "Council", "Equinox", "Solstice", "Anvil", "Throne", "Highborn", "Winterfolk", "Freeborn",
            "League", "Marches", "Navarr", "Dawn", "Urizen", "Varushka", "Wintermark", "Highguard", "Jotun", "Druj",
            "Grendel", "Thule", "Game", "Information", "Saturday", "Friday", "Sunday", "Further", "Reading"}
    for i in recent:
        body = re.sub(r"\*?\[?Image:[^\n]*", "", plain(page_body(i)))
        for name in set(near.findall(body)):
            if name in known or name in pages or name in place_words or any(w in skip for w in name.split()):
                continue
            counts[name] += 1
            where[name].add(i["title"])
    report["places"] = [{"name": n, "mentions": c, "pages": sorted(where[n])[:5]}
                        for n, c in counts.most_common(25) if len(where[n]) >= 2]
    return report


_TITLES = None


def titles_known(pages):
    global _TITLES
    if _TITLES is None:
        _TITLES = {t for t in pages} | {w for t in pages for w in t.split() if w[:1].isupper()}
    return _TITLES


def show(r: dict) -> None:
    print(f"REPORTS to read ({len(r['reports'])}):")
    for x in r["reports"]:
        print(f"  {x['event']:13} {x['title']}  ({x['words']} words)  {x['path']}")
    print(f"\nREGIONS with no map position ({len(r['regions']['missing'])}):")
    for x in r["regions"]["missing"]:
        print(f"  {x['territory']}: {x['region']}")
    print(f"STALE region positions ({len(r['regions']['stale'])}):")
    for x in r["regions"]["stale"]:
        print(f"  {x['territory']}: {x['region']}")
    print(f"\nREGION MAPS new or redrawn ({len(r['maps'])}):")
    for x in r["maps"]:
        print(f"  {x['territory']}: {x['file']} (uploaded {x['uploaded']})")
    print(f"\nUPLOADS since last check ({len(r['uploads'])}):")
    for x in r["uploads"]:
        used = ", ".join(f"{u['title']} [{u['class'] or 'not in archive yet'}]" for u in x["used_on"]) or "not used on any page yet"
        print(f"  {x['uploaded'][:10]} {x['file']} — {used}")
    print(f"\nPOSSIBLE NEW PLACES ({len(r['places'])}):")
    for x in r["places"]:
        print(f"  {x['name']}: {x['mentions']} mentions, e.g. {'; '.join(x['pages'][:3])}")


def record(r: dict) -> None:
    state = _json(IMAGE_STATE, {"maps": {}, "uploads_checked_through": None})
    state["maps"] = r["_maps_now"]
    state["uploads_checked_through"] = r["_uploads_now"]
    IMAGE_STATE.write_text(json.dumps(state, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"recorded {len(state['maps'])} region maps; uploads checked through {state['uploads_checked_through']}")


if __name__ == "__main__":
    rep = audit(Api())
    CACHE.mkdir(exist_ok=True)
    (CACHE / "audit.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
    if "--record" in sys.argv:
        record(rep)
    else:
        show(rep)
