"""Strict existing-service release. No full startup, migrations or business restore."""
import argparse
import ast
import base64
from contextlib import contextmanager
from decimal import Decimal
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import time
import types
from urllib.parse import urlsplit

BUSINESS = 'employee leave attendance payroll tax benefits expense recruitment performance lms succession compensation assets grievance workflow notification analytics survey'.split()
CANDIDATES = {**{'shared-'+n:'backend' for n in BUSINESS}, **{n:'backend' for n in ['shared-auth','shared-maintenance','organization','kabipay-auth','kabipay-subgraphs']}, **{n:'gateway' for n in ['shared-gateway','kabipay-gateway']}, **{n:'ui' for n in ['shared-ui','kabipay-ui']}}
FILES = {'compose.json','release.json','release.sha256'}
sha = lambda raw: hashlib.sha256(raw).hexdigest()
canonical = lambda value: json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def need(ok, code):
    if not ok: raise ValueError(code)


def digest(value):
    return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None


def reviewed_probe_networks(plan):
    networks=plan.get('probeNetworks',{})
    need(isinstance(networks,dict),'PROBE_NETWORK_BINDING_INVALID')
    for key,binding in networks.items():
        need(isinstance(key,str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]*',key) and isinstance(binding,dict) and set(binding)=={'name','id'} and isinstance(binding['name'],str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]*',binding['name']) and digest(binding['id']),'PROBE_NETWORK_BINDING_INVALID')
    return networks


def probe_network(plan,probe):
    networks=reviewed_probe_networks(plan)
    if 'networkKey' not in probe:
        return dict(name=plan['probeRuntime']['network'],id=plan['probeRuntime']['networkId'])
    key=probe['networkKey']
    need(isinstance(key,str) and key in networks,'PROBE_NETWORK_KEY_INVALID')
    return networks[key]


def validate(plan):
    need(plan['version']==1 and re.fullmatch('[A-Za-z0-9_.-]+',plan['tag']) and plan['appDir']=='/opt/apps/hrms','RELEASE_IDENTITY_INVALID')
    need(type(plan.get('contractFingerprintVersion')) is int and plan['contractFingerprintVersion']==2,'CONTRACT_FINGERPRINT_VERSION_REQUIRED')
    if 'resume' in plan:
        binding=plan['resume']
        need(type(binding) is dict and set(binding)=={'executorSha256','originalPlan','observation','originalReadback','originalJournal','originalPolicy','protectedContracts','alreadyUpdated','observationExecutorSha256','compatibilityReceipt','fingerprintSource'},'RESUME_BINDING_INVALID')
        need(digest(binding['executorSha256']) and digest(binding['observationExecutorSha256']) and type(binding['originalJournal']) is str and binding['originalJournal'].startswith('/root/'),'RESUME_BINDING_INVALID')
        for key in ['originalPlan','observation','originalReadback','originalPolicy','protectedContracts','compatibilityReceipt','fingerprintSource']:
            value=binding[key]
            need(type(value) is dict and set(value)=={'path','sha256'} and type(value['path']) is str and value['path'].startswith('/root/') and digest(value['sha256']),'RESUME_PROTECTED_RECEIPT_REQUIRED')
    selected=plan['selected']; names=[s['service'] for s in selected]
    need(bool(names) and len(names)==len(set(names)) and set(names)<=set(CANDIDATES),'SELECTION_INVALID')
    phases=[CANDIDATES[n] for n in names]
    need(phases==sorted(phases,key=['backend','gateway','ui'].index),'RELEASE_ORDER_INVALID')
    for s in selected:
        n=s['service']; baseline=plan['baselineFleet'].get(n,{})
        need(s['phase']==CANDIDATES[n] and baseline.get('running') is True and baseline.get('service')==n and baseline.get('project')=='apps','SELECTED_NOT_RUNNING')
        need(all(re.fullmatch('sha256:[a-f0-9]{64}',s[k]) for k in ['oldImage','newImage']) and baseline['image']==s['oldImage'],'IMAGE_BINDING_INVALID')
        need(s['readiness'] and set(s['readiness'])<=set(plan['probes']),'EXPLICIT_READINESS_REQUIRED')
        family='kabipay-svc' if s['phase']=='backend' else 'kabipay-'+s['phase']
        need(s['repository']==family and re.fullmatch(re.escape(family)+r':[A-Za-z0-9_.-]+',s['oldRepositoryTag']) and (s['oldImageReference']==s['oldImage'] or re.fullmatch(re.escape(family)+r':[A-Za-z0-9_.-]+',s['oldImageReference'])),'REVIEWED_IMAGE_FAMILY_PROOF_REQUIRED')
    for key,kind in [('employeeGate','employeeSchema'),('gatewayGate','gatewaySchema'),('finalGate','http')]:
        need(plan[key] and set(plan[key])<=set(plan['probes']) and any(plan['probes'][n]['kind']==kind for n in plan[key]),'EXPLICIT_SCHEMA_HTTP_GATES_REQUIRED')
    need(set(plan['rollback']['order'])==set(names) and len(plan['rollback']['order'])==len(names) and plan['rollback']['probes'] and set(plan['rollback']['probes'])<=set(plan['probes']) and set(plan['rollback']['readiness'])==set(names),'REVIEWED_ROLLBACK_REQUIRED')
    need(all(ids and set(ids)<=set(plan['probes']) for ids in plan['rollback']['readiness'].values()),'ROLLBACK_READINESS_REQUIRED')
    preflight=plan.get('preflightProbes')
    need(type(preflight) is list and bool(preflight) and all(type(n) is str for n in preflight) and len(preflight)==len(set(preflight)) and set(preflight)<=set(plan['probes']),'EXPLICIT_PREFLIGHT_PROBES_REQUIRED')
    reviewed_probe_networks(plan)
    for probe in plan['probes'].values():
        probe_network(plan,probe)
        url=urlsplit(probe['url'])
        need(probe['kind'] in ['http','employeeSchema','gatewaySchema'] and url.scheme in ['http','https'] and url.hostname and not url.username and not url.password and not url.fragment,'PROBE_INVALID')
        if 'expectedErrorCodes' in probe:
            codes=probe['expectedErrorCodes']
            need(probe['kind']=='http' and probe['method']=='POST' and probe['expectedStatus']==200 and type(codes) is list and 1<=len(codes)<=8 and all(type(c) is str and re.fullmatch('[A-Z][A-Z0-9_]{0,63}',c) for c in codes) and not any(k in probe for k in ['expectedText','bodySha256','jsonChecks']),'NEGATIVE_PROBE_ASSERTION_INVALID')
        need(probe['method'] in ['GET','POST'] and isinstance(probe['expectedStatus'],int) and ('expectedText' in probe or 'bodySha256' in probe or probe.get('jsonChecks') or 'expectedErrorCodes' in probe),'EXPLICIT_PROBE_ASSERTION_REQUIRED')
        need(type(probe['attempts']) is int and 1<=probe['attempts']<=30 and type(probe['intervalSeconds']) is int and 0<=probe['intervalSeconds']<=5,'EXPLICIT_PROBE_TIMING_REQUIRED')
        if probe['method']=='POST': need(re.match(r'^\s*query\b',probe.get('query','')) and not re.search(r'\b(mutation|subscription)\b',probe['query']),'READ_ONLY_PROBE_REQUIRED')
        if probe['kind']!='http': need(probe['method']=='POST' and digest(probe.get('bodySha256')) and (('_service' in probe['query'] and 'sdl' in probe['query']) or ('__schema' in probe['query'] and 'types' in probe['query'])),'COMPLETE_SCHEMA_ASSERTION_REQUIRED')
        need('headers' not in probe,'INLINE_SESSION_HEADERS_FORBIDDEN')
        if 'headersFile' in probe: need(probe['headersFile']['path'].startswith('/root/') and digest(probe['headersFile']['sha256']),'PROTECTED_PROBE_SESSION_REQUIRED')
    for key in ['sourceReceipt','grantsReceipt','registryReceipt','hostDefaultsReceipt']:
        need(digest(plan[key]['sha256']) and str(plan[key]['path']).startswith('/root/'),'PROTECTED_RECEIPT_REQUIRED')
    need(digest(plan['rollback']['compatibilityReceipt']['sha256']) and digest(plan['executorSha256']),'REVIEWED_SOURCE_PINS_REQUIRED')
    companies=plan.get('policyCompanies')
    need(digest(plan.get('policyExecutorSha256')) and type(companies) is list and len(companies)==5 and all(type(c) is dict and set(c)=={'database','schema','tenantId'} and all(type(v) is str for v in c.values()) for c in companies),'POLICY_ROLLBACK_BINDING_REQUIRED')
    need(re.fullmatch('/root/hrms-private-config-[a-z0-9_]+',plan['operator']['directory']) and digest(plan['operator']['packageSha256']) and re.fullmatch('[0-9]{1,20}',plan['systemId']),'PROTECTED_OPERATOR_CLUSTER_REQUIRED')
    need(re.fullmatch('sha256:[a-f0-9]{64}',plan['probeRuntime']['image']) and digest(plan['probeRuntime']['networkId']) and re.fullmatch('[a-zA-Z0-9_-]+',plan['probeRuntime']['network']),'PINNED_PROBE_RUNTIME_REQUIRED')
    need(bool(plan['protectedFiles']) and all(isinstance(n,str) and n.startswith('/') for n in plan['protectedFiles']),'PRESERVED_BINDINGS_REQUIRED')
    need(all(re.fullmatch(r'(?:compose\.json|release\.(?:json|sha256)|[a-z-]+\.txt|caddy/[a-z-]+\.caddy|config/(?:companies/[a-z]+|ui-[a-z0-9-]+)\.json)',n) and digest(h) for n,h in plan['oldArtifacts'].items()),'PUBLIC_ARTIFACT_PATH_INVALID')
    need(set(plan['newArtifacts'])==FILES and all(digest(h) for h in plan['newArtifacts'].values()),'REVIEWED_TRANSITION_HASHES_REQUIRED')
    proxy=plan['rootProxy']; caddy_binding(proxy)
    baseline=[v for v in plan['baselineFleet'].values() if v['id']==proxy['containerId']]
    need(len(baseline)==1 and baseline[0]['image']==proxy['image'] and baseline[0]['service']=='caddy' and baseline[0]['project']=='apps' and baseline[0]['running'] is True,'ROOT_PROXY_BINDING_REQUIRED')


