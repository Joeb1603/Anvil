"""Events for the timeline: every dated archive page, tied to the places it links to."""
from __future__ import annotations

import collections
import json
import os
import re

from scraper.classify import event_key
from scraper.common import DATA, read_json

from .geometry import MAP_DIR, territory_polygons
from .regions import page_body, plain, territory_regions

TYPES = [  # (label, wiki categories) in priority order
    ("Wind of War", {"Winds of War"}),
    ("Wind of Fortune", {"Winds of Fortune", "Wind of Fortune", "Wiands of Fortune"}),
    ("Wind of Magic", {"Winds of Magic"}),
    ("Trade Wind", {"Trade Winds"}),
    ("Mandate", {"Mandate"}),
    ("Senate motion", {"Senate Motion", "Failed Senate Motion", "Vetoed Senate Motion"}),
    ("Military Council", {"Military Council"}),
    ("Synod", {"Synod Judgements", "Synod Results", "Synod"}),
    ("Conclave", {"Conclave Sessions", "Conclave"}),
]
LINK = re.compile(r"\]\(([^)\s#]+\.md)(?:#([^)\s]*))?\)")
YEAR = re.compile(r"\b(\d{1,3})\s?(YE|BE)\b")


EVENT_NAMES = {"Spring": "Spring Equinox", "Summer": "Summer Solstice", "Autumn": "Autumn Equinox",
               "Winter": "Winter Solstice"}
# The summit after 383YE Autumn (Autumn Equinox 2019) was postponed by the Covid lockdown and
# held as Winter Solstice 2022. In-game time paused across the gap.
BREAK_BEFORE = "383YE Winter"


def real_event(season: str) -> str:
    """Real-world event name for an in-game season, following the wiki's own event pages.

    Each real year opens with a Winter Solstice, which closes the previous Imperial year
    (the wiki numbers Winter Solstice 2014 as the fifth event and Spring Equinox 2014 as the
    sixth). Before the break a real year Y holds Winter (Y-1637)YE then Spring to Autumn
    (Y-1636)YE; after it the offsets are 1639 and 1638.
    """
    y, s = int(season[:3]), season.split()[1]
    if s == "Winter":
        year = y + 1637 if y <= 382 else (2022 if y == 383 else y + 1639)
    else:
        year = y + 1636 if y <= 383 else y + 1638
    return f"{EVENT_NAMES[s]} {year}"


def real_events(seasons: list, pages: dict) -> list:
    out = []
    for s in seasons:
        name = real_event(s)
        info = pages.get(name)
        out.append({"n": name, "u": info["source"] if info else None})
    return out


def first_sentence(body: str, limit: int = 220) -> str:
    for para in body.split("\n\n"):
        text = plain(para).strip()
        if (not text or text.startswith(("#", "|", ">", "*[Image", "-", "---")) or len(text) < 40):
            continue
        text = re.sub(r"[*_`]", "", re.sub(r"\s+", " ", text))
        cut = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
        return cut if len(cut) <= limit else cut[: limit - 1].rsplit(" ", 1)[0] + "…"
    return ""


def name_body(name: str) -> str:
    return "".join("['’]" if ch in "'’" else re.escape(ch) for ch in name)


def name_rx(name: str):
    """A place name as a whole word, with either kind of apostrophe ("Crow's Ridge" = "Crow’s Ridge")."""
    return re.compile(r"(?<![\w'’-])" + name_body(name) + r"(?![\w'’-])")


