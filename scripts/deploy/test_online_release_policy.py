"""Synthetic policy/session guards. No database, Docker, network or credentials."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

SPEC=importlib.util.spec_from_file_location('release_policy',Path(__file__).with_name('online-release-policy.py'))
policy=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(policy)


def fixture():
    companies=[dict(database='company_fixture'+str(i),tenantId=f'{i:08x}-0000-4000-8000-000000000001',schema=f'tenant_{i:08x}') for i in range(1,6)]
    registry=[dict(row,subdomain=row['database'][8:],status='ACTIVE',dbHost='postgres',dbType='POSTGRES',active=True) for row in companies]
    return companies,registry


class Server:
    def __init__(self):
        self.companies,self.registry=fixture(); self.events=[]; self.held=set(); self.sessions=[]
        self.states={r['database']:dict(database=r['database'],oid=100+i,allowConnections=i<3,connectionLimit=-1,template=False,connections=0) for i,r in enumerate(self.companies)}
        self.hashes={r['database']:'a'*64 for r in self.companies}; self.fail_close=None; self.dead=None; self.table_dead=None
    def control(self,sql):
        self.events.append(('catalog',sql))
        return json.dumps(dict(systemId='123',databases=list(self.states.values())))
    def session(self,database):
        server=self
        class Session:
            def __init__(self): self.database=database; self.pid=1000+len(server.sessions); self.transaction='tx-'+str(self.pid); self.closed=False
            def query(self,sql):
                server.events.append(('query',database,sql))
                if sql=='ROLLBACK;': server.held.discard(database); return ''
                if sql.startswith('BEGIN READ ONLY;'): server.held.add(database)
                return json.dumps(dict(database=database,databaseOid=server.states[database]['oid'],systemId='123',backendPid=self.pid,transactionStartedAt=self.transaction,readOnly=True,lockHeld=database in server.held and database!=server.dead,tablesLocked=database!=server.table_dead,policySha256=server.hashes[database]))
            def close(self):
                server.events.append(('close',database)); server.held.discard(database); self.closed=True
                if database==server.fail_close: raise ValueError('SYNTHETIC_CLOSE_FAILURE')
        value=Session(); self.sessions.append(value); return value
    def guard(self): return policy.PolicyGuard(self.companies,self.registry,'123',self.control,self.session)


class PolicyTests(unittest.TestCase):
    def test_capture_returns_only_metadata_hashes_and_releases_all_owned_sessions(self):
        server=Server(); guard=server.guard(); captured=guard.capture()
        self.assertIsInstance(captured,dict)
        self.assertEqual(set(captured['policySha256']),{'company_fixture1','company_fixture2','company_fixture3'})
        self.assertFalse(server.held); self.assertTrue(all(s.closed for s in server.sessions))
        self.assertEqual([s.database for s in server.sessions],['company_fixture1','company_fixture2','company_fixture3'])

    def test_strict_five_company_registry_bindings(self):
        for case in ['missing','extra','database','uuid','schema','duplicate','registry','host','inactive']:
            server=Server()
            if case=='missing': server.companies.pop()
            if case=='extra': server.companies[0]['sql']='unreviewed'
            if case=='database': server.companies[0]['database']='company_bad;SELECT secret'
            if case=='uuid': server.companies[0]['tenantId']='not-a-uuid'
            if case=='schema': server.companies[0]['schema']='tenant_deadbeef'
            if case=='duplicate': server.companies[1]=server.companies[0]
            if case=='registry': server.registry[0]['tenantId']=server.registry[1]['tenantId']
            if case=='host': server.registry[0]['dbHost']='remote'
            if case=='inactive': server.registry[0]['active']=False
            with self.subTest(case=case),self.assertRaises(ValueError): server.guard()
            self.assertFalse(server.events)

    def test_closed_database_zero_connections_required_without_connecting_it(self):
        server=Server(); server.states['company_fixture5']['connections']=1
        with self.assertRaisesRegex(ValueError,'CLOSED_POLICY_DATABASE_HAS_SESSIONS'): server.guard().capture()
        self.assertEqual(server.sessions,[])

    def test_policy_admission_oid_or_closed_session_drift_refuses_before_body(self):
        for case in ['policy','openClosed','closedOpen','oid','limit','closedSessions']:
            server=Server(); guard=server.guard(); guard.capture()
            if case=='policy': server.hashes['company_fixture1']='b'*64
            if case=='openClosed': server.states['company_fixture1']['allowConnections']=False
            if case=='closedOpen': server.states['company_fixture5']['allowConnections']=True
            if case=='oid': server.states['company_fixture1']['oid']+=1
            if case=='limit': server.states['company_fixture1']['connectionLimit']=0
            if case=='closedSessions': server.states['company_fixture5']['connections']=1
            entered=False
            with self.subTest(case=case),self.assertRaises(ValueError):
                with guard.rollback_guard(): entered=True
            self.assertFalse(entered); self.assertFalse(server.held)
            self.assertTrue(all(s.closed for s in server.sessions))

    def test_all_open_locks_held_in_deterministic_order_until_body_and_final_check(self):
        server=Server(); guard=server.guard(); guard.capture(); server.events=[]
        with guard.rollback_guard() as held:
            self.assertEqual(server.held,{'company_fixture1','company_fixture2','company_fixture3'})
            held.check(); server.events.append(('old-replacement',))
            held.check(); server.events.append(('artifact-restore',))
            self.assertEqual(len(server.held),3)
        starts=[e[1] for e in server.events if e[0]=='query' and e[2].startswith('BEGIN READ ONLY;')]
        self.assertEqual(starts,['company_fixture1','company_fixture2','company_fixture3'])
        self.assertFalse(server.held)
        self.assertGreater(next(i for i,e in enumerate(server.events) if e[0]=='close'),server.events.index(('artifact-restore',)))

    def test_lost_lock_or_changed_transaction_stops_guard_and_cleans_all_clients(self):
        for case in ['lock','table','transaction','hash','admission']:
            server=Server(); guard=server.guard(); guard.capture()
            with self.subTest(case=case),self.assertRaises(ValueError):
                with guard.rollback_guard() as held:
                    if case=='lock': server.dead='company_fixture1'
                    if case=='table': server.table_dead='company_fixture1'
                    if case=='transaction': server.sessions[-3].transaction='different'
                    if case=='hash': server.hashes['company_fixture1']='b'*64
                    if case=='admission': server.states['company_fixture5']['allowConnections']=True
                    held.check()
            self.assertFalse(server.held); self.assertTrue(all(s.closed for s in server.sessions))

    def test_cleanup_failure_never_claims_success_and_other_sessions_close(self):
        server=Server(); guard=server.guard(); guard.capture(); server.fail_close='company_fixture3'
        with self.assertRaisesRegex(ValueError,'ROLLBACK_POLICY_SESSION_CLEANUP_FAILED'):
            with guard.rollback_guard(): pass
        self.assertFalse(server.held); self.assertTrue(all(s.closed for s in server.sessions))

    def test_sql_returns_only_server_hash_and_exact_lock_namespace(self):
        row=fixture()[0][0]; sql=policy.begin_sql(row)
        self.assertIn('BEGIN READ ONLY;',sql)
        self.assertIn('company-account-admin:'+row['tenantId'],sql)
        self.assertIn('pg_advisory_xact_lock(hashtextextended(',sql)
        self.assertIn("lock_timeout='5s'",sql); self.assertIn("statement_timeout='10s'",sql)
        self.assertIn('sha256(convert_to(',sql)
        self.assertIn('LOCK TABLE ',sql); self.assertIn(' IN SHARE MODE;',sql)
        for table in ['role','permission','role_permission','permission_scope','user_role']:
            self.assertIn('"'+row['schema']+'"."'+table+'"',sql)
        for forbidden in ['ALTER ','UPDATE ','INSERT ','DELETE ','pg_terminate_backend','password_hash','user_session','MaintenanceSession']:
            self.assertNotIn(forbidden,sql)

    def test_sql_compilers_refuse_unvalidated_identifier_or_uuid_inputs(self):
        for field in ['database','schema','tenantId']:
            row=fixture()[0][0].copy(); row[field]="unreviewed';SELECT 1;--"
            for compile_sql in [policy.begin_sql,policy.snapshot_sql,lambda c:policy.catalog_sql([c])]:
                with self.subTest(field=field),self.assertRaises(ValueError): compile_sql(row)


if __name__=='__main__': unittest.main(testRunner=unittest.TextTestRunner(stream=sys.stdout))
