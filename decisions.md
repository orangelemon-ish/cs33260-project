# decisions.md

Rule: every definition, filter, or judgment call goes here the moment you make it,
with the date and who decided. The methods section of the paper is built from this file.

Status key: DECIDED / RECOMMENDED (awaiting team confirmation) / OPEN / CHECK (verify against data or docs) / SUPERSEDED

## A. Decisions from the proposal

| ID | Decision | Status | Notes |
|----|----------|--------|-------|
| D1 | Unit of analysis: post (`tweetId`) for RQ1; note (`noteId`) for RQ2 | DECIDED | |
| D2 | RQ2 population: notes created >= 30 days before snapshot | SUPERSEDED by W1-15 | Kept as sensitivity option |
| D3 | RQ1 population: posts whose first request/note is >= 14 days before the data cutoff | DECIDED | Cutoff date in W1-16 |
| D4 | Five fates (Under-rated, Unresolved, Rated not helpful, Published-then-removed, Published) | SUPERSEDED by W1-17 | |
| D5 | Minimum rating count for "Under-rated" is 5 | CHECK | Confirm in scoring code (W1-4) |
| D6 | Posts with no note by the cutoff are right-censored | DECIDED | |
| D7 | No regression discontinuity; report adjusted associations, not causal effects | DECIDED | Alert display time not in public data |
| D8 | Language splits only if a language field exists | SUPERSEDED by W1-7 | |
| D9 | Stack: Python, DuckDB/Parquet, lifelines, statsmodels | DECIDED | |

## B. Week 1 decisions

