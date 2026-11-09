#!/usr/bin/env python3
"""Build a tailored resume.md (+ .docx) from profile/master-resume.md and a JSON spec.

Usage: python3 scripts/tailor.py applications/<dir>/spec.json [--changelog-only]
Also writes changelog.md (Before / After / Reasoning) next to the spec for review. --changelog-only skips rebuilding the resume.

Spec keys (all optional except headline/summary/skills):
  tagline    str            short descriptor shown next to the name ("# Name | Tagline")
  headline   str            replaces the bold headline line
  summary    str            replaces the Summary paragraph
  skills     [str]          replaces the Skills lines ("**Label:** a, b, c")
  order      {role: [substr, ...]}  for a role title starting with `role`, put bullets containing each substr first, in order
  limit      {role: n}      keep at most n bullets for that role (after ordering)
  drop       [substr]       remove any bullet containing substr
  replace    [[old, new, reason?]]   text substitutions applied to every bullet (keyword mirroring; must stay truthful)
  why        {key: reason}  reasoning shown in changelog.md (see changelog() for the keys)
  early      "condensed" (default) | "full"   how to render older employers (past the first `recent_employers`
             in profile/config.json): condensed uses the master's "## Early Career" section instead
  awards     bool (default true)
Every bullet still comes from the master resume, so tailoring rewords and reorders but never invents.
"""
import datetime, json, re, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
MASTER = ROOT / "profile" / "master-resume.md"

sys.path.insert(0, str(ROOT / "scripts"))
import agency_config
RECENT = agency_config.load()["recent_employers"]  # 0 = every employer in full



def parse_master():
    text = re.sub(r"<!--.*?-->", "", MASTER.read_text(encoding="utf-8"), flags=re.S)
    lines = [l.rstrip() for l in text.splitlines()]
    header, sections, cur = [], {}, None
    for l in lines:
        if l.startswith("## "):
            cur = l[3:].strip(); sections[cur] = []
        elif cur is None:
            if l.strip(): header.append(l)
        else:
            sections[cur].append(l)
    return header, sections


def split_experience(lines):
    """Return list of blocks: ('employer', line) or ('role', title_line, [bullets])."""
    blocks = []
    for l in lines:
        if l.startswith("### "):
            blocks.append(["employer", l])
        elif l.startswith("#### "):
            blocks.append(["role", l, []])
        elif l.startswith("- ") and blocks and blocks[-1][0] == "role":
            blocks[-1][2].append(l[2:])
    return blocks


def transform(title, bullets, spec):
    """Apply drop/order/limit/replace to one role's bullets. Returns (bullets, events) so the changelog sees every change."""
    events = []
    kept = [x for x in bullets if not any(d in x for d in spec.get("drop", []))]
    for x in bullets:
        if x not in kept:
            events.append(("drop", x, next(d for d in spec.get("drop", []) if d in x)))
    bullets = kept
    role_title = title[5:]  # strip "#### "; keys match the start of the title
    for role_key, prefs in spec.get("order", {}).items():
        if role_title.startswith(role_key):
            first = []
            for p in prefs:
                for x in bullets:
                    if p in x and x not in first:
                        first.append(x)
            moved = first + [x for x in bullets if x not in first]
            if moved != bullets:
                events.append(("order", bullets, moved, role_key))
            bullets = moved
    for role_key, n in spec.get("limit", {}).items():
        if role_title.startswith(role_key):
            events += [("limit", x, role_key) for x in bullets[n:]]
            bullets = bullets[:n]
    for r in spec.get("replace", []):  # [old, new] or [old, new, reason]
        changed = [x.replace(r[0], r[1]) for x in bullets]
        events += [("replace", a, b, r) for a, b in zip(bullets, changed) if a != b]
        bullets = changed
    return bullets, events


def tailor(spec, events=None):
    header, sec = parse_master()
    name, contact = header[0], header[1]
    if spec.get("tagline"):
        name = f"{name.partition(' | ')[0]} | {spec['tagline']}"
    out = [name, contact, f"**{spec['headline']}**", "", "## Summary", spec["summary"], "", "## Experience"]
    blocks = split_experience(sec["Experience"])
    condense = spec.get("early", "condensed") == "condensed" and RECENT and sec.get("Early Career")
    early_started, employers = False, 0
    for b in blocks:
        if b[0] == "employer":
            employers += 1
            if RECENT and employers > RECENT:
                early_started = True
                if condense:
                    continue
            out += ["", b[1]] if out[-1] else [b[1]]
            continue
        if early_started and condense:
            continue
        title = b[1]
        bullets, ev = transform(title, list(b[2]), spec)
        if events is not None:
            events += [(title[5:].split(" | ")[0],) + e for e in ev]
        out.append(title)
        out += [f"- {x}" for x in bullets]
    if condense:
        out += [""] + [l for l in sec["Early Career"] if l.strip()]
    if spec.get("projects") and sec.get("Projects"):
        out += ["", "## Projects"] + [l for l in sec["Projects"] if l.strip()]
    out += ["", "## Skills"] + spec["skills"]
    if spec.get("awards", True) and any(l.strip() for l in sec.get("Awards", [])):
        out += ["", "## Awards"] + [l for l in sec["Awards"] if l.strip()]
    if any(l.strip() for l in sec.get("Education", [])):
        out += ["", "## Education"] + [l for l in sec["Education"] if l.strip()]
    return "\n".join(out) + "\n"


