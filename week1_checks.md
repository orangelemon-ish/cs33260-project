# Week 1 checks

Snapshot cutoff (max timestampMillisOfCurrentStatus): 2026-10-26 12:49:53.368 UTC

## 1. Table overlap (deleted notes live only in noteStatusHistory)
| in both | only in notes | only in noteStatusHistory |
|---|---|---|
| 2,992,199 | 254,804 | 463,203 |

## 2. Sentinel timestamps (values <= 0) per millis column in noteStatusHistory
| column | rows with value <= 0 |
|---|---|
| createdAtMillis | 0 |
| timestampMillisOfFirstNonNMRStatus | 0 |
| timestampMillisOfCurrentStatus | 0 |
| timestampMillisOfLatestNonNMRStatus | 0 |
| timestampMillisOfStatusLock | 0 |
| timestampMillisOfRetroLock | 0 |
| timestampMillisOfMostRecentStatusChange | 1,093,540 |
| timestampMillisOfNmrDueToMinStableCrhTime | 2,275,981 |
| timestampMinuteOfFinalScoringOutput | 0 |
| timestampMillisOfFirstNmrDueToMinStableCrhTime | 118 |
| timestampMillisAbovePcrhThreshold | 31,302 |

## 3. Lock lag in days (timestampMillisOfStatusLock - createdAtMillis), notes with a lock
| n | p10 | p50 | p90 | p99 |
|---|---|---|---|---|
| 3,203,561 | 14.0 | 14.0 | 14.2 | 309.2 |

## 4. currentStatus vs lockedStatus (all notes)
| currentStatus | lockedStatus | n |
|---|---|---|
| NEEDS_MORE_RATINGS | NEEDS_MORE_RATINGS | 2,798,366 |
| CURRENTLY_RATED_HELPFUL | CURRENTLY_RATED_HELPFUL | 271,441 |
| NEEDS_MORE_RATINGS |  | 227,155 |
| CURRENTLY_RATED_NOT_HELPFUL | CURRENTLY_RATED_NOT_HELPFUL | 133,703 |
| CURRENTLY_RATED_HELPFUL |  | 20,071 |
| CURRENTLY_RATED_NOT_HELPFUL |  | 4,615 |
| NEEDS_MORE_RATINGS | CURRENTLY_RATED_NOT_HELPFUL | 48 |
| NEEDS_MORE_RATINGS | CURRENTLY_RATED_HELPFUL | 3 |

## 5. firstNonNMRStatus vs mostRecentNonNMRStatus vs currentStatus (published-then-removed candidates)
| first | most recent | current | n |
|---|---|---|---|
|  |  | NEEDS_MORE_RATINGS | 2,865,553 |
| CURRENTLY_RATED_HELPFUL | CURRENTLY_RATED_HELPFUL | CURRENTLY_RATED_HELPFUL | 290,502 |
| CURRENTLY_RATED_NOT_HELPFUL | CURRENTLY_RATED_NOT_HELPFUL | CURRENTLY_RATED_NOT_HELPFUL | 137,915 |
| CURRENTLY_RATED_HELPFUL | CURRENTLY_RATED_HELPFUL | NEEDS_MORE_RATINGS | 87,674 |
| CURRENTLY_RATED_NOT_HELPFUL | CURRENTLY_RATED_NOT_HELPFUL | NEEDS_MORE_RATINGS | 72,306 |
|  |  | CURRENTLY_RATED_HELPFUL | 982 |
|  |  | CURRENTLY_RATED_NOT_HELPFUL | 375 |
| CURRENTLY_RATED_NOT_HELPFUL | CURRENTLY_RATED_HELPFUL | NEEDS_MORE_RATINGS | 30 |
| CURRENTLY_RATED_NOT_HELPFUL | CURRENTLY_RATED_HELPFUL | CURRENTLY_RATED_HELPFUL | 28 |
| CURRENTLY_RATED_HELPFUL | CURRENTLY_RATED_NOT_HELPFUL | CURRENTLY_RATED_NOT_HELPFUL | 28 |
| CURRENTLY_RATED_HELPFUL | CURRENTLY_RATED_NOT_HELPFUL | NEEDS_MORE_RATINGS | 9 |

## 6. Notes created per year x currentStatus
| year | currentStatus | n |
|---|---|---|
| 2,021 | CURRENTLY_RATED_HELPFUL | 672 |
| 2,021 | CURRENTLY_RATED_NOT_HELPFUL | 202 |
| 2,021 | NEEDS_MORE_RATINGS | 22,196 |
| 2,022 | CURRENTLY_RATED_HELPFUL | 2,211 |
| 2,022 | CURRENTLY_RATED_NOT_HELPFUL | 1,080 |
| 2,022 | NEEDS_MORE_RATINGS | 23,747 |
| 2,023 | CURRENTLY_RATED_HELPFUL | 38,486 |
| 2,023 | CURRENTLY_RATED_NOT_HELPFUL | 18,337 |
| 2,023 | NEEDS_MORE_RATINGS | 398,692 |
| 2,024 | CURRENTLY_RATED_HELPFUL | 97,536 |
| 2,024 | CURRENTLY_RATED_NOT_HELPFUL | 47,898 |
| 2,024 | NEEDS_MORE_RATINGS | 1,031,281 |
| 2,025 | CURRENTLY_RATED_HELPFUL | 69,955 |
| 2,025 | CURRENTLY_RATED_NOT_HELPFUL | 37,656 |
| 2,025 | NEEDS_MORE_RATINGS | 691,438 |
| 2,026 | CURRENTLY_RATED_HELPFUL | 82,652 |
| 2,026 | CURRENTLY_RATED_NOT_HELPFUL | 33,145 |
| 2,026 | NEEDS_MORE_RATINGS | 858,218 |

## 7. Posts: notes per tweetId (notes table)
| posts | mean notes/post | max notes/post | posts with >1 note |
|---|---|---|---|
| 2,208,841 | 1.47 | 112 | 617,017 |

## 8. classification x currentStatus (notes in both tables)
| classification | currentStatus | n |
|---|---|---|
| MISINFORMED_OR_POTENTIALLY_MISLEADING | NEEDS_MORE_RATINGS | 2,048,618 |
| NOT_MISLEADING | NEEDS_MORE_RATINGS | 566,766 |
| MISINFORMED_OR_POTENTIALLY_MISLEADING | CURRENTLY_RATED_HELPFUL | 275,721 |
| MISINFORMED_OR_POTENTIALLY_MISLEADING | CURRENTLY_RATED_NOT_HELPFUL | 64,432 |
| NOT_MISLEADING | CURRENTLY_RATED_NOT_HELPFUL | 36,660 |
| NOT_MISLEADING | CURRENTLY_RATED_HELPFUL | 2 |
