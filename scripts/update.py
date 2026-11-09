#!/usr/bin/env python3
"""Update this copy of agent.cv from the project's GitHub repo, without touching the user's own files.

Usage:
  python3 scripts/update.py check              what's new upstream (version + changelog entries), changes nothing
  python3 scripts/update.py plan               download the latest version and list exactly what would change
  python3 scripts/update.py apply              apply it: back up, replace project files, flag conflicts
  python3 scripts/update.py manifest           (maintainers) rebuild scripts/manifest.json before publishing
  Add --source <folder or .zip> to plan/apply to update from a local copy instead of GitHub.

How it stays safe:
- Only project files are ever written: paths matching PROJECT_FILES below (this local list, not anything downloaded).
  The user's profile, pipeline, applications, plans, logs and house rules are never touched.
- scripts/manifest.json records a fingerprint of every project file as installed. A file the user has changed since is a
  conflict: their version stays, and the new one is saved next to it as <file>.incoming for Claude to merge with them.
- Everything replaced is copied to backups/update-<time>/ first.
"""
import fnmatch, hashlib, io, json, pathlib, re, shutil, sys, tempfile, urllib.request, zipfile, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts" / "manifest.json"
PROJECT_FILES = ["CLAUDE.md", "README.md", "LICENSE", "STARTER-PROMPT.md", ".gitignore", "VERSION", "CHANGELOG.md",
                 "scripts/*.py", "scripts/*.swift", "scripts/manifest.json", "dashboard/*.html", "dashboard/app.css",
                 "dashboard/app.js", "companies/agencies.md", "outreach/recruiter-templates.md"]


def is_project_file(rel):
    return any(fnmatch.fnmatchcase(rel, p) for p in PROJECT_FILES) and ".." not in rel.split("/")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(root):
    p = root / "scripts" / "manifest.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"version": "0.0.0", "files": {}}


def vkey(v):
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def fetch_upstream(source=None):
    """Return a folder holding the latest upstream copy (from GitHub, a local folder, or a .zip)."""
    if source and pathlib.Path(source).is_dir():
        return pathlib.Path(source).resolve()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="agentcv-update-"))
    if source:
        data = pathlib.Path(source).read_bytes()
    else:
        m = load_manifest(ROOT)
        if not m.get("repo") or "YOUR-GITHUB-USERNAME" in m["repo"]:
            sys.exit("No upstream repo set. Put \"repo\": \"<owner>/agent.cv\" in scripts/manifest.json.")
        url = f"https://codeload.github.com/{m['repo']}/zip/refs/heads/{m.get('branch', 'main')}"
        with urllib.request.urlopen(url, timeout=60) as r:
            data = r.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            parts = info.filename.split("/", 1)  # GitHub zips wrap everything in "<repo>-<branch>/"
            rel = parts[1] if len(parts) > 1 else ""
            if info.is_dir() or not rel or not is_project_file(rel):
                continue
            out = tmp / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(z.read(info))
    return tmp


def changelog_since(text, version):
    """The CHANGELOG.md entries newer than `version` (headings like '## 1.1.0 (2026-12-01)')."""
    blocks = re.split(r"(?m)^(?=## \d)", text)
    return [b.strip() for b in blocks if re.match(r"## \d", b) and vkey(b[3:]) > vkey(version)]


def make_plan(up):
    local, remote = load_manifest(ROOT), load_manifest(up)
    plan = {"from": local["version"], "to": remote["version"], "new": [], "update": [], "conflict": [], "remove": [], "same": 0}
    for rel, h in sorted(remote["files"].items()):
        if not is_project_file(rel) or not (up / rel).exists():
            continue
        mine = ROOT / rel
        if not mine.exists():
            plan["new"].append(rel)
        elif sha(mine) == h:
            plan["same"] += 1
        elif rel in local["files"] and sha(mine) != local["files"][rel]:
            plan["conflict"].append(rel)  # the user changed this file since it was installed
        else:
            plan["update"].append(rel)
    for rel in local["files"]:
        if rel not in remote["files"] and is_project_file(rel) and (ROOT / rel).exists():
            plan["remove"].append(rel)
    return plan, remote


