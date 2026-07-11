# dcc-pipeline-publish

A small, portable publish-manifest contract connecting DCC exports, OpenUSD
validation, render-farm jobs, and Autodesk Flow Production Tracking.

![DCC exports validated, rendered on a farm, and recorded as published versions](docs/images/dcc-pipeline-publish-showcase.webp)

## Why a manifest

The skill does not reimplement ShotGrid, OpenUSD, or Deadline. It records the
immutable files, hashes, entity identity, version, and optional farm job in one
JSON handoff that existing adapters can consume.

```mermaid
flowchart LR
    D[DCC export] --> P[Publish manifest]
    P --> U[OpenUSD validation]
    P --> R[Deadline or Flamenco]
    U --> S[ShotGrid PublishedFile]
    R --> V[ShotGrid Version]
```

See [`references/WORKFLOW.md`](skill/pipeline-publish/references/WORKFLOW.md)
for the agent orchestration recipe.

