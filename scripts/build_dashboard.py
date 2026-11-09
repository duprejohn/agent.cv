#!/usr/bin/env python3
"""Write dashboard/data.js from pipeline.csv, outreach.csv, agencies.csv and plan/next-actions.json.
The pages (dashboard.html overview, dashboard/roles.html, dashboard/network.html) and dashboard/app.js + app.css are static;
run this after any change, then republish the artifact with its files (see CLAUDE.md)."""
import csv, json, re, datetime, pathlib, sys
root = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "scripts"))
import agency_config
cfg = agency_config.load()
today = datetime.date.today().isoformat()
CLOSED = {"rejected", "passed", "withdrawn", "declined"}

def pay_low(comp):
    nums = [int(n) for n in re.findall(r"\$(\d+)K", comp)]
    return bool(nums) and bool(cfg["pay_floor_k"]) and min(nums) < cfg["pay_floor_k"]

roles = [{
    "co": r["company"], "role": r["role"], "stage": r["stage"], "fit": int(r["fit"] or 0),
    "pay": r["comp_range"] or "Not listed", "payLow": pay_low(r["comp_range"]),
    "where": r["location"], "link": r["link"], "next": r["next_action"],
    "due": r["next_action_due"] if r["stage"] not in CLOSED else "", "note": r["notes"],
    "closed": r["stage"] in CLOSED, "track": r.get("track") or "full-time", "src": r.get("source") or "",
} for r in csv.DictReader(open(root / "pipeline.csv", encoding="utf-8"))]

OUT_CLOSED = {"closed", "no-response", "declined"}
outreach = [{
    "name": o["name"], "org": o["organization"], "rel": o["relationship"], "channel": o["channel"],
    "purpose": o["purpose"], "stage": o["stage"], "sent": o["date_sent"], "next": o["next_action"],
    "due": o["next_action_due"] if o["stage"] not in OUT_CLOSED else "", "note": o["notes"],
} for o in csv.DictReader(open(root / "outreach.csv", encoding="utf-8"))] if (root / "outreach.csv").exists() else []

agencies = [{
    "name": a["agency"], "cat": a["category"], "model": a["model"], "pri": int(a["priority"] or 3), "how": a["how_to_get_on_roster"],
    "url": a["url"], "contact": a["contact"], "stage": a["stage"], "next": a["next_action"],
    "due": a["next_action_due"] if a["stage"] not in ("skip", "dormant") else "", "note": a["notes"],
} for a in csv.DictReader(open(root / "agencies.csv", encoding="utf-8"))] if (root / "agencies.csv").exists() else []

# On deck: agenda items + live sprint counts + follow-ups grouped by date
agenda = json.loads((root / "plan/next-actions.json").read_text()) if (root / "plan/next-actions.json").exists() else {"items": []}
prow = list(csv.DictReader(open(root / "pipeline.csv", encoding="utf-8")))
ondeck = []
for it in agenda.get("items", []):
    if it.get("done"):
        continue
    it = dict(it)
    if it.get("plan"):
        fname = it["plan"].split("/")[-1]
        left = [r for r in prow if r["stage"] == "shortlisted" and fname in r["next_action"]]
        if not left:
            continue
        it["count"] = len(left)
    ondeck.append(it)
fu = {}
for r in prow:
    if r["stage"] in ("applied", "recruiter-screen") and r["next_action"].lower().startswith("follow up") and r["next_action_due"]:
        d = datetime.date.fromisoformat(r["next_action_due"])
        wk = d - datetime.timedelta(days=d.weekday())
        fu.setdefault(wk, []).append((r["next_action_due"], r["company"].split(" (")[0]))
for wk, items in sorted(fu.items()):
    names = sorted(set(c for _, c in items))
    first = min(d for d, _ in items)
    ondeck.append({"date": first, "when": f"week of {wk.strftime('%b')} {wk.day}", "kind": "Follow-up", "count": len(items),
                   "title": f"Follow up on {len(items)} application{'s' if len(items) != 1 else ''}",
                   "detail": ", ".join(names[:6]) + (f" +{len(names) - 6} more" if len(names) > 6 else "")})
