#!/usr/bin/env python3
"""Scan every verified job board in companies/ats-boards.json (Greenhouse, Lever, Ashby public APIs + Workday) and print
roles that match your targets (profile/config.json "search") and aren't already in pipeline.csv.
Usage: python3 scripts/sweep.py [--all]   (--all also shows roles already in the pipeline)
Screen the output by hand: fit-score honestly, then add fit 3+ rows to pipeline.csv. Boards that block scripts go in
board-checks.md and get checked by hand."""
import concurrent.futures as cf, html, json, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
cfg = json.loads((ROOT / "companies/ats-boards.json").read_text(encoding="utf-8"))

sys.path.insert(0, str(ROOT / "scripts"))
import agency_config
search = agency_config.load()["search"]  # edit these in profile/config.json
TITLE, EXCL, LOC = (re.compile(search[k], re.I) for k in ("title", "exclude", "location"))
if not search["title"].strip():
    sys.exit('No job-title filter yet. Set "search" > "title" in profile/config.json (Claude does this after the targets interview).')

def get(url, data=None):
    try:
        req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except Exception:
        return None

def scan(b):
    ats, s = b["ats"], b["slug"]
    if ats == "greenhouse":
        d = get(f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs") or {}
        return [(s, j["title"], j["location"]["name"], j["absolute_url"], "") for j in d.get("jobs", [])]
    if ats == "lever":
        d = get(f"https://api.lever.co/v0/postings/{s}?mode=json")
        return [(s, j["text"], j.get("categories", {}).get("location", ""), j["hostedUrl"], "") for j in d] if isinstance(d, list) else []
    d = get(f"https://api.ashbyhq.com/posting-api/job-board/{s}?includeCompensation=true") or {}
    return [(s, j["title"], (j.get("location") or "") + (" (remote)" if j.get("isRemote") else ""), j["jobUrl"],
             ((j.get("compensation") or {}).get("compensationTierSummary") or "").split("•")[0].strip()) for j in d.get("jobs", [])]

def workday(w):
    out = []
    for text in search["workday_terms"]:
        d = get(f"https://{w['tenant']}.{w['wd']}.myworkdayjobs.com/wday/cxs/{w['tenant']}/{w['site']}/jobs",
                json.dumps({"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": text}).encode()) or {}
        out += [(w["tenant"], j["title"], j.get("locationsText", ""), f"https://{w['tenant']}.{w['wd']}.myworkdayjobs.com/{w['site']}{j['externalPath']}", "")
                for j in d.get("jobPostings", [])]
    return out

boards = [(ind, b) for ind, bs in cfg["industries"].items() for b in bs]
pipeline = (ROOT / "pipeline.csv").read_text(encoding="utf-8").lower()
results = []
with cf.ThreadPoolExecutor(32) as ex:
    for (ind, b), jobs in zip(boards, ex.map(lambda x: scan(x[1]), boards)):
        results += [(ind,) + j for j in jobs]
    for w, jobs in zip(cfg.get("workday", []), ex.map(workday, cfg.get("workday", []))):
        results += [("workday: " + w["company"],) + j for j in jobs]
seen, shown = set(), 0
for ind, slug, title, loc, url, pay in sorted(results):
    key = (slug, title.lower())
    if key in seen or not TITLE.search(title) or EXCL.search(title) or not LOC.search(loc or ""):
        continue
    seen.add(key)
    if url.lower() in pipeline and "--all" not in sys.argv:
        continue
    shown += 1
    print(f"{ind} | {slug} | {title} | {loc} | {pay} | {url}")
print(f"\n{len(boards)} boards scanned, {len(results)} jobs, {shown} candidate roles shown", file=sys.stderr)
