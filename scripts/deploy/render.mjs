import {readFile, mkdir, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {createHash} from 'node:crypto';

const tenantServices = {employee:4013, leave:4014, attendance:4015, payroll:4016, tax:4017,
  benefits:4018, expense:4019, recruitment:4020, performance:4021, lms:4022, succession:4023,
  compensation:4024, assets:4025, grievance:4026, workflow:4027, notification:4028, analytics:4029, survey:4030};
const commandServices = ['employee','leave','attendance','payroll','performance','workflow'];
const hostPattern = /^(?=.{1,253}$)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$/;
const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const mount = (source,target,readOnly=true) => ({type:'bind',source,target,read_only:readOnly,bind:{create_host_path:false}});
function required(condition, message) { if (!condition) throw Error(message); }
function host(value) { required(typeof value==='string' && hostPattern.test(value) && value.split('.').every(label=>/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(label)), 'Invalid public hostname'); return value; }
function safePath(value) { required(typeof value==='string' && /^\/[a-zA-Z0-9_./-]+$/.test(value) && !value.split('/').includes('..'), 'Invalid absolute deployment path'); return path.posix.normalize(value).replace(/\/$/,''); }

export function validate(config) {
  required(config && config.version===1 && config.mode==='organization', 'This release requires the bound company layout; use the previous release artifacts for rollback');
  required(/^[a-zA-Z0-9_.-]+$/.test(config.tag??''), 'Invalid image tag');
  const appDir=safePath(config.appDir??'/opt/apps/hrms');
  const platformDir=safePath(config.platformDir??'/opt/apps');
  required(appDir.startsWith(`${platformDir}/`) && appDir!==platformDir, 'HRMS must have its own directory under platformDir');
  const network=config.appNetwork??'apps_app-network';
  required(/^[a-zA-Z0-9_.-]+$/.test(network), 'Invalid shared network');
  host(config.publicHost); host(config.apiHost??config.publicHost);
  required(Array.isArray(config.companies) && config.companies.length>0 && config.companies.length<=100, 'Configure 1..100 companies');
  const ids=new Set(), slugs=new Set(), hosts=new Set([config.publicHost,config.apiHost??config.publicHost]), storage=[];
  for(const c of config.companies) {
    required(uuidPattern.test(c.id??'') && !ids.has(c.id), 'Invalid/duplicate company UUID'); ids.add(c.id);
    required(/^[a-z][a-z0-9-]{0,30}$/.test(c.slug??'') && !slugs.has(c.slug), 'Invalid/duplicate company slug'); slugs.add(c.slug);
    host(c.publicHost); required(!hosts.has(c.publicHost),'Duplicate public host'); hosts.add(c.publicHost);
    required(c.publicHost===`${c.slug}.${host(config.tenantBaseDomain)}`, 'Company hostname must match tenant slug and base domain');
    c.privateFilesPath=safePath(c.privateFilesPath);
    required(c.privateFilesPath.startsWith(`${appDir}/data/`) || c.privateFilesPath.startsWith(`${platformDir}/data/private-files/`),'Company files must use an explicit company data directory');
    required(!storage.some(p=>p===c.privateFilesPath || p.startsWith(`${c.privateFilesPath}/`) || c.privateFilesPath.startsWith(`${p}/`)),'Company private file paths must not overlap');
    storage.push(c.privateFilesPath);
  }
  return {...config,appDir,platformDir,appNetwork:network,apiHost:config.apiHost??config.publicHost};
}

// One route grammar with an explicit operator or bound company plane.
// Source command/policy, Auth eligibility and archive APIs never enter this list.
export function publicRoutes({plane,auth,gateway,employee,notification,ui}) {
  required(plane==='ops' || plane==='company', 'Invalid public route plane');
  const companyRoutes=plane==='company' ?
    `handle /prejoining-api/* {\n header Cache-Control "private, no-store"\n header Referrer-Policy "no-referrer"\n header X-Content-Type-Options "nosniff"\n request_body {\n max_size 10MiB\n }\n reverse_proxy ${employee}\n}\n`+
    `handle /files/announcement-video/* {\n request_body {\n max_size 50MiB\n }\n reverse_proxy ${notification}\n}\n`+
    `handle /files/employee-document* {\n reverse_proxy ${employee}\n}\n` : '';
  return `route {\n@private path /internal /internal/* /auth/internal /auth/internal/* /auth/client/organization-identity\nrespond @private 404\n`+
    (plane==='ops' ? `@company path /prejoining-api /prejoining-api/* /files/employee-document* /files/announcement-video /files/announcement-video/*\nrespond @company 404\n` : '')+
    `handle /graphql* {\n reverse_proxy ${gateway}\n}\nhandle /auth/* {\n reverse_proxy ${auth}\n}\n`+
    companyRoutes+`handle /healthz {\n reverse_proxy ${auth}\n}\nhandle {\n reverse_proxy ${ui}\n}\n}\n`;
}

export function render(input) {
  const c=validate(input), files={}, services={}, networks={
    'app-network':{external:true,name:c.appNetwork},
  };
  const cfg=`${c.appDir}/config`, secrets=`${c.appDir}/secrets`;
  const runtime = (command,envFile,nets,environment={},volumes=[]) => ({
    image:`kabipay-svc:${c.tag}`,command:[command],env_file:[envFile],environment,
    restart:'unless-stopped',init:true,read_only:true,tmpfs:['/tmp'],networks:nets,volumes,
    logging:{driver:'json-file',options:{'max-size':'10m','max-file':'3'}},
  });
  const env=(name)=>`${c.appDir}/env/${name}.env`;
  const image=(name)=>`kabipay-${name}:${c.tag}`;
  services['kabipay-auth']=runtime('kabipay-auth',env('ops-auth'),['app-network','metadata'],{KABIPAY_AUTH_PLANE:'ops'});
  services['kabipay-subgraphs']=runtime('kabipay-ops',env('ops'),['app-network','metadata']);
  services['kabipay-gateway']={image:image('gateway'),restart:'unless-stopped',networks:['app-network'],environment:{NODE_ENV:'production',KABIPAY_SUBGRAPH_BASE_URL:'http://kabipay-subgraphs',KABIPAY_ORGANIZATION_ENABLED:'false',KABIPAY_ALLOW_PARTIAL_SUBGRAPHS:'false'}};
  services['kabipay-ui']={image:image('ui'),restart:'unless-stopped',networks:['app-network'],volumes:[mount(`${cfg}/ui-config.json`,'/usr/share/nginx/html/config.json'),mount(`${c.appDir}/media/video-guides`,'/srv/video-guides')]};
  files['config/ui-config.json']=JSON.stringify({gatewayUrl:`https://${c.apiHost}/graphql`,authUrl:`https://${c.apiHost}`,tenantBaseDomain:c.tenantBaseDomain},null,2);
  const opsRoutes=publicRoutes({plane:'ops',auth:'kabipay-auth:4001',gateway:'kabipay-gateway:4009',ui:'kabipay-ui:80'});
  files['caddy/legacy-routes.caddy']=opsRoutes;
  let sites='';
  // No alternate unbound tenant/HMAC path may remain public.
  services['kabipay-gateway'].environment.KABIPAY_GATEWAY_PLANE='ops';
  Object.assign(networks,{organization:{external:true,name:'hrms_organization'},metadata:{external:true,name:'hrms_metadata'},sources:{external:true,name:'hrms_sources'},'private-history':{internal:true}});
  const publicKeys=mount(`${cfg}/public-keys`,'/run/public-keys');
  const sharedCa=mount(`${cfg}/tls/organization-ca.pem`,'/run/tls/organization-ca.pem');
  const identities={}, endpoints={};
  for(const company of c.companies) {
    const slug=company.slug, local=`company-${slug}`, egress=`egress-${slug}`, source=`source-${slug}`, auth=`auth-${slug}`, ingress=`ingress-${slug}`, gateway=`gateway-${slug}`;
    networks[local]={internal:true};
    networks[egress]={internal:false};
    const binding={KABIPAY_BOUND_TENANT_ID:company.id,KABIPAY_CLIENT_JWT_MODE:'rs256',KABIPAY_ORGANIZATION_HTTP_CA_FILE:'/run/tls/organization-ca.pem'};
    const companyEnv=env(`companies/${slug}/runtime`);
    const sourceVolumes=[publicKeys,sharedCa,mount(company.privateFilesPath,'/var/lib/kabipay/private-files',false)];
    services[auth]=runtime('kabipay-auth',env(`companies/${slug}/auth`),[local,'sources','metadata',egress],{...binding,KABIPAY_AUTH_PLANE:'client'},[publicKeys,sharedCa,mount(`${secrets}/${slug}/auth`,'/run/auth-secrets')]);
    for(const service of Object.keys(tenantServices)) {
      const serviceName=`${service}-${slug}`;
      services[serviceName]=runtime(`kabipay-${service}`,companyEnv,[local,'sources','metadata',egress],{
        ...binding,KABIPAY_SERVICE_ID:`kabipay-${service}`,KABIPAY_SERVICE_PRIVATE_KEY_FILE:'/run/service-secrets/service.key',
        KABIPAY_ORGANIZATION_POLICY_URL:'https://organization-internal:8443',
        KABIPAY_EMPLOYEE_PUBLIC_BASE:`https://${company.publicHost}`,KABIPAY_NOTIFICATION_PUBLIC_BASE:`https://${company.publicHost}`,
        KABIPAY_LOCAL_FILE_ROOT:'/var/lib/kabipay/private-files',
      },[...sourceVolumes,mount(`${secrets}/${slug}/${service}`,'/run/service-secrets')]);
      if(['employee','leave','attendance','expense','notification','survey','analytics'].includes(service)){
        services[serviceName].volumes.push(mount(`${secrets}/${slug}/private-events/${service}`,'/run/private-events'));
        services[serviceName].environment.KABIPAY_PRIVATE_EVENT_KEYS_FILE='/run/private-events/keys.json';
      }
      if(['survey','analytics'].includes(service)){
        Object.assign(services[serviceName].environment,{KABIPAY_PRIVATE_HISTORY_CLIENT_FILE:'/run/private-events/audit-client.json',KABIPAY_PRIVATE_HISTORY_CLIENT_CERT_FILE:'/run/private-events/client.crt',KABIPAY_PRIVATE_HISTORY_CLIENT_KEY_FILE:'/run/private-events/client.key'});
        services[serviceName].networks.push('private-history');
      }
      if(service==='analytics')services[serviceName].environment.KABIPAY_PRIVATE_DELIVERY_HISTORY_CLIENT_FILE='/run/private-events/delivery-client.json';
      if(service==='employee')Object.assign(services[serviceName].environment,{KABIPAY_PRIVATE_DELIVERY_ADAPTER_FILE:'/run/private-events/delivery-adapter.json',KABIPAY_PRIVATE_DELIVERY_BROKER_OWNER_ID:company.id});
    }
    services[`maintenance-${slug}`]=runtime('kabipay-tenant-maintenance',companyEnv,[local,'sources','metadata',egress],{...binding,KABIPAY_PRIVATE_EVENT_KEYS_FILE:'/run/private-events/keys.json'},[...sourceVolumes,mount(`${secrets}/${slug}/private-events/maintenance`,'/run/private-events')]);
    identities[company.id]=`https://${source}:8443/auth/client/organization-identity`;
    endpoints[company.id]=Object.fromEntries(commandServices.map((s,i)=>[`kabipay-${s}`,`https://${source}:${8444+i}/internal/organization/command`]));
    services[gateway]={image:image('gateway'),restart:'unless-stopped',networks:[local],environment:{NODE_ENV:'production',KABIPAY_SUBGRAPH_BASE_URL:`http://unused-${slug}`,KABIPAY_SUBGRAPH_ENDPOINTS:JSON.stringify(Object.fromEntries(Object.entries(tenantServices).map(([s,port])=>[s,`http://${s}-${slug}:${port}/graphql`]))),KABIPAY_OPS_SUBGRAPH_URL:'http://kabipay-subgraphs:4010/graphql',KABIPAY_ORGANIZATION_SUBGRAPH_URL:'http://organization:4031/graphql',KABIPAY_ORGANIZATION_ENABLED:'true',KABIPAY_ALLOW_PARTIAL_SUBGRAPHS:'false'}};
    // The gateway reaches only fixed tenant subgraphs plus ops/organization networks.
    services[gateway].networks.push('app-network','organization');
    const ui=`ui-${slug}`;
    services[ui]={image:image('ui'),restart:'unless-stopped',networks:[local],volumes:[mount(`${cfg}/ui-${slug}.json`,'/usr/share/nginx/html/config.json'),mount(`${c.appDir}/media/video-guides`,'/srv/video-guides')]};
    files[`config/ui-${slug}.json`]=JSON.stringify({gatewayUrl:`https://${company.publicHost}/graphql`,authUrl:`https://${company.publicHost}`,tenantBaseDomain:c.tenantBaseDomain},null,2);
    files[`caddy/public-${slug}.caddy`]=`{\n auto_https off\n admin off\n}\n:80 {\n${publicRoutes({plane:'company',auth:`${auth}:4001`,gateway:`${gateway}:4009`,employee:`employee-${slug}:4013`,notification:`notification-${slug}:4028`,ui:`${ui}:80`})}}\n`;
    files[`caddy/source-${slug}.caddy`]=`{\n admin off\n auto_https off\n}\n`+[
      `https://${source}:8443 {\n tls /run/tls/server.pem /run/tls/server.key\n @allowed path /auth/client/organization-identity /auth/internal/account-eligibility /auth/internal/employment-eligibility\n handle @allowed {\n reverse_proxy ${auth}:4001\n }\n respond 404\n}\n`,
      ...commandServices.map((s,i)=>`https://${source}:${8444+i} {\n tls /run/tls/server.pem /run/tls/server.key\n handle /internal/organization/* {\n reverse_proxy ${s}-${slug}:${tenantServices[s]}\n }\n respond 404\n}\n`),
      `https://${source}:8450 {\n tls /run/tls/server.pem /run/tls/server.key {\n client_auth {\n mode require_and_verify\n trust_pool file /run/tls/private-delivery-client-ca.pem\n }\n }\n @delivery path /internal/private-events/delivery /internal/private-events/ownership\n handle @delivery {\n request_body {\n max_size 16KiB\n }\n reverse_proxy employee-${slug}:4013\n }\n respond 404\n}\n`,
      ...[['payroll',8451],['employee',8452]].map(([s,port])=>`https://${source}:${port} {\n tls /run/tls/server.pem /run/tls/server.key\n handle /internal/finance {\n request_body {\n max_size 128KiB\n }\n reverse_proxy ${s}-${slug}:${tenantServices[s]}\n }\n respond 404\n}\n`),
    ].join('');
    services[ingress]={image:'caddy:2.10.2-alpine',restart:'unless-stopped',read_only:true,tmpfs:['/data','/config'],networks:[local,'app-network'],volumes:[mount(`${c.appDir}/caddy/public-${slug}.caddy`,'/etc/caddy/Caddyfile')]};
    services[source]={image:'caddy:2.10.2-alpine',restart:'unless-stopped',read_only:true,tmpfs:['/data','/config'],networks:[local,'organization'],volumes:[mount(`${c.appDir}/caddy/source-${slug}.caddy`,'/etc/caddy/Caddyfile'),mount(`${secrets}/${slug}/tls`,'/run/tls')]};
    sites+=`${company.publicHost} {\n tls /etc/caddy/certs/origin.pem /etc/caddy/certs/origin.key\n @private path /internal /internal/* /auth/internal /auth/internal/* /auth/client/organization-identity\n respond @private 404\n reverse_proxy ${ingress}:80\n}\n`;
  }
  services.organization=runtime('kabipay-organization',env('organization'),['organization','metadata'],{
    KABIPAY_ORGANIZATION_EXECUTION_ENABLED:'true',KABIPAY_ORGANIZATION_IDENTITY_ENDPOINTS:JSON.stringify(identities),
    KABIPAY_ORGANIZATION_RUNTIME_ENDPOINTS:JSON.stringify(endpoints),KABIPAY_ORGANIZATION_HTTP_CA_FILE:'/run/tls/organization-ca.pem',
  },[publicKeys,sharedCa,mount(`${secrets}/organization`,'/run/organization-secrets')]);
  files['caddy/organization-internal.caddy']='{\n admin off\n auto_https off\n}\nhttps://organization-internal:8443 {\n tls /run/tls/server.pem /run/tls/server.key\n handle /internal/organization/* {\n reverse_proxy organization:4031\n }\n respond 404\n}\n';
  services['organization-internal']={image:'caddy:2.10.2-alpine',restart:'unless-stopped',read_only:true,tmpfs:['/data','/config'],networks:['organization','sources'],volumes:[mount(`${c.appDir}/caddy/organization-internal.caddy`,'/etc/caddy/Caddyfile'),mount(`${secrets}/organization/tls`,'/run/tls')]};
  const worker = (name,command) => ({image:image('organization-events'),command:['node',`src/${command}.mjs`],env_file:[env(`workers/${name}`)],restart:'unless-stopped',read_only:true,init:true,tmpfs:['/tmp'],networks:['organization','metadata'],volumes:[mount(`${cfg}/events`,'/etc/organization'),mount(`${secrets}/workers/${name}`,'/run/secrets')],environment:{NODE_EXTRA_CA_CERTS:'/run/secrets/clickhouse-ca.crt'}});
  for(const role of ['inbox','history','reporting']) services[`${role}-worker`]={...worker(role,'worker'),environment:{CONSUMER_ROLE:role,TOPIC_BINDINGS_FILE:'/etc/organization/topic-bindings.json',NODE_EXTRA_CA_CERTS:'/run/secrets/clickhouse-ca.crt'}};
  services['capture-coordinator']=worker('capture','capture-worker');
  services['control-history-worker']=worker('control','control-worker');
  services.archive=worker('archive','archive-server');
  services.archive.volumes.push(mount(`${c.appDir}/data/archive`,'/var/lib/organization-archive',false));
  // Archive secrets are deliberately distinct from consumers and source DBs.
  services.archive.volumes[1]=mount(`${secrets}/workers/archive`,'/run/archive-secrets');
  services.archive.environment.NODE_EXTRA_CA_CERTS='/run/archive-secrets/clickhouse-ca.crt';
  for(const company of c.companies)for(const purpose of ['audit','delivery']){
    const slug=company.slug,name=`private-${purpose}-${slug}`;
    services[name]={...worker(`private/${slug}/${purpose}`,'private/worker'),networks:['organization'],volumes:[mount(`${cfg}/private/${slug}`,'/etc/private-events'),mount(`${secrets}/workers/private/${slug}/${purpose}`,'/run/secrets')],environment:{NODE_EXTRA_CA_CERTS:'/run/secrets/clickhouse-ca.crt',PRIVATE_EVENT_BINDING_FILE:`/etc/private-events/${purpose}-binding.json`,KABIPAY_PRIVATE_EVENT_KEYS_FILE:'/run/secrets/keys.json'}};
    if(purpose==='delivery')Object.assign(services[name].environment,{KABIPAY_PRIVATE_DELIVERY_WORKER_FILE:'/run/secrets/source.json',PRIVATE_DELIVERY_BROKER_OWNER_ID:company.id,PRIVATE_SOURCE_CA_FILE:'/run/secrets/source-ca.crt',PRIVATE_SOURCE_CERT_FILE:'/run/secrets/source-client.crt',PRIVATE_SOURCE_KEY_FILE:'/run/secrets/source-client.key'});
  }
  for(const [purpose,script,port] of [['audit','query-server',8445],['delivery','delivery-query-server',8446]]){
    const name=`private-${purpose}-history`;
    services[name]={...worker(name,`private/${script}`),networks:['organization','private-history']};
    Object.assign(services[name].environment,{[purpose==='audit'?'KABIPAY_PRIVATE_HISTORY_SERVER_FILE':'KABIPAY_PRIVATE_DELIVERY_HISTORY_SERVER_FILE']:'/run/secrets/bindings.json',PRIVATE_HISTORY_TLS_KEY_FILE:'/run/secrets/server.key',PRIVATE_HISTORY_TLS_CERT_FILE:'/run/secrets/server.crt',PRIVATE_HISTORY_CLIENT_CA_FILE:'/run/secrets/source-client-ca.crt',[purpose==='audit'?'PRIVATE_HISTORY_PORT':'PRIVATE_DELIVERY_HISTORY_PORT']:String(port)});
  }
  services['private-operator-audit']={...worker('private-operator-audit','private/worker'),networks:['organization'],environment:{NODE_EXTRA_CA_CERTS:'/run/secrets/clickhouse-ca.crt',PRIVATE_EVENT_BINDING_FILE:'/etc/organization/operator-audit-binding.json',KABIPAY_PRIVATE_EVENT_KEYS_FILE:'/run/secrets/keys.json'}};
  files['caddy/company-sites.caddy']=sites;
  files['compose.json']=JSON.stringify({name:'apps',services,networks},null,2)+'\n';
  files['finance-checks.txt']=c.companies.map(company=>`${env(`companies/${company.slug}/runtime`)}|employee-${company.slug} payroll-${company.slug}`).join('\n')+'\n';
  files['private-files.txt']=c.companies.map(company=>company.privateFilesPath).join('\n')+'\n';
  files['required-tenants.txt']=c.companies.map(v=>v.id).sort().join(',')+'\n';
  files['release.json']=JSON.stringify({version:1,tag:c.tag,mode:c.mode,tenantBaseDomain:c.tenantBaseDomain,
    companyBindings:c.companies.map(({id,slug,publicHost})=>({id,slug,publicHost})),
    artifacts:[...Object.keys(files),'release.json','release.sha256'],services:Object.keys(services),publicHosts:[c.apiHost,...c.companies.map(v=>v.publicHost)]},null,2);
  files['release.sha256']=Object.entries(files).map(([name,content])=>createHash('sha256').update(content).digest('hex')+'  '+name).join('\n')+'\n';
  return files;
}

if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  try {
    const [manifest,output]=process.argv.slice(2); required(manifest&&output,'Usage: node render.mjs manifest.json output-directory');
    const files=render(JSON.parse(await readFile(manifest,'utf8')));
    for(const [relative,content] of Object.entries(files)){const target=path.join(output,relative);await mkdir(path.dirname(target),{recursive:true});await writeFile(target,content,{mode:0o600});}
    console.log(`Rendered ${Object.keys(files).length} deployment artifacts; no secrets or live operations.`);
  }catch{console.error('Deployment manifest/render failed; inspect manifest fields and required paths.');process.exitCode=1;}
}