| ID | Question / decision | Status | Answer, date, who |
|----|---------------------|--------|-------------------|
| W1-1 | Raw data location | DECIDED | `/home/lawre/cs33260-project/data/raw/2026-10-28/` (never committed to git) |
| W1-2 | Analysis snapshot is 2026-10-28 (downloaded 2026-10-29). Data cutoff = 2026-10-26 12:49:53 UTC (max `timestampMillisOfCurrentStatus`) | DECIDED | |
| W1-3 | Downloader: `heruberuto/community-notes`; paste commit hash here (`git rev-parse HEAD`). Default output path in the script is hard-coded to `/mnt/data/...`, so we always pass `--out` | OPEN | hash: ______ |
| W1-4 | Rating threshold and status names confirmed from scoring code (file, line, value) | OPEN | Lawrence |
| W1-5 | How we obtained the note-request file | DECIDED | `batSignals-00000.tsv`, downloaded by Avni from X's logged-in Download Data page. Still to fill in: download date/time ______; login required? ______ |
| W1-6 | No daily cron job: snapshots are cumulative since 2021-01-23 and status history has the timestamps we need. Optionally re-download once in week 4 as a stability check | DECIDED | Confirmed by team 2026-10-29 |
| W1-7 | `notes` has no language column. No language splits, no Zenodo. DDIA validation uses the all-language figure only. Consequence: drop the language-detector, the 100-note manual labeling, and the English/Spanish comparison from the methods | DECIDED | Confirmed by team 2026-10-29 |
| W1-8 | **RQ2 population: surviving notes in `notes` that are also in `noteStatusHistory` (2,992,199).** Two other groups are tracked, not analyzed in the main fates: notes only in `notes` (254,804; presumably never scored) and notes only in `noteStatusHistory` (463,203; presumably deleted). Deleted notes are a survivorship-bias sensitivity check and a stated limitation | DECIDED | Confirmed by team 2026-10-29. The "presumably" labels are inferences from the README, not verified |
| W1-9 | Request-file checks (requester IDs? timestamps? cumulative? does RQ1 survive?) | ANSWERED | 2026-10-29: no requester IDs, no request counts, no per-request times. Only 30,657 of 517,786 posts (5.9%) have a valid in-app eligibility time; 99.3% of those (30,444) fall in Aug to Oct 2026, with only 213 earlier (earliest 2025-11-05). The API XL feed column is valid for 517,612 posts (99.97%), so the file is mostly an AI-writer-feed table. Usable RQ1 window is about Aug 1 to Oct 27, 2026. RQ1 as written (mid-2025 to 2026, request counts, requester reliability) is not possible (W1-21) |
| W1-10 | Do ratings contain duplicate (noteId, rater) rows? If so, how deduplicated | OPEN | Needs ratings table |
| W1-11 | All `...Millis` columns are UTC milliseconds since epoch; we report in UTC | DECIDED | |
| W1-12 | Always read columns by NAME, never by position (the notes file has 24 columns as of 2026) | DECIDED | |
| W1-13 | Timestamps <= 0 are treated as missing, with documented meanings: `timestampMillisOfMostRecentStatusChange` = -1 if the status never changed; `timestampMillisAbovePcrhThreshold` = -1 if cleared (e.g. after lock) and a NEGATIVE real timestamp if the note once exceeded the threshold but no longer does (this explains the 1913 dates). We do not currently use either column. The columns we do use have no sentinels | DECIDED | Docs read 2026-10-29 |
| W1-14 | **RQ2 is restricted to notes classified `MISINFORMED_OR_POTENTIALLY_MISLEADING`.** `NOT_MISLEADING` notes are excluded from the main analysis and reported in one footnote: only 2 of 603,428 are ever rated helpful | DECIDED | Team follows recommendation, 2026-10-29. (Counts are for notes in both tables) |
| W1-15 | Final fate = `lockedStatus`, falling back to `currentStatus`. Eligible notes created on or before **2026-10-11** (15 days before cutoff). Sensitivity: use `currentStatus`. Evidence: median lock lag 14.0 days, p90 14.2; current = locked for all but 51 of 3,203,561 locked notes | RECOMMENDED | Pending Lawrence's docs check on what a lock means. Open question: long tail (p99 = 309 days) |
| W1-16 | RQ1 age rule: posts whose first request or note is on or before **2026-10-12** | DECIDED | The old 30-day date (2026-09-26) is no longer used for RQ2 |
| W1-17 | Revised fates: Published; Published-then-removed (ever helpful, final not helpful); Rated not helpful (never helpful); for never-published notes, Under-rated vs. Unresolved by rating count (ratings before lock time); plus Never scored (the 254,804) tracked separately | RECOMMENDED | Finalize after ratings are loaded |
| W1-18 | `isMediaNote` and `isCollaborativeNote`. Docs: media note = about an image and appears on ALL posts containing that image (new 2023-05-24); collaborative note = flagged 1 if collaborative (new 2026-02-04; semantics beyond that not documented). Proposal: keep both in the main analysis; report RQ2 fates separately by each flag; for RQ1 post-level linking, rerun without media notes because their displayed posts differ from `tweetId` | RECOMMENDED | Confirm. Docs do not define how collaborative notes are scored; check the ranking pages |
| W1-19 | `timestampMillisOfFirstNmrDueToMinStableCrhTime` (118 sentinel rows, about 242,800 real values). Docs: the note first met the scoring rules to become helpful but was held at NMR until it had been stable for a minimum time. It does NOT describe reversals, so it does not explain the roughly 87,700 published-then-removed notes (my earlier guess was wrong). Possible extra category: notes held at NMR despite meeting helpful criteria | OPEN | Decide whether to report it as a sub-category of Unresolved; then explain published-then-removed using `lockedStatus` and the rescoring history |
| W1-20 | Request-file column meanings | DECIDED | From the Download Data page, 2026-10-29. `tweetId` = post on which a note request has appeared (in-product or via the AI Note Writer API). `noteRequestFeedEligibleAtMillis` = time requests met criteria to be shown to contributors in-app on the post (file name; docs call it `...Timestamp`); there may be extra display limits (only within N hours of post creation, only M hours after requests start showing); -1 if never on this feed. The three `api...FeedEligibleAtMillis` columns = same for the AI Note Writer API feeds (small / large / xl), -1 if never. `sourceLinks`, `suggestions` = optional requestor-provided arrays. Eligibility is NOT the same as actual display. Whether the file is cumulative is still unknown |
| W1-21 | RQ1 reformulation. Evidence from `requests_checks.md` and `request_window_checks.md` (2026-10-29): (1) in-app eligibility is 99.3% in Aug to Oct 2026; (2) 97.3% of request-file posts were created in Aug to Oct 2026; (3) notes per month are flat across Aug 2026 (about 100k in Jul and Aug), so the surge is in the request/eligibility records, not in note writing; (4) sparse older eligibility times exist (Nov 2025 onward), so it is not a simple rolling retention window. Most consistent with a rollout or expansion in Aug 2026 (inference, not verified). Identification problem for a causal event study: every post in the file eventually becomes eligible, and posts that never got a note or request are invisible, so there is no unexposed comparison group; the effect of eligibility is only identified from variation in WHEN posts became eligible. **Proposed RQ1 (descriptive):** among posts that became in-app eligible in Aug 1 to Oct 27, 2026, how quickly do notes follow, and how does that vary with post age at eligibility, month, and eligibility for the AI-writer feeds? Kaplan-Meier from eligibility for the at-risk posts; no causal claims. Event-study models only as an exploratory robustness check | DECIDED | Confirmed by team 2026-10-29: descriptive RQ1 (option b); event-study models only as an exploratory robustness check; option (c) rejected. The regime changed in Aug 2026, so findings describe that regime only. Describe the deviation from the proposal in the final paper |
| W1-22 | Can AI-written notes be identified in the data, and how do we handle them? An arXiv abstract (2609.40067, not yet read) says an AI note writer produced 52% of notes shown as helpful in June 2026. If true, 2026 fates mix human and AI notes and trends may reflect that shift | OPEN | Check top-author counts (see Log); read `isCollaborativeNote` docs (W1-18) Docs: `userEnrollment.enrollmentState = apiEarnedIn` marks AI Note Writer API authors (see W1-24). |
| W1-23 | Post creation time is derived from `tweetId` (snowflake ID: (id >> 22) + 1288834974657 = creation time in ms since epoch). Validate by decoding at least 5 tweetIds and comparing with the timestamps shown on the posts themselves | RECOMMENDED | Not yet validated. Needed for time-since-post controls and eligibility lag in RQ1 |
| W1-24 | AI note writers: `userEnrollment.enrollmentState = apiEarnedIn` marks AI Note Writer API authors. Proposal: join on note author ID and report RQ2 fates for AI vs. human authors for 2025 to 2026. Caveat: enrollment state is the current state, not historical | RECOMMENDED | Confirm; check how many notes have `apiEarnedIn` authors |
| W1-25 | Ratings table (week 2): docs describe `createdAtMillis` as 'time the note was created' (probably a copy-paste error; verify it is the rating time by checking rating time >= note time). `ratingSourceBucketed` = POPULATION_SAMPLED for ratings made via 'Needs Your Help' notifications (new 2025-09-30): decide whether to count them in the rating minimum. Also `ratedOnTweetId` may differ from the note's `tweetId` for media notes | OPEN | |
| W1-26 | tweetId quality. Counts from `request_window_checks.md` section D: request file 113 of 517,786 rows decoded before 2015 (0.02%); notes 8 non-positive IDs plus 268 pre-2015 IDs (276 of 3,247,003, 0.009%). The decode formula does not apply to them. Rule: drop these rows from any analysis that uses decoded post time and report the counts | DECIDED | Negligible share; no further action needed beyond dropping them |
| W1-27 | RQ1 sample definition: posts with `noteRequestFeedEligibleAtMillis` valid and >= 2026-08-01 (30,444 posts). At risk = no note before eligibility (19,550 posts; 10,227 noted later, 9,323 with no note in the notes table, some of which may have had deleted notes). The 213 earlier-eligible posts are excluded from the main analysis and reported in a footnote. Rows failing W1-26 are dropped | DECIDED | Confirmed by team 2026-10-29 together with W1-21 |

