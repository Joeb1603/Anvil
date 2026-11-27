"""Region lists per territory, read from the 'Regions' section of each territory page."""
from __future__ import annotations

import json
import re

from scraper.common import DATA, LOCAL, WIKI, read_json
from scraper.render import slug

from .geometry import MAP_DIR, territory_polygons


NOT_REGIONS = {"strategic considerations", "ooc notes", "ooc note", "further reading"}


def page_body(info: dict) -> str:
    path = (LOCAL / "wiki" / info["path"]) if info.get("held_back") else (WIKI / info["path"])
    return path.read_text(encoding="utf-8").split("\n---\n", 1)[1]


def plain(text: str) -> str:
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text).strip()


def territory_regions() -> dict:
    """{territory: [{"name", "anchor", "words"}]} for every territory with a page."""
    pages = read_json(DATA / "pages.json")
    out = {}
    polys = territory_polygons()
    for name, t in polys.items():
        if not t["has_page"]:
            continue
        body = page_body(pages[name])
        m = re.search(r"^## (?:Regions[^\n]*|Territories)\n(.*?)(?=^## |\Z)", body, re.M | re.S)
        regions = []
        if m:
            for sec in re.split(r"^### ", m.group(1), flags=re.M)[1:]:
                head, _, rest = sec.partition("\n")
                title = plain(head)
                if title.lower() in NOT_REGIONS or (title in polys and title != name):
                    continue  # a heading, or a part that has its own outline on the map
                regions.append({"name": title, "anchor": slug(title), "words": len(rest.split())})
        out[name] = regions
    return out


if __name__ == "__main__":
    r = territory_regions()
    (MAP_DIR / "regions.json").write_text(json.dumps(r, ensure_ascii=False, indent=1))
    print(sum(1 for v in r.values() if v), "territories with regions;", sum(len(v) for v in r.values()), "regions")
