import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {render} from './render.mjs';
test('Compose CLI parses the bound application layout and shared platform without a Docker daemon',async()=>{
  const folder=await mkdtemp(path.join(tmpdir(),'hrms-compose-'));
  try{
    const fixture=JSON.parse(await readFile(new URL('../../deploy/hrms/manifest.example.json',import.meta.url),'utf8'));
    for(const mode of ['organization']) {
      const files=render({...fixture,mode});const compose=JSON.parse(files['compose.json']);
      // Temporary operator env fixtures only. Linux production paths stay unchanged in renderer output.
      for(const [name,service] of Object.entries(compose.services))if(service.env_file){
        const local=path.join(folder,`dummy-${name}.env`);
        await writeFile(local,'SYNTHETIC_ONLY=true\n');service.env_file=[local];
      }
      const manifest=path.join(folder,`compose-${mode}.json`);await writeFile(manifest,JSON.stringify(compose));
      const r=spawnSync('docker',['compose','--file',manifest,'config','--quiet'],{encoding:'utf8',timeout:30000,windowsHide:true});
      assert.equal(r.status,0,`${mode}: ${r.stderr??r.error?.message}`);
    }
    const env={...process.env,POSTGRES_USER:'synthetic',POSTGRES_PASSWORD:'synthetic-only',POSTGRES_DB:'synthetic',MONGO_INITDB_ROOT_USERNAME:'synthetic',MONGO_INITDB_ROOT_PASSWORD:'synthetic-only'};
    const r=spawnSync('docker',['compose','--file',fileURLToPath(new URL('../../deploy/platform/compose.yaml',import.meta.url)),'config','--quiet'],{env,encoding:'utf8',timeout:30000,windowsHide:true});
    assert.equal(r.status,0,r.stderr??r.error?.message);
  }finally{await rm(folder,{recursive:true,force:true});}
});