def show(plan, up):
    print(f"agent.cv {plan['from']} → {plan['to']}")
    notes = changelog_since((up / "CHANGELOG.md").read_text(encoding="utf-8"), plan["from"]) if (up / "CHANGELOG.md").exists() else []
    for n in notes:
        print("\n" + n)
    print(f"\nNew files: {len(plan['new'])} · Updated: {len(plan['update'])} · Conflicts (you edited them): {len(plan['conflict'])}"
          f" · Removed: {len(plan['remove'])} · Unchanged: {plan['same']}")
    for k, label in (("new", "+"), ("update", "~"), ("conflict", "!"), ("remove", "-")):
        for rel in plan[k]:
            print(f"  {label} {rel}")
    if plan["conflict"]:
        print("\n! = you've changed these. Your version stays; the new one is saved as <file>.incoming to merge.")


def apply(plan, up, remote):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = ROOT / "backups" / f"update-{stamp}"
    def keep(rel):
        dest = backup / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dest)
    for rel in plan["update"] + plan["new"]:
        if (ROOT / rel).exists():
            keep(rel)
        (ROOT / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(up / rel, ROOT / rel)
    for rel in plan["conflict"]:
        keep(rel)
        shutil.copy2(up / rel, ROOT / (rel + ".incoming"))
    for rel in plan["remove"]:
        keep(rel)
        (ROOT / rel).unlink()
    # record what's installed now; conflicts keep upstream's fingerprint, so they show as edited until merged identically
    local = load_manifest(ROOT)
    local.update({k: remote[k] for k in ("version", "repo", "branch") if k in remote})
    local["files"] = {rel: h for rel, h in remote["files"].items() if is_project_file(rel)}
    MANIFEST.write_text(json.dumps(local, indent=1) + "\n", encoding="utf-8")
    (ROOT / "VERSION").write_text(remote["version"] + "\n", encoding="utf-8")
    print(f"Updated to {remote['version']}. Backup: {backup.relative_to(ROOT) if backup.exists() else '(nothing replaced)'}")
    if plan["conflict"]:
        print("Merge these with the user, then delete the .incoming files: " + ", ".join(r + ".incoming" for r in plan["conflict"]))


def build_manifest():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    old = load_manifest(ROOT)
    files = {}
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT).as_posix()
        if p.is_file() and rel != "scripts/manifest.json" and is_project_file(rel) and not rel.startswith("backups/"):
            files[rel] = sha(p)
    m = {"version": version, "repo": old.get("repo", "duprejohn/agent.cv"), "branch": old.get("branch", "main"), "files": files}
    MANIFEST.write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
    print(f"manifest.json: version {version}, {len(files)} project files")


if __name__ == "__main__":
    args = sys.argv[1:]
    cmd = args[0] if args else "check"
    source = args[args.index("--source") + 1] if "--source" in args else None
    if cmd == "manifest":
        build_manifest()
    elif cmd in ("check", "plan", "apply"):
        up = fetch_upstream(source)
        plan, remote = make_plan(up)
        if vkey(plan["to"]) <= vkey(plan["from"]) and not (plan["new"] or plan["update"]):
            print(f"agent.cv is up to date ({plan['from']}).")
        elif cmd == "check":
            print(f"Update available: {plan['from']} → {plan['to']}\n")
            for n in changelog_since((up / "CHANGELOG.md").read_text(encoding="utf-8"), plan["from"]) if (up / "CHANGELOG.md").exists() else []:
                print(n + "\n")
        else:
            show(plan, up)
            if cmd == "apply":
                apply(plan, up, remote)
    else:
        sys.exit(__doc__)
