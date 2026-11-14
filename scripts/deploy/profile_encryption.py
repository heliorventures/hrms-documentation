"""Pure profile-key preservation and Employee-only Compose configuration.

No I/O, key generation or logging. The operator supplies existing configuration
privately; keys must never be printed, rotated or replaced during migration.
"""
import base64
import copy
import re

KEY_NAME='KABIPAY_PROFILE_CHANGE_ENCRYPTION_KEY'

def need(ok,code):
    if not ok:raise ValueError(code)

def valid_key(value):
    need(isinstance(value,str) and len(value)==44,'PROFILE_KEY_FORMAT_INVALID')
    try:decoded=base64.b64decode(value,validate=True)
    except Exception:raise ValueError('PROFILE_KEY_FORMAT_INVALID') from None
    need(len(decoded)==32 and base64.b64encode(decoded).decode()==value,'PROFILE_KEY_FORMAT_INVALID')
    return value

def existing_key(text):
    need(isinstance(text,str) and len(text)<=1048576,'LEGACY_CONFIGURATION_INVALID')
    found=[]
    for line in text.splitlines():
        match=re.fullmatch(r'\s*(?:export\s+)?'+KEY_NAME+r'\s*=\s*(.*?)\s*',line)
        if not match:continue
        value=match[1]
        if len(value)>=2 and value[0] in "\"'" and value[-1]==value[0]:value=value[1:-1]
        found.append(value)
    need(len(found)==1,'EXACT_EXISTING_PROFILE_KEY_REQUIRED')
    return valid_key(found[0])

def environment_bytes(key):
    return (KEY_NAME+"='"+valid_key(key)+"'\n").encode()

def compose_with_profile_environment(document,root):
    need(isinstance(root,str) and re.fullmatch(r'/[a-zA-Z0-9_./-]+',root)
         and not root.endswith('/') and not any(p in ('','..','.') for p in root.split('/')[1:]),'APPLICATION_ROOT_INVALID')
    value=copy.deepcopy(document);services=value.get('services',{})
    need(isinstance(services,dict) and 'shared-employee' in services,'SHARED_EMPLOYEE_REQUIRED')
    file=root+'/env/shared/employee-profile.env'
    for name,service in services.items():
        if name!='shared-employee':need(file not in service.get('env_file',[]),'PROFILE_KEY_SCOPE_CHANGED')
    employee=services['shared-employee'];files=employee.get('env_file')
    need(isinstance(files,list) and all(isinstance(p,str) for p in files)
         and files.count(root+'/env/metadata/employee.env')==1 and files[-1]==root+'/env/metadata/employee.env'
         and files.count(file)<=1 and KEY_NAME not in employee.get('environment',{}),'EMPLOYEE_ENVIRONMENT_CHANGED')
    if file not in files:files.insert(len(files)-1,file)
    return value
