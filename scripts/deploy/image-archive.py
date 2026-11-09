#!/usr/bin/env python3
"""Read Docker save metadata without extracting paths; bind loaded IDs to archives."""
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tarfile


def require(ok, message):
    if not ok:
        raise ValueError(message)


def identities(filename, tag):
    with tarfile.open(filename, 'r:') as archive:
        members = archive.getmembers()
        names = [m.name for m in members]
        require(len(names) == len(set(names)), 'Duplicate archive entry')

        def read(name):
            require(not name.startswith('/') and '..' not in name.split('/'), 'Unsafe metadata path')
            member = archive.getmember(name)
            require(member.isfile() and member.size <= 8 * 1024 * 1024, 'Invalid image metadata')
            return archive.extractfile(member).read()

        manifest = json.loads(read('manifest.json'))
        require(len(manifest) == 1 and manifest[0]['RepoTags'] == [tag], 'Archive tag mismatch')
        entry = manifest[0]
        require(re.fullmatch(r'(?:blobs/sha256/)?[a-f0-9]{64}(?:\.json)?', entry['Config']), 'Invalid config path')
        config_bytes = read(entry['Config'])
        config_digest = 'sha256:' + hashlib.sha256(config_bytes).hexdigest()
        require(pathlib.PurePosixPath(entry['Config']).name.removesuffix('.json') == config_digest[7:], 'Config digest mismatch')
        config = json.loads(config_bytes)
        require(config.get('os') == 'linux' and config.get('architecture') == 'amd64', 'Expected linux/amd64')
        accepted = {config_digest}

        def descriptor(item):
            require(re.fullmatch(r'sha256:[a-f0-9]{64}', item['digest']), 'Invalid descriptor')
            data = read('blobs/sha256/' + item['digest'][7:])
            require(len(data) == item['size'] and 'sha256:' + hashlib.sha256(data).hexdigest() == item['digest'], 'Descriptor digest mismatch')
            return json.loads(data)

        if 'index.json' in names:
            index = json.loads(read('index.json'))
            roots = [d for d in index['manifests'] if d.get('annotations', {}).get('io.containerd.image.name') == 'docker.io/library/' + tag]
            require(len(roots) == 1, 'Missing image index identity')
            root = roots[0]
            image = descriptor(root)
            digests = {root['digest']}
            if 'manifests' in image:
                platforms = [d for d in image['manifests'] if d.get('platform', {}).get('os') == 'linux' and d.get('platform', {}).get('architecture') == 'amd64']
                require(len(platforms) == 1, 'Ambiguous platform')
                digests.add(platforms[0]['digest'])
                image = descriptor(platforms[0])
            require(image['config']['digest'] == config_digest and image['config']['size'] == len(config_bytes), 'Manifest config mismatch')
            require(['blobs/sha256/' + d['digest'][7:] for d in image['layers']] == entry['Layers'], 'Layer manifest mismatch')
            accepted.update(digests)
        return accepted


def main(args):
    require(len(args) in (2, 3), 'Usage: image-archive.py IMAGE_DIR TAG [--load]')
    directory, tag = args[:2]
    require(re.fullmatch(r'[a-zA-Z0-9_.-]+', tag), 'Invalid release tag')
    require(len(args) == 2 or args[2] == '--load', 'Invalid operation')
    records = []
    for image in ('svc', 'gateway', 'ui', 'organization-events'):
        expected = 'kabipay-' + image + ':' + tag
        filename = pathlib.Path(directory) / ('kabipay-' + image + '-' + tag + '.tar')
        records.append((filename, expected, identities(filename, expected)))
    # Check all archives before loading any; a pre-existing tag cannot prove a load.
    if len(args) == 3:
        for filename, expected, accepted in records:
            subprocess.run(['docker', 'load', '--input', str(filename)], check=True)
            loaded = subprocess.check_output(['docker', 'image', 'inspect', expected, '--format', '{{.Id}}'], text=True).strip()
            require(loaded in accepted, 'Loaded image identity mismatch')
    print('Verified four archive tags, platforms and image identities.')


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except Exception:
        print('Image archive verification/load failed; application startup blocked.', file=sys.stderr)
        sys.exit(1)
