"""Stage 3: assign every page a class (in-character / mixed / out-of-character) and a topic.

All decisions come from scraper/classification.yaml, so they can be corrected and re-run.
"""
from __future__ import annotations

import collections
import re

import yaml

from .common import DATA, MAPPING, PAGE_CACHE, RENDER_NAMESPACES, read_json, write_json

EVENT_RE = re.compile(r"^(\d{3})YE (Spring|Summer|Autumn|Winter)$")
TITLE_EVENT_RE = re.compile(r"(\d{3})\s?YE (Spring|Summer|Autumn|Winter)")
# The Winter Solstice is the last summit of an Imperial year.
SEASON_ORDER = {"Spring": 0, "Summer": 1, "Autumn": 2, "Winter": 3}


def event_key(event: str):
    m = EVENT_RE.match(event)
    return (int(m.group(1)), SEASON_ORDER[m.group(2)])


class Classifier:
    def __init__(self) -> None:
        cfg = yaml.safe_load(MAPPING.read_text(encoding="utf-8"))
        self.cfg = cfg
        self.ignore = set(cfg.get("ignore_categories", []))
        self.ignore_prefixes = tuple(cfg.get("ignore_category_prefixes", []))
        self.title_rules = [(re.compile(r["pattern"]), r) for r in cfg.get("title_rules", [])]
        self.fallback_title_rules = [(re.compile(r["pattern"]), r) for r in cfg.get("fallback_title_rules", [])]
        self.rules = cfg["rules"]
        self.by_cat: dict[str, tuple[int, dict]] = {}
        for i, rule in enumerate(self.rules):
            for cat in rule["categories"]:
                self.by_cat.setdefault(cat, (i, rule))
        self.overrides = cfg.get("page_overrides", {})
        self.song_pages = cfg.get("song_pages")
        self.ns_defaults = cfg.get("namespace_defaults", {})
        self.ns_forced = set(cfg.get("namespace_forced", []))
        self.default = cfg["default"]

    def usable(self, cats):
        return [c for c in cats if c not in self.ignore and not c.startswith(self.ignore_prefixes)]

    def classify(self, title: str, ns: int, cats: list[str], has_song: bool = False) -> dict:
        cats = self.usable(cats)
        events = sorted((c for c in cats if EVENT_RE.match(c)), key=event_key)
        event = events[0] if events else None
        if not event:
            m = TITLE_EVENT_RE.search(title)
            if m:
                event = f"{m.group(1)}YE {m.group(2)}"
        topical = [c for c in cats if not EVENT_RE.match(c)]

        def result(rule, why):
            return {"class": rule["class"], "topic": rule["topic"], "event": event, "rule": why,
                    "categories": cats}

        if title in self.overrides:
            return result(self.overrides[title], "override")
        if RENDER_NAMESPACES.get(ns, "") in self.ns_forced:
            return result(self.ns_defaults[RENDER_NAMESPACES[ns]], f"namespace:{RENDER_NAMESPACES[ns]}")
        for rx, rule in self.title_rules:
            if rx.search(title):
                return result(rule, f"title:{rx.pattern}")
        hits = sorted((self.by_cat[c] for c in topical if c in self.by_cat), key=lambda t: t[0])
        if hits:
            return result(hits[0][1], "category:" + next(c for c in topical if self.by_cat.get(c, (None,))[0] == hits[0][0]))
        if has_song and self.song_pages and ns == 0:
            return result(self.song_pages, "song-block")
        ns_name = RENDER_NAMESPACES.get(ns, "")
        if ns_name in self.ns_defaults:
            return result(self.ns_defaults[ns_name], f"namespace:{ns_name}")
        for rx, rule in self.fallback_title_rules:
            if rx.search(title):
                return result(rule, f"fallback-title:{rx.pattern}")
        return result(self.default, "default")


def classify_all() -> dict:
    manifest = read_json(DATA / "manifest.json")
    clf = Classifier()
    out, unmapped = {}, collections.Counter()
    for p in manifest["pages"]:
        if p["ns"] not in RENDER_NAMESPACES:
            continue
        path = PAGE_CACHE / f"{p['pageid']}.json.gz"
        if not path.exists():
            continue
        rec = read_json(path)
        cats = [c["name"] for c in rec["categories"]]
        res = clf.classify(p["title"], p["ns"], cats, has_song='class="song"' in (rec["html"] or ""))
        out[str(p["pageid"])] = res
        for c in res["categories"]:
            if c not in clf.by_cat and not EVENT_RE.match(c) and not re.fullmatch(r"\d{3}YE", c):
                unmapped[c] += 1
    write_json(DATA / "classification.json", out, indent=1)
    write_json(DATA / "unmapped_categories.json", dict(unmapped.most_common()), indent=1)
    return out


if __name__ == "__main__":
    res = classify_all()
    tally = collections.Counter((r["class"], r["topic"]) for r in res.values())
    for (cls, topic), n in sorted(tally.items()):
        print(f"{n:5}  {cls}/{topic}")
    print("by class:", dict(collections.Counter(r["class"] for r in res.values())))
