"""Schema and fake-clock tests; no native/runtime behavior claims."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'skill/dcc-gameplay-design-review/assets'
EXAMPLE = json.loads((ASSETS / 'impact.example.json').read_text())
SCHEMAS = {name: json.loads((ASSETS / (name + '.schema.json')).read_text())
           for name in ('hit-event', 'impact-profile')}
spec = importlib.util.spec_from_file_location('impact_lease_model', ROOT / 'tests/support/impact_lease_model.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def require_finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError('non-finite JSON number')
    if isinstance(value, dict):
        for item in value.values(): require_finite(item)
    elif isinstance(value, list):
        for item in value: require_finite(item)


def validate(name, value):
    require_finite(value)
    Draft202012Validator(SCHEMAS[name]).validate(value)


class ImpactContractTests(unittest.TestCase):
    def make(self):
        return model.LeaseModel('world-a', 'run-1')

    def acquire(self, ledger, event='hit-1', owner='actor-a', generation=1,
                duration=0.1, scale=0.0, incarnation='run-1', instance='world-a'):
        return ledger.acquire(event, owner, generation, duration, scale, instance, incarnation)

    def test_example_schemas_and_profiles(self):
        for schema in SCHEMAS.values():
            Draft202012Validator.check_schema(schema)
        validate('hit-event', EXAMPLE['event'])
        for profile in EXAMPLE['profiles']:
            validate('impact-profile', profile)
            self.assertEqual(profile['assets'], [])
        self.assertTrue(EXAMPLE['example_only'])
        self.assertEqual(set(EXAMPLE['native_status'].values()), {'not_run'})

    def test_event_profile_lock_matches_exact_canonical_fixture_bytes(self):
        profile = EXAMPLE['profiles'][0]
        data = json.dumps(profile, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=False, allow_nan=False).encode()
        self.assertEqual(EXAMPLE['event']['profile_version'], profile['version'])
        self.assertEqual(EXAMPLE['event']['profile_digest'],
                         'sha256:' + hashlib.sha256(data).hexdigest())
        changed = copy.deepcopy(profile); changed['camera_seconds'] += 0.01
        changed_data = json.dumps(changed, sort_keys=True, separators=(',', ':'),
                                  ensure_ascii=False, allow_nan=False).encode()
        self.assertNotEqual(EXAMPLE['event']['profile_digest'],
                            'sha256:' + hashlib.sha256(changed_data).hexdigest())

    def test_invalid_event_and_scope_semantics(self):
        for key, value in [('damage_applied', -1), ('authority', 'predicted'),
                           ('direction', [0, 0, 0]), ('direction', [float('nan'), 0, 0]), ('result', 'blocked')]:
            event = copy.deepcopy(EXAMPLE['event']); event[key] = value
            with self.subTest(key=key), self.assertRaises((ValidationError, ValueError)):
                validate('hit-event', event)
        profile = copy.deepcopy(EXAMPLE['profiles'][0]); profile['scope'] = 'presentation_only'
        with self.assertRaises(ValidationError): validate('impact-profile', profile)
        profile['simulation_hitstop_seconds'] = 0
        validate('impact-profile', profile)

    def test_unknown_unreviewed_asset_and_global_scope_rejected(self):
        profile = copy.deepcopy(EXAMPLE['profiles'][0])
        profile['assets'] = [{'asset_id': 'unknown'}]
        with self.assertRaises(ValidationError): validate('impact-profile', profile)
        profile['assets'] = []; profile['scope'] = 'global'
        with self.assertRaises(ValidationError): validate('impact-profile', profile)

    def test_overlapping_release_does_not_restore_one(self):
        ledger = self.make(); ledger.set_base(0.5)
        self.acquire(ledger, scale=0.0)
        self.acquire(ledger, event='hit-2', scale=0.4)
        ledger.release('hit-1', 'actor-a', 1, 'run-1')
        self.assertAlmostEqual(ledger.effective, 0.2)
        ledger.set_base(0.8)
        ledger.release('hit-2', 'actor-a', 1, 'run-1')
        self.assertEqual(ledger.effective, 0.8)
        self.assertFalse(ledger.release('hit-2', 'actor-a', 1, 'run-1'))

    def test_reverse_release_preserves_stronger_hold(self):
        ledger = self.make(); self.acquire(ledger)
        self.acquire(ledger, event='hit-2', scale=0.5)
        ledger.release('hit-2', 'actor-a', 1, 'run-1')
        self.assertEqual(ledger.effective, 0)

    def test_duplicate_event_does_not_extend_and_stays_seen_after_rearm(self):
        ledger = self.make(); self.acquire(ledger)
        ledger.advance(0.05)
        self.assertFalse(self.acquire(ledger, duration=0.2))
        ledger.advance(0.1); self.assertEqual(ledger.effective, 1)
        ledger.rearm(); self.assertFalse(self.acquire(ledger))

    def test_owner_cleanup_preserves_other_generation(self):
        ledger = self.make(); self.acquire(ledger)
        self.acquire(ledger, event='hit-2', generation=2, scale=0.5)
        ledger.cancel_owner('actor-a', 1)
        self.assertEqual(ledger.effective, 0.5)
        ledger.cancel_owner('actor-a', 2)
        self.assertEqual(ledger.effective, 1)

    def test_death_and_scene_close_reject_stale_work(self):
        ledger = self.make(); self.acquire(ledger)
        ledger.retire_owner('actor-a', 1)
        with self.assertRaises(ValueError): self.acquire(ledger, event='late-hit')
        self.acquire(ledger, event='new-generation', generation=2)
        self.assertFalse(ledger.release('new-generation', 'actor-a', 1, 'run-1'))
        ledger.close(); self.assertEqual(ledger.effective, 1)
        with self.assertRaises(ValueError): self.acquire(ledger, event='after-close', generation=2)

    def test_host_and_incarnation_isolation(self):
        ledger = self.make(); self.acquire(ledger)
        for kwargs in ({'instance': 'world-b'}, {'incarnation': 'run-2'}):
            with self.assertRaises(ValueError): self.acquire(ledger, **kwargs)
        replacement = model.LeaseModel('world-a', 'run-2')
        self.acquire(replacement, incarnation='run-2')
        self.assertFalse(replacement.release('hit-1', 'actor-a', 1, 'run-1'))
        self.assertEqual(replacement.effective, 0)
        self.assertEqual(ledger.effective, 0)

    def test_unscaled_expiry_does_not_unpause(self):
        ledger = self.make(); ledger.set_base(0.7, paused=True); self.acquire(ledger)
        ledger.advance(0.1)
        self.assertFalse(ledger.active); self.assertEqual(ledger.effective, 0)
        ledger.set_base(0.7, paused=False); self.assertEqual(ledger.effective, 0.7)

    def test_no_effect_request_does_not_start_hold_budget(self):
        for kwargs in ({'duration': 0}, {'scale': 1}):
            ledger = self.make()
            self.assertFalse(self.acquire(ledger, event='no-effect', **kwargs))
            self.assertIsNone(ledger.burst_start)
            ledger.advance(1)
            self.assertTrue(self.acquire(ledger, event='real-hit'))
            self.assertEqual(ledger.effective, 0)

    def test_continuous_budget_cannot_be_rearmed_by_incoming_hits(self):
        ledger = self.make(); self.acquire(ledger, duration=1)
        ledger.advance(0.15); self.acquire(ledger, event='hit-2', duration=1)
        with self.assertRaises(ValueError): ledger.rearm()
        ledger.advance(0.2); self.assertEqual(ledger.effective, 1)
        self.assertFalse(self.acquire(ledger, event='hit-3'))
        ledger.rearm(); self.assertTrue(self.acquire(ledger, event='hit-4'))

    def test_fps_and_long_frame_expire_on_first_observed_step(self):
        for fps in (30, 60, 120):
            ledger = self.make(); self.acquire(ledger, duration=0.05)
            ticks = 0
            while ledger.active:
                ticks += 1; ledger.advance(ticks / fps)
            self.assertGreaterEqual(ledger.now, 0.05)
            self.assertLess(ledger.now, 0.05 + 1 / fps + 1e-10)
        ledger = self.make(); self.acquire(ledger); ledger.advance(2)
        self.assertEqual(ledger.effective, 1)

    def test_clock_validation_and_dedup_capacity_fail_closed(self):
        ledger = self.make()
        for value in (float('nan'), float('inf'), -1, True):
            with self.assertRaises(ValueError): ledger.advance(value)
        ledger.advance(1)
        with self.assertRaises(ValueError): ledger.advance(0)
        ledger = model.LeaseModel('world-a', 'run-1', capacity=1)
        self.acquire(ledger)
        with self.assertRaises(ValueError): self.acquire(ledger, event='hit-2')
        self.assertEqual(len(ledger.seen), 1)


if __name__ == '__main__': unittest.main()
