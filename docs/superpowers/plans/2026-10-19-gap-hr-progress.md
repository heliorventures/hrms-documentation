# Gap closure A: source HR administration

Owner: Task A; source contracts below are implementation inputs, not production deployment evidence.

## Typed wire contract

All operations require `OrganizationGrant`, exact canonical capability, and `employee_scope=ALL`. Employee authority is `employee:manage`; accounts use separate `role:manage`; workflows use separate `workflow:manage`. Unknown payload fields fail deserialization. Identifiers and expected resource version are command envelope fields, never payload overrides.

| Operation | Service | Resource | Payload | Result |
| --- | --- | --- | --- | --- |
| EmployeeDetail | kabipay-employee | employee | `{}` | employee record below |
| EmployeeCreate | kabipay-employee | employee, future UUID, expected 1 | `{employee_code,first_name,last_name,date_of_joining,department_id?,designation_id?,employment_type?}` | employee record |
| EmployeeUpdate | kabipay-employee | employee | `{first_name?,last_name?,department_id?,designation_id?,employment_type?}` | employee record |
| EmployeeEmployment | kabipay-employee | employee | `{status}` | employee record |
| AccountList | kabipay-employee | company_accounts, membership UUID/version | `{after?,first:1..100}` | `{accounts:[{user_id,username,email,is_active,version,role_ids}],available_roles:[{role_id,name}],after,has_more}` |
| AccountCreate | kabipay-employee | user, future UUID, expected 1 | `{username,email?,initial_password,role_ids:[UUID]}` | account record below |
| AccountUpdate | kabipay-employee | user | `{username?,email?}` | account record |
| AccountAccess | kabipay-employee | user | `{is_active:boolean}` | account record |
| AccountRoles | kabipay-employee | user | `{role_ids:[UUID]}` | account record |
| WorkflowList | kabipay-workflow | company_workflows, membership UUID/version | `{after?,first:1..100}` | `{workflows:[{workflow_id,name,entity_type,is_active,version}],after,has_more}` |
| WorkflowDetail | kabipay-workflow | workflow_definition | `{}` | workflow record below |
| WorkflowSave | kabipay-workflow | workflow_definition, existing or future UUID | `{name,entity_type,is_active,steps:[{step_name,approver_type,can_skip,sla_hours?}]}` | workflow record |
| WorkflowActivation | kabipay-workflow | workflow_definition | `{is_active:boolean}` | workflow record |
| SeparationList | kabipay-employee | company_separations, membership UUID/version | `{after?,first:1..100}` | `{separations:[{separation_id,employee_id,separation_type,last_working_date,status,version}],after,has_more}` |
| SeparationDetail | kabipay-employee | separation | `{}` | separation record below |
| SeparationCreate | kabipay-employee | separation, future UUID expected 1 | `{employee_id,separation_type,resignation_date?,last_working_date,reason?}` | separation record |
| SeparationReject | kabipay-employee | separation | `{}` | separation record |
| SeparationCancelApproval | kabipay-employee | separation | `{}` | separation record |
| ClearanceUpdate | kabipay-employee | clearance_checklist | `{is_cleared:boolean}` | `{clearance_id,separation_id,is_cleared,cleared_at,cleared_by_principal_id}` |

Employee record: `{employee_id,employee_code,first_name,last_name,date_of_joining,department_id,designation_id,employment_type,status}`. Account record: `{user_id,username,email,is_active,role_ids}`. Workflow record: `{workflow_id,name,entity_type,is_active,steps:[{step_id,sequence_order,step_name,approver_type,approver_permission,can_skip,sla_hours}]}`. Actual resulting version comes from the common command outcome envelope.

All separation and clearance operations require separate `onboarding:manage=ALL` company authority. Separation record: `{separation_id,employee_id,separation_type,resignation_date,last_working_date,reason,status,approved_by,approved_by_principal_id,offboarded_at,clearance:[{clearance_id,department,task_name,is_cleared,cleared_at,cleared_by,cleared_by_principal_id,version}],approval_operation?:{operation_id,state}}`.

## Source constraints

- Employee create/update reuse `employee_service`, with a transaction-owned update core and explicit source resource UUID for create. Employee employment status uses the existing canonical status validator and linked account synchronization. Employee operations cannot relink users, provision login, alter bank/tax/private profile fields, or override organization-owned reporting relationships.
- Accounts reuse active tenant role validation, account normalization/password hashing/unique checks and role replacement/session revocation. Plaintext password is input only, never returned or placed in history/topic facts. Account access cannot reactivate login blocked by employment eligibility. Last administrator and self administrator removal guards apply to account authority transitions; the local roles resolver also passes its real source actor.
- Workflow save uses the existing entity/approver/permission validation and step service in one receipt transaction. A workflow with runtime history cannot be replaced. Existing request type cannot change; activation serializes the request type and rejects a competing active definition or an empty workflow. Foreign principals retain original principal attribution, without fabricated local accounts/claims.
- Source migration `0118_organization_hr_administration` adds private user/workflow-definition versions and dependent role/step triggers. It preserves existing resource versions/receipts during rollback and exports no credential rows.
- Separation initiation validates employment and dates in the source transaction; rejection only resolves a pending request and calls the existing registered-operation cancellation/outbox service. Cancellation cannot undo a committed exit. Clearance shares a source transaction core between real local-user and logical-principal callers. The migration adds principal FKs and rejects rollback if principal attribution exists. Finance-approved exit approval, artifact preparation and FNF finalization retain their independent Finance authorization; the HR adapter provides no approval substitute.
- Self administration checks use the fresh central policy's verified target-company login links (`actor_target_user_ids`) under the actual target record lock. This boolean identity proof never becomes local-user attribution. Last administrator checks exclude deleted/inactive/password-change-pending accounts and ambiguous or ineligible employment links. Existing local role-permission/scope editors share the account-admin lock and preserve effective administrator access.

## Evidence ledger

- Initial DTO contract tests executed before adapter behavior: `cargo test -p kabipay-employee --lib organization_admin --offline`: 3 passed, 0 failed. This proves typed payload field constraints only.
- Current adapter/domain library validation executed: `cargo test -p kabipay-employee -p kabipay-workflow --lib --offline`: Employee 94 passed, 0 failed, 2 existing S3 environment tests ignored; Workflow 5 passed, 0 failed. This includes company grant/capability/scope constraints, protected payload fields, self administrator restriction, existing role lifecycle/session rollback regressions, and workflow entity/approver/permission constraints. The workflow invalid-save test invokes the actual transaction core against a proxy that panics on business database access. Existing Leave dead-code and proc-macro future compatibility warnings remain outside this change.
- Source migration XML parsed successfully with PowerShell `[xml]`; scoped `git diff --check` returned exit 0. These prove document syntax and whitespace only.
- Reusable HTTP acceptance driver `hrms-svc/scripts/test-organization-hr-administration.cjs` exports `runHrAdministrationAcceptance(ctx)` for the root-owned disposable fixture; `node --check` passed. It requires separate origin/target companies, an explicitly supplied fixture DB, actual verified target login links, initial effective local admin roles, workflow execution history and an admin-grant revocation callback. It covers live source adapters for employee/account/workflow/exit/clearance, replay/version conflicts, role tenant restrictions, last/self administrator safety, logical attribution and revocation. Its runtime remains unexecuted until root supplies the fixture processes and identities.
- Source SQL rehearsal, actual separate-database HTTP administration/revocation, production binary all-target checks and final independent review: pending root integration.
- Production migration/deployment and existing-company mutation: not executed.
