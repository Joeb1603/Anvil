"""Written summaries for every event: an overview, a longer description, and what it means for each
nation, territory and region the atlas attaches it to.

    python3 -m mapbuilder.summarise --dry-run            # what would be sent, and the estimated cost
    python3 -m mapbuilder.summarise --limit 20           # summarise up to 20 events now (direct calls)
    python3 -m mapbuilder.summarise --batch              # submit everything outstanding as one batch
    python3 -m mapbuilder.summarise --collect            # fetch a finished batch's results

Needs ANTHROPIC_API_KEY (a GitHub Actions secret in the workflows); without it nothing is sent and the
page falls back to each page's first sentence. Results go to map/summaries.json, keyed by page title,
and an event is only sent again when its page, its places or the prompt change.

Budget: real usage from every response is added to map/summaries_cost.json. A run whose estimate would
take the running total past BUDGET is refused, and submission stops once it is reached.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time

from scraper.common import DATA, ROOT, read_json

from .geometry import MAP_DIR

MODEL = "claude-opus-5-5"
EFFORT = os.environ.get("SUMMARY_EFFORT", "high")
PROMPT_VERSION = 1
BUDGET = 95.0                         # US dollars, all runs together
PRICE = {"in": 4.0, "out": 20.0, "cache_read": 0.40, "cache_write": 5.0}  # $ per million tokens
BATCH_DISCOUNT = 0.5
OUT = MAP_DIR / "summaries.json"
COST = MAP_DIR / "summaries_cost.json"
PENDING = MAP_DIR / "summaries_batch.json"

SYSTEM = """You write short, accurate summaries of pages from the Empire LARP wiki for an interactive map of the setting.

You are given one page (a Wind of War, Wind of Fortune, Senate motion, Synod judgement, Military Council order or similar) and the places and nations the map attaches it to, with who held each place at the time.

Write:
- overview: one or two sentences saying what happened or what the page is, in plain past-tense prose. Lead with the substance, not "This page describes".
- detail: a concise fuller description, at most about 110 words: the key facts, who did what, outcomes and consequences. No headings or lists.
- for every nation, territory and region listed, one sentence (two at most) on what the event means specifically for that nation, territory or region. Keep each line specific to its subject: for a nation, its people, armies, leaders, lands and interests; for a territory, what happens there; for a region, what happens in that region. Do not repeat the overview. If the page only mentions the subject in passing (a senator voting, a name in a list, a passing reference, a donation), set passing to true and write a short honest line starting "Mentioned in passing:" saying how it is mentioned.

