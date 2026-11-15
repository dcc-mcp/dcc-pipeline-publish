# Shared hit-event and impact contract

Use this with the [four-switch contract](game-feel-four-switches.md), not a
second gameplay framework. This increment supplies schemas, synthetic examples
and a deterministic test oracle, **not an engine implementation**. Native Godot,
Unity, Unreal and human-input evidence remain `not_run`. Only six described
effect groups were supplied; no complete twelve-effect video was inspected.

## Authority and dispatch

Resolve eligibility, collision, damage and gameplay state once in the engine.
Publish an immutable [HitEvent](../assets/hit-event.schema.json) after confirmation.
Its identity includes world/host incarnation, attack instance, hit index and a
unique event ID; entity generations distinguish destroyed/reused objects.
Position/direction use the declared world space; bindings specify axis and unit
conversion. Damage is the amount actually applied, not a second damage command.
`blocked` and `immune` results require zero applied damage; fatal requires `hit`.
Direction must be finite and nonzero; normalize it in the binding before use.

The v1 contract accepts confirmed events only. Predicted presentation and
rollback reconciliation need a separate versioned contract; do not route an
unconfirmed event into authoritative damage or combo scoring. Multiple targets
in one attack have distinct event IDs. Deduplicate per event, recipient and
channel, not merely attack ID. An expired effect does not erase its dedup record.

Schedule local effects from the same confirmed event time. Do not wait for
hitstop to finish before emitting every VFX/SFX. Each channel specifies whether
it begins immediately or after the hold. Logical knockback and combo eligibility
belong to gameplay/rhythm; visual motion and combo display belong to feedback.
Turning feedback off cannot change authoritative hit times, damage, collision,
knockback, accepted input or combo count. Rhythm's simulation hold can change
subsequent simulation timing and must be tested separately.

## Profiles and safe time recovery

Events pin profile ID, version and a SHA-256 digest; reject a mismatched resolved
profile rather than silently using latest. For this v1 fixture protocol, hash UTF-8
JSON with sorted keys, compact separators, no ASCII escaping and no non-finite
numbers (no trailing newline). Preserve the serialized numeric representation
when transferring a profile; this is not a general cross-language canonical JSON
claim. Production exports must distribute these exact locked canonical bytes.

An [ImpactProfile](../assets/impact-profile.schema.json) identifies versioned
parameters and reviewed assets. The [three examples](../assets/impact.example.json)
use the user's 60-reference-fps tuning starts: melee 1--6 reference frames,
ranged up to 2, camera 0.05--0.2 seconds. These are hypotheses, not universal
standards. Store seconds; never count rendered frames at the current FPS.
The example intensities and maximum hold budget are synthetic trial choices.

The minimal contract supports `local_actor` and `presentation_only`, not global
or multiplayer simulation dilation. Zero requested scale means an abstract local
state hold, **not an instruction to set any engine's global time scale to zero**.
`presentation_only` requires simulation_hitstop_seconds=0. Feedback disablement
removes only presentation freeze, not the independent rhythm hold. Bindings that
cannot isolate presentation must report unsupported rather than alter gameplay.

Use a local coordinator per world incarnation and explicit affected object/set.
Tokens carry event ID, owning object/generation, scope, requested multiplier and
an unscaled deadline. For the chosen `strongest_active` policy, apply the minimum
active multiplier to the current base policy; do not sum hold durations. Releasing
one token recomputes the remainder; never blindly restore scale to 1 or restore
an old snapshot over a newer slow-motion policy. User pause is a separate policy
and remains active after all hitstop tokens expire.

Bound continuous hold by a configured budget. The test oracle requires an explicit
rearm at a safe action/reset boundary after all tokens end; an incoming hit must
not rearm its own budget. Replays remain deduplicated after rearm. Bound the trial's
event ledger: capacity exhaustion fails visibly, never silently evicts tombstones
and permits old hits to replay. Production bindings may use proven bounded replay
windows instead, with equivalent no-duplicate guarantees.

