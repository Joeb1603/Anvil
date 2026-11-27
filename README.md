# Anvil

Tools for building a personal, offline markdown archive of the
[Empire wiki](https://www.profounddecisions.co.uk/empire-wiki/Main_Page), sorted into
in-character, mixed and out-of-character material and fully indexed.

The wiki's text is written by Profound Decisions and licensed under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), as set out in the wiki's
[terms](https://www.profounddecisions.co.uk/empire-wiki/Terms_and_conditions). The archive in
`wiki/` is shared under the same licence; see `wiki/LICENSE.md` for attribution and the list
of changes. Art and music are excluded from that licence, so images appear only as links and
pages carrying songs appear as a title and a link.

## Empire Atlas

`map/index.html` is an interactive map with a timeline, built from the archive: who held each
territory and region season by season, and what happened where. See `map/README.md` for how it
is made and how far to trust each layer.

## Usage

```
python3 -m scraper.run               # full run: discover, fetch, classify, render, index, verify
python3 -m scraper.run --skip-fetch  # re-sort and re-render from the local cache
python3 -m scraper.package           # zip the complete archive, song pages included
```

Requires Python 3.10+ with `requests`, `beautifulsoup4`, `lxml`, `markdownify` and `PyYAML`.
The fetch is single-threaded at about two requests per second and resumes where it stopped.

## Output

```
wiki/
  README.md                       master index
  in-character/<topic>/…          setting material: winds of war and fortune, history, nations, religion
  mixed/<topic>/…                 lore that carries game rules: rituals, items, titles
  out-of-character/<topic>/…      rules, events, costume, game design
  indexes/                        A–Z, by class, by category, by event, chronological lists, redirects
data/
  manifest.json                   every page and redirect on the wiki
  pages.json                      per-page metadata and classification
  wikitext/                       raw wiki source for every page and template
local-only/                       complete copies of pages that hold songs (not committed)
```

Each markdown file starts with front matter: title, source URL, class, topic, categories,
event, last-edited time and revision, and any redirect aliases.

## Changing how pages are sorted

Every decision lives in `scraper/classification.yaml`. A page takes the first rule that lists
one of its categories. Edit the file and run with `--skip-fetch`.

## Pipeline

| Stage | Module | Result |
|---|---|---|
| Discover | `scraper/discover.py` | `data/manifest.json` |
| Fetch | `scraper/fetch.py` | `.cache/pages/` (rendered HTML and wikitext per page) |
| Classify | `scraper/classify.py` | `data/classification.json` |
| Render | `scraper/render.py` | `wiki/<class>/<topic>/*.md`, `data/wikitext/` |
| Index | `scraper/index.py` | `wiki/indexes/`, `wiki/README.md`, `wiki/LICENSE.md` |
| Verify | `scraper/verify.py` | `data/verify_report.json` |