## C. Corrections to the submitted proposal (note in the final paper)

- The proposal says daily snapshots stay available only about a week. In fact the CDN keeps roughly a week of daily snapshots (confirmed by `--list`: 2026-10-22 to 10-28, 10-25 missing), but each snapshot is cumulative since January 2021 (confirmed: earliest note 2021-01-23). One download is enough.
- Zenodo archive is not used (see W1-7).
- Fates and age rules differ from the proposal text (W1-15, W1-16, W1-17).
- The proposal assumed per-request records (requester IDs, request timestamps, request counts). The public request file is post-level feed-eligibility timestamps. Planned RQ1 variables 'number and timing of requests', the Cox model by request count, and requester reliability are not available (W1-9, W1-21).
- Column names in the docs differ from the files: docs `latestNonNMRStatus` vs file `mostRecentNonNMRStatus`; docs `participantId` vs file `noteAuthorParticipantId`; docs `currentDecidedByKey` vs file `currentDecidedBy`; docs `noteRequestFeedEligibleTimestamp` vs file `noteRequestFeedEligibleAtMillis` (same for the API columns). Always use the file's names (W1-12).
- The proposal planned to study requests from mid-2025 to 2026. The public request file supports only about Aug 1 to Oct 27, 2026 for in-app eligibility, and most of the file is AI-writer API feed eligibility (W1-9).

## D. Facts established so far (for the data section of the paper)

