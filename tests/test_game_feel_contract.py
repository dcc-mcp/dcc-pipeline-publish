"""Pure-data design fixtures only; no engine, input or human-playtest claim."""
import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill/dcc-gameplay-design-review"
SCHEMA = json.loads((SKILL / "assets/game-feel.schema.json").read_text())
EXAMPLE = json.loads((SKILL / "assets/game-feel.example.json").read_text())
SWITCHES = ("response", "rhythm", "feedback", "forgiveness")


def validate_fixture(value):
    """Test-only fixture validation, not a production runtime validator."""
    Draft202012Validator(SCHEMA).validate(value)
    rhythm = value["rhythm"]["parameters"]
    if rhythm["combo_open_seconds"] > rhythm["combo_close_seconds"]:
        raise ValueError("base combo window must not be inverted")


def changed_paths(before, after, prefix=()):
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        keys = before.keys() | after.keys()
        if not prefix:
            keys -= {"trial_id", "config_digest", "verification"}
        for key in sorted(keys):
            if key not in before or key not in after:
                result.append(prefix + (key,))
            else:
                result.extend(changed_paths(before[key], after[key], prefix + (key,)))
        return result
    return [] if before == after else [prefix]


class GameFeelContractTests(unittest.TestCase):
    def test_schema_and_example_are_valid_but_unverified(self):
        Draft202012Validator.check_schema(SCHEMA)
        validate_fixture(EXAMPLE)
        self.assertTrue(EXAMPLE["example_only"])
        self.assertIsNone(EXAMPLE["baseline_digest"])
        self.assertIsNone(EXAMPLE["config_digest"])
        self.assertEqual(set(EXAMPLE["verification"].values()), {"not_run"})

    def test_four_independent_toggle_variants_retain_parameters(self):
        for name in SWITCHES:
            with self.subTest(name=name):
                variant = copy.deepcopy(EXAMPLE)
                variant[name]["enabled"] = True
                validate_fixture(variant)
                self.assertEqual(changed_paths(EXAMPLE, variant), [(name, "enabled")])
                variant[name]["enabled"] = False
                self.assertEqual(variant, EXAMPLE)

    def test_single_parameter_comparison_and_confounded_trial_detection(self):
        baseline = copy.deepcopy(EXAMPLE)
        baseline["forgiveness"]["enabled"] = True
        variant = copy.deepcopy(baseline)
        variant["forgiveness"]["parameters"]["input_buffer_seconds"] = 0.01
        validate_fixture(variant)
        self.assertEqual(changed_paths(baseline, variant), [
            ("forgiveness", "parameters", "input_buffer_seconds")
        ])
        variant["response"]["enabled"] = True
        self.assertEqual(len(changed_paths(baseline, variant)), 2,
                         "two changes cannot be reported as single-variable A/B")

    def test_comparison_ignores_only_top_level_trial_evidence(self):
        before = {"trial_id": "a", "config_digest": None,
                  "verification": {"notes": "fixture-a"},
                  "response": {"enabled": False}}
        after = copy.deepcopy(before)
        after.update(trial_id="b", config_digest="synthetic-digest",
                     verification={"notes": "fixture-b"})
        after["response"]["enabled"] = True
        self.assertEqual(changed_paths(before, after), [("response", "enabled")])
        # Do not hide future gameplay fields merely because their name matches
        # a top-level metadata key.
        after["response"]["verification"] = "nested-change"
        self.assertIn(("response", "verification"), changed_paths(before, after))

    def test_hitstop_has_separate_owners_in_all_four_combinations(self):
        for rhythm in (False, True):
            for feedback in (False, True):
                variant = copy.deepcopy(EXAMPLE)
                variant["rhythm"]["enabled"] = rhythm
                variant["feedback"]["enabled"] = feedback
                validate_fixture(variant)
                self.assertEqual(variant["clock_policy"], EXAMPLE["clock_policy"])
        self.assertIn("simulation_hitstop_seconds", EXAMPLE["rhythm"]["parameters"])
        self.assertIn("presentation_freeze_seconds", EXAMPLE["feedback"]["parameters"])
        # This checks ownership and shape, not actual engine timing invariance.

    def test_accessibility_and_native_status_cannot_be_claimed_by_toggle(self):
        variant = copy.deepcopy(EXAMPLE)
        variant["feedback"]["enabled"] = True
        self.assertEqual(variant["accessibility_overrides"], EXAMPLE["accessibility_overrides"])
        variant["verification"]["godot_native"] = "passed"
        with self.assertRaises(ValidationError):
            validate_fixture(variant)

    def test_invalid_types_ranges_owners_versions_and_clocks_are_rejected(self):
        changes = [
            (("response", "enabled"), "true"),
            (("response", "parameters", "deadzone_normalized"), 1.1),
            (("rhythm", "parameters", "startup_seconds"), -1),
            (("feedback", "parameters", "simulation_hitstop_seconds"), 0.1),
            (("forgiveness", "parameters", "auto_hit"), True),
            (("clock_policy", "input_expiry"), "unspecified"),
            (("schema_version",), "game-feel-four-switches/v2"),
            (("switch_policy",), "mid_action"),
            (("baseline_digest",), "unverified-but-looks-real"),
        ]
        for path, value in changes:
            with self.subTest(path=path):
                variant = copy.deepcopy(EXAMPLE)
                cursor = variant
                for key in path[:-1]:
                    cursor = cursor[key]
                cursor[path[-1]] = value
                with self.assertRaises(ValidationError):
                    validate_fixture(variant)

    def test_missing_required_switch_and_inverted_window_are_rejected(self):
        variant = copy.deepcopy(EXAMPLE)
        del variant["response"]
        with self.assertRaises(ValidationError):
            validate_fixture(variant)
        variant = copy.deepcopy(EXAMPLE)
        variant["rhythm"]["parameters"]["combo_open_seconds"] = 1.0
        with self.assertRaisesRegex(ValueError, "inverted"):
            validate_fixture(variant)

    def test_contract_links_are_local_and_resolve(self):
        import re
        document = SKILL / "references/game-feel-four-switches.md"
        for link in re.findall(r"\]\(([^)]+)\)", document.read_text()):
            path = (document.parent / link).resolve()
            path.relative_to(SKILL.resolve())
            self.assertTrue(path.is_file(), link)


if __name__ == "__main__":
    unittest.main()
