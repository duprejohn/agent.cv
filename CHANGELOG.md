# Changelog
Each release lists what changed and any steps for existing users. To update your copy, tell Claude
"update agent.cv" (it runs `python3 scripts/update.py` and walks you through it).

**Format (maintainers):** newest first, headed `## <version> (<YYYY-MM-DD>)`, with "What's new" and, when needed,
"Steps for existing users" (data changes Claude should make, like adding a column to pipeline.csv).
Before publishing: bump `VERSION`, add the entry here, run `python3 scripts/update.py manifest`, then push.

## 0.9.0 (2026-11-09)
### What's new
- First public preview (0.9: working and tested on a real search, still being refined): the operating manual (CLAUDE.md), four-phase setup (LinkedIn intake, master resume coaching,
  LinkedIn update, targets), daily format, pipeline and dashboard, agency playbook and templates.
- Scripts: tailored resumes with a Before / After / Reasoning changelog, ATS-safe .docx, PDFs on Mac, Windows and Linux,
  Workday-friendly resumes, job board sweep, do-not-submit list, dashboard.
- Updates: `scripts/update.py` and the "update agent.cv" routine. Your own rules live in `profile/house-rules.md`.

### Steps for existing users
- None (first release).
