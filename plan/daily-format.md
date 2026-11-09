# The Morning Block: your daily format
Adjust the times and the rotation to your life; Claude follows whatever this file says.

**One 3-hour block, every weekday morning, 9:00–12:00.** Same order every day. The block is for *doing*: sending,
submitting, deciding. All research, sourcing and material-building happens outside the block (Claude's prep shift).

## The rules (anti-sidetrack)
1. **Execution only.** No new research, no new sources, no new tools or file tweaks during the block.
2. **New idea? Park it.** Say *"park: …"* and Claude adds it to the Parking Lot below. It gets discussed Friday, not now.
3. **Only submit what's ready.** If an application kit isn't ready, skip it. Never build materials during the block.
4. **Hard stops.** When a block's time is up, stop. Unfinished items go to the top of tomorrow's card.
5. **Max 12 applications a day.** Tailored, not sprayed: every one still gets its kit and changelog. Fast platforms (Ashby, Greenhouse, Lever) take 5–10 minutes with a kit ready; account-based portals take longer, so batch them on a "Wheel of Pain" day. The cap protects the other fronts.
6. **Decisions are fast.** In triage, every lead gets *yes / no / later* in about 30 seconds. No deep dives.
7. **Report as you go.** Say *"done: Acme"* (or *"skipped: …"*). Claude logs it, so you never update files yourself.

## The block
| Time | Block | What happens |
|---|---|---|
| 9:00–9:10 | **0. Brief** | Say *"start my morning."* Claude gives today's card: what's due, what's ready, any replies. Read it, no discussion. |
| 9:10–10:30 | **1. Apply** (80 min) | Submit up to 12 applications from the Ready queue, top to bottom (fit 4–5 first). Whatever isn't done moves to the top of tomorrow. Kit open, cheat sheet open, submit, say "done." |
| 10:30–10:50 | **2. Follow-ups & replies** (20 min) | Answer any recruiter or employer reply first. Then send follow-ups due today (Claude has drafts ready). |
| 10:50–11:00 | Break | Stand up. Away from the screen. |
| 11:00–11:40 | **3. Today's front** (40 min) | One front per weekday (below). Do only that front. |
| 11:40–11:55 | **4. Triage** (15 min) | Default is YES (anything remotely relevant goes into `plan/apply-queue.md`). You only flag the ones to skip. |
| 11:55–12:00 | **5. Close** | Say *"done for today."* Claude logs everything and sets tomorrow's card. |

## Weekly rotation for Block 3
| Day | Front | Typical tasks |
|---|---|---|
| **Mon** | **Agencies** | Register with 2–3 agencies from agencies.csv; send batched agency notes; reply to recruiters. |
| **Tue** | **Contract & consulting** | Consulting profile, contract and freelance applications, work samples. |
| **Wed** | **LinkedIn & visibility** | Comment on 3–5 posts in your field; one short post every other week; profile tweaks Claude suggests. |
| **Thu** | **Network & warm intros** | Referral asks, coffee-chat requests, thank-yous. 2–3 personal messages. |
| **Fri** | **Weekly review + new ground** | Review the week's numbers with Claude; read the Parking Lot; 20 min on pivots, wildcards or learning. |

## Claude's prep shift (outside the block, when you say "prep tomorrow")
- Build resumes, cover letters and apply kits for every lead you said "yes" to in triage.
- Draft follow-ups and referral notes due tomorrow.
- Check that tomorrow's postings are still open.
- **Fridays:** run the full sweep (`scripts/sweep.py` + browser-only boards) and queue new leads for Monday's triage.
- Write tomorrow's card: `plan/<date>.md`.

## Words that run the system
- **"start my morning"**: today's card.
- **"done: X"** / **"skipped: X"**: log it.
- **"park: X"**: Parking Lot.
- **"done for today"**: close out and set tomorrow.
- **"prep tomorrow"**: Claude's prep shift.

## Interview days
When an interview is scheduled, it outranks everything: the day before, Block 3 becomes a 40-min **mock interview with Claude**, and the
Apply block shrinks to 1 application. Prep sheets live in `interviews/`.

## Parking Lot (reviewed Fridays)
- (empty)