- Tables: notes 3,247,003 rows (24 columns); noteStatusHistory 3,455,402 (24 columns); userEnrollment 1,510,511 (8 columns); ratings: pending.
- Posts: 2,208,841 distinct `tweetId`; mean 1.47 notes per post; max 112; 617,017 posts with more than one note.
- Current status across all 3,455,402 notes in status history: NEEDS_MORE_RATINGS 3,025,572; CURRENTLY_RATED_HELPFUL 291,512 (8.4%); CURRENTLY_RATED_NOT_HELPFUL 138,318.
- Roughly 87,700 notes were rated helpful at some point and are now back to needs-more-ratings (about 23% of ever-helpful notes). Needs a careful definition (W1-17).
- `timestampMillisOfFirstNonNMRStatus` begins 2022-05-19, so time-to-helpful is unavailable for earlier publications.
- Request file: 517,786 rows, 7 columns, one row per post (distinct `tweetId` = rows). Four eligibility-timestamp columns plus `sourceLinks` and `suggestions`. Each timestamp column contains -1 sentinel values (1969-12-31 23:59:59.999). Latest valid timestamp 2026-10-27. Earliest valid timestamp not yet determined.
- Request file valid timestamps: in-app 30,657 (earliest 2025-11-05); API small 30,991; API large 180,775; API XL 517,612 (earliest 2026-02-11). In-app eligibility by month: Aug 2026 6,793; Sep 11,338; Oct 12,313; all months before Aug combined 213 (Jul 153).
- Posts in the request file with at least one note in the notes table: 126,761 of 517,786 (24.5%); that is 5.7% of the 2,208,841 posts that have notes.
- First note after post creation (decoded from tweetId): median 7.1h for in-app-eligible posts vs. 8.0h for all posts with notes (p90 24.3h vs. 35.9h). Not yet validated (W1-23, W1-26).
- Notes per month (notes table): 2025 ranged 53k to 113k; 2026: Jan 75.7k, Feb 83.7k, Mar 101.2k, Apr 104.3k, May 104.7k, Jun 98.1k, Jul 100.5k, Aug 100.4k, Sep 114.4k, Oct (through Oct 26) 111.1k. No jump in Aug 2026. The rise from Jan to Mar 2026 may relate to AI writers or collaborative notes (W1-22, W1-24, W1-18); not checked.
- Request-file posts by decoded creation month: about 150 to 3,000 per month from Jan 2025 to Jul 2026, then Aug 2026 120,012; Sep 192,459; Oct 191,418 (97.3% of the file). 3,162 posts were created before 2025.
- In-app eligible posts by month with at least one note: Aug 4,800 of 6,793 (70.7%); Sep 7,953 of 11,338 (70.1%); Oct 8,368 of 12,313 (68.0%). Noted before eligibility: Aug 2,350; Sep 3,945; Oct 4,599.

## E. Log (newest at bottom)

- 2026-10-29: `--list` showed snapshots 2026-10-22 to 10-28 (10-25 missing). Downloaded 2026-10-28.
- 2026-10-29: `cn_downloader.py` crashed on the default output path; resolved with `--out`.
- 2026-10-29: Parquet conversion of notes, noteStatusHistory, userEnrollment OK (row counts match source lines).
- 2026-10-29: Week-1 checks run. Overlap 2,992,199 / 254,804 / 463,203. W1-8 and W1-14 confirmed by team.
- 2026-10-29: W1-6 (no cron job) and W1-7 (no language splits) confirmed by team.

- 2026-10-29: Request file converted (517,786 rows). Schema shows a post-level eligibility table, not per-request records (W1-9).
- 2026-10-29: RQ1 options to decide in W1-21: (a) event-study of first-note hazard before vs. after `noteRequestFeedEligibleAtMillis`, if W1-20 shows that column marks when requests made a post visible to writers; (b) descriptive RQ1 only (which posts become eligible, how fast notes follow), no causal framing; (c) drop RQ1 and make RQ2 the whole project.
- 2026-10-29: Could not open the Download Data page directly (no page-fetch tool); search did not return the Note Requests column definitions. Avni to paste the Note Requests section (W1-20). Two leads from search: (1) a dataset paper describes the Note Requests table as recording requests submitted by X users, added after Dec 2024; (2) arXiv 2609.40067 says explicit note requests and user posts determine the AI API post feeds, which suggests the `api...FeedEligibleAtMillis` columns relate to AI-writer feeds and are not purely request-driven. Both unverified.
- 2026-10-29: Read the Download Data documentation. Resolved W1-20; clarified W1-13, W1-18, W1-19; added W1-23 to W1-25 (W1-22 was already in the file). Correction: the min-stable-CRH column is about holding a note at NMR until stable, not about reversals.

- 2026-10-29: `requests_checks.md` reviewed. In-app eligibility is concentrated in Aug to Oct 2026; half of noted posts had a note before eligibility; no hard cap on eligibility timing visible. Next: `05_request_window_checks.py`, then decide W1-21.

- 2026-10-29: `request_window_checks.md` reviewed. Notes volume flat in Aug 2026 while request-file posts rose about 40x, so the August jump is in request/eligibility records. tweetId quality problems are negligible (W1-26 decided). Recommended RQ1 is descriptive on Aug to Oct 2026 (W1-21, W1-27).

- 2026-10-29: Team chose descriptive RQ1 (W1-21) and the Aug 1 to Oct 27, 2026 in-app-eligible sample (W1-27). Deviation from the proposal to be explained in the final paper.