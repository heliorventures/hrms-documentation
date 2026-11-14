import assert from 'node:assert/strict';import test from 'node:test';import{readFileSync}from'node:fs';
import{render}from'./render.mjs';
import{validateStartup}from'./startup-scope.mjs';
const fixture=JSON.parse(readFileSync(new URL('../../deploy/hrms/manifest.example.json',import.meta.url)));
const five=()=>({...structuredClone(fixture),databasePools:{...fixture.databasePools,applicationBudget:120},companies:Array.from({length:5},(_,i)=>({id:`00000000-0000-4000-8000-00000000000${i+1}`,slug:`company-${i+1}`,clientJwtKeyId:`company-${i+1}-client-v1`,publicHost:`company-${i+1}.${fixture.tenantBaseDomain}`,privateFilesPath:`${fixture.appDir}/data/company-${i+1}/private-files`})),privateHistoryCompanyIds:['00000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000002','00000000-0000-4000-8000-000000000003']});
test('five company credential catalogs retain all companies while only three private source pairs activate',()=>{
 const config=five(),files=render(config),release=JSON.parse(files['release.json']),compose=JSON.parse(files['compose.json']);
 assert.equal(release.services.length,49);assert.equal(release.activeServices.length,45);assert.equal(files['startup-services.txt'],[...release.activeServices].sort().join('\n')+'\n');
 const active=JSON.parse(files['compose-active.json']);assert.deepEqual(Object.keys(active.services).sort(),release.activeServices);assert.deepEqual(active.networks,compose.networks);
 assert.equal(JSON.parse(files['config/companies/auth.json']).companies.length,5);assert.equal(files['required-tenants.txt'].trim().split(',').length,5);
 for(const company of config.companies)for(const purpose of ['audit','delivery']){const name=`private-${purpose}-${company.slug}`,active=config.privateHistoryCompanyIds.includes(company.id);assert.equal(release.activeServices.includes(name),active);assert.deepEqual(compose.services[name].profiles,active?undefined:['inactive-private-history']);}
});
test('worker activation must be explicit and refuses unknown, duplicate or malformed company selectors',()=>{
 for(const ids of [undefined,null,'all',['00000000-0000-4000-8000-000000000099'],['00000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001']])assert.throws(()=>render({...five(),privateHistoryCompanyIds:ids}),/private history activation/i);
});
test('explicit empty activation keeps shared applications and complete tenant inventory',()=>{
 const files=render({...five(),privateHistoryCompanyIds:[]}),release=JSON.parse(files['release.json']);assert.equal(release.activeServices.length,39);assert.equal(release.companyBindings.length,5);
});
test('startup validation rejects altered activation, profiles, dependencies and active composition',()=>{
 const files=render(five()),release=JSON.parse(files['release.json']),compose=JSON.parse(files['compose.json']),active=JSON.parse(files['compose-active.json']),text=files['startup-services.txt'];
 assert.equal(validateStartup(release,compose,text,active).active.length,45);
 for(const change of [r=>delete r.privateHistoryCompanyIds,r=>r.activeServices.push('private-audit-company-4'),r=>r.services.pop()]){const r=structuredClone(release);change(r);assert.throws(()=>validateStartup(r,compose,text,active));}
 for(const change of [c=>delete c.services['private-audit-company-4'].profiles,c=>c.services['shared-auth'].depends_on=['private-audit-company-4']]){const c=structuredClone(compose);change(c);assert.throws(()=>validateStartup(release,c,text,active));}
 const altered=structuredClone(active);altered.services['private-audit-company-4']=compose.services['private-audit-company-4'];assert.throws(()=>validateStartup(release,compose,text,altered));assert.throws(()=>validateStartup(release,compose,text+release.activeServices[0]+'\n',active));
});