def build_events() -> dict:
    pages = read_json(DATA / "pages.json")
    terr = territory_polygons()
    regions = territory_regions()
    path_to_terr = {pages[t]["path"]: t for t in terr if t in pages}
    anchors = {t: {r["anchor"]: r["name"] for r in rs} for t, rs in regions.items()}
    from .geometry import extra_territories
    extras = extra_territories()
    # Names to look for in the text: every territory on the map, and each territory's regions.
    tnames = sorted([t for t in terr if not t.startswith("_")], key=len, reverse=True)
    t_rx = {t: name_rx(t) for t in tnames}
    r_rx = {t: {r["name"]: name_rx(r["name"]) for r in rs} for t, rs in regions.items()}
    for t, extra in extras.items():
        r_rx[t] = {n: re.compile(rx) for n, rx in (extra.get("region_match") or {}).items()}
    # Text that names a territory without being about it: who proposed a motion, who donated to a
    # great work, senators' titles, and people's names ("Otmar van Holberg", "Antonio var Tassato").
    not_about = [
        re.compile(r"(?im)^.*\b(proposed|seconded|provided by|withdrawn by)\b.*$"),
        re.compile(r"(?i)\bsenators?\s+(?:for\s+|of\s+)?(?=[A-Z])"),
        re.compile(r"(?<![\w'’-])(?:von|van|vun|de|di|da|del|della|du|var|i)\s+(?=[A-Z])"),
    ]
    surname = re.compile(r"(?<![\w'’-])(?:von|van|vun|de|di|da|del|della|du|var|i)\s+$")
    senator = re.compile(r"(?i)\bsenators?\s+(?:for\s+|of\s+)?$")
    # Lists of who holds which title name every territory as a constituency: link-based places only.
    rosters = re.compile(r"(?i)elections|imperial titles|roll of honou?r|senate sessions|judgements|"
                         r"\bsessions\b|\bvotes?\b|ballot")
    dated = {title: info for title, info in pages.items() if info["ns"] != 14 and info["event"]}
    texts = {title: re.sub(r"(?m)^Categories:.*$", "", not_about[0].sub("", plain(page_body(info))))
             for title, info in dated.items()}
    # Region names that usually mean something else ("Terunael" is mostly the ancient Navarr nation, not
    # the region of Brocéliande): across the dated pages, most mentions come without the territory.
    flat = lambda n: n.replace("’", "'")
    every = sorted({flat(r) for rxs in r_rx.values() for r in rxs}, key=len, reverse=True)
    any_region = re.compile(r"(?<![\w'’-])(" + "|".join(name_body(r) for r in every) + r")(?![\w'’-])")
    said = {title: {flat(m.group(1)) for m in any_region.finditer(x)} for title, x in texts.items()}
    ambiguous = set()
    for t, rxs in r_rx.items():
        if t not in t_rx:
            continue
        for region in rxs:
            hits = [title for title, names in said.items() if flat(region) in names]
            if len(hits) >= 8 and sum(1 for title in hits if t_rx[t].search(texts[title])) < 0.6 * len(hits):
                ambiguous.add((t, region))
    print("ambiguous region names:", sorted(ambiguous))
    counts = collections.Counter()
    counts["ambiguous region names"] = len(ambiguous)
    events = []
    for title, info in dated.items():
        body = page_body(info)
        here = os.path.dirname(info["path"])
        places: dict[str, set] = {}
        for target, frag in LINK.findall(body):
            t = path_to_terr.get(os.path.normpath(os.path.join(here, target)))
            if not t:
                continue
            places.setdefault(t, set())
            if frag and frag in anchors.get(t, {}):
                places[t].add(anchors[t][frag])
        for t, extra in extras.items():  # territories with no wiki page are matched by name
            if extra.get("match") and re.search(extra["match"], body):
                places.setdefault(t, set())
        # Places named in the text but not linked. Sponsor lines ("Proposed by Holberg, seconded by Karsk")
        # name who brought a motion, not where it happens, so they don't count.
        text = texts[title]

        def named(rx):
            for m in rx.finditer(text):
                before = text[max(0, m.start() - 20):m.start()]
                if not surname.search(before) and not senator.search(before):
                    return True
            return False

        if not rosters.search(title):
            for t, rx in t_rx.items():
                if t not in places and named(rx):
                    places.setdefault(t, set())
        for t in list(places):
            for region, rx in r_rx.get(t, {}).items():
                if (t, region) in ambiguous:  # only where the same sentence names the territory too
                    if any(rx.search(x) and t_rx[t].search(x) for x in re.split(r"(?<=[.!?])\s+|\n+", text)):
                        places[t].add(region)
                elif named(rx):
                    places[t].add(region)
        if not places:
            counts["dated pages with no place"] += 1
            continue
        cats = set(info["categories"])
        kind = next((label for label, cs in TYPES if cs & cats), "Other")
        events.append({
            "title": title, "event": info["event"], "type": kind, "class": info["class"],
            "places": {t: sorted(rs) for t, rs in sorted(places.items())},
            "roundup": len(places) > 10,
            "excerpt": first_sentence(body),
            "path": "../wiki/" + info["path"], "source": info["source"],
        })
        counts[kind] += 1
    events.sort(key=lambda e: (event_key(e["event"]), e["type"], e["title"]))

    # Older history: sentences in territory pages that mention a year before play began.
    history = []
    for t in terr:
        if t not in pages:
            continue
        body = page_body(pages[t])
        for sec in re.findall(r"^## (?:Overview|Recent History)\n(.*?)(?=^## |\Z)", body, re.M | re.S):
            for sent in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", plain(sec))):
                years = [(int(y), era) for y, era in YEAR.findall(sent)]
                if not years or len(sent) < 30:
                    continue
                y, era = years[0]
                year = -y if era == "BE" else y
                if year >= 376:
                    continue
                text = re.sub(r"[*_`]", "", sent).strip()
                history.append({"year": year, "territory": t,
                                "text": text if len(text) <= 260 else text[:259].rsplit(" ", 1)[0] + "…",
                                "path": "../wiki/" + pages[t]["path"], "source": pages[t]["source"]})
    history.sort(key=lambda h: (h["year"], h["territory"]))
    seasons = sorted({e["event"] for e in events}, key=event_key)
    return {"events": events, "history": history, "seasons": seasons, "counts": dict(counts),
            "real": real_events(seasons, pages)}


if __name__ == "__main__":
    data = build_events()
    (MAP_DIR / "events.json").write_text(json.dumps(data, ensure_ascii=False))
    print("events:", len(data["events"]), "| seasons:", len(data["seasons"]), data["seasons"][0], "->", data["seasons"][-1])
    print("by type:", data["counts"])
    print("older history entries:", len(data["history"]), "| years", data["history"][0]["year"], "to", data["history"][-1]["year"])
    with_regions = sum(1 for e in data["events"] if any(e["places"].values()))
    print("events naming a region:", with_regions, "| roundups:", sum(e["roundup"] for e in data["events"]))
    per = collections.Counter(t for e in data["events"] for t in e["places"])
    print("territories with events:", len(per), "| busiest:", per.most_common(6), "| quietest:", per.most_common()[-4:])
