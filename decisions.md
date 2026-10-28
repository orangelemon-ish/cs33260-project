# decisions.md

Rule: every definition, filter, or judgment call goes here the moment you make it,
with the date and who decided. The methods section of the paper is built from this file.

Status key: DECIDED / OPEN / CHECK (needs verification against data or docs)

## A. Decided in the proposal (carry forward)

| ID | Decision | Status | Notes |
|----|----------|--------|-------|
| D1 | Unit of analysis: post (`tweetId`) for RQ1; note (`noteId`) for RQ2 | DECIDED | |
| D2 | RQ2 population: notes created >= 30 days before snapshot | DECIDED | Sensitivity: 14 / 60 days |
| D3 | RQ1 population: posts with first request/note >= 14 days before snapshot | DECIDED | Limits truncation bias |
| D4 | Fates: Under-rated, Unresolved, Rated not helpful, Published-then-removed, Published | DECIDED | Definitions in proposal table |
| D5 | Minimum rating count for "Under-rated" is 5 | CHECK | Confirm in scoring code (see W1-5) |
| D6 | Posts with no note by snapshot are right-censored | DECIDED | |
| D7 | No regression discontinuity; report adjusted associations, not causal effects | DECIDED | Alert display time not in public data |
| D8 | Language splits only if a language field exists | CHECK | See W1-8 |
| D9 | Stack: Python, DuckDB/Parquet, lifelines, statsmodels | DECIDED | |

## B. Week 1 decisions to make (fill in as you go)

| ID | Question | Status | Answer / date / who |
|----|----------|--------|---------------------|
| W1-1 | Team roles (pipeline / RQ1 / RQ2)? Suggestion: Luke = pipeline, Avni = RQ1, Lawrence = RQ2; everyone writes | OPEN | |
| W1-2 | Where raw data lives (path, disk). Raw data is never committed to git or shared | OPEN | |
| W1-3 | Snapshot date used as THE analysis snapshot (record the folder name, e.g. 2026-10-27) | OPEN | |
| W1-4 | Downloader: which tool and which commit hash (record `git rev-parse HEAD`) | OPEN | |
| W1-5 | Rating threshold and status names, confirmed from scoring code: file, line, value | OPEN | |
| W1-6 | How we obtained the note-request file (login page? filename? date) | OPEN | |
| W1-7 | Snapshot cadence after the main one: weekly, or none (see note below) | OPEN | |
| W1-8 | Does `notes` have a language field? If not: no language splits, drop Zenodo | OPEN | |
| W1-9 | Deleted notes: they vanish from `notes` but stay in `noteStatusHistory`. RQ2 population = notes in `noteStatusHistory`, or notes in both tables? | OPEN | |
| W1-10 | Request file: earliest/latest date, requester IDs present?, cumulative? Does RQ1 survive? | OPEN | |
| W1-11 | Do ratings contain duplicate (noteId, rater) rows? If so, how deduplicated | OPEN | |
| W1-12 | Timestamp convention: all `...Millis` columns are UTC milliseconds since epoch; we report in UTC | DECIDED | |
| W1-13 | Column handling: always read by column NAME, never by position (the notes file gained a 24th column in 2026) | DECIDED | |

## C. Corrections to the submitted proposal (note in final paper, no need to resubmit)

- Proposal says daily snapshots stay available only about a week. A third-party README says snapshots are cumulative since January 2021, so one fresh download covers all history. Verify with `--list` and then fix this in the paper.
- Zenodo archive: likely unnecessary if current `notes` already has a language column or if you don't split by language.

## D. Log (append newest at bottom)

- YYYY-MM-DD, initials: what was decided and why
