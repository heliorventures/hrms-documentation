# Performance, Appraisal, and Survey Flow

## Performance and appraisal

1. An admin creates a performance process and chooses `MONTHLY`, `QUARTERLY`, `YEARLY`, or `MANUAL` cadence, rating range, and optional HR-calibration and employee-acknowledgement stages.
2. The admin creates a versioned appraisal template. A template contains ordered sections, top-level questions, one level of subquestions, single- or multiple-choice questions, text questions, and optional self/manager ratings. Published templates are immutable cycle snapshots.
3. After a published template exists, the admin activates the process. The background worker creates each due calendar period exactly once. Admins can also launch a cycle explicitly.
4. Launch snapshots every eligible employee's manager, department, designation, location, and template. A later reporting-line change does not silently transfer an in-progress appraisal.
5. During goal setting, employees propose weighted goals. The snapshotted manager approves them only when the goal weights total 100.
6. Managers can add dated, goal-linked feedback throughout the cycle. Employee-visible feedback is shown with the employee's goals and appraisal.
7. During self review, the employee answers the questions assigned to `EMPLOYEE` or `BOTH` and supplies configured self-ratings.
8. During manager review, the assigned manager sees the employee responses, goals, and feedback, answers manager questions, gives ratings, and submits the final rating/band.
9. If configured, HR calibration follows. If acknowledgement is configured, the employee acknowledges the result. The final stage closes the cycle.

Authorization is based on exact scoped permissions: `performance:manage` with `ALL`, `performance:evaluate` with `TEAM`, and `performance:self` with `SELF`. Runtime code does not infer access from role names.

## Surveys

1. An admin creates a draft survey with sections, scored areas (dimensions), rating/choice/text questions, an optional department audience, and a reporting threshold of at least three.
2. Publishing snapshots eligible employees into an assignment ledger. Each assigned employee can submit once while the survey is open.
3. Submission locks the assignment and writes the response transactionally. The identity-bearing assignment has no response reference; the response has no employee ID.
4. HR/admin (`ALL`), department viewers (`DEPARTMENT`), and managers (`TEAM`) see only aggregates inside their exact scope. There is no raw-response or per-user result API.
5. Results below the configured group threshold are fully suppressed. Question/area scores and option counts are also suppressed for undersized answer groups. Free-text comments appear only when at least the threshold number of comments exists in the authorized group.
