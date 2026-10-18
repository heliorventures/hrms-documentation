const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { test } = require('node:test');

const root = path.resolve(__dirname, '../..');
const deploy = fs.readFileSync(path.join(root, 'scripts/deploy-on-vps.ps1'), 'utf8');
// Exercise the actual payload selected by the deployment entry point.
assert.match(deploy, /^\s*\$EnvReconcileScriptContent = Get-Content -LiteralPath .*deploy\/reconcile-env\.sh'\) -Raw\r?$/m);
const script = fs.readFileSync(path.join(root, 'scripts/deploy/reconcile-env.sh'), 'utf8');
const valid = [
  'POSTGRES_HOST=postgres', 'POSTGRES_PORT=5432', 'POSTGRES_DB=demo',
  'POSTGRES_USER=demo', 'POSTGRES_PASSWORD=existing-db-password',
  'KABIPAY_JWT_SECRET=existing-jwt-secret-with-at-least-32-bytes',
  'KABIPAY_PROFILE_CHANGE_ENCRYPTION_KEY=existing-encryption-key',
  'KABIPAY_FINANCE_SERVICE_SECRET=independent-finance-secret-with-32-bytes',
  'KABIPAY_FINANCE_EMPLOYEE_URL=http://127.0.0.1:4013',
  'KABIPAY_FINANCE_PAYROLL_URL=http://127.0.0.1:4016',
].join('\n') + '\n';
const example = valid.replaceAll('existing-', 'example-') + 'NEW_SETTING=enabled\n';

function run(body) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'kabipay-env-test-'));
  try {
    fs.writeFileSync(path.join(dir, 'reconcile.sh'), script.replace(/\r\n/g, '\n'));
    fs.writeFileSync(path.join(dir, 'fixture.env'), valid);
    fs.writeFileSync(path.join(dir, 'fixture.example'), example);
    const result = spawnSync('docker', ['run', '--rm', '-i', '--network', 'none',
      '--mount', `type=bind,source=${dir},target=/fixtures,readonly`,
      'postgres:16', 'bash', '-s'], {
      input: `set -euo pipefail\nmkdir /tmp/app\ncd /tmp/app\ncp /fixtures/fixture.env .env\ncp /fixtures/fixture.example .env.example\n${body}\n`,
      encoding: 'utf8', timeout: 60000,
    });
    assert.ifError(result.error);
    assert.equal(result.status, 0, result.stdout + result.stderr);
  } finally {
    const resolvedDir = fs.realpathSync(dir);
    assert.equal(path.dirname(resolvedDir), fs.realpathSync(os.tmpdir()), 'Cleanup must stay in the test temporary directory');
    assert.match(path.basename(resolvedDir), /^kabipay-env-test-/);
    fs.rmSync(resolvedDir, { recursive: true, force: true });
  }
}

test('reconciliation preserves existing credentials and configuration, adding only missing defaults', () => run(`
bash /fixtures/reconcile.sh /tmp/app release-002 >/tmp/output
grep -qx 'POSTGRES_PASSWORD=existing-db-password' .env
grep -qx 'KABIPAY_JWT_SECRET=existing-jwt-secret-with-at-least-32-bytes' .env
grep -qx 'KABIPAY_PROFILE_CHANGE_ENCRYPTION_KEY=existing-encryption-key' .env
grep -qx 'NEW_SETTING=enabled' .env
grep -qx 'KABIPAY_IMAGE_TAG=release-002' .env
! grep -q 'existing-db-password\\|existing-jwt-secret' /tmp/output
test "$(stat -c %a .env)" = 600
`));

test('missing Finance secret is generated once and is independent of JWT', () => run(`
sed -i '/^KABIPAY_FINANCE_SERVICE_SECRET=/d' .env
sed -i 's/^KABIPAY_FINANCE_SERVICE_SECRET=.*/KABIPAY_FINANCE_SERVICE_SECRET=/' .env.example
bash /fixtures/reconcile.sh /tmp/app release-002 >/tmp/output
secret="$(sed -n 's/^KABIPAY_FINANCE_SERVICE_SECRET=//p' .env)"
test "$(printf %s "$secret" | wc -c)" = 64
[[ "$secret" =~ ^[0-9a-f]+$ ]]
bash /fixtures/reconcile.sh /tmp/app release-003 >/dev/null
test "$secret" = "$(sed -n 's/^KABIPAY_FINANCE_SERVICE_SECRET=//p' .env)"
! grep -q "$secret" /tmp/output
`));

