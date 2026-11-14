"""Synthetic inputs only; never reads an environment or key file."""
import base64
import copy
import unittest
import profile_encryption as subject

class ProfileConfiguration(unittest.TestCase):
    def setUp(self):
        self.key=base64.b64encode(bytes(range(32))).decode()
        self.compose={'services':{'shared-employee':{'env_file':['/opt/apps/hrms/env/shared/runtime.env','/opt/apps/hrms/env/metadata/employee.env']},'shared-leave':{'env_file':['/opt/apps/hrms/env/shared/runtime.env']}}}

    def test_existing_key_preserved_exactly_without_other_environment_fields(self):
        for value in (self.key,"'"+self.key+"'",'"'+self.key+'"'):
            result=subject.existing_key('UNRELATED=never-copy\r\nKABIPAY_PROFILE_CHANGE_ENCRYPTION_KEY='+value+'\r\n')
            self.assertEqual(result,self.key)
            self.assertEqual(subject.environment_bytes(result),('KABIPAY_PROFILE_CHANGE_ENCRYPTION_KEY=\''+self.key+'\'\n').encode())

    def test_missing_invalid_duplicate_or_interpolated_key_fails_without_generation(self):
        for raw in ('OTHER=value','KABIPAY_PROFILE_CHANGE_ENCRYPTION_KEY=',
                    'KABIPAY_PROFILE_CHANGE_ENCRYPTION_KEY=not-base64',
                    'KABIPAY_PROFILE_CHANGE_ENCRYPTION_KEY=${OTHER}',
                    'KABIPAY_PROFILE_CHANGE_ENCRYPTION_KEY='+base64.b64encode(bytes(16)).decode(),
                    ('KABIPAY_PROFILE_CHANGE_ENCRYPTION_KEY='+self.key+'\n')*2):
            with self.assertRaises(ValueError): subject.existing_key(raw)

    def test_only_employee_receives_key_file_and_input_is_unchanged(self):
        before=copy.deepcopy(self.compose)
        after=subject.compose_with_profile_environment(self.compose,'/opt/apps/hrms')
        self.assertEqual(self.compose,before)
        self.assertEqual(after['services']['shared-leave'],before['services']['shared-leave'])
        self.assertEqual(after['services']['shared-employee']['env_file'],[
            '/opt/apps/hrms/env/shared/runtime.env','/opt/apps/hrms/env/shared/employee-profile.env','/opt/apps/hrms/env/metadata/employee.env'])
        self.assertEqual(subject.compose_with_profile_environment(after,'/opt/apps/hrms'),after)

    def test_ambiguous_paths_or_other_consumers_fail_closed(self):
        for root in ('relative','/opt/apps/../hrms','/opt/apps/hrms/'):
            with self.assertRaises(ValueError):subject.compose_with_profile_environment(self.compose,root)
        value=copy.deepcopy(self.compose)
        value['services']['shared-leave']['env_file'].append('/opt/apps/hrms/env/shared/employee-profile.env')
        with self.assertRaises(ValueError):subject.compose_with_profile_environment(value,'/opt/apps/hrms')

if __name__=='__main__':unittest.main()
