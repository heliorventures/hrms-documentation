"""Read-only policy continuity guard for automatic application rollback."""
from contextlib import contextmanager
import copy
import json
import re
import uuid

TABLES=('role','permission','role_permission','permission_scope','user_role')


def need(ok,code):
    if not ok: raise ValueError(code)


def digest(value):
    return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None


def company_binding(row):
    need(type(row) is dict and set(row)=={'database','schema','tenantId'} and all(type(v) is str for v in row.values()),'POLICY_COMPANY_BINDING_INVALID')
    need(re.fullmatch('company_[a-z][a-z0-9_]{0,54}',row['database']) and len(row['database'])<=63 and re.fullmatch('[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',row['tenantId']) and str(uuid.UUID(row['tenantId']))==row['tenantId'] and row['schema']=='tenant_'+row['tenantId'][:8],'POLICY_COMPANY_BINDING_INVALID')


def companies_bound(companies,registry):
    need(type(companies) is list and len(companies)==5 and type(registry) is list and len(registry)==5,'FIVE_POLICY_COMPANIES_REQUIRED')
    for row in companies: company_binding(row)
    need(all(len({row[key] for row in companies})==5 for key in ['database','tenantId']),'POLICY_COMPANY_BINDING_INVALID')
    for row in registry:
        need(type(row) is dict and row.get('dbHost')=='postgres' and row.get('dbType')=='POSTGRES' and row.get('status')=='ACTIVE' and row.get('active') is True and row.get('database')=='company_'+str(row.get('subdomain')),'POLICY_REGISTRY_BINDING_CHANGED')
    expected=sorted(({k:row.get(k) for k in ['database','schema','tenantId']} for row in registry),key=lambda v:v['database'])
    actual=sorted(copy.deepcopy(companies),key=lambda v:v['database'])
    need(actual==expected,'POLICY_REGISTRY_BINDING_CHANGED'); return actual


def catalog_sql(companies):
    for row in companies: company_binding(row)
    names=','.join("'"+row['database']+"'" for row in companies)
    return ("BEGIN READ ONLY; SET LOCAL search_path=pg_catalog; SET LOCAL statement_timeout='10s'; "
            "SELECT jsonb_build_object('systemId',(SELECT system_identifier::text FROM pg_control_system()),'databases',"
            "(SELECT jsonb_agg(jsonb_build_object('database',d.datname,'oid',d.oid::bigint,'allowConnections',d.datallowconn,"
            "'connectionLimit',d.datconnlimit,'template',d.datistemplate,'connections',"
            "(SELECT count(*) FROM pg_stat_activity a WHERE a.datid=d.oid)) ORDER BY d.datname) FROM pg_database d WHERE d.datname IN ("+names+"))); COMMIT;")


def snapshot_sql(company):
    company_binding(company)
    key="hashtextextended('company-account-admin:"+company['tenantId']+"',0)"
    tables=','.join("'"+name+"',(SELECT coalesce(jsonb_agg(to_jsonb(r) ORDER BY to_jsonb(r)::text),'[]'::jsonb) FROM \""+company['schema']+'"."'+name+'" r)' for name in TABLES)
    held="EXISTS(SELECT 1 FROM pg_locks WHERE pid=pg_backend_pid() AND locktype='advisory' AND granted AND mode='ExclusiveLock' AND objsubid=1 AND classid=(("+key+">>32)&4294967295)::oid AND objid=("+key+"&4294967295)::oid)"
    relations=','.join("'\""+company['schema']+'"."'+name+'"\'::regclass' for name in TABLES)
    tables_held="(SELECT count(DISTINCT relation)=5 FROM pg_locks WHERE pid=pg_backend_pid() AND locktype='relation' AND granted AND mode='ShareLock' AND relation IN ("+relations+"))"
    return ("SELECT jsonb_build_object('database',current_database(),'databaseOid',(SELECT oid::bigint FROM pg_database WHERE datname=current_database()),"
            "'systemId',(SELECT system_identifier::text FROM pg_control_system()),'backendPid',pg_backend_pid(),"
            "'transactionStartedAt',transaction_timestamp()::text,'readOnly',current_setting('transaction_read_only')='on','lockHeld',"+held+",'tablesLocked',"+tables_held+","
            "'policySha256',encode(sha256(convert_to(jsonb_build_object("+tables+")::text,'UTF8')),'hex'));")


def begin_sql(company):
    company_binding(company)
    relations=','.join('"'+company['schema']+'"."'+name+'"' for name in TABLES)
    return ("BEGIN READ ONLY; SET LOCAL search_path=pg_catalog; SET LOCAL standard_conforming_strings=on; SET LOCAL TIME ZONE 'UTC'; SET LOCAL DateStyle='ISO, YMD'; "
            "SET LOCAL lock_timeout='5s'; SET LOCAL statement_timeout='10s'; "
            "SELECT pg_advisory_xact_lock(hashtextextended('company-account-admin:"+company['tenantId']+"',0)); LOCK TABLE "+relations+" IN SHARE MODE; "+snapshot_sql(company))


