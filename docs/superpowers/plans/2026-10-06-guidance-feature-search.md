# Guidance and Feature Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The user selects the method before execution.

**Goal:** Cover every accessible tenant page/tab/action with accurate tours and page help, real screenshots, and searchable authorized features.

**Architecture:** Extend the current tours, Page Information drawer, and command palette through colocated typed feature/help definitions. Generate a focused AST inventory and link its routes/tabs/actions to tours, instructions, screenshots, and access rules. Navigation and help share feature metadata so search reaches the same authorized destination described by guidance.

**Tech Stack:** React 18/TypeScript, existing TypeScript compiler API, Vitest/testing-library, current in-app browser and screenshot workflow.

**Spec:** [Approved design, Workstream 4](../specs/2026-10-06-claims-locations-and-guidance-design.md).

## Global Constraints

- Update every accessible tenant page tour against current UI, including the new reports, locations, assignments, weekly offs, and required files.
- Keep explanatory tours free of business mutations.
- Dirty forms must not be discarded by guidance navigation.
- Render only instructions the user can access.
- No generated or fabricated screenshot is presented as a verified application view.
- Feature results navigate to the correct visible tab and optionally focus a stable action anchor; they do not execute the action.
- `rtk` commands; no automatic commits; user-owned validation; preserve current employee-directory/tour edits. See [shared constraints](2026-10-06-claims-locations-and-guidance.md).

## Review Focus

1. User can reach a page but cannot use its HR tab/action: no hidden feature result, help, or tour step; Tasks 1/2 pin feature-level filtering.
2. Tab uses delayed rendering or a data-dependent empty state: navigation waits for a real anchor and shows a useful fallback; Task 2 checks both.
3. User has an unsaved form: tour/search navigation follows the existing leave-page guard; Tasks 2/4 prevent silent discard.
4. Screenshot no longer matches the control or includes employee information: delivery requires manifest review and synthetic captures; Task 5 rejects unverified/unsafe assets.
5. Keyboard or mobile user opens long instructions/images: numbering, focus return, scrolling and accessible enlargement work; Task 3 tests drawer/image behavior.

## Task 1: Derive current coverage and define shared feature metadata

**Files:** Create `hrms-ui/scripts/build-guidance-inventory.mjs`, `src/guidance/{featureTypes.ts,featureRegistry.ts,featureAccess.ts,featureAccess.test.ts,guidanceFeatureCoverage.test.ts}`, and `docs/guidance/coverage.json`; modify existing `tourCoverage.test.ts` only to consume shared route coverage. Read `src/routes/appRouteConfig.tsx`, page-owner imports, `src/navigation/navigationModel.ts`, and existing colocated tour definitions through AST-selected declarations.

**Interfaces:**
- `FeatureDefinition = { id: string; routePath: string; pageTitle: string; label: string; tabId?: string; path: string; anchor?: string; keywords: readonly string[]; access: FeatureAccess; tourStepIds: readonly string[]; helpTaskIds: readonly string[] }`.
- `FeatureAccess = { capability?: Capability; permission?: PermissionCode; scopes?: readonly ExplicitPermissionScope[]; requiresEmployeeProfile?: boolean }`; all specified predicates must pass, in addition to current route/module authorization. General features rely on route access; write actions require exact capability or permission/scope from the owning page.
- `accessibleFeatures(features: readonly FeatureDefinition[], context: FeatureAccessContext): FeatureDefinition[]`, with context containing current `canAccessPath`, permission service, employee-profile availability, and allowed tab IDs per page.
- Inventory output schema version 1 contains route identity/title/source path, declared tab IDs, stable anchors and action references, source declaration locations, and coverage IDs. Record dynamic definitions requiring focused manual review with explicit source locations; never assume an AST-discovered string proves an action works. Exclude operator routes and redirects; record disabled placeholder controls as non-operational with an explanation.

- [ ] Add `each_accessible_route_tab_and_action_has_guidance_mapping`, `feature_access_requires_exact_capability_and_visible_tab`, and `module_revocation_removes_feature_help`. Assert every operational inventory item has an owner, a relevant tour step, and a help task; no unknown/duplicate IDs or dead route/tab targets. Pin restricted approver, employee, and ALL-admin contexts without hardcoding role names as authorization.
- [ ] Obtain failing output from `rtk npm test -- src/guidance/featureAccess.test.ts src/guidance/guidanceFeatureCoverage.test.ts`.
- [ ] Implement inventory generation with the installed TypeScript compiler API. Follow only registered route owners and their tab/action declarations; output metadata instead of dumping repository source. Run the read-only-source inventory generator with `rtk proxy node scripts/build-guidance-inventory.mjs` to write its review artifact. Manually reconcile dynamic/data-driven controls into typed feature definitions before treating coverage as complete.
- [ ] Implement the registry as an index of per-owner exports. Reuse centralized permission/module checks and normal route IDs; avoid a second hardcoded route table. Obtain passing coverage/access output and inspect the inventory diff for newly missing features when UI changes are incorporated.