def transition(plan, current):
    need(set(current)==set(plan['oldArtifacts']) and FILES<=set(current) and all(sha(v)==plan['oldArtifacts'][n] for n,v in current.items()),'PUBLIC_ARTIFACTS_CHANGED')
    need(FILES<=set(plan['previousBytes'])<=set(current) and all(base64.b64decode(raw,validate=True)==current[n] for n,raw in plan['previousBytes'].items()),'REVIEWED_ROLLBACK_BYTES_CHANGED')
    model=json.loads(current['compose.json']); release=json.loads(current['release.json'])
    need(set(model)<={'services','networks','name','version'},'UNSUPPORTED_COMPOSE_RESOURCES')
    for step in plan['selected']:
        need(step['service'] in model['services'],'UNKNOWN_COMPOSE_SERVICE')
        reference=model['services'][step['service']]['image']; family='kabipay-svc' if step['phase']=='backend' else 'kabipay-'+step['phase']
        need(step['repository']==family and reference==step['oldImageReference'] and (reference==step['oldImage'] or re.fullmatch(re.escape(family)+r':[A-Za-z0-9_.-]+',reference)) and re.fullmatch(re.escape(family)+r':[A-Za-z0-9_.-]+',step['oldRepositoryTag']),'COMPOSE_IMAGE_FAMILY_CHANGED')
        need(not model['services'][step['service']].get('depends_on'),'DEPENDENCIES_NOT_ALLOWED')
        model['services'][step['service']]['image']=step['newImage']
    release['tag']=plan['tag']
    data={'compose.json':(json.dumps(model,indent=2)+'\n').encode(),'release.json':(json.dumps(release,indent=2)+'\n').encode()}
    lines=current['release.sha256'].decode().splitlines(); names=[]
    for line in lines:
        match=re.fullmatch('([a-f0-9]{64})  ([A-Za-z0-9_./-]+)',line)
        need(match is not None,'CHECKSUM_INDEX_INVALID')
        h,n=match.groups(); need(n in current and n!='release.sha256' and h==sha(current[n]),'CHECKSUM_INDEX_CHANGED'); names.append(n)
    need(len(names)==len(set(names)) and set(names)==set(current)-{'release.sha256'},'CHECKSUM_INDEX_INCOMPLETE')
    data['release.sha256']=''.join(sha(data.get(n,current[n]))+'  '+n+'\n' for n in names).encode()
    return data


def check_fleet(plan, current, images, uncertain=False):
    need(set(current)==set(plan['baselineFleet']),'FLEET_MEMBERS_CHANGED')
    for name,before in plan['baselineFleet'].items():
        after=current[name]
        if name not in images: need(after==before,'PRESERVED_CONTAINER_CHANGED'); continue
        allowed=images[name] if isinstance(images[name],set) else {images[name]}
        need(after['image'] in allowed and all(after[k]==before[k] for k in ['service','project','contractSha256']),'SELECTED_CONTRACT_OR_IMAGE_CHANGED')
        need(uncertain or after['running'] is True and after['restarts']==0,'SELECTED_NOT_READY')


def check_artifacts(adapter, expected):
    current=adapter.artifacts()
    need(set(current)==set(expected) and all(sha(current[n])==h for n,h in expected.items()),'PUBLIC_ARTIFACTS_CHANGED')


def failure_location(error, stage, service=None, probe=None):
    """Export fixed categories only; an uppercase exception is not inherently safe."""
    codes={'SELECTED_CONTRACT_OR_IMAGE_CHANGED','PRESERVED_CONTAINER_CHANGED','FLEET_MEMBERS_CHANGED','SELECTED_NOT_READY',
           'EXPLICIT_HTTP_PROBE_FAILED','PROBE_NETWORK_CHANGED','PUBLIC_ARTIFACTS_CHANGED','INTENDED_ENVIRONMENT_CHANGED',
           'RUNNING_ENVIRONMENT_CHANGED','DOCKER_OPERATION_FAILED_RAW_OUTPUT_SUPPRESSED','ROLLBACK_POLICY_CHANGED',
           'ROLLBACK_POLICY_ADMISSION_CHANGED','ROLLBACK_POLICY_LOCK_OR_IDENTITY_CHANGED','ROLLBACK_POLICY_SESSION_CLEANUP_FAILED',
           'ROLLBACK_ARTIFACT_READBACK_FAILED','ARTIFACT_PUBLICATION_READBACK_FAILED','ROOT_PROXY_ACTIVE_CHANGED'}
    code=str(error) if type(error) is ValueError and str(error) in codes else 'UNCLASSIFIED_RELEASE_FAILURE'
    kind=type(error).__name__ if type(error) in [ValueError,KeyError,TypeError,OSError,TimeoutError,FileNotFoundError] else 'OtherError'
    return dict(stage=stage,service=service,probe=probe,code=code,errorType=kind)


