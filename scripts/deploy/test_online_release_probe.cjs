// Actual fixed Node probe program with mocked fetch; no network or subprocesses.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {EventEmitter}=require('node:events');
const source=fs.readFileSync(path.join(__dirname,'online-release.py'),'utf8');
const code=/PROBE = r"""([\s\S]*?)"""/.exec(source)[1];
const negative={kind:'http',url:'http://synthetic/graphql',method:'POST',query:'query ReleaseOpsBoundary { tenants(limit:1) { id } }',expectedStatus:200,expectedErrorCodes:['FORBIDDEN']};
async function run(spec,value,status=200){
 let out='',err='';
 const stdin=new EventEmitter();
 let done;
 const completion=new Promise(resolve=>{done=()=>setImmediate(resolve);});
 const process={stdin,stdout:{write:v=>{out+=v;done();}},stderr:{write:v=>{err+=v;done();}},exitCode:0};
 const response=JSON.stringify(value);
 const fetch=async(url,options)=>{assert.equal(url,spec.url);assert.equal(options.method,spec.method);assert.equal(options.redirect,'error');return {status,text:async()=>response};};
 vm.runInNewContext(code,{process,fetch,AbortSignal,require});
 stdin.emit('data',JSON.stringify(spec));stdin.emit('end');await completion;
 assert(!out.includes('private-sentinel')&&!err.includes('private-sentinel'));
 return {out,err,exitCode:process.exitCode};
}
(async()=>{
 const denied={data:null,errors:[{message:'private-sentinel',extensions:{code:'FORBIDDEN'}}]};
 assert.equal((await run(negative,denied)).out,'{"ok":true}');
 for(const value of [
  {data:{tenants:[]},errors:denied.errors},{errors:denied.errors},{data:null,errors:[]},
  {data:null,errors:[{extensions:{code:'UNAUTHENTICATED'}}]},
  {data:null,errors:[{message:'private-sentinel'}]},
  {data:null,errors:[...denied.errors,...denied.errors]},
 ])assert.equal((await run(negative,value)).exitCode,1);
 const ordered={...negative,expectedErrorCodes:['FORBIDDEN','UNAUTHENTICATED']};
 const both={data:null,errors:[...denied.errors,{extensions:{code:'UNAUTHENTICATED'}}]};
 assert.equal((await run(ordered,both)).out,'{"ok":true}');
 assert.equal((await run(ordered,{...both,errors:[...both.errors].reverse()})).exitCode,1);
 assert.equal((await run(negative,denied,403)).exitCode,1);
 const positive={...negative};delete positive.expectedErrorCodes;
 positive.expectedText=JSON.stringify(denied);
 assert.equal((await run(positive,denied)).exitCode,1,'positive response must reject GraphQL errors even if exact text matches');
 const allowed={data:{tenants:[]}};positive.expectedText=JSON.stringify(allowed);
 assert.equal((await run(positive,allowed)).out,'{"ok":true}');
 console.log('PASS: fixed Node program enforces exact ordered negative error codes/data:null/status, rejects positive GraphQL errors, exports no error/body; mocked fetch only');
})().catch(error=>{console.error(error);process.exitCode=1;});
