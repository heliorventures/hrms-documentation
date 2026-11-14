import assert from 'node:assert/strict';
import test from 'node:test';
import {readFileSync} from 'node:fs';
import {render,validate,publicRoutes} from './render.mjs';
import {createHash} from 'node:crypto';
const fixture=JSON.parse(readFileSync(new URL('../../deploy/hrms/manifest.example.json',import.meta.url)));

const signingServices=['employee','leave','attendance','payroll','tax','benefits','expense','recruitment','performance','lms','succession','compensation','assets','grievance','workflow','notification','analytics','survey'];
const signingIds=()=>Object.fromEntries(signingServices.map(name=>[name,`shared-${name}-v1`]));

test('organization runtime reporting and archive configuration has one explicit purpose file',()=>{
  const {services}=JSON.parse(render(fixture)['compose.json']);
  const extra=`${fixture.appDir}/env/organization-runtime.env`;
  assert.deepEqual(Object.entries(services).filter(([,s])=>s.env_file?.includes(extra)).map(([name])=>name),['organization']);
  assert.deepEqual(services.organization.env_file,[`${fixture.appDir}/env/organization.env`,extra,`${fixture.appDir}/env/metadata/organization.env`]);
});

test('Finance credentials mount only into the two Finance callers',()=>{
  const files=render(fixture),{services}=JSON.parse(files['compose.json']);
  const finance=`${fixture.appDir}/env/shared/finance.env`;
  const readers=Object.entries(services).filter(([,s])=>s.env_file?.includes(finance)).map(([name])=>name).sort();
  assert.deepEqual(readers,['shared-employee','shared-payroll']);
  assert.equal(files['finance-checks.txt'],`${finance}|shared-employee shared-payroll\n`);
});

test('metadata credentials are purpose-specific and every metadata client mounts its verified CA',()=>{
  const {services}=JSON.parse(render(fixture)['compose.json']);
  const files=new Set();
  for(const name of [...signingServices,'auth','maintenance']){
    const service=services[`shared-${name}`];
    const expected=`${fixture.appDir}/env/metadata/${name}.env`;
    assert.equal(service.env_file.at(-1),expected);
    assert(!files.has(expected));files.add(expected);
    assert(service.volumes.some(v=>v.target==='/run/tls/organization-ca.pem'&&v.read_only));
  }
  for(const [service,purpose]of [['kabipay-auth','ops-auth'],['kabipay-subgraphs','ops'],['organization','organization']]){
    assert.equal(services[service].env_file.at(-1),`${fixture.appDir}/env/metadata/${purpose}.env`);
    assert(services[service].volumes.some(v=>v.target==='/run/tls/organization-ca.pem'&&v.read_only));
  }
  for(const [service,purpose]of [['inbox-worker','inbox'],['history-worker','history'],['reporting-worker','reporting'],['capture-coordinator','capture'],['archive','archive']]){
    assert.equal(services[service].env_file.at(-1),`${fixture.appDir}/env/metadata/workers/${purpose}.env`);
    assert(services[service].volumes.some(v=>v.target==='/run/tls/organization-ca.pem'&&v.read_only));
  }
  assert(!services['control-history-worker'].env_file.some(file=>file.includes('/env/metadata/')));
});
test('shared services receive distinct manifest-owned signer IDs and retain explicit rotation',()=>{
  const config={...structuredClone(fixture),serviceKeyIds:signingIds()};
  const services=JSON.parse(render(config)['compose.json']).services;
  for(const name of signingServices)assert.equal(services[`shared-${name}`].environment.KABIPAY_SERVICE_KEY_ID,config.serviceKeyIds[name]);
  assert.equal(services['shared-auth'].environment.KABIPAY_SERVICE_KEY_ID,undefined);
  assert.equal(services['shared-maintenance'].environment.KABIPAY_SERVICE_KEY_ID,undefined);
  config.serviceKeyIds.leave='shared-leave-v2';
  const next=JSON.parse(render(config)['compose.json']).services;
  assert.equal(next['shared-leave'].environment.KABIPAY_SERVICE_KEY_ID,'shared-leave-v2');
  assert.equal(next['shared-employee'].environment.KABIPAY_SERVICE_KEY_ID,services['shared-employee'].environment.KABIPAY_SERVICE_KEY_ID);
});
test('signer ID inventory rejects missing, extra, duplicate and unsafe selectors',()=>{
  for(const edit of [c=>delete c.serviceKeyIds,c=>delete c.serviceKeyIds.leave,c=>c.serviceKeyIds.unexpected='other',c=>c.serviceKeyIds.leave=c.serviceKeyIds.employee,c=>c.serviceKeyIds.leave='bad\nvalue',c=>c.serviceKeyIds=[]]){
    const config={...structuredClone(fixture),serviceKeyIds:signingIds()};edit(config);
    assert.throws(()=>render(config),/service.*key|signing/i);
  }
});

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

