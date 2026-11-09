const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { test } = require('node:test');

const root = path.resolve(__dirname, '../..');
const deploy = fs.readFileSync(path.join(root, 'scripts/deploy-on-vps.ps1'), 'utf8');
const release = fs.readFileSync(path.join(root, 'scripts/deploy/release.sh'), 'utf8');
const script = fs.readFileSync(path.join(root, 'scripts/deploy/reconcile-env.sh'), 'utf8');
const valid = [
  'POSTGRES_HOST=postgres', 'POSTGRES_PORT=5432', 'POSTGRES_DB=demo',
  'POSTGRES_USER=demo', 'POSTGRES_PASSWORD=existing-db-password',
  'KABIPAY_JWT_SECRET=existing-jwt-secret-with-at-least-32-bytes',
  'KABIPAY_PROFILE_CHANGE_ENCRYPTION_KEY=existing-encryption-key',
  'KABIPAY_FINANCE_SERVICE_SECRET=independent-finance-secret-with-32-bytes',
  'KABIPAY_FINANCE_EMPLOYEE_URL=https://source-demo:8452',
  'KABIPAY_FINANCE_PAYROLL_URL=https://source-demo:8451',
].join('\n') + '\n';
const example = valid.replaceAll('existing-', 'example-') + 'NEW_SETTING=enabled\n';
const inventoryFixture=String.raw`
make_inventory_fixture() {
 printf '{}' > compose.json
 printf '{}' > release.json
 printf '11111111-1111-4111-8111-111111111111\n' > required-tenants.txt
 sha256sum --text compose.json release.json required-tenants.txt > release.sha256
 now="$(date -u +%s)"
 digest="$(sha256sum release.sha256 | cut -d ' ' -f 1)"
 printf 'version=1\nscope=single-shared-fleet\ntag=release-002\nrelease_sha256=%s\nchecked_at=%s\nexpires_at=%s\ntenant_ids=11111111-1111-4111-8111-111111111111\n' "$digest" "$now" "$((now+900))" > cutover-inventory.txt
}
`;