test('invalid existing Finance configuration fails before changing the environment', () => run(`
sed -i 's/^KABIPAY_FINANCE_SERVICE_SECRET=.*/KABIPAY_FINANCE_SERVICE_SECRET=too-short/' .env
cp .env /tmp/before
if bash /fixtures/reconcile.sh /tmp/app release-002 >/tmp/output 2>&1; then exit 41; fi
cmp /tmp/before .env
grep -q 'KABIPAY_FINANCE_SERVICE_SECRET' /tmp/output
! grep -q 'too-short' /tmp/output
`));

test('Finance secret cannot reuse browser JWT signing key', () => run(`
sed -i 's/^KABIPAY_FINANCE_SERVICE_SECRET=.*/KABIPAY_FINANCE_SERVICE_SECRET=existing-jwt-secret-with-at-least-32-bytes/' .env
if bash /fixtures/reconcile.sh /tmp/app release-002 --check-only >/tmp/output 2>&1; then exit 42; fi
grep -q 'independent' /tmp/output
`));

test('private service URLs reject credentials, paths, queries and invalid ports', () => run(`
for url in 'http://user:password@example.test' 'http://example.test/private' 'http://example.test?token=x' 'http://example.test:99999' 'http://[:::]:4013' 'http://999.999.999.999:4013' 'http://example.123' 'http://example.0xff'; do
  cp /fixtures/fixture.env .env
  sed -i "s|^KABIPAY_FINANCE_EMPLOYEE_URL=.*|KABIPAY_FINANCE_EMPLOYEE_URL=$url|" .env
  if bash /fixtures/reconcile.sh /tmp/app release-002 --check-only >/tmp/output 2>&1; then exit 43; fi
  grep -q 'KABIPAY_FINANCE_EMPLOYEE_URL' /tmp/output
done
`));

test('preflight accepts compressed and full IPv6 service origins', () => run(`
for url in 'http://[::1]:4013' 'https://[2001:db8::1]' 'http://[2001:db8:1:2:3:4:5:6]:4013'; do
  cp /fixtures/fixture.env .env
  sed -i "s|^KABIPAY_FINANCE_EMPLOYEE_URL=.*|KABIPAY_FINANCE_EMPLOYEE_URL=$url|" .env
  bash /fixtures/reconcile.sh /tmp/app release-002 --check-only >/dev/null
done
`));

test('preflight validates without changing valid configuration or provisioning missing secrets', () => run(`
cp .env /tmp/before
bash /fixtures/reconcile.sh /tmp/app release-002 --check-only >/dev/null
cmp /tmp/before .env
sed -i '/^KABIPAY_FINANCE_SERVICE_SECRET=/d' .env
cp .env /tmp/before
if bash /fixtures/reconcile.sh /tmp/app release-002 --check-only >/dev/null 2>&1; then exit 44; fi
cmp /tmp/before .env
`));

test('legacy JWT aliases migrate without adopting example credentials', () => run(`
sed -i 's/^KABIPAY_JWT_SECRET=/KABIPAY_CLIENT_JWT_SECRET=/' .env
bash /fixtures/reconcile.sh /tmp/app release-002 >/dev/null
grep -qx 'KABIPAY_JWT_SECRET=existing-jwt-secret-with-at-least-32-bytes' .env
! grep -q '^KABIPAY_CLIENT_JWT_SECRET=' .env
`));

test('fresh deployment generates a restricted environment and keeps backups restricted', () => run(`
rm .env
sed -i 's/^KABIPAY_FINANCE_SERVICE_SECRET=.*/KABIPAY_FINANCE_SERVICE_SECRET=/' .env.example
bash /fixtures/reconcile.sh /tmp/app release-002 >/dev/null
test "$(stat -c %a .env)" = 600
bash /fixtures/reconcile.sh /tmp/app release-003 >/dev/null
for backup in .env.backup.*; do test "$(stat -c %a "$backup")" = 600; done
`));

