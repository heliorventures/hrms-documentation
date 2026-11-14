"""Order-independent mount contracts and safe failure-journal regressions."""
import copy
import json
import unittest

from test_online_release import Fake, NEW, fixture, release

def container():
    return dict(Name='/apps-shared-employee-1',Id='synthetic',Image=NEW,RestartCount=0,
                Config=dict(Labels={'com.docker.compose.project':'apps','com.docker.compose.service':'shared-employee'},Cmd=['employee'],Entrypoint=None,User='1000'),
                Mounts=[dict(Type='bind',Source='/a',Destination='/run/a',RW=False),dict(Type='bind',Source='/b',Destination='/run/b',RW=True)],
                HostConfig=dict(ReadonlyRootfs=True,Mounts=[dict(Type='bind',Source='/a',Target='/run/a',ReadOnly=True,BindOptions={}),dict(Type='bind',Source='/b',Target='/run/b',BindOptions={})]),
                NetworkSettings={'Networks':{}},State=dict(Running=True,StartedAt='synthetic'))

class ContractTests(unittest.TestCase):
    def fingerprint(self,value):return release.fleet_snapshot([value])['shared-employee']['contractSha256']

    def test_mount_order_does_not_change_fingerprint(self):
        first=container();second=copy.deepcopy(first)
        second['Mounts'].reverse();second['HostConfig']['Mounts'].reverse()
        self.assertEqual(self.fingerprint(first),self.fingerprint(second))
        self.assertNotEqual(first,second)

    def test_mount_values_and_host_security_still_change_fingerprint(self):
        first=container()
        for field in ['source','rw','propagation','hostSource','hostReadOnly','bindOptions','security']:
            second=copy.deepcopy(first)
            if field=='source':second['Mounts'][0]['Source']='/foreign'
            if field=='rw':second['Mounts'][0]['RW']=True
            if field=='propagation':second['Mounts'][0]['Propagation']='shared'
            if field=='hostSource':second['HostConfig']['Mounts'][0]['Source']='/foreign'
            if field=='hostReadOnly':second['HostConfig']['Mounts'][0]['ReadOnly']=False
            if field=='bindOptions':second['HostConfig']['Mounts'][0]['BindOptions']={'Propagation':'shared'}
            if field=='security':second['HostConfig']['ReadonlyRootfs']=False
            with self.subTest(field=field):self.assertNotEqual(self.fingerprint(first),self.fingerprint(second))

    def test_duplicate_mount_targets_are_refused(self):
        for field in ['Mounts','HostConfig']:
            value=container()
            rows=value['Mounts'] if field=='Mounts' else value['HostConfig']['Mounts']
            rows.append(copy.deepcopy(rows[0]))
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'AMBIGUOUS_MOUNT_TARGET'):self.fingerprint(value)

    def test_alias_and_other_array_order_is_not_normalized(self):
        first=container();first['NetworkSettings']['Networks']={'app':{'Aliases':['one','two'],'NetworkID':'network'}}
        second=copy.deepcopy(first);second['NetworkSettings']['Networks']['app']['Aliases'].reverse()
        self.assertNotEqual(self.fingerprint(first),self.fingerprint(second))

    def test_fingerprint_algorithm_binding_tracks_bodies_not_locations(self):
        source=b'def ordered_mounts(a,b): return a\ndef container_contract(a): return a\ndef fleet_snapshot(a): return a\n'
        self.assertEqual(release.fingerprint_code(source),release.fingerprint_code(b'\n\n'+source+b'\ndef unrelated(): pass\n'))
        self.assertNotEqual(release.fingerprint_code(source),release.fingerprint_code(source.replace(b'return a',b'return {}',1)))

    def test_fingerprint_version_is_required_before_operations(self):
        plan,old=fixture();plan.pop('contractFingerprintVersion',None)
        fake=Fake(plan,old)
        with self.assertRaisesRegex(ValueError,'CONTRACT_FINGERPRINT_VERSION'):release.execute(plan,fake)
        self.assertEqual(fake.events,[])

    def test_forward_and_recovery_failure_locations_are_saved(self):
        plan,old=fixture();fake=Fake(plan,old)
        def probe(name):
            if name=='ready-employee':raise ValueError('EXPLICIT_HTTP_PROBE_FAILED')
        fake.probe=probe;fake.fail_rollback='shared-employee'
        with self.assertRaisesRegex(ValueError,'OPERATOR_REVIEW'):release.execute(plan,fake)
        failure=fake.receipts['failure.json']
        self.assertEqual(failure['primaryFailure'],dict(stage='service_readiness',service='shared-employee',probe='ready-employee',code='EXPLICIT_HTTP_PROBE_FAILED',errorType='ValueError'))
        self.assertEqual(failure['recoveryFailure']['stage'],'recovery_replace')
        self.assertEqual(failure['recoveryFailure']['service'],'shared-employee')

    def test_unknown_exception_text_never_enters_receipt(self):
        plan,old=fixture();fake=Fake(plan,old)
        def probe(name):
            if name=='ready-employee':raise ValueError('PRIVATE_PASSWORD_AND_TOKEN')
        fake.probe=probe
        with self.assertRaisesRegex(ValueError,'ROLLED_BACK'):release.execute(plan,fake)
        failure=fake.receipts['failure.json']
        self.assertEqual(failure['primaryFailure']['code'],'UNCLASSIFIED_RELEASE_FAILURE')
        self.assertIsNone(failure['recoveryFailure'])
        self.assertNotIn('PRIVATE_PASSWORD',json.dumps(fake.receipts))

if __name__=='__main__':unittest.main()
