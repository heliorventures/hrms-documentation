import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {render} from './render.mjs';
const fixture=JSON.parse(readFileSync(new URL('../../deploy/hrms/manifest.example.json',import.meta.url)));
test('retirement release deploys shared maintenance and no retired worker binary',()=>{
 const {services}=JSON.parse(render(fixture)['compose.json']);
 assert(!Object.values(services).some(s=>s.command?.includes('kabipay-outbox-worker')));
 const service=services['shared-maintenance'];assert.equal(service.command[0],'kabipay-tenant-maintenance');assert.equal(service.environment.KABIPAY_BOUND_TENANT_ID,undefined);assert.equal(service.environment.KABIPAY_COMPANY_CONFIG_FILE,'/run/company-config/companies.json');
 assert.throws(()=>render({...fixture,mode:'legacy',companies:[]}));
});
test('private purpose workers have scoped mounts and no source database network or env file',()=>{
 const {services}=JSON.parse(render(fixture)['compose.json']);
 for(const c of fixture.companies)for(const purpose of ['audit','delivery']){
  const s=services[`private-${purpose}-${c.slug}`];assert(s);
  assert.deepEqual(s.command,['node','src/private/worker.mjs']);assert(!s.networks.includes('sources'));assert(!s.networks.includes('metadata'));
  assert(s.env_file[0].endsWith(`/workers/private/${c.slug}/${purpose}.env`));assert(s.volumes.every(v=>!v.source.includes(`/secrets/${c.slug}/`)));
 }
 const query=services['private-audit-history'];assert(query.networks.includes('private-history'));assert(!query.networks.includes('sources'));assert(!query.networks.includes('metadata'));
 assert(query.volumes.every(v=>!v.source.includes('/secrets/company-')));
});
test('source egress ingress requires mTLS and public routes exclude every private endpoint',()=>{
 const files=render(fixture),{services}=JSON.parse(files['compose.json']);
 for(const c of fixture.companies){
  const proxy=files['caddy/shared-source.caddy'];assert(proxy.includes('/internal/private-events/delivery'));assert(proxy.includes('/internal/private-events/ownership'));assert(proxy.includes('require_and_verify'));assert(proxy.includes('private-delivery-client-ca.pem'));
  assert.equal(services['shared-employee'].environment.KABIPAY_COMPANY_CONFIG_FILE,'/run/company-config/companies.json');
  assert(services['shared-analytics'].networks.includes('private-history'));
  assert(!services['shared-auth'].volumes.some(v=>v.source.includes('/private-events/')));
 }
 assert(files['caddy/company-sites.caddy'].includes('respond @private 404'));
});