def execute(plan, adapter):
    validate(plan)
    with adapter.lock():
        adapter.context(); check_fleet(plan,adapter.snapshot(),{})
        captured_policy=adapter.capture_policy()
        if 'resume' in plan: need(captured_policy==adapter.resume_policy_baseline,'RESUME_ORIGINAL_POLICY_CHANGED')
        adapter.save('policy-baseline.json',captured_policy)
        for name in plan['preflightProbes']: adapter.probe(name)
        adapter.context(); check_fleet(plan,adapter.snapshot(),{})
        old=adapter.artifacts()
        new={n:old[n] for n in FILES} if 'resume' in plan else transition(plan,old)
        if 'resume' in plan: need({n:sha(v) for n,v in old.items()}==plan['oldArtifacts'],'RESUME_PUBLISHED_ARTIFACTS_CHANGED')
        new_hashes={n:sha(v) for n,v in new.items()}; touched=[]; images={}; published=False
        need(new_hashes==plan['newArtifacts'],'REVIEWED_TRANSITION_CHANGED')
        expected={**plan['oldArtifacts'],**new_hashes}
        adapter.save('intent.json',dict(selected=plan['selected'],oldArtifacts=plan['oldArtifacts'],newArtifacts=new_hashes,grantsRetained=True))
        stage='publish'; active_service=None; active_probe=None
        try:
            if 'resume' not in plan:
                published=True; adapter.publish(new,{n:plan['oldArtifacts'][n] for n in FILES})
            check_artifacts(adapter,expected)
            completed_phases=set()
            for index,step in enumerate(plan['selected']):
                name=step['service']; phase=step['phase']
                active_service=name; active_probe=None; stage='phase_gate'
                if phase in ['gateway','ui'] and 'backend' not in completed_phases:
                    for probe in plan['employeeGate']: active_probe=probe; adapter.probe(probe)
                    completed_phases.add('backend')
                if phase=='ui' and 'gateway' not in completed_phases:
                    for probe in plan['gatewayGate']: active_probe=probe; adapter.probe(probe)
                    completed_phases.add('gateway')
                stage='service_preflight'; active_probe=None
                adapter.context(); check_fleet(plan,adapter.snapshot(),images); check_artifacts(adapter,expected)
                adapter.save(str(index)+'-intent.json',step); touched.append(name)
                stage='service_replace'; adapter.replace(name,step['newImage']); images[name]=step['newImage']
                stage='service_readiness'
                for probe in step['readiness']: active_probe=probe; adapter.probe(probe)
                stage='service_readback'; active_probe=None
                adapter.context(); check_fleet(plan,adapter.snapshot(),images)
                adapter.save(str(index)+'-completion.json',dict(service=name,image=step['newImage']))
            stage='final_probes'; active_service=None
            for probe in plan['employeeGate']+plan['gatewayGate']+plan['finalGate']: active_probe=probe; adapter.probe(probe)
            stage='final_readback'; active_probe=None
            adapter.context(); check_fleet(plan,adapter.snapshot(),images)
            need(all(sha(adapter.artifacts()[n])==h for n,h in {**plan['oldArtifacts'],**new_hashes}.items()),'FINAL_PUBLIC_ARTIFACT_CHANGED')
        except Exception as primary_error:
            primary_failure=failure_location(primary_error,stage,active_service,active_probe)
            recovery='operator_review_required'
            recovery_failure=None; stage='recovery_policy_guard'; active_service=None; active_probe=None
            try:
                with adapter.rollback_guard() as policy:
                    stage='recovery_preflight'
                    policy.check(); adapter.context(); check_artifacts(adapter,expected)
                    allowed={n:{s['oldImage'],s['newImage']} for s in plan['selected'] for n in [s['service']] if n in touched}
                    check_fleet(plan,adapter.snapshot(),allowed,uncertain=True)
                    # No older authorization code runs until every open company policy is locked and unchanged.
                    for name in plan['rollback']['order']:
                        if name in touched:
                            active_service=name; active_probe=None; stage='recovery_service_preflight'
                            policy.check(); adapter.context(); check_fleet(plan,adapter.snapshot(),allowed,uncertain=True)
                            step=next(s for s in plan['selected'] if s['service']==name)
                            adapter.save(name+'-rollback-intent.json',dict(image=step['oldImage']))
                            stage='recovery_replace'; policy.check(); adapter.replace(name,step['oldImage'])
                            stage='recovery_readiness'
                            for probe in plan['rollback']['readiness'][name]: active_probe=probe; adapter.probe(probe)
                            adapter.save(name+'-rollback-completion.json',dict(image=step['oldImage']))
                    stage='recovery_publication'; active_service=None; active_probe=None; policy.check()
                    if published: adapter.publish({n:old[n] for n in FILES},new_hashes)
                    stage='recovery_final_probes'
                    for probe in plan['rollback']['probes']: active_probe=probe; adapter.probe(probe)
                    stage='recovery_final_readback'; active_probe=None
                    policy.check(); check_fleet(plan,adapter.snapshot(),{n:plan['baselineFleet'][n]['image'] for n in touched})
                    need(adapter.artifacts()==old,'ROLLBACK_ARTIFACT_READBACK_FAILED')
                    stage='recovery_guard_cleanup'
                recovery='rolled_back'
            except Exception as recovery_error: recovery_failure=failure_location(recovery_error,stage,active_service,active_probe)
            adapter.save('failure.json',dict(recovery=recovery,attempted=touched,primaryFailure=primary_failure,recoveryFailure=recovery_failure,grantsRetained=True,businessDataRestored=False,rawOutputReturned=False))
            raise ValueError('ONLINE_RELEASE_ROLLED_BACK' if recovery=='rolled_back' else 'ONLINE_RELEASE_OPERATOR_REVIEW_REQUIRED') from None
        report=dict(status='online_release_verified',selected=[s['service'] for s in plan['selected']],grantsRetained=True,businessDataRestored=False,environmentUnchanged=True)
        if 'resume' in plan: report['alreadyUpdated']=plan['resume']['alreadyUpdated']
        adapter.save('completion.json',report)
        return report


def protected(path, mode=0o600):
    path=Path(path); need(path.resolve()==path,'PROTECTED_PATH_ALIAS')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as stream:
        info=os.fstat(stream.fileno()); need(stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==mode and info.st_size<=8*1024*1024,'PROTECTED_FILE_CHANGED')
        return stream.read()


