# Request window checks

## A. Notes created per month (notes table, 2025 onward). A jump in Aug 2026 would suggest a platform change
| month | notes |
|---|---|
| 2025-01 | 113,412 |
| 2025-02 | 89,821 |
| 2025-03 | 79,197 |
| 2025-04 | 57,269 |
| 2025-05 | 54,316 |
| 2025-06 | 58,071 |
| 2025-07 | 53,891 |
| 2025-08 | 53,324 |
| 2025-09 | 58,768 |
| 2025-10 | 62,595 |
| 2025-11 | 63,353 |
| 2025-12 | 64,205 |
| 2026-01 | 75,712 |
| 2026-02 | 83,665 |
| 2026-03 | 101,176 |
| 2026-04 | 104,252 |
| 2026-05 | 104,728 |
| 2026-06 | 98,115 |
| 2026-07 | 100,504 |
| 2026-08 | 100,401 |
| 2026-09 | 114,439 |
| 2026-10 | 111,088 |

## B. Request-file posts by decoded post-creation month (tests whether the file is a rolling window of recent posts)
| post month | posts |
|---|---|
| 2025-01 | 149 |
| 2025-02 | 153 |
| 2025-03 | 149 |
| 2025-04 | 169 |
| 2025-05 | 137 |
| 2025-06 | 171 |
| 2025-07 | 235 |
| 2025-08 | 221 |
| 2025-09 | 256 |
| 2025-10 | 282 |
| 2025-11 | 287 |
| 2025-12 | 255 |
| 2026-01 | 408 |
| 2026-02 | 583 |
| 2026-03 | 721 |
| 2026-04 | 942 |
| 2026-05 | 1,099 |
| 2026-06 | 1,488 |
| 2026-07 | 3,030 |
| 2026-08 | 120,012 |
| 2026-09 | 192,459 |
| 2026-10 | 191,418 |
| before 2025 | 3,162 |

## C. In-app feed eligible posts by eligibility month: how many have any note, and how many had a note BEFORE eligibility
| eligibility month | posts | with >= 1 note | note before eligibility |
|---|---|---|---|
| 2025-11 | 1 | 0 | 0 |
| 2026-01 | 1 | 1 | 1 |
| 2026-03 | 2 | 1 | 0 |
| 2026-04 | 4 | 2 | 0 |
| 2026-05 | 13 | 10 | 3 |
| 2026-06 | 39 | 29 | 19 |
| 2026-07 | 153 | 116 | 59 |
| 2026-08 | 6,793 | 4,800 | 2,350 |
| 2026-09 | 11,338 | 7,953 | 3,945 |
| 2026-10 | 12,313 | 8,368 | 4,599 |

## D. tweetId quality (decoded creation before 2015 means pre-snowflake or invalid ID; the decode formula does not apply to them)
| table | rows | not numeric | <= 0 | decoded before 2015 |
|---|---|---|---|---|
| request file | 517,786 | 0 | 0 | 113 |
| notes | 3,247,003 | 0 | 8 | 268 |

## E. Event-study sample: posts with valid in-app eligibility
| group | posts | note before eligibility | at risk at eligibility | of those, noted later | of those, no note in notes table |
|---|---|---|---|---|---|
| eligible Aug 2026 or later | 30,444 | 10,894 | 19,550 | 10,227 | 9,323 |
| eligible before Aug 2026 | 213 | 82 | 131 | 77 | 54 |

(Posts with no note may have had notes that were later deleted; deleted notes are not in the notes table.)
