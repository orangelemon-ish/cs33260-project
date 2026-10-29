# Schema report

## ratings
- rows: 240,306,182
- columns (35): noteId, raterParticipantId, createdAtMillis, version, agree, disagree, helpful, notHelpful, helpfulnessLevel, helpfulOther, helpfulInformative, helpfulClear, helpfulEmpathetic, helpfulGoodSources, helpfulUniqueContext, helpfulAddressesClaim, helpfulImportantContext, helpfulUnbiasedLanguage, notHelpfulOther, notHelpfulIncorrect, notHelpfulSourcesMissingOrUnreliable, notHelpfulOpinionSpeculationOrBias, notHelpfulMissingKeyPoints, notHelpfulOutdated, notHelpfulHardToUnderstand, notHelpfulArgumentativeOrBiased, notHelpfulOffTopic, notHelpfulSpamHarassmentOrAbuse, notHelpfulIrrelevantSources, notHelpfulOpinionSpeculation, notHelpfulNoteNotNeeded, ratedOnTweetId, ratingSourceBucketed, suggestion, suggestionId
- language-like columns: ['helpfulUnbiasedLanguage']
- `noteId`: 3,171,475 distinct (approx)
- `raterParticipantId`: 1,487,846 distinct (approx)
- `createdAtMillis`: 2021-01-23 07:50:22.12 to 2026-10-26 12:02:17.49 (240,306,182 non-empty)
- `helpfulnessLevel` values: 'HELPFUL'=147,833,764, 'NOT_HELPFUL'=86,271,910, 'SOMEWHAT_HELPFUL'=6,166,144, None=34,364
- `ratedOnTweetId`: 2,273,795 distinct (approx)
- `ratingSourceBucketed` values: 'DEFAULT'=237,976,553, 'POPULATION_SAMPLED'=2,329,629
- `suggestionId`: 22,594 distinct (approx)
