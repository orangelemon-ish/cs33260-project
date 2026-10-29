# Schema report

## noteStatusHistory
- rows: 3,455,402
- columns (24): noteId, noteAuthorParticipantId, createdAtMillis, timestampMillisOfFirstNonNMRStatus, firstNonNMRStatus, timestampMillisOfCurrentStatus, currentStatus, timestampMillisOfLatestNonNMRStatus, mostRecentNonNMRStatus, timestampMillisOfStatusLock, lockedStatus, timestampMillisOfRetroLock, currentCoreStatus, currentExpansionStatus, currentGroupStatus, currentDecidedBy, currentModelingGroup, timestampMillisOfMostRecentStatusChange, timestampMillisOfNmrDueToMinStableCrhTime, currentMultiGroupStatus, currentModelingMultiGroup, timestampMinuteOfFinalScoringOutput, timestampMillisOfFirstNmrDueToMinStableCrhTime, timestampMillisAbovePcrhThreshold
- language-like columns: NONE
- `noteId`: 3,455,402 distinct
- `noteAuthorParticipantId`: 372,195 distinct
- `createdAtMillis`: 2021-01-23 01:54:44.227 to 2026-10-26 12:39:39.997 (3,455,402 non-empty)
- `timestampMillisOfFirstNonNMRStatus`: 2022-05-19 19:55:55.132 to 2026-10-26 12:49:53.368 (588,492 non-empty)
- `firstNonNMRStatus` values: None=2,866,910, 'CURRENTLY_RATED_HELPFUL'=378,213, 'CURRENTLY_RATED_NOT_HELPFUL'=210,279
- `timestampMillisOfCurrentStatus`: 2024-07-25 15:07:48.424 to 2026-10-26 12:49:53.368 (3,455,402 non-empty)
- `currentStatus` values: 'NEEDS_MORE_RATINGS'=3,025,572, 'CURRENTLY_RATED_HELPFUL'=291,512, 'CURRENTLY_RATED_NOT_HELPFUL'=138,318
- `timestampMillisOfLatestNonNMRStatus`: 2022-05-19 19:55:55.132 to 2026-10-26 12:49:53.368 (588,492 non-empty)
- `timestampMillisOfStatusLock`: 2023-01-18 00:51:49.873 to 2026-10-26 12:49:53.368 (3,203,561 non-empty)
- `lockedStatus` values: 'NEEDS_MORE_RATINGS'=2,798,366, 'CURRENTLY_RATED_HELPFUL'=271,444, None=251,841, 'CURRENTLY_RATED_NOT_HELPFUL'=133,751
- `timestampMillisOfRetroLock`: 2022-08-14 00:00:00 to 2023-01-18 06:29:27.238 (1,512 non-empty)
- `timestampMillisOfMostRecentStatusChange`: 1969-12-31 23:59:59.999 to 2026-10-26 12:49:53.368 (3,455,402 non-empty)
- `timestampMillisOfNmrDueToMinStableCrhTime`: 1969-12-31 23:59:59.999 to 2026-10-26 12:41:30.035 (2,276,022 non-empty)
- `timestampMillisOfFirstNmrDueToMinStableCrhTime`: 1969-12-31 23:59:59.999 to 2026-10-26 12:41:30.035 (242,947 non-empty)
- `timestampMillisAbovePcrhThreshold`: 1913-03-08 11:18:29.965 to 2026-10-26 12:11:31.982 (31,343 non-empty)

## notes
- rows: 3,247,003
- columns (24): noteId, noteAuthorParticipantId, createdAtMillis, tweetId, classification, believable, harmful, validationDifficulty, misleadingOther, misleadingFactualError, misleadingManipulatedMedia, misleadingOutdatedInformation, misleadingMissingImportantContext, misleadingUnverifiedClaimAsFact, misleadingSatire, notMisleadingOther, notMisleadingFactuallyCorrect, notMisleadingOutdatedButNotWhenWritten, notMisleadingClearlySatire, notMisleadingPersonalOpinion, trustworthySources, summary, isMediaNote, isCollaborativeNote
- language-like columns: NONE
- `noteId`: 3,247,003 distinct
- `noteAuthorParticipantId`: 349,156 distinct
- `createdAtMillis`: 2021-01-28 00:27:47.892 to 2026-10-26 12:00:28.263 (3,247,003 non-empty)
- `tweetId`: 2,208,841 distinct
- `classification` values: 'MISINFORMED_OR_POTENTIALLY_MISLEADING'=2,618,935, 'NOT_MISLEADING'=628,066, None=2

## userEnrollment
- rows: 1,510,511
- columns (8): participantId, enrollmentState, successfulRatingNeededToEarnIn, timestampOfLastStateChange, timestampOfLastEarnOut, modelingPopulation, modelingGroup, numberOfTimesEarnedOut
- language-like columns: NONE
- `participantId`: 1,510,511 distinct
