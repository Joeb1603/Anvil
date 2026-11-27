"""Should today's scheduled update run?

Runs on Mondays, and on any day while campaign reports (Winds of Fortune or Winds of War) are being
published: new pages in those categories in the last 21 days mean a summit is near. Prints the
decision and, under GitHub Actions, writes run=true/false to $GITHUB_OUTPUT.

    python3 -m scraper.check_schedule [--force]
"""
from __future__ import annotations

import datetime as dt
import os
import sys

from .common import Api

WINDOW_DAYS = 21
CATEGORIES = ["Category:Winds of Fortune", "Category:Winds of War"]


def recent_reports(api: Api, days: int = WINDOW_DAYS) -> list[str]:
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    titles = []
    for data in api.query_all(list="recentchanges", rctype="new", rcnamespace="0", rcend=since,
                              rcprop="title", rclimit="500"):
        titles += [c["title"] for c in data["query"]["recentchanges"]]
    found = []
    for i in range(0, len(titles), 50):
        data = api.get(action="query", prop="categories", titles="|".join(titles[i:i + 50]),
                       clcategories="|".join(CATEGORIES), cllimit="max")
        found += [p["title"] for p in data["query"]["pages"] if p.get("categories")]
    return sorted(found)


def decide(force: bool = False) -> tuple[bool, str]:
    if force:
        return True, "run requested"
    today = dt.datetime.now(dt.timezone.utc)
    if today.weekday() == 0:
        return True, "weekly Monday update"
    reports = recent_reports(Api())
    if reports:
        return True, f"summit approaching: {len(reports)} new campaign reports in the last {WINDOW_DAYS} days"
    return False, "no new campaign reports in the last three weeks; waiting for Monday"


if __name__ == "__main__":
    run, reason = decide("--force" in sys.argv)
    print(("RUN: " if run else "SKIP: ") + reason)
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"run={'true' if run else 'false'}\nreason={reason}\n")