## Task 2: Update tours across all routes and tabs

**Files:** Modify `src/guidance/{tourTypes.ts,tourRegistry.ts,TourDialog.tsx,useTourController.ts}` and `src/components/layout/PageTools.tsx`; create `src/guidance/{tourNavigation.ts,tourNavigation.test.tsx}`. Update every registered definition in `src/appearance/guidance/AppearanceTour.ts` and `src/modules/*/guidance/*Tour.ts`, preserving unrelated edits. Create per-owner `guidance/features.ts` files and register the new company-locations tour from Plan 3.

**Interfaces:** Extend `TourStep` with optional `destination: { path: string; tabId?: string; anchor?: string }` and `featureId?: string`. `resolveTourDestination(step: TourStep, context: FeatureAccessContext): string | null` returns only an accessible local application URL. `navigateTourStep(...)` selects normal navigation/tab state, waits for the anchor through the existing layout/anchor mechanisms, and returns `{ status: 'ready' | 'missing' | 'blocked' }`. It never invokes button actions or form submissions.

- [ ] Add `tour_reaches_permitted_tab_then_anchor`, `tour_skips_revoked_feature`, `late_anchor_is_resolved`, `empty_state_has_explanatory_fallback`, and `dirty_form_blocks_tour_navigation`. Spy on all submit/upload/approve/save handlers and assert they remain uncalled throughout a tour, including cross-tab navigation.
- [ ] Obtain failing output from `rtk npm test -- src/guidance/tourNavigation.test.tsx src/guidance`.
- [ ] Implement guarded destination selection and active-tab re-evaluation without changing current first-login/dismissal persistence semantics. Keep persistent anchors for tab selectors, use visible tab/action anchors for task steps, and provide explanatory fallback text for unrendered optional/data-dependent controls. Do not advance a step as if it highlighted a nonexistent control.
- [ ] Reconcile all definitions through the Task 1 coverage matrix: personal/dashboard/my-work/profile; people/documents/profile review and every employee-profile tab; attendance/timesheets/leave including comp-off and calendars; expense/travel including evidence, approval/payment, categories/policies/reports; payroll/tax/compensation; hiring/onboarding/prejoining; performance/assets/talent/learning/surveys/succession/benefits/grievance; notifications/workflows/access/settings/module health/appearance. Each route owner's feature export names actual tabs/actions from its source, not assumed generic CRUD.
- [ ] Obtain passing existing/new tour and coverage tests. Browser-check employee and HR/admin contexts, tab navigation, closed dialogs, missing data, permission revocation, mobile geometry and replay. No business action may be triggered during acceptance.

## Task 3: Reusable detailed page help and owner content

**Files:** Create `src/guidance/help/{helpTypes.ts,helpRegistry.ts,PageHelpContent.tsx,HelpTask.tsx,HelpScreenshot.tsx,PageHelpContent.test.tsx,HelpScreenshot.test.tsx}`; mount authorized reference content through `src/components/layout/PageTools.tsx` and existing `PageInformation`; modify the drawer provider only if needed for readable overflow/width. Create `help/{tasks.ts,screenshots.ts}` under each owning module; `src/appearance/help/` owns appearance instructions.

**Interfaces:** `HelpTaskDefinition = { id: string; featureId: string; title: string; prerequisites: readonly string[]; steps: readonly { id: string; text: string; screenshotId?: string }[]; requiredFields: readonly string[]; afterSave: string; checkStatus: string; recovery: readonly string[] }`. `PageHelpContent` selects current route/tab help using Task 1's authorized feature registry. It renders semantic ordered lists, accessible screenshots, and optional navigation to another allowed tab's help. Content is plain typed text/metadata; never unrestricted HTML.

- [ ] Add `page_help_filters_hidden_features`, `how_to_has_numbered_steps_and_outcome`, `long_help_remains_scrollable`, and `screenshot_enlargement_returns_focus`. Assert changing route/identity dismisses stale content; requesting a hidden help ID shows no private task content. Missing/unverified screenshots have explicit internal coverage failures, not fabricated user images.
- [ ] Obtain failing output from `rtk npm test -- src/guidance/help src/components/common/PageInformation.test.tsx src/components/layout/PageTools.test.tsx`.
- [ ] Implement the reusable help renderer with existing drawer/modal/focus infrastructure. Keep action-critical validation beside forms and avoid duplicate legacy reference blocks by integrating or replacing each owner's prior content deliberately. Lazy-load screenshot assets; provide readable captions, alt text, responsive width, and keyboard-accessible enlargement.
- [ ] Author exact field/control instructions for leave/expense/travel employee requests and all HR/admin expense-category/policy, leave-type/policy/balance, holiday, workflow, company-location and weekly-off tabs first. Include required file types/size, selected Saturday preview, effective-date behavior, and approval/payment results from the new contracts. Validate instructions against field labels and server rules.
- [ ] Add the remaining owner help modules for every operational Task 1 inventory action. Record prerequisites, exact sequence, expected outcome, where to confirm it, and recoverable error cases. Split large content by owner/feature instead of a monolithic component. Obtain passing help/coverage tests and review actual rendered employee/admin drawers before claiming all-page coverage.

