# Ratings checks

Sample: notes with hash(noteId) % 100 = 0 (all their ratings). Full-table sections are marked.

## A. Sample size
| ratings | notes with ratings | notes in status history |
|---|---|---|
| 2,437,253 | 33,371 | 34,644 |

## B. Duplicate (noteId, rater) pairs in the sample (W1-10)
| ratings | extra rows from duplicate pairs |
|---|---|
| 2,437,253 | 0 |

## C. Rating time vs. note creation time (W1-25: is `createdAtMillis` in ratings the RATING time? expect about 0 ratings before the note)
| ratings joined | rating BEFORE note creation | p1 (hours after note) | p50 | p99 | % later than 48h |
|---|---|---|---|---|---|
| 2,436,737 | 0 | 0.06 | 6.32 | 2395.04 | 6.2 |

## D. Ratings made AFTER the note's lock time (notes with a lock)
| ratings on locked notes | after lock | % |
|---|---|---|
| 2,325,756 | 48,836 | 2.1 |

## E. Main window (created 2024-12-13 to 2026-09-06): ratings received up to lock time, by final status (sample). NMR with 5+ ratings = Unresolved candidates; NMR with fewer = Under-rated (W1-17, W1-28)
| final status | ratings up to lock | notes |
|---|---|---|
| CURRENTLY_RATED_HELPFUL | 10+ | 1,415 |
| CURRENTLY_RATED_NOT_HELPFUL | 1-4 | 1 |
| CURRENTLY_RATED_NOT_HELPFUL | 10+ | 585 |
| CURRENTLY_RATED_NOT_HELPFUL | 5-9 | 93 |
| NEEDS_MORE_RATINGS | 0 | 22 |
| NEEDS_MORE_RATINGS | 1-4 | 3,495 |
| NEEDS_MORE_RATINGS | 10+ | 8,474 |
| NEEDS_MORE_RATINGS | 5-9 | 2,168 |

## F. Validation of the threshold: notes that ever left Needs More Ratings, with fewer than 5 ratings made by that time (expect near 0%; if not, our counting rule needs revisiting)
| notes that got a first status | with < 5 ratings by then | % |
|---|---|---|
| 5,867 | 33 | 0.56 |

## G. FULL TABLE: ratings per month from 2025-09 and the population-sampled share (W1-25)
| month | ratings | population-sampled | % |
|---|---|---|---|
| 2025-09 | 6,842,414 | 143,716 | 2.1 |
| 2025-10 | 6,077,504 | 141,061 | 2.32 |
| 2025-11 | 5,412,606 | 124,775 | 2.31 |
| 2025-12 | 5,266,604 | 117,785 | 2.24 |
| 2026-01 | 7,270,056 | 145,001 | 1.99 |
| 2026-02 | 5,705,104 | 102,347 | 1.79 |
| 2026-03 | 6,274,152 | 129,215 | 2.06 |
| 2026-04 | 5,082,139 | 106,871 | 2.1 |
| 2026-05 | 4,977,629 | 93,497 | 1.88 |
| 2026-06 | 4,532,438 | 88,152 | 1.94 |
| 2026-07 | 4,641,543 | 109,238 | 2.35 |
| 2026-08 | 4,089,181 | 101,271 | 2.48 |
| 2026-09 | 4,657,615 | 90,745 | 1.95 |
| 2026-10 | 4,583,742 | 59,650 | 1.3 |

## H. FULL TABLE: ratings per year and how many have no `helpfulnessLevel` (older ratings used the deprecated binary flags)
| year | ratings | no helpfulnessLevel |
|---|---|---|
| 2021 | 147,744 | 34,364 |
| 2022 | 831,666 | 0 |
| 2023 | 26,204,623 | 0 |
| 2024 | 88,721,401 | 0 |
| 2025 | 72,587,149 | 0 |
| 2026 | 51,813,599 | 0 |

## I. FULL TABLE: notes in status history with NO ratings at all, by creation year (these count as Under-rated with 0 ratings)
| year | notes | with no ratings | % |
|---|---|---|---|
| 2021 | 23,070 | 6,997 | 30.33 |
| 2022 | 27,038 | 4,367 | 16.15 |
| 2023 | 455,515 | 48,950 | 10.75 |
| 2024 | 1,176,715 | 69,948 | 5.94 |
| 2025 | 799,049 | 1,300 | 0.16 |
| 2026 | 974,015 | 702 | 0.07 |
