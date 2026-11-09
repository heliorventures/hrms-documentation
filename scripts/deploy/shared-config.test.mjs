import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,readFile,mkdir,rm,realpath} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {checkSharedConfig} from './check-shared-config.mjs';
const a='11111111-1111-4111-8111-111111111111',b='22222222-2222-4222-8222-222222222222';
async function fixture(run){
  const root=await mkdtemp(path.join(os.tmpdir(),'hrms-shared-config-'));
  const file=path.join(root,'companies.json');
  const companies=[a,b].map((id,i)=>({tenant_id:id,database_url:`postgres://user_${i}:synthetic@postgres/company_${i}?sslmode=verify-full`,schema:`tenant_${i}`,public_origin:`https://company-${i}.example.com`,settings:{}}));
  const config={version:1,companies};
  try{
    await writeFile(path.join(root,'release.json'),JSON.stringify({applicationLayout:'shared',companyBindings:companies.map((c,i)=>({id:c.tenant_id,publicHost:`company-${i}.example.com`}))}));
    await writeFile(path.join(root,'compose.json'),JSON.stringify({services:{'shared-payroll':{environment:{KABIPAY_COMPANY_CONFIG_FILE:'/run/company-config/companies.json'},volumes:[{type:'bind',source:file,target:'/run/company-config/companies.json'}]}}}));
    await writeFile(file,JSON.stringify(config));
    await run({root,file,config});
  }finally{
    const resolved=await realpath(root);
    assert.equal(path.dirname(resolved),await realpath(os.tmpdir()));
    assert.match(path.basename(resolved),/^hrms-shared-config-/);
    await rm(resolved,{recursive:true,force:true});
  }
}
test('shared configuration accepts explicit inventory and refuses omitted, duplicate, remapped and insecure bindings',()=>fixture(async({root,file,config})=>{
  await checkSharedConfig(root);
  for(const mutate of [
    c=>c.companies.pop(),
    c=>c.companies[1].tenant_id=a,
    c=>c.companies[1].database_url=c.companies[0].database_url,
    c=>c.companies[0].public_origin='https://wrong.example.com',
    c=>c.companies[0].database_url=c.companies[0].database_url.replace('verify-full','require'),
    c=>c.companies[0].database_url+='&sslmode=disable',
  ]){
    const candidate=structuredClone(config);mutate(candidate);await writeFile(file,JSON.stringify(candidate));
    await assert.rejects(checkSharedConfig(root));
  }
}));
test('required private files cannot be omitted or selected from another company mount',()=>fixture(async({root,file,config})=>{
  const compose=JSON.parse(await readFile(path.join(root,'compose.json'),'utf8'));
  const service=compose.services['shared-payroll'];delete compose.services['shared-payroll'];compose.services['shared-auth']=service;
  for(const company of config.companies){
    const dir=path.join(root,company.tenant_id);await mkdir(dir);await writeFile(path.join(dir,'client.key'),'synthetic fixture');
    service.volumes.push({type:'bind',source:dir,target:`/run/companies/${company.tenant_id}/auth`});
    company.settings={KABIPAY_CLIENT_JWT_KEY_ID:`key-${company.tenant_id}`,KABIPAY_CLIENT_JWT_PRIVATE_KEY_FILE:`/run/companies/${company.tenant_id}/auth/client.key`};
  }
  await writeFile(path.join(root,'compose.json'),JSON.stringify(compose));await writeFile(file,JSON.stringify(config));
  await checkSharedConfig(root);
  config.companies[0].settings.KABIPAY_CLIENT_JWT_PRIVATE_KEY_FILE=`/run/companies/${b}/auth/client.key`;
  await writeFile(file,JSON.stringify(config));await assert.rejects(checkSharedConfig(root));
  delete config.companies[0].settings.KABIPAY_CLIENT_JWT_PRIVATE_KEY_FILE;
  await writeFile(file,JSON.stringify(config));await assert.rejects(checkSharedConfig(root));
}));
