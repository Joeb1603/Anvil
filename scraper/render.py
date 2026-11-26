"""Stage 4a: convert cached HTML to markdown files under wiki/, plus raw wikitext under data/."""
from __future__ import annotations

import os
import re
import shutil
from urllib.parse import unquote

import yaml
from bs4 import BeautifulSoup, Comment, NavigableString
from markdownify import markdownify

from .common import (DATA, LOCAL, MAPPING, PAGE_CACHE, RAW_NAMESPACES, RENDER_NAMESPACES, SITE, WIKI, norm_title,
                     page_url, read_json, safe_name, write_json)

BR = "⟨BR⟩"  # placeholder for line breaks inside table cells


def slug(fragment: str) -> str:
    """Approximate GitHub-style heading anchor for a MediaWiki section anchor."""
    text = unquote(fragment).replace("_", " ").lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "-", text.strip())


class Site:
    """Title -> output path lookup, shared by rendering and indexing."""

    def __init__(self) -> None:
        self.manifest = read_json(DATA / "manifest.json")
        self.classes = read_json(DATA / "classification.json")
        self.pages = [p for p in self.manifest["pages"] if p["ns"] in RENDER_NAMESPACES
                      and str(p["pageid"]) in self.classes]
        self.raw_pages = [p for p in self.manifest["pages"] if p["ns"] in RAW_NAMESPACES]
        self.path: dict[str, str] = {}
        used: set[str] = set()
        for p in sorted(self.pages, key=lambda p: p["pageid"]):
            c = self.classes[str(p["pageid"])]
            if p["ns"] == 14:
                rel = f"indexes/by-category/{safe_name(p['title'].split(':', 1)[1])}.md"
            else:
                rel = f"{c['class']}/{c['topic']}/{safe_name(p['title'])}.md"
            if rel.lower() in used:
                rel = rel[:-3] + f"-{p['pageid']}.md"
            used.add(rel.lower())
            self.path[p["title"]] = rel
        self.used = used
        self.redirect = {r["title"]: (r.get("to"), r.get("fragment") or "") for r in self.manifest["redirects"]}
        self.aliases: dict[str, list[str]] = {}
        for src, (to, _frag) in self.redirect.items():
            if to:
                self.aliases.setdefault(to, []).append(src)

    def category_path(self, name: str) -> str:
        """Path of the index page for a category, whether or not it has a wiki page."""
        title = "Category:" + name
        if title not in self.path:
            rel = f"indexes/by-category/{safe_name(name)}.md"
            if rel.lower() in self.used:
                rel = rel[:-3] + "-cat.md"
            self.used.add(rel.lower())
            self.path[title] = rel
        return self.path[title]

    def resolve(self, title: str):
        """Return (relative path, fragment) for a wiki title, following redirects; None if unknown."""
        title = norm_title(title)
        frag = ""
        for _ in range(4):
            if title in self.path:
                return self.path[title], frag
            if title in self.redirect and self.redirect[title][0]:
                title, frag = self.redirect[title]
                title = norm_title(title)
                continue
            break
        if title.startswith("Category:"):
            return self.category_path(title.split(":", 1)[1]), ""
        return None


SONG_NOTE = "Song text omitted: music and lyrics belong to their authors and are not covered by the wiki's licence."


