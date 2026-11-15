# Exact-window game PV capture workflow

## Ownership and prerequisites

1. Build the game with its Unity, Unreal, or Godot adapter.
2. Pass `game-runtime-acceptance` against that exact executable.
3. Query DCC-MCP inventory and select the intended `instance_id`.
4. Bind canonical `ui-control` to the accepted process and exact HWND.
5. Capture and finalize shots with this Skill.
6. Edit the verified sequences with HyperFrames.

The engine adapter owns build/runtime state. Core UI Control owns target
selection, desktop safety, input policy, and WGC recording. This Skill owns
shot provenance and immutable evidence. HyperFrames owns editorial output.

## Shot design

Prefer several bounded 3-12 second shots over one long undifferentiated
recording. A useful survivor-game plan usually includes live combat, an upgrade
choice, a boss/evolution beat, and a victory/result beat. Set
`minimum_unique_frames=1` only for an intentionally static title or result
card; gameplay should require multiple unique frames.

The aggregate plan is capped at 21,600 frames. Each Core clip is capped at 180
seconds, 60 FPS, and the exact capability-bound window. Recording has no audio.

## Two-level session routing

`instance_id` selects an adapter/DCC instance. `session_id` is logical only
inside that adapter connection. Core internally namespaces the pair, so two
instances can both use `session_id="pv"`. Keep the exact plan route for every
call; do not rediscover a window by title between shots.

Multiple sessions may remain active. Native input is still serialized by the
Core Host, and the global emergency interrupt stops all active sessions.
Stopping one planned session must not be treated as permission to address a
different instance.

## Failure rules

- `desktop_unavailable`: pause; no polling, injection, or alternate recorder.
- stale observation/capability: reacquire on the same exact instance and HWND.
- target replacement or resolution change: reject the incomplete artifact.
- hash, byte length, frame count, timestamp, or JPEG mismatch: fail the shot.
- insufficient unique frames: capture real motion; do not duplicate stills.
- missing audio: add licensed/original audio during HyperFrames editing; never
  claim Core window recording captured it.

The final report proves which window frames entered editorial. It does not
prove gameplay milestones, audio rights, final layout quality, encoding,
installation, signing, malware status, or store publication.
