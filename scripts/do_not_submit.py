#!/usr/bin/env python3
"""Regenerate the do-not-submit list from pipeline.csv.
Writes companies/do-not-submit.md (internal) and outreach/Do-Not-Submit.{md,html,pdf} (to send to recruiters).
Your name and contact line come from the first two lines of profile/master-resume.md.
Includes every row with a date_applied, plus active processes that came through a recruiter (stage past 'applied' without a date).
Usage: python3 scripts/do_not_submit.py"""
import csv, datetime, html, pathlib, re, subprocess, sys
root = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "scripts"))
import make_pdf
rows = list(csv.DictReader(open(root / "pipeline.csv", newline="", encoding="utf-8")))
head_lines = [l.strip() for l in (root / "profile/master-resume.md").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("<!--")]
NAME = head_lines[0].lstrip("# ").partition(" | ")[0].strip()
CONTACT = head_lines[1] if len(head_lines) > 1 else ""
ACTIVE = {"recruiter-screen", "interviewing", "final", "offer"}
picked = [r for r in rows if r["date_applied"].strip() or r["stage"] in ACTIVE]

def company(c, external=False):
    c = re.sub(r"\s*\(TOP PRIORITY\)", "", c, flags=re.I).strip()
    if external:  # drop private labels like "(contract)" from the list recruiters see
        c = re.sub(r"\s*\([^)]*\)\s*$", "", c).strip()
    return c

def when(r):
    d = r["date_applied"].strip()
    return d if d else (r["last_contact"].strip() or r["date_found"].strip())

def pretty(d):
    try:
        return datetime.date.fromisoformat(d).strftime("%b %-d, %Y")
    except ValueError:
        try:
            return datetime.datetime.strptime(d, "%Y-%m").strftime("%b %Y")
        except ValueError:
            return d

picked.sort(key=lambda r: (company(r["company"], True).lower(), when(r)))
today = datetime.date.today()

# internal list
p = root / "companies/do-not-submit.md"
s = p.read_text(encoding="utf-8") if p.exists() else ""
head = s[: s.index("| Employer |")] if "| Employer |" in s else "# Do-not-submit list (internal)\n\nRoles already applied to. Check before any agency submission or right-to-represent reply.\n\n"
tbl = ["| Employer | Role | Applied |", "|---|---|---|"] + [
    f"| {company(r['company'])} | {r['role'].replace('|', '/')} | {r['date_applied'].strip() or 'in process (via recruiter)'} |" for r in picked]
p.write_text(head + "\n".join(tbl) + "\n", encoding="utf-8")

# external list
ext = [(company(r["company"], True), r["role"].replace("|", "/"),
        pretty(r["date_applied"].strip()) if r["date_applied"].strip() else "In process") for r in picked]
md = [f"# {NAME}: roles already applied to", "",
      f"Please don't submit me to these roles; I've already applied or am in process. Updated {today:%B} {today.day}, {today.year}.", "",
      "| Employer | Role | Applied |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in ext]
(root / "outreach/Do-Not-Submit.md").write_text("\n".join(md) + "\n", encoding="utf-8")

css = """@page{size:816px 1056px;margin:0}body{margin:0;font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;color:#1f2937}
.page{width:816px;height:1056px;box-sizing:border-box;padding:56px 60px;overflow:hidden}
h1{font-size:26px;color:#1e3a5f;margin:0}.sub{color:#4b6a8f;font-size:15px;margin:4px 0 10px}
.contact{font-size:12px;color:#4b5563;border-bottom:2px solid #1e3a5f;padding-bottom:10px;margin-bottom:14px}
p.note{font-size:13px;margin:0 0 12px}
table{width:100%;border-collapse:collapse;font-size:11.5px}th{text-align:left;color:#1e3a5f;font-size:11px;letter-spacing:.06em;text-transform:uppercase;border-bottom:1.5px solid #1e3a5f;padding:5px 6px}
td{padding:4.5px 6px;border-bottom:1px solid #e5e7eb;vertical-align:top}td:last-child,th:last-child{white-space:nowrap;text-align:right}
.foot{font-size:10.5px;color:#6b7280;text-align:right;margin-bottom:8px}"""
FIRST, REST = 32, 36  # rows per page (page 1 has the header)
chunks, i = [], 0
while i < len(ext):
    n = FIRST if not chunks else REST
    chunks.append(ext[i:i + n]); i += n
pages = []
for k, c in enumerate(chunks):
    if k == 0:
        top = (f"<h1>{html.escape(NAME)}</h1><div class='sub'>Roles already applied to: please do not submit</div>"
               f"<div class='contact'>{html.escape(CONTACT).replace(' | ', ' &nbsp;|&nbsp; ')}</div>"
               f"<p class='note'>I've applied directly to the roles below (or am already in process), so please don't submit me to them. "
               f"Other roles at these employers are fine to discuss; please check with me first. Updated {today:%B} {today.day}, {today.year} ({len(ext)} roles).</p>")
    else:
        top = f"<div class='foot'>{html.escape(NAME)} · Do-not-submit list · Page {k + 1}</div>"
    trs = "".join(f"<tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td><td>{html.escape(d)}</td></tr>" for a, b, d in c)
    pages.append(f"<section class='page'>{top}<table><tr><th>Employer</th><th>Role</th><th>Applied</th></tr>{trs}</table></section>")
hp = root / "outreach/Do-Not-Submit.html"
hp.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{''.join(pages)}</body></html>", encoding="utf-8")
pdf = root / "outreach/Do-Not-Submit.pdf"
if make_pdf.use_browser():  # Windows/Linux: headless Edge/Chrome/Chromium (the page CSS sets US Letter, no margins)
    if not make_pdf.browser_pdf(hp, pdf):
        print("PDF skipped: open outreach/Do-Not-Submit.html in a browser and Print > Save as PDF.")
else:
    subprocess.run(["swift", str(root / "scripts/webkit_pdf.swift"), str(hp), str(pdf)], check=True)
print(f"do-not-submit: {len(ext)} roles, {len(pages)} pages")
