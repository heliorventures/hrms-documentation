"""Synthetic resume validation; no Docker, database, network or production input."""
import copy
import importlib.util
from pathlib import Path
import unittest
from test_online_release import Fake, NEW, fixture, release

spec=importlib.util.spec_from_file_location('resume',Path(__file__).with_name('online-release-resume.py'))
resume=importlib.util.module_from_spec(spec);spec.loader.exec_module(resume)

def inputs():
    original,old=fixture();current=release.transition(original,old)
    artifacts={**original['oldArtifacts'],**{n:release.sha(v) for n,v in current.items()}}
    fleet=copy.deepcopy(original['baselineFleet']);fleet['shared-employee'].update(image=NEW,id='employee-new')
    contracts={'version':2,'contracts':{}}
    for name,row in fleet.items():
        value=dict(command=['fixed'],entrypoint=None,user='',workingDir='',mounts=[],networks={},hostConfig={})
        contracts['contracts'][name]=value;row['contractSha256']=release.sha(release.canonical(value))
    updated=['shared-employee']
    policy=dict(companies=sorted(original['policyCompanies'],key=lambda r:r['database']),databases={'fixture':{'closed':False}},policySha256={'fixture':'a'*64})
    observation=dict(completed=True,status='partial_release_v2_baseline_observed_not_approved',contractFingerprintVersion=2,originalExecution='original',sourceSha256='b'*64,alreadyUpdated=updated,
                     originalRawFleetMatched=True,fullDeclaredEnvironmentAndSecurityContextVerified=True,remaining=['shared-gateway','shared-ui'],fleet=fleet,publicArtifacts=artifacts,
                     originalPolicies=[dict(database='fixture',closed=False,originalIdentityAndAdmissionUnchanged=True,originalPolicyUnchanged=True,policySha256='a'*64)],
                     servicesChanged=False,grantsChanged=False,admissionChanged=False,environmentValuesExported=False,credentialValuesExported=False)
    readback=dict(executionId='original',fleetDeltas=[dict(name='shared-employee',after=fleet['shared-employee'])])
    binding=dict(alreadyUpdated=updated,observationExecutorSha256='b'*64,executorSha256='e'*64,originalJournal='/root/synthetic-journal',compatibilityReceipt={'path':'/root/resume-compatibility.json','sha256':'c'*64},
                 **{key:{'path':'/root/'+key+'.json','sha256':'f'*64} for key in ['originalPlan','observation','originalReadback','originalPolicy','protectedContracts','fingerprintSource']})
    plan=copy.deepcopy(original);plan.update(executorSha256='d'*64,baselineFleet=fleet,selected=original['selected'][1:],oldArtifacts=artifacts,resume=binding)
    plan['rollback']['order']=['shared-ui','shared-gateway'];plan['rollback']['readiness'].pop('shared-employee');plan['rollback']['compatibilityReceipt']=binding['compatibilityReceipt']
    return plan,original,observation,readback,policy,contracts,{**old,**current}

class ResumeTests(unittest.TestCase):
    def test_exact_reviewed_remaining_subset_is_valid(self):
        values=inputs();self.assertEqual(resume.validate_resume(*values[:6]),values[4])

    def test_scope_image_policy_and_contract_drift_are_refused(self):
        for case in ['selection','preserved','command','policy','scope','artifacts','source','unverified']:
            values=list(inputs());plan,original,observation,readback,policy,contracts=values[:6]
            if case=='selection':plan['selected'].reverse()
            if case=='preserved':observation['fleet']['preserved-worker']['id']='foreign'
            if case=='command':contracts['contracts']['shared-employee']['command']=['foreign']
            if case=='policy':observation['originalPolicies'][0]['policySha256']='f'*64
            if case=='scope':plan['policyCompanies']=plan['policyCompanies'][:1]
            if case=='artifacts':observation['publicArtifacts']['compose.json']='f'*64
            if case=='source':observation['sourceSha256']='f'*64
            if case=='unverified':observation['originalRawFleetMatched']=False
            with self.subTest(case=case),self.assertRaises(ValueError):resume.validate_resume(*values[:6])

    def test_resume_never_publishes_or_replaces_the_completed_prefix(self):
        plan,_,_,_,policy,_,old=inputs();fake=Fake(plan,old);fake.resume_policy_baseline=policy
        fake.capture_policy=lambda:copy.deepcopy(policy)
        report=release.execute(plan,fake)
        self.assertEqual(report['status'],'online_release_verified')
        self.assertNotIn('publish',fake.events)
        self.assertFalse(any(isinstance(e,tuple) and e[:2]==('replace','shared-employee') for e in fake.events))

    def test_resume_policy_capture_cannot_reset_original_baseline(self):
        plan,_,_,_,policy,_,old=inputs();fake=Fake(plan,old);fake.resume_policy_baseline=policy
        fake.capture_policy=lambda:{'different':'policy'}
        with self.assertRaisesRegex(ValueError,'RESUME_ORIGINAL_POLICY_CHANGED'):release.execute(plan,fake)
        self.assertFalse(any(isinstance(e,tuple) and e[0]=='replace' for e in fake.events))

    def test_resume_failure_returns_only_remaining_subset_to_starting_images(self):
        plan,_,_,_,policy,_,old=inputs();fake=Fake(plan,old);fake.resume_policy_baseline=policy
        def capture():fake.policy_captured=True;return copy.deepcopy(policy)
        fake.capture_policy=capture;fake.fail_probe='ready-gateway'
        with self.assertRaisesRegex(ValueError,'ROLLED_BACK'):release.execute(plan,fake)
        self.assertNotIn('publish',fake.events)
        self.assertEqual(fake.fleet['shared-employee']['image'],NEW)
        self.assertEqual(fake.files,old)

if __name__=='__main__':unittest.main()
