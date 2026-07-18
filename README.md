# dcc-pipeline-publish

<p align="center">
  <img src="docs/assets/dcc-pipeline-publish.svg" alt="DCC-MCP · PIPELINE-PUBLISH" width="600">
</p>

## Agent workflow

AI agents should use installed package skills through the shared gateway. IDE
users may continue to use the MCP endpoint.

```bash
dcc-mcp-cli dcc-types
dcc-mcp-cli list
dcc-mcp-cli search --query "<task>" --dcc-type <host>
dcc-mcp-cli describe <tool-slug>
dcc-mcp-cli call <tool-slug> --json '{"key":"value"}'
```

If the package skill is not active, call
`dcc-mcp-cli load-skill <skill-name> --dcc-type <host>`. After the task,
query `dcc-mcp-cli stats --range 24h --session-id <task-id>` and pass only
bounded evidence to the `review_skill_improvement` prompt from
`dcc-mcp-skills-creator`.


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

