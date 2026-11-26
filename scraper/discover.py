"""Stage 1: enumerate every page and redirect. Writes data/manifest.json."""
from __future__ import annotations

from .common import DATA, RAW_NAMESPACES, RENDER_NAMESPACES, Api, write_json


def discover(api: Api) -> dict:
    pages, redirects = [], []
    for ns in list(RENDER_NAMESPACES) + list(RAW_NAMESPACES):
        for filt, bucket in (("nonredirects", pages), ("redirects", redirects)):
            for data in api.query_all(list="allpages", apnamespace=ns, aplimit="500", apfilterredir=filt):
                for p in data["query"]["allpages"]:
                    bucket.append({"pageid": p["pageid"], "ns": p["ns"], "title": p["title"]})
            print(f"  ns {ns:>3} {filt:<12} running total {len(bucket)}", flush=True)

    # Resolve redirect targets, 50 at a time.
    targets: dict[str, dict] = {}
    for i in range(0, len(redirects), 50):
        chunk = redirects[i : i + 50]
        data = api.get(action="query", pageids="|".join(str(r["pageid"]) for r in chunk), redirects="1")
        for r in data["query"].get("redirects", []):
            targets[r["from"]] = {"to": r["to"], "fragment": r.get("tofragment", "")}
    for r in redirects:
        t = targets.get(r["title"], {})
        r["to"] = t.get("to")
        r["fragment"] = t.get("fragment", "")

    stats = api.get(action="query", meta="siteinfo", siprop="general|statistics")["query"]
    manifest = {
        "site": stats["general"]["sitename"],
        "generator": stats["general"]["generator"],
        "snapshot": stats["general"]["time"],
        "statistics": stats["statistics"],
        "pages": pages,
        "redirects": redirects,
    }
    write_json(DATA / "manifest.json", manifest, indent=1)
    return manifest


if __name__ == "__main__":
    m = discover(Api())
    print(f"{len(m['pages'])} pages, {len(m['redirects'])} redirects")
