"""Validate an explicitly reviewed continuation of a published partial release."""
import copy
import hashlib
import json

canonical=lambda value:json.dumps(value,sort_keys=True,separators=(',',':')).encode()
sha=lambda raw:hashlib.sha256(raw).hexdigest()
FILES={'compose.json','release.json','release.sha256'}

def need(ok,code):
    if not ok:raise ValueError(code)

def adapted_probes(names,already_updated):
    result=[]
    for name in names:
        for service in already_updated:
            prefix='old-'+service+'-'
            if name.startswith(prefix):name='new-'+service+'-'+name[len(prefix):];break
        result.append(name)
    return result

def validate_resume(plan,original,observation,original_readback,policy,contracts):
    binding=plan['resume'];updated=binding['alreadyUpdated']
    need(type(updated) is list and 0<len(updated)<len(original['selected']) and updated==[s['service'] for s in original['selected'][:len(updated)]],'RESUME_PREFIX_INVALID')
    need(observation.get('completed') is True and observation.get('status')=='partial_release_v2_baseline_observed_not_approved' and observation.get('contractFingerprintVersion')==2 and observation.get('originalExecution')==original_readback.get('executionId') and observation.get('sourceSha256')==binding['observationExecutorSha256'],'RESUME_OBSERVATION_BINDING_CHANGED')
    need(observation.get('alreadyUpdated')==updated and observation.get('originalRawFleetMatched') is True and observation.get('fullDeclaredEnvironmentAndSecurityContextVerified') is True,'RESUME_CONTEXT_NOT_VERIFIED')
    need(all(observation.get(k) is False for k in ['servicesChanged','grantsChanged','admissionChanged','environmentValuesExported','credentialValuesExported']),'RESUME_OBSERVATION_SCOPE_CHANGED')
    remaining=[s for s in original['selected'] if s['service'] not in updated]
    need(observation.get('remaining')==[s['service'] for s in remaining],'RESUME_REMAINING_SELECTION_CHANGED')
    need(set(observation['fleet'])==set(original['baselineFleet']) and set(contracts)=={'version','contracts'} and contracts['version']==2 and set(contracts['contracts'])==set(observation['fleet']),'RESUME_CONTRACT_COVERAGE_CHANGED')
    deltas={r['name']:r for r in original_readback['fleetDeltas']}
    need(set(deltas)==set(updated),'RESUME_ORIGINAL_PARTIAL_STATE_CHANGED')
    for name,before in original['baselineFleet'].items():
        after=observation['fleet'][name]
        historical=deltas[name]['after'] if name in updated else before
        need(all(after[k]==historical[k] for k in before if k!='contractSha256'),'RESUME_LIFECYCLE_OR_IMAGE_CHANGED')
        value=contracts['contracts'][name]
        need(set(value)=={'command','entrypoint','user','workingDir','mounts','networks','hostConfig'} and sha(canonical(value))==after['contractSha256'],'RESUME_PROTECTED_CONTRACT_CHANGED')
    need(observation['publicArtifacts']=={**original['oldArtifacts'],**original['newArtifacts']},'RESUME_PUBLIC_ARTIFACT_CHANGED')
    policies={r['database']:r for r in observation['originalPolicies']}
    need(set(policies)==set(policy['databases']) and policy['companies']==sorted(original['policyCompanies'],key=lambda r:r['database']),'RESUME_ORIGINAL_POLICY_BINDING_CHANGED')
    for name,row in policies.items():
        need(row['originalIdentityAndAdmissionUnchanged'] is True and row['originalPolicyUnchanged'] is True and row['closed']==policy['databases'][name]['closed'] and row['policySha256']==policy['policySha256'].get(name),'RESUME_ORIGINAL_POLICY_CHANGED')
    expected=copy.deepcopy(original)
    expected.update(contractFingerprintVersion=2,executorSha256=plan['executorSha256'],baselineFleet=observation['fleet'],selected=remaining,
                    oldArtifacts=observation['publicArtifacts'],preflightProbes=adapted_probes(original['preflightProbes'],updated),resume=binding)
    expected['rollback']['order']=[name for name in original['rollback']['order'] if name not in updated]
    expected['rollback']['readiness']={name:probes for name,probes in original['rollback']['readiness'].items() if name not in updated}
    expected['rollback']['probes']=adapted_probes(original['rollback']['probes'],updated)
    expected['rollback']['compatibilityReceipt']=binding['compatibilityReceipt']
    need(plan==expected,'RESUME_PLAN_SCOPE_CHANGED')
    need(plan['newArtifacts']=={name:observation['publicArtifacts'][name] for name in FILES},'RESUME_ALREADY_PUBLISHED_BYTES_CHANGED')
    return policy
