# Cross-engine game runtime acceptance

## Ownership boundary

1. Build through the Unity, Unreal, or Godot adapter.
2. Run this Skill against the exported executable and structured player log.
3. Bind canonical `ui-control` to the returned exact PID/HWND for visual proof
   or a game-owned exit action. UI Control policy remains authoritative.
4. Package only the accepted build with `game-release-package`.

This Skill does not invoke an editor, modify project files, inject input, record
the desktop, install a package, sign code, scan for malware, or publish to a
store account.

## Structured log contract

Emit line-oriented records containing `event=<name>` and whitespace-separated
`key=value` fields. Values containing whitespace should be quoted. A project
prefix such as `[MY_GAME]` may be required with `event_prefix`.

Use:

- `completion_event` for the terminal success record and its exact fields;
- `required_events` for milestone counts such as boss spawns and chests;
- `required_markers` for immutable build or asset identity text;
- `forbidden_markers` for crash, assertion, or known failure text;
- `metrics` for per-sample numeric bounds such as minimum FPS or maximum memory.

Rules are structured data, not regular expressions. This keeps evaluation
bounded and avoids project-owned executable scripts as the acceptance oracle.

## Launch behavior

`engine` controls only the log argument added to the exact executable:

- `unity`: `-logFile <request-log>`
- `unreal`: `-log -abslog=<request-log>`
- `godot`: `--log-file <request-log>`
- `custom_stdout`: capture stdout/stderr to the request log

Arguments are passed as an array with no shell expansion. The working directory
is always the declared build root. Evidence is written under
`<evidence_directory>/<request_id>`; an existing request directory is rejected.

On success, leaving the game open is explicit and the returned PID becomes the
only valid target for subsequent visual evidence. On timeout, cancellation, or
acceptance failure, the launched process tree is terminated.

## Evidence limits

- Runtime logs are capped at 64 MiB.
- Rule collections and individual markers are bounded by the typed schema.
- Reports include executable and log SHA-256 values, matched event counts,
  metric summaries, process state, and every failure reason.
- A report proves only the declared runtime contract. Installer integrity,
  signing, antivirus scanning, visual quality, and store submission are
  separate gates.
