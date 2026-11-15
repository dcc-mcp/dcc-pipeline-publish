"""Deterministic test oracle. Never imports an engine or modifies a runtime clock.

Adapters implement this lifecycle in their existing local dispatch mechanisms.
This model deliberately does not handle networking, physics or visual effects.
"""
import math


class LeaseModel:
    def __init__(self, instance, incarnation, max_continuous=0.2, capacity=1024):
        self.instance = instance
        self.incarnation = incarnation
        self.max_continuous = self._number(max_continuous, positive=True)
        self.capacity = capacity
        self.now = 0.0
        self.base = 1.0
        self.paused = False
        self.active = {}
        self.seen = set()
        self.retired = set()
        self.closed = False
        self.burst_start = None

    @staticmethod
    def _number(value, positive=False):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('finite nonnegative number required')
        if not math.isfinite(value) or value < 0 or (positive and value == 0):
            raise ValueError('finite nonnegative number required')
        return value

    def advance(self, unscaled_now):
        unscaled_now = self._number(unscaled_now)
        if unscaled_now < self.now:
            raise ValueError('clock cannot move backward')
        self.now = unscaled_now
        self.active = {key: value for key, value in self.active.items()
                       if value['deadline'] > self.now}
        # Burst budget remains until reset/rearm, preventing a stream of hits
        # from immediately reacquiring after the cap in the same action window.

    def acquire(self, event, owner, generation, duration, scale,
                instance, incarnation):
        if self.closed or (owner, generation) in self.retired:
            raise ValueError('scope closed or owner generation retired')
        if (instance, incarnation) != (self.instance, self.incarnation):
            raise ValueError('wrong host lifecycle')
        duration = self._number(duration)
        scale = self._number(scale)
        if scale > 1:
            raise ValueError('impact scale must be <= 1')
        key = (event, owner, generation)
        if key in self.seen:
            return False
        if len(self.seen) >= self.capacity:
            raise ValueError('dedup capacity reached; start a new bounded trial')
        self.seen.add(key)
        if duration == 0 or scale == 1:
            return False
        if self.burst_start is None:
            self.burst_start = self.now
        deadline = min(self.now + duration, self.burst_start + self.max_continuous)
        if deadline <= self.now:
            return False
        self.active[key] = {'deadline': deadline, 'scale': scale}
        return True

    def release(self, event, owner, generation, incarnation):
        if incarnation != self.incarnation:
            return False
        return self.active.pop((event, owner, generation), None) is not None

    def cancel_owner(self, owner, generation):
        self.active = {key: value for key, value in self.active.items()
                       if key[1:] != (owner, generation)}

    def retire_owner(self, owner, generation):
        self.cancel_owner(owner, generation)
        self.retired.add((owner, generation))

    def close(self):
        self.active.clear()
        self.closed = True

    def rearm(self):
        if self.active:
            raise ValueError('cannot rearm an active impact window')
        self.burst_start = None
        # Do not erase dedup tombstones: a replay must not become a new hit.

    def set_base(self, scale, paused=False):
        self.base = self._number(scale)
        self.paused = paused

    @property
    def effective(self):
        if self.paused:
            return 0.0
        return self.base * min((v['scale'] for v in self.active.values()), default=1.0)