def html_to_markdown(html: str, site: Site, current: str, stats: dict, strip_songs: bool = False,
                     source: str = "") -> str:
    soup = BeautifulSoup(html, "lxml")
    root = soup.select_one(".mw-parser-output") or soup.body or soup
    songs = [b for b in root.select("div.song") if not b.find_parent(class_="song")]
    stats["songs"] += len(songs)
    if strip_songs:
        for box in songs:
            p = soup.new_tag("p")
            em = soup.new_tag("em")
            em.string = SONG_NOTE + " "
            link = soup.new_tag("a", href=source)
            link.string = "See the original page."
            em.append(link)
            p.append(em)
            box.replace_with(p)
    for c in root.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for el in root.select(".mw-editsection, .toc, #toc, script, style, .mw-empty-elt, .noprint"):
        el.decompose()

    here = os.path.dirname(current)

    def rel(target: str) -> str:
        return os.path.relpath(target, here).replace(os.sep, "/")

    # Images: text-only archive, so each becomes a link to the original.
    for box in root.select("div.captioned-image"):
        a = box.find("a", href=True)
        cap = box.select_one(".caption")
        label = cap.get_text(" ", strip=True) if cap else ""
        img = box.find("img")
        label = label or (img.get("alt") if img else "") or "image"
        p = soup.new_tag("p")
        em = soup.new_tag("em")
        link = soup.new_tag("a", href=(a["href"] if a else (img.get("src") if img else "#")))
        link.string = f"Image: {label}"
        em.append(link)
        p.append(em)
        box.replace_with(p)
        stats["images"] += 1
    for img in root.find_all("img"):
        parent = img.parent if img.parent and img.parent.name == "a" else None
        link = soup.new_tag("a", href=(parent.get("href") if parent else img.get("src", "#")))
        link.string = f"Image: {img.get('alt') or os.path.basename(img.get('src', 'image'))}"
        (parent or img).replace_with(link)
        stats["images"] += 1

    # The wiki's own in-character boxes, quotes, songs and call-out boxes become block quotes.
    for box in root.select("div.ic, div.quote, div.song, div.box"):
        if box.find_parent(class_=["ic", "quote", "song", "box"]):
            continue
        classes = set(box.get("class", []))
        quote = soup.new_tag("blockquote")
        if "ic" in classes or box.select_one(".ic-inner") or "ic-inner" in classes:
            marker = soup.new_tag("p")
            em = soup.new_tag("em")
            em.string = "In-character text:"
            marker.append(em)
            quote.append(marker)
            stats["ic_boxes"] += 1
        box.wrap(quote)
        quote.append(box)  # keep marker first
        box.unwrap()
    for inner in root.select(".ic-inner, .box-inner"):
        inner.unwrap()

    # Links.
    for a in root.find_all("a"):
        href = a.get("href")
        if not href:
            a.unwrap()
            continue
        if "new" in a.get("class", []) or "redlink=1" in href:
            a.unwrap()
            stats["redlinks"] += 1
            continue
        if href.startswith("#"):
            a["href"] = "#" + slug(href[1:])
        elif href.startswith("/empire-wiki/"):
            target, _, frag = unquote(href[len("/empire-wiki/"):]).partition("#")
            hit = None if target.startswith(("File:", "Media:", "Special:")) else site.resolve(target)
            if hit:
                path, rfrag = hit
                frag = frag or rfrag
                a["href"] = rel(path) + ("#" + slug(frag) if frag else "")
                stats["internal"] += 1
            else:
                a["href"] = SITE + href
                if not target.startswith(("File:", "Media:", "Special:")):
                    stats["unresolved"].add(norm_title(target))
        elif href.startswith("//"):
            a["href"] = "https:" + href
        elif href.startswith("/"):
            a["href"] = SITE + href
        for attr in ("title", "class", "rel"):
            a.attrs.pop(attr, None)

    for span in root.select("span.mw-headline"):
        span.unwrap()

    # Tables: keep each cell on one line so pipe tables survive.
    for table in reversed(root.find_all("table")):
        if table.find_parent("table"):
            table.replace_with(NavigableString(table.get_text(" ", strip=True)))
            continue
        for cell in table.find_all(["td", "th"]):
            for br in cell.find_all("br"):
                br.replace_with(NavigableString(BR))
            for li in cell.find_all("li"):
                li.insert(0, NavigableString("• "))
                li.append(NavigableString(BR))
                li.unwrap()
            for blk in cell.find_all(["p", "div", "ul", "ol", "blockquote"]):
                blk.append(NavigableString(BR))
                blk.unwrap()
            for h in cell.find_all(re.compile(r"^h[1-6]$")):
                h.name = "strong"
                h.insert_after(NavigableString(BR))
        if not table.find("th"):
            first = table.find("tr")
            if first and len(table.find_all("tr")) > 1:
                pass  # markdownify will emit an empty header row

    md = markdownify(str(root), heading_style="ATX", bullets="-", strong_em_symbol="*")
    md = md.replace("\r", "")
    md = re.sub(rf"(\s*{BR}\s*)+", " <br> ", md)
    md = re.sub(r" <br> (?=\|)", " ", md)          # no trailing break before a cell edge
    md = re.sub(r"(?<=\|) <br> ", " ", md)
    md = "\n".join(line.rstrip() if not line.endswith("  ") else line.rstrip() + "  " for line in md.split("\n"))
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    return md


def front_matter(meta: dict) -> str:
    return "---\n" + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=1000) + "---\n"


def new_stats() -> dict:
    return {"images": 0, "ic_boxes": 0, "redlinks": 0, "internal": 0, "songs": 0, "unresolved": set()}


