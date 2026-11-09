// Shared application topology. Company-specific TLS endpoints remain logical
// names on one source proxy; they do not create application process replicas.
import {companyCatalog} from './company-catalog.mjs';
const mount=(source,target,read_only=true)=>({type:'bind',source,target,read_only,bind:{create_host_path:false}});
const privateServices=new Set(['employee','leave','attendance','expense','notification','survey','analytics','maintenance']);
export function shareCompanyServices(c, files, services, networks, tenantServices, commandServices, publicRoutes) {
  const root=c.appDir;
  const names=[...Object.keys(tenantServices),'auth','maintenance'];
  const sharedNetwork='company-applications', egress='company-egress';
  networks[sharedNetwork]={internal:true}; networks[egress]={internal:false};
  const sharedConfig='/run/company-config/companies.json';
  for(const name of names){
    files[`config/companies/${name}.json`]=JSON.stringify(companyCatalog(c.companies,name),null,2)+'\n';
    const service={image:`kabipay-svc:${c.tag}`,command:[`kabipay-${name==='maintenance'?'tenant-maintenance':name}`],
      restart:'unless-stopped',init:true,read_only:true,tmpfs:['/tmp'],
      logging:{driver:'json-file',options:{'max-size':'10m','max-file':'3'}}};
    service.env_file=[`${root}/env/shared/${name==='auth'?'auth':'runtime'}.env`];
    service.networks=[sharedNetwork,'sources','metadata',egress];
    if(['survey','analytics'].includes(name))service.networks.push('private-history');
    service.environment={KABIPAY_COMPANY_CONFIG_FILE:sharedConfig,KABIPAY_CLIENT_JWT_MODE:'rs256',
      KABIPAY_COMPANY_DATABASE_FILE:'/run/service-secrets/database.json',
      KABIPAY_REQUIRE_AUTH:'1',KABIPAY_ORGANIZATION_HTTP_CA_FILE:'/run/tls/organization-ca.pem',
      KABIPAY_DB_POOL_MAX:String(c.databasePools.opsPerService),
      KABIPAY_TENANT_DB_POOL_MAX:String(c.databasePools.perCompany),
      KABIPAY_TENANT_DB_CONNECTION_BUDGET:String(c.companies.length*c.databasePools.perCompany)};
    service.volumes=[mount(`${root}/config/public-keys`,'/run/public-keys'),
      mount(`${root}/config/tls/organization-ca.pem`,'/run/tls/organization-ca.pem'),
      mount(`${root}/config/companies/${name}.json`,sharedConfig),
      mount(`${root}/secrets/shared/${name}/service`,'/run/service-secrets')];
    if(name==='auth')service.environment.KABIPAY_AUTH_PLANE='client';
    else if(name!=='maintenance')Object.assign(service.environment,{
      KABIPAY_SERVICE_ID:`kabipay-${name}`,KABIPAY_SERVICE_PRIVATE_KEY_FILE:'/run/service-secrets/service.key',
      KABIPAY_ORGANIZATION_POLICY_URL:'https://organization-internal:8443'});
    if(['employee','notification','maintenance'].includes(name)){
      service.environment.KABIPAY_LOCAL_FILE_ROOT='/var/lib/kabipay/private-files';
      for(const company of c.companies)service.volumes.push(mount(
        `${company.privateFilesPath}/tenants/${company.id}`,
        `/var/lib/kabipay/private-files/tenants/${company.id}`,false));
    }
    // A service receives only its own purpose-specific files for each company.
    for(const company of c.companies){
      if(name==='auth')service.volumes.push(mount(`${root}/secrets/${company.slug}/auth`,`/run/companies/${company.id}/auth`));
      if(privateServices.has(name))service.volumes.push(mount(`${root}/secrets/${company.slug}/private-events/${name}`,`/run/companies/${company.id}/private-events`));
    }
    services[`shared-${name}`]=service;
  }
  const gateway={image:`kabipay-gateway:${c.tag}`,restart:'unless-stopped',networks:[sharedNetwork,'app-network','organization'],environment:{
    NODE_ENV:'production',KABIPAY_SUBGRAPH_BASE_URL:'http://unused-shared',
    KABIPAY_OPS_SUBGRAPH_URL:'http://kabipay-subgraphs:4010/graphql',KABIPAY_ORGANIZATION_SUBGRAPH_URL:'http://organization:4031/graphql',
    KABIPAY_ORGANIZATION_ENABLED:'true',KABIPAY_ALLOW_PARTIAL_SUBGRAPHS:'false'}};
  gateway.environment.KABIPAY_SUBGRAPH_ENDPOINTS=JSON.stringify(Object.fromEntries(
    Object.entries(tenantServices).map(([name,port])=>[name,`http://shared-${name}:${port}/graphql`])));
  services['shared-gateway']=gateway;
  services['shared-ui']={image:`kabipay-ui:${c.tag}`,restart:'unless-stopped',networks:[sharedNetwork],
    volumes:[mount(`${root}/media/video-guides`,'/srv/video-guides')]};
  let publicConfig='{\n admin off\n auto_https off\n}\n',sourceConfig='{\n admin off\n auto_https off\n}\n';
  const sourceVolumes=[mount(`${root}/caddy/shared-source.caddy`,'/etc/caddy/Caddyfile')];
  let sites='';
  for(const company of c.companies){
    const slug=company.slug;
    files[`config/ui-${slug}.json`]=JSON.stringify({gatewayUrl:`https://${company.publicHost}/graphql`,authUrl:`https://${company.publicHost}`,tenantBaseDomain:c.tenantBaseDomain},null,2);
    let publicSite=`http://${company.publicHost} {\n${publicRoutes({plane:'company',auth:'shared-auth:4001',gateway:'shared-gateway:4009',employee:'shared-employee:4013',notification:'shared-notification:4028',ui:'shared-ui:80'})}}\n`;
    publicSite=publicSite.replace('route {',`route {\nhandle /config.json {\n header Cache-Control no-store\n root * /run/ui-config\n rewrite * /ui-${slug}.json\n file_server\n}\n`);
    publicConfig+=publicSite;
    const tls=`/run/companies/${company.id}/tls`,sourceHost=`source-${slug}`;
    let source=[
      `https://${sourceHost}:8443 {\n tls ${tls}/server.pem ${tls}/server.key\n @allowed path /auth/client/organization-identity /auth/internal/account-eligibility /auth/internal/employment-eligibility\n handle @allowed {\n reverse_proxy shared-auth:4001\n }\n respond 404\n}\n`,
      ...commandServices.map((name,i)=>`https://${sourceHost}:${8444+i} {\n tls ${tls}/server.pem ${tls}/server.key\n handle /internal/organization/* {\n reverse_proxy shared-${name}:${tenantServices[name]}\n }\n respond 404\n}\n`),
      `https://${sourceHost}:8450 {\n tls ${tls}/server.pem ${tls}/server.key {\n client_auth {\n mode require_and_verify\n trust_pool file ${tls}/private-delivery-client-ca.pem\n }\n }\n @delivery path /internal/private-events/delivery /internal/private-events/ownership\n handle @delivery {\n request_body {\n max_size 16KiB\n }\n reverse_proxy shared-employee:4013\n }\n respond 404\n}\n`,
      ...[['payroll',8451],['employee',8452]].map(([name,port])=>`https://${sourceHost}:${port} {\n tls ${tls}/server.pem ${tls}/server.key\n handle /internal/finance {\n request_body {\n max_size 128KiB\n }\n reverse_proxy shared-${name}:${tenantServices[name]}\n }\n respond 404\n}\n`),
    ].join('');
    // This selector is overwritten by the private proxy and subsequently bound
    // to the signed target by both Auth eligibility and organization commands.
    source=source.replace(/reverse_proxy (shared-[a-z]+:\d+)/g,
      `reverse_proxy $1 {\n header_up X-Organization-Company-Id ${company.id}\n }`);
    sourceConfig+=source;
    sourceVolumes.push(mount(`${root}/secrets/${slug}/tls`,`/run/companies/${company.id}/tls`));
    sites+=`${company.publicHost} {\n tls /etc/caddy/certs/origin.pem /etc/caddy/certs/origin.key\n @private path /internal /internal/* /auth/internal /auth/internal/* /auth/client/organization-identity\n respond @private 404\n reverse_proxy shared-ingress:80\n}\n`;
  }
  // Finance calls between the shared Employee/Payroll services use one stable
  // TLS origin. The Finance protocol authenticates the company in its body.
  const financeTls='/run/shared-source-tls';
  sourceVolumes.push(mount(`${root}/secrets/shared/source-tls`,financeTls));
  for(const [name,port] of [['payroll',8451],['employee',8452]])sourceConfig+=
    `https://shared-source:${port} {\n tls ${financeTls}/server.pem ${financeTls}/server.key\n handle /internal/finance {\n request_body {\n max_size 128KiB\n }\n reverse_proxy shared-${name}:${tenantServices[name]}\n }\n respond 404\n}\n`;
  files['caddy/shared-public.caddy']=publicConfig;
  files['caddy/shared-source.caddy']=sourceConfig;
  files['caddy/company-sites.caddy']=sites;
  const proxy={image:'caddy:2.10.2-alpine',restart:'unless-stopped',read_only:true,tmpfs:['/data','/config']};
  services['shared-ingress']={...proxy,networks:[sharedNetwork,'app-network'],volumes:[
    mount(`${root}/caddy/shared-public.caddy`,'/etc/caddy/Caddyfile'),mount(`${root}/config`,'/run/ui-config')]};
  services['shared-source']={...proxy,networks:{[sharedNetwork]:{},organization:{aliases:c.companies.map(company=>`source-${company.slug}`)}},volumes:sourceVolumes};
  files['finance-checks.txt']=`${root}/env/shared/runtime.env|shared-employee shared-payroll\n`;
  files['private-files.txt']=c.companies.map(company=>`${company.privateFilesPath}/tenants/${company.id}`).join('\n')+'\n';
  files['company-configs.txt']=names.map(name=>`${root}/config/companies/${name}.json`).join('\n')+'\n';
}
