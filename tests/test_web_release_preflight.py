"""Static instruction/template checks, not browser or store acceptance."""
import json
from pathlib import Path
import re
import unittest

import yaml

SKILL = Path(__file__).resolve().parents[1] / "skill/game-web-release-preflight"


class WebReleasePreflightTests(unittest.TestCase):
    def test_standard_frontmatter(self):
        data = yaml.safe_load((SKILL / "SKILL.md").read_text().split("---", 2)[1])
        self.assertEqual(data["name"], SKILL.name)
        self.assertRegex(data["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertLessEqual(len(data["name"]), 64)
        self.assertTrue(0 < len(data["description"]) <= 1024)
        self.assertEqual(data["license"], "MIT")
        self.assertTrue(all(isinstance(v, str) for v in data["metadata"].values()))

    def test_references_resolve_inside_skill(self):
        links = re.findall(r"\]\(([^)]+)\)", (SKILL / "SKILL.md").read_text())
        self.assertTrue(links)
        for link in links:
            path = (SKILL / link).resolve()
            path.relative_to(SKILL.resolve())
            self.assertTrue(path.is_file(), link)

    def test_handoff_cannot_claim_release_or_browser_evidence(self):
        data = json.loads((SKILL / "assets/handoff.example.json").read_text())
        self.assertTrue(data["example_only"])
        self.assertEqual(data["visibility"], "private")
        for key in ("upload_authorized", "uploaded", "review_submitted", "published"):
            self.assertIs(data[key], False)
        for key in ("browser_checks", "storage_checks", "touch_checks", "package_checks"):
            self.assertEqual(data[key]["status"], "not-tested")
            self.assertEqual(data[key]["evidence"], [])
        self.assertEqual(data["artifact"]["files"], [])
        self.assertIsNone(data["artifact"]["engine"])
        self.assertIsNone(data["artifact"]["version"])
        self.assertEqual(data["artifact"]["export_settings"], {})
        self.assertEqual(data["browser_checks"]["devices"], [])
        self.assertEqual(data["account_prerequisites"], "not-verified")
        self.assertEqual(data["cost_review"], "not-verified")
        self.assertEqual(data["rights_review"], "unknown")
        self.assertEqual(data["privacy_review"], "unknown")


if __name__ == "__main__":
    unittest.main()
