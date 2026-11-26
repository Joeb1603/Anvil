"""Stage 4b: build the indexes under wiki/indexes/, wiki/README.md and the public titles-only index."""
from __future__ import annotations

import collections
import os
import shutil

from .classify import EVENT_RE, event_key
from .common import DATA, PUBLIC_INDEX, WIKI, page_url, read_json, safe_name
from .render import Site, front_matter

CLASS_ORDER = ["in-character", "mixed", "out-of-character", "uncategorised"]
CHRONO = [  # (file stem, heading, topics)
    ("winds-of-war", "Winds of War", {"winds-of-war"}),
    ("winds-of-fortune", "Winds of Fortune", {"winds-of-fortune"}),
    ("winds-of-magic", "Winds of Magic", {"winds-of-magic"}),
    ("trade-winds", "Trade Winds", {"trade-winds"}),
    ("senate-motions", "Senate motions", {"senate-motions"}),
    ("mandates", "Mandates", {"mandates"}),
]


def link(info: dict, here: str) -> str:
    return f"[{info['title']}]({os.path.relpath(info['path'], here)})"


def write(rel: str, text: str) -> None:
    out = WIKI / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text.rstrip() + "\n", encoding="utf-8")


def build_indexes() -> dict:
    site = Site()
    pages = read_json(DATA / "pages.json")
    shutil.rmtree(WIKI / "indexes", ignore_errors=True)
    content = [i for i in pages.values() if i["ns"] != 14]
    content.sort(key=lambda i: i["title"].lower())
    cat_pages = {i["title"].split(":", 1)[1]: i for i in pages.values() if i["ns"] == 14}

    members = collections.defaultdict(list)
    for i in pages.values():
        for c in i["categories"]:
            members[c].append(i)

    # --- by-category (every category in use, plus category pages with no members)
    here = "indexes/by-category"
    linked = set(read_json(DATA / "linked_categories.json"))
    for name in sorted(set(members) | set(cat_pages) | linked):
        rel = site.category_path(name)
        info = cat_pages.get(name)
        subs = sorted((m for m in members.get(name, []) if m["ns"] == 14), key=lambda m: m["title"])
        mem = sorted((m for m in members.get(name, []) if m["ns"] != 14), key=lambda m: m["title"].lower())
        meta = {"title": f"Category:{name}", "source": page_url("Category:" + name), "members": len(mem)}
        text = front_matter(meta) + f"\n# Category: {name}\n\n"
        if info and info.get("body"):
            text += info["body"] + "\n\n"
        if info and info["categories"]:
            text += "Parent categories: " + ", ".join(
                f"[{c}]({os.path.relpath(site.category_path(c), here)})" for c in info["categories"]) + "\n\n"
        if subs:
            text += "## Subcategories\n\n" + "\n".join(
                f"- [{s['title'].split(':', 1)[1]}]({os.path.relpath(s['path'], here)})" for s in subs) + "\n\n"
        text += f"## Pages ({len(mem)})\n\n" + "\n".join(f"- {link(m, here)} ({m['class']})" for m in mem)
        write(rel, text)

    # --- by-event
    here = "indexes/by-event"
    events = collections.defaultdict(list)
    for i in content:
        if i["event"]:
            events[i["event"]].append(i)
    ordered_events = sorted(events, key=event_key)
    for ev in ordered_events:
        by_topic = collections.defaultdict(list)
        for i in events[ev]:
            by_topic[i["topic"]].append(i)
        text = f"# {ev}\n\nEvery page tagged to this event, grouped by topic ({len(events[ev])} pages).\n"
        for topic in sorted(by_topic):
            text += f"\n## {topic} ({len(by_topic[topic])})\n\n" + "\n".join(
                f"- {link(i, here)}" for i in by_topic[topic]) + "\n"
        write(f"{here}/{safe_name(ev)}.md", text)
    text = "# Events\n\nImperial years run Winter, Spring, Summer, Autumn.\n\n"
    text += "\n".join(f"- [{ev}]({safe_name(ev)}.md) ({len(events[ev])} pages)" for ev in ordered_events)
    write(f"{here}/README.md", text)

    # --- chronological indexes
    here = "indexes"
    chrono_counts = {}
    for stem, heading, topics in CHRONO:
        rows = [i for i in content if i["topic"] in topics]
        chrono_counts[heading] = len(rows)
        dated = collections.defaultdict(list)
        for i in rows:
            dated[i["event"]].append(i)
        text = f"# {heading}\n\n{len(rows)} pages, oldest event first.\n"
        for ev in sorted((e for e in dated if e), key=event_key):
            text += f"\n## {ev} ({len(dated[ev])})\n\n" + "\n".join(f"- {link(i, here)}" for i in dated[ev]) + "\n"
        if dated.get(None):
            text += f"\n## Undated ({len(dated[None])})\n\n" + "\n".join(f"- {link(i, here)}" for i in dated[None]) + "\n"
        write(f"{here}/{stem}.md", text)

    # --- per-class indexes grouped by topic
    for cls in CLASS_ORDER:
        rows = [i for i in content if i["class"] == cls]
        if not rows:
            continue
        by_topic = collections.defaultdict(list)
        for i in rows:
            by_topic[i["topic"]].append(i)
        text = f"# {cls} pages\n\n{len(rows)} pages in {len(by_topic)} topics.\n\n"
        text += "\n".join(f"- [{t}](#{t.replace('/', '')}) ({len(by_topic[t])})" for t in sorted(by_topic)) + "\n"
        for t in sorted(by_topic):
            text += f"\n## {t}\n\n" + "\n".join(f"- {link(i, here)}" for i in by_topic[t]) + "\n"
        write(f"{here}/{cls}.md", text)

    # --- A-Z, redirects, uncategorised
    text = f"# All pages (A–Z)\n\n{len(content)} pages.\n\n| Page | Class | Topic | Event |\n|---|---|---|---|\n"
    text += "\n".join(f"| {link(i, here)} | {i['class']} | {i['topic']} | {i['event'] or ''} |" for i in content)
    write(f"{here}/all-pages.md", text)

    reds = sorted(site.manifest["redirects"], key=lambda r: r["title"].lower())
    text = f"# Redirects (aliases)\n\n{len(reds)} alternative titles.\n\n| Alias | Points to |\n|---|---|\n"
    for r in reds:
        hit = site.resolve(r["title"])
        target = r.get("to") or "(broken redirect)"
        text += f"| {r['title']} | " + (f"[{target}]({os.path.relpath(hit[0], here)})" if hit else target) + " |\n"
    write(f"{here}/redirects.md", text)

    unc = [i for i in content if i["rule"] == "default"]
    text = f"# Uncategorised pages\n\n{len(unc)} pages matched no rule in `scraper/classification.yaml`.\n\n"
    text += "\n".join(f"- {link(i, here)}" for i in unc)
    write(f"{here}/uncategorised.md", text)

    # --- master README
    tally = collections.Counter((i["class"], i["topic"]) for i in content)
    by_class = collections.Counter(i["class"] for i in content)
    m = site.manifest
    text = (f"# Empire wiki archive\n\nSnapshot of {m['site']} ({page_url('Main Page')}) taken {m['snapshot']}.\n"
            "Text © Profound Decisions; this is a personal offline copy.\n\n"
            f"- **{len(content)}** pages, **{len(cat_pages)}** category pages, **{len(reds)}** redirects\n"
            + "".join(f"- **{by_class[c]}** {c}\n" for c in CLASS_ORDER if by_class[c]) +
            "\n## Indexes\n\n"
            "- [All pages A–Z](indexes/all-pages.md)\n"
            + "".join(f"- [{c} pages by topic](indexes/{c}.md)\n" for c in CLASS_ORDER if by_class[c])
            + "".join(f"- [{h}](indexes/{s}.md) ({chrono_counts[h]})\n" for s, h, _ in CHRONO) +
            "- [By event](indexes/by-event/README.md)\n- [By category](indexes/by-category/)\n"
            "- [Redirects](indexes/redirects.md)\n- [Uncategorised](indexes/uncategorised.md)\n\n## Topics\n\n"
            "| Class | Topic | Pages |\n|---|---|---|\n"
            + "\n".join(f"| {c} | [{t}]({c}/{t}/) | {n} |" for (c, t), n in
                        sorted(tally.items(), key=lambda kv: (CLASS_ORDER.index(kv[0][0]), kv[0][1]))))
    write("README.md", text)

    # --- public titles-only index (no page text)
    PUBLIC_INDEX.mkdir(exist_ok=True)
    text = (f"# Empire wiki: titles-only index\n\nSnapshot {m['snapshot']}. Page titles, classification and links to the "
            "original pages only; no wiki text is stored in this repository.\n\n"
            "| Page | Class | Topic | Event |\n|---|---|---|---|\n"
            + "\n".join(f"| [{i['title']}]({i['source']}) | {i['class']} | {i['topic']} | {i['event'] or ''} |"
                        for i in content))
    (PUBLIC_INDEX / "titles.md").write_text(text + "\n", encoding="utf-8")
    return {"pages": len(content), "categories": len(set(members) | set(cat_pages)), "events": len(ordered_events),
            "uncategorised": len(unc), **{f"chrono:{k}": v for k, v in chrono_counts.items()}}


if __name__ == "__main__":
    print(build_indexes())
