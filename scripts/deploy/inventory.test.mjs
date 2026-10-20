import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {render} from './render.mjs';
import operator from '../../../hrms-database/provisioning/organization/check-rollout.cjs';
const {readRelease,checkRegistry}=operator;
const example=JSON.parse(fs.readFileSync(new URL('../../deploy/hrms/manifest.example.json',import.meta.url)));
const gate=fileURLToPath(new URL('./check-inventory.sh',import.meta.url));
function fixture(config=example) {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'hrms-inventory-'));
  for(const [name,content] of Object.entries(render(structuredClone(config)))) {
    fs.mkdirSync(path.dirname(path.join(dir,name)),{recursive:true});
    fs.writeFileSync(path.join(dir,name),content);
  }
  return {dir,release:readRelease(dir),rows:config.companies.map((c,i)=>({id:c.id,subdomain:c.slug,status:i?'SUSPENDED':'ACTIVE',is_deleted:false})),
    cleanup(){assert.equal(path.dirname(fs.realpathSync(dir)),fs.realpathSync(os.tmpdir()));assert.match(path.basename(dir),/^hrms-inventory-/);fs.rmSync(dir,{recursive:true,force:true});}};
}
function runGate(f,receipt) {
  fs.writeFileSync(path.join(f.dir,'cutover-inventory.txt'),receipt);
  const bash=process.env.GIT_BASH??(process.platform==='win32'?'C:/Program Files/Git/bin/bash.exe':'bash');
  const posix=v=>v.replaceAll('\\','/').replace(/^([A-Za-z]):/,(_,drive)=>'/'+drive.toLowerCase());
  const r=spawnSync(bash,['--noprofile','--norc',posix(gate),posix(f.dir),f.release.tag],
    {encoding:'utf8',timeout:10000,windowsHide:true,env:{...process.env,MSYS_NO_PATHCONV:'1'}});
  assert.ifError(r.error);return r;
}
test('complete live registry inventory accepts active and suspended companies with current host slugs',()=>{
  const f=fixture();try {
    const receipt=checkRegistry(f.release,[...f.rows].reverse());
    assert(receipt.includes('tenant_ids=11111111-1111-4111-8111-111111111111,22222222-2222-4222-8222-222222222222\n'));
    const r=runGate(f,receipt);assert.equal(r.status,0,r.stdout+r.stderr);
  }finally{f.cleanup();}
});
test('omitting an active or suspended tenant blocks inventory issuance',()=>{
  const config=structuredClone(example);config.companies.pop();
  const f=fixture(config);try {
    for(const status of ['ACTIVE','SUSPENDED'])assert.throws(()=>checkRegistry(f.release,[...f.rows,{id:example.companies[1].id,subdomain:'company-b',status,is_deleted:false}]),/INVENTORY_MISSING_TENANTS/);
  }finally{f.cleanup();}
});
test('extra unready company, stale subdomain and malformed registry rows are refused',()=>{
  const f=fixture();try {
    assert.throws(()=>checkRegistry(f.release,f.rows.slice(0,1)),/COMPANY_NOT_READY/);
    assert.throws(()=>checkRegistry(f.release,f.rows.map((r,i)=>i?{...r,subdomain:'old-company'}:r)),/SUBDOMAIN_MISMATCH/);
    for(const rows of [[...f.rows,f.rows[0]],f.rows.map(r=>({...r,is_deleted:true})),f.rows.map(r=>({...r,status:'PROVISIONING'}))])
      assert.throws(()=>checkRegistry(f.release,rows),/INVALID_REGISTRY_RESULT/);
  }finally{f.cleanup();}
});
test('expired, future, wrong-tag, altered and malformed receipts fail the native gate',()=>{
  const f=fixture();try {
    const now=Math.floor(Date.now()/1000),receipt=checkRegistry(f.release,f.rows,now);
    const cases=[
      receipt.replace('checked_at='+now,'checked_at='+(now-901)).replace('expires_at='+(now+900),'expires_at='+(now-1)),
      receipt.replace('checked_at='+now,'checked_at='+(now+120)).replace('expires_at='+(now+900),'expires_at='+(now+1020)),
      receipt.replace('tag='+f.release.tag,'tag=other-release'),
      receipt.replace('release_sha256='+f.release.digest,'release_sha256='+'a'.repeat(64)),
      receipt.replace('scope=single-shared-fleet','scope=other-fleet'),
      receipt.replace('tenant_ids=','tenant_ids=unexpected,'),
      receipt+'version=1\n',
      receipt.replace(/^expires_at=.*\n/m,''),
    ];
    for(const candidate of cases){const r=runGate(f,candidate);assert.notEqual(r.status,0);assert.match(r.stderr,/inventory/i);}
  }finally{f.cleanup();}
});
test('changing a rendered artifact after inventory invalidates the operator and release checks',()=>{
  const f=fixture();try {
    const receipt=checkRegistry(f.release,f.rows);
    fs.appendFileSync(path.join(f.dir,'compose.json'),' ');
    assert.throws(()=>readRelease(f.dir),/RELEASE_ARTIFACT_CHANGED/);
    const r=runGate(f,receipt);assert.notEqual(r.status,0);assert.match(r.stderr,/inventory/i);
  }finally{f.cleanup();}
});
test('unsafe or incomplete artifact index is refused without reading outside the release',()=>{
  const f=fixture();try {
    const index=path.join(f.dir,'release.sha256'),original=fs.readFileSync(index,'utf8');
    for(const bad of [original+'a'.repeat(64)+'  ../outside\n',original+original.split('\n')[0]+'\n',original.replace(/.*  compose.json\n/,'')]) {
      fs.writeFileSync(index,bad);assert.throws(()=>readRelease(f.dir),/INVALID_RELEASE_INDEX|INCOMPLETE_RELEASE_INDEX/);
    }
  }finally{f.cleanup();}
});