test('quoted literal Finance values and CRLF configuration compare with container values', () => run(`
sed -i "s|^KABIPAY_FINANCE_EMPLOYEE_URL=.*|KABIPAY_FINANCE_EMPLOYEE_URL='http://127.0.0.1:4013'|" .env
sed -i 's/$/\\r/' .env
bash /fixtures/reconcile.sh /tmp/app release-002 --check-only >/dev/null
`));

test('deploy requires preflight before container restart and validates propagated Finance settings', () => {
  const preflight = deploy.indexOf('bash $RemoteEnvReconcileScriptPathQ $AppDirQ $TagQ --check-only');
  const start = deploy.indexOf('"Starting KabiPay containers with docker compose"');
  assert.ok(preflight > 0 && preflight < start, 'Finance must be validated before docker compose up');
  assert.match(deploy, /bash "\$APP_DIR\/config\/kabipay-reconcile-env\.sh" "\$APP_DIR" "\$TAG" --check-container/);
  assert.match(deploy, /\$EnvFile = Join-Path \$ProjectDocumentationDir 'deploy\/\.env'/);
  assert.match(deploy, /Copy-ToRemote "Uploading local deploy\/\.env as reconciliation input" \$EnvFile \$RemoteEnvExamplePath/);
  assert.match(deploy, /umask 077; touch \$RemoteEnvExamplePathQ; chmod 0600 \$RemoteEnvExamplePathQ/);
});

test('container validation detects missing or mismatched Finance propagation without printing values', () => run(`
mkdir /tmp/bin
printf '#!/bin/sh\\ncat /tmp/container.env\\n' > /tmp/bin/docker
chmod +x /tmp/bin/docker
export PATH="/tmp/bin:$PATH"
cp .env /tmp/container.env
bash /fixtures/reconcile.sh /tmp/app release-002 --check-container >/dev/null
sed -i 's/^KABIPAY_FINANCE_SERVICE_SECRET=.*/KABIPAY_FINANCE_SERVICE_SECRET=mismatched-secret-with-more-than-32-bytes/' /tmp/container.env
if bash /fixtures/reconcile.sh /tmp/app release-002 --check-container >/tmp/output 2>&1; then exit 45; fi
grep -q 'KABIPAY_FINANCE_SERVICE_SECRET' /tmp/output
! grep -q 'mismatched-secret' /tmp/output
`));

test('inline comments cannot pad a short effective Finance secret past preflight', () => run(`
sed -i 's/^KABIPAY_FINANCE_SERVICE_SECRET=.*/KABIPAY_FINANCE_SERVICE_SECRET=short # padding that is not part of the effective secret/' .env
cp .env /tmp/before
if bash /fixtures/reconcile.sh /tmp/app release-002 >/tmp/output 2>&1; then exit 46; fi
cmp /tmp/before .env
grep -q 'KABIPAY_FINANCE_SERVICE_SECRET' /tmp/output
`));

test('JWT independence compares effective quoted values with trailing comments', () => run(`
sed -i 's/^KABIPAY_JWT_SECRET=.*/KABIPAY_JWT_SECRET="independent-finance-secret-with-32-bytes" # jwt comment/' .env
if bash /fixtures/reconcile.sh /tmp/app release-002 --check-only >/tmp/output 2>&1; then exit 47; fi
grep -q 'independent' /tmp/output
`));

test('preflight rejects interpolated JWT configuration without evaluating shell content', () => run(`
sed -i 's/^KABIPAY_JWT_SECRET=.*/KABIPAY_JWT_SECRET=$DUMMY_KEY/' .env
cp .env /tmp/before
if bash /fixtures/reconcile.sh /tmp/app release-002 >/tmp/output 2>&1; then exit 48; fi
cmp /tmp/before .env
grep -q 'KABIPAY_JWT_SECRET' /tmp/output
`));

test('unquoted leading whitespace is rejected before restart rather than reinterpreted', () => run(`
sed -i 's/^KABIPAY_FINANCE_SERVICE_SECRET=.*/KABIPAY_FINANCE_SERVICE_SECRET= # literal whitespace-comment value with more than thirty two bytes/' .env
cp .env /tmp/before
if bash /fixtures/reconcile.sh /tmp/app release-002 >/tmp/output 2>&1; then exit 49; fi
cmp /tmp/before .env
grep -q 'KABIPAY_FINANCE_SERVICE_SECRET' /tmp/output
`));
