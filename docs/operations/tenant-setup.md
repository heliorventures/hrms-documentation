# New tenant setup runbook

Use this runbook to create any new HRMS tenant. Developers should run scripts with inputs; do not copy SQL into a database console for normal tenant onboarding.

## What the setup script does

The setup script:

1. Creates or updates the tenant record.
2. Creates the tenant database mapping.
3. Creates the tenant schema.
4. Runs tenant Liquibase migrations.
5. Creates the first admin login users.
6. Assigns `TENANT_ADMIN` and `HR_ADMIN`.
7. Creates the core admin permissions and data scopes needed for Employee, RBAC, profile review, and org-chart visibility.

It does not load demo data.

## Inputs required

| Input | Example | Notes |
| --- | --- | --- |
| Tenant name | `Solvian Consultancy` | Display name. |
| Tenant code | `solvianconsultancy` | Lowercase DNS-safe code. This becomes the subdomain. |
| Admin usernames | `aniket.dobhada`, `ritesh.jain` | Login usernames for first tenant admins. |
| Temporary password | `ChangeMe!123` | Bootstrap only. Admins must change it after first login. |
| Runtime DB host | `postgres` | Use `postgres` for the VPS Docker Compose database service. |

Tenant URL format:

```text
https://<tenant-code>.heliorsoft.com
```

For the example above:

```text
https://solvianconsultancy.heliorsoft.com
```

Do not use `www.<tenant-code>.heliorsoft.com` unless TLS is explicitly configured for that nested hostname.

## One-time machine setup

Open PowerShell:

```powershell
Set-Location D:\work\heliorventures\hrms-database
npm install
```

Confirm `hrms-database\.env` has production PostgreSQL connection values:

```text
POSTGRES_HOST=<database host reachable from your machine>
POSTGRES_PORT=<database port>
POSTGRES_DB=<database name>
POSTGRES_USER=<database user>
POSTGRES_PASSWORD=<database password>
POSTGRES_SSLMODE=require
```

Only keep `POSTGRES_SSLMODE=require` when the database provider requires SSL.

## Create a tenant

Example for Solvian Consultancy:

```powershell
Set-Location D:\work\heliorventures\hrms-database

.\scripts\setup-tenant.ps1 `
  -Name "Solvian Consultancy" `
  -Code solvianconsultancy `
  -AdminUsernames @("aniket.dobhada", "ritesh.jain") `
  -TemporaryPassword "ChangeMe!123" `
  -RuntimePostgresHost postgres
```

For a different tenant, change only the input values:

```powershell
Set-Location D:\work\heliorventures\hrms-database

.\scripts\setup-tenant.ps1 `
  -Name "<Tenant Display Name>" `
  -Code "<tenant-code>" `
  -AdminUsernames @("<admin-user-1>", "<admin-user-2>") `
  -TemporaryPassword "ChangeMe!123" `
  -RuntimePostgresHost postgres
```

If you do not want to use `hrms-database\.env`, pass DB connection inputs directly:

```powershell
Set-Location D:\work\heliorventures\hrms-database

.\scripts\setup-tenant.ps1 `
  -Name "<Tenant Display Name>" `
  -Code "<tenant-code>" `
  -AdminUsernames @("<admin-user-1>", "<admin-user-2>") `
  -TemporaryPassword "ChangeMe!123" `
  -PostgresHost "<database-host>" `
  -PostgresPort <database-port> `
  -DbName "<database-name>" `
  -DbUser "<database-user>" `
  -DbPassword "<database-password>" `
  -PostgresSsl `
  -RuntimePostgresHost postgres `
  -RuntimeDbName "<runtime-database-name>"
```

## Add admins to an existing tenant

If the tenant already exists and only admin users need to be added:

```powershell
Set-Location D:\work\heliorventures\hrms-database

.\scripts\bootstrap-tenant-admins.ps1 `
  -TenantCode "<tenant-code>" `
  -AdminUsernames @("<admin-user-1>", "<admin-user-2>") `
  -TemporaryPassword "ChangeMe!123"
```

The admin bootstrap script is safe to re-run:

- Existing admin users are activated but their passwords are not reset.
- Missing admin users are created with `must_change_password = true`.
- Missing roles, permissions, role links, and data scopes are created.

## DNS and SSL

Create DNS for:

```text
<tenant-code>.heliorsoft.com
```

It should point to the same target as existing tenant subdomains.

The current Caddy template supports single-level tenant subdomains under `heliorsoft.com`. Example:

```text
solvianconsultancy.heliorsoft.com
```

Avoid:

```text
www.solvianconsultancy.heliorsoft.com
```

That nested hostname is not covered by the existing wildcard certificate.

## Deploy application changes if needed

Tenant setup is a database operation. Rebuild and deploy Docker images only when code changed and the VPS does not already have the latest release.

From `hrms-documentation`:

```powershell
Set-Location D:\work\heliorventures\hrms-documentation

$Tag = "helior-$(Get-Date -Format yyyyMMdd-HHmm)"

.\scripts\build-save-upload-images.ps1 `
  -Tag $Tag `
  -VpsHost 159.198.70.19 `
  -VpsUser deploy `
  -PublicBaseUrl https://heliorsoft.com `
  -ApiBaseUrl https://api.heliorsoft.com `
  -TenantId "<tenant-id-printed-by-setup-script>" `
  -DeployAfterUpload
```

If images are already uploaded and only deployment needs to run:

```powershell
Set-Location D:\work\heliorventures\hrms-documentation

.\scripts\deploy-on-vps.ps1 `
  -Tag "<existing-image-tag>" `
  -VpsHost 159.198.70.19 `
  -VpsUser deploy `
  -PublicBaseUrl https://heliorsoft.com `
  -ApiBaseUrl https://api.heliorsoft.com `
  -TenantId "<tenant-id-printed-by-setup-script>" `
  -SyncCompose `
  -SyncCaddyfile `
  -LoadImages `
  -Up `
  -Validate
```

Do not use `-SyncEnvExample` unless you intentionally want to reconcile `/opt/apps/.env` from the template.

## First-login validation

Open:

```text
https://<tenant-code>.heliorsoft.com
```

Login with each bootstrap admin username and the temporary password.

Validate:

- The user can change the temporary password.
- Employee directory opens.
- Org chart opens.
- Admin/RBAC page opens.
- Profile review queue opens.

## Production security checklist

- Temporary password was shared out-of-band.
- Each bootstrap admin changed the temporary password.
- `KABIPAY_PROFILE_CHANGE_ENCRYPTION_KEY` exists in `/opt/apps/.env`.
- No demo data was loaded.
- DNS points only to the intended production VPS/load balancer.
