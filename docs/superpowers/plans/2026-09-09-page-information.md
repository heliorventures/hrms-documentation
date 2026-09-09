# Page information panel implementation plan

Approved design: move secondary reference information into one top-right information control and right-side drawer across application pages. Keep primary records, actions, errors, action warnings, and necessary form instructions visible.

Architecture: a shared provider in employee and operator layouts owns the drawer. PageInformation sections register their presence and portal their current content into the drawer, preserving page context and permissions. The shared header supplies the single trigger. PageHeader descriptions use the same section API. Route and authorization changes dismiss the drawer.

Constraints: preserve existing dirty work; no commits; no Dart or Flutter commands; no server/data changes.

- [x] Test and implement shared provider, trigger, section, and PageHeader integration. Verify hidden-by-default content, one trigger, live updates, cleanup, navigation, and keyboard dismissal/focus return.
- [x] Integrate employee/operator layouts. Move Leave holiday/type references, Attendance guidance/shifts, Timesheet guidance/policy, and identified secondary page/component notes. Use a single-column layout for drawer reference cards.
- [x] Review remaining page content; retain primary data and safety-critical/action-specific instructions. Document coverage and exceptions.
- [x] Run focused behavior tests, existing affected tests, TypeScript/build, changed-file lint, and diff checks. Inspect browser behavior if the local app/session is available; distinguish automated from live verification.

Execution: continue in the current checkout so the user can review alongside their existing work. No branch integration or deployment is authorized or needed.

Results: 85 tests passed, Vite production bundle passed, shared information/header ESLint passed with zero warnings, scoped diff check passed. Concurrent workflow TypeScript errors and legacy-page lint remain; no connected browser was available. See `hrms-ui/docs/page-information.md` for exact coverage and acceptance limits.