ondeck.sort(key=lambda x: (x.get("date") is None, x.get("date") or "9999"))

# Funnel flow (Sankey): found -> passed / held / queued / applied -> no response / rejected / screened -> active / rejected after screen
SCREEN_STAGES = {"recruiter-screen", "interviewing", "final", "offer", "accepted", "declined"}
def screened(r):  # a rejection counts as post-screen when the notes record an interview
    return r["stage"] in SCREEN_STAGES or (r["stage"] == "rejected" and re.search(r"first[- ]round|recruiter screen|interview", r["notes"], re.I))
applied = [r for r in prow if r["date_applied"].strip() or r["stage"] == "rejected" or r["stage"] in SCREEN_STAGES]
scr = [r for r in applied if screened(r)]
flow = {
    "found": len(prow),
    "passed": sum(r["stage"] in ("passed", "withdrawn") and r not in applied for r in prow),
    "held": sum(r["stage"] == "sourced" for r in prow),
    "queued": sum(r["stage"] == "shortlisted" for r in prow),
    "applied": len(applied),
    "waiting": sum(r["stage"] == "applied" for r in applied),
    "rejected": sum(r["stage"] == "rejected" and not screened(r) for r in applied),
    "screened": len(scr),
    "active": sum(r["stage"] not in ("rejected", "withdrawn", "declined") for r in scr),
    "rejectedAfter": sum(r["stage"] in ("rejected", "withdrawn", "declined") for r in scr),
}


# Profile pages: master resume + bios (read straight from the source files, so the pages always match them)
def md_sections(path, level="## "):
    out, cur, buf = [], None, []
    for line in (root / path).read_text(encoding="utf-8").splitlines():
        if line.startswith(level) or (level == "**" and line.startswith("**") and line.rstrip().endswith("**")):
            if cur: out.append((cur, "\n".join(buf).strip()))
            cur, buf = line.strip("#* ").strip(), []
        elif cur is not None:
            buf.append(line)
    if cur: out.append((cur, "\n".join(buf).strip()))
    return out
def unwrap(t):  # join hard-wrapped lines into paragraphs
    return re.sub(r"(?<!\n)\n(?!\n|- |\d\. )", " ", t).strip()
bios = []
kit = dict(md_sections("profile/agency-kit.md")) if (root / "profile/agency-kit.md").exists() else {}
for k in ("300-character bio (character-limited forms)", "Short bio (~50 words)", "Longer bio (~120 words)"):
    if k in kit: bios.append({"title": k.split(" (")[0], "note": k[k.find("(")+1:-1] if "(" in k else "", "src": "profile/agency-kit.md", "text": unwrap(kit[k])})
cons = dict(md_sections("profile/consulting-profile.md")) if (root / "profile/consulting-profile.md").exists() else {}
for k, v in cons.items():
    if k.startswith("Short bio"):
        bios.append({"title": "Third-person bio", "note": "proposals, LinkedIn Services, email intros", "src": "profile/consulting-profile.md", "text": unwrap(v)})
intake = []
for k, v in (md_sections("profile/agency-intake-answers.md", "**") if (root / "profile/agency-intake-answers.md").exists() else []):
    intake.append({"title": k, "src": "profile/agency-intake-answers.md", "text": unwrap(v)})
mr = root / "profile/master-resume.md"
resume = {"md": re.sub(r"<!--.*?-->", "", mr.read_text(encoding="utf-8"), flags=re.S).strip(),
          "updated": datetime.date.fromtimestamp(mr.stat().st_mtime).isoformat()}

data = {"title": cfg["desk_title"], "subtitle": cfg["desk_subtitle"], "today": today, "roles": roles, "agencies": agencies, "ondeck": ondeck, "outreach": outreach, "flow": flow, "bios": bios, "intake": intake, "resume": resume}
(root / "dashboard").mkdir(exist_ok=True)
(root / "dashboard/data.js").write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
print(f"dashboard: {len(roles)} roles, {len(outreach)} outreach, {len(agencies)} agencies, {len(ondeck)} on deck, {today}")
