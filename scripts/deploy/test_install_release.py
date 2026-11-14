"""Offline public-artifact installation tests; no database, secrets or SSH."""
import hashlib,importlib.util,json,os,stat,subprocess,sys,tempfile,unittest,uuid,zipfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('subject',Path(__file__).with_name('install-release.py'))
subject=importlib.util.module_from_spec(spec);spec.loader.exec_module(subject)
class Install(unittest.TestCase):
 def fixture(self,where,extra=None,root='/opt/apps/hrms'):
  files={'release.json':b'{"tag":"synthetic-001","mode":"organization","artifacts":["compose.json","release.json","release.sha256"]}',
         'compose.json':b'{"services":{}}','release.sha256':b'synthetic',
         'scripts/release.sh':b'#!/bin/sh\nexit 0\n'}
  for name in subject.HELPERS:files.setdefault('scripts/'+name,b'synthetic helper')
  files.update(extra or {})
  manifest=dict(version=1,appDir=root,imageDir=root+'/images/synthetic-001',tag='synthetic-001',mode='organization',syncCompose=True,loadImages=False,startApplications=False,validateApplications=False,
   files=[dict(path=n,sha256=hashlib.sha256(b).hexdigest())for n,b in sorted(files.items())])
  zip_path=where/'release.zip'
  with zipfile.ZipFile(zip_path,'w')as archive:
   archive.writestr('bundle.json',json.dumps(manifest))
   for n,b in files.items():archive.writestr(n,b)
  return zip_path,hashlib.sha256(zip_path.read_bytes()).hexdigest(),files
 def test_installs_public_files_and_preserves_protected_files(self):
  with tempfile.TemporaryDirectory()as temp:
   base=Path(temp);root=base/'hrms';root.mkdir();(root/'env').mkdir();secret=root/'env/runtime.env';secret.write_bytes(b'synthetic-only')
   bundle,sha,files=self.fixture(base);manifest,contents=subject.read_bundle(bundle,sha)
   subject.install(root,contents);subject.install(root,contents)
   self.assertEqual(secret.read_bytes(),b'synthetic-only')
   for n,b in files.items():self.assertEqual((root/n).read_bytes(),b)
   if os.name=='posix':self.assertEqual(stat.S_IMODE((root/'compose.json').stat().st_mode),0o644)
   self.assertFalse(any(manifest[k]for k in ('loadImages','startApplications','validateApplications')))
   manifest['syncCompose']=False
   self.assertTrue(all(name.startswith('scripts/')for name in subject.installation_contents(manifest,contents)))
 def test_rejects_bad_hash_extra_member_and_protected_paths(self):
  with tempfile.TemporaryDirectory()as temp:
   base=Path(temp);bundle,sha,_=self.fixture(base)
   with self.assertRaisesRegex(ValueError,'BUNDLE_DIGEST_CHANGED'):subject.read_bundle(bundle,'0'*64)
   with zipfile.ZipFile(bundle,'a')as archive:archive.writestr('unexpected.txt','x')
   with self.assertRaisesRegex(ValueError,'BUNDLE_MEMBER_SET_CHANGED'):subject.read_bundle(bundle,hashlib.sha256(bundle.read_bytes()).hexdigest())
   for name in ('../outside','env/runtime.env','secrets/private.key','data/anything','config/../../outside'):
    bundle,sha,_=self.fixture(base,{name:b'blocked'})
    with self.assertRaisesRegex(ValueError,'UNREVIEWED_ARTIFACT_PATH'):subject.read_bundle(bundle,sha)
 def test_rejects_symlink_parent_before_any_file_changes(self):
  if os.name!='posix':self.skipTest('POSIX symlink proof runs in the Linux fixture')
  with tempfile.TemporaryDirectory()as temp:
   base=Path(temp);root=base/'hrms';root.mkdir();outside=base/'outside';outside.mkdir();(root/'config').symlink_to(outside,target_is_directory=True)
   with self.assertRaisesRegex(ValueError,'UNSAFE_DESTINATION_PATH'):subject.install(root,{'compose.json':b'x','config/ui-config.json':b'y'})
   self.assertFalse((root/'compose.json').exists());self.assertEqual(list(outside.iterdir()),[])
 @unittest.skipUnless(os.name=='posix'and hasattr(os,'geteuid')and os.geteuid()==0,'POSIX root fixture')
 def test_claims_only_public_application_directories_and_preserves_private_ownership(self):
  with tempfile.TemporaryDirectory()as temp:
   base=Path(temp);root=base/'hrms';root.mkdir();config=root/'config';config.mkdir();private=root/'secrets';private.mkdir(mode=0o700)
   os.chown(root,1000,1000);os.chown(config,1000,1000);os.chown(private,1234,1234)
   subject.install(root,{'compose.json':b'x','config/ui-config.json':b'y'})
   self.assertEqual((root.stat().st_uid,config.stat().st_uid),(0,0))
   self.assertEqual(private.stat().st_uid,1234)
   self.assertEqual(stat.S_IMODE(private.stat().st_mode),0o700)
   self.assertEqual(base.stat().st_uid,0)
 def test_rejects_protected_shared_or_unrelated_application_roots(self):
  with tempfile.TemporaryDirectory()as temp:
   for root in ('/opt/apps/hrms/env','/opt/apps/hrms/secrets','/opt/apps/hrms/data','/opt/apps/data','/opt/apps/finance'):
    bundle,sha,_=self.fixture(Path(temp),root=root)
    with self.assertRaisesRegex(ValueError,'INVALID_APPLICATION_ROOT'):subject.read_bundle(bundle,sha)
 def test_action_arguments_are_exact_and_sync_only_does_not_execute(self):
  with tempfile.TemporaryDirectory()as temp:
   bundle,sha,_=self.fixture(Path(temp));manifest,_=subject.read_bundle(bundle,sha);calls=[]
   subject.release(manifest,lambda args:calls.append(args))
   self.assertEqual(calls,[])
   manifest['startApplications']=True
   subject.release(manifest,lambda args:calls.append(args))
   self.assertEqual(calls,[['bash','/opt/apps/hrms/scripts/release.sh','/opt/apps/hrms','/opt/apps/hrms/images/synthetic-001','synthetic-001','0','1','0','organization']])
 @unittest.skipUnless(os.environ.get('PRIVATE_RELEASE_CLI_TEST')=='1','Explicit isolated Linux container fixture only')
 def test_cli_sync_installs_as_root_and_preserves_private_runtime_file(self):
  self.assertEqual(os.geteuid(),0)
  stage=Path('/tmp')/('hrms-release-'+uuid.uuid4().hex);stage.mkdir(mode=0o700)
  bundle,sha,files=self.fixture(stage)
  root=Path('/opt/apps/hrms');(root/'env').mkdir(parents=True,mode=0o700)
  sentinel=root/'env/synthetic.env';sentinel.write_bytes(b'fixture-only-not-production')
  Path('/run/lock').mkdir(parents=True,exist_ok=True)
  result=subprocess.run([sys.executable,str(Path(subject.__file__)),str(bundle),sha],capture_output=True,text=True,timeout=15)
  self.assertEqual(result.returncode,0,result.stderr)
  receipt=json.loads(result.stdout.strip());self.assertEqual(receipt['status'],'public_release_artifacts_installed')
  self.assertEqual(sentinel.read_bytes(),b'fixture-only-not-production')
  for name,data in files.items():self.assertEqual((root/name).read_bytes(),data)
if __name__=='__main__':unittest.main()