def caddy_binding(proxy):
    need(type(proxy) is dict and proxy.get('container')=='caddy' and proxy.get('source')=='/opt/apps/Caddyfile' and digest(proxy.get('sha256')) and digest(proxy.get('activeSha256')) and digest(proxy.get('containerId')) and isinstance(proxy.get('image'),str) and re.fullmatch('sha256:[a-f0-9]{64}',proxy['image']),'ROOT_PROXY_BINDING_REQUIRED')
    metadata=proxy.get('metadata')
    need(type(metadata) is dict and set(metadata)=={'uid','gid','mode','inode','device','size'} and all(type(v) is int for v in metadata.values()) and metadata['uid']>=0 and metadata['gid']>=0 and metadata['mode']==0o644 and metadata['inode']>0 and metadata['device']>=0 and 0<metadata['size']<=128*1024 and type(proxy.get('inode')) is int and proxy['inode']==metadata['inode'],'ROOT_PROXY_BINDING_REQUIRED')
    mount=proxy.get('mountBinding')
    need(type(mount) is dict and set(mount)=={'destination','readOnly'} and isinstance(mount['destination'],str) and mount['destination'].startswith('/') and '..' not in mount['destination'].split('/') and type(mount['readOnly']) is bool,'ROOT_PROXY_BINDING_REQUIRED')


def caddy_metadata(info):
    return dict(uid=info.st_uid,gid=info.st_gid,mode=stat.S_IMODE(info.st_mode),inode=info.st_ino,device=info.st_dev,size=info.st_size)


def public_caddy_source(proxy):
    """Only the reviewed public Caddy file may have an explicitly bound nonroot owner."""
    caddy_binding(proxy); path=Path(proxy['source']); need(path.resolve()==path,'ROOT_PROXY_SOURCE_ALIAS')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as stream:
        def unchanged(info):
            need(stat.S_ISREG(info.st_mode) and caddy_metadata(info)==proxy['metadata'],'ROOT_PROXY_SOURCE_CHANGED')
        unchanged(os.fstat(stream.fileno()))
        raw=stream.read(proxy['metadata']['size']+1)
        need(len(raw)==proxy['metadata']['size'] and sha(raw)==proxy['sha256'],'ROOT_PROXY_SOURCE_CHANGED')
        unchanged(os.fstat(stream.fileno())); unchanged(path.lstat())
        return raw


def root_proxy_container(proxy,containers):
    caddy_binding(proxy); matches=[c for c in containers if c['Id']==proxy['containerId']]
    need(len(matches)==1,'ROOT_PROXY_CONTAINER_OR_MOUNT_CHANGED'); value=matches[0]
    need(value['Image']==proxy['image'] and value['Name']=='/'+proxy['container'] and value['State']['Running'] is True,'ROOT_PROXY_CONTAINER_OR_MOUNT_CHANGED')
    mounts=[m for m in value['Mounts'] if m['Type']=='bind' and m['Source']==proxy['source']]
    need(len(mounts)==1 and mounts[0]['Destination']==proxy['mountBinding']['destination'] and type(mounts[0]['RW']) is bool and mounts[0]['RW'] is not proxy['mountBinding']['readOnly'],'ROOT_PROXY_CONTAINER_OR_MOUNT_CHANGED')


def ordered_mounts(entries, target):
    need(type(entries) is list and all(type(row) is dict and type(row.get(target)) is str for row in entries),'MOUNT_CONTRACT_INVALID')
    need(len(entries)==len({row[target] for row in entries}),'AMBIGUOUS_MOUNT_TARGET')
    return sorted(copy.deepcopy(entries),key=lambda row:row[target])


def container_contract(value):
    """Version 2: retain every value; canonicalize only unique mount target order."""
    config=value['Config']; host=copy.deepcopy(value['HostConfig'])
    if 'Mounts' in host and host['Mounts'] is not None: host['Mounts']=ordered_mounts(host['Mounts'],'Target')
    return dict(command=config.get('Cmd'),entrypoint=config.get('Entrypoint'),user=config.get('User'),workingDir=config.get('WorkingDir'),
                mounts=ordered_mounts(value['Mounts'],'Destination'),networks={n:dict(aliases=v.get('Aliases'),networkId=v['NetworkID']) for n,v in value['NetworkSettings']['Networks'].items()},hostConfig=host)


def fingerprint_code(raw):
    names=['ordered_mounts','container_contract','fleet_snapshot'];nodes=ast.parse(raw).body
    selected=[next((node for node in nodes if isinstance(node,ast.FunctionDef) and node.name==name),None) for name in names]
    need(all(node is not None for node in selected),'FINGERPRINT_SOURCE_INCOMPLETE')
    return sha(canonical([ast.dump(node,include_attributes=False) for node in selected]))


def fleet_snapshot(items):
    """Allowlisted receipt shape; raw inspect/environment stays only in memory."""
    result={}
    for c in items:
        labels=c['Config'].get('Labels') or {}; service=labels.get('com.docker.compose.service'); project=labels.get('com.docker.compose.project')
        key=service if project=='apps' and service in CANDIDATES else c['Name']
        need(key not in result,'AMBIGUOUS_SERVICE_CONTAINER')
        contract=container_contract(c)
        result[key]=dict(id=c['Id'],image=c['Image'],running=c['State']['Running'],restarts=c['RestartCount'],started=c['State']['StartedAt'],service=service,project=project,contractSha256=sha(canonical(contract)))
    return result


def env_map(entries):
    """Private memory only. Callers must never log, store or return this map."""
    result={}
    for entry in entries or []:
        key,separator,value=entry.partition('=')
        need(separator and key and key not in result,'ENVIRONMENT_AMBIGUOUS')
        result[key]=value
    return result


def integer(value):
    if isinstance(value,Decimal):
        need(value.is_finite() and value==value.to_integral_value(),'UNSUPPORTED_HOST_NUMBER'); return int(value)
    need(not isinstance(value,bool) and re.fullmatch('-?[0-9]+',str(value)),'UNSUPPORTED_HOST_NUMBER')
    return int(value)


def bytes_value(value):
    match=re.fullmatch(r'(-?[0-9]+(?:\.[0-9]+)?)\s*([kmgtpe]?)(?:i?b)?',str(value).lower())
    need(match is not None,'UNSUPPORTED_HOST_SIZE')
    size=Decimal(match[1])*(1024**('kmgtpe'.index(match[2])+1) if match[2] else 1)
    need(size==size.to_integral_value(),'UNSUPPORTED_HOST_SIZE'); return int(size)


def options(value):
    return sorted(str(item).upper().removeprefix('CAP_') for item in value or [])


def security_options(value):
    result=[]
    for item in value or []:
        text=str(item); separator='=' if '=' in text and (':' not in text or text.index('=')<text.index(':')) else ':'
        key,separator,argument=text.partition(separator)
        need(separator or key=='no-new-privileges','UNSUPPORTED_SECURITY_OPTION')
        result.append(key+'='+(argument if separator else 'true'))
    return sorted(result)


def tmpfs(value):
    if not isinstance(value,dict):
        value=dict(str(item).partition(':')[::2] for item in value or [])
    return {path:','.join(sorted(parts.split(','))) if parts else '' for path,parts in value.items()}


def ulimits(value):
    if isinstance(value,dict):
        value=[dict(Name=name,Soft=v['soft'] if isinstance(v,dict) else v,Hard=v['hard'] if isinstance(v,dict) else v) for name,v in value.items()]
    return sorted((dict(Name=v['Name'],Soft=integer(v['Soft']),Hard=integer(v['Hard'])) for v in value or []),key=lambda v:v['Name'])