def render_all() -> dict:
    site = Site()
    for sub in ("in-character", "mixed", "out-of-character", "uncategorised"):
        shutil.rmtree(WIKI / sub, ignore_errors=True)
    shutil.rmtree(DATA / "wikitext", ignore_errors=True)
    shutil.rmtree(LOCAL, ignore_errors=True)
    # Topics the wiki's CC BY-SA licence does not cover (music stays with its authors).
    restricted = set(yaml.safe_load(MAPPING.read_text(encoding="utf-8")).get("not_openly_licensed_topics", []))
    totals = {"files": 0, "images": 0, "ic_boxes": 0, "redlinks": 0, "internal": 0, "songs": 0,
              "stubbed_pages": 0, "pages_with_songs_removed": 0}
    unresolved: dict[str, int] = {}
    page_info = {}
    for p in site.pages:
        rec = read_json(PAGE_CACHE / f"{p['pageid']}.json.gz")
        c = site.classes[str(p["pageid"])]
        ns_dir = RENDER_NAMESPACES[p["ns"]] or "Main"
        rel = site.path[p["title"]]
        source = page_url(p["title"])
        stats = new_stats()
        body = html_to_markdown(rec["html"] or "", site, rel, stats)      # complete text
        stub = c["topic"] in restricted and p["ns"] != 14
        held_back = stub or stats["songs"] > 0                             # needs a public variant
        raw_root = (LOCAL / "data" / "wikitext") if held_back else (DATA / "wikitext")
        raw = raw_root / ns_dir / (safe_name(p["title"]) + f"-{p['pageid']}.wiki")
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text(rec["wikitext"] or "", encoding="utf-8")
        full_body = body
        if stub:
            body = (f"*This page holds music or lyrics, which belong to their authors and are not covered by the "
                    f"wiki's licence, so its text is not included here.* [Read it on the wiki.]({source})")
            totals["stubbed_pages"] += 1
        elif held_back:
            body = html_to_markdown(rec["html"] or "", site, rel, new_stats(), strip_songs=True, source=source)
            totals["pages_with_songs_removed"] += 1
        info = {"pageid": p["pageid"], "ns": p["ns"], "title": p["title"], "path": rel,
                "class": c["class"], "topic": c["topic"], "event": c["event"], "categories": c["categories"],
                "rule": c["rule"], "revision": rec.get("revid"), "last_edited": rec.get("timestamp"),
                "aliases": sorted(site.aliases.get(p["title"], [])), "ic_boxes": stats["ic_boxes"],
                "words": len(full_body.split()), "source": source, "held_back": held_back}
        page_info[p["title"]] = info
        for t in stats["unresolved"]:
            unresolved[t] = unresolved.get(t, 0) + 1
        for k in ("images", "ic_boxes", "redlinks", "internal", "songs"):
            totals[k] += stats[k]
        if p["ns"] == 14:
            info["body"] = body  # category description; written by the index stage
            continue
        meta = {"title": p["title"], "source": info["source"], "class": c["class"], "topic": c["topic"],
                "categories": c["categories"]}
        if c["event"]:
            meta["event"] = c["event"]
        meta["last_edited"] = info["last_edited"]
        meta["revision"] = info["revision"]
        if info["aliases"]:
            meta["aliases"] = info["aliases"]
        if stats["ic_boxes"]:
            meta["in_character_boxes"] = stats["ic_boxes"]
        here = os.path.dirname(rel)
        cats = ", ".join(f"[{n}]({os.path.relpath(site.category_path(n), here)})" for n in c["categories"])
        tail = f"\n---\n\nCategories: {cats}\n" if cats else ""
        variants = [(WIKI / rel, body)]
        if held_back:
            variants.append((LOCAL / "wiki" / rel, full_body))             # complete copy, kept off GitHub
        for out, text_body in variants:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(front_matter(meta) + f"\n# {p['title']}\n\n{text_body}\n" + tail, encoding="utf-8")
        totals["files"] += 1
    for p in site.raw_pages:
        path = PAGE_CACHE / f"{p['pageid']}.json.gz"
        if not path.exists():
            continue
        rec = read_json(path)
        raw = DATA / "wikitext" / RAW_NAMESPACES[p["ns"]] / (safe_name(p["title"].split(":", 1)[1]) + f"-{p['pageid']}.wiki")
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text(rec["wikitext"] or "", encoding="utf-8")
    write_json(DATA / "pages.json", page_info, indent=1)
    write_json(DATA / "linked_categories.json",
               sorted(t.split(":", 1)[1] for t in site.path if t.startswith("Category:")), indent=1)
    write_json(DATA / "unresolved_links.json", dict(sorted(unresolved.items(), key=lambda kv: -kv[1])), indent=1)
    totals["unresolved_targets"] = len(unresolved)
    return totals


if __name__ == "__main__":
    print(render_all())
