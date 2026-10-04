# Performance completion GraphQL contract

Coordinator-reviewed contract for the approved performance completion scope. All administration operations require `performance:manage` at `ALL` scope. Employee and manager KPI operations continue to use the existing self/team authority and the participant's snapshotted reporting relationship. User validation remains unrun.

## Query

```graphql
type Query {
  performanceProgramPolicy(performanceProgramId: ID!): PerformanceProgramPolicy!
  performanceAdminCycles(input: PerformanceAdminCyclesInput!): PerformanceAdminCyclePage!
  performanceCycleAdministration(reviewCycleId: ID!, cursor: String, limit: Int = 50): PerformanceCycleAdministration!
  performancePopulationOptions(input: PerformancePopulationOptionsInput!): PerformancePopulationOptions!
  privatePerformanceFeedback(input: PrivatePerformanceFeedbackInput!): PerformanceFeedbackPage!
  performanceGoalKpis(participantId: ID!, goalId: ID): [PerformanceGoalKpi!]!
  performanceReviewRevision(participantId: ID!, revision: Int!): PerformanceReviewRevisionDetail!
}

input PerformanceAdminCyclesInput { cursor: String, limit: Int = 20, status: String, performanceProgramId: ID }
type PerformanceAdminCyclePage { items: [PerformanceAdminCycle!]!, nextCursor: String }
type PerformanceAdminCycle { reviewCycle: ReviewCycle!, currentStage: String!, participantCount: Int!, excludedParticipantCount: Int!, actionableExceptionCount: Int! }
type PerformanceCycleAdministration { reviewCycle: ReviewCycle!, currentStage: String!, deadlines: [PerformanceStageDeadline!]!, participants: [PerformanceParticipantAdministration!]!, nextParticipantCursor: String, exceptions: [PerformanceAdminException!]! }
type PerformanceStageDeadline { stage: String!, dueDate: Date! }
type PerformanceParticipantAdministration { participantId: ID!, employeeId: ID!, employeeName: String!, managerEmployeeId: ID, status: String!, isExcluded: Boolean!, exclusionReason: String, responseRevision: Int!, selfSubmittedAt: DateTime, managerSubmittedAt: DateTime, acknowledgedAt: DateTime, managerRating: String, finalRating: String, performanceBand: String, calibrationProvenance: String, revisions: [PerformanceReviewRevision!]! }
type PerformanceReviewRevision { revision: Int!, reopenedAt: DateTime, reopenedByUserId: ID, reopenReason: String, correctionStage: String!, selfSubmittedAt: DateTime, managerSubmittedAt: DateTime, acknowledgedAt: DateTime, managerRating: String, finalRating: String, performanceBand: String, calibrationProvenance: String }
type PerformanceCalibrationDecision { id: ID!, revision: Int!, finalRating: String!, performanceBand: String, reason: String!, decidedByUserId: ID!, decidedAt: DateTime! }
type PerformanceReviewRevisionDetail { review: PerformanceReviewRevision!, answers: [AppraisalAnswer!]!, kpis: [PerformanceGoalKpi!]!, calibrations: [PerformanceCalibrationDecision!]!, acknowledgementComment: String }
type PerformanceAdminException { id: ID!, exceptionCode: String!, details: String!, resolvedAt: DateTime, createdAt: DateTime }
input PerformancePopulationOptionsInput { mode: PerformancePopulationMode!, search: String, cursor: String, limit: Int = 50 }
type PerformancePopulationOptions { items: [PerformancePopulationOption!]!, nextCursor: String }
type PerformancePopulationOption { id: ID!, name: String!, departmentId: ID, locationId: ID }
input PrivatePerformanceFeedbackInput { participantId: ID!, cursor: String, limit: Int = 20 }
type PerformanceFeedbackPage { items: [PerformanceFeedback!]!, nextCursor: String }
```

`privatePerformanceFeedback` returns only private HR entries and is absent from every existing public review/detail query. Use the existing database visibility literal/constraint (HR_ONLY if that is the current schema); it is not a client-selectable field in the dedicated private operation.

History detail is manage-ALL only for this administration release; do not weaken existing SELF/TEAM current-review access. A prior revision's answer/KPI/acknowledgement/calibration snapshot is immutable. The current revision can be read through this same authorized history query. Cycle administration returns unresolved actionable exceptions; participant pagination must be stable. All list limits are bounded to 1..100 and cursors validated server-side. Population option selection must retain chosen IDs across pages/searches.

## Program policy and population

