# Bounded gameplay contract

Start from the current project, not a genre template. Keep only sections that
change implementation or the next test; explicitly omit irrelevant systems.

## Brief and iteration

Record the experience goal, audience, platform/input, engine/build version,
current milestone, excluded work, available time, and approved spending limit.
Separate long-term ambitions from this iteration's playable acceptance scene.
Keep the existing style reference and asset budget visible to implementation.

For each changed mechanic, specify:
- Player intent and input; observable starting state and eligibility.
- State transition, timing, resource cost, and cancellation/interruption.
- Feedback, counterplay, success/failure, recovery, and save/restart behavior.
- Its relationship to the core loop and one likely exploit or dominant choice.

For each relevant numeric variable, record its unit, formula, initial value or
range, source/assumption, and intended player-facing effect. For example,
seconds to defeat an enemy depends on actual hit rate and cooldown behavior,
not just damage divided by health. Describe probability models explicitly;
expected loot is not a guarantee for an individual playthrough. Check boundary
values, resource sources/sinks, and progression bottlenecks before tuning.
Do not introduce combat, loot, monetization, or multiplayer by template.

## Test proposal

Choose a test that could falsify the weakest important assumption. Name the
scene/build, inputs, observable events, comparison, budget, and decision that
its result would change. Define success/failure criteria before collecting
results. Use numeric thresholds only where supported by the project's goal;
there is no universal balance ratio or mandatory repair count.

When simulation is available, compare policies with the same seeds, tick rate,
initial state, duration, and search budget. Label hidden-state/oracle,
precise-visible-state, and human-limited agents separately. Verify the harness
actually engages the intended mechanics before interpreting its score. If
runs are not deterministic, record repeated runs and spread, not a single
lucky run or an invented confidence claim.

Difficulty and pacing conclusions require real-player observations or a
clearly described, calibrated human-limited model; disclose model limitations.
Do not silently change the game to satisfy a test agent. When evidence is
missing, propose the smallest probe instead of declaring a pass or blocking
unrelated implementation.

## Handoff

Return: proposed change; expected effect; evidence and counter-evidence;
implementation risks; smallest playable test; asset locks; remaining unknowns.
Preserve immutable replays against their original rules/build. After a rule
change, collect new evidence rather than relabeling old results.
