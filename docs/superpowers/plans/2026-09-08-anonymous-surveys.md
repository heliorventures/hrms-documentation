# Anonymous Surveys Implementation Plan

## Goal

Add tenant-scoped surveys that admins can draft, publish, close, and report on; employees can submit once; and authorized HR, managers, or department viewers can read threshold-protected aggregate scores and comments without respondent identities.

## Work

1. Add migration 0076 for surveys, sections, questions/options, identity-bearing assignments, identity-free responses/answers, audience departments, RBAC, and forward-only retention.
2. Add a dedicated `kabipay-survey` GraphQL subgraph with exact permission-scope checks, transactional one-time submission, published-window validation, and aggregate-only result queries.
3. Register the subgraph in the workspace, gateway, container/deployment configuration, and gateway schema contract.
4. Add the Surveys workspace UI for admin authoring, employee completion, and aggregate reporting. Never render a respondent identity or expose raw response records.
5. Verify migration contracts, Rust tests/checks, gateway contracts, focused UI tests, and regression builds without deploying or applying tenant migrations.

## Security invariants

- Assignment rows containing employee IDs have no foreign key or API path to identity-free response rows.
- Result rows are grouped and suppressed below the configured threshold (minimum 3).
- `survey:results` applies exact `TEAM`, `DEPARTMENT`, or `ALL` scope; `survey:respond` applies exact `SELF` scope.
- Comments are returned only from a qualifying aggregate group and are never paired with timestamps or response IDs.
