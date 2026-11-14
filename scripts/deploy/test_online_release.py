"""Synthetic local adapter tests. No Docker, network, secrets or VPS data."""
import base64
import copy
import hashlib
import importlib.util
import json
import io
import stat
from types import SimpleNamespace
from pathlib import Path
import uuid
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('online_release', Path(__file__).with_name('online-release.py'))
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)
H = lambda raw: hashlib.sha256(raw).hexdigest()
OLD = 'sha256:' + '1' * 64
NEW = 'sha256:' + '2' * 64
NAMES = ['shared-employee', 'shared-gateway', 'shared-ui']


def fixture():
    compose = {'services': {n: {'image': 'kabipay-' + ('svc' if i == 0 else 'gateway' if i == 1 else 'ui') + ':old', 'command': ['fixed'], 'networks': ['existing']} for i, n in enumerate(NAMES)}, 'networks': {'existing': {'external': True}}}
    compose['services']['private-audit-dormant'] = {'image': 'events:old'}
    old = {'compose.json': json.dumps(compose).encode(), 'release.json': json.dumps({'tag': 'old', 'companyBindings': ['synthetic']}).encode(), 'config/ui-config.json': b'{}'}
    old['release.sha256'] = ''.join(H(v) + '  ' + n + '\n' for n, v in old.items()).encode()
    fleet = {n: dict(id=n + '-old', image=OLD, running=True, restarts=0, contractSha256='a' * 64, service=n, project='apps', started='old') for n in NAMES}
    fleet['preserved-worker'] = dict(id='untouched', image=OLD, running=False, restarts=0, contractSha256='b' * 64, service='preserved-worker', project='apps', started='old')
    probes = {n: dict(kind='http', url='http://synthetic/healthz', method='GET', expectedStatus=200, expectedText='ok', attempts=1, intervalSeconds=0) for n in ['ready-employee', 'ready-gateway', 'ready-ui', 'final-http', 'rollback-http', 'rollback-employee', 'rollback-gateway', 'rollback-ui']}
    probes['employee-schema'] = dict(kind='employeeSchema',url='http://synthetic/graphql',method='POST',query='query { _service { sdl } }',bodySha256='a'*64,expectedStatus=200,attempts=1,intervalSeconds=0)
    probes['gateway-schema'] = dict(probes['employee-schema'], kind='gatewaySchema',query='query { __schema { types { name } } }')
    plan = dict(version=1, contractFingerprintVersion=2, tag='new', appDir='/opt/apps/hrms', baselineFleet=fleet,
                oldArtifacts={n:H(v) for n,v in old.items()}, previousBytes={n:base64.b64encode(v).decode() for n,v in old.items()},
                selected=[dict(service=n, phase=phase, oldImage=OLD, newImage=NEW, readiness=['ready-' + label]) for n,phase,label in zip(NAMES, ['backend','gateway','ui'], ['employee','gateway','ui'])],
                probes=probes, employeeGate=['employee-schema'], gatewayGate=['gateway-schema'], finalGate=['final-http'],preflightProbes=['final-http'],
                rollback=dict(order=list(reversed(NAMES)), probes=['rollback-http'], readiness={n:['rollback-'+label] for n,label in zip(NAMES,['employee','gateway','ui'])}, compatibilityReceipt=dict(path='/root/synthetic-compatibility.json', sha256='c' * 64)),
                sourceReceipt=dict(path='/root/synthetic-source.json', sha256='d' * 64),
                grantsReceipt=dict(path='/root/synthetic-grants.json', sha256='e' * 64),
                protectedFiles={'/root/synthetic-binding.json':'f' * 64},
                operator=dict(directory='/root/hrms-private-config-synthetic', packageSha256='0' * 64),
                registryReceipt=dict(path='/root/synthetic-registry.json',sha256='3'*64),systemId='7666443962289373219',
                hostDefaultsReceipt=dict(path='/root/synthetic-host-defaults.json',sha256='7'*64),
                rootProxy=dict(container='caddy',containerId='8'*64,image=OLD,source='/opt/apps/Caddyfile',sha256='5'*64,inode=1,activeSha256='6'*64,
                               metadata=dict(uid=1000,gid=1000,mode=0o644,inode=1,device=2050,size=3),mountBinding=dict(destination='/etc/caddy/Caddyfile',readOnly=False)),
                probeRuntime=dict(image=OLD, network='existing', networkId='4'*64), executorSha256='9' * 64,
                policyExecutorSha256='a'*64,policyCompanies=[dict(database='company_fixture'+str(i),tenantId=f'{i:08x}-0000-4000-8000-000000000001',schema=f'tenant_{i:08x}') for i in range(1,6)])
    for step in plan['selected']:
        step['repository']='kabipay-svc' if step['phase']=='backend' else 'kabipay-'+step['phase']
        step['oldImageReference']=json.loads(old['compose.json'])['services'][step['service']]['image']
        step['oldRepositoryTag']=step['oldImageReference']
    plan['baselineFleet']['/caddy']=dict(id='8'*64,image=OLD,running=True,restarts=0,contractSha256='8'*64,service='caddy',project='apps',started='old')
    plan['newArtifacts']={n:H(v) for n,v in release.transition(plan,old).items()}
    return plan, old


class Fake:
    def __init__(self, plan, old):
        self.plan, self.files, self.fleet = plan, copy.deepcopy(old), copy.deepcopy(plan['baselineFleet'])
        self.events, self.receipts = [], {}
        self.fail_probe = self.fail_replace = self.fail_rollback = None
        self.locked = False
        self.policy_drift=False; self.policy_held=False; self.policy_captured=False; self.policy_cleanup_failure=False
        self.old_policy_states=[]; self.restore_policy_states=[]; self.original_files=copy.deepcopy(old)
    def context(self): self.events.append('context')
    def snapshot(self): return copy.deepcopy(self.fleet)
    def artifacts(self): return copy.deepcopy(self.files)
    def publish(self, data, expected):
        self.assert_locked()
        assert all(H(self.files[n]) == h for n,h in expected.items())
        self.files.update(data)
        if data and all(value==self.original_files[name] for name,value in data.items()): self.restore_policy_states.append(self.policy_held)
        self.events.append('publish')
    def assert_locked(self): assert self.locked
    def replace(self, name, image):
        self.assert_locked()
        self.events.append(('replace', name, image))
        if image==OLD: self.old_policy_states.append(self.policy_held)
        if name == self.fail_replace:
            self.fleet[name]['image'] = 'sha256:' + '7' * 64
            raise ValueError('AMBIGUOUS_REPLACE')
        if image == OLD and name == self.fail_rollback: raise ValueError('ROLLBACK_REPLACE_FAILED')
        self.fleet[name].update(image=image, id=name + image[-3:], started='new')
    def probe(self, name):
        self.events.append(('probe', name))
        if name == self.fail_probe: raise ValueError('PROBE_FAILED')
    def save(self, name, value):
        assert name not in self.receipts
        self.receipts[name] = copy.deepcopy(value)
    def lock(self):
        from contextlib import contextmanager
        @contextmanager
        def held():
            self.locked = True
            try: yield
            finally: self.locked = False
        return held()
    def capture_policy(self):
        self.events.append('policy-capture'); self.policy_captured=True
        return dict(policySha256={'synthetic':'a'*64})
    def rollback_guard(self):
        from contextlib import contextmanager
        @contextmanager
        def held():
            self.events.append('rollback-policy-acquire')
            if not self.policy_captured or self.policy_drift: raise ValueError('ROLLBACK_POLICY_CHANGED')
            self.policy_held=True
            def check():
                self.events.append('rollback-policy-check')
                if not self.policy_held or self.policy_drift: raise ValueError('ROLLBACK_POLICY_LOCK_CHANGED')
            try:
                check(); yield SimpleNamespace(check=check); check()
            finally:
                self.policy_held=False; self.events.append('rollback-policy-release')
                if self.policy_cleanup_failure: raise ValueError('ROLLBACK_POLICY_SESSION_CLEANUP_FAILED')
        return held()


