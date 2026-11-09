import hashlib
import importlib.util
import io
import json
import pathlib
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('archive', pathlib.Path(__file__).with_name('image-archive.py'))

class ArchiveTests(unittest.TestCase):
    def test_expected_tag_and_config_identity(self):
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / 'image.tar'
            config = json.dumps({'os': 'linux', 'architecture': 'amd64'}).encode()
            digest = hashlib.sha256(config).hexdigest()
            with tarfile.open(target, 'w') as archive:
                for name, data in [(digest + '.json', config), ('manifest.json', json.dumps([{'RepoTags': ['kabipay-svc:test'], 'Config': digest + '.json', 'Layers': []}]).encode())]:
                    item = tarfile.TarInfo(name); item.size = len(data)
                    archive.addfile(item, io.BytesIO(data))
            self.assertEqual(module.identities(target, 'kabipay-svc:test'), {'sha256:' + digest})
            with self.assertRaises(ValueError): module.identities(target, 'kabipay-ui:test')

if __name__ == '__main__': unittest.main()
