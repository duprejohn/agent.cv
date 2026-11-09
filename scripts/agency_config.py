"""Shared settings for the scripts, read from profile/config.json (every key is optional; defaults below)."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULTS = {
    "desk_title": "Search Desk",          # dashboard heading, e.g. "Jane Doe · Search Desk"
    "desk_subtitle": "",                  # one line under it: target roles, location, pay floor
    "pay_floor_k": 0,                     # dashboard flags roles whose listed pay range starts below this ($K); 0 = off
    "recent_employers": 0,                # resumes show this many most-recent employers in full; older ones use the
                                          # master's "## Early Career" section when early="condensed". 0 = show all in full
    "search": {                           # scripts/sweep.py filters (Python regular expressions, case-insensitive).
        "title": "",                      # filled in from profile/targets.md during setup, e.g. "account (manager|director)|customer success"
        "exclude": r"\bintern\b",        # titles to skip
        "location": r"remote|united states|anywhere|hybrid|^$",
        "workday_terms": [],              # search phrases for Workday boards, e.g. ["account manager"]
    },
}


def load():
    p = ROOT / "profile" / "config.json"
    cfg = json.loads(json.dumps(DEFAULTS))
    if p.exists():
        user = json.loads(p.read_text(encoding="utf-8"))
        cfg.update({k: v for k, v in user.items() if k != "search"})
        cfg["search"].update(user.get("search", {}))
    return cfg
