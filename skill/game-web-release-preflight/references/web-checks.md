# Browser export checks

## Local package inspection

Identify the exported artifact, not the engine source project. Work on a copy
only when packaging is requested. Inventory relative paths, sizes, and hashes;
flag symlinks, private files, credentials, unexpected sources, and missing
notices before any future upload. Do not silently strip files from the original.

For itch.io, index.html must be in the archive's served root. Local references
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

Sources checked 2026-10-24:
- https://itch.io/docs/creators/html5
- https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html
- https://itch.io/docs/creators/quality-guidelines