def boolean(value):
    need(value is None or type(value) is bool,'UNSUPPORTED_HOST_BOOLEAN'); return bool(value)


def host_collection(value, kind):
    need(value is None or type(value) is kind,'UNSUPPORTED_HOST_COLLECTION_TYPE')
    return kind() if value is None else value


def dynamic_host_value(field, value):
    if field in ['Dns','DnsOptions','DnsSearch','MaskedPaths','ReadonlyPaths']:
        return host_collection(value,list)
    if field=='LogConfig':
        need(type(value) is dict and set(value)<={'Type','Config'} and isinstance(value.get('Type'),str),'UNSUPPORTED_LOG_CONFIG')
        return dict(Type=value['Type'],Config=host_collection(value.get('Config'),dict))
    return value


def host_contract(service, actual, defaults):
    """Compare supported Compose semantics before any public write/recreation."""
    # Docker defaults the total memory+swap allowance to twice a positive limit.
    # An explicit nonzero swap allowance remains an exact operator decision.
    memory=bytes_value(service.get('mem_limit',0))
    implicit_swap=2*memory if memory>0 else 0
    simple={'CapAdd':('cap_add',[],options),'CapDrop':('cap_drop',[],options),'SecurityOpt':('security_opt',[],security_options),
            'Memory':('mem_limit',0,bytes_value),'MemoryReservation':('mem_reservation',0,bytes_value),'MemorySwap':('memswap_limit',0,bytes_value),
            'MemorySwappiness':('mem_swappiness',None,lambda v:None if v is None else integer(v)),
            'PidsLimit':('pids_limit',None,lambda v:None if v in (None,0,-1) else integer(v)),
            'CpuShares':('cpu_shares',0,integer),'CpuPeriod':('cpu_period',0,integer),'CpuQuota':('cpu_quota',0,integer),
            'CpuRealtimePeriod':('cpu_rt_period',0,integer),'CpuRealtimeRuntime':('cpu_rt_runtime',0,integer),
            'NanoCpus':('cpus',0,lambda v:integer(Decimal(str(v))*1000000000)),
            'CpusetCpus':('cpuset','',str),'CpusetMems':('cpuset_mems','',str),
            'Privileged':('privileged',False,boolean),'ReadonlyRootfs':('read_only',False,boolean),
            'Init':('init',None,lambda v:None if v is None else boolean(v)),'OomKillDisable':('oom_kill_disable',False,boolean),'OomScoreAdj':('oom_score_adj',0,integer),
            'Ulimits':('ulimits',[],ulimits),'Tmpfs':('tmpfs',{},tmpfs),
            'PidMode':('pid','',str),'UTSMode':('uts','',str),'UsernsMode':('userns_mode','',str),
            'GroupAdd':('group_add',[],lambda v:sorted(str(x) for x in v or [])),'Sysctls':('sysctls',{},lambda v:v or {})}
    dynamic={'Runtime':'runtime','IpcMode':'ipc','CgroupnsMode':'cgroup','CgroupParent':'cgroup_parent','ShmSize':'shm_size','LogConfig':'logging',
             'MaskedPaths':None,'ReadonlyPaths':None,'Dns':'dns','DnsOptions':'dns_opt','DnsSearch':'dns_search','Isolation':None,'ConsoleSize':None,'InitBinary':None}
    neutral={'AutoRemove':False,'PublishAllPorts':False,'ContainerIDFile':'','VolumeDriver':'','VolumesFrom':[],'Links':[],'Cgroup':'',
             'Devices':[],'DeviceRequests':[],'DeviceCgroupRules':[],'ExtraHosts':[],'StorageOpt':{},'Annotations':{},
             'CpuCount':0,'CpuPercent':0,'IOMaximumIOps':0,'IOMaximumBandwidth':0,'BlkioWeight':0,'BlkioWeightDevice':[],
             'BlkioDeviceReadBps':[],'BlkioDeviceWriteBps':[],'BlkioDeviceReadIOps':[],'BlkioDeviceWriteIOps':[],'KernelMemory':0,'KernelMemoryTCP':0}
    derived={'Binds','Mounts','PortBindings','NetworkMode'}
    need(set(actual)<=set(simple)|set(dynamic)|set(neutral)|derived|{'RestartPolicy'},'UNSUPPORTED_ACTUAL_HOST_FIELD')
    need(set(defaults)<=set(dynamic)|{'BindPropagation'} and set(actual)&set(dynamic)<=set(defaults),'REVIEWED_ENGINE_HOST_DEFAULTS_REQUIRED')
    allowed={entry[0] for entry in simple.values()}|{v for v in dynamic.values() if v}|{'image','command','entrypoint','user','working_dir','environment','env_file','networks','volumes','ports','restart','depends_on','name','container_name','labels'}
    need(set(service)<=allowed,'UNSUPPORTED_COMPOSE_HOST_SETTING')
    for field,(option,empty,normalize) in simple.items():
        observed=integer(actual.get(field,0)) if field=='NanoCpus' else normalize(actual.get(field,empty))
        intended=normalize(service.get(option,empty))
        if field=='MemorySwap' and intended==0: intended=implicit_swap
        need(intended==observed,'INTENDED_HOST_SECURITY_OR_RESOURCE_CHANGED')
    restart=service.get('restart') or 'no'; name,_,maximum=restart.partition(':')
    need(name in ['no','always','unless-stopped','on-failure'],'UNSUPPORTED_RESTART_POLICY')
    need(actual.get('RestartPolicy',{'Name':'no','MaximumRetryCount':0})==dict(Name=name,MaximumRetryCount=integer(maximum or 0)),'INTENDED_RESTART_POLICY_CHANGED')
    for field,empty in neutral.items():
        value=actual.get(field,empty)
        if isinstance(empty,(list,dict)):
            need(value is None or type(value) is type(empty) and not value,'UNSUPPORTED_NONDEFAULT_HOST_SETTING')
        else: need(type(value) is type(empty) and value==empty,'UNSUPPORTED_NONDEFAULT_HOST_SETTING')
    for field,option in dynamic.items():
        if field not in actual and (not option or option not in service): continue
        intended=service.get(option,defaults.get(field)) if option else defaults.get(field)
        if field=='ShmSize': intended=bytes_value(intended)
        if field=='LogConfig' and option in service:
            logging=service[option]; need(set(logging)<={'driver','options'} and logging.get('driver'),'EXPLICIT_LOG_DRIVER_REQUIRED')
            intended=dict(Type=logging['driver'],Config=logging.get('options',{}))
        need(dynamic_host_value(field,intended)==dynamic_host_value(field,actual.get(field)),'INTENDED_ENGINE_HOST_SETTING_CHANGED')