function run(body) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'kabipay-env-test-'));
  try {
    const fixtures = path.join(dir, 'fixtures');
    const temporary = path.join(dir, 'tmp');
    fs.mkdirSync(fixtures);fs.mkdirSync(temporary);
    fs.writeFileSync(path.join(fixtures, 'reconcile.sh'), script.replace(/\r\n/g, '\n'));
    fs.writeFileSync(path.join(fixtures, 'release.sh'), release.replace(/\r\n/g, '\n'));
    fs.writeFileSync(path.join(fixtures, 'check-inventory.sh'), fs.readFileSync(path.join(root,'scripts/deploy/check-inventory.sh'),'utf8').replace(/\r\n/g,'\n'));
    fs.writeFileSync(path.join(fixtures, 'fixture.env'), valid);
    fs.writeFileSync(path.join(fixtures, 'fixture.example'), example);
    const bashPath = value => value.replaceAll('\\','/').replace(/^([A-Za-z]):/, (_,drive)=>`/${drive.toLowerCase()}`);
    const fixturePath=bashPath(fixtures),temporaryPath=bashPath(temporary);
    const bash=process.env.GIT_BASH ?? (process.platform==='win32'?'C:/Program Files/Git/bin/bash.exe':'bash');
    // Git Bash/NTFS reports0644 after chmod0600; runtime permission checks remain on POSIX.
    const modeHelper=process.platform==='win32' ? 'assert_private_mode() { :; }' : 'assert_private_mode() { test "$(stat -c %a "$1")" = 600; }';
    const isolatedBody=body.replaceAll('/fixtures/',`${fixturePath}/`).replaceAll('/tmp/',`${temporaryPath}/`);
    const result=spawnSync(bash,['--noprofile','--norc','-s'],{
      input:`set -euo pipefail\n${modeHelper}\nmkdir "${temporaryPath}/app"\ncd "${temporaryPath}/app"\nmkdir scripts\ncp "${fixturePath}/check-inventory.sh" scripts/check-inventory.sh\ncp "${fixturePath}/fixture.env" .env\ncp "${fixturePath}/fixture.example" .env.example\n${inventoryFixture}\n${isolatedBody}\n`,
      encoding:'utf8',timeout:60000,env:{...process.env,MSYS_NO_PATHCONV:'1'},
    });
    assert.ifError(result.error);
    const output=path.join(temporary,'output');
    const diagnostic=result.status!==0 && fs.existsSync(output)?fs.readFileSync(output,'utf8').slice(-2500):'';
    assert.equal(result.status, 0, result.stdout + result.stderr + diagnostic);
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
assert_private_mode .env
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
for url in 'https://user:password@example.test' 'https://example.test/private' 'https://example.test?token=x' 'https://example.test:99999' 'https://[:::]:4013' 'https://999.999.999.999:4013' 'https://example.123' 'https://example.0xff'; do
  cp /fixtures/fixture.env .env
  sed -i "s|^KABIPAY_FINANCE_EMPLOYEE_URL=.*|KABIPAY_FINANCE_EMPLOYEE_URL=$url|" .env
  if bash /fixtures/reconcile.sh /tmp/app release-002 --check-only >/tmp/output 2>&1; then exit 43; fi
  grep -q 'KABIPAY_FINANCE_EMPLOYEE_URL' /tmp/output
done
`));

test('Finance requires HTTPS for each service origin before any environment mutation', () => run(`
for name in KABIPAY_FINANCE_EMPLOYEE_URL KABIPAY_FINANCE_PAYROLL_URL; do
  cp /fixtures/fixture.env .env
  sed -i "s|^$name=.*|$name=http://source-demo:8452|" .env
  cp .env /tmp/before
  if bash /fixtures/reconcile.sh /tmp/app release-002 --check-finance-file /tmp/app/.env >/tmp/output 2>&1; then exit 56; fi
  cmp /tmp/before .env
  grep -q "$name" /tmp/output
done
`));

test('preflight accepts compressed and full IPv6 service origins', () => run(`
for url in 'https://[::1]:8452' 'https://[2001:db8::1]' 'https://[2001:db8:1:2:3:4:5:6]:8452'; do
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
assert_private_mode .env
bash /fixtures/reconcile.sh /tmp/app release-003 >/dev/null
for backup in .env.backup.*; do assert_private_mode "$backup"; done
`));

test('quoted literal Finance values and CRLF configuration compare with container values', () => run(`
sed -i "s|^KABIPAY_FINANCE_EMPLOYEE_URL=.*|KABIPAY_FINANCE_EMPLOYEE_URL='https://source-demo:8452'|" .env
sed -i 's/$/\\r/' .env
bash /fixtures/reconcile.sh /tmp/app release-002 --check-only >/dev/null
`));

test('release validates Finance before up and checks explicit propagated container identity without fleet env upload', () => {
  const preflight=release.indexOf('--check-finance-file');
  const start=release.indexOf('"${compose[@]}" up');
  assert.ok(preflight>=0 && start>preflight,'Finance file preflight must precede application up');
  assert.ok(release.indexOf('--check-finance-container')>=0,'Release must verify propagated Finance values');
  assert.match(deploy,/Fleet-wide deploy\/\.env is never copied/);
  assert.doesNotMatch(deploy,/Uploading local deploy\/\.env as reconciliation input/);
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

test('finance-only file validation needs no PostgreSQL or global JWT and never rewrites source', () => run(`
sed -i '/^POSTGRES_/d;/^KABIPAY_JWT_SECRET=/d' .env
cp .env /tmp/before
bash /fixtures/reconcile.sh /tmp/app release-002 --check-finance-file /tmp/app/.env >/tmp/output
cmp /tmp/before .env
test "$(find . -name '.env.backup.*' | wc -l)" = 0
`));

test('finance-only validation preserves effective JWT independence and strict origin rules', () => run(`
sed -i '/^POSTGRES_/d' .env
sed -i 's/^KABIPAY_JWT_SECRET=.*/KABIPAY_JWT_SECRET="independent-finance-secret-with-32-bytes" # effective jwt/' .env
if bash /fixtures/reconcile.sh /tmp/app release-002 --check-finance-file /tmp/app/.env >/tmp/output 2>&1; then exit 51; fi
grep -q independent /tmp/output
sed -i '/^KABIPAY_JWT_SECRET=/d' .env
sed -i 's|^KABIPAY_FINANCE_EMPLOYEE_URL=.*|KABIPAY_FINANCE_EMPLOYEE_URL=https://example.test/private|' .env
if bash /fixtures/reconcile.sh /tmp/app release-002 --check-finance-file /tmp/app/.env >/tmp/output 2>&1; then exit 52; fi
grep -q KABIPAY_FINANCE_EMPLOYEE_URL /tmp/output
`));

test('finance-only container check targets supplied ID and detects propagation mismatch without PG', () => run(`
sed -i '/^POSTGRES_/d;/^KABIPAY_JWT_SECRET=/d' .env
mkdir /tmp/bin
printf '#!/bin/sh\\n[ "$4" = abcdef123456 ] || exit 79\\ncat /tmp/container.env\\n' > /tmp/bin/docker
chmod +x /tmp/bin/docker
export PATH="/tmp/bin:$PATH"
cp .env /tmp/container.env
bash /fixtures/reconcile.sh /tmp/app release-002 --check-finance-container /tmp/app/.env abcdef123456 >/dev/null
sed -i 's/^KABIPAY_FINANCE_SERVICE_SECRET=.*/KABIPAY_FINANCE_SERVICE_SECRET=mismatched-secret-with-more-than-32-bytes/' /tmp/container.env
if bash /fixtures/reconcile.sh /tmp/app release-002 --check-finance-container /tmp/app/.env abcdef123456 >/tmp/output 2>&1; then exit 53; fi
grep -q KABIPAY_FINANCE_SERVICE_SECRET /tmp/output
! grep -q mismatched-secret /tmp/output
`));

test('actual release rejects invalid Finance source before mocked application up', () => run(`
sed -i '/^POSTGRES_/d;/^KABIPAY_JWT_SECRET=/d' .env
sed -i 's/^KABIPAY_FINANCE_SERVICE_SECRET=.*/KABIPAY_FINANCE_SERVICE_SECRET=too-short/' .env
mkdir -p scripts /tmp/bin
cp /fixtures/reconcile.sh scripts/reconcile-env.sh
printf '/tmp/app/.env|employee-fixture payroll-fixture\\n' > finance-checks.txt
printf '' > private-files.txt
printf '#!/bin/sh\\nprintf "%s\\\\n" "$*" >> /tmp/docker.log\\nif [ "$1" = container ]; then exit 1; fi\\nexit 0\\n' > /tmp/bin/docker
chmod +x /tmp/bin/docker
export PATH="/tmp/bin:$PATH"
make_inventory_fixture
if bash /fixtures/release.sh /tmp/app /tmp/app/images release-002 0 1 0 organization >/tmp/output 2>&1; then exit 54; fi
! grep -q ' up ' /tmp/docker.log
grep -q KABIPAY_FINANCE_SERVICE_SECRET /tmp/output
! grep -q too-short /tmp/output
`));
test('reconciliation retains explicit Unix credential permission controls',()=>{
 assert.match(script,/umask 077/);
 assert.match(script,/chmod 600 "\$backup"/);
 assert.match(script,/chmod 600 "\$next"/);
});

test('organization startup rejects missing tenant inventory before image load or up',()=>run(`
mkdir /tmp/bin
printf '' > private-files.txt
printf '' > finance-checks.txt
cat > /tmp/bin/docker <<'MOCK'
#!/bin/sh
printf '%s\\n' "$*" >> /tmp/docker.log
if [ "$1" = container ]; then exit 1; fi
if [ "$1" = compose ]; then
 case "$*" in *'config --services'*) printf 'fixture\\n';; esac
