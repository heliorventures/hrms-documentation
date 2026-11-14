#!/usr/bin/env python3
"""Install a verified public HRMS release bundle; never read runtime secrets."""
import hashlib,io,json,os,re,stat,subprocess,sys,tempfile,zipfile
from pathlib import Path,PurePosixPath

HELPERS={'release.sh','reconcile-env.sh','check-inventory.sh','check-shared-config.mjs','startup-scope.mjs','image-archive.py'}
TOP={'compose.json','compose-active.json','release.json','release.sha256','required-tenants.txt','finance-checks.txt','private-files.txt','company-configs.txt','startup-services.txt','cutover-inventory.txt'}

def require(ok,code):
 if not ok:raise ValueError(code)

def artifact(name):
 require(isinstance(name,str)and len(name)<=200 and not any(p in ('','.','..')for p in name.split('/')),'UNREVIEWED_ARTIFACT_PATH')
 allowed=name in TOP or name.startswith('scripts/')and name[8:]in HELPERS
 allowed=allowed or re.fullmatch(r'caddy/[a-z][a-z-]*\.caddy',name)is not None
 allowed=allowed or re.fullmatch(r'config/(?:companies/[a-z]+|ui-[a-z0-9-]+)\.json',name)is not None
 require(allowed,'UNREVIEWED_ARTIFACT_PATH');return name

def read_bundle(file,expected_sha):
 require(re.fullmatch('[0-9a-f]{64}',expected_sha)is not None,'INVALID_BUNDLE_DIGEST')
 require(file.is_file()and not file.is_symlink()and file.stat().st_size<=32*1024*1024,'UNSAFE_BUNDLE_FILE')
 data=file.read_bytes();require(hashlib.sha256(data).hexdigest()==expected_sha,'BUNDLE_DIGEST_CHANGED')
 with zipfile.ZipFile(io.BytesIO(data))as archive:
  members=archive.infolist();names=[m.filename for m in members]
  require(len(names)==len(set(names))and 1<len(names)<=1000 and sum(m.file_size for m in members)<=32*1024*1024,'INVALID_BUNDLE_MEMBERS')
  require(all(not m.is_dir()and not stat.S_ISLNK(m.external_attr>>16)and m.file_size<=4*1024*1024 for m in members),'INVALID_BUNDLE_MEMBER_TYPE')
  require('bundle.json'in names,'MISSING_BUNDLE_MANIFEST')
  manifest=json.loads(archive.read('bundle.json'))
  require(isinstance(manifest,dict)and set(manifest)=={'version','appDir','imageDir','tag','mode','syncCompose','loadImages','startApplications','validateApplications','files'},'INVALID_BUNDLE_MANIFEST')
  require(manifest['version']==1 and manifest['mode']=='organization'and re.fullmatch('[A-Za-z0-9_.-]+',manifest['tag'])is not None,'INVALID_RELEASE_IDENTITY')
  root=manifest['appDir'];images=manifest['imageDir']
  require(isinstance(root,str)and re.fullmatch(r'/(?:opt|srv)/apps/hrms(?:-[a-z0-9][a-z0-9-]{0,30})?',root)is not None,'INVALID_APPLICATION_ROOT')
  require(isinstance(images,str)and images.startswith(root+'/images')and(images==root+'/images'or images.startswith(root+'/images/'))and '..'not in PurePosixPath(images).parts and str(PurePosixPath(images))==images,'INVALID_IMAGE_DIRECTORY')
  require(all(type(manifest[n])is bool for n in ('syncCompose','loadImages','startApplications','validateApplications')),'INVALID_RELEASE_ACTIONS')
  entries=manifest['files'];require(isinstance(entries,list)and 0<len(entries)<1000,'INVALID_ARTIFACT_LIST')
  wanted={};contents={}
  for item in entries:
   require(isinstance(item,dict)and set(item)=={'path','sha256'},'INVALID_ARTIFACT_ENTRY')
   name=artifact(item['path']);require(name not in wanted and re.fullmatch('[0-9a-f]{64}',item['sha256'])is not None,'INVALID_ARTIFACT_DIGEST');wanted[name]=item['sha256']
  require(set(names)==set(wanted)|{'bundle.json'},'BUNDLE_MEMBER_SET_CHANGED')
  for name,sha in wanted.items():
   contents[name]=archive.read(name);require(hashlib.sha256(contents[name]).hexdigest()==sha,'ARTIFACT_DIGEST_CHANGED')
  require({'release.json','release.sha256','compose.json','scripts/release.sh'}<=set(contents),'INCOMPLETE_RELEASE')
  release=json.loads(contents['release.json']);require(release.get('tag')==manifest['tag']and release.get('mode')=='organization','RENDERED_RELEASE_IDENTITY_CHANGED')
  artifacts=release.get('artifacts');require(isinstance(artifacts,list)and len(artifacts)==len(set(artifacts))and all(artifact(n)==n for n in artifacts),'INVALID_RENDERED_ARTIFACTS')
  helpers={'scripts/'+n for n in HELPERS}
  require(set(wanted)==set(artifacts)|helpers|({'cutover-inventory.txt'}if manifest['startApplications']else set()),'RENDERED_ARTIFACT_SET_CHANGED')
  return manifest,contents

