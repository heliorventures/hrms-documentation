import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,access} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const doc=path.resolve(fileURLToPath(new URL('../..',import.meta.url)));
const canonical=path.join(doc,'docs/architecture/2026-10-18-organization-cross-company-management.html');
test('architecture and mirrors preserve IDs, local links and unchanged frozen baseline',async()=>{
  for(const file of [canonical,path.join(doc,'docs/superpowers/specs/2026-10-18-organization-cross-company-management.html'),path.resolve(doc,'../docs/superpowers/specs/2026-10-18-organization-cross-company-management.html')]) {
    const body=await readFile(file,'utf8');const ids=[...body.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
    assert.equal(new Set(ids).size,ids.length,`duplicate ID: ${file}`);
    assert(ids.includes('infrastructure-ownership'));
    for(const [,href]of body.matchAll(/href="([^"]+)"/g)) {
      if(/^[a-z]+:/i.test(href))continue;
      if(href.startsWith('#')){assert(ids.includes(href.slice(1)),`missing anchor ${href}`);continue;}
      const target=path.resolve(path.dirname(file),href.split('#')[0]);
      await assert.doesNotReject(access(target),`missing local reference ${href} in ${file}`);
    }
  }
  const frozen=await readFile(path.join(doc,'docs/superpowers/specs/2026-10-19-organization-recorded-baseline.html'));
  assert.equal(createHash('sha256').update(frozen).digest('hex'),'ae0e0aa8df303f62ce6cd85e840204e76c251b37f73265f65570792bdc2ef1e4');
});
