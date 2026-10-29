# decisions.md

## Week 1: data and design

### Decisions

| ID | Decision | Notes |
|---|---|---|
| W1-1 | **Data:** public Community Notes dump, snapshot 2026-10-28 (cutoff 2026-10-26 12:49 UTC), converted to Parquet with DuckDB; raw data never goes in git. | Downloader `heruberuto/community-notes` @ e44e4b4; scoring code `twitter/communitynotes` @ 93647eb. Ratings are a folder of parts, converted one at a time. |
| W1-2 | **Conventions:** read columns by name; all `...Millis` are UTC; values ≤ 0 are missing; no daily cron (one snapshot is cumulative since 2021); no language splits (no language column), no Zenodo. | Post creation time = `(tweetId >> 22) + 1288834974657`, checked by hand against X; drop the 276 notes and 113 request rows with invalid IDs. |
| W1-3 | **RQ2 population:** notes in both `notes` and status history, classified misleading. Main window: created 2024-12-13 to 2026-09-06. Extended series: 2023-02-01 to 2026-10-11, clearly labeled. | NOT_MISLEADING notes almost never become Helpful (2 of 603,428). Window starts after stabilization began for Expansion notes (2024-12-12) and ends before the 2026-09-21 Not Helpful rule. |
| W1-4 | **Final status** = `lockedStatus`, else `currentStatus`. Unlocked notes (5.75%) are kept using `currentStatus`, with sensitivity runs excluding them and excluding the Jul to Sep 2024 cohorts. | X locks status two weeks after creation (median 14.0 days). Unlocked notes follow the model that decided them, not deletion. |
| W1-5 | **Fates**, in order of precedence: Published; Published-then-removed; Rated not helpful; Near miss; Unresolved (NMR, 5+ ratings); Under-rated (NMR, under 5 ratings). | Near miss = held by the stability rule, final NMR, created from 2024-08-01. Never-scored (254,804) and deleted-like (463,203) notes are counted separately. |
| W1-6 | **Ratings:** count all ratings up to lock time; always show the split <5, 5 to 9, 10+. Sensitivity: Under-rated means <10 ratings for notes created from 2025-03-27. | Status needs 5 ratings; Helpful effectively needs 10 since 2025-03-27 (5 raters on each side). No duplicate ratings found; rating time confirmed. |
| W1-7 | **Media and collaborative notes** stay in the main analysis; report fates by each flag; for RQ1, rerun without media notes. | A media note appears on every post with that image. |
| W1-8 | **AI authors** = `enrollmentState = apiEarnedIn` (current state). Stratify RQ2 by author type from Sep 2025. Every author-type comparison is also shown on S2 = all status-history notes in the window, deleted included, no classification filter. | AI authors wrote about 48% of notes in Sep and Oct 2026; about 20% of their notes are deleted since Apr 2026, vs. 3 to 6% for others. |
| W1-9 | **RQ1 is descriptive.** The request file is post-level eligibility times (no requester IDs or counts), kept only for about 75 days, so use posts first eligible 2026-08-13 to 2026-10-12. | XL time is about the first request; feeds nest XL, Large, then Small, and Small equals in-app eligibility (checked). No causal model, no Cox replication. |
| W1-10 | **RQ1 outcome:** share of posts with no note at eligibility that get a first note within 24 hours of in-app eligibility (6 and 72 hours secondary), with Kaplan-Meier curves; split AI-authored vs. other first notes. | Eligibility means the display criteria were met, not that the request was shown. Display rules are in `note-requests.md`. |

### Open items

- Optional: 223 posts have a Large time before their XL time, and 347 have a Small time but no in-app time; unexplained and small.

## Week 2: fate table and trends

### Open items

- Build the note-level fate table and check it against the 1% sample (8.7% Helpful, 4.2% Not Helpful, 21.6% under-rated, 65.5% 5+ ratings but NMR).
- Monthly fate shares with confidence intervals and rule-change dates marked.
- Test the AI-writer paper's claims: AI share of Helpful notes created in June 2026 (at least 52%) and of all notes (at least 41%).
- Recount the RQ1 sample for the 2026-08-13 to 2026-10-12 window.
- Validate against DDIA's finding that over 90% of notes never publish.

## C. Changes from the proposal

- RQ1 is descriptive and uses a different clock; RQ3 is dropped; language splits and Zenodo are dropped.
- The first look at the data does not support the expected result that under-rating causes most failures (21.6% under-rated vs. 65.5% rated but unresolved).
- Three papers already study requests, none of them AI writers, and they used per-request data that no longer exists in the public file.

## D. Key facts

- Tables: 3.25M notes, 3.46M in status history, 240.3M ratings, 1.51M users, 517,786 requested posts. About 8.4% of notes are currently Helpful.
- Scoring rule changes to mark on plots: 2025-03-27, 04-08, 05-28, 06-30, 11-10; 2026-06-30, 07-28, 08-03, 09-21.
- Display criteria: MAX(4, views/25,000) requests, or 2 medium-score requestors, or 1 high-score requestor; shown 24 hours; requesting needs a verified phone number.
- Ratings per new note fell from about 114 (Sep 2025) to about 42 (Aug and Sep 2026).
- Deleted-like notes are 9.7% of the main window; 2.7% of them are Helpful vs. 9.4% of the rest.

## E. Log

- 2026-10-29: Data downloaded, converted, and checked; week-1 decisions confirmed by the team.
- 2026-10-29: Request file found to be post-level; RQ1 redesigned. The August 2026 "jump" was a retention window, not a rollout.