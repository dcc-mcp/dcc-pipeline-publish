---
name: game-release-package
description: Cross-engine Windows game release packaging for prebuilt Unreal, Unity, and Godot exports, including installers, SteamPipe preview scripts, and WeGame submission preflight records.
license: MIT
compatibility: "dcc-mcp-core 0.19+, Python 3.9+, Windows installer builds require Inno Setup 6"
metadata:
  dcc-mcp:
    dcc: python
    layer: domain
    stage: pipeline
    version: "0.2.0"
    tags: [game, release, package, installer, steam, wegame, unreal, unity, godot]
    search-hint: "package or distribute a built Unreal Unity or Godot game, create Windows installer, prepare SteamPipe or WeGame release"
    tools: tools.yaml
---

# Game Release Package

Use this skill after an engine-specific tool has exported a complete Windows
game directory. It does not cook, compile, or modify engine projects.

Call `package_prebuilt_game_release` with the exported directory, the main
executable path relative to that directory, a separate output directory, and
the required release profile. Read `references/WORKFLOW.md` before creating a
store handoff.

Every call must explicitly declare `content_license_mode`. Use `original_only`
only when the shipped directory contains no third-party content. Otherwise use
`third_party_notices` and provide a bounded `.txt` or `.md` notices path inside
the source directory. The tool verifies and hashes that file, includes it with
the shipped content, and writes `license-provenance.json` for the handoff.

The Steam profile always writes a preview build and never uploads it. The
WeGame profile writes a local preflight record, not a portal-owned manifest.
Neither profile stores credentials or performs authenticated submission.
