import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {spawnSync} from 'node:child_process';import {createHash} from 'node:crypto';import {fileURLToPath} from 'node:url';
test('image-only release verifies exact archives and does not require legacy worker retirement',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'hrms-load-'));const posix=v=>v.replaceAll('\\','/').replace(/^([A-Za-z]):/,(_,d)=>'/'+d.toLowerCase());
 try{
  const sums=[];
  for(const name of ['svc','gateway','ui','organization-events']){const file=`kabipay-${name}-synthetic.tar`;const content=`test ${name}`;fs.writeFileSync(path.join(dir,file),content);sums.push(createHash('sha256').update(content).digest('hex')+'  '+file);}
  fs.writeFileSync(path.join(dir,'SHA256SUMS'),sums.join('\r\n')+'\r\n');
  const script=fileURLToPath(new URL('./release.sh',import.meta.url));
  const wrapper=path.join(dir,'run.sh');
  fs.writeFileSync(wrapper,`#!/usr/bin/env bash\nset -eu\ndocker() { if [ "$1" = ps ]; then echo old-worker; fi; }\npython3() { [ "$4" = --load ] || exit 1; printf 'loaded\\nloaded\\nloaded\\nloaded\\n' > '${posix(dir)}/loads'; }\nexport -f docker python3\nbash '${posix(script)}' '${posix(dir)}' '${posix(dir)}' synthetic 1 0 0 organization\n`);
  const run=()=>spawnSync(process.platform==='win32'?'C:/Program Files/Git/bin/bash.exe':'bash',['--noprofile','--norc',posix(wrapper)],{encoding:'utf8',windowsHide:true});
  let result=run();assert.ifError(result.error);assert.equal(result.status,0,result.stderr);assert.equal(fs.readFileSync(path.join(dir,'loads'),'utf8').trim().split('\n').length,4);
  fs.unlinkSync(path.join(dir,'loads'));fs.appendFileSync(path.join(dir,'kabipay-svc-synthetic.tar'),'changed');
  result=run();assert.notEqual(result.status,0);assert(!fs.existsSync(path.join(dir,'loads')),'Corrupt release loaded some images');
 }finally{assert.equal(path.dirname(fs.realpathSync(dir)),fs.realpathSync(os.tmpdir()));assert.match(path.basename(dir),/^hrms-load-/);fs.rmSync(dir,{recursive:true});}
});