def changelog(spec, folder):
    """Before / After / Reasoning table of every change from the master resume, for review before anything is sent.
    Reasons come from spec["why"] (keys: tagline, headline, summary, skills, projects, awards, early, order:<role key>,
    limit:<role key>, drop:<substring>, replace:<old text>) or a third element in a replace entry."""
    header, sec = parse_master()
    why, rows, events = spec.get("why", {}), [], []
    tailor(spec, events)
    NEED = "**NEEDS A REASON:** add one under \"why\" in spec.json."
    cell = lambda t: str(t).replace("|", "\\|").replace("\n", "<br>")
    short = lambda b, n=14: " ".join(b.split()[:n]) + (" …" if len(b.split()) > n else "")
    add = lambda where, before, after, reason: rows.append((f"**{where}**<br>{cell(before)}", cell(after), cell(reason or NEED)))

    m_tag = header[0].partition(" | ")[2].strip()
    if spec.get("tagline") and spec["tagline"] != m_tag:
        add("Tagline", m_tag, spec["tagline"], why.get("tagline"))
    m_head = next((l.strip("* ") for l in header[2:] if l.startswith("**")), "")
    if spec["headline"] != m_head:
        add("Headline", m_head, spec["headline"], why.get("headline"))
    m_sum = " ".join(l.strip() for l in sec.get("Summary", []) if l.strip())
    if spec["summary"] != m_sum:
        add("Summary", m_sum, spec["summary"], why.get("summary"))
    for e in events:
        role, kind = e[0], e[1]
        if kind == "order":
            numbered = lambda bs: "\n".join(f"{i}. {short(b)}" for i, b in enumerate(bs, 1))
            add(f"{role}: bullet order", numbered(e[2]), numbered(e[3]), why.get(f"order:{e[4]}"))
        elif kind == "drop":
            add(f"{role}: bullet removed", e[2], "(removed)", why.get(f"drop:{e[3]}"))
        elif kind == "limit":
            add(f"{role}: bullet cut for length", e[2], "(removed)", why.get(f"limit:{e[3]}") or "Kept the most relevant bullets for this role within the 2-page limit.")
        elif kind == "replace":
            r = e[4]
            add(f"{role}: wording", e[2], e[3], (r[2] if len(r) > 2 else None) or why.get(f"replace:{r[0]}"))
    if spec.get("early", "condensed") == "condensed" and RECENT and sec.get("Early Career"):
        early = [b[1][4:].split(" | ")[0] for b in split_experience(sec["Experience"]) if b[0] == "employer"][RECENT:]
        add("Early roles", "Full entries: " + ", ".join(early), "Condensed to one line per employer",
            why.get("early") or "Standard: older roles condensed so recent, relevant experience leads and the resume stays at 2 pages.")
    if sec.get("Projects") and not spec.get("projects"):
        add("Projects section", "Included in master", "(removed)", why.get("projects"))
    if sec.get("Awards") and not spec.get("awards", True):
        add("Awards section", "Included in master", "(removed)", why.get("awards"))
    m_skills = [l for l in sec.get("Skills", []) if l.strip()]
    if spec["skills"] != m_skills:
        add("Skills", "\n".join(m_skills), "\n".join(spec["skills"]), why.get("skills"))

    out = [f"# Resume changelog: {folder.name}",
           f"What changed from `profile/master-resume.md`, and why. Generated by scripts/tailor.py on {datetime.date.today()}.",
           "Review before sending: every After must be true, and every row needs a reason.", ""]
    missing = sum(NEED in r[2] for r in rows)
    out += [f"**{len(rows)} changes** · " + (f"**{missing} still need a reason**" if missing else "all have reasons"), ""]
    built = folder / "resume.md"
    if built.exists():
        sent = [l for l in built.read_text(encoding="utf-8").splitlines() if not l.startswith("<!--")]
        drift = sum(1 for a, b in zip(sent, tailor(spec).splitlines()) if a != b) + abs(len(sent) - len(tailor(spec).splitlines()))
        if drift:
            out += [f"> **Note:** the master resume has changed since resume.md was built ({drift} lines differ). "
                    "This table shows the changes as the spec would apply them today; check resume.md for the exact text that was sent.", ""]
    out += ["| Before | After | Reasoning |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in rows]
    (folder / "changelog.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote changelog.md: {len(rows)} changes, {missing} without a reason")


if __name__ == "__main__":
    spec_path = pathlib.Path(sys.argv[1]).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if "--changelog-only" not in sys.argv:  # --changelog-only: leave an existing (e.g. already-sent) resume untouched
        md = spec_path.parent / "resume.md"
        md.write_text(f"<!-- Generated by scripts/tailor.py from {spec_path.name}; edit the spec, not this file. -->\n" + tailor(spec), encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_docx.py"), str(md)], check=True)
        subprocess.run([sys.executable, str(ROOT / "scripts" / "make_pdf.py"), str(md)], check=True)
    changelog(spec, spec_path.parent)
