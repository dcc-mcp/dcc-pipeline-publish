# Evidence and reusable assets

## Evidence ledger

For each meaningful claim record: claim ID, status (observed, inferred,
unmeasured), build/version, method, relevant inputs/seeds, artifact location,
and limitations. Link actual logs, frames, or player notes; never invent them.
A screenshot establishes visible appearance at that moment, not controls,
progression, save reliability, or balance. Static tests and bots do not prove
human enjoyment. Report “real engine playtest not performed” when appropriate.

Review style consistency, legibility, feedback, pacing, performance, audio,
and recovery only to the extent the current milestone and evidence support.
Agree on the next useful check rather than installing a universal quality gate.

## Select, verify, lock

Inspect existing project assets and available DCC-MCP asset-source/provider
capabilities before making new assets. Provider availability and downloadability
are not permission to redistribute. Record license and attribution per asset,
including dependencies such as textures, fonts, audio, and rig components.

Keep two layers:
- Private source records: immutable source files/versions, generation records,
  author/provider/model version, input rights, terms URL and dated evidence,
  creation date and approved cost without credentials, and dependencies.
- Optional public index: only authorized fields and files whose publication and
  redistribution rights were separately verified. Do not export private paths,
  private prompts, account identifiers, or secrets. A preview needs its own
  rights check. Unknown rights remain private, even for AI-generated content.

Use asset_id + version + SHA-256 in the project's lock list. Deduplicate matching
bytes without discarding distinct provenance or licenses; never overwrite a
locked version. Record modified derivatives and dependency locks separately.
Do not write fabricated hashes: null means unverified in the example sidecar,
and cannot become a production file record or a verified project lock.

Record UV/PBR conventions, rig and named actions, scale/axes, LODs, collision,
preview, and engine import validation for the exact file hashes and engine
version. Mark each not-tested or not-applicable instead of implying success.
Use the repository's existing pipeline-publish manifest for actual exported
files and hash verification; this optional sidecar supplements it, not replaces
its schema or changes its runtime behavior.

AI generation is not automatically CC0. Commercial use, copyright ownership,
and redistribution are different questions. Verify the service/model terms
applicable on the generation date and input rights before reuse. Original RTS
units/buildings may share a genre, not copied Warcraft characters, logos, or
assets. Paid generation requires the appropriate approval, not just this brief.

## Downstream ownership

Engine adapters own implementation and builds. Existing runtime acceptance
owns runtime evidence; existing game PV capture owns exact-window provenance;
HyperFrames owns the subsequent edit. If a required adapter is absent, report
that capability gap and preserve the brief rather than installing or claiming
completion. A CUA fallback cannot weaken these contracts.
