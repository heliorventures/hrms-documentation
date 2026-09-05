# Admin Password Provisioning Design

## Goal

Admins can create employee login accounts without email, set or reset temporary passwords, and require users to change those temporary passwords at next login.

## Decisions

- Username is the tenant-scoped login identity.
- Email remains optional contact metadata.
- Add Employee can create an employee-only record or create employee plus login account together.
- Existing employee rows can be provisioned with a login account later.
- Linked employee users can have their password reset by an admin without knowing the old password.
- Admin-set initial and reset passwords are temporary and set `must_change_password = true`.
- User self-service password change requires current password, clears `must_change_password`, and revokes sessions.
- Admin provisioning/reset requires tenant RBAC admin authority (`role:manage` or HR/TENANT/ORG admin role), not plain employee edit access.
- Password hashing remains Argon2 and runs outside the async reactor.

## Backend Design

- Add `user.must_change_password BOOLEAN NOT NULL DEFAULT false` via a new tenant Liquibase migration.
- Add the field to the SeaORM tenant `user` entity.
- Extend client auth token output and client JWT claims with `must_change_password`.
- On client login and refresh, include the current `user.must_change_password` value.
- On self-service change password, update the password hash, set `must_change_password = false`, and delete all sessions for that user.
- Add employee GraphQL account-management inputs:
  - `EmployeeLoginAccountInput { username, email, initialPassword, roleIds }`
  - `ProvisionEmployeeLoginInput { employeeId, username, email, initialPassword, roleIds }`
  - `ResetEmployeePasswordInput { employeeId, newPassword }`
- Extend `CreateEmployeeInput` with optional `loginAccount`.
- Create employee plus user in one transaction when `loginAccount` is supplied.
- Assign supplied roles to the new user in the same transaction.
- Add `provisionEmployeeLogin(input)` for employees without a linked user.
- Add `resetEmployeePassword(input)` for linked users; reset revokes sessions and sets `must_change_password = true`.

## Frontend Design

- Add Employee modal includes a `Create login account` checkbox, enabled by default.
- When checked, username, initial password, confirm password, and optional role selection appear. Email is optional.
- Edit Employee modal shows linked username/email.
- Edit Employee modal includes:
  - `Provision login` when no `userId` exists.
  - `Reset password` when `userId` exists.
- Login/session parsing reads `must_change_password`.
- Route guard forces users with `must_change_password` to `/profile/settings?tab=security`.
- Security tab shows the password-change form and, when forced, explains the password must be changed before using the app.

## Validation

- UI and backend both require passwords to be at least 8 characters to match the existing self-service policy.
- Backend rejects blank usernames and normalizes usernames to lowercase.
- Backend rejects duplicate tenant usernames through validation plus the existing tenant unique constraint.
- Backend rejects provision-login for an employee that already has a linked user.
- Backend rejects admin reset for an employee without a linked user.

## Verification Constraints

- Unit tests are not run by Codex per project instruction.
- Static checks, codegen, and build/check commands may be used if they are not unit tests.
