import assert from 'node:assert/strict';
import test from 'node:test';
import {readFileSync} from 'node:fs';
import {render,validate,publicRoutes} from './render.mjs';
import {createHash} from 'node:crypto';
const fixture=JSON.parse(readFileSync(new URL('../../deploy/hrms/manifest.example.json',import.meta.url)));

test('onboarding generates registry catalogues without adding tenant credentials to service files',()=>{
  const files=render(fixture),{services}=JSON.parse(files['compose.json']);
  const catalog=JSON.parse(files['config/companies/employee.json']);
  assert.equal(catalog.version,2);
  assert.equal(catalog.companies.length,fixture.companies.length);
  assert(catalog.companies.every(c=>!('database_url' in c)&&!('schema' in c)));
  assert.equal(services['shared-employee'].environment.KABIPAY_COMPANY_DATABASE_FILE,'/run/service-secrets/database.json');
  const next=structuredClone(fixture);
  next.companies.push({id:'33333333-3333-4333-8333-333333333333',slug:'company-c',publicHost:`company-c.${next.tenantBaseDomain}`,privateFilesPath:`${next.appDir}/data/company-c/private-files`,clientJwtKeyId:'company-c-client-v1'});
  next.databasePools.applicationBudget=80;
  const added=render(next),newServices=JSON.parse(added['compose.json']).services;
  assert.equal(JSON.parse(added['config/companies/employee.json']).companies.length,3);
  for(const name of ['employee','auth','maintenance']) {
    assert.equal(newServices[`shared-${name}`].environment.KABIPAY_COMPANY_DATABASE_FILE,services[`shared-${name}`].environment.KABIPAY_COMPANY_DATABASE_FILE);
    assert.deepEqual(newServices[`shared-${name}`].volumes.find(v=>v.target==='/run/service-secrets'),services[`shared-${name}`].volumes.find(v=>v.target==='/run/service-secrets'));
  }
});

