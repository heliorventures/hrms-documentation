import assert from 'node:assert/strict';
import test from 'node:test';
import {readFileSync} from 'node:fs';
import {render,validate,publicRoutes} from './render.mjs';
import {createHash} from 'node:crypto';
const fixture=JSON.parse(readFileSync(new URL('../../deploy/hrms/manifest.example.json',import.meta.url)));
test('release inventory and checksums bind every rendered company and artifact',()=>{
  const files=render(fixture),release=JSON.parse(files['release.json']);
  assert.deepEqual(release.companyBindings,fixture.companies.map(({id,slug,publicHost})=>({id,slug,publicHost})));
  assert.equal(release.tenantBaseDomain,fixture.tenantBaseDomain);
  assert.equal(files['required-tenants.txt'],fixture.companies.map(c=>c.id).sort().join(',')+'\n');
  const indexed=new Set();
  for(const line of files['release.sha256'].trimEnd().split('\n')){
    const match=line.match(/^([a-f0-9]{64})  ([a-zA-Z0-9_./-]+)$/);assert(match);
    const [,digest,name]=match;assert(!indexed.has(name));indexed.add(name);
    assert.equal(digest,createHash('sha256').update(files[name]).digest('hex'));
  }
  assert.deepEqual([...indexed].sort(),Object.keys(files).filter(n=>n!=='release.sha256').sort());
  assert(release.artifacts.includes('release.sha256'));
});
test('application release excludes shared installation and uses fixed company bindings',()=>{
  const files=render(fixture), {services,networks}=JSON.parse(files['compose.json']);
  for(const server of ['postgres','mongo','kafka','connect','clickhouse','caddy']) assert.equal(services[server],undefined);
  assert.equal(networks['app-network'].name,'apps_app-network');
  assert.equal(services['auth-company-a'].environment.KABIPAY_BOUND_TENANT_ID,fixture.companies[0].id);
  assert.equal(services['auth-company-a'].environment.KABIPAY_CLIENT_JWT_MODE,'rs256');
  assert.equal(services['leave-company-a'].environment.KABIPAY_ORGANIZATION_POLICY_URL,'https://organization-internal:8443');
  assert(services['organization-internal'].networks.includes('sources'));
  assert(!services.organization.networks.includes('sources'));
  assert.equal(networks['egress-company-a'].internal,false);
  assert(services['maintenance-company-a'].networks.includes('egress-company-a'));
  assert(!services.organization.networks.includes('egress-company-a'));
  assert(files['caddy/public-company-a.caddy'].includes('/auth/client/organization-identity'));
  assert.equal(services['leave-company-b'].environment.KABIPAY_SERVICE_ID,'kabipay-leave');
  assert(!JSON.stringify(services.organization).includes('/secrets/company-'));
  assert(!JSON.stringify(services.organization).includes('/env/companies/'));
  assert.equal(services['kabipay-gateway'].environment.KABIPAY_ORGANIZATION_ENABLED,'false');
  assert.equal(services['kabipay-gateway'].environment.KABIPAY_GATEWAY_PLANE,'ops');
  assert.deepEqual(services['kabipay-subgraphs'].command,['kabipay-ops']);
  assert.equal(services['kabipay-auth'].environment.KABIPAY_AUTH_PLANE,'ops');
  assert.equal(services['auth-company-a'].environment.KABIPAY_AUTH_PLANE,'client');
  assert.equal(services['kabipay-outbox-worker'],undefined);
  assert.equal(services['gateway-company-a'].environment.KABIPAY_ORGANIZATION_ENABLED,'true');
  assert(!Object.values(services).some(s=>s.ports));
  assert(files['finance-checks.txt'].includes('/env/companies/company-a/runtime.env|employee-company-a payroll-company-a'));
});
test('company sessions use their own public hostname and internal APIs are denied',()=>{
  const f=render(fixture);
  assert.equal(JSON.parse(f['config/ui-company-a.json']).authUrl,'https://company-a.heliorsoft.com');
  for(const name of ['caddy/legacy-routes.caddy','caddy/public-company-a.caddy','caddy/company-sites.caddy']) assert(f[name].includes('/auth/internal/*'));
  assert(publicRoutes({plane:'company',auth:'auth:1',gateway:'g:2',employee:'e:3',notification:'n:4',ui:'ui:80'}).includes('respond @private 404'));
  assert(!f['caddy/company-sites.caddy'].includes('organization:4031'));
});
test('global operator routes contain no retired company upstreams and require an explicit valid plane',()=>{
  const files=render(fixture),ops=files['caddy/legacy-routes.caddy'];
  assert.doesNotMatch(ops,/:4013|:4028/);
  assert(!ops.includes('reverse_proxy undefined'));
  for(const plane of [undefined,'legacy','tenant',''])assert.throws(()=>publicRoutes({plane,auth:'auth:1',gateway:'g:2',ui:'ui:80'}),/plane/);
});
test('reject duplicate/ambiguous/untrusted deployment selectors before rendering',()=>{
  for(const edit of [c=>c.tag='x\nRUN',c=>c.appDir='/opt/apps',c=>c.appDir='/opt/apps/../etc',c=>c.companies[1].id=c.companies[0].id,c=>c.companies[1].publicHost=c.companies[0].publicHost,c=>c.companies[0].publicHost='evil.invalid',c=>c.companies[0].slug='a\nreverse_proxy evil',c=>delete c.companies[0].privateFilesPath,c=>c.companies[1].privateFilesPath=c.companies[0].privateFilesPath,c=>c.companies[1].privateFilesPath=c.companies[0].privateFilesPath+'/child',c=>c.companies[1].privateFilesPath=c.companies[0].privateFilesPath.replace('/data/','//data/./'),c=>c.companies[0].privateFilesPath='/opt/apps/hrms/secrets']) {
    const c=structuredClone(fixture);edit(c);assert.throws(()=>validate(c));
  }
});
test('new release requires reviewed bound sources; previous artifacts own rollback',()=>{
  assert.throws(()=>render({...fixture,mode:'legacy',companies:[]}),/bound company layout/);
});
test('release artifact allowlist is complete and never includes operator secrets',()=>{
  const files=render(fixture),release=JSON.parse(files['release.json']);
  assert.deepEqual(release.artifacts.sort(),Object.keys(files).sort());
  assert(!release.artifacts.some(p=>p.includes('secrets')||p.endsWith('.env')));
});
