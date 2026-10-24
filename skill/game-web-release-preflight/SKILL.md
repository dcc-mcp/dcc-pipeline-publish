---
name: game-web-release-preflight
description: Prepare an existing browser game export for a reviewed Web distribution handoff, including itch.io packaging and mini-game platform routing. Use before uploading a build; does not convert engines, upload, submit for review, publish, or create credentials.
license: MIT
metadata:
  version: "0.1.0"
---

# Web Release Preflight

Prepare a local release-readiness report for an existing Web export. Record the
engine/version, export settings, exact build hash/inventory, intended audience,
and target platform. Do not replace working games or assume an export exists.
If export is missing, hand that gap to the engine adapter instead of claiming
release readiness. Inspect existing capabilities before requesting new tools.

Read [Web checks](references/web-checks.md) for browser exports and
[platform routing](references/platform-routing.md) before choosing a destination.
Keep measured package facts, user declarations, observed browser results, and
unknowns separate. The [handoff example](assets/handoff.example.json) is a
private, untested template, not proof of acceptance or permission to upload.

Prefer the existing game's supported Web target for the first reusable slice.
An HTML5 export, especially Godot Web, is not a WeChat or Douyin mini-game
package. Those routes require their actual engine/platform adapter and device
verification. Do not rename HTML files or add game.json to pretend conversion.

Produce a short report: package findings, browser/input/storage evidence,
asset-license and privacy questions, account/review prerequisites, known costs
and unknown fees, and the next explicitly bounded action. Missing evidence
means not tested, not passed. Avoid turning this guidance into a runtime gate.

This skill is preparation only. Do not upload even a private preview, submit
for platform review, publicly publish, create accounts, accept agreements,
generate/configure credentials, or pay fees. Those are separate authorized
steps. Never put secrets into a command example or report. A platform preview
command may transmit the build; check its semantics before proposing it.

Reuse `pipeline-publish` for file hash manifests when available. Existing
`game-release-package` owns Windows distribution; `game-runtime-acceptance`
and `game-pv-capture` currently declare Windows-build support. Browser testing
needs its own evidence and is not satisfied by those Windows results. Keep
marketing capture/editing separate; do not synthesize gameplay evidence.