class PolicyGuard:
    def __init__(self,companies,registry,system_id,control,session_factory):
        self.companies=companies_bound(companies,registry)
        need(isinstance(system_id,str) and re.fullmatch('[0-9]{1,20}',system_id),'POLICY_CLUSTER_BINDING_INVALID')
        self.system_id=system_id; self.control=control; self.factory=session_factory
        self.baseline=None; self.sessions={}; self.identities={}

    def catalog(self):
        value=json.loads(self.control(catalog_sql(self.companies)))
        need(type(value) is dict and set(value)=={'systemId','databases'} and value['systemId']==self.system_id and type(value['databases']) is list,'POLICY_DATABASE_IDENTITY_CHANGED')
        rows=value['databases']; need(len(rows)==5 and {r.get('database') for r in rows}=={r['database'] for r in self.companies},'POLICY_DATABASE_IDENTITY_CHANGED')
        result={}
        for row in rows:
            need(set(row)=={'database','oid','allowConnections','connectionLimit','template','connections'} and type(row['oid']) is int and row['oid']>0 and type(row['allowConnections']) is bool and type(row['connectionLimit']) is int and row['connectionLimit']>=-1 and row['template'] is False and type(row['connections']) is int and row['connections']>=0,'POLICY_DATABASE_IDENTITY_CHANGED')
            closed=not row['allowConnections'] or row['connectionLimit']==0
            need(not closed or row['connections']==0,'CLOSED_POLICY_DATABASE_HAS_SESSIONS')
            result[row['database']]={k:v for k,v in row.items() if k!='connections'}
            result[row['database']]['closed']=closed
        return result

    def state(self,company,raw,catalog):
        value=json.loads(raw); name=company['database']
        need(type(value) is dict and set(value)=={'database','databaseOid','systemId','backendPid','transactionStartedAt','readOnly','lockHeld','tablesLocked','policySha256'} and value['database']==name and value['databaseOid']==catalog[name]['oid'] and value['systemId']==self.system_id and type(value['backendPid']) is int and value['backendPid']>0 and isinstance(value['transactionStartedAt'],str) and bool(value['transactionStartedAt']) and value['readOnly'] is True and value['lockHeld'] is True and value['tablesLocked'] is True and digest(value['policySha256']),'ROLLBACK_POLICY_LOCK_OR_IDENTITY_CHANGED')
        return value

    def acquire(self):
        need(not self.sessions,'POLICY_SESSIONS_ALREADY_HELD')
        catalog=self.catalog()
        if self.baseline is not None: need(catalog==self.baseline['databases'],'ROLLBACK_POLICY_ADMISSION_CHANGED')
        self.identities={}
        for company in self.companies:
            name=company['database']
            if catalog[name]['closed']: continue
            session=self.factory(name); self.sessions[name]=session
            value=self.state(company,session.query(begin_sql(company)),catalog); self.identities[name]=value
            if self.baseline is not None: need(value['policySha256']==self.baseline['policySha256'][name],'ROLLBACK_POLICY_CHANGED')
        return catalog

    def cleanup(self):
        failed=False
        for session in reversed(list(self.sessions.values())):
            try: session.query('ROLLBACK;')
            except Exception: failed=True
            try: session.close()
            except Exception: failed=True
        self.sessions={}; self.identities={}
        need(not failed,'ROLLBACK_POLICY_SESSION_CLEANUP_FAILED')

    def capture(self):
        need(self.baseline is None,'POLICY_BASELINE_ALREADY_CAPTURED')
        try:
            catalog=self.acquire()
            self.baseline=dict(version=1,companies=copy.deepcopy(self.companies),databases=catalog,policySha256={n:v['policySha256'] for n,v in self.identities.items()})
            self.check(); return copy.deepcopy(self.baseline)
        finally: self.cleanup()

    def check(self):
        need(self.baseline is not None and set(self.sessions)==set(self.baseline['policySha256']),'ROLLBACK_POLICY_SESSIONS_MISSING')
        need(self.catalog()==self.baseline['databases'],'ROLLBACK_POLICY_ADMISSION_CHANGED')
        for company in self.companies:
            name=company['database']
            if name not in self.sessions: continue
            value=self.state(company,self.sessions[name].query(snapshot_sql(company)),self.baseline['databases'])
            need(value==self.identities[name] and value['policySha256']==self.baseline['policySha256'][name],'ROLLBACK_POLICY_LOCK_OR_IDENTITY_CHANGED')

    @contextmanager
    def rollback_guard(self):
        need(self.baseline is not None,'POLICY_BASELINE_REQUIRED')
        try:
            self.acquire(); self.check(); yield self; self.check()
        finally: self.cleanup()
