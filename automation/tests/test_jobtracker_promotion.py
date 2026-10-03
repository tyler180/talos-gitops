import copy
import importlib.util
import unittest
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('promotion', BASE / 'automation/validate_jobtracker_promotion.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PromotionTests(unittest.TestCase):
    def setUp(self):
        self.before = list(yaml.safe_load_all((BASE / module.DEPLOYMENT).read_text()))
        self.container = next(d for d in self.before if d['kind'] == 'Deployment')['spec']['template']['spec']['containers'][0]
        self.container['image'] = 'ghcr.io/tyler180/jobtracker:v0.2.4@sha256:' + 'a' * 64
        self.after = copy.deepcopy(self.before)
        self.new = next(d for d in self.after if d['kind'] == 'Deployment')['spec']['template']['spec']['containers'][0]
        self.new['image'] = 'ghcr.io/tyler180/jobtracker:v0.2.5@sha256:' + 'b' * 64

    def test_accepts_only_image_update(self):
        module.validate_documents(self.before, self.after)

    def test_rejects_storage_and_config_changes(self):
        self.after[0]['spec']['storageClassName'] = 'other'
        with self.assertRaises(ValueError): module.validate_documents(self.before, self.after)
        self.after = copy.deepcopy(self.before)
        self.new = next(d for d in self.after if d['kind'] == 'Deployment')['spec']['template']['spec']['containers'][0]
        self.new['image'] = 'ghcr.io/tyler180/jobtracker:v0.2.5@sha256:' + 'b' * 64
        self.new['env'][0]['value'] = ':8081'
        with self.assertRaises(ValueError): module.validate_documents(self.before, self.after)

    def test_rejects_unpinned_or_nonadvancing_version(self):
        for image in ('ghcr.io/tyler180/jobtracker:latest',
                      'ghcr.io/tyler180/jobtracker:v0.2.4@sha256:' + 'b'*64,
                      'ghcr.io/tyler180/jobtracker:v0.2.3@sha256:' + 'b'*64):
            self.new['image'] = image
            with self.assertRaises(ValueError): module.validate_documents(self.before, self.after)


if __name__ == '__main__': unittest.main()
