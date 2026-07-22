---
name: game-pv-capture
description: Plan, record, verify, and preserve exact-window gameplay shots for a game PV through canonical DCC-MCP UI Control without whole-desktop or title-matched recorder fallbacks.
license: MIT
compatibility: "dcc-mcp-core 0.19.65+ with exact_window_recording, Python 3.9+, Windows game players"
metadata:
  dcc-mcp:
    dcc: python
    layer: domain
    stage: capture
    version: "0.1.0"
    tags: [game, pv, trailer, capture, recording, evidence, unity, unreal, godot]
    search-hint: "record a real Unity Unreal or Godot gameplay PV trailer shot with exact window ui-control manifests and frame hashes"
    tools: tools.yaml
---

# Game PV Capture

Use this Skill after the exact game build has passed runtime acceptance and
before HyperFrames editing. It owns shot planning, exact-window recording
provenance, frame verification, and preservation. It does not build or launch
the game, inject input, record audio, edit a timeline, synthesize gameplay,
encode the final PV, or publish media.

Read `references/WORKFLOW.md` before capturing. Select the DCC `instance_id`
first, then keep one logical `session_id` within that adapter connection. Two
game instances may reuse the same logical session name because Core isolates
connections; the plan still pins the exact PID and HWND for every shot.

Use `create_game_pv_capture_plan` with a request UUID, evidence root, exact
route/target, and bounded shot list. For each returned shot, call canonical
`ui_control__record_clip` through the specified `instance_id` with the returned
arguments. Do not alter the route or substitute a title-only, whole-desktop,
FFmpeg desktop, OBS, platform Computer Use, or mock recording path.

Pass every returned `manifest_path` to `finalize_game_pv_capture`. It validates
target identity, encoding, expected frame count, JPEG boundaries, timestamps,
every frame hash, and minimum unique-frame evidence before atomically copying
the sequence into request-scoped evidence. Inspect the returned first/middle/
last poster frames visually. Then hand only those verified sequences to
HyperFrames for composition, licensed/original audio, titles, transitions, and
final decode validation.

If UI Control returns `desktop_unavailable`, pause and wait for the user to
unlock or reconnect. If it returns target replacement, size change, stale
capability, cancellation, or partial capture, discard that shot and reacquire a
fresh observation on the same intended instance. Never weaken the manifest or
motion thresholds to turn a failed capture into a pass.