## Task 4: Feature search through authorized destinations

**Files:** Create `src/navigation/{featureSearch.ts,featureSearch.test.ts,featureNavigation.ts,featureNavigation.test.tsx}`; modify `navigationSelectors.ts`, `useAccessibleNavigation.ts`, and `src/components/layout/CommandPalette.tsx` with its tests. Consume Task 1's feature registry rather than duplicating its metadata.

**Interfaces:** `searchFeatures(features: readonly FeatureDefinition[], query: string): readonly FeatureDefinition[]` operates on already-authorized features. `SearchResult = { id: string; kind: 'page' | 'feature'; label: string; pageTitle: string; path: string; tabId?: string; anchor?: string }`. `resolveSearchResults(pages, features, query): SearchResult[]` ranks normalized exact labels before prefix before all-word substring matches, then stable page/feature order, deduplicating the same feature identity. `navigateFeature(result, context)` rechecks current access, uses normal route/tab navigation and optional anchor focus, and performs no business mutation.

- [ ] Add `search_matches_page_tab_feature_and_synonym`, `search_excludes_inaccessible_admin_actions`, `search_rechecks_permission_before_navigation`, and `feature_navigation_runs_no_action`. Pin “claim expense,” “request leave,” “travel report,” “expense type,” “holiday,” “location,” and “weekly off” to actual authorized destinations. Preserve existing empty-query/current-page/arrow-key/Enter/Escape/focus tests and test dirty-form guard behavior.
- [ ] Obtain failing output from `rtk npm test -- src/navigation/featureSearch.test.ts src/navigation/featureNavigation.test.tsx src/components/layout/CommandPalette.test.tsx`.
- [ ] Normalize case/whitespace, add colloquial synonyms in owner metadata, and combine page/feature results with clear labels and page context. Keep current authorized page results and Ctrl/Cmd+K behavior. Navigate to permitted tab query parameters and wait/focus a declared anchor; choosing a “Submit” feature opens its page context, not its submission action.
- [ ] Clear old search results on tenant/module/permission change and reauthorize the selection just before navigation. Obtain passing focused tests and browser keyboard/mobile proof for employee, approver, and HR/admin accounts.

## Task 5: Real screenshots and final coverage reconciliation

**Files:** Create `hrms-ui/public/help/screenshots/` assets and `docs/guidance/screenshots.json`; populate owner `help/screenshots.ts` exports; add `src/guidance/help/screenshotCoverage.test.ts` and extend `docs/guidance/coverage.json` with verified capture references.

**Interfaces:** `HelpScreenshotDefinition = { id: string; featureId: string; src: string; alt: string; caption: string; routePath: string; tabId?: string; capturedAt: string; uiRevision: string; verified: boolean }`. Names are stable feature/step identifiers; manifest records the actual local code revision and relevant dirty-file content hash so captures are not falsely attributed to a clean commit.

- [ ] Add `every_referenced_screenshot_exists_and_is_verified`, `screenshot_metadata_matches_feature_destination`, and `help_capture_manifest_contains_no_storage_or_session_urls`. Assert every image reference resolves to a local asset; this test complements visual/content review and does not prove redaction by itself.
- [ ] After Plans 1–3 and owner help exist, use the browser skill and a synthetic demonstration tenant to open real views/dialogs. Capture focused, readable screens for each help sequence; use built-in browser capture capabilities. Inspect each image for current labels, relevant tabs, and absence of real employee/financial data, credentials, tokens and browser chrome. Capture without executing business actions during explanatory tour runs.
- [ ] Register captions/alt text and mark verified only after visual comparison to the implemented UI. If the demo app/session is unavailable, request the missing access and keep capture work pending; no fake or generated screenshot may close the task.
- [ ] Obtain passing screenshot/feature/tour/help coverage output, then browser-check drawer images on desktop/mobile and keyboard enlargement. Rebuild the AST inventory after all edits; reconcile every missing route/tab/action/help/screenshot mapping and review disabled/nonoperational exclusions explicitly.
- [ ] Supply final focused UI test commands, `rtk npm run lint`, and `rtk npm run build`; collect user outputs and browser/capture evidence. Mark overall work complete only when all approved operational features and walkthroughs have real verified coverage. No commit/deployment occurs automatically.
