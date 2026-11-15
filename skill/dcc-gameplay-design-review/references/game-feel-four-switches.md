# Four independent game-feel switches

Status: design and data contract only. Native Godot, Unity, and Unreal input
validation and human playtests are **not_run**. Extend the existing playable
project and this review skill; do not create a replacement framework.

## Ownership and baseline

The four switches are response, rhythm, feedback, and forgiveness. Each has an
independent `enabled` flag and retained parameters. Disabled means use the
locked baseline behavior, not disable basic input or set every duration to zero.
The [example](../assets/game-feel.example.json) is synthetic, not recommended
values. The [schema](../assets/game-feel.schema.json) validates its data shape,
not engine behavior. Null digests mean unverified, never verified provenance.
Before a real trial, record exact build, baseline and effective configuration
hashes, input device, engine version, input sequence, initial state and clocks.

| Switch | Owns | Must not silently change |
| --- | --- | --- |
| response | Sampling/dispatch and deadzone normalization of current input | Input buffering or legal combo windows |
| rhythm | Startup, active and recovery phases; base legal combo window; simulation hitstop | Accessibility preferences |
| feedback | Audio/VFX/flash/shake and presentation-only freeze | Authoritative hit time, damage, collision or input eligibility |
| forgiveness | Buffering real input, grace and extension of the base combo window | Automatic input, automatic hits or collision reach |

Rhythm owns the base legal window. Forgiveness adds explicitly bounded grace;
never maintain a second competing base window. Consume buffered input at most
once; reject expired input. No input means no action; an out-of-range target
must not become a hit because forgiveness is enabled. Record units, valid
ranges, assumptions and player-facing effects. No universal timing values are
implied. Additional parameters require an explicit versioned contract change.

## Hitstop and time domains

Simulation hitstop belongs to rhythm. Presentation freeze belongs to feedback.
Both originate from one authoritative hit event ID, deduplicated per recipient.
Do not add both durations to the same clock. Pure presentation freeze cannot
freeze authoritative state, collision or the input state machine. If a binding
cannot separate presentation from simulation, report that feature unsupported;
do not substitute global time scale. Turning feedback off must leave the same
input sequence's logical hit times, damage and accepted combo results unchanged.

Declare whether input-buffer expiry and grace use input real time or simulation
time, including during hitstop. Feedback cannot change this clock choice. The
schema uses seconds for durations, normalized [0, 1] deadzone and feedback
intensity, simulation time for action phases, and presentation time for visual
freeze. Bindings must document the conversion to engine-native units.

## Switching and accessibility

Apply trial changes only at a reset boundary in this initial contract. Retain
disabled parameters for reproducible re-enabling. Mid-action live switching is
not supported until state/timer migration is separately specified. User flash
and shake opt-outs override trial configuration, including when feedback is on;
never re-enable them for an experiment. Record effective settings, not only the
requested configuration.

## Minimal validation in the existing scene

1. Validate configuration shape and explicit clock policy. Reject unknown fields,
   invalid ranges, unsupported versions and inverted base combo windows.
2. Lock one baseline and four variants, changing exactly one switch OR one
   parameter per comparison. For parameter A/B, keep that switch enabled in
   both trials; editing an inactive parameter cannot establish an effect. Compare
   the effective gameplay configuration, excluding trial IDs and evidence metadata.
   Keep build, device, initial state, seed, input sequence and other settings fixed. Reset between trials. An all-off baseline
   is valid but must still be playable.
3. In a native Godot run, log input event, action acceptance, startup completion,
   authoritative hit, recovery, buffer consumption and feedback event IDs with
   clock domains. Verify response dispatch and rhythm phase boundaries.
4. Compare feedback on/off: output may differ but authoritative hit time, damage
   and combo acceptance must not. Check flash/shake opt-outs independently.
5. Exercise forgiveness inside, at and outside each boundary, expiration, duplicate
   events, no input and out-of-range targets. Verify single consumption.
6. Separately test all four rhythm x feedback combinations for double hitstop,
   and input expiry during pause/hitstop. These are interaction tests, not
   single-variable A/B evidence. Include different frame rates and pause/resume.
7. Collect native human input/playtest notes. Automated native input traces can
   verify mechanics, not enjoyment. Video corroborates presentation only; it
   does not prove input latency, forgiveness or native control quality.

Godot is the first verification target. Unity and Unreal reuse the contract with
thin input/time/event mappings, but remain not_run until individually exercised.
Static schema/fixture tests do not establish any of these native results. Report
passed, failed, unsupported and not_run separately, with evidence locations.