test('existing shared file root mounts only separate tenant directories without relocation',()=>{
  const config=structuredClone(fixture);
  for(const company of config.companies)company.privateFilesPath='/opt/apps/data/private-files';
  const files=render(config),{services}=JSON.parse(files['compose.json']);
  const paths=config.companies.map(c=>`/opt/apps/data/private-files/tenants/${c.id}`);
  assert.deepEqual(files['private-files.txt'].trim().split('\n'),paths);
  for(const name of ['employee','notification','maintenance']) {
    const mounts=services[`shared-${name}`].volumes.filter(v=>v.target.startsWith('/var/lib/kabipay/private-files'));
    assert.deepEqual(mounts.map(v=>v.source),paths);
    assert(mounts.every(v=>v.target.endsWith(v.source.slice('/opt/apps/data/private-files'.length)) && !v.bind.create_host_path));
  }
  assert(!Object.values(services).some(s=>s.volumes?.some(v=>v.source==='/opt/apps/data/private-files')));
  const overlapping=structuredClone(config);
  overlapping.companies[1].privateFilesPath=paths[0];
  assert.throws(()=>validate(overlapping),/overlap/);
  const normalized=structuredClone(config);
  normalized.companies[1].privateFilesPath='/opt/apps/data//private-files/./';
  assert.doesNotThrow(()=>validate(normalized));
});
test('five separate companies still deploy exactly 18 business application processes',()=>{
  const config=structuredClone(fixture);
  config.companies=Array.from({length:5},(_,i)=>({id:`00000000-0000-4000-8000-00000000000${i+1}`,slug:`company-${i+1}`,clientJwtKeyId:`company-${i+1}-client-v1`,publicHost:`company-${i+1}.${config.tenantBaseDomain}`,privateFilesPath:`${config.appDir}/data/company-${i+1}/private-files`}));
  config.databasePools.applicationBudget=120;
  config.privateHistoryCompanyIds=config.companies.map(c=>c.id);
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
  assert(files['finance-checks.txt'].includes('/env/shared/finance.env|shared-employee shared-payroll'));
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
  for(const edit of [c=>c.tag='x\nRUN',c=>c.appDir='/opt/apps',c=>c.appDir='/opt/apps/../etc',c=>c.companies[1].id=c.companies[0].id,c=>c.companies[1].publicHost=c.companies[0].publicHost,c=>c.companies[0].publicHost='evil.invalid',c=>c.companies[0].slug='a\nreverse_proxy evil',c=>delete c.companies[0].privateFilesPath,c=>c.companies[1].privateFilesPath=c.companies[0].privateFilesPath+'/tenants/'+c.companies[0].id,c=>c.companies[1].privateFilesPath=c.companies[0].privateFilesPath.replace('/data/','//data/./')+'/tenants/'+c.companies[0].id,c=>c.companies[0].privateFilesPath='/opt/apps/hrms/secrets']) {
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