```graphql
input PerformanceProgramPolicyInput {
  performanceProgramId: ID!
  populationMode: PerformancePopulationMode!
  populationIds: [ID!]! = []
  goalSettingDueDays: Int
  selfReviewDueDays: Int
  managerReviewDueDays: Int
  calibrationDueDays: Int
  acknowledgementDueDays: Int
}
enum PerformancePopulationMode { ALL DEPARTMENTS LOCATIONS EMPLOYEES }
type PerformanceProgramPolicy { performanceProgramId: ID!, archivedAt: DateTime, populationMode: PerformancePopulationMode!, populationIds: [ID!]!, goalSettingDueDays: Int, selfReviewDueDays: Int, managerReviewDueDays: Int, calibrationDueDays: Int, acknowledgementDueDays: Int }
```

Each non-`ALL` mode accepts only tenant identifiers of its declared kind. Launch writes an immutable participant snapshot and cycle deadline snapshot; later policy changes apply only to later cycles.

## Mutations

```graphql
type Mutation {
  savePerformanceProgramPolicy(input: PerformanceProgramPolicyInput!): PerformanceProgramPolicy!
  archivePerformanceProgram(performanceProgramId: ID!, reason: String!): PerformanceProgram!
  savePerformanceCalibration(input: SavePerformanceCalibrationInput!): PerformanceParticipantAdministration!
  reopenPerformanceReview(input: ReopenPerformanceReviewInput!): PerformanceParticipantAdministration!
  setPerformanceParticipantExcluded(input: SetPerformanceParticipantExcludedInput!): PerformanceParticipantAdministration!
  addPrivatePerformanceFeedback(input: AddPrivatePerformanceFeedbackInput!): PerformanceFeedback!
  savePerformanceKpiTarget(input: SavePerformanceKpiTargetInput!): PerformanceGoalKpi!
  submitPerformanceKpiActual(input: SubmitPerformanceKpiActualInput!): PerformanceGoalKpi!
  deletePerformanceGoalKpi(participantId: ID!, goalKpiId: ID!): Boolean!
  retryPerformanceException(exceptionId: ID!): PerformanceAdminException!
}

input SavePerformanceCalibrationInput { participantId: ID!, expectedRevision: Int!, finalRating: String!, performanceBand: String, reason: String! }
input ReopenPerformanceReviewInput { participantId: ID!, expectedRevision: Int!, correctionStage: PerformanceCorrectionStage!, reason: String! }
enum PerformanceCorrectionStage { SELF_REVIEW MANAGER_REVIEW }
input SetPerformanceParticipantExcludedInput { participantId: ID!, excluded: Boolean!, reason: String! }
input AddPrivatePerformanceFeedbackInput { participantId: ID!, goalId: ID, observationDate: Date!, comments: String! }
input SavePerformanceKpiTargetInput { participantId: ID!, goalId: ID!, id: ID, metricName: String!, targetValue: String, unit: String }
input SubmitPerformanceKpiActualInput { participantId: ID!, goalKpiId: ID!, expectedRevision: Int!, actualValue: String, evidence: String, comment: String, measurementDate: Date }
type PerformanceGoalKpi { id: ID!, goalId: ID!, metricName: String!, targetValue: String, actualValue: String, unit: String, evidence: String, comment: String, measurementDate: Date }
```

`savePerformanceCalibration` never modifies employee or manager answer fields. A calibration-enabled cycle requires an explicit decision for every included participant's latest revision. Reopen preserves revision history, prior answers, calibration, acknowledgement and KPI evidence; it creates the next response revision and clears only the reopened participant's downstream values. Exclusion and restoration are allowed only before self review and require a reason. KPI targets are editable only in goal setting and reset the affected goal approval; actuals require the applicable open employee/manager review stage and never calculate a rating.

Automatic deadline advancement and `retryPerformanceException` invoke the same idempotent transition operation used by `advancePerformanceCycle`; one cycle advances at most once per worker run.

## Existing review operation extensions

`PerformanceReviewSummary` adds `responseRevision: Int!`, taken from the locked/current participant revision. Existing `submitSelfAppraisal`, `submitManagerAppraisal` and `acknowledgePerformanceReview` accept an additional `expectedRevision: Int` argument. The new UI always sends the loaded revision. Under the shared cycle/participant locks, a mismatched revision is a conflict; omission is accepted only for initial revision 1, never for reopened revisions. This preserves initial-cycle callers while preventing legacy/stale clients from silently writing a later revision.

The UI hydrates editable saved answers for a newly selected participant/revision using the correct employee/manager fields. A background reload must not erase unsaved edits. Reopening to manager review retains submitted self answers; reopening to self review clears downstream manager completion in the new revision. Reject reopening before the chosen submission has ever completed.