def intended_contract(resolved, name, image, before, host_defaults=None):
    service=resolved['services'][name]; config=before['Config']; host=before['HostConfig']
    need(not image.get('Volumes'),'IMAGE_ANONYMOUS_MOUNTS_NOT_SUPPORTED')
    for field,option in [('Cmd','command'),('Entrypoint','entrypoint'),('User','user'),('WorkingDir','working_dir')]:
        fallback=image.get(field,'' if field in ['User','WorkingDir'] else None)
        intended=service.get(option)
        if intended is None: intended=fallback
        need(intended==config.get(field,'' if field in ['User','WorkingDir'] else None),'INTENDED_COMMAND_OR_USER_CHANGED')
    mounts={(v['type'],v.get('source'),v['target'],bool(v.get('read_only',False))) for v in service.get('volumes',[])}
    need(mounts=={(v['Type'],v['Source'],v['Destination'],not v['RW']) for v in before['Mounts']},'INTENDED_MOUNTS_CHANGED')
    if mounts:
        default=(host_defaults or {}).get('BindPropagation'); need(default in ['private','rprivate'],'REVIEWED_BIND_PROPAGATION_REQUIRED')
        volumes={v['target']:v for v in service['volumes']}
        for mount in before['Mounts']:
            bind=volumes[mount['Destination']].get('bind',{})
            need(set(bind)<={'create_host_path','propagation'} and mount.get('Propagation')==bind.get('propagation',default),'INTENDED_BIND_OPTIONS_CHANGED')
        need(not host.get('Binds') and len(host.get('Mounts') or [])==len(mounts),'UNSUPPORTED_LEGACY_BIND_OPTIONS')
        for mount in host.get('Mounts') or []:
            bind=mount.get('BindOptions') or {}
            need(set(mount)<={'Type','Source','Target','ReadOnly','Consistency','BindOptions'} and not mount.get('Consistency') and set(bind)<={'Propagation','CreateMountpoint'} and not bind.get('CreateMountpoint'),'UNSUPPORTED_BIND_HOST_OPTIONS')
            need((mount['Type'],mount['Source'],mount['Target'],bool(mount.get('ReadOnly'))) in mounts and (bind.get('Propagation') or default)==volumes[mount['Target']].get('bind',{}).get('propagation',default),'INTENDED_BIND_HOST_OPTIONS_CHANGED')
    networks={resolved['networks'][n]['name'] for n in service.get('networks',{})}
    need(networks==set(before['NetworkSettings']['Networks']) and not service.get('ports') and not host.get('PortBindings'),'INTENDED_NETWORK_OR_PORTS_CHANGED')
    need('NetworkMode' not in host or host['NetworkMode'] in networks,'UNSUPPORTED_NETWORK_NAMESPACE_MODE')
    host_contract(service,host,host_defaults or {})


def reviewed_recovery(plan, compatibility):
    need(compatibility.get('applicationRollbackCompatible') is True and compatibility.get('businessDataRestore') is False and compatibility.get('grantsRetained') is True,'ROLLBACK_COMPATIBILITY_NOT_REVIEWED')
    need(compatibility.get('sourceReceiptSha256')==plan['sourceReceipt']['sha256'] and compatibility.get('selected')==plan['selected'] and compatibility.get('newWritesCompatible') is True,'ROLLBACK_NEW_WRITES_NOT_REVIEWED')
    guard=compatibility.get('policyGuard')
    need(type(guard) is dict and set(guard)=={'version','executorSha256','companies','unchangedPolicyRequired'} and type(guard['version']) is int and guard['version']==1 and guard['executorSha256']==plan['policyExecutorSha256'] and guard['companies']==plan['policyCompanies'] and guard['unchangedPolicyRequired'] is True,'ROLLBACK_POLICY_COMPATIBILITY_NOT_REVIEWED')


def image_family_proof(step, metadata, tag_id):
    need(metadata['Id']==step['oldImage'] and step['oldRepositoryTag'] in (metadata.get('RepoTags') or []) and tag_id==step['oldImage'],'OLD_IMAGE_REPOSITORY_PROOF_CHANGED')


def engine_contract(info, compose_version):
    fields=['ServerVersion','DefaultRuntime','Runtimes','SecurityOptions','CgroupDriver','CgroupVersion','LoggingDriver','Driver','OSType','KernelVersion','InitBinary']
    need(all(field in info for field in fields) and bool(compose_version.strip()),'ENGINE_DEFAULT_EVIDENCE_INCOMPLETE')
    return dict(engine={key:info[key] for key in fields},composeVersion=compose_version.strip())


