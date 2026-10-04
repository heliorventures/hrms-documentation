# Performance UI handoff

## Implemented UI surface

- `hrms-ui/src/modules/workplace/performanceAdminQueries.ts`: reviewed administration, policy, private-feedback and KPI documents/types.
- `hrms-ui/src/modules/workplace/performance-admin/PerformanceAdministrationPanel.tsx` and `PerformanceAdministrationParticipant.tsx`: manage-only cycles, stable participant pages, deadlines, exception retry, exclusion/reinclude, calibration, revision readout, reopen warning/reason, and private HR feedback.
- `performance-admin/PerformanceProgramPolicyEditor.tsx`: single population mode, persisted selection across search/pages, deadline offsets, archive reason/confirmation.
- `performance-admin/PerformanceGoalKpis.tsx`: role/stage guarded target CRUD and actual/evidence submission. Uses the existing per-participant goal-action serialization.
- `performanceLifecycleQueries.ts`, `usePerformanceReviewActions.ts`, `usePerformanceReviewData.ts`, and `usePerformanceReviewDrafts.ts`: public `responseRevision`, expected-revision submissions, and revision-aware draft hydration that preserves background edits.

## Tests authored, not run

- `usePerformanceReviewDrafts.test.ts` covers reopened-answer hydration and draft retention during unchanged refreshes.
- Existing access/appraisal/concurrency fixtures now cover `responseRevision`; access coverage asserts personal flows do not request private feedback.
- `PerformancePage.access.test.tsx` covers an unauthorized administration URL without an administration query.
- `performance-admin/PerformanceGoalKpis.test.tsx` covers clearing a KPI target draft when the participant identity changes.

## Required user-run checks

```powershell
rtk npm run lint
rtk npm run test -- src/modules/workplace/usePerformanceReviewDrafts.test.ts src/modules/workplace/PerformancePage.access.test.tsx src/modules/workplace/PerformancePage.appraisal.test.tsx src/modules/workplace/PerformancePage.goalConcurrency.test.tsx
rtk npm run build
```

## Limitations

- No lint, tests, typecheck, build, browser, authenticated GraphQL, migration, or deployment validation was run.
- The backend owner must complete the reviewed administration resolvers before the new manage-only flows can be accepted end-to-end.
- Administration loaders and policy editing are split into focused files. This was source-inspected only; no automated validation was run.
