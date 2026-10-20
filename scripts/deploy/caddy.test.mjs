import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn,spawnSync} from 'node:child_process';
import {createServer} from 'node:http';
import {mkdtemp,writeFile,readFile,rm,mkdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {once} from 'node:events';
import {render,publicRoutes} from './render.mjs';

const binary=process.env.CADDY_BINARY;
for(const plane of ['ops','company'])test(`actual Caddy ${plane} routes deny unauthorized paths before proxying`, {skip:!binary},async()=>{
  const folder=await mkdtemp(path.join(tmpdir(),'hrms-caddy-'));
  let hits=0,processHandle;
  const upstream=createServer((req,res)=>{hits++;res.writeHead(200,{'content-type':'text/plain'});res.end('synthetic-upstream');});
  const reservation=createServer();
  try {
    upstream.listen(0,'127.0.0.1');await once(upstream,'listening');
    reservation.listen(0,'127.0.0.1');await once(reservation,'listening');const port=reservation.address().port;await new Promise(r=>reservation.close(r));
    const address=`127.0.0.1:${upstream.address().port}`;
    const file=path.join(folder,'Caddyfile');
    await writeFile(file,`{\n admin off\n auto_https off\n}\nhttp://127.0.0.1:${port} {\n${publicRoutes({plane,auth:address,gateway:address,employee:address,notification:address,ui:address})}}\n`);
    const validation=spawnSync(binary,['validate','--config',file,'--adapter','caddyfile'],{encoding:'utf8',timeout:15000,windowsHide:true});
    assert.equal(validation.status,0,validation.stderr);
    processHandle=spawn(binary,['run','--config',file,'--adapter','caddyfile'],{stdio:'ignore',windowsHide:true});
    let ready=false;
    for(let i=0;i<60;i++){try{const r=await fetch(`http://127.0.0.1:${port}/healthz`,{signal:AbortSignal.timeout(500)});if(r.status===200){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,100));}
    assert(ready,'synthetic Caddy did not become ready');
    const companyPaths=['/prejoining-api','/prejoining-api/example','/files/employee-document','/files/employee-document/example','/files/announcement-video','/files/announcement-video/example'];
    for(const url of ['/internal','/internal/organization/command','/auth/internal','/auth/internal/account-eligibility','/auth/client/organization-identity',...(plane==='ops'?companyPaths:[])]) {
      const before=hits;const r=await fetch(`http://127.0.0.1:${port}${url}`,{method:'POST',headers:{authorization:'Bearer synthetic'},signal:AbortSignal.timeout(3000)});
      assert.equal(r.status,404,url);assert.equal(hits,before,'denied path reached upstream');
    }
    for(const url of ['/graphql','/auth/client/login','/auth/ops/login','/healthz','/ui-route',...(plane==='company'?companyPaths:[])]) {
      const r=await fetch(`http://127.0.0.1:${port}${url}`,{signal:AbortSignal.timeout(3000)});assert.equal(r.status,200,url);assert.equal(await r.text(),'synthetic-upstream');
    }
  }finally {
    if(processHandle && processHandle.exitCode===null){processHandle.kill();await Promise.race([once(processHandle,'exit'),new Promise(r=>setTimeout(r,3000))]);}
    upstream.closeAllConnections();await new Promise(r=>upstream.close(r));
    reservation.close();await rm(folder,{recursive:true,force:true});
  }
});

test('all generated Caddy files and canonical root imports adapt with the real parser',{skip:!binary},async()=>{
  const folder=await mkdtemp(path.join(tmpdir(),'hrms-caddy-adapt-'));
  try {
    const manifest=JSON.parse(await readFile(new URL('../../deploy/hrms/manifest.example.json',import.meta.url),'utf8'));
    const files=render(manifest);const normalized=folder.replaceAll('\\','/');
    for(const [relative,body] of Object.entries(files).filter(([name])=>name.startsWith('caddy/'))){
      const target=path.join(folder,path.basename(relative));await writeFile(target,body);
      if(!['legacy-routes.caddy','company-sites.caddy'].includes(path.basename(relative))) {
        const r=spawnSync(binary,['adapt','--config',target,'--adapter','caddyfile'],{encoding:'utf8',timeout:15000,windowsHide:true});assert.equal(r.status,0,`${relative}: ${r.stderr}`);
      }
    }
    const root=(await readFile(new URL('../../deploy/Caddyfile.example',import.meta.url),'utf8')).replaceAll('/etc/caddy/hrms',normalized);
    const rootFile=path.join(folder,'RootCaddyfile');await writeFile(rootFile,root);
    const r=spawnSync(binary,['adapt','--config',rootFile,'--adapter','caddyfile'],{encoding:'utf8',timeout:15000,windowsHide:true});assert.equal(r.status,0,r.stderr);
    const parsed=JSON.parse(r.stdout);assert(parsed.apps.http.servers);
  }finally {await rm(folder,{recursive:true,force:true});}
});
