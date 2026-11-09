# agent.cv

*Your CV's agent: a job search agency with one client (you), run on Claude. Built and tested with Claude Opus 5.5.*

This folder turns Claude into your own recruiter and account team. It
sources roles, screens them honestly, tailors ATS-safe resumes and cover letters, preps you for interviews, and keeps
every lead on a pipeline and dashboard. You make every decision and press every Submit button.

It started as John DuPre's personal setup during his own 2026 job search and grew into a system over a few months of
real use. This is that system with the personal data taken out, shared so other job seekers can skip the trial and error.

> Built with Claude. Not affiliated with or endorsed by Anthropic.

## How it works
- **`CLAUDE.md` is the operating manual.** Claude reads it at the start of every session. It defines the roles Claude
  plays (intake recruiter, sourcer, account manager, resume writer, interview coach, negotiator) and the house rules.
- **The house rules keep it honest:**
  - Nothing goes out without your explicit approval.
  - Every resume claim comes from your profile. Claude rewords and reorders, and never invents.
  - Claude rates your fit honestly, even when it's awkward.
  - You always enter passwords, codes, uploads and the final Submit yourself.
- **A daily rhythm** (`plan/daily-format.md`): a 3-hour morning block of Brief → Apply (up to 12) → Follow-ups → one
  rotating front (agencies, contract work, LinkedIn, networking, weekly review) → Triage → Close. Say
  "start my morning" and "done for today", and Claude keeps the cards and the log.
- **A pipeline** (`pipeline.csv`) is the single source of truth, from `sourced` through `offer`.
- **A dashboard doubles as your project tracker.** Claude refreshes it after every change; open `dashboard/index.html`
  in a browser to see where everything stands at a glance:
  - **Overview:** stage counts across the pipeline, a funnel-flow diagram (found → applied → screened → active, with
    rejections and no-responses shown), active conversations, an "On deck" agenda of sprints, interviews and
    follow-ups by week, and agency progress.
  - **Roles:** every opportunity in filterable tables, with fit score, pay, location, next step and due date; contract
    work in its own section.
  - **Network:** agencies and outreach, by stage.
  - **Resume and Bio:** your master resume and every bio, rendered with copy buttons for forms.
- **Scripts** do the repetitive work (Python 3, standard library only):

| Script | What it does |
|---|---|
| `scripts/tailor.py <spec.json>` | Builds a tailored resume (.md, .docx, .pdf) from your master resume and a small JSON spec: headline, summary, skills, bullet order, truthful keyword swaps. Also writes a changelog (Before / After / Reasoning) so you can review every change before you send it |
| `scripts/build_docx.py <file.md>` | ATS-friendly Word file: single column, real bullets, no tables or text boxes |
| `scripts/make_pdf.py <file.md>` | Matching PDF on Mac, Windows or Linux |
| `scripts/workday_resume.py <spec.json>` | A Workday-friendly variant (one block per position, no tagline) plus a paste sheet for fixing autofill by hand |
| `scripts/sweep.py` | Scans public Greenhouse, Lever, Ashby and Workday job boards (`companies/ats-boards.json`) for new matching roles |
| `scripts/do_not_submit.py` | A recruiter-ready list of roles you've already applied to, so agencies don't double-submit you |
| `scripts/build_dashboard.py` | Refreshes the dashboard data |

## Quick start

### 1. Set up Claude Cowork
Cowork is the mode of the Claude desktop app that can work with files on your computer.
1. **Get a paid Claude plan:** Cowork comes with Pro, Max, Team and Enterprise plans. On Team or Enterprise, your
   admin may need to turn it on.
