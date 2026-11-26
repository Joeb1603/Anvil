"""Shared settings and a polite MediaWiki API client."""
from __future__ import annotations

import gzip
import json
import re
import time
from pathlib import Path

import requests

SITE = "https://www.profounddecisions.co.uk"
API = SITE + "/mediawiki-public/api.php"
ARTICLE_URL = SITE + "/empire-wiki/"
USER_AGENT = "wiki-archiver/1.0 (personal offline archive; low request rate)"

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
PAGE_CACHE = CACHE / "pages"
DATA = ROOT / "data"
WIKI = ROOT / "wiki"
PUBLIC_INDEX = ROOT / "public-index"
MAPPING = Path(__file__).resolve().parent / "classification.yaml"

# Namespaces rendered to markdown, and those kept as raw wikitext only.
RENDER_NAMESPACES = {0: "", 14: "Category", 500: "Archive", 12: "Help", 700: "Crew", 600: "Draft"}
RAW_NAMESPACES = {10: "Template"}

MIN_INTERVAL = 0.5  # seconds between requests (about 2 per second)


class Api:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self._last = 0.0

    def get(self, **params) -> dict:
        params.setdefault("format", "json")
        params.setdefault("formatversion", "2")
        delay = 2.0
        for attempt in range(7):
            wait = MIN_INTERVAL - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                r = self.session.get(API, params=params, timeout=90)
                if r.status_code == 200:
                    data = r.json()
                    if "error" in data and data["error"].get("code") in ("ratelimited", "maxlag", "readonly"):
                        raise RuntimeError(data["error"]["code"])
                    return data
                if r.status_code not in (429, 500, 502, 503, 504):
                    r.raise_for_status()
            except (requests.RequestException, ValueError, RuntimeError) as exc:  # retry below
                last = exc
            else:
                last = RuntimeError(f"http {r.status_code}")
            time.sleep(delay)
            delay = min(delay * 2, 120)
        raise RuntimeError(f"giving up on {params}: {last}")

    def query_all(self, **params):
        """Yield each response of a continued query."""
        cont: dict = {}
        while True:
            data = self.get(action="query", **params, **cont)
            yield data
            if "continue" not in data:
                return
            cont = data["continue"]


def read_json(path: Path):
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj, indent=None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    if path.suffix == ".gz":
        with gzip.open(tmp, "wt", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False)
    else:
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=indent), encoding="utf-8")
    tmp.replace(path)


def page_url(title: str) -> str:
    from urllib.parse import quote

    return ARTICLE_URL + quote(title.replace(" ", "_"), safe="/:(),'!*~-._")


_BAD = re.compile(r"[^\w.-]+", re.UNICODE)


def safe_name(title: str) -> str:
    """Filesystem- and markdown-link-safe file stem for a page title."""
    name = _BAD.sub("-", title.replace(" ", "_")).strip("._-")
    name = re.sub(r"-{2,}", "-", name)
    return name[:150] or "untitled"


def norm_title(title: str) -> str:
    """Normalise a link target the way MediaWiki does (underscores, first letter)."""
    title = re.sub(r"\s+", " ", title.replace("_", " ")).strip()
    if ":" in title:
        ns, rest = title.split(":", 1)
        if ns.strip().lower() in ("category", "archive", "help", "crew", "draft", "template", "file"):
            rest = rest.strip()
            return ns.strip().capitalize() + ":" + rest[:1].upper() + rest[1:]
    return title[:1].upper() + title[1:]