class OnlineReleaseTests(unittest.TestCase):
    def test_preflight_failure_prevents_public_intent_and_every_replacement(self):
        plan,old=fixture(); fake=Fake(plan,old); fake.fail_probe='final-http'
        with self.assertRaisesRegex(ValueError,'PROBE_FAILED'): release.execute(plan,fake)
        self.assertNotIn('publish',fake.events)
        self.assertNotIn('intent.json',fake.receipts)
        self.assertFalse(any(isinstance(e,tuple) and e[0]=='replace' for e in fake.events))

    def test_preflight_names_and_exact_negative_error_codes_are_strict(self):
        for value in [None,[],['unknown'],['final-http','final-http'],'final-http']:
            plan,_=fixture(); plan['preflightProbes']=value
            with self.subTest(preflight=value),self.assertRaisesRegex(ValueError,'EXPLICIT_PREFLIGHT_PROBES_REQUIRED'): release.validate(plan)
        for case in ['empty','invalid','type','long','kind','get','status','mixed']:
            plan,_=fixture()
            negative=dict(kind='http',url='http://synthetic/graphql',method='POST',query='query ReleaseOpsBoundary { tenants(limit:1) { id } }',expectedStatus=200,expectedErrorCodes=['FORBIDDEN'],attempts=1,intervalSeconds=0)
            if case=='empty': negative['expectedErrorCodes']=[]
            if case=='invalid': negative['expectedErrorCodes']=['forbidden']
            if case=='type': negative['expectedErrorCodes']='FORBIDDEN'
            if case=='long': negative['expectedErrorCodes']=['FORBIDDEN']*9
            if case=='kind': negative['kind']='employeeSchema'
            if case=='get': negative['method']='GET'
            if case=='status': negative['expectedStatus']=403
            if case=='mixed': negative['expectedText']='anything'
            plan['probes']['negative']=negative
            with self.subTest(case=case),self.assertRaisesRegex(ValueError,'NEGATIVE_PROBE_ASSERTION_INVALID'): release.validate(plan)

    def test_exact_http_graphql_negative_probe_is_a_valid_explicit_assertion(self):
        plan,_=fixture()
        plan['probes']['negative']=dict(kind='http',url='http://synthetic/graphql',method='POST',query='query ReleaseOpsBoundary { tenants(limit:1) { id } }',expectedStatus=200,expectedErrorCodes=['FORBIDDEN'],attempts=1,intervalSeconds=0)
        release.validate(plan)

    def test_caddy_exact_public_metadata_and_baseline_bindings_required_before_operations(self):
        for case in ['missing','ownerType','mode','size','inode','extra','identity','image','mount','readOnlyType']:
            plan,old=fixture(); proxy=plan['rootProxy']
            if case=='missing': del proxy['metadata']
            if case=='ownerType': proxy['metadata']['uid']=True
            if case=='mode': proxy['metadata']['mode']=0o666
            if case=='size': proxy['metadata']['size']=0
            if case=='inode': proxy['metadata']['inode']=2
            if case=='extra': proxy['metadata']['allowAnyOwner']=True
            if case=='identity': proxy['containerId']='7'*64
            if case=='image': proxy['image']=NEW
            if case=='mount': proxy['mountBinding']['destination']='relative'
            if case=='readOnlyType': proxy['mountBinding']['readOnly']=1
            fake=Fake(plan,old)
            with self.subTest(case=case),self.assertRaisesRegex(ValueError,'ROOT_PROXY_BINDING_REQUIRED'):
                release.execute(plan,fake)
            self.assertEqual(fake.events,[])

    def caddy_reader(self,proxy,raw,facts,after=None,path_facts=None,reader=None):
        class Stream(io.BytesIO):
            def fileno(self): return 42
        after=facts if after is None else after
        path_facts=facts if path_facts is None else path_facts
        with patch.object(Path,'resolve',lambda path:path),patch.object(Path,'lstat',return_value=path_facts),\
             patch.object(release.os,'O_NOFOLLOW',0x20000,create=True),patch.object(release.os,'open',return_value=42) as opened,\
             patch.object(release.os,'fdopen',return_value=Stream(raw)),patch.object(release.os,'fstat',side_effect=[facts,after]):
            value=(release.public_caddy_source if reader is None else reader)(proxy)
            self.assertEqual(opened.call_args.args[1],release.os.O_RDONLY|release.os.O_NOFOLLOW)
            return value

    def test_caddy_public_reader_accepts_only_exact_declared_nonroot_file(self):
        plan,_=fixture(); proxy=plan['rootProxy']; proxy['sha256']=H(b'abc')
        facts=SimpleNamespace(st_uid=1000,st_gid=1000,st_mode=stat.S_IFREG|0o644,st_ino=1,st_dev=2050,st_size=3)
        self.assertTrue(hasattr(release,'public_caddy_source'),'Dedicated exact-bound Caddy reader missing')
        self.assertEqual(self.caddy_reader(proxy,b'abc',facts),b'abc')
        for field,value in [('st_uid',0),('st_gid',0),('st_mode',stat.S_IFREG|0o600),('st_ino',2),('st_dev',2),('st_size',4)]:
            changed=SimpleNamespace(**{**vars(facts),field:value})
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'ROOT_PROXY_SOURCE_CHANGED'):
                self.caddy_reader(proxy,b'abc',changed)
        for raw in [b'abd',b'abcd']:
            with self.subTest(raw=raw),self.assertRaisesRegex(ValueError,'ROOT_PROXY_SOURCE_CHANGED'):
                self.caddy_reader(proxy,raw,facts)

    def test_caddy_reader_refuses_symlink_nonregular_and_read_time_replacement(self):
        plan,_=fixture(); proxy=plan['rootProxy']; proxy['sha256']=H(b'abc')
        facts=SimpleNamespace(st_uid=1000,st_gid=1000,st_mode=stat.S_IFREG|0o644,st_ino=1,st_dev=2050,st_size=3)
        self.assertTrue(hasattr(release,'public_caddy_source'),'Dedicated exact-bound Caddy reader missing')
        for changed in [SimpleNamespace(**{**vars(facts),'st_ino':2}),SimpleNamespace(**{**vars(facts),'st_mode':stat.S_IFLNK|0o644})]:
            for point in ['before','after','path']:
                with self.subTest(point=point),self.assertRaisesRegex(ValueError,'ROOT_PROXY_SOURCE_CHANGED'):
                    self.caddy_reader(proxy,b'abc',changed if point=='before' else facts,changed if point=='after' else facts,changed if point=='path' else facts)
        with patch.object(Path,'resolve',return_value=Path('/different')):
            with self.assertRaisesRegex(ValueError,'ROOT_PROXY_SOURCE_ALIAS'): release.public_caddy_source(proxy)

    def test_protected_reader_still_refuses_nonroot_receipts_even_with_public_mode(self):
        facts=SimpleNamespace(st_uid=1000,st_mode=stat.S_IFREG|0o644,st_size=3)
        class Stream(io.BytesIO):
            def fileno(self): return 42
        with patch.object(Path,'resolve',lambda path:path),patch.object(release.os,'O_NOFOLLOW',0x20000,create=True),\
             patch.object(release.os,'open',return_value=42),patch.object(release.os,'fdopen',return_value=Stream(b'abc')),patch.object(release.os,'fstat',return_value=facts):
            with self.assertRaisesRegex(ValueError,'PROTECTED_FILE_CHANGED'): release.protected('/root/receipt.json',0o644)

    def test_root_proxy_container_and_unique_exact_mount_binding_are_required(self):
        plan,_=fixture(); proxy=plan['rootProxy']
        container=dict(Id=proxy['containerId'],Image=proxy['image'],Name='/caddy',State={'Running':True},
                       Mounts=[dict(Type='bind',Source=proxy['source'],Destination='/etc/caddy/Caddyfile',RW=True)])
        self.assertTrue(hasattr(release,'root_proxy_container'),'Exact Caddy identity/mount guard missing')
        release.root_proxy_container(proxy,[container])
        for case in ['id','image','name','stopped','missing','duplicate','source','destination','readOnly']:
            changed=copy.deepcopy(container)
            if case=='id': changed['Id']='7'*64
            if case=='image': changed['Image']=NEW
            if case=='name': changed['Name']='/foreign'
            if case=='stopped': changed['State']['Running']=False
            if case=='missing': changed['Mounts']=[]
            if case=='duplicate': changed['Mounts']*=2
            if case=='source': changed['Mounts'][0]['Source']='/foreign'
            if case=='destination': changed['Mounts'][0]['Destination']='/foreign'
            if case=='readOnly': changed['Mounts'][0]['RW']=False
            with self.subTest(case=case),self.assertRaisesRegex(ValueError,'ROOT_PROXY_CONTAINER_OR_MOUNT_CHANGED'):
                release.root_proxy_container(proxy,[changed])

    def test_native_context_checks_bound_public_caddy_then_active_hash_by_container_id(self):
        plan,_=fixture(); proxy=plan['rootProxy']; proxy['sha256']=H(b'abc')
        engine={'synthetic':'engine'}; active={'synthetic':'active'}; proxy['activeSha256']=H(release.canonical(active))
        values={plan['sourceReceipt']['path']:b'{}',plan['grantsReceipt']['path']:json.dumps(dict(status='five_company_business_columns_verified',proofs=[{'allRequired':True}]*5)).encode(),
                plan['registryReceipt']['path']:json.dumps(dict(registrySql='SELECT synthetic',registry=[])).encode(),
                plan['hostDefaultsReceipt']['path']:json.dumps(dict(reviewedEngineDefaults=True,engineSha256=H(release.canonical(engine)),defaults={})).encode()}
        for key in ['sourceReceipt','grantsReceipt','registryReceipt','hostDefaultsReceipt']: plan[key]['sha256']=H(values[plan[key]['path']])
        compatibility=dict(applicationRollbackCompatible=True,newWritesCompatible=True,businessDataRestore=False,grantsRetained=True,sourceReceiptSha256=plan['sourceReceipt']['sha256'],selected=plan['selected'],policyGuard=dict(version=1,executorSha256=plan['policyExecutorSha256'],companies=plan['policyCompanies'],unchangedPolicyRequired=True))
        path=plan['rollback']['compatibilityReceipt']['path']; values[path]=json.dumps(compatibility).encode(); plan['rollback']['compatibilityReceipt']['sha256']=H(values[path])
        for path in plan['protectedFiles']: values[path]=b'preserved'; plan['protectedFiles'][path]=H(values[path])
        containers=[dict(Id=n,Config=dict(Labels={'com.docker.compose.project':'apps','com.docker.compose.service':n},Env=[])) for n in NAMES]
        containers.append(dict(Id=proxy['containerId'],Image=proxy['image'],Name='/caddy',Config={},State={'Running':True},Mounts=[dict(Type='bind',Source=proxy['source'],Destination=proxy['mountBinding']['destination'],RW=True)]))
        facts=SimpleNamespace(st_uid=1000,st_gid=1000,st_mode=stat.S_IFREG|0o644,st_ino=1,st_dev=2050,st_size=3)
        reader=release.public_caddy_source
        for drift in [False,True]:
            native=release.Native.__new__(release.Native); native.plan=plan; native.environment={n:{} for n in NAMES}; calls=[]
            native.operator=SimpleNamespace(database_sql=lambda db,sql:plan['systemId'] if db=='postgres' else '[]')
            def command(args,data=None):
                calls.append(args)
                if args[0]=='inspect': return json.dumps(containers)
                if args[0]=='ps': return 'selected caddy'
                if args[0]=='compose': return 'synthetic'
                if args[0]=='exec': return json.dumps(active)
                return '{}'
            def source(binding):
                changed=SimpleNamespace(**{**vars(facts),'st_uid':999}) if drift else facts
                return self.caddy_reader(binding,b'abc',changed,reader=reader)
            def protected(path,mode=0o600):
                self.assertNotEqual(str(path),proxy['source'],'Public Caddy file routed through root-only protected()')
                return values[str(path)]
            native.command=command
            with self.subTest(drift=drift),patch.object(release,'engine_contract',return_value=engine),patch.object(release,'protected',side_effect=protected),patch.object(release,'public_caddy_source',side_effect=source) as read_source:
                if drift:
                    with self.assertRaisesRegex(ValueError,'ROOT_PROXY_SOURCE_CHANGED'): native.context()
                    self.assertFalse(any(args[0]=='exec' for args in calls))
                else:
                    native.context()
                    self.assertIn(['exec',proxy['containerId'],'wget','-qO-','http://127.0.0.1:2019/config/'],calls)
                read_source.assert_called_once_with(proxy)

    def test_transition_only_selected_images_and_release_tag(self):
        plan, old = fixture()
        new = release.transition(plan, old)
        model = json.loads(new['compose.json'])
        original = json.loads(old['compose.json'])
        for name in NAMES:
            self.assertEqual(model['services'][name]['image'], NEW)
            original['services'][name]['image'] = NEW
        self.assertEqual(model, original)
        self.assertEqual(set(new), {'compose.json','release.json','release.sha256'})
    def test_success_serial_order_schema_gates_and_preservation(self):
        plan, old = fixture(); fake = Fake(plan, old)
        report = release.execute(plan, fake)
        self.assertEqual(report['status'], 'online_release_verified')
        self.assertEqual([e[1] for e in fake.events if isinstance(e,tuple) and e[0]=='replace'], NAMES)
        self.assertLess(fake.events.index(('probe','employee-schema')), fake.events.index(('replace','shared-gateway',NEW)))
        self.assertLess(fake.events.index(('probe','gateway-schema')), fake.events.index(('replace','shared-ui',NEW)))
        self.assertEqual(fake.fleet['preserved-worker'], plan['baselineFleet']['preserved-worker'])
    def test_stopped_unknown_dormant_or_missing_probe_rejected(self):
        for case in ['stopped','unknown','dormant','probe']:
            plan, old = fixture()
            if case=='stopped': plan['baselineFleet']['shared-employee']['running']=False
            if case=='unknown': plan['selected'][0]['service']='unknown'
            if case=='dormant': plan['selected'][0]['service']='private-audit-dormant'
            if case=='probe': plan['selected'][0]['readiness']=[]
            with self.subTest(case=case), self.assertRaises(ValueError): release.execute(plan, Fake(plan,old))
    def test_missing_employee_or_wrong_phase_order_rejected(self):
        for case in ['gate','order','placeholder']:
            plan, old=fixture()
            if case=='gate': plan['employeeGate']=[]
            if case=='order': plan['selected'].reverse()
            if case=='placeholder': plan['selected'][0]['newImage']='PENDING_BUILD'
            with self.subTest(case=case), self.assertRaises(ValueError): release.execute(plan,Fake(plan,old))
    def test_partial_failure_reviewed_rollback_preserves_grants_and_old_bytes(self):
        plan,old=fixture(); fake=Fake(plan,old); fake.fail_probe='ready-gateway'
        with self.assertRaisesRegex(ValueError,'ROLLED_BACK'): release.execute(plan,fake)
        self.assertEqual(fake.files,old)
        self.assertEqual(fake.receipts['failure.json']['recovery'],'rolled_back')
        self.assertTrue(fake.receipts['failure.json']['grantsRetained'])
        self.assertNotIn(('replace','shared-ui',NEW),fake.events)

    def test_policy_drift_refuses_every_old_replacement_and_preserves_new_policy(self):
        plan,old=fixture(); fake=Fake(plan,old)
        original=fake.probe
        def changed(name):
            if name=='ready-gateway': fake.policy_drift=True; raise ValueError('SYNTHETIC_PROBE_FAILURE')
            original(name)
        fake.probe=changed
        with self.assertRaisesRegex(ValueError,'OPERATOR_REVIEW'): release.execute(plan,fake)
        self.assertFalse(any(isinstance(e,tuple) and e[0]=='replace' and e[2]==OLD for e in fake.events))
        self.assertTrue(fake.policy_drift)
        self.assertIn('policy-baseline.json',fake.receipts)

    def test_policy_locks_cover_all_old_replacements_restore_and_final_probes(self):
        plan,old=fixture(); fake=Fake(plan,old); fake.fail_probe='ready-gateway'
        with self.assertRaisesRegex(ValueError,'ROLLED_BACK'): release.execute(plan,fake)
        self.assertTrue(fake.old_policy_states and all(fake.old_policy_states))
        self.assertEqual(fake.restore_policy_states,[True])
        self.assertLess(fake.events.index(('probe','rollback-http')),fake.events.index('rollback-policy-release'))
        self.assertLess(fake.events.index('policy-capture'),fake.events.index('publish'))

    def test_policy_cleanup_failure_is_operator_review_even_after_restoration(self):
        plan,old=fixture(); fake=Fake(plan,old); fake.fail_probe='ready-gateway'; fake.policy_cleanup_failure=True
        with self.assertRaisesRegex(ValueError,'OPERATOR_REVIEW'): release.execute(plan,fake)
        self.assertEqual(fake.receipts['failure.json']['recovery'],'operator_review_required')

    def test_policy_lock_loss_stops_before_next_old_replacement(self):
        plan,old=fixture(); fake=Fake(plan,old); fake.fail_probe='ready-gateway'; original=fake.replace
        def changed(name,image):
            original(name,image)
            if image==OLD: fake.policy_held=False
        fake.replace=changed
        with self.assertRaisesRegex(ValueError,'OPERATOR_REVIEW'): release.execute(plan,fake)
        self.assertEqual(len(fake.old_policy_states),1)

    def test_successful_online_release_allows_policy_changes_after_initial_capture(self):
        plan,old=fixture(); fake=Fake(plan,old); original=fake.probe
        def changed(name):
            if name=='ready-employee': fake.policy_drift=True
            original(name)
        fake.probe=changed
        self.assertEqual(release.execute(plan,fake)['status'],'online_release_verified')
        self.assertTrue(fake.policy_drift)
        self.assertNotIn('rollback-policy-acquire',fake.events)
    def test_rollback_failure_marks_operator_review(self):
        plan,old=fixture(); fake=Fake(plan,old); fake.fail_probe='ready-gateway'; fake.fail_rollback='shared-gateway'
        with self.assertRaisesRegex(ValueError,'OPERATOR_REVIEW'): release.execute(plan,fake)
        self.assertEqual(fake.receipts['failure.json']['recovery'],'operator_review_required')
    def test_ambiguous_replacement_refuses_automatic_rollback(self):
        plan,old=fixture(); fake=Fake(plan,old); fake.fail_replace='shared-gateway'
        with self.assertRaisesRegex(ValueError,'OPERATOR_REVIEW'): release.execute(plan,fake)
        self.assertFalse(any(isinstance(e,tuple) and e[0]=='replace' and e[2]==OLD for e in fake.events))
    def test_unrelated_drift_before_apply_refused(self):
        plan,old=fixture(); fake=Fake(plan,old); fake.fleet['preserved-worker']['id']='foreign'
        with self.assertRaises(ValueError): release.execute(plan,fake)
        self.assertFalse(any(isinstance(e,tuple) and e[0]=='replace' for e in fake.events))
    def test_main_entry_hash_gate_and_simulated_complete_flow(self):
        plan,old=fixture(); fake=Fake(plan,old)
        path=Path(__file__).with_name('.online-test-'+uuid.uuid4().hex+'.json')
        try:
            path.write_text(json.dumps(plan)); digest=H(path.read_bytes())
            report=release.main(['--apply','--plan',str(path),'--plan-sha256',digest],adapter_factory=lambda p:fake,root_check=lambda:True)
            self.assertEqual(report['status'],'online_release_verified')
            with self.assertRaisesRegex(ValueError,'PLAN_CHANGED'):
                release.main(['--apply','--plan',str(path),'--plan-sha256','0'*64],adapter_factory=lambda p:fake,root_check=lambda:True)
        finally:
            if path.exists(): path.unlink()
    def test_no_implicit_probe_or_shell_mutation(self):
        plan,old=fixture(); plan['probes']['ready-employee'].update(method='POST',query='mutation { grantAdmin }')
        with self.assertRaises(ValueError): release.execute(plan,Fake(plan,old))

    def test_schema_gate_cannot_be_health_only(self):
        plan,old=fixture(); plan['probes']['employee-schema']=dict(plan['probes']['ready-employee'],kind='employeeSchema')
        with self.assertRaisesRegex(ValueError,'COMPLETE_SCHEMA'): release.execute(plan,Fake(plan,old))

    def test_source_contract_drift_stops_recovery(self):
        plan,old=fixture(); fake=Fake(plan,old)
        original=fake.replace
        def changed(name,image):
            original(name,image)
            fake.fleet[name]['contractSha256']='8'*64
        fake.replace=changed
        with self.assertRaisesRegex(ValueError,'OPERATOR_REVIEW'): release.execute(plan,fake)
        self.assertFalse(any(isinstance(e,tuple) and e[0]=='replace' and e[2]==OLD for e in fake.events))

    def test_missing_rollback_service_probe_rejected(self):
        plan,old=fixture(); plan['rollback']['readiness']['shared-employee']=[]
        with self.assertRaisesRegex(ValueError,'ROLLBACK_READINESS'): release.execute(plan,Fake(plan,old))

    def test_native_replacement_command_has_explicit_safe_selection(self):
        plan,old=fixture(); native=release.Native.__new__(release.Native)
        native.plan=plan; native.root=Path('/opt/apps/hrms'); native.work=Path('/synthetic-journal')
        commands=[]; saved={}; native.command=lambda args,data=None: commands.append(args)
        native.save=lambda name,value:saved.update({name:value})
        native.verify_environment=lambda name,image:{'existing':{'external':True,'name':'existing'}}
        with patch.object(release,'protected',return_value=old['compose.json']):
            native.replace('shared-employee',NEW)
        command=commands[0]
        self.assertEqual(command[-1],'shared-employee')
        for option in ['--no-deps','--no-build','--force-recreate']: self.assertIn(option,command)
        self.assertEqual(command[command.index('--pull')+1],'never')
        self.assertEqual(command[command.index('--env-file')+1],'/dev/null')
        self.assertEqual(set(next(iter(saved.values()))['services']),{'shared-employee'})

    def test_native_readonly_probe_uses_pinned_isolated_image_and_no_shell(self):
        plan,_=fixture(); native=release.Native.__new__(release.Native); native.plan=plan
        calls=[]
        def command(args,data=None):
            if args[:2]==['network','inspect']: return json.dumps([{'Id':plan['probeRuntime']['networkId']}])
            calls.append((args,json.loads(data))); return '{"ok":true}'
        native.command=command; native.probe('employee-schema')
        args,payload=calls[0]
        for option in ['--read-only','--cap-drop','--security-opt','--log-driver']: self.assertIn(option,args)
        self.assertIn(plan['probeRuntime']['image'],args)
        self.assertEqual(args[args.index('--entrypoint')+1],'node')
        self.assertEqual(payload['method'],'POST')
        self.assertTrue(payload['query'].startswith('query'))

    def test_unknown_probe_network_key_fails_before_any_operation(self):
        for key in ['unreviewed', '', None, False, ['business']]:
            plan,old=fixture(); plan['probeNetworks']={'business':dict(name='business',id='5'*64)}
            plan['probes']['employee-schema']['networkKey']=key
            fake=Fake(plan,old)
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'PROBE_NETWORK_KEY_INVALID'):
                release.execute(plan,fake)
            self.assertEqual(fake.events,[])

    def test_invalid_reviewed_network_binding_fails_before_any_operation(self):
        invalid=[None,[],{'bad key':dict(name='business',id='5'*64)},
                 {'business':None},{'business':dict(name='--host',id='5'*64)},
                 {'business':dict(name='business',id='5'*63)},
                 {'business':dict(name='business',id='G'*64)},
                 {'business':dict(name='business',id='5'*64,driver='bridge')},
                 {'business':dict(name='business',networkId='5'*64)}]
        for networks in invalid:
            plan,old=fixture(); plan['probeNetworks']=networks; fake=Fake(plan,old)
            with self.subTest(networks=networks),self.assertRaisesRegex(ValueError,'PROBE_NETWORK_BINDING_INVALID'):
                release.execute(plan,fake)
            self.assertEqual(fake.events,[])

    def test_native_routes_default_and_two_reviewed_networks_with_one_pinned_image(self):
        plan,_=fixture()
        plan['probeNetworks']={'business':dict(name='apps_business',id='5'*64),
                               'organization':dict(name='hrms_organization',id='6'*64)}
        plan['probes']['employee-schema']['networkKey']='business'
        plan['probes']['rollback-http']['networkKey']='organization'
        release.validate(plan)
        native=release.Native.__new__(release.Native); native.plan=plan; calls=[]
        ids={'existing':'4'*64,'apps_business':'5'*64,'hrms_organization':'6'*64}
        def command(args,data=None):
            calls.append(args)
            if args[:2]==['network','inspect']: return json.dumps([{'Id':ids[args[2]]}])
            return '{"ok":true}'
        native.command=command
        for name in ['final-http','employee-schema','rollback-http']: native.probe(name)
        runs=[args for args in calls if args[0]=='run']
        self.assertEqual([args[args.index('--network')+1] for args in runs],list(ids.values()))
        for args in runs:
            self.assertEqual(args.count('--network'),1)
            self.assertEqual(args[args.index('--entrypoint')+1],'node')
            self.assertEqual(args[args.index('-e')-1],OLD)
        self.assertEqual([args for args in calls if args[0]=='network'],
                         [['network','inspect',name] for name in ids])

    def test_native_refuses_reviewed_network_drift_before_running_probe(self):
        for explicit in [False,True]:
            plan,_=fixture(); plan['probeNetworks']={'business':dict(name='apps_business',id='5'*64)}
            if explicit: plan['probes']['employee-schema']['networkKey']='business'
            native=release.Native.__new__(release.Native); native.plan=plan; calls=[]
            def command(args,data=None):
                calls.append(args); return json.dumps([{'Id':'f'*64}])
            native.command=command
            with self.subTest(explicit=explicit),self.assertRaisesRegex(ValueError,'PROBE_NETWORK_CHANGED'):
                native.probe('employee-schema')
            expected='apps_business' if explicit else 'existing'
            self.assertEqual(calls,[['network','inspect',expected]])

    def test_native_rechecks_reviewed_network_id_before_retry(self):
        plan,_=fixture(); plan['probeNetworks']={'business':dict(name='apps_business',id='5'*64)}
        plan['probes']['employee-schema'].update(networkKey='business',attempts=2)
        native=release.Native.__new__(release.Native); native.plan=plan; calls=[]; inspections=0
        def command(args,data=None):
            nonlocal inspections
            calls.append(args)
            if args[:2]==['network','inspect']:
                inspections+=1; return json.dumps([{'Id':('5' if inspections==1 else 'f')*64}])
            raise ValueError('SYNTHETIC_HTTP_FAILURE')
        native.command=command
        with self.assertRaisesRegex(ValueError,'PROBE_NETWORK_CHANGED'): native.probe('employee-schema')
        self.assertEqual(sum(args[0]=='run' for args in calls),1)
        self.assertEqual(inspections,2)

    def test_fleet_snapshot_exports_hash_and_rejects_duplicate_selected_service(self):
        item=dict(Name='/apps-shared-employee-1',Id='synthetic-id',Image=OLD,RestartCount=0,
                  Config=dict(Labels={'com.docker.compose.project':'apps','com.docker.compose.service':'shared-employee'},Cmd=['fixed'],Entrypoint=None,User='1000',Env=['PRIVATE_TEST=synthetic-secret']),
                  Mounts=[],HostConfig={'ReadonlyRootfs':True},NetworkSettings={'Networks':{}},State=dict(Running=True,StartedAt='synthetic'))
        before=release.fleet_snapshot([item]); self.assertNotIn('synthetic-secret',json.dumps(before))
        changed=copy.deepcopy(item); changed['Config']['Env']=['PRIVATE_TEST=changed']
        self.assertEqual(before['shared-employee']['contractSha256'],release.fleet_snapshot([changed])['shared-employee']['contractSha256'])
        with self.assertRaisesRegex(ValueError,'AMBIGUOUS'): release.fleet_snapshot([item,item])

    def test_private_resolved_environment_must_equal_running_environment(self):
        plan,_=fixture(); native=release.Native.__new__(release.Native); native.plan=plan
        native.root=Path('/opt/apps/hrms'); native.environment={'shared-employee':{'PATH':'fixed','PRIVATE_TEST':'synthetic-secret'}}
        native.hostDefaults={}
        native.privateContracts={'shared-employee':dict(Config={},Mounts=[],HostConfig={},NetworkSettings={'Networks':{}})}
        native.model_file=lambda name,image:Path('/synthetic-model.json')
        def command(args,data=None):
            if args[:2]==['image','inspect']: return json.dumps([{'Config':{'Env':['PATH=fixed']}}])
            return json.dumps({'services':{'shared-employee':{'environment':{'PRIVATE_TEST':'synthetic-secret'}}}})
        native.command=command; native.verify_environment('shared-employee',NEW)
        native.environment['shared-employee']['PRIVATE_TEST']='different'
        with self.assertRaisesRegex(ValueError,'INTENDED_ENVIRONMENT_CHANGED'): native.verify_environment('shared-employee',NEW)
        with self.assertRaisesRegex(ValueError,'ENVIRONMENT_AMBIGUOUS'): release.env_map(['A=1','A=2'])

    def test_intended_source_contract_drift_refused_before_recreation(self):
        before=dict(Config={'Cmd':['fixed'],'User':'1000'},HostConfig={},Mounts=[],NetworkSettings={'Networks':{'existing':{}}})
        model={'services':{'shared-employee':{'command':['fixed'],'user':'1000','networks':{'network':{}}}},'networks':{'network':{'name':'existing'}}}
        release.intended_contract(model,'shared-employee',{},before)
        for case in ['command','mount','network','security']:
            changed=copy.deepcopy(model)
            if case=='command': changed['services']['shared-employee']['command']=['foreign']
            if case=='mount': changed['services']['shared-employee']['volumes']=[dict(type='bind',source='/foreign',target='/private')]
            if case=='network': changed['networks']['network']['name']='foreign'
            if case=='security': changed['services']['shared-employee']['privileged']=True
            with self.subTest(case=case), self.assertRaises(ValueError): release.intended_contract(changed,'shared-employee',{},before)

    def test_rollback_requires_exact_review_of_new_write_compatibility(self):
        plan,_=fixture(); receipt=dict(applicationRollbackCompatible=True,businessDataRestore=False,grantsRetained=True,newWritesCompatible=True,sourceReceiptSha256=plan['sourceReceipt']['sha256'],selected=copy.deepcopy(plan['selected']),policyGuard=dict(version=1,executorSha256=plan['policyExecutorSha256'],companies=plan['policyCompanies'],unchangedPolicyRequired=True))
        release.reviewed_recovery(plan,receipt)
        for key in ['applicationRollbackCompatible','newWritesCompatible','grantsRetained','sourceReceiptSha256','selected']:
            changed=copy.deepcopy(receipt); changed[key]=False
            with self.subTest(key=key), self.assertRaises(ValueError): release.reviewed_recovery(plan,changed)

    def test_recovery_receipt_must_review_exact_conditional_policy_guard(self):
        plan,_=fixture()
        receipt=dict(applicationRollbackCompatible=True,businessDataRestore=False,grantsRetained=True,newWritesCompatible=True,sourceReceiptSha256=plan['sourceReceipt']['sha256'],selected=plan['selected'])
        binding=dict(version=1,executorSha256=plan['policyExecutorSha256'],companies=copy.deepcopy(plan['policyCompanies']),unchangedPolicyRequired=True)
        for case in ['missing','version','source','companies','condition','extra']:
            changed=copy.deepcopy(receipt); value=copy.deepcopy(binding)
            if case=='version': value['version']=True
            if case=='source': value['executorSha256']='0'*64
            if case=='companies': value['companies'].pop()
            if case=='condition': value['unchangedPolicyRequired']=False
            if case=='extra': value['unconditional']=True
            if case!='missing': changed['policyGuard']=value
            with self.subTest(case=case),self.assertRaisesRegex(ValueError,'ROLLBACK_POLICY_COMPATIBILITY_NOT_REVIEWED'):
                release.reviewed_recovery(plan,changed)

    def test_reviewed_new_artifact_hash_mismatch_prevents_publication(self):
        plan,old=fixture(); plan['newArtifacts']['compose.json']='0'*64; fake=Fake(plan,old)
        with self.assertRaisesRegex(ValueError,'REVIEWED_TRANSITION_CHANGED'): release.execute(plan,fake)
        self.assertNotIn('publish',fake.events)

    def test_main_requires_explicit_root_apply_before_reading_plan(self):
        with self.assertRaisesRegex(ValueError,'ROOT_EXPLICIT_APPLY'):
            release.main(['--plan','missing','--plan-sha256','0'*64],root_check=lambda:True)

    def test_all_host_security_and_resource_drift_fails_before_recreation(self):
        changes={'CapDrop':['ALL'],'CapAdd':['SYS_ADMIN'],'SecurityOpt':['no-new-privileges:true'],
                 'Memory':67108864,'MemoryReservation':1024,'MemorySwap':-1,'MemorySwappiness':60,
                 'PidsLimit':64,'NanoCpus':500000000,'CpuShares':256,'CpuPeriod':100000,'CpuQuota':50000,
                 'CpuRealtimePeriod':400000,'CpuRealtimeRuntime':200000,'CpusetCpus':'0-1','CpusetMems':'0',
                 'OomKillDisable':True,'OomScoreAdj':100,
                 'Init':True,'RestartPolicy':{'Name':'unless-stopped','MaximumRetryCount':0},
                 'Ulimits':[{'Name':'nofile','Soft':1024,'Hard':2048}],
                 'Tmpfs':{'/tmp':'rw,size=64m'},'Runtime':'unreviewed-runtime',
                 'PidMode':'host','IpcMode':'host','UTSMode':'host','UsernsMode':'host',
                 'CgroupnsMode':'host','ShmSize':67108864}
        for field,value in changes.items():
            before=dict(Config={},Mounts=[],HostConfig={field:value},NetworkSettings={'Networks':{}})
            with self.subTest(field=field), self.assertRaises(ValueError):
                release.intended_contract({'services':{'shared-employee':{}}},'shared-employee',{},before)

    def test_first_release_output_is_valid_next_release_input(self):
        plan,old=fixture(); first_adapter=Fake(plan,old); release.execute(plan,first_adapter); current=first_adapter.files
        second=copy.deepcopy(plan); second['tag']='next'
        second['baselineFleet']=copy.deepcopy(first_adapter.fleet)
        second['oldArtifacts']={n:H(v) for n,v in current.items()}
        second['previousBytes']={n:base64.b64encode(v).decode() for n,v in current.items()}
        for step in second['selected']:
            step['repository']='kabipay-svc' if step['phase']=='backend' else 'kabipay-'+step['phase']
            step['oldImageReference']=NEW
            step['oldRepositoryTag']=step['repository']+':reviewed-first-release'
            step['oldImage']=NEW; step['newImage']='sha256:'+'3'*64
            second['baselineFleet'][step['service']]['image']=NEW
        result=release.transition(second,current)
        self.assertTrue(all(s['image']=='sha256:'+'3'*64 for n,s in json.loads(result['compose.json'])['services'].items() if n in NAMES))
        second['newArtifacts']={n:H(v) for n,v in result.items()}
        self.assertEqual(release.execute(second,Fake(second,current))['status'],'online_release_verified')

    def test_explicit_null_command_and_entrypoint_inherit_pinned_image(self):
        before=dict(Config={'Cmd':['image-command'],'Entrypoint':['image-entrypoint']},HostConfig={},Mounts=[],NetworkSettings={'Networks':{}})
        model={'services':{'shared-employee':{'command':None,'entrypoint':None}}}
        release.intended_contract(model,'shared-employee',dict(Cmd=['image-command'],Entrypoint=['image-entrypoint']),before)

    def test_explicit_supported_host_contract_preserves_all_limits(self):
        service=dict(cap_drop=['ALL'],cap_add=['CAP_NET_BIND_SERVICE'],security_opt=['no-new-privileges:true'],
                     mem_limit='64m',mem_reservation=1024,memswap_limit=-1,pids_limit=64,cpus='0.5',cpu_shares=128,
                     read_only=True,init=True,restart='unless-stopped',ulimits={'nofile':{'soft':1024,'hard':2048}},tmpfs=['/tmp:rw,size=64m'])
        actual=dict(CapDrop=['ALL'],CapAdd=['NET_BIND_SERVICE'],SecurityOpt=['no-new-privileges'],
                    Memory=67108864,MemoryReservation=1024,MemorySwap=-1,PidsLimit=64,NanoCpus=500000000,CpuShares=128,
                    ReadonlyRootfs=True,Init=True,RestartPolicy={'Name':'unless-stopped','MaximumRetryCount':0},
                    Ulimits=[{'Name':'nofile','Soft':1024,'Hard':2048}],Tmpfs={'/tmp':'size=64m,rw'},Runtime='runc',IpcMode='private')
        release.host_contract(service,actual,{'Runtime':'runc','IpcMode':'private'})
        for key in ['cap_drop','security_opt','mem_limit','pids_limit','cpus','init','restart','ulimits','tmpfs']:
            changed=copy.deepcopy(service); del changed[key]
            with self.subTest(key=key),self.assertRaises(ValueError): release.host_contract(changed,actual,{'Runtime':'runc','IpcMode':'private'})

    def test_host_contract_unknowns_and_defaults_cannot_hide_security_drift(self):
        for service,actual,defaults in [({}, {'FutureUnmappedIsolation':True}, {}),
                                        ({'deploy':{'resources':{'limits':{'memory':'64m'}}}}, {}, {}),
                                        ({}, {'CapDrop':['ALL']}, {'CapDrop':['ALL']}),
                                        ({}, {'Runtime':'runc'}, {}),
                                        ({}, {'Devices':[{'PathOnHost':'/dev/foreign'}]}, {})]:
            with self.subTest(actual=actual),self.assertRaises(ValueError): release.host_contract(service,actual,defaults)

    def test_host_drift_is_rejected_before_publication(self):
        plan,old=fixture(); fake=Fake(plan,old)
        fake.context=lambda:release.host_contract({},dict(CapDrop=['ALL']),{})
        with self.assertRaises(ValueError): release.execute(plan,fake)
        self.assertNotIn('publish',fake.events)
        self.assertFalse(any(isinstance(e,tuple) and e[0]=='replace' for e in fake.events))

    def test_digest_image_requires_reviewed_family_and_metadata_identity(self):
        plan,old=fixture(); step=plan['selected'][0]
        metadata={'Id':OLD,'RepoTags':[step['oldRepositoryTag']]}
        release.image_family_proof(step,metadata,OLD)
        for changed,identity in [({'Id':NEW,'RepoTags':metadata['RepoTags']},OLD),({'Id':OLD,'RepoTags':['foreign:tag']},OLD),(metadata,NEW)]:
            with self.subTest(metadata=changed),self.assertRaises(ValueError): release.image_family_proof(step,changed,identity)

    def test_bind_isolation_needs_reviewed_default_and_exact_host_options(self):
        service={'volumes':[dict(type='bind',source='/synthetic',target='/run/source',read_only=True,bind={'create_host_path':False})]}
        before=dict(Config={},Mounts=[dict(Type='bind',Source='/synthetic',Destination='/run/source',RW=False,Propagation='rprivate')],NetworkSettings={'Networks':{}},HostConfig={'Mounts':[dict(Type='bind',Source='/synthetic',Target='/run/source',ReadOnly=True,BindOptions={'CreateMountpoint':False})]})
        model={'services':{'shared-employee':service}}
        release.intended_contract(model,'shared-employee',{},before,{'BindPropagation':'rprivate'})
        with self.assertRaisesRegex(ValueError,'BIND_PROPAGATION'): release.intended_contract(model,'shared-employee',{},before)
        changed=copy.deepcopy(before); changed['HostConfig']['Mounts'][0]['BindOptions']['ReadOnlyNonRecursive']=True
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_BIND_HOST_OPTIONS'): release.intended_contract(model,'shared-employee',{},changed,{'BindPropagation':'rprivate'})

    def test_complete_engine_default_fingerprint_rejects_missing_metadata(self):
        with self.assertRaisesRegex(ValueError,'ENGINE_DEFAULT_EVIDENCE_INCOMPLETE'): release.engine_contract({},'synthetic-compose')

    def test_native_empty_devices_null_and_omitted_are_equivalent(self):
        for actual in [{},{'Devices':None},{'Devices':[]}]:
            with self.subTest(actual=actual): release.host_contract({},actual,{})

    def test_neutral_collections_reject_nonempty_and_wrong_collection_types(self):
        for field,empty in [('Devices',[]),('DeviceRequests',[]),('Links',[]),('StorageOpt',{}),('Annotations',{})]:
            for value in [None,empty]:
                with self.subTest(field=field,value=value): release.host_contract({},{field:value},{})
            for value in ([{},False,0,'',[{'PathOnHost':'/dev/foreign'}]] if isinstance(empty,list) else [[],False,0,'',{'key':'value'}]):
                with self.subTest(field=field,value=value),self.assertRaisesRegex(ValueError,'UNSUPPORTED_NONDEFAULT_HOST_SETTING'):
                    release.host_contract({},{field:value},{})

    def test_native_memory_limit_derives_omitted_swap_total(self):
        release.host_contract({'mem_limit':'128m'},{'Memory':134217728,'MemorySwap':268435456},{})
        release.host_contract({'mem_limit':'128m','memswap_limit':0},{'Memory':134217728,'MemorySwap':268435456},{})
        release.host_contract({},{'Memory':0,'MemorySwap':0},{})
        for actual in [0,134217728,-1,402653184]:
            with self.subTest(swap=actual),self.assertRaisesRegex(ValueError,'INTENDED_HOST_SECURITY_OR_RESOURCE_CHANGED'):
                release.host_contract({'mem_limit':'128m'},{'Memory':134217728,'MemorySwap':actual},{})

    def test_explicit_swap_limit_remains_exact(self):
        for configured,actual in [('128m',134217728),(-1,-1)]:
            release.host_contract({'mem_limit':'128m','memswap_limit':configured},{'Memory':134217728,'MemorySwap':actual},{})
            with self.assertRaisesRegex(ValueError,'INTENDED_HOST_SECURITY_OR_RESOURCE_CHANGED'):
                release.host_contract({'mem_limit':'128m','memswap_limit':configured},{'Memory':134217728,'MemorySwap':268435456},{})

    def test_dynamic_list_empty_serialization_preserves_nonempty_contracts(self):
        for field in ['Dns','DnsOptions','DnsSearch','MaskedPaths','ReadonlyPaths']:
            for expected,actual in [([],None),(None,[]),(['required'],['required'])]:
                with self.subTest(field=field,expected=expected,actual=actual): release.host_contract({},{field:actual},{field:expected})
            for expected,actual in [([],{}),([],''),([],False),(['required'],None),(['required'],[]),(['required'],['foreign'])]:
                with self.subTest(field=field,expected=expected,actual=actual),self.assertRaises(ValueError):
                    release.host_contract({},{field:actual},{field:expected})

    def test_logging_config_empty_serialization_preserves_driver_and_options(self):
        for expected,actual in [({},None),(None,{}),({'max-size':'10m'},{'max-size':'10m'})]:
            release.host_contract({},{'LogConfig':dict(Type='json-file',Config=actual)},{'LogConfig':dict(Type='json-file',Config=expected)})
        for actual in [dict(Type='none',Config={}),dict(Type='json-file',Config=[]),dict(Type='json-file',Config={'max-size':'20m'}),dict(Type='json-file',Config=None,Future=True)]:
            with self.subTest(actual=actual),self.assertRaises(ValueError):
                release.host_contract({},{'LogConfig':actual},{'LogConfig':dict(Type='json-file',Config={'max-size':'10m'})})


if __name__=='__main__':
    import sys
    unittest.main(testRunner=unittest.TextTestRunner(stream=sys.stdout))