fi
exit 0
MOCK
chmod +x /tmp/bin/docker
export PATH="/tmp/bin:$PATH"
if bash /fixtures/release.sh /tmp/app /tmp/app/images release-002 0 1 0 organization >/tmp/output 2>&1; then exit 66; fi
grep -qi 'inventory' /tmp/output
! grep -q ' up \\| load ' /tmp/docker.log
`));

for (const legacyName of ['compose-generated','explicit-name']) test(`organization release blocks ${legacyName} legacy worker before up`,()=>run(`
mkdir /tmp/bin
cat > /tmp/bin/docker <<'MOCK'
#!/bin/sh
printf '%s\\n' "$*" >> /tmp/docker.log
if [ "$1" = ps ]; then
  case "$*" in
   *com.docker.compose.service=kabipay-outbox-worker*) ${legacyName==='compose-generated' ? 'printf abcdef123456' : ':'};;
   *name=*) ${legacyName==='explicit-name' ? 'printf abcdef123456' : ':'};;
  esac
fi
if [ "$1" = container ]; then ${legacyName==='compose-generated' ? 'exit 1' : 'exit 0'}; fi
if [ "$1" = inspect ]; then printf running; fi
exit 0
MOCK
chmod +x /tmp/bin/docker
export PATH="/tmp/bin:$PATH"
if bash /fixtures/release.sh /tmp/app /tmp/app/images release-002 0 1 0 organization >/tmp/output 2>&1; then exit 55; fi
grep -q 'Retired delivery worker' /tmp/output
! grep -q ' up ' /tmp/docker.log
`));

test('organization release inventories every running owned command and fails closed without stopping containers',()=>run(`
mkdir /tmp/bin
printf '' > private-files.txt
printf '' > finance-checks.txt
cat > /tmp/bin/docker <<'MOCK'
#!/bin/sh
printf '%s\\n' "$*" >> /tmp/docker.log
if [ "$1" = ps ]; then
 case "$*" in
  *com.docker.compose.service=kabipay-outbox-worker*) [ "$WORKER_CASE" != old-label ] || printf abcdef123456; exit 0;;
  *name=*) [ "$WORKER_CASE" != explicit-outside-project ] || printf abcdef123456; exit 0;;
 esac
 case "$*" in *com.docker.compose.project=apps*) :;; *) exit 79;; esac
 [ "$WORKER_CASE" != inventory-error ] || exit 80
 [ "$WORKER_CASE" != unrelated-project ] || exit 0
 printf abcdef123456
 exit 0
