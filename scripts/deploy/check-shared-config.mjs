// Read-only release preflight. Never prints operator configuration or secrets.
import {readFile,stat} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const requireValue=(ok)=>{if(!ok)throw Error('Shared company configuration is incomplete or inconsistent');};
async function json(file){return JSON.parse(await readFile(file,'utf8'));}
export async function checkSharedConfig(root){
  requireValue(root&&path.isAbsolute(root));
  const release=await json(path.join(root,'release.json'));
  const {services}=await json(path.join(root,'compose.json'));
  requireValue(release.applicationLayout==='shared');
  const expected=new Map(release.companyBindings.map(c=>[c.id,c]));
  const locations=new Map(),serviceUsers=new Set();let registryServer,catalogVersion;
  for(const [name,service] of Object.entries(services)){
    if(!service.environment?.KABIPAY_COMPANY_CONFIG_FILE)continue;
    const resolve=target=>{
      const mounts=service.volumes.filter(v=>v.type==='bind'&&(target===v.target||target.startsWith(v.target+'/')))
        .sort((a,b)=>b.target.length-a.target.length);
      requireValue(mounts.length>0);
      const mount=mounts[0],relative=target.slice(mount.target.length).replace(/^\//,'');
      requireValue(!relative.split('/').includes('..'));
      return path.join(mount.source,relative);
    };
    const config=await json(resolve(service.environment.KABIPAY_COMPANY_CONFIG_FILE));
    requireValue([1,2].includes(config.version)&&Array.isArray(config.companies)&&config.companies.length===expected.size);
    requireValue(!catalogVersion||catalogVersion===config.version);catalogVersion=config.version;
    if(config.version===2){
      const database=await json(resolve(service.environment.KABIPAY_COMPANY_DATABASE_FILE??''));
      requireValue(database.version===1&&typeof database.server_url==='string');
      requireValue(typeof database.database_prefix==='string'&&/^[a-z_][a-z0-9_]{0,30}_$/.test(database.database_prefix)&&!database.database_prefix.startsWith('pg_'));
      const url=new URL(database.server_url);
      const allowed=new Set(['sslmode','sslrootcert','ssl-root-cert','ssl-ca','sslcert','ssl-cert','sslkey','ssl-key','statement-cache-capacity','application_name']);
      requireValue(['postgres:','postgresql:'].includes(url.protocol)&&url.hostname&&url.username&&decodeURIComponent(url.username)!=='postgres'&&url.password&&url.pathname.length>1&&!url.hash);
      requireValue(url.searchParams.getAll('sslmode').length===1&&url.searchParams.get('sslmode')==='verify-full'&&[...url.searchParams.keys()].every(k=>allowed.has(k)));
      const server=JSON.stringify([url.hostname,url.port||'5432',database.database_prefix]);
      requireValue(!registryServer||registryServer===server);registryServer=server;
      const user=JSON.stringify([url.hostname,url.port||'5432',decodeURIComponent(url.username)]);
      requireValue(!serviceUsers.has(user));serviceUsers.add(user);
    }else requireValue(!service.environment.KABIPAY_COMPANY_DATABASE_FILE);
    const seen=new Set(),users=new Set(),databases=new Set();
    for(const company of config.companies){
      requireValue(expected.has(company.tenant_id)&&!seen.has(company.tenant_id));seen.add(company.tenant_id);
      requireValue(company.public_origin===`https://${expected.get(company.tenant_id).publicHost}`);
      if(config.version===2){
        requireValue(!Object.hasOwn(company,'database_url')&&!Object.hasOwn(company,'schema'));
        locations.set(company.tenant_id,'registry');
      }else{
      const db=new URL(company.database_url),location=`${db.hostname}:${db.port||5432}${db.pathname}`;
      requireValue(['postgres:','postgresql:'].includes(db.protocol)&&db.username&&db.password&&db.pathname.length>1);
      requireValue(db.searchParams.getAll('sslmode').length===1&&db.searchParams.get('sslmode')==='verify-full'&&!db.searchParams.has('ssl-mode')&&/^[a-zA-Z_][a-zA-Z0-9_]{0,62}$/.test(company.schema));
      requireValue(!databases.has(location)&&!users.has(`${db.host}/${db.username}`));
      databases.add(location);users.add(`${db.host}/${db.username}`);
      const binding=JSON.stringify([location,company.schema]);
      requireValue(!locations.has(company.tenant_id)||locations.get(company.tenant_id)===binding);
      locations.set(company.tenant_id,binding);
      }
      const settings=company.settings??{},required=[];
      const role=name.replace(/^shared-/,'');
      if(role==='auth')required.push('KABIPAY_CLIENT_JWT_KEY_ID','KABIPAY_CLIENT_JWT_PRIVATE_KEY_FILE');
      if(['employee','leave','attendance','expense','notification','survey','analytics','maintenance'].includes(role))required.push('KABIPAY_PRIVATE_EVENT_KEYS_FILE');
      if(['survey','analytics'].includes(role))required.push('KABIPAY_PRIVATE_HISTORY_CLIENT_FILE','KABIPAY_PRIVATE_HISTORY_CLIENT_CERT_FILE','KABIPAY_PRIVATE_HISTORY_CLIENT_KEY_FILE');
      if(role==='analytics')required.push('KABIPAY_PRIVATE_DELIVERY_HISTORY_CLIENT_FILE');
      if(role==='employee')required.push('KABIPAY_PRIVATE_DELIVERY_ADAPTER_FILE','KABIPAY_PRIVATE_DELIVERY_BROKER_OWNER_ID');
      for(const key of required)requireValue(typeof settings[key]==='string'&&settings[key].length>0);
      for(const [key,value] of Object.entries(settings))if(key.endsWith('_FILE')){
        requireValue(typeof value==='string'&&value.startsWith(`/run/companies/${company.tenant_id}/`));
        requireValue((await stat(resolve(value))).isFile());
      }
    }
  }
  requireValue(locations.size===expected.size);
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))try{
  await checkSharedConfig(process.argv[2]);
  console.log('Shared company configuration preflight passed; database reachability and runtime acceptance remain separate.');
}catch{
  console.error('Shared company configuration preflight failed. Check the protected per-service files, company inventory, TLS and secret mounts. Values were not logged.');
  process.exitCode=1;
}