class Native:
    def __init__(self,plan):
        self.plan=plan; self.root=Path(plan['appDir']); self.environment=None; self.privateContracts={}; self.hostDefaults=None
        need(sha(protected(Path(__file__).resolve()))==plan['executorSha256'],'EXECUTOR_SOURCE_CHANGED')
        policy_path=Path(__file__).resolve().with_name('online-release-policy.py'); policy_raw=protected(policy_path)
        need(sha(policy_raw)==plan['policyExecutorSha256'],'POLICY_EXECUTOR_SOURCE_CHANGED')
        self.policy_module=types.ModuleType('pinned_release_policy'); self.policy_module.__file__=str(policy_path)
        exec(compile(policy_raw,str(policy_path),'exec'),self.policy_module.__dict__)
        directory=Path(plan['operator']['directory']); raw=protected(directory/'package.json')
        need(sha(raw)==plan['operator']['packageSha256'],'OPERATOR_PACKAGE_CHANGED')
        for name,h in json.loads(raw)['sources'].items():
            need(Path(name).name==name and sha(protected(directory/name))==h,'OPERATOR_SOURCE_CHANGED')
        sys.path.insert(0,str(directory))
        import run as operator
        from maintenance_signals import defer_termination
        from maintenance_session import PersistentPsql
        self.operator=operator; self.defer=defer_termination
        self.policy_session=lambda database:PersistentPsql(database,command_factory=operator.psql_command,timeout=30)
        self.policy=None
        self.work=Path(tempfile.mkdtemp(prefix='hrms-online-release-',dir='/root')); self.save('plan.json',plan)
        print(json.dumps(dict(stage='protected_online_release_journal',workDirectory=str(self.work))),flush=True)
        for step in plan['selected']:
            for key in ['oldImage','newImage']:
                image=json.loads(self.command(['image','inspect',step[key]]))[0]
                need(image['Id']==step[key],'LOADED_IMAGE_CHANGED')
                if key=='oldImage':
                    image_family_proof(step,image,json.loads(self.command(['image','inspect',step['oldRepositoryTag']]))[0]['Id'])
                    need(json.loads(self.command(['image','inspect',step['oldImageReference']]))[0]['Id']==step['oldImage'],'CURRENT_COMPOSE_IMAGE_ID_CHANGED')
                if step['phase']=='ui': need((image['Config'].get('Labels') or {}).get('io.kabipay.ui.organization-workspace')=='true','ORGANIZATION_UI_BUILD_REQUIRED')
        runtime=plan['probeRuntime']
        need(json.loads(self.command(['image','inspect',runtime['image']]))[0]['Id']==runtime['image'],'PROBE_RUNTIME_CHANGED')
        for network in [dict(name=runtime['network'],id=runtime['networkId']),*reviewed_probe_networks(plan).values()]:
            need(json.loads(self.command(['network','inspect',network['name']]))[0]['Id']==network['id'],'PROBE_RUNTIME_CHANGED')
        self.resume_policy_baseline=None
        if 'resume' in plan: self.read_resume_context()

    def read_resume_context(self):
        binding=self.plan['resume'];path=Path(__file__).resolve().with_name('online-release-resume.py');raw=protected(path)
        need(sha(raw)==binding['executorSha256'],'RESUME_EXECUTOR_SOURCE_CHANGED')
        module=types.ModuleType('pinned_release_resume');module.__file__=str(path)
        exec(compile(raw,str(path),'exec'),module.__dict__)
        values={}
        for key in ['originalPlan','observation','originalReadback','originalPolicy','protectedContracts']:
            item=binding[key];content=protected(item['path']);need(sha(content)==item['sha256'],'RESUME_RECEIPT_CHANGED');values[key]=json.loads(content)
        prior=binding['fingerprintSource'];prior_raw=protected(prior['path'])
        need(sha(prior_raw)==prior['sha256']==binding['observationExecutorSha256'] and fingerprint_code(prior_raw)==fingerprint_code(protected(Path(__file__).resolve())),'RESUME_FINGERPRINT_ALGORITHM_CHANGED')
        original=values['originalPlan'];readback=values['originalReadback'];journal=Path(binding['originalJournal'])
        need(journal.resolve()==journal and protected(journal/'plan.json')==canonical(original),'RESUME_ORIGINAL_JOURNAL_CHANGED')
        files=readback['journal']['files'];need({p.name for p in journal.iterdir()}=={row['name'] for row in files},'RESUME_ORIGINAL_PROGRESS_CHANGED')
        for row in files:
            need(Path(row['name']).name==row['name'] and sha(protected(journal/row['name']))==row['sha256'],'RESUME_ORIGINAL_JOURNAL_CHANGED')
        need(binding['originalPolicy']['path']==str(journal/'policy-baseline.json') and values['observation']['protectedContracts']==binding['protectedContracts'],'RESUME_PROTECTED_BINDING_CHANGED')
        self.resume_policy_baseline=module.validate_resume(self.plan,original,values['observation'],readback,values['originalPolicy'],values['protectedContracts'])

    def command(self,args,data=None):
        result=subprocess.run(['/usr/bin/docker',*args],input=data,capture_output=True,text=True,timeout=150,env={'PATH':os.defpath,'HOME':'/root','LANG':'C.UTF-8'})
        need(result.returncode==0,'DOCKER_OPERATION_FAILED_RAW_OUTPUT_SUPPRESSED'); return result.stdout

    def capture_policy(self):
        need(self.policy is None,'POLICY_BASELINE_ALREADY_CAPTURED')
        binding=self.plan['registryReceipt']; raw=protected(binding['path'])
        need(sha(raw)==binding['sha256'],'REGISTRY_RECEIPT_CHANGED'); registry=json.loads(raw)
        self.policy=self.policy_module.PolicyGuard(self.plan['policyCompanies'],registry['registry'],self.plan['systemId'],lambda sql:self.operator.database_sql('postgres',sql),self.policy_session)
        return self.policy.capture()

    def rollback_guard(self):
        need(self.policy is not None,'POLICY_BASELINE_REQUIRED')
        return self.policy.rollback_guard()

    @contextmanager
    def lock(self):
        import fcntl
        fd=os.open('/run/lock/hrms-release.lock',os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            info=os.fstat(fd); need(stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o600,'RELEASE_LOCK_CHANGED')
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.operator.operator_lock(),self.defer(): yield
        finally: os.close(fd)

    def save(self,name,value):
        fd=os.open(self.work/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as stream: stream.write(canonical(value)); stream.flush(); os.fsync(stream.fileno())

    def context(self):
        receipt=self.plan['hostDefaultsReceipt']; raw=protected(receipt['path'])
        need(sha(raw)==receipt['sha256'],'ENGINE_HOST_DEFAULT_RECEIPT_CHANGED'); reviewed=json.loads(raw)
        observed=engine_contract(json.loads(self.command(['info','--format','{{json .}}'])),self.command(['compose','version','--short']))
        need(reviewed.get('reviewedEngineDefaults') is True and reviewed.get('engineSha256')==sha(canonical(observed)) and isinstance(reviewed.get('defaults'),dict),'ENGINE_HOST_DEFAULTS_NOT_REVIEWED')
        self.hostDefaults=reviewed['defaults']
        ids=self.command(['ps','-aq']).split(); need(ids,'FLEET_EMPTY')
        current={}
        containers=json.loads(self.command(['inspect',*ids]))
        for c in containers:
            labels=c['Config'].get('Labels') or {}; name=labels.get('com.docker.compose.service')
            if labels.get('com.docker.compose.project')=='apps' and name in {s['service'] for s in self.plan['selected']}:
                need(name not in current,'AMBIGUOUS_SERVICE_ENVIRONMENT'); current[name]=env_map(c['Config'].get('Env'))
                if self.environment is None: self.privateContracts[name]=c
        need(set(current)=={s['service'] for s in self.plan['selected']},'SELECTED_ENVIRONMENT_MISSING')
        if self.environment is None:
            self.environment=current
            for step in self.plan['selected']: self.verify_environment(step['service'],step['newImage'])
            self.save('contract-baseline.json',dict(version=2,contracts={name:container_contract(value) for name,value in self.privateContracts.items()}))
        need(current==self.environment,'RUNNING_ENVIRONMENT_CHANGED')
        proxy=self.plan['rootProxy']; root_proxy_container(proxy,containers); public_caddy_source(proxy)
        need(sha(canonical(json.loads(self.command(['exec',proxy['containerId'],'wget','-qO-','http://127.0.0.1:2019/config/']))))==proxy['activeSha256'],'ROOT_PROXY_ACTIVE_CHANGED')
        for key in ['sourceReceipt','grantsReceipt']:
            receipt=self.plan[key]; raw=protected(receipt['path']); need(sha(raw)==receipt['sha256'],'PROTECTED_RECEIPT_CHANGED')
            if key=='grantsReceipt':
                value=json.loads(raw); report=value.get('report',value)
                need(report['status']=='five_company_business_columns_verified' and len(report['proofs'])==5 and all(p['allRequired'] for p in report['proofs']),'FIVE_DATABASE_GRANTS_REQUIRED')
        receipt=self.plan['rollback']['compatibilityReceipt']; raw=protected(receipt['path'])
        need(sha(raw)==receipt['sha256'],'ROLLBACK_COMPATIBILITY_CHANGED')
        reviewed_recovery(self.plan,json.loads(raw))
        for name,binding in self.plan['protectedFiles'].items():
            h=binding if isinstance(binding,str) else binding['sha256']; mode=0o600 if isinstance(binding,str) else int(binding['mode'],8)
            need(sha(protected(name,mode))==h,'PRESERVED_BINDING_CHANGED')
        receipt=self.plan['registryReceipt']; raw=protected(receipt['path'])
        need(sha(raw)==receipt['sha256'],'REGISTRY_RECEIPT_CHANGED'); registry=json.loads(raw)
        need(self.operator.database_sql('postgres','BEGIN READ ONLY;SELECT system_identifier::text FROM pg_control_system();COMMIT;')==self.plan['systemId'],'CLUSTER_CHANGED')
        need(json.loads(self.operator.database_sql('helior','BEGIN READ ONLY;'+registry['registrySql']+';COMMIT;'))==registry['registry'],'LIVE_REGISTRY_CHANGED')

    def artifacts(self):
        return {n:protected(self.root/n,0o644) for n in self.plan['oldArtifacts']}

    def publish(self,data,expected):
        need(all(sha(protected(self.root/n,0o644))==h for n,h in expected.items()),'ARTIFACT_CAS_CHANGED')
        for name,raw in data.items():
            target=self.root/name; fd,temporary=tempfile.mkstemp(prefix='.online-release-',dir=target.parent)
            try:
                with os.fdopen(fd,'wb') as stream: stream.write(raw); stream.flush(); os.fchmod(stream.fileno(),0o644); os.fsync(stream.fileno())
                os.replace(temporary,target)
            finally:
                if os.path.exists(temporary): os.unlink(temporary)
        fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
        need(all(protected(self.root/n,0o644)==raw for n,raw in data.items()),'ARTIFACT_PUBLICATION_READBACK_FAILED')

    def snapshot(self):
        ids=self.command(['ps','-aq']).split(); need(ids,'FLEET_EMPTY')
        return fleet_snapshot(json.loads(self.command(['inspect',*ids])))

    def replace(self,name,image):
        need(name in {s['service'] for s in self.plan['selected']},'UNSELECTED_REPLACEMENT')
        file=self.model_file(name,image,self.verify_environment(name,image))
        self.command(['compose','--project-name','apps','--project-directory',str(self.root),'--env-file','/dev/null','--file',str(file),'up','--detach','--no-deps','--no-build','--pull','never','--force-recreate',name])

    def model_file(self,name,image,networks=None):
        model=json.loads(protected(self.root/'compose.json',0o644))
        model['services']={name:model['services'][name]}; model['services'][name]['image']=image
        model['networks']={n:model['networks'][n] for n in model['services'][name].get('networks',{})} if networks is None else networks
        file=self.work/(name+'-'+image.split(':')[1]+('-external' if networks is not None else '')+'.json')
        if not file.exists(): self.save(file.name,model)
        else: need(json.loads(protected(file))==model,'PRIVATE_SERVICE_MODEL_CHANGED')
        return file

    def verify_environment(self,name,image):
        need(self.environment is not None,'PRIVATE_ENVIRONMENT_BASELINE_REQUIRED')
        file=self.model_file(name,image)
        resolved=json.loads(self.command(['compose','--project-name','apps','--project-directory',str(self.root),'--env-file','/dev/null','--file',str(file),'config','--format','json']))
        image_config=json.loads(self.command(['image','inspect',image]))[0]['Config']
        need(self.hostDefaults is not None,'ENGINE_HOST_DEFAULTS_NOT_REVIEWED')
        intended_contract(resolved,name,image_config,self.privateContracts[name],self.hostDefaults)
        networks={}
        for logical in resolved['services'][name].get('networks',{}):
            actual=resolved['networks'][logical]['name']; expected=self.privateContracts[name]['NetworkSettings']['Networks'][actual]['NetworkID']
            need(json.loads(self.command(['network','inspect',actual]))[0]['Id']==expected,'INTENDED_NETWORK_ID_CHANGED')
            networks[logical]=dict(external=True,name=actual)
        for volume in resolved['services'][name].get('volumes',[]):
            source=Path(volume['source'])
            need(volume['type']=='bind' and volume.get('bind',{}).get('create_host_path') is False and source.is_absolute() and source.exists() and source.resolve()==source,'INTENDED_MOUNT_SOURCE_UNSAFE')
        intended=env_map(image_config.get('Env'))
        values=resolved['services'][name].get('environment',{})
        need(isinstance(values,dict),'RESOLVED_ENVIRONMENT_INVALID')
        for key,value in values.items():
            if value is None: intended.pop(key,None)
            else: intended[key]=str(value)
        need(intended==self.environment[name],'INTENDED_ENVIRONMENT_CHANGED')
        return networks

    def probe(self,name):
        spec=copy.deepcopy(self.plan['probes'][name]); runtime=self.plan['probeRuntime']
        network=probe_network(self.plan,spec)
        if 'headersFile' in spec:
            binding=spec.pop('headersFile'); raw=protected(binding['path']); need(sha(raw)==binding['sha256'],'PROBE_SESSION_CHANGED'); spec['headers']=json.loads(raw)
        for attempt in range(spec['attempts']):
            need(json.loads(self.command(['network','inspect',network['name']]))[0]['Id']==network['id'],'PROBE_NETWORK_CHANGED')
            try:
                result=self.command(['run','--rm','--pull','never','--network',network['id'],'--read-only','--log-driver','none','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','32','--memory','128m','-i','--entrypoint','node',runtime['image'],'-e',PROBE],json.dumps(spec))
                need(json.loads(result)=={'ok':True},'EXPLICIT_HTTP_PROBE_FAILED'); return
            except Exception:
                if attempt+1==spec['attempts']: raise ValueError('EXPLICIT_HTTP_PROBE_FAILED') from None
                time.sleep(spec['intervalSeconds'])


PROBE = r"""let input='';process.stdin.on('data',b=>input+=b);process.stdin.on('end',async()=>{try{const p=JSON.parse(input);const r=await fetch(p.url,{method:p.method,redirect:'error',signal:AbortSignal.timeout(10000),headers:{'content-type':'application/json',...(p.headers||{})},...(p.method==='POST'?{body:JSON.stringify({query:p.query,variables:p.variables||{}})}:{})});if(r.status!==p.expectedStatus)throw 0;const text=await r.text();if('expectedText'in p&&text!==p.expectedText)throw 0;if(p.bodySha256&&require('node:crypto').createHash('sha256').update(text).digest('hex')!==p.bodySha256)throw 0;let data;if(p.method==='POST'||p.jsonChecks){data=JSON.parse(text);if(p.expectedErrorCodes){if(data.data!==null||!Array.isArray(data.errors)||JSON.stringify(data.errors.map(e=>e.extensions.code))!==JSON.stringify(p.expectedErrorCodes))throw 0;}else if(data.errors)throw 0;}if(p.jsonChecks){for(const c of p.jsonChecks){let v=data;for(const k of c.path)v=v[k];if(JSON.stringify(v)!==JSON.stringify(c.equals))throw 0;}}process.stdout.write('{"ok":true}');}catch{process.stderr.write('READ_ONLY_PROBE_FAILED');process.exitCode=1;}});"""


def main(argv=None,adapter_factory=Native,root_check=None):
    parser=argparse.ArgumentParser(); parser.add_argument('--apply',action='store_true'); parser.add_argument('--plan',required=True); parser.add_argument('--plan-sha256',required=True); args=parser.parse_args(argv)
    need(args.apply and (root_check() if root_check else hasattr(os,'geteuid') and os.geteuid()==0),'ROOT_EXPLICIT_APPLY_REQUIRED')
    raw=Path(args.plan).read_bytes(); need(sha(raw)==args.plan_sha256,'PLAN_CHANGED'); plan=json.loads(raw); validate(plan)
    report=execute(plan,adapter_factory(plan)); print(json.dumps(report)); return report


if __name__=='__main__':
    try: main()
    except Exception as error:
        print(json.dumps(dict(completed=False,code=str(error) if type(error)is ValueError and re.fullmatch('[A-Z_]+',str(error)) else 'ONLINE_RELEASE_FAILED_RAW_OUTPUT_SUPPRESSED',operatorReviewRequired=True)),file=sys.stderr); sys.exit(1)
