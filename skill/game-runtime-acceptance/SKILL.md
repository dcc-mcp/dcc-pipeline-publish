---
name: game-runtime-acceptance
description: Cross-engine acceptance for prebuilt Unity, Unreal, and Godot games using bounded launches, structured runtime events, performance thresholds, and hash-bearing evidence.
license: MIT
compatibility: "dcc-mcp-core 0.19.64+, Python 3.9+, Windows game builds"
metadata:
  dcc-mcp:
    dcc: python
    layer: domain
    stage: validation
    version: "0.1.0"
    tags: [game, runtime, acceptance, validation, evidence, unity, unreal, godot]
    search-hint: "launch or validate a built Unity Unreal or Godot game, verify runtime events performance victory bosses logs and evidence"
    tools: tools.yaml
---

# Game Runtime Acceptance

Use this skill after an engine adapter has produced a complete Windows game
directory and before distribution packaging. It owns runtime acceptance, not
engine builds, UI input, video capture, installation, signing, or store upload.

Use `run_game_runtime_acceptance` to launch the exact `.exe` inside the supplied
build directory without a shell. The tool writes a request-specific log and
JSON report outside that build, evaluates structured `event=<name>` records,
fixed required/forbidden markers, and numeric metric thresholds, then returns
the launched PID. Keep `leave_running_on_success=true` when a scoped
`ui_control` screenshot or game-owned exit action must follow.

Use `validate_game_runtime_log` for an already completed log. It never launches
or controls an application and returns the same structured acceptance report.

Read `references/WORKFLOW.md` before defining event rules. Do not convert a
policy denial, missing UI evidence, unsigned installer, or absent store approval
into a runtime pass.