fi
if [ "$1" = container ]; then exit 1; fi
if [ "$1" = inspect ]; then
 [ "$WORKER_CASE" != inspect-error ] || exit 81
 case "$3" in
  *.Config.Labels*) [ "$WORKER_CASE" != old-application ] || printf 'maintenance-company-a\\n'; exit 0;;
 esac
 case "$3" in
  *.Config.Entrypoint*) [ "$WORKER_CASE" != entrypoint ] || printf '/app/kabipay-outbox-worker\\n';;
 esac
 case "$3" in
  *.Config.Cmd*)
   case "$WORKER_CASE" in
    absolute-command) printf '/usr/local/bin/kabipay-outbox-worker\\nSYNTHETIC_SECRET_DO_NOT_LOG\\n';;
    shell-command) printf '/bin/sh\\n-c\\nexec "/app/kabipay-outbox-worker" --token SYNTHETIC_SECRET_DO_NOT_LOG\\n';;
    entrypoint) printf '%s\\n' --bound-company;;
    *) printf '/usr/local/bin/kabipay-tenant-maintenance\\n';;
   esac;;
 esac
 exit 0
fi
if [ "$1" = compose ]; then
 case "$*" in *'config --services'*)
  if [ "$WORKER_CASE" = expire-receipt ]; then sed -i 's/^expires_at=.*/expires_at=1/' cutover-inventory.txt; fi
  printf 'maintenance-fixture\\n';; esac
fi
exit 0
MOCK
chmod +x /tmp/bin/docker
export PATH="/tmp/bin:$PATH"
for WORKER_CASE in absolute-command shell-command entrypoint old-label explicit-outside-project inspect-error inventory-error old-application; do
 export WORKER_CASE
 printf '' > /tmp/docker.log
 if bash /fixtures/release.sh /tmp/app /tmp/app/images release-002 0 1 0 organization >/tmp/output 2>&1; then exit 57; fi
 case "$WORKER_CASE" in
  inspect-error|inventory-error) grep -q 'safety inventory failed' /tmp/output;;
  old-application) grep -q 'Previous company application containers' /tmp/output;;
  *) grep -q 'Retired delivery worker is running' /tmp/output;;
 esac
 ! grep -q ' up ' /tmp/docker.log
 ! grep -q ' stop \\| rm \\| kill ' /tmp/docker.log
 ! grep -q 'SYNTHETIC_SECRET_DO_NOT_LOG' /tmp/output
done
make_inventory_fixture
for WORKER_CASE in maintenance unrelated-project; do
 export WORKER_CASE
 printf '' > /tmp/docker.log
 bash /fixtures/release.sh /tmp/app /tmp/app/images release-002 0 1 0 organization >/tmp/output 2>&1
 grep -q ' up ' /tmp/docker.log
 ! grep -q ' stop \\| rm \\| kill ' /tmp/docker.log
done
export WORKER_CASE=expire-receipt
printf '' > /tmp/docker.log
if bash /fixtures/release.sh /tmp/app /tmp/app/images release-002 0 1 0 organization >/tmp/output 2>&1; then exit 68; fi
grep -qi inventory /tmp/output
! grep -q ' up ' /tmp/docker.log
make_inventory_fixture
export WORKER_CASE=maintenance
printf '' > /tmp/docker.log
if bash /fixtures/release.sh /tmp/app /tmp/app/images release-002 0 1 0 legacy >/tmp/output 2>&1; then exit 69; fi
grep -qi 'requires organization' /tmp/output
! grep -q ' up ' /tmp/docker.log
`));
