# Request file checks

Columns: tweetId, noteRequestFeedEligibleAtMillis, apiSmallFeedEligibleAtMillis, apiLargeFeedEligibleAtMillis, apiXlFeedEligibleAtMillis, sourceLinks, suggestions

## 1. Eligibility timestamps: rows with value <= 0 (missing) vs valid, and valid date range
| column | rows | <= 0 | valid | earliest valid | latest valid |
|---|---|---|---|---|---|
| noteRequestFeedEligibleAtMillis | 517,786 | 487,129 | 30,657 | 2025-11-05 05:28:13.032 | 2026-10-27 15:37:23.417 |
| apiSmallFeedEligibleAtMillis | 517,786 | 486,795 | 30,991 | 2025-11-03 04:44:18.282 | 2026-10-27 15:37:23.417 |
| apiLargeFeedEligibleAtMillis | 517,786 | 337,011 | 180,775 | 2025-10-29 17:19:48.331 | 2026-10-27 15:37:23.435 |
| apiXlFeedEligibleAtMillis | 517,786 | 174 | 517,612 | 2026-02-11 16:14:28.534 | 2026-10-27 18:38:01.227 |

## 2. Posts per month by `noteRequestFeedEligibleAtMillis`
| month | posts |
|---|---|
| 2025-11 | 1 |
| 2026-01 | 1 |
| 2026-03 | 2 |
| 2026-04 | 4 |
| 2026-05 | 13 |
| 2026-06 | 39 |
| 2026-07 | 153 |
| 2026-08 | 6,793 |
| 2026-09 | 11,338 |
| 2026-10 | 12,313 |

## 2. Posts per month by `apiSmallFeedEligibleAtMillis`
| month | posts |
|---|---|
| 2025-11 | 16 |
| 2025-12 | 19 |
| 2026-01 | 21 |
| 2026-02 | 52 |
| 2026-03 | 75 |
| 2026-04 | 64 |
| 2026-05 | 73 |
| 2026-06 | 75 |
| 2026-07 | 164 |
| 2026-08 | 6,791 |
| 2026-09 | 11,335 |
| 2026-10 | 12,306 |

## 2. Posts per month by `apiLargeFeedEligibleAtMillis`
| month | posts |
|---|---|
| 2025-10 | 2 |
| 2025-11 | 60 |
| 2025-12 | 41 |
| 2026-01 | 62 |
| 2026-02 | 145 |
| 2026-03 | 204 |
| 2026-04 | 165 |
| 2026-05 | 219 |
| 2026-06 | 217 |
| 2026-07 | 439 |
| 2026-08 | 40,280 |
| 2026-09 | 67,938 |
| 2026-10 | 71,003 |

## 2. Posts per month by `apiXlFeedEligibleAtMillis`
| month | posts |
|---|---|
| 2026-02 | 209 |
| 2026-03 | 328 |
| 2026-04 | 292 |
| 2026-05 | 365 |
| 2026-06 | 410 |
| 2026-07 | 805 |
| 2026-08 | 117,053 |
| 2026-09 | 196,441 |
| 2026-10 | 201,709 |

## 3. Overlap with notes (by tweetId)
| request-file posts | of those with >= 1 note | posts with notes (all) | of those in request file |
|---|---|---|---|
| 517,786 | 126,761 | 2,208,841 | 126,761 |

## 4. Days from `noteRequestFeedEligibleAtMillis` to first note (negative = note came first)
| posts with valid time and a note | first note BEFORE eligibility | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| 21,280 | 10,976 | -0.47 | -0.14 | -0.0 | 0.01 | 0.13 |

## 4. Days from `apiSmallFeedEligibleAtMillis` to first note (negative = note came first)
| posts with valid time and a note | first note BEFORE eligibility | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| 21,550 | 11,097 | -0.47 | -0.14 | -0.0 | 0.01 | 0.13 |

## 4. Days from `apiLargeFeedEligibleAtMillis` to first note (negative = note came first)
| posts with valid time and a note | first note BEFORE eligibility | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| 82,873 | 22,985 | -0.2 | -0.0 | 0.01 | 0.01 | 0.14 |

## 4. Days from `apiXlFeedEligibleAtMillis` to first note (negative = note came first)
| posts with valid time and a note | first note BEFORE eligibility | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| 126,675 | 25,107 | -0.07 | 0.0 | 0.01 | 0.02 | 0.27 |

## 5. Non-empty counts in other columns
| column | non-empty rows |
|---|---|
| sourceLinks | 125,168 |
| suggestions | 517,786 |

## 6. Post creation time decoded from tweetId (sanity check; validate by hand on a few posts, see decisions W1-23)
| table | earliest decoded | latest decoded |
|---|---|---|
| request file | 2010-11-04 01:42:55.005 | 2026-10-27 15:53:17.086 |
| posts with notes | 2010-11-04 01:42:54.656 | 2026-10-26 11:43:08.807 |

## 7. Hours from post creation to `noteRequestFeedEligibleAtMillis` (docs say eligibility may be capped within N hours of post creation; a hard cap would show up here)
| posts | p1 | p10 | p50 | p90 | p99 | % > 24h | % > 48h | % > 168h |
|---|---|---|---|---|---|---|---|---|
| 30,657 | 0.49 | 2.08 | 10.4 | 28.76 | 110.9 | 15.5 | 2.7 | 0.7 |

## 8. Hours from post creation to first note
| group | posts | p10 | p50 | p90 |
|---|---|---|---|---|
| in request feed (valid eligibility) | 21,280 | 1.38 | 7.09 | 24.34 |
| all posts with notes | 2,208,841 | 0.67 | 7.97 | 35.93 |

## 9. First note relative to feed eligibility (posts with a note)
| posts | before eligibility | 0-6h after | 6-24h after | 24-72h after | >72h after |
|---|---|---|---|---|---|
| 21,280 | 10,976 | 8,896 | 1,159 | 215 | 34 |
