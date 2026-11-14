// Explicit private source activation is separate from the complete company fleet.
import {readFileSync,lstatSync,realpathSync} from 'node:fs';
import {fileURLToPath} from 'node:url';import path from 'node:path';
import {isDeepStrictEqual} from 'node:util';
const business=['employee','leave','attendance','payroll','tax','benefits','expense','recruitment','performance','lms','succession','compensation','assets','grievance','workflow','notification','analytics','survey'];
const mandatory=[...business.map(n=>'shared-'+n),...['auth','maintenance','gateway','ui','ingress','source'].map(n=>'shared-'+n),'kabipay-auth','kabipay-subgraphs','kabipay-gateway','kabipay-ui','organization','organization-internal','inbox-worker','history-worker','reporting-worker','capture-coordinator','control-history-worker','archive','private-operator-audit','private-audit-history','private-delivery-history'];
const need=(ok,message)=>{if(!ok)throw Error(message)};
const same=(a,b)=>Array.isArray(a)&&a.length===b.length&&new Set(a).size===a.length&&[...a].sort().every((v,i)=>v===[...b].sort()[i]);
export function privateActivation(companies,ids){
 need(Array.isArray(ids)&&ids.every(id=>typeof id==='string'&&companies.some(c=>c.id===id))&&new Set(ids).size===ids.length,'Explicit private history activation requires unique known company UUIDs');
 return [...ids].sort();
}
export function startupScope(companies,ids,services){
 need(Array.isArray(companies)&&companies.length>0&&companies.length<=100&&companies.every(c=>/^[a-z][a-z0-9-]{0,30}$/.test(c.slug??'')&&/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(c.id??''))&&new Set(companies.map(c=>c.id)).size===companies.length&&new Set(companies.map(c=>c.slug)).size===companies.length,'Invalid complete company startup inventory');
 const selected=privateActivation(companies,ids),pairs=companies.flatMap(c=>['audit','delivery'].map(p=>({name:`private-${p}-${c.slug}`,active:selected.includes(c.id)})));
 const all=[...mandatory,...pairs.map(p=>p.name)].sort();
 need(services&&same(Object.keys(services),all),'Compose service inventory differs from canonical startup groups');
 const active=[...mandatory,...pairs.filter(p=>p.active).map(p=>p.name)].sort(),inactive=pairs.filter(p=>!p.active).map(p=>p.name).sort();
 for(const [name,s]of Object.entries(services))need(!s.depends_on,'Startup dependencies require explicit policy review');
 return {active,inactive,all,privateHistoryCompanyIds:selected};
}
export function activeCompose(compose,active){return {...compose,services:Object.fromEntries(active.map(name=>[name,compose.services[name]]))};}
export function validateStartup(release,compose,text,selectedCompose){
 need(release.version===1&&release.mode==='organization'&&release.applicationLayout==='shared','Shared release startup contract required');
 const scope=startupScope(release.companyBindings,release.privateHistoryCompanyIds,compose.services);
 need(same(release.services,scope.all)&&same(release.activeServices,scope.active)&&text===scope.active.join('\n')+'\n','Rendered startup service selection differs from release policy');
 need(isDeepStrictEqual(selectedCompose,activeCompose(compose,scope.active)),'Active Compose model differs from the exact reviewed selection');
 for(const name of scope.inactive)need(same(compose.services[name].profiles,['inactive-private-history']),'Inactive private worker profile required');
 for(const name of scope.active)need(!compose.services[name].profiles,'Selected service must not have an alternate activation profile');
 for(const name of scope.all)need(typeof compose.services[name].image==='string'&&/^[a-zA-Z0-9_./:@-]+$/.test(compose.services[name].image),'Invalid startup image reference');
 return scope;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{
  const [directory]=process.argv.slice(2);need(directory&&path.isAbsolute(directory)&&realpathSync(directory)===directory,'Canonical release directory required');
  const read=name=>{const file=path.join(directory,name),s=lstatSync(file);need(s.isFile()&&!s.isSymbolicLink()&&s.size<=4*1024*1024&&realpathSync(file)===file,'Regular bounded startup artifact required');return readFileSync(file,'utf8')};
  const release=JSON.parse(read('release.json')),compose=JSON.parse(read('compose.json')),scope=validateStartup(release,compose,read('startup-services.txt'),JSON.parse(read('compose-active.json')));
  process.stdout.write(scope.all.map(name=>[scope.active.includes(name)?'active':'inactive',name,compose.services[name].image].join('|')).join('\n')+'\n');
 }catch{console.error('Explicit startup scope is missing or inconsistent; render and review the release again.');process.exitCode=1;}
}
