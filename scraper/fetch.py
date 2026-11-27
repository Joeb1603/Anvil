"""Stage 2: download pages into .cache/pages/<pageid>.json.gz.

Incremental: every run asks the wiki for each page's latest revision and re-downloads only pages
that are new or have been edited since they were cached. Safe to interrupt and resume."""
from __future__ import annotations

import sys
import time

from .common import DATA, PAGE_CACHE, RAW_NAMESPACES, RENDER_NAMESPACES, Api, read_json, write_json


def fetch(api: Api) -> list[dict]:
    manifest = read_json(DATA / "manifest.json")
    pages = manifest["pages"]
    PAGE_CACHE.mkdir(parents=True, exist_ok=True)
    failures: list[dict] = []

    # Latest revision and edit time of every page, 50 pages per request (about 110 requests).
    stamp_path = PAGE_CACHE.parent / "timestamps.json"
    stamps = {}
    todo = pages
    for i in range(0, len(todo), 50):
        chunk = todo[i : i + 50]
        data = api.get(action="query", prop="revisions", rvprop="ids|timestamp",
                       pageids="|".join(str(p["pageid"]) for p in chunk))
        for p in data["query"]["pages"]:
            rev = (p.get("revisions") or [{}])[0]
            stamps[str(p["pageid"])] = {"revid": rev.get("revid"), "timestamp": rev.get("timestamp")}
        write_json(stamp_path, stamps)
    print(f"timestamps: {len(stamps)}", flush=True)
    # the snapshot is the wiki's latest edit, not the time of this run, so an unchanged wiki changes nothing
    latest_edit = max((v["timestamp"] for v in stamps.values() if v.get("timestamp")), default=None)
    if latest_edit and manifest.get("snapshot") != latest_edit:
        manifest["snapshot"] = latest_edit
        write_json(DATA / "manifest.json", manifest, indent=1)

    started = time.monotonic()
    done = 0
    changed: list[str] = []
    for n, p in enumerate(pages, 1):
        out = PAGE_CACHE / f"{p['pageid']}.json.gz"
        latest = stamps.get(str(p["pageid"]), {}).get("revid")
        if out.exists():
            try:
                cached = read_json(out).get("revid")
            except Exception:
                cached = None
            if cached is not None and (latest is None or cached == latest):
                continue
        changed.append(p["title"])
        try:
            if p["ns"] in RENDER_NAMESPACES:
                data = api.get(action="parse", pageid=p["pageid"],
                               prop="text|wikitext|categories|displaytitle|revid|sections",
                               disablelimitreport="1", disableeditsection="1", disabletoc="1")
                if "parse" not in data:
                    raise RuntimeError(str(data.get("error", data))[:300])
                d = data["parse"]
                rec = {
                    "html": d["text"],
                    "wikitext": d["wikitext"],
                    "categories": [{"name": c["category"].replace("_", " "), "hidden": bool(c.get("hidden")),
                                    "missing": bool(c.get("missing"))} for c in d.get("categories", [])],
                    "displaytitle": d.get("displaytitle"),
                    "revid": d.get("revid"),
                    "sections": [{"level": s["level"], "line": s["line"], "anchor": s["anchor"]}
                                 for s in d.get("sections", [])],
                }
            else:  # raw namespaces: wikitext only
                data = api.get(action="query", prop="revisions", rvprop="ids|content", rvslots="main",
                               pageids=p["pageid"])
                rev = data["query"]["pages"][0]["revisions"][0]
                rec = {"html": None, "wikitext": rev["slots"]["main"]["content"], "categories": [],
                       "displaytitle": None, "revid": rev["revid"], "sections": []}
            rec.update(pageid=p["pageid"], ns=p["ns"], title=p["title"],
                       timestamp=stamps.get(str(p["pageid"]), {}).get("timestamp"))
            write_json(out, rec)
            done += 1
        except Exception as exc:  # keep going; report at the end
            failures.append({"pageid": p["pageid"], "title": p["title"], "error": str(exc)[:300]})
            print(f"FAIL {p['title']}: {exc}", flush=True)
        if done and done % 100 == 0:
            rate = done / (time.monotonic() - started)
            print(f"{n}/{len(pages)} fetched this run: {done} ({rate:.2f}/s)", flush=True)
            done += 0
    write_json(PAGE_CACHE.parent / "failures.json", failures, indent=1)
    write_json(PAGE_CACHE.parent / "changed.json", changed, indent=1)
    print(f"new or edited pages downloaded: {len(changed)}", flush=True)
    cached = sum(1 for _ in PAGE_CACHE.glob("*.json.gz"))
    print(f"DONE cached={cached} of {len(pages)} failures={len(failures)}", flush=True)
    return failures


if __name__ == "__main__":
    sys.exit(1 if fetch(Api()) else 0)