2. **Install the Claude desktop app** for Mac or Windows from [claude.com/download](https://claude.com/download), and
   sign in. Keep it updated, especially on Windows.
3. **Open Cowork:** at the top of the app, switch from **Chat** to **Cowork**.

The app's layout changes from time to time. If a step doesn't match what you see, Anthropic's
[Get started with Cowork](https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork) guide has
the current version.

### 2. Get your copy of agent.cv
1. Click the green **Code** button at the top of this page, then **Download ZIP**, and unzip it.
   (GitHub users: **Use this template** makes your own copy of the repo. Make it **private**, then clone it.)
2. Put the `agent.cv` folder somewhere private, like your Documents folder.
3. **Add your LinkedIn profile:** on your LinkedIn profile page, click **More → Save to PDF**. Put that PDF, and any
   current resume, in `agent.cv/profile/materials/`.

### 3. Point Cowork at the folder
1. In Cowork, start a new task and choose a folder to work in. Pick **Use an existing folder** (the wording may vary)
   and select your `agent.cv` folder.
2. When Claude asks for access, allow it for **this folder only**. Don't give it your whole home folder or anything
   with financial documents.
3. Claude reads `CLAUDE.md`, the agency's operating manual, from the folder.

### 4. Paste the starter prompt
Copy this into Cowork and send it (it's also in [`STARTER-PROMPT.md`](STARTER-PROMPT.md)):

> You're my job search agency, and I'm your only client. Read CLAUDE.md in this folder: it's your operating manual. This is our first session, so start setup at Phase 1. Read my LinkedIn PDF and resume in profile/materials/, then interview me a few questions at a time. Coach me to a strong master resume, help me update LinkedIn to match it, and then ask me what jobs and industries I want to target. Don't send, submit or post anything without my explicit OK.

Setup runs in four phases over one to three sessions:
1. **Intake:** Claude reads your LinkedIn and resume, then asks about the gaps (numbers, scope, team size).
2. **Master resume:** Claude coaches you bullet by bullet to an ATS-safe resume, using only facts you confirm.
3. **LinkedIn:** Claude writes matching LinkedIn copy (headline, About, experience, skills) for you to paste in.
4. **Targets:** Claude asks what roles, industries, pay and location you want, then builds your job board list and
   runs the first search.

### 5. Every day after that
Open the same folder in Cowork and say **"start my morning."** Say **"done for today"** at the end. Keep the app open
while Claude is working with your files. Claude will ask before it runs anything new; approve what you're comfortable with.

**Prefer the terminal?** [Claude Code](https://claude.com/claude-code) works too: open a terminal in the `agent.cv`
folder, run `claude`, and paste the same starter prompt.

## Requirements
- **Claude** with access to a local folder: Cowork in the Claude desktop app (paid plans), or Claude Code. Tailoring
  and sourcing use a lot of messages, so a higher plan helps if you apply often.
- **Model:** built and tested with **Claude Opus 5.5**; use it for everything. Pick it in the app's model menu.
- **Python 3.9+.** It comes with macOS and most Linux distributions. On Windows, install it from python.org or the
  Microsoft Store, and use `py` wherever the docs say `python3`.
- **For PDFs:**
  - **macOS:** nothing extra; it uses the built-in text system.
  - **Windows:** nothing extra; it uses Microsoft Edge in headless mode, which ships with Windows 10 and 11.
  - **Linux:** install Chromium or Chrome (`sudo apt install chromium`), or LibreOffice (`sudo apt install libreoffice`).
    Also install `fonts-liberation`, an Arial-compatible font, so page counts match.
  - **Anywhere:** if no renderer is found, open the .docx in Word or Google Docs and save as PDF.

## Make it yours
- **`profile/config.json`** holds the dashboard title, your pay floor, the job-title and location filters for the sweep,
  and how many recent employers to show in full on a resume.
- **`companies/ats-boards.json`** starts empty. After asking what you're looking for, Claude finds the public job boards
  for your target employers and adds them, so the sweep only scans companies you care about.
- **Standing rules:** when you tell Claude "always do X" or "never say Y", it saves the rule in `CLAUDE.md`, so every
  future session follows it.

## Getting updates
agent.cv improves over time. To get the latest version, tell Claude **"update agent.cv."** Claude will:
1. Check this repo for a newer version and explain what changed (see [`CHANGELOG.md`](CHANGELOG.md)).
2. Show you exactly which files would change, and wait for your OK.
3. Replace only the project's own files: scripts, dashboard pages, templates and this manual. Your profile, resumes,
   pipeline, plans, logs and house rules are never touched. Everything it replaces is backed up to `backups/`.
4. If you've edited one of the project's files yourself, keep your version and help you merge in the new one.

Your own rules ("always…", "never…") live in `profile/house-rules.md`, so updates never overwrite them.

**For maintainers:** bump `VERSION`, add a `CHANGELOG.md` entry (with "Steps for existing users" if data changes), run
`python3 scripts/update.py manifest`, then push.

## Privacy
Your copy will hold your work history, salary targets and notes on every employer. **Keep it private.** Don't push your
filled-in copy to a public repository. If you use git, make the repo private. The `.gitignore` already skips generated
resumes, PDFs and dashboard data, but your profile and pipeline files are still tracked.

## Folder map
```
CLAUDE.md               operating manual (Claude reads this first)
STARTER-PROMPT.md       paste this into your first session
profile/                who you are: profile, targets, master resume, form answers, config
pipeline.csv            every opportunity and its stage
roles/ companies/       research on openings and employers; job board list; agency playbook
applications/           1-upcoming/<platform>/  →  2-submitted/<date>/  →  3-archive/
interviews/             prep sheets, debriefs, answer bank
outreach/               drafted messages, recruiter templates
plan/                   daily format, daily cards, apply queue, sprint plans
dashboard/              open index.html in a browser
scripts/                the tools above
log.md  backlog.md  board-checks.md  outreach.csv  agencies.csv  rtr.csv
```

## License
MIT. See [LICENSE](LICENSE). Use it, change it, share it. If it helps you land something, pass it on.