test('generated history TLS references preserve established company provisioning filenames',()=>{
  const files=render(fixture);
  for(const name of ['survey','analytics'])for(const company of JSON.parse(files[`config/companies/${name}.json`]).companies){
    assert.equal(company.settings.KABIPAY_PRIVATE_HISTORY_CLIENT_CERT_FILE,`/run/companies/${company.tenant_id}/private-events/client.crt`);
    assert.equal(company.settings.KABIPAY_PRIVATE_HISTORY_CLIENT_KEY_FILE,`/run/companies/${company.tenant_id}/private-events/client.key`);
  }
  const auth=JSON.parse(files['config/companies/auth.json']);
  assert.deepEqual(auth.companies.map(c=>c.settings.KABIPAY_CLIENT_JWT_KEY_ID),fixture.companies.map(c=>c.clientJwtKeyId));
});
test('five separate companies still deploy exactly 18 business application processes',()=>{
  const config=structuredClone(fixture);
  config.companies=Array.from({length:5},(_,i)=>({id:`00000000-0000-4000-8000-00000000000${i+1}`,slug:`company-${i+1}`,clientJwtKeyId:`company-${i+1}-client-v1`,publicHost:`company-${i+1}.${config.tenantBaseDomain}`,privateFilesPath:`${config.appDir}/data/company-${i+1}/private-files`}));
  config.databasePools.applicationBudget=120;
  const files=render(config),{services}=JSON.parse(files['compose.json']);
  const business=Object.values(services).filter(s=>s.command?.[0]?.startsWith('kabipay-')&&!['kabipay-auth','kabipay-ops','kabipay-organization','kabipay-tenant-maintenance'].includes(s.command[0]));
  assert.equal(business.length,18);
  assert.equal(Object.keys(services).filter(n=>/^shared-/.test(n)).length,24);
  for(const company of config.companies){
    assert.equal(services[`employee-${company.slug}`],undefined);
    assert(files['caddy/shared-source.caddy'].includes(`header_up X-Organization-Company-Id ${company.id}`));
    const fileMount=services['shared-employee'].volumes.find(v=>v.target===`/var/lib/kabipay/private-files/tenants/${company.id}`);
    assert.equal(fileMount.source,`${company.privateFilesPath}/tenants/${company.id}`);
    assert.equal(fileMount.read_only,false);
  }
  assert.throws(()=>render({...config,databasePools:{...config.databasePools,applicationBudget:119}}),/connection budget/);
  assert.throws(()=>render({...config,applicationLayout:undefined}),/shared company layout/);
});
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
test('application release excludes shared installation and shares application processes with explicit company configuration',()=>{
  const files=render(fixture), {services,networks}=JSON.parse(files['compose.json']);
  for(const server of ['postgres','mongo','kafka','connect','clickhouse','caddy']) assert.equal(services[server],undefined);
  assert.equal(networks['app-network'].name,'apps_app-network');
  assert.equal(services['shared-auth'].environment.KABIPAY_BOUND_TENANT_ID,undefined);
  assert.equal(services['shared-auth'].environment.KABIPAY_COMPANY_CONFIG_FILE,'/run/company-config/companies.json');
  assert.equal(services['shared-auth'].environment.KABIPAY_CLIENT_JWT_MODE,'rs256');
  assert.equal(services['shared-leave'].environment.KABIPAY_ORGANIZATION_POLICY_URL,'https://organization-internal:8443');
  assert(services['organization-internal'].networks.includes('sources'));
  assert(!services.organization.networks.includes('sources'));
  assert.equal(networks['company-egress'].internal,false);
  assert(services['shared-maintenance'].networks.includes('company-egress'));
  assert(!services.organization.networks.includes('company-egress'));
  assert(files['caddy/shared-public.caddy'].includes('/auth/client/organization-identity'));
  assert.equal(services['shared-leave'].environment.KABIPAY_SERVICE_ID,'kabipay-leave');
  assert(!JSON.stringify(services.organization).includes('/secrets/company-'));
  assert(!JSON.stringify(services.organization).includes('/env/companies/'));
  assert.equal(services['kabipay-gateway'].environment.KABIPAY_ORGANIZATION_ENABLED,'false');
  assert.equal(services['kabipay-gateway'].environment.KABIPAY_GATEWAY_PLANE,'ops');
  assert.deepEqual(services['kabipay-subgraphs'].command,['kabipay-ops']);
  assert.equal(services['kabipay-auth'].environment.KABIPAY_AUTH_PLANE,'ops');
  assert.equal(services['shared-auth'].environment.KABIPAY_AUTH_PLANE,'client');
  assert.equal(services['kabipay-outbox-worker'],undefined);
  assert.equal(services['shared-gateway'].environment.KABIPAY_ORGANIZATION_ENABLED,'true');
  assert(!Object.values(services).some(s=>s.ports));
  assert(files['finance-checks.txt'].includes('/env/shared/runtime.env|shared-employee shared-payroll'));
});
test('company sessions use their own public hostname and internal APIs are denied',()=>{
  const f=render(fixture);
  assert.equal(JSON.parse(f['config/ui-company-a.json']).authUrl,'https://company-a.heliorsoft.com');
  for(const name of ['caddy/legacy-routes.caddy','caddy/shared-public.caddy','caddy/company-sites.caddy']) assert(f[name].includes('/auth/internal/*'));
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
test('new release requires reviewed shared application layout; previous artifacts own rollback',()=>{
  assert.throws(()=>render({...fixture,mode:'legacy',companies:[]}),/shared company layout/);
});
test('release artifact allowlist is complete and never includes operator secrets',()=>{
  const files=render(fixture),release=JSON.parse(files['release.json']);
  assert.deepEqual(release.artifacts.sort(),Object.keys(files).sort());
  assert(!release.artifacts.some(p=>p.includes('secrets')||p.endsWith('.env')));
});