Rules:
- Use only what the page says. Never invent outcomes, numbers or names. If the page is a proposal or an opportunity, say so rather than presenting it as having happened.
- Write in British English, in the setting's own terms (Imperial nations, territories, regions, the Senate, the Synod, Winds of War and Fortune). Out-of-character notes may be used for facts but say nothing about the game's mechanics unless they are the point of the page.
- Return every listed nation, territory and region exactly once, using the names exactly as given."""

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["overview", "detail", "nations", "territories", "regions"],
    "properties": {
        "overview": {"type": "string"},
        "detail": {"type": "string"},
        **{k: {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["name", "line", "passing"],
            "properties": {"name": {"type": "string"}, "line": {"type": "string"}, "passing": {"type": "boolean"}}}}
           for k in ("nations", "territories", "regions")},
    },
}

IMPERIAL = ["Dawn", "Highguard", "Imperial Orcs", "Navarr", "The Brass Coast", "The League", "The Marches",
            "Urizen", "Varushka", "Wintermark"]
BARBARIAN = ["Jotun", "Druj", "Grendel", "Thule"]


def page_text(info: dict) -> str:
    """The page as plain-ish text: front matter, images, link targets and category lines removed."""
    path = ROOT / "wiki" / info["path"]
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    text = re.sub(r"\*?\[Image:[^\]]*\]\([^)]*\)\*?", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"(?m)^Categories:.*$", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def jobs() -> list[dict]:
    """One job per event: its text, its places and who held them, and the nations to cover."""
    data = json.loads((MAP_DIR / "data.json").read_text())
    pages = read_json(DATA / "pages.json")
    S, tl = data["seasons"], data["control"]["timeline"]
    names = {h["id"]: h["name"] for h in data["holders"]}

    def holder(t, r, s):
        seq = tl.get(t, {}).get(r or "") or tl.get(t, {}).get("") or [[0, "unknown"]]
        h = "unknown"
        for i, x in seq:
            if i <= s:
                h = x
        return h

    out = []
    for e in data["events"]:
        info = pages.get(e["ti"])
        if not info:
            continue
        text = page_text(info)
        places, nations = [], set()
        for t, rs in sorted(e["pl"].items()):
            hs = sorted({holder(t, r, e["s"]) for r in (rs or [""])} | {holder(t, "", e["s"])})
            places.append({"territory": t, "regions": rs, "held_by": [names.get(h, h) for h in hs if h != "unknown"]})
            nations |= {h for h in hs if h in IMPERIAL or h in BARBARIAN}
        nations |= {n for n in IMPERIAL + BARBARIAN if re.search(r"(?<![\w'-])" + re.escape(n) + r"(?![\w'-])", text)}
        key = hashlib.sha1(json.dumps([info.get("revision"), places, sorted(nations), PROMPT_VERSION],
                                      sort_keys=True).encode()).hexdigest()[:16]
        out.append({"title": e["ti"], "season": S[e["s"]], "type": e["ty"], "text": text, "places": places,
                    "nations": sorted(nations), "key": key})
    return out


def request(job: dict) -> dict:
    regions = [f"{p['territory']}/{r}" for p in job["places"] for r in p["regions"]]
    user = (f"Page title: {job['title']}\nSeason: {job['season']}\nKind: {job['type']}\n\n"
            "Nations to cover: " + (", ".join(job["nations"]) or "none") + "\n"
            "Territories to cover (with who held them that season):\n" +
            ("\n".join(f"- {p['territory']} (held by {', '.join(p['held_by']) or 'unknown'})" for p in job["places"]) or "none") +
            "\nRegions to cover (Territory/Region):\n" + ("\n".join(f"- {r}" for r in regions) or "none") +
            "\n\n<page>\n" + job["text"] + "\n</page>")
    return {
        "model": MODEL,
        "max_tokens": 32000,
        "system": [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user}],
        "output_config": {"effort": EFFORT, "format": {"type": "json_schema", "schema": SCHEMA}},
    }


def estimate(js: list[dict], batch: bool) -> float:
    """Rough dollars: input from the page length, output allowing for thinking at the chosen effort."""
    tin = sum(len(j["text"]) / 3.6 + 900 for j in js)
    lines = sum(1 + len(j["nations"]) + len(j["places"]) + sum(len(p["regions"]) for p in j["places"]) for j in js)
    think = {"low": 400, "medium": 1200, "high": 2500, "xhigh": 4000, "max": 6000}.get(EFFORT, 2500)
    tout = sum(think for _ in js) + lines * 45 + len(js) * 200
    dollars = (tin * PRICE["in"] + tout * PRICE["out"]) / 1e6
    return dollars * (BATCH_DISCOUNT if batch else 1)


def cost_of(usage, batch: bool) -> float:
    d = (getattr(usage, "input_tokens", 0) * PRICE["in"] + getattr(usage, "output_tokens", 0) * PRICE["out"]
         + (getattr(usage, "cache_read_input_tokens", 0) or 0) * PRICE["cache_read"]
         + (getattr(usage, "cache_creation_input_tokens", 0) or 0) * PRICE["cache_write"]) / 1e6
    return d * (BATCH_DISCOUNT if batch else 1)


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=0, sort_keys=True) + "\n", encoding="utf-8")


def _norm(name: str) -> str:
    n = re.sub(r"_?placeholder", "", str(name), flags=re.I).replace("’", "'").strip().lower()
    return re.sub(r"^the\s+", "", re.sub(r"\s+", " ", n))


def tidy(lines: dict, job: dict) -> dict:
    """File each line under a name that was asked for, whichever list the model put it in (a region in
    the territory list, a nation as a territory, a stray suffix); lines for anything else are dropped."""
    wanted = {"n": job["nations"], "t": [p["territory"] for p in job["places"]],
              "r": [f"{p['territory']}/{r}" for p in job["places"] for r in p["regions"]]}
    pool = {}
    for k in ("n", "t", "r"):
        for name, v in (lines.get(k) or {}).items():
            pool.setdefault(_norm(name), v)
    out = {}
    for k, names in wanted.items():
        out[k] = {}
        for name in names:
            v = pool.get(_norm(name))
            if v is None and k == "r":  # a region given without its territory
                v = pool.get(_norm(name.split("/", 1)[1]))
            if v is not None:
                out[k][name] = v
    return out


def store(summaries: dict, job: dict, text: str) -> bool:
    try:
        r = json.loads(text)
    except ValueError:
        return False
    pick = lambda k: {x["name"]: {"t": x["line"], "p": bool(x["passing"])} for x in r.get(k, []) if x.get("name")}
    lines = tidy({"n": pick("nations"), "t": pick("territories"), "r": pick("regions")}, job)
    summaries[job["title"]] = {"key": job["key"], "o": r["overview"].strip(), "d": r["detail"].strip(), **lines}
    return True


def outstanding(summaries: dict) -> list[dict]:
    return [j for j in jobs() if summaries.get(j["title"], {}).get("key") != j["key"]]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch", action="store_true")
    ap.add_argument("--collect", action="store_true")
    ap.add_argument("--wait", action="store_true", help="with --batch/--collect: wait for the batch to finish")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tidy", action="store_true", help="re-file stored lines under the requested names (no API calls)")
    ap.add_argument("--only", nargs="*", help="page titles to (re)summarise")
    ap.add_argument("--changed", action="store_true",
                    help="only pages downloaded in this update (.cache/changed.json) - for the daily run")
    a = ap.parse_args(argv)

    summaries = load(OUT, {})
    spent = load(COST, {"dollars": 0.0, "runs": []})
    if a.tidy:
        byt = {j["title"]: j for j in jobs()}
        for t, x in summaries.items():
            if t in byt:
                x.update(tidy({k: x.get(k, {}) for k in ("n", "t", "r")}, byt[t]))
        save(OUT, summaries)
        print(f"tidied {len(summaries)} summaries")
        return 0
    todo = outstanding(summaries)
    if a.only:
        todo = [j for j in jobs() if j["title"] in set(a.only)]
    if a.changed:
        cp = ROOT / ".cache" / "changed.json"
        changed = set(json.loads(cp.read_text())) if cp.exists() else set()
        todo = [j for j in todo if j["title"] in changed]
    if a.limit and a.limit <= 30 and not a.batch and not a.only:
        # a pilot: a spread of event types and years rather than the earliest few
        by = {}
        for j in todo:
            by.setdefault(j["type"], []).append(j)
        pick, i = [], 0
        while len(pick) < a.limit and any(by.values()):
            for ty in sorted(by):
                if by[ty] and len(pick) < a.limit:
                    lst = by[ty]
                    pick.append(lst.pop((i * 7919) % len(lst)))
            i += 1
        todo = pick
    elif a.limit:
        todo = todo[: a.limit]
    est = estimate(todo, a.batch)
    print(f"{len(todo)} events to summarise | estimated ${est:.2f} | spent so far ${spent['dollars']:.2f} of ${BUDGET:.0f}")
    if a.dry_run:
        return 0
    if not os.environ.get("ANTHROPIC_API_KEY") and not a.collect:
        print("No ANTHROPIC_API_KEY: nothing sent.")
        return 0

    import anthropic
    client = anthropic.Anthropic()

    if a.collect or (a.batch and PENDING.exists()):
        pend = load(PENDING, None)
        if not pend:
            print("No batch pending.")
            return 0
        while True:
            b = client.messages.batches.retrieve(pend["id"])
            if b.processing_status == "ended" or not a.wait:
                break
            print(f"batch {b.processing_status}: {b.request_counts.processing} processing"); sys.stdout.flush()
            time.sleep(120)
        if b.processing_status != "ended":
            print(f"Batch {pend['id']} still {b.processing_status}.")
            return 0
        byid = {j["id"]: j for j in pend["jobs"]}
        ok = bad = 0
        run_cost = 0.0
        for res in client.messages.batches.results(pend["id"]):
            job = byid.get(res.custom_id)
            if res.result.type == "succeeded":
                msg = res.result.message
                run_cost += cost_of(msg.usage, True)
                text = next((c.text for c in msg.content if c.type == "text"), "")
                if job and msg.stop_reason != "refusal" and store(summaries, job, text):
                    ok += 1
                    continue
            bad += 1
        spent["dollars"] = round(spent["dollars"] + run_cost, 4)
        spent["runs"].append({"batch": pend["id"], "events": ok, "failed": bad, "dollars": round(run_cost, 4)})
        save(OUT, summaries); save(COST, spent); PENDING.unlink()
        print(f"collected {ok} summaries, {bad} failed | this batch ${run_cost:.2f} | total ${spent['dollars']:.2f}")
        return 0

    if spent["dollars"] + est > BUDGET:
        print(f"Refused: the estimate would take spending past ${BUDGET:.0f}. Use --limit or a lower effort.")
        return 1

    if a.batch:
        from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
        from anthropic.types.messages.batch_create_params import Request
        reqs, meta = [], []
        for i, j in enumerate(todo):
            cid = f"e{i}"
            reqs.append(Request(custom_id=cid, params=MessageCreateParamsNonStreaming(**request(j))))
            meta.append({"id": cid, "title": j["title"], "key": j["key"]})
        b = client.messages.batches.create(requests=reqs)
        save(PENDING, {"id": b.id, "jobs": [dict(m, **{k: v for k, v in jj.items() if k in ("title", "key")})
                                            for m, jj in zip(meta, todo)]})
        print(f"submitted batch {b.id} with {len(reqs)} events")
        if a.wait:
            return main(["--collect", "--wait"])
        return 0

    run_cost, ok = 0.0, 0
    for j in todo:
        if spent["dollars"] + run_cost > BUDGET:
            print("Budget reached; stopping.")
            break
        try:
            with client.messages.stream(**request(j)) as s:
                msg = s.get_final_message()
        except anthropic.APIStatusError as exc:
            print(f"failed: {j['title']}: {exc.status_code}")
            continue
        run_cost += cost_of(msg.usage, False)
        text = next((c.text for c in msg.content if c.type == "text"), "")
        if msg.stop_reason != "refusal" and store(summaries, j, text):
            ok += 1
            print(f"ok ${cost_of(msg.usage, False):.3f}  {j['title']}"); sys.stdout.flush()
        if ok % 10 == 0:
            save(OUT, summaries)
    spent["dollars"] = round(spent["dollars"] + run_cost, 4)
    spent["runs"].append({"direct": True, "events": ok, "dollars": round(run_cost, 4)})
    save(OUT, summaries); save(COST, spent)
    print(f"summarised {ok} events | this run ${run_cost:.2f} | total ${spent['dollars']:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
