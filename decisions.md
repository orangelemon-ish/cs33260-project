# decisions.md

Logged = decided. Open items sit at the end of each week. The long Week 1 version is in `decisions_archive_week1.md`.

## Research questions (final)

**Topic:** why proposed Community Notes fail to become Helpful, and whether requests and AI writers change that.

**RQ1 (requests and speed).** For posts first eligible between 2026-08-13 and 2026-10-12:
- (a) How quickly does a first note follow the first request (the XL time), and does this differ by the highest request feed the post later reached (XL only, Large, or Small = in-app display)?
- (b) Among posts that reach in-app display with no note yet, what share get a first note within 24 hours (6 and 72 hours secondary), and how often is that first note AI-written?

*Descriptive; no causal claims.*

**RQ2 (failure modes).** For notes created 2024-12-13 to 2026-09-06 (extended series from 2023-02-01):
- (a) What share of notes ends in each fate: Published, Published-then-removed, Rated not helpful, Near miss, Unresolved, Under-rated?
- (b) How do these shares change month by month as scoring rules change and ratings per note fall?
- (c) Do fates differ for AI-written vs. other notes, once deleted notes are included?

**Working expectation (from the 1% sample, to be tested):** most failures are notes that were rated but not resolved, not notes that went unrated; under-rating may rise in 2026 as ratings per note fall.

**Out of scope:** causal effects of requests, language splits, requester-level analysis (not in the data).

## Glossary

| Term | Meaning |
|---|---|
| Post | An X post, identified by `tweetId`. |
| Note | A proposed piece of context on a post, written by a volunteer or an AI; a proposal until the community approves it. |
| Rating | A contributor's vote on a note: helpful, somewhat helpful, or not helpful. |
| Top Writer | A writer with at least 4% of notes rated Helpful and writing impact (Helpful minus Not Helpful notes) of at least 10; only they see request alerts. |
| Status | Needs More Ratings (NMR, the default), Currently Rated Helpful (CRH, shown to everyone), or Currently Rated Not Helpful (CRNH). |
| Bridging | A note becomes Helpful only if raters who usually disagree both rate it helpful; since 2025-03-27 it needs at least 5 raters on each side, so about 10 ratings. |
| Lock | X freezes a note's status about two weeks after creation; we treat it as the final status. |
| Fate | Our outcome label for a note, in order of precedence: Published (final Helpful); Published-then-removed (was Helpful, is not); Rated not helpful; Near miss (met Helpful criteria but held by a stability rule, ended NMR); Unresolved (NMR, 5+ ratings); Under-rated (NMR, fewer than 5 ratings). |
| Request | A user with a verified phone number clicks "Request Community Note" on a post. |
| Display criteria (alert) | Top Writers see an alert for 24 hours when requests reach MAX(4, views / 25,000), or 2 requests come from medium-score requestors, or 1 from a high-score requestor. |
| Eligible | A post met the display criteria; we see the time, not whether anyone saw the alert. |
| Requestor helpfulness score | A requestor's record of requests that led to Helpful notes; a better score lets fewer requests trigger an alert. |
| Feeds (XL / Large / Small) | Nested lists of posts offered to AI writers through the API: XL needs about one request, Large more, Small matches in-app display. The larger XXL feed is not in our file. |
| AI note writer | Automated writer admitted since 2025-09-02, identified by `apiEarnedIn`; wrote about 48% of notes in Sep and Oct 2026. |
| Deleted-like note | In status history but not in the notes table, probably deleted; AI writers delete many of their own. |
| At-risk post | An eligible post with no note yet when it became eligible. |
| Main window | RQ2: notes created 2024-12-13 to 2026-09-06. RQ1: the request file covers only about Aug 13 to Oct 27, 2026. |

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

### Decisions

| ID | Decision | Notes |
|---|---|---|
| W2-1 | **Fate table:** one row per status-history note, with flags for the main window, extended window, deleted-like, author type and class. Every analysis filters this one table (main population, S2, extended). | Built by `10_build_fate_table.py` into `data/derived/` (never committed). Verified: final-status totals match the earlier full-table check exactly. |
| W2-2 | **Validation accepted:** the fate table reproduces the published figures closely. Through 2025-06-25, 82.2% of notes never left NMR (Gong & Wu: 83.1%); through 2025-03-31, 11.4% were ever Helpful, and over all history 91.6% of notes are not currently Helpful (DDIA: over 90% never published). | DDIA's "published" most likely means currently Helpful, not ever Helpful. Our status-history count through 2025-06-25 is 2,111,978 vs. Gong & Wu's 2,108,340. |
| W2-3 | **Near miss is 0 before 2024-08-01 by construction** (the stability-hold field starts then), so any figure or claim that spans earlier months reports Unresolved and Near miss together; trend claims use the main window (from 2024-12-13). | Under-rated depends only on rating counts, not on scoring rules, so its trend can be read across the whole series. |
| W2-4 | **RQ1 first notes come from the notes table only.** Deleted notes have no post ID there, so posts whose only note was deleted count as having no note. | About 20% of AI notes are deleted, so speeds and the AI share of first notes are approximate; state this as a limitation. |
| W2-5 | **The Aug 2024 step is explained and is a data break, not behavior.** From notes created on 2024-07-25, notes with no rating at all drop from about 7 to 8% to about 0.3%, which accounts for nearly all of the 5 to 6 point fall in Under-rated. The extended-series figures mark 2024-07-25 as a break; the main window (from 2024-12-13) is unaffected. | Not a lock artifact: counting ratings in a fixed first 14 days gives the same shares within 0.4 points. The date matches the change-log entry on faster scoring of new notes; the mechanism is our guess (faster scoring puts new notes in rating queues). |

