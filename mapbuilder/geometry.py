"""Territory outlines from the wiki's clickable Gazetteer map (ImageMap polygons)."""
from __future__ import annotations

import glob
import json
import re

from scraper.common import DATA, ROOT, read_json

MAP_DIR = ROOT / "map"
MASTER_SIZE = (1982, 1618)  # pixel size of the wiki's master map the polygons refer to


def extra_territories() -> dict:
    """Hand-made territories the wiki's map does not include (map/extra_territories.json)."""
    path = MAP_DIR / "extra_territories.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def territory_polygons() -> dict:
    """Return {territory: {"polys": [[[x, y], ...], ...], "has_page": bool}}."""
    src = glob.glob(str(DATA / "wikitext" / "Main" / "Gazetteer-*.wiki"))[0]
    text = open(src, encoding="utf-8").read()
    block = re.search(r"<imagemap>(.*?)</imagemap>", text, re.S | re.I).group(1)
    pages = read_json(DATA / "pages.json")
    out: dict = {}
    for line in block.splitlines():
        m = re.match(r"\s*poly\s+([\d\s]+)\[\[([^\]|#]+)", line, re.I)
        if not m:
            continue
        nums = [int(n) for n in m.group(1).split()]
        pts = [[nums[i], nums[i + 1]] for i in range(0, len(nums) - 1, 2)]
        name = m.group(2).replace("_", " ").strip()
        entry = out.setdefault(name, {"polys": [], "has_page": name in pages})
        entry["polys"].append(pts)
    for name, extra in extra_territories().items():
        out[name] = {"polys": extra["polys"], "has_page": False, "approx": True}
    return out


def map_features() -> dict:
    """Shapes the wiki's map links to a section of a territory page rather than the page itself, such as
    the Great Sinkhole (Miaren#The_Great_Sinkhole): {"The Great Sinkhole": {"territory", "anchor", "polys"}}.
    They stay part of their territory's outline; the build decides which to draw, and from when."""
    src = glob.glob(str(DATA / "wikitext" / "Main" / "Gazetteer-*.wiki"))[0]
    block = re.search(r"<imagemap>(.*?)</imagemap>", open(src, encoding="utf-8").read(), re.S | re.I).group(1)
    out: dict = {}
    for line in block.splitlines():
        m = re.match(r"\s*poly\s+([\d\s]+)\[\[([^\]|#]+)#([^\]|]+)", line, re.I)
        if not m:
            continue
        nums = [int(n) for n in m.group(1).split()]
        anchor = m.group(3).strip()
        name = anchor.replace("_", " ")
        f = out.setdefault(name, {"territory": m.group(2).replace("_", " ").strip(), "anchor": anchor, "polys": []})
        f["polys"].append([[nums[i], nums[i + 1]] for i in range(0, len(nums) - 1, 2)])
    return out


if __name__ == "__main__":
    t = territory_polygons()
    MAP_DIR.mkdir(exist_ok=True)
    (MAP_DIR / "territories.json").write_text(json.dumps(t, ensure_ascii=False))
    xs = [p[0] for v in t.values() for poly in v["polys"] for p in poly]
    ys = [p[1] for v in t.values() for poly in v["polys"] for p in poly]
    print(len(t), "territories;", sum(len(v["polys"]) for v in t.values()), "polygons; x", min(xs), max(xs), "y", min(ys), max(ys))
    print("no page:", sorted(k for k, v in t.items() if not v["has_page"]))
