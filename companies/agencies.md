# Recruiting & placement agencies: playbook

## How agencies actually work (so we use them well)
- **Recruiters work for the employer, not the candidate.** They're paid when they fill the employer's role. Your job is to
  be the obvious, easy candidate for the roles they already have, and memorable for the next one.
- **Contingency recruiters** (most staffing firms) are paid only on a hire, often 15–25% of first-year salary. They move
  fast and submit widely, so you need to control where your resume goes.
- **Retained search firms** are paid upfront for a specific senior search and work exclusively on it. They call you when a
  search fits, so the goal is to be in their network and easy to find.
- **Contract/staffing firms** place people in temp, contract and contract-to-hire roles. They'll ask your rate and whether
  you want W-2 or 1099.
- **Fractional/interim networks** vet you once, then match you to projects.

## Best practices
1. **Be easy to place.** Give a clear target (titles, level, sectors), pay or rate, location/remote, start date and work
   authorization in the first message. Vague "open to anything" candidates get skipped.
2. **Lead with a tailored, ATS-clean resume.** Recruiters forward documents as they are.
3. **Make LinkedIn do the work.** Recruiters search by keywords and filter on Open to Work. Keep Open to Work on with
   recruiter-only visibility, a keyword-rich headline and skills, and a clear call to action in About.
4. **Control your submissions.** Ask every recruiter to get your OK before submitting you anywhere, and to name the
   employer first. Never let two agencies submit you to the same role, and never let an agency submit you somewhere
   you've applied directly. Send the do-not-submit list (`outreach/Do-Not-Submit.pdf`).
5. **Go wide on databases, deep on a few people.** Registering on 20–40 sites is cheap. Real relationships are with 2–3
   specialist recruiters per track.
6. **Reach named recruiters,** not only "submit resume" forms. Find the practice lead on LinkedIn and send a short note.
7. **Respond within 24 hours** and be candid (pay, other processes, why you left).
8. **Prep for the recruiter screen like an interview:** 60-second pitch, top 3 wins with numbers, why you left, what you
   want, pay, availability.
9. **Stay warm without being a pest:** a short update every 3–4 weeks, and send referrals their way.
10. **Know your numbers:** full-time base target and floor; contract hourly floor. W-2 contract rates run lower than 1099
    rates because the agency pays employer taxes.

## Stages in agencies.csv
`to-register` → `registered` → `in-conversation` → `active` (they're submitting you, with your OK) → `dormant` (no
activity in 6+ weeks) | `skip`

## Exclusivity and direct applications
- **Overall exclusivity is not normal.** Say up front: "I'm working with a few agencies and applying directly; please get
  my OK before each submission."
- **Exclusivity is per role.** Once an agency submits you to a specific job (often via a "right to represent" email),
  don't apply to that role directly or through another agency.
- **Marketplaces and fractional networks** usually have a non-circumvention clause. Read it before accepting.
- **Red flags:** blanket exclusivity, any fee charged to you, or a submission without your consent.

## Right-to-represent (RTR) tracking
When a recruiter asks for an RTR, paste it to Claude before replying. Claude checks it against `companies/do-not-submit.md`
and pipeline.csv, flags any exclusivity window or rate issue, and drafts your reply. After you approve it, Claude logs it in
`rtr.csv`, adds a pipeline row (source = agency, stage = applied), and regenerates the do-not-submit list.