### Open items

- Optional: why AI notes get fewer ratings than human notes (median about 9 vs. 15), for example lower-visibility posts.

## C. Changes from the proposal

- RQ1 is descriptive and uses a different clock; RQ3 is dropped; language splits and Zenodo are dropped.
- The first look at the data does not support the expected result that under-rating causes most failures (main window: 21.5% under-rated vs. 58.4% rated but unresolved).
- Three papers already study requests, none of them AI writers, and they used per-request data that no longer exists in the public file.

## D. Key facts

- Tables: 3.25M notes, 3.46M in status history, 240.3M ratings, 1.51M users, 517,786 requested posts. About 8.4% of notes are currently Helpful.
- Scoring rule changes to mark on plots: 2025-03-27, 04-08, 05-28, 06-30, 11-10; 2026-06-30, 07-28, 08-03, 09-21.
- Display criteria: MAX(4, views/25,000) requests, or 2 medium-score requestors, or 1 high-score requestor; shown 24 hours; requesting needs a verified phone number.
- Ratings per new note fell from about 114 (Sep 2025) to about 42 (Aug and Sep 2026).
- Fates in the main window (main population, 1,222,673 notes): Published 11.4%, Published-then-removed 2.4%, Rated not helpful 4.3%, Near miss 1.9%, Unresolved 58.4%, Under-rated 21.5%. Fate-table totals match the earlier full-table check exactly.
- Monthly trend (main population): Under-rated rose from about 20% (Mar 2026) to 26.5% (Apr 2026) and 29 to 30% (Aug and Sep 2026), while Unresolved fell from about 59% to about 54%; this starts the same month AI notes jumped from 14% to 37% of all notes. Published-then-removed fell from 4.6% (2024) to 2.5% (2025) after the Oct 2024 flip-flop fix. Published slipped from about 12 to about 10 to 11% in 2026.
- Author type, Mar to Aug 2026 (main population): Under-rated rose for human notes (19.9% to 25.4%) and AI notes (21.6% to 32.8%); about 85% of the 8.6-point overall rise is within-type and about 15% is AI notes growing from 17% to 46% of notes. Median ratings per note: human 28 (Jan 2026) to 15 (Aug); AI 29 to 9. So rating attention is spread thinner for everyone.
- AI vs. other notes, Jul to Oct 2026 (S2, deleted included): Published 9 to 10% for AI vs. 5 to 7% for others; Under-rated 29 to 31% vs. 26.5 to 27.6%. Surviving AI notes (main population) look better (Published 11 to 13%), so deletion flatters AI.
- AI authors wrote about 56% of Helpful notes created in June 2026 (the paper's Community Writer alone: 52%) and 44.7% of all notes (Community Writer: 41%).
- RQ1 sample (first eligible 2026-08-13 to 10-12): 395,951 posts; highest feed reached: XL only 259,500, Large 113,663, Small/in-app 22,788. Among posts with no note at first eligibility, a first note within 72 hours: XL only 10.0%, Large 36.1%, Small/in-app 66.6%; when a note comes it is fast (median 0.2 to 0.8 hours); AI wrote 56 to 72% of first notes within 24 hours.
- RQ1b (in-app group, 22,788 posts): 35.3% already had a note before display; of the 14,739 without one, 46.3% got a first note within 6 hours of display, 52.4% within 24 hours, 53.6% within 72 hours; AI wrote 53.7% of those 24-hour first notes.
- Aug 2024 step: unrated notes disappear from 2024-07-25 (0 ratings: 7 to 8% to 0.3%), so Under-rated falls from 23.1% (Jul) to 18.0% (Aug). Ratings per new note also rose from about 63 to 67 (Jan to Jun 2024) to 91 to 94 (Aug to Oct 2024). Across periods, Under-rated moves opposite to ratings per new note: 24.6% at 67 (Jun 2024), 18 to 19% at 91 to 94 (Aug to Oct 2024), 28.8% at about 42 (Aug 2026).
- Validation: 82.2% of notes never left NMR by 2025-06-25 (Gong & Wu: 83.1%); 11.4% ever Helpful by 2025-03-31 (DDIA: over 90% never published, i.e. currently Helpful).
- Deleted-like notes are 9.7% of the main window; 2.7% of them are Helpful vs. 9.4% of the rest.

## E. Log

- 2026-10-29: Data downloaded, converted, and checked; week-1 decisions confirmed by the team.
- 2026-10-29: Request file found to be post-level; RQ1 redesigned. The August 2026 "jump" was a retention window, not a rollout.