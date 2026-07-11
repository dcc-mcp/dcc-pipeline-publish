# Publish workflow

1. Export from the active DCC with its typed geometry, cache, texture, or USD tool.
2. Call `create_publish_manifest` with every file and its role.
3. Call `validate_publish_manifest`; stop if a file is missing or changed.
4. For USD files, call `openusd-validate__validate_stage`.
5. Submit previews or final frames through the host `*-render-farm` skill.
6. Use `shotgrid-crud` to resolve the Project, Asset/Shot, and Task.
7. Create or update the ShotGrid Version and PublishedFile. Store the manifest
   path and render job ID in studio fields when those fields exist.
8. Use `shotgrid-note` for validation warnings that require artist action.

Never put ShotGrid credentials or cloud tokens in the manifest.

