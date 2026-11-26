"""Checks: completeness against the manifest, and internal links that point nowhere."""
from __future__ import annotations

import collections
import os
import re

from .common import DATA, PAGE_CACHE, RENDER_NAMESPACES, WIKI, read_json

LINK_RE = re.compile(r"\]\(([^)\s]+)\)")


def verify() -> dict:
    manifest = read_json(DATA / "manifest.json")
    pages = read_json(DATA / "pages.json")
    missing_cache = [p["title"] for p in manifest["pages"] if not (PAGE_CACHE / f"{p['pageid']}.json.gz").exists()]
    expected = [p for p in manifest["pages"] if p["ns"] in RENDER_NAMESPACES]
    missing_files = [p["title"] for p in expected
                     if p["title"] not in pages or not (WIKI / pages[p["title"]]["path"]).exists()]
    paths = collections.Counter(i["path"].lower() for i in pages.values())
    dupes = [p for p, n in paths.items() if n > 1]
    broken = collections.Counter()
    checked = 0
    for root, _dirs, files in os.walk(WIKI):
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            in_code = False
            for line in open(full, encoding="utf-8"):
                for target in LINK_RE.findall(line):
                    if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                        continue
                    checked += 1
                    path = target.split("#", 1)[0]
                    if path and not os.path.exists(os.path.normpath(os.path.join(root, path))):
                        broken[(os.path.relpath(full, WIKI), target)] += 1
    md_files = sum(1 for _r, _d, fs in os.walk(WIKI) for f in fs if f.endswith(".md"))
    report = {"manifest_pages": len(manifest["pages"]), "expected_rendered": len(expected),
              "missing_from_cache": missing_cache, "missing_output_files": missing_files,
              "duplicate_paths": dupes, "markdown_files": md_files, "relative_links_checked": checked,
              "broken_relative_links": [list(k) for k in list(broken)[:200]], "broken_count": len(broken)}
    (DATA / "verify_report.json").write_text(__import__("json").dumps(report, indent=1, ensure_ascii=False))
    return report


if __name__ == "__main__":
    r = verify()
    for k, v in r.items():
        print(k, ":", v if not isinstance(v, list) else f"{len(v)} {v[:8]}")
