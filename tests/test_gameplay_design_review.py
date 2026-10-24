"""Static and fixture contracts, not agent behavior or gameplay acceptance.

PyYAML is an existing project optional test dependency. Publisher observations
are recorded separately because they belong to a pinned external core version.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill/dcc-gameplay-design-review"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frontmatter():
    return yaml.safe_load((SKILL / "SKILL.md").read_text().split("---", 2)[1])


class GameplayDesignReviewTests(unittest.TestCase):
    def test_standard_frontmatter(self):
        data = frontmatter()
        self.assertEqual(data["name"], SKILL.name)
        self.assertRegex(data["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertLessEqual(len(data["name"]), 64)
        self.assertTrue(0 < len(data["description"]) <= 1024)
        self.assertEqual(data["license"], "MIT")
        self.assertTrue(all(isinstance(k, str) and isinstance(v, str)
                            for k, v in data.get("metadata", {}).items()))

    def test_references_resolve_inside_skill(self):
        links = re.findall(r"\]\(([^)]+)\)", (SKILL / "SKILL.md").read_text())
        self.assertTrue(links)
        for link in links:
            path = (SKILL / link).resolve()
            path.relative_to(SKILL.resolve())
            self.assertTrue(path.is_file(), link)

    def test_example_cannot_claim_verified_asset_or_public_rights(self):
        data = json.loads((SKILL / "assets/asset-sidecar.example.json").read_text())
        self.assertTrue(data["example_only"])
        self.assertEqual(data["visibility"], "private")
        self.assertEqual(data["rights"]["redistribution"], "unknown")
        self.assertEqual(data["rights"]["license"], "unknown")
        self.assertEqual(data["import_validation"]["status"], "not-tested")
        self.assertIsNone(data["project_lock"])
        self.assertTrue(all(f["sha256"] is None for f in data["files"]))

    def test_optional_sidecar_preserves_existing_manifest_hash_contract(self):
        manifest = load_module(ROOT / "skill/pipeline-publish/scripts/_manifest.py",
                               "gameplay_existing_manifest")
        with tempfile.TemporaryDirectory() as directory:
            asset = Path(directory) / "original.txt"
            asset.write_bytes(b"local test fixture, not a game asset")
            record = manifest.file_record(str(asset), "source")
            self.assertEqual(record["sha256"], hashlib.sha256(asset.read_bytes()).hexdigest())
            data = {"schema": manifest.SCHEMA, "project": "test", "entity": {},
                    "version": 1, "files": [record]}
            self.assertEqual(manifest.validate(data), [])
            augmented = copy.deepcopy(data)
            augmented["asset_sidecar"] = "private-sidecar.json"
            self.assertEqual(manifest.validate(augmented), [])
            asset.write_bytes(b"changed")
            self.assertTrue(any("hash changed" in e for e in manifest.validate(augmented)))


if __name__ == "__main__":
    unittest.main()