def destination(root,name):
 artifact(name);target=root/name
 for item in [root,*reversed(root.parents),*list(target.parents)[:-1],target]:
  if item.is_symlink():raise ValueError('UNSAFE_DESTINATION_PATH')
  if item.exists():
   require(item.is_file()if item==target else item.is_dir(),'UNSAFE_DESTINATION_PATH')
   if os.name=='posix':require(stat.S_IMODE(item.stat().st_mode)&0o022==0,'UNSAFE_DESTINATION_PERMISSIONS')
 return target

def install(root,contents):
 require(root.is_absolute(),'ABSOLUTE_APPLICATION_ROOT_REQUIRED')
 targets={name:destination(root,name)for name in contents}
 # Preflight every destination before publishing any public artifact.
 public_directories={root}
 for target in targets.values():
  missing=[];parent=target.parent
  while not parent.exists():missing.append(parent);parent=parent.parent
  for directory in reversed(missing):directory.mkdir(mode=0o755);directory.chmod(0o755)
  parent=target.parent
  while parent==root or root in parent.parents:
   public_directories.add(parent)
   if parent==root:break
   parent=parent.parent
 # Root installation owns only its application root and public publication
 # parents. Never recursively chown env, secrets, data or platform ancestors.
 if os.name=='posix':
  for directory in sorted(public_directories,key=lambda p:len(p.parts)):
   descriptor=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
   try:
    info=os.fstat(descriptor);require(stat.S_ISDIR(info.st_mode)and stat.S_IMODE(info.st_mode)&0o022==0,'UNSAFE_DESTINATION_PERMISSIONS')
    os.fchown(descriptor,0,0);os.fsync(descriptor)
   finally:os.close(descriptor)
 for name,target in targets.items():
  fd,temporary=tempfile.mkstemp(prefix='.hrms-release-',dir=target.parent)
  try:
   with os.fdopen(fd,'wb')as handle:
    handle.write(contents[name]);handle.flush();os.fsync(handle.fileno());os.fchmod(handle.fileno(),0o600 if name=='cutover-inventory.txt'else 0o644)
   os.replace(temporary,target)
   if os.name=='posix':
    descriptor=os.open(target.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)
  finally:
   if os.path.exists(temporary):os.unlink(temporary)
 for name,target in targets.items():require(target.read_bytes()==contents[name],'INSTALLED_ARTIFACT_READBACK_FAILED')

def release(manifest,runner=subprocess.check_call):
 if not any(manifest[n]for n in ('loadImages','startApplications','validateApplications')):return
 runner(['bash',manifest['appDir']+'/scripts/release.sh',manifest['appDir'],manifest['imageDir'],manifest['tag'],*['1'if manifest[n]else'0'for n in ('loadImages','startApplications','validateApplications')],manifest['mode']])

def installation_contents(manifest,contents):
 return contents if manifest['syncCompose']else{name:data for name,data in contents.items()if name.startswith('scripts/')or name=='cutover-inventory.txt'}

def main():
 if len(sys.argv)==4 and sys.argv[1]=='--check':
  manifest,contents=read_bundle(Path(sys.argv[2]),sys.argv[3])
  print(json.dumps(dict(status='release_bundle_verified',files=len(contents),tag=manifest['tag'],productionChanged=False,secretsRead=False)));return
 require(len(sys.argv)==3 and hasattr(os,'geteuid')and os.geteuid()==0,'ROOT_AND_REVIEWED_BUNDLE_REQUIRED')
 import fcntl
 file=Path(sys.argv[1]);require(file.parent.parent==Path('/tmp')and re.fullmatch('hrms-release-[0-9a-f]{32}',file.parent.name)is not None and file.parent.resolve()==file.parent,'INVALID_UPLOAD_DIRECTORY')
 info=file.parent.stat();require(stat.S_ISDIR(info.st_mode)and stat.S_IMODE(info.st_mode)==0o700,'UNSAFE_UPLOAD_DIRECTORY')
 os.umask(0o077)
 fd=os.open('/run/lock/hrms-release.lock',os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600)
 try:
  lock=os.fstat(fd);require(lock.st_uid==0 and stat.S_ISREG(lock.st_mode)and stat.S_IMODE(lock.st_mode)==0o600,'UNSAFE_RELEASE_LOCK')
  fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
  manifest,contents=read_bundle(file,sys.argv[2]);selected=installation_contents(manifest,contents);install(Path(manifest['appDir']),selected)
  print(json.dumps(dict(status='public_release_artifacts_installed',files=len(selected),tag=manifest['tag'],publicDirectoriesRootOwned=True,secretsRead=False,registryChanged=False)),flush=True)
  release(manifest)
 finally:os.close(fd)

if __name__=='__main__':
 try:main()
 except Exception as error:
  code=str(error)if type(error)is ValueError and re.fullmatch('[A-Z_]+',str(error))else'RELEASE_INSTALLATION_FAILED'
  print(json.dumps(dict(completed=False,code=code)),file=sys.stderr);sys.exit(1)
