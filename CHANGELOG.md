# Changelog
Each release lists what changed and any steps for existing users. To update your copy, tell Claude
"update agentCV" (it runs `python3 scripts/update.py` and walks you through it).

**Format (maintainers):** newest first, headed `## <version> (<YYYY-MM-DD>)`, with "What's new" and, when needed,
"Steps for existing users" (data changes Claude should make, like adding a column to pipeline.csv).
Before publishing: bump `VERSION`, add the entry here, run `python3 scripts/update.py manifest`, then push.

## 0.9.3 (2026-11-25)
### What's new
- **One operating manual for any agent: `AGENTS.md`.** The manual moved from CLAUDE.md to AGENTS.md, the file OpenAI
  Codex and other agents read on their own. `CLAUDE.md` is now a short pointer, so Claude (Cowork and Claude Code) works
  exactly as before. The manual says "the agent" instead of "Claude"; the safety rules are unchanged.
- **Experimental: runs on OpenAI Codex.** See "Using OpenAI Codex instead" in the README. Claude stays the recommended,
  tested setup; please report how Codex goes in GitHub Issues.
- The starter prompt now says "Read AGENTS.md". The old prompt still works through the pointer.
- README fix: standing rules go in `profile/house-rules.md` (it said CLAUDE.md).

### Steps for existing users
- **Run the update twice.** Your current updater doesn't know about AGENTS.md yet, so the first pass installs the new
  updater and the short CLAUDE.md; the second pass (`python3 scripts/update.py apply`) adds AGENTS.md. Then confirm
  AGENTS.md exists and read it before doing anything else.

## 0.9.2 (2026-11-24)
### What's new
- **`profile/master-resume.md` is now `profile/primary-resume.md`.** The docs already called it your primary resume;
  now the file name matches. Scripts and the dashboard look for the new name and still find the old one, so nothing
  breaks if you haven't renamed yet.
- **agent.cv is now agentCV.** Apps kept turning "agent.cv" into a link to a website that isn't ours. The repo is
  now github.com/duprejohn/agentcv (old links redirect), downloads are `agentcv-<version>.zip`, and they unzip to an
  `agentcv` folder. Your existing `agent.cv` folder keeps working; rename it only if you want to.
- Release downloads are versioned: `agentcv-<version>.zip` on each GitHub release.

### Steps for existing users
- Ask Claude to rename `profile/master-resume.md` (and any `.docx`/`.pdf` built from it) to `primary-resume.*`, and to
  update any of your own notes that mention the old path.

## 0.9.1 (2026-11-24)
### What's new
- **Interview coaching, rebuilt from a real multi-round loop.** Prep sheets now have a set shape: what the
  interviewer is testing, a 60-second opener, the top 2 answers written out, questions to ask, a watch list and the
  numbers. Onsites and panels get one sheet per interviewer.
- **Debriefs after every round** capture what each interviewer said they need, flag new stories to confirm, and carry
  themes into the next round's sheets.
- **Live case interviews:** a time plan for the session, a structure to say out loud, and how to handle being
  redirected. If a case felt messy, the thank-you can restate the approach in three lines.
- **Founder and leadership calls:** check what the company actually ships (and what competitors are launching) before
  the call. If they aren't sure they need the role full time, consider offering a short contract engagement.
- **Thank-you notes:** one per interviewer, or one team note for the recruiter to forward when you don't have emails.
- **Audio briefing:** on request, Claude writes a NotebookLM prompt that turns your prep sheets into a ~15-minute
  podcast to listen to on a walk.
- **New script: `scripts/doc_pdf.py`** makes readable PDFs of prep sheets and study guides (tables, lists, quotes) on
  Mac, Windows and Linux.
- **Fact corrections:** when you correct a claim, Claude fixes it in the profile, the primary resume, every unsent kit
  and open prep sheets, and lists what already went out with the old wording.
- **Workday:** autofill often fails outright; plan to enter each job by hand from `experience-paste.txt`.
- **"Primary resume":** the docs, dashboard and scripts now call `profile/master-resume.md` your primary resume. The
  file name is unchanged, so nothing to move.
- Answer bank: added "Aren't you overqualified?" and a question to ask every interviewer.

### Known issues
- **Workday parsing is only partly understood.** How Workday splits titles, merges roles and reads headlines varies
  by employer, and `workday_resume.py` hasn't produced a clean autofill in real tests. More testing is needed before
  the rules are reliable. Until then, enter each job by hand and review every field.

### Steps for existing users
- Optional: the answer bank is your own file, so the updater doesn't touch it. To get the two new entries, ask Claude
  to add "Aren't you overqualified?" and "What do you want more of from the people in this role?" to
  `interviews/answer-bank.md`.

## 0.9.0 (2026-11-09)
### What's new
- First public preview (0.9: working and tested on a real search, still being refined): the operating manual (CLAUDE.md), four-phase setup (LinkedIn intake, master resume coaching,
  LinkedIn update, targets), daily format, pipeline and dashboard, agency playbook and templates.
- Scripts: tailored resumes with a Before / After / Reasoning changelog, ATS-safe .docx, PDFs on Mac, Windows and Linux,
  Workday-friendly resumes, job board sweep, do-not-submit list, dashboard.
- Updates: `scripts/update.py` and the "update agent.cv" routine. Your own rules live in `profile/house-rules.md`.

### Steps for existing users
- None (first release).
