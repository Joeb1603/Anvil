"""Run the whole pipeline:  python3 -m scraper.run [--skip-fetch]"""
from __future__ import annotations

import sys

from .classify import classify_all
from .common import Api
from .discover import discover
from .fetch import fetch
from .index import build_indexes
from .render import render_all
from .verify import verify


def main() -> None:
    if "--skip-fetch" not in sys.argv:
        api = Api()
        print("discover:", {k: len(v) for k, v in discover(api).items() if isinstance(v, list)})
        print("fetch failures:", len(fetch(api)))
    print("classified:", len(classify_all()))
    print("render:", render_all())
    print("index:", build_indexes())
    report = verify()
    print("verify:", {k: (len(v) if isinstance(v, list) else v) for k, v in report.items()})


if __name__ == "__main__":
    main()
