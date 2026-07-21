# Cross-engine game release workflow

## Ownership boundary

1. Use the Unreal, Unity, or Godot adapter to produce a complete playable build.
2. Smoke-test that build before distribution packaging.
3. Call `package_prebuilt_game_release` on the exported directory.
4. Verify the returned artifacts in the target platform's test environment.

This skill deliberately does not open an editor, compile scripts, cook assets,
or publish to an authenticated store account.

## Profiles

### `installer`

Requires Inno Setup 6. The tool auto-detects `ISCC.exe`, or accepts
`installer_compiler_path`. Pass Microsoft's official x64 redistributable as
`vc_redist_path` when the exported game requires that runtime. The generated
installer supports silent installation and uninstallation.

### `steam`

Requires numeric `steam_app_id` and `steam_depot_id`. The generated app VDF has
`Preview` enabled. Review it, configure required redistributables in Steamworks,
and use an authenticated SteamCMD session only after approval.

### `wegame`

Creates a hash-bearing local preflight record and checklist. It is not a WeGame
manifest. Project approval, Rail SDK integration, developer-client testing, and
authenticated portal submission remain external steps.

## Safety

- `output_directory` must not be inside `source_directory`.
- `executable_relative_path` cannot escape the source directory.
- The tool never launches the game, uploads content, or stores credentials.
- Code signing is a separate release gate and should use protected credentials.
