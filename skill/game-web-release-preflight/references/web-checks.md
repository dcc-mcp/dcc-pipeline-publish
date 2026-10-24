# Browser export checks

## Local package inspection

Identify the exported artifact, not the engine source project. Work on a copy
only when packaging is requested. Inventory relative paths, sizes, and hashes;
flag symlinks, private files, credentials, unexpected sources, and missing
notices before any future upload. Do not silently strip files from the original.

For itch.io ZIP uploads, index.html must be in the archive's served root.
A standalone self-contained HTML upload does not require that filename. Local references
must have exact case and resolve relative to the project; leading-slash paths
can break when hosted under a subdirectory. Inventory external domains and
mixed-content URLs. Static reference checks cannot resolve all dynamically
constructed URLs; verify actual browser requests separately.

As checked on 2026-10-24, itch.io's documented default HTML5 limits are 1,000
extracted files, 500 MB total extracted content, 200 MB per extracted file,
and 240 characters for filenames including paths. Record measured values and
check the current documentation at release time; these are platform defaults,
not universal engine limits. Do not increase limits or imply exemptions.

## Browser acceptance evidence

Record exact browser/device, export version/hash, tested URL or local server,
and whether the result is local or hosted. Test loading, runtime console/network
errors, gameplay goal and failure/restart, audio after a user gesture, viewport
resize/orientation, keyboard/mouse focus, fullscreen, and touch if advertised.
Do not enable a mobile-friendly claim based on a desktop screenshot. Measure
startup and peak memory on intended devices where tools permit; otherwise list
these as not tested. Do not download large tooling to satisfy this guide.

Use a disposable browser profile and test saves for storage-failure or clearing
tests; never erase a real player's saved progress. Test persistence by saving,
refreshing, closing/reopening, and observing actual restored state. Include denied/cleared storage and private browsing behavior.
Browser/iframe storage is not guaranteed cloud save. Verify a fallback that
explains loss of persistence rather than falsely promising durable progress.

For Godot 4, confirm the precise version's Web support: current stable guidance
requires Compatibility/WebGL 2 and does not support C# Web exports. Export as
index.html from the engine instead of renaming related generated files later.
Single-threaded export avoids the multi-threaded cross-origin-isolation
requirements. Threaded builds need secure context and appropriate COOP/COEP;
verify the actual host supports these, not just a local server. Godot user://
persistence uses browser storage and can fail in iframe/private contexts.

## Rights, privacy, and handoff

Inspect third-party assets, fonts, audio, SDKs, telemetry, external services,
and notices. Record redistribution permissions, required credits, data flows,
consent behavior, and unresolved restrictions. AI-generated assets are not
inherently CC0. A hosting account's terms do not license the game's assets.

Keep the build private until a distinct upload/publication authorization states
the target account/project, exact artifact/version, audience/visibility, and
purpose. Separate upload, preview, review submission, and publication states.
A valid archive is not evidence of successful publication or store acceptance.

## Actionable manual handoff

When automation is unavailable or not authorized, provide a concise handoff:
- Current state: local preparation, preview, uploaded, review submitted, or live.
  State which are verified; a platform preview can already involve uploading.
- Official entry: verified documentation or the exact authorized project page.
  Do not invent dashboard URLs, button labels, or an unobserved UI sequence.
- Operator: the account owner or an existing authorized role, not an invented
  administrator. Explain why this step needs them (identity, agreement, payment,
  access, review choice, or unavailable capability).
- Materials: categories and the exact approved build/version, listing copy,
  screenshots, license notices, and privacy disclosures needed. Enter identity
  documents, tax details, signing keys and credentials only on the verified
  official platform or approved secure flow, never back in chat or a repository.
- Smallest step: one bounded action and intended audience, separating upload,
  review submission and public release; do not imply authorization for all three.
- Completion evidence: a nonsensitive status label, build/version ID, or shareable
  project URL. If a screenshot is necessary, ask to redact private information.
  Never ask for a secret or identity-document image to establish completion.
- Resume: name the next read-only verification or preparation step. A reported
  upload is not proof of live availability; check the actual state when access
  is authorized. Never promise review approval or a guaranteed release date.

Example: itch.io handoff after local package checks

"The local HTML5 package is prepared; nothing has been uploaded or published.
The account owner can start from itch.io's official HTML5 upload guide below
and select their intended existing project. Have the reviewed ZIP/build hash,
listing materials and notices ready. This needs the owner because project
access and audience choices are not yet verified. If uploading is authorized,
upload only that build after verifying Draft visibility and who has access;
do not make the page public as part of the upload. Verify the current controls
rather than assuming a button sequence. Report only the nonsensitive project
URL and uploaded build/version status. I can then verify preview loading,
input and save behavior within the authorized access, before asking separately
about a public release."

Verify itch.io's current visibility modes: Draft, Restricted, and Public.
Draft access can include editors and secret-link holders; Restricted access
can include approved viewers. Public with Unlisted in search & browse is still
public, and disabling new downloads does not hide the page. Verify page access
and file access separately. Do not request access secrets as evidence.

An upload to an already-public project/channel may make the build immediately
available. Upload and publication are distinct states, but can coincide on that
destination; verify visibility before any separately authorized upload, rather
than assuming every upload is staged or private.

If the user cannot access the official project or the expected visibility
control is absent, stop the upload step and help identify the account/capability
gap without switching projects or publishing as a workaround. Other stores
need their own official process; do not apply itch.io steps to Steam or mobile.

Sources checked 2026-10-24:
- https://itch.io/docs/creators/html5
- https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html
- https://itch.io/docs/creators/quality-guidelines

- https://itch.io/docs/creators/access-control
- https://itch.io/docs/butler/pushing.html