Expiry uses monotonic unscaled time on a coordinator that survives the recipient.
The timer/tick used to release a hold must continue when the held actor stops.
Completion, interruption, death, disable and destruction cancel owned tokens;
scene teardown disposes the coordinator. Old-incarnation callbacks cannot affect
a replacement world. Do not cancel another owner's tokens when one object dies.
Duplicate release is harmless. Pause does not stop token expiry but remains a
separate gate on effective simulation time. Input-buffer/grace clock policy stays
as specified by the four-switch contract, not inferred from feedback settings.

`tests/support/impact_lease_model.py` is a fake-clock acceptance oracle, not a
runtime package. Engine adapters retain their existing dispatch and main-thread
rules. MCP prepares profiles, starts bounded tests and reads results; it never
runs the per-frame impact loop. A local model's passing tests do not establish
physics, input latency, networking or presentation behavior.

## Godot-first handoff and other bindings

Continue dcc-mcp-godot #98's existing asset-free roguelike scene, not a new starter.
Pin engine, adapter, Core and build hashes. Map local actor holds and presentation
holds separately, record effective values and clock domains. Use unscaled expiry
outside the frozen actor; test lifecycle cleanup and primitive VFX/SFX first.

- Godot: [SceneTree timer](https://docs.godotengine.org/en/stable/classes/class_scenetree.html#class-scenetree-method-create-timer)
  exposes ignore_time_scale and process_always. Choose pause semantics explicitly.
  [Engine.time_scale](https://docs.godotengine.org/en/stable/classes/class_engine.html#class-engine-property-time-scale)
  affects delta-based simulation, recommends values above zero and does not scale audio.
- Unity: [timeScale](https://docs.unity.com/en-us/engine/6000.0/script-reference/unityengine/time/timescale)
  at zero stops FixedUpdate and WaitForSeconds progress. Use a surviving coordinator
  and [unscaled waits](https://docs.unity.com/en-us/engine/6000.0/script-reference/unityengine/waitforsecondsrealtime),
  not a scaled timer to undo the hold.
- Unreal: [SetTimeDilation](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/AWorldSettings/SetTimeDilation)
  can clamp; inspect actual values. [FGameTime](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/FGameTime)
  distinguishes real time from paused/dilated world time. Global dilation is not
  the local-actor mapping and is outside this MVP.

These references explain API boundaries, not tested compatibility. Unity/Unreal
bindings are future work. Multiplayer may use local cosmetic feedback only until
server authority/prediction is explicitly qualified. Never share mutable holds
between DCC instances or use client-global slow motion to change server gameplay.

## Acceptance and assets

Keep baseline and one-variable variants for response/rhythm/feedback/forgiveness.
Exercise light melee, heavy melee and ranged with native input. Log event IDs,
input acceptance, authoritative hit/damage, logical knockback, hold acquisition,
release reason, effective scale and clock domains. Compare 30/60/120 FPS plus a
long-frame case; timer completion is quantized to the next actual processing step,
not guaranteed sub-frame accuracy. Separately test rhythm x feedback combinations.

Required lifecycle cases: overlapping hits, duplicate events, multi-target attack,
reverse release order, interrupt/death, scene reset, stale incarnation/generation,
existing slow motion changing during a hold, user pause and continuous-hit cap.
Showcase A/B video supplements native input traces and human notes; it cannot
prove input responsiveness or gameplay timing. Record static/fixture/native/manual
results separately and preserve existing Windows runtime/PV support boundaries.

Examples use no third-party assets. Optional replacements must carry source,
version/hash, license evidence, redistribution decision and reviewed-data status;
unknown rights or unreviewed executable content block replacement, not primitive
playability. Schema-shaped rights strings are not legal verification. Reuse existing
asset sidecars/providers. Do not mirror third-party bundles or interpret free/CC0
as script safety. Shared contract publication and marketplace registration remain
separate from this partial implementation of pipeline #17 / marketplace #82/#83.
