# Lock checks

Data cutoff (max timestampMillisOfCurrentStatus): 2026-10-26 12:49:53.368 UTC

## 1. Notes created 2023-02-01 or later and at least 15 days before the cutoff
| notes | locked | % locked | locked within 13.5-14.5 days | lag p1 (days) | lag p50 | lag p99 |
|---|---|---|---|---|---|---|
| 3,336,511 | 3,144,789 | 94.254 | 2,892,569 | 14.0 | 14.01 | 74.69 |

## 2. lockedStatus vs currentStatus (same population, locked notes only)
| lockedStatus | currentStatus | n |
|---|---|---|
| NEEDS_MORE_RATINGS | NEEDS_MORE_RATINGS | 2,744,723 |
| CURRENTLY_RATED_HELPFUL | CURRENTLY_RATED_HELPFUL | 267,765 |
| CURRENTLY_RATED_NOT_HELPFUL | CURRENTLY_RATED_NOT_HELPFUL | 132,268 |
| CURRENTLY_RATED_NOT_HELPFUL | NEEDS_MORE_RATINGS | 33 |

## 3. Same population but NOT locked (should be rare if the two-week rule is universal)
| currentStatus | n |
|---|---|
| NEEDS_MORE_RATINGS | 172,121 |
| CURRENTLY_RATED_HELPFUL | 15,848 |
| CURRENTLY_RATED_NOT_HELPFUL | 3,753 |

## 4. Notes created before 2023-02-01 (retro-lock era)
| notes | with retro lock | with any lock |
|---|---|---|
| 54,735 | 1,512 | 54,735 |

## 5. Locked status by creation year (population for the RQ2 trend)
| year | lockedStatus | n |
|---|---|---|
| 2023 | CURRENTLY_RATED_HELPFUL | 36,397 |
| 2023 | CURRENTLY_RATED_NOT_HELPFUL | 17,590 |
| 2023 | NEEDS_MORE_RATINGS | 373,075 |
| 2024 | CURRENTLY_RATED_HELPFUL | 88,227 |
| 2024 | CURRENTLY_RATED_NOT_HELPFUL | 45,582 |
| 2024 | NEEDS_MORE_RATINGS | 916,729 |
| 2025 | CURRENTLY_RATED_HELPFUL | 67,600 |
| 2025 | CURRENTLY_RATED_NOT_HELPFUL | 37,605 |
| 2025 | NEEDS_MORE_RATINGS | 685,669 |
| 2026 | CURRENTLY_RATED_HELPFUL | 75,541 |
| 2026 | CURRENTLY_RATED_NOT_HELPFUL | 31,524 |
| 2026 | NEEDS_MORE_RATINGS | 769,250 |

## 6. tweetId decode sanity: notes whose decoded post time is LATER than the note's own creation time (a correct decode should give about 0%; media notes may add a few)
| notes (valid IDs) | decoded post later than note | % | median hours from post to note |
|---|---|---|---|
| 3,246,727 | 0 | 0.0 | 9.45 |
