// Generated non-secret service catalogues. Database coordinates live in the
// metadata registry; stable service credentials are provisioned only on the VPS.
const privateServices=new Set(['employee','leave','attendance','expense','notification','survey','analytics','maintenance']);
export function companyCatalog(companies,service){
  return {version:2,companies:companies.map(company=>{
    const base=`/run/companies/${company.id}`,settings={};
    if(service==='auth')Object.assign(settings,{
      KABIPAY_CLIENT_JWT_KEY_ID:company.clientJwtKeyId,
      KABIPAY_CLIENT_JWT_PRIVATE_KEY_FILE:`${base}/auth/client.key`,
    });
    if(privateServices.has(service))settings.KABIPAY_PRIVATE_EVENT_KEYS_FILE=`${base}/private-events/keys.json`;
    if(['survey','analytics'].includes(service))Object.assign(settings,{
      KABIPAY_PRIVATE_HISTORY_CLIENT_FILE:`${base}/private-events/audit-client.json`,
      KABIPAY_PRIVATE_HISTORY_CLIENT_CERT_FILE:`${base}/private-events/client.crt`,
      KABIPAY_PRIVATE_HISTORY_CLIENT_KEY_FILE:`${base}/private-events/client.key`,
    });
    if(service==='analytics')settings.KABIPAY_PRIVATE_DELIVERY_HISTORY_CLIENT_FILE=`${base}/private-events/delivery-client.json`;
    if(service==='employee')Object.assign(settings,{
      KABIPAY_PRIVATE_DELIVERY_ADAPTER_FILE:`${base}/private-events/delivery-adapter.json`,
      KABIPAY_PRIVATE_DELIVERY_BROKER_OWNER_ID:company.id,
    });
    return {tenant_id:company.id,public_origin:`https://${company.publicHost}`,settings};
  })};
}
