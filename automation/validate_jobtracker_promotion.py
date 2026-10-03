"""Allow unattended Jobtracker promotions to change only its pinned image."""
import argparse
import copy
import re
import subprocess
from pathlib import Path

import yaml

DEPLOYMENT = 'applications/jobtracker/deployment.yaml'
IMAGE = re.compile(r'ghcr\.io/tyler180/jobtracker:v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)@sha256:[a-f0-9]{64}$')


def validate_documents(before, after):
    expected = copy.deepcopy(before)
    containers = []
    previous = []
    for docs, found in ((expected, previous), (after, containers)):
        for doc in docs:
            if isinstance(doc, dict) and doc.get('kind') == 'Deployment' and doc.get('metadata', {}).get('name') == 'jobtracker':
                found.extend(c for c in doc['spec']['template']['spec']['containers'] if c.get('name') == 'jobtracker')
    if len(containers) != 1 or len(previous) != 1:
        raise ValueError('Expected exactly one Jobtracker Deployment/container')
    old, new = IMAGE.fullmatch(previous[0]['image']), IMAGE.fullmatch(containers[0]['image'])
    if not old or not new:
        raise ValueError('Both images must have a semantic version and SHA256 digest')
    if tuple(map(int, new.groups())) <= tuple(map(int, old.groups())):
        raise ValueError('An unattended promotion must advance the release version')
    previous[0]['image'] = containers[0]['image']
    if expected != after:
        raise ValueError('Unattended promotion may change only the Jobtracker image; storage and configuration must remain identical')


def validate(base, head):
    changed = subprocess.check_output(['git', 'diff', '--name-only', base, head], text=True).splitlines()
    if changed != [DEPLOYMENT]:
        raise ValueError('Unattended promotion must change only ' + DEPLOYMENT)
    before = subprocess.check_output(['git', 'show', f'{base}:{DEPLOYMENT}'], text=True)
    after = subprocess.check_output(['git', 'show', f'{head}:{DEPLOYMENT}'], text=True)
    validate_documents(list(yaml.safe_load_all(before)), list(yaml.safe_load_all(after)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', required=True)
    parser.add_argument('--head', required=True)
    args = parser.parse_args()
    validate(args.base, args.head)
