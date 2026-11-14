// Actual native Bash startup/validation, mocked Docker only. No daemon or VPS.
import test from'node:test';import assert from'node:assert/strict';import fs from'node:fs';import os from'node:os';import path from'node:path';import{spawnSync}from'node:child_process';import{fileURLToPath}from'node:url';import{createHash}from'node:crypto';
import{render}from'./render.mjs';import{validateStartup}from'./startup-scope.mjs';import operator from'../../../hrms-database/provisioning/organization/check-rollout.cjs';
const root=path.dirname(fileURLToPath(import.meta.url)),posix=v=>v.replaceAll('\\','/').replace(/^([A-Za-z]):/,(_,d)=>'/'+d.toLowerCase());
function run(mode){
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'hrms-startup-'));
 try{
  const c=JSON.parse(fs.readFileSync(path.join(root,'../../deploy/hrms/manifest.example.json')));c.databasePools.applicationBudget=120;c.companies=Array.from({length:5},(_,i)=>({id:`00000000-0000-4000-8000-00000000000${i+1}`,slug:`company-${i+1}`,clientJwtKeyId:`company-${i+1}-v1`,publicHost:`company-${i+1}.${c.tenantBaseDomain}`,privateFilesPath:`${c.appDir}/data/company-${i+1}/private-files`}));c.privateHistoryCompanyIds=c.companies.slice(0,3).map(v=>v.id);
  const files=render(c),release=JSON.parse(files['release.json']),composition=JSON.parse(files['compose.json']),scope=validateStartup(release,composition,files['startup-services.txt'],JSON.parse(files['compose-active.json']));
  const directories=c.companies.map((_,i)=>path.join(dir,'data-'+i));directories.forEach(d=>fs.mkdirSync(d));files['private-files.txt']=directories.map(posix).join('\n')+'\n';files['finance-checks.txt']='';files['release.sha256']=Object.entries(files).filter(([n])=>n!=='release.sha256').map(([n,b])=>createHash('sha256').update(b).digest('hex')+'  '+n).join('\n')+'\n';
  for(const[n,b]of Object.entries(files)){fs.mkdirSync(path.dirname(path.join(dir,n)),{recursive:true});fs.writeFileSync(path.join(dir,n),b)}
  fs.mkdirSync(path.join(dir,'scripts'));fs.copyFileSync(path.join(root,'check-inventory.sh'),path.join(dir,'scripts/check-inventory.sh'));const receipt=operator.checkRegistry(operator.readRelease(dir),c.companies.map(v=>({id:v.id,subdomain:v.slug,status:'ACTIVE',is_deleted:false})));fs.writeFileSync(path.join(dir,'cutover-inventory.txt'),receipt);
  fs.writeFileSync(path.join(dir,'scope.txt'),scope.all.map(n=>[scope.active.includes(n)?'active':'inactive',n,composition.services[n].image].join('|')).join('\n')+'\n');
  const shell=String.raw`set -euo pipefail
cd "$TEST_ROOT"
docker() {
 if [ "$1" = run ]; then case "$*" in *startup-scope.mjs*) cat scope.txt;; esac; return 0; fi
 if [ "$1" = image ]; then
  case "$*" in *io.kabipay.ui.organization-workspace*) if [ "$TEST_MODE" = ui-disabled ]; then printf 'false\n'; else printf 'true\n'; fi;;
  *) printf 'sha256:%s\n' "$TEST_IMAGE";; esac
  return 0
 fi
 if [ "$1" = ps ]; then
  if [ "$TEST_MODE" = inactive ]; then case "$*" in *service=private-audit-company-4*) printf 'abcdef123456\n';; esac; fi
  return 0
 fi
 if [ "$1" = inspect ]; then
  if [ "$TEST_MODE" = wrong-image ]; then printf 'running|sha256:%064d\n' 0; else printf 'running|sha256:%s\n' "$TEST_IMAGE"; fi
  return 0
 fi
 if [ "$1" = compose ]; then
  case "$*" in
   *' up '*) printf '%s\n' "$@" > started-args;;
   *' ps '*) for arg; do service="$arg"; done; printf '%s\n' "$service" >> validated; printf 'abcdef123456\n';;
  esac
  return 0
 fi
 return 70
}
sleep() { return 99; }
export -f docker sleep
bash "$TEST_SCRIPT" "$TEST_ROOT" "$TEST_ROOT/images" "$TEST_TAG" 0 1 1 organization
`;
  const r=spawnSync(process.platform==='win32'?'C:/Program Files/Git/bin/bash.exe':'bash',['--noprofile','--norc','-s'],{input:shell,encoding:'utf8',timeout:60000,windowsHide:true,env:{...process.env,MSYS_NO_PATHCONV:'1',TEST_ROOT:posix(dir),TEST_SCRIPT:posix(path.join(root,'release.sh')),TEST_TAG:c.tag,TEST_MODE:mode,TEST_IMAGE:'a'.repeat(64)}});assert.ifError(r.error);
  if(mode==='inactive'){assert.notEqual(r.status,0);assert.match(r.stderr,/inactive private worker/);assert(!fs.existsSync(path.join(dir,'started-args')));return;}
  if(mode==='ui-disabled'){assert.notEqual(r.status,0);assert.match(r.stderr,/organization workspace/);assert(!fs.existsSync(path.join(dir,'started-args')));return;}
  const args=fs.readFileSync(path.join(dir,'started-args'),'utf8').trim().split('\n');assert.deepEqual(args.slice(args.indexOf('never')+1),scope.active);assert(args.includes('--no-deps'));assert(!args.some(v=>scope.inactive.includes(v)));
  const validated=fs.readFileSync(path.join(dir,'validated'),'utf8').trim().split('\n');assert.deepEqual(validated,scope.active);
  if(mode==='wrong-image'){assert.notEqual(r.status,0);assert.doesNotMatch(r.stdout,/HRMS containers running/)}else{assert.equal(r.status,0,r.stderr);assert.match(r.stdout,/HRMS containers running/)}
 }finally{assert.equal(path.dirname(fs.realpathSync(dir)),fs.realpathSync(os.tmpdir()));assert.match(path.basename(dir),/^hrms-startup-/);fs.rmSync(dir,{recursive:true,force:true})}
}
test('native release starts and validates exactly 45 selected services, retains five file roots',()=>run('success'));
test('running inactive worker blocks before any application startup',()=>run('inactive'));
test('running selected service on wrong image cannot pass readiness',()=>run('wrong-image'));
test('organization release refuses a saved UI image compiled without its workspace',()=>run('ui-disabled'));
