---
name: dcc-gameplay-design-review
description: Review a game's core loop, mechanics, numerical assumptions, and asset dependencies into a bounded implementation and playtest brief. Use before or between playable iterations, not for engine operation, runtime acceptance, video capture, or publishing.
license: MIT
metadata:
  version: "0.1.1"
---

# Gameplay Design Review

Produce the smallest review that changes the next playable iteration. Preserve
its intended genre, audience, engine, milestone, and existing work. Inspect the
current design, build evidence, asset inventory, and unresolved feedback first;
do not replace a working vertical slice with a new framework or exhaustive GDD.

Read [the gameplay contract](references/gameplay-contract.md) when specifying
rules or numerical changes. Read [evidence and assets](references/evidence-and-assets.md)
when evaluating results, selecting resources, or preparing a handoff. For response, rhythm, feedback, or forgiveness tuning, read
[the four-switch contract](references/game-feel-four-switches.md). Its data
fixtures are not a runtime implementation or native playtest result. For hit
events, impact profiles and safe hitstop recovery, read
[the impact contract](references/impact-contract.md). Record
assumptions separately from user decisions and measured findings. Infer
reversible defaults; ask only when a missing answer changes scope or authority.

Deliver a concise brief with the experience goal, playable loop, a bounded
change, numeric assumptions, asset locks, and the cheapest meaningful test.
Include the build/version, evidence locations, unresolved risks, and a next
milestone within the existing time and cost budget. A design review is not
proof of fun, balanced progression, or a working build. If no real playtest was
observed, say so; do not turn simulated or static checks into player evidence.

Discover existing assets and capabilities before requesting new production.
Keep this skill platform-neutral: implementation belongs to the available
engine/DCC adapter, using discovered typed MCP tools. Scoped CUA is an optional
fallback for a genuine capability gap, never a way around denied access or a
more restrictive capture contract. Do not install tools, spend money, publish,
or change the runtime merely because the brief recommends doing so.

For later delivery, the existing `game-runtime-acceptance` and
`game-pv-capture` currently declare Windows-build support. Hand the exact
Windows build to runtime acceptance, then use PV capture and its HyperFrames
handoff. Other platforms need an appropriate acceptance/capture adapter; this
design skill being platform-neutral does not make those implementations
cross-platform. Locate capabilities in the target environment rather than
assuming installation. This review neither duplicates nor relaxes them.

The example [asset sidecar](assets/asset-sidecar.example.json) is deliberately
private and unverified. It is not a real asset, a license grant, or a production
manifest. Use optional sidecars alongside existing publish manifests rather
than adding a mandatory runtime gate.
