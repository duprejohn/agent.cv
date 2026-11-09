#!/usr/bin/env python3
"""Build a Workday-friendly variant of a tailored resume, for portals that autofill "My Experience" from the upload.
Usage: python3 scripts/workday_resume.py <applications/.../spec.json>
Writes resume-workday.md/.docx/.pdf next to the spec. Same facts and bullets as resume.md; only the structure changes:
- every position is its own block: title line (no commas or dashes), then employer alone, then "Mon YYYY – Mon YYYY" (no pipes),
  so stacked promotions at one employer parse as separate jobs instead of one merged entry
- early roles are listed separately (from the master) instead of condensed "Title A; Title B" lines
- the bold headline and the tagline are dropped (parsers read them as a current job title)
- "Experience" becomes "Work Experience". Projects stay their own section (never a job): undated, each bullet
  prefixed with its project name, so the parser has no "title | place | dates" heading to turn into a position."""
import importlib.util, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec_path = pathlib.Path(sys.argv[1]).resolve()
spec = json.loads(spec_path.read_text(encoding="utf-8"))

mod_spec = importlib.util.spec_from_file_location("tailor", ROOT / "scripts" / "tailor.py")
tailor = importlib.util.module_from_spec(mod_spec)
mod_spec.loader.exec_module(tailor)
sys.path.insert(0, str(ROOT / "scripts"))
import make_pdf

full = dict(spec, early="full", projects=True)
lines = tailor.tailor(full).splitlines()

name = lines[0][2:].partition(" | ")[0].strip()
contact = lines[1]
tagline = spec.get("tagline", "")
EARLY_BULLETS = 1  # keep the early roles to one line each so the resume stays at 2 pages
TOP_ROLE_MAX = 7   # the separate title/employer/date lines cost space, so cap the most recent role's bullets (spec order decides which stay)

import datetime
def start_of(dates):
    m = re.match(r"([A-Z][a-z]{2}) (\d{4})", dates)
    return datetime.datetime.strptime(" ".join(m.groups()), "%b %Y") if m else datetime.datetime.min

# split tailor's output into sections
sections, cur = [], None
for l in lines[2:]:
    if l.startswith("## "):
        cur = [l[3:].strip(), []]; sections.append(cur)
    elif cur is not None:
        cur[1].append(l)

# experience -> one block per position, sorted newest first
roles, employer, early, employers = [], None, False, 0
for l in dict(sections)["Experience"]:
    if l.startswith("### "):
        parts = [p.strip() for p in l[4:].split("|")]
        employer = f"{parts[0]}, {parts[1]}" if len(parts) > 2 else parts[0]
        employers += 1
        early = bool(tailor.RECENT) and employers > tailor.RECENT
    elif l.startswith("#### "):
        title, _, dates = (p.strip() for p in l[5:].rpartition("|"))
        roles.append({"title": title, "employer": employer, "dates": dates, "early": early, "bullets": []})
    elif l.startswith("- ") and roles:
        roles[-1]["bullets"].append(l)
# Projects stay a separate section, never a job: no dated "### Project | Place | Dates" headings
# for the parser to mistake for a position; each bullet carries its project name instead.
project_lines, project_firsts, pname = [], [], None
for l in dict(sections).get("Projects", []):
    if l.startswith("### "):
        pname = l[4:].split("|")[0].strip()
    elif l.startswith("- "):
        project_lines.append(f"- {pname}: {l[2:]}" if pname else l)
        if pname:
            project_firsts.append(project_lines[-1])
        pname = None  # name only the first bullet of each project
roles.sort(key=lambda r: start_of(r["dates"]), reverse=True)

def safe_title(t):
    """Same words, no commas or dashes: in testing, Workday cut 'Senior Manager, Operations' at the comma."""
    return re.sub(r"\s+", " ", re.sub(r"[,–—-]", " ", t)).strip()

def build(TOP_ROLE_MAX, short_projects=False):
    out = [f"# {name}", contact]  # no tagline: in testing, Workday read it as a job title with the summary as its description
    for title, body in sections:
        if title == "Projects":
            out += ["", "## Projects"] + (project_firsts if short_projects else project_lines)
            continue
        if title == "Experience":
            out += ["", "## Work Experience"]
            for r in roles:
                out += ["", f"#### {safe_title(r['title'])}", r["employer"].rsplit(", ", 2)[0], r["dates"]]
                if r["early"]:
                    out += r["bullets"][:EARLY_BULLETS]
                elif r is roles[0]:
                    out += r["bullets"][:TOP_ROLE_MAX]
                else:
                    out += r["bullets"]
            continue
        out += ["", f"## {title}"] + [l for l in body if l.strip()]

    return out

def pages(pdf):
    """Drop trailing blank pages (the renderer adds one when text ends at the bottom edge), then return the page count."""
    if make_pdf.use_browser():  # Windows/Linux: count pages without macOS's PDFKit
        try:
            import pypdf
            return len(pypdf.PdfReader(pdf).pages)
        except ImportError:
            return len(re.findall(rb"/Type\s*/Page[^s]", pathlib.Path(pdf).read_bytes()))
    code = ('import PDFKit; let u = URL(fileURLWithPath: "%s"); let d = PDFDocument(url: u)!; '
            'while d.pageCount > 1, (d.page(at: d.pageCount - 1)!.string ?? "").trimmingCharacters(in: .whitespacesAndNewlines).isEmpty '
            '{ d.removePage(at: d.pageCount - 1) }; d.write(to: u); print(d.pageCount)') % pdf
    out = subprocess.run(["swift", "-e", code], capture_output=True, text=True)
    return int(out.stdout.strip() or 0)

md = spec_path.parent / "resume-workday.md"
# fit to 2 pages: first trim the most recent role's bullets down to 5, then keep only each project's first bullet
attempts = [(c, False) for c in range(TOP_ROLE_MAX, 4, -1)] + [(5, True)]
for cap, short in attempts:
    md.write_text("<!-- Generated by scripts/workday_resume.py from spec.json: Workday-friendly structure. Edit the spec, not this file. -->\n"
                  + "\n".join(build(cap, short)) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make_pdf.py"), str(md)], check=True, capture_output=True)
    n = pages(md.with_suffix(".pdf"))
    if n <= 2:
        break
subprocess.run([sys.executable, str(ROOT / "scripts" / "build_docx.py"), str(md)], check=True)
print(f"resume-workday.pdf: {n} pages, most recent role's bullets capped at {cap}" + (", project bullets shortened" if short else ""))

# Backup for fixing autofill by hand: one plain-text block per position (one line per bullet, no wraps),
# using the full bullet list for each role (form fields have more room than the 2-page resume).
blocks = ["Workday 'My Experience' paste sheet. Copy each Role Description block into the matching job.",
          "Use the .docx for Autofill with Resume: a PDF stores every visual line wrap as a hard return.", ""]
for r in roles:
    blocks += ["=" * 60, f"Job Title: {r['title']}", f"Company: {r['employer'].rsplit(', ', 2)[0]}",
               f"Location: {', '.join(r['employer'].rsplit(', ', 2)[1:])}", f"Dates: {r['dates']}", "Role Description:"]
    blocks += [b[2:] for b in r["bullets"]]
    blocks.append("")
(spec_path.parent / "experience-paste.txt").write_text("\n".join(blocks), encoding="utf-8")
print("wrote experience-paste.txt")
