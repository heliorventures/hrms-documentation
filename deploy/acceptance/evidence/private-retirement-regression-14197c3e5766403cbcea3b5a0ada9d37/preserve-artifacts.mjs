import fs from 'node:fs';
import {resolve,dirname,basename,join} from 'node:path';
import {tmpdir} from 'node:os';
import {syncBuiltinESMExports} from 'node:module';
const root=resolve(process.env.PRIVATE_REGRESSION_EVIDENCE_ROOT),remove=fs.rmSync;
if(!root.endsWith('private-retirement-regression-14197c3e5766403cbcea3b5a0ada9d37'))throw Error('REGRESSION_EVIDENCE_BOUNDARY');
fs.rmSync=function(path,options){const source=resolve(String(path));if(dirname(source)===resolve(tmpdir())&&/^(org-gap-|control-retention-|kabipay-control-)/.test(basename(source))&&fs.existsSync(source)){const target=join(root,'filesystem',basename(source));fs.mkdirSync(dirname(target),{recursive:true});fs.cpSync(source,target,{recursive:true,errorOnExist:true,force:false});console.log(JSON.stringify({synthetic_artifacts_preserved:basename(source)}));}return remove(path,options);};
syncBuiltinESMExports();
