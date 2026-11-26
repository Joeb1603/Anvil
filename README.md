# Anvil

Tools for building a personal, offline markdown archive of the
[Empire wiki](https://www.profounddecisions.co.uk/empire-wiki/Main_Page), sorted into
in-character, mixed and out-of-character material and fully indexed.

The wiki's text belongs to Profound Decisions and is **not** stored in this repository.
The repository holds the scraper, the classification rules, and a titles-only index.
Run the scraper to build the archive locally.

## Usage

```
python3 -m scraper.run               # full run: discover, fetch, classify, render, index, verify
python3 -m scraper.run --skip-fetch  # re-sort and re-render from the local cache
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
| Index | `scraper/index.py` | `wiki/indexes/`, `wiki/README.md`, `public-index/titles.md` |
| Verify | `scraper/verify.py` | `data/verify_report.json` |
