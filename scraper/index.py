"""Stage 4b: build the indexes under wiki/indexes/, wiki/README.md and the public titles-only index."""
from __future__ import annotations

import collections
import os
import shutil

from .classify import EVENT_RE, event_key
from .common import DATA, WIKI, page_url, read_json, safe_name
from .render import Site, front_matter

CLASS_ORDER = ["in-character", "mixed", "out-of-character", "uncategorised"]
CHRONO = [  # (file stem, heading, wiki categories that define membership)
    ("winds-of-war", "Winds of War", {"Winds of War"}),
    ("winds-of-fortune", "Winds of Fortune", {"Winds of Fortune", "Wind of Fortune", "Wiands of Fortune"}),
    ("winds-of-magic", "Winds of Magic", {"Winds of Magic"}),
    ("trade-winds", "Trade Winds", {"Trade Winds"}),
    ("senate-motions", "Senate motions", {"Senate Motion", "Failed Senate Motion", "Vetoed Senate Motion"}),
    ("mandates", "Mandates", {"Mandate"}),
    ("military-council", "Military Council", {"Military Council"}),
    ("synod", "Synod judgements and results", {"Synod Judgements", "Synod Results"}),
    ("conclave", "Conclave sessions", {"Conclave Sessions"}),
]


LICENCE_TEXT = """# Licence and attribution

The text in this folder comes from the Empire wiki
(https://www.profounddecisions.co.uk/empire-wiki/Main_Page), written and published by
Profound Decisions. Snapshot taken {snapshot}.

Profound Decisions license their games and website content under the
**Creative Commons Attribution-ShareAlike 4.0 International** licence
(https://creativecommons.org/licenses/by-sa/4.0/), as stated in the wiki's terms:
https://www.profounddecisions.co.uk/empire-wiki/Terms_and_conditions

This archive is distributed under that same licence. You may copy, adapt and share it,
including commercially, provided you credit Profound Decisions, link to the licence, say
what you changed, and release your version under the same terms.

## Changes made

- Each wiki page was converted from HTML to markdown; the wording is unchanged.
- Pages were sorted into `in-character`, `mixed` and `out-of-character` folders and indexed.
- Front matter was added to each page: source link, categories, last-edited time, revision.
- Images were replaced by links to the originals.

## Not covered by the licence

The wiki's terms exclude art and music, which stay with their authors.

- **Art and photographs** are not included; only links to them.
- **Music and lyrics** are not included. {held} pages that carry songs appear here as a
  title and a link to the original, or with the song text removed.

Each page's `source` field links to the original, where the full edit history gives
individual authorship.
"""


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
    text = "# Events\n\nImperial years run Spring, Summer, Autumn, Winter.\n\n"
    text += "\n".join(f"- [{ev}]({safe_name(ev)}.md) ({len(events[ev])} pages)" for ev in ordered_events)
    write(f"{here}/README.md", text)

    # --- chronological indexes
    here = "indexes"
    chrono_counts = {}
    for stem, heading, cats in CHRONO:
        rows = [i for i in content if cats & set(i["categories"])]
        chrono_counts[heading] = len(rows)
        dated = collections.defaultdict(list)
        for i in rows:
            dated[i["event"]].append(i)
        text = (f"# {heading}\n\n{len(rows)} pages in the wiki's {' / '.join(sorted(cats))} "
                f"categor{'y' if len(cats) == 1 else 'ies'}, oldest event first.\n")
        for ev in sorted((e for e in dated if e), key=event_key):
            text += f"\n## {ev} ({len(dated[ev])})\n\n" + "\n".join(f"- {link(i, here)}" for i in dated[ev]) + "\n"
        if dated.get(None):
            text += f"\n## Undated ({len(dated[None])})\n\n" + "\n".join(f"- {link(i, here)}" for i in dated[None]) + "\n"
        write(f"{here}/{stem}.md", text)

    # --- per-class indexes grouped by topic
    for cls in CLASS_ORDER[:3]:  # unsorted pages get their own list below
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

    # --- by-category (every category in use, plus category pages with no members)
    here = "indexes/by-category"
    linked = set(read_json(DATA / "linked_categories.json"))
    linked |= {t.split(":", 1)[1] for t in site.path if t.startswith("Category:")}
    all_categories = sorted(set(members) | set(cat_pages) | linked)
    for name in all_categories:
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

    # --- master README
    tally = collections.Counter((i["class"], i["topic"]) for i in content)
    by_class = collections.Counter(i["class"] for i in content)
    m = site.manifest
    text = (f"# Empire wiki archive\n\nSnapshot of {m['site']} ({page_url('Main Page')}) taken {m['snapshot']}.\n"
            "Text © Profound Decisions, reused under [CC BY-SA 4.0](LICENSE.md). Converted from the wiki's HTML to "
            "markdown and re-sorted; wording is unchanged.\n\n"
            f"- **{len(content)}** pages, **{len(cat_pages)}** category pages, **{len(reds)}** redirects\n"
            + "".join(f"- **{by_class[c]}** {c}\n" for c in CLASS_ORDER if by_class[c]) +
            "\n## Indexes\n\n"
            "- [All pages A–Z](indexes/all-pages.md)\n"
            + "".join(f"- [{c} pages by topic](indexes/{c}.md)\n" for c in CLASS_ORDER[:3] if by_class[c])
            + "".join(f"- [{h}](indexes/{s}.md) ({chrono_counts[h]})\n" for s, h, _ in CHRONO) +
            "- [By event](indexes/by-event/README.md)\n- [By category](indexes/by-category/)\n"
            "- [Redirects](indexes/redirects.md)\n- [Unsorted pages](indexes/uncategorised.md)\n\n## Topics\n\n"
            "| Class | Topic | Pages |\n|---|---|---|\n"
            + "\n".join(f"| {c} | [{t}]({c}/{t}/) | {n} |" for (c, t), n in
                        sorted(tally.items(), key=lambda kv: (CLASS_ORDER.index(kv[0][0]), kv[0][1]))))
    write("README.md", text)

    held = sum(1 for i in content if i.get("held_back"))
    write("LICENSE.md", LICENCE_TEXT.format(snapshot=m["snapshot"], held=held))
    return {"pages": len(content), "categories": len(all_categories), "events": len(ordered_events),
            "uncategorised": len(unc), **{f"chrono:{k}": v for k, v in chrono_counts.items()}}


if __name__ == "__main__":
    print(build_indexes())
