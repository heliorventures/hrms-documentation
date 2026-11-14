import assert from 'node:assert/strict';
import test from 'node:test';
import {readFileSync} from 'node:fs';
import {render} from './render.mjs';
const fixture=JSON.parse(readFileSync(new URL('../../deploy/hrms/manifest.example.json',import.meta.url)));
test('only Employee receives the preserved profile encryption environment',()=>{
  const {services}=JSON.parse(render(fixture)['compose.json']);
  const file=`${fixture.appDir}/env/shared/employee-profile.env`;
  assert.deepEqual(Object.entries(services).filter(([,s])=>s.env_file?.includes(file)).map(([name])=>name),['shared-employee']);
  assert.equal(services['shared-employee'].env_file.at(-1),`${fixture.appDir}/env/metadata/employee.env`);
  assert(!Object.values(render(fixture)).some(content=>content.includes('KABIPAY_PROFILE_CHANGE_ENCRYPTION_KEY=')));
});
