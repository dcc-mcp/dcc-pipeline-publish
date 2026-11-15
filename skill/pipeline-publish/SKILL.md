---
name: pipeline-publish
description: Pipeline skill for creating and validating portable publish manifests that connect DCC exports, OpenUSD validation, render jobs, and ShotGrid/FPT records.
license: MIT
compatibility: "dcc-mcp-core 0.19+, Python 3.9+"
metadata:
  dcc-mcp:
    dcc: python
    layer: domain
    stage: pipeline
    version: "0.2.0"
    tags: [publish, shotgrid, fpt, openusd, deadline, render-farm, pipeline, scene-qa]
    search-hint: "publish asset or shot, create publish manifest, register PublishedFile, link render job, production tracking, check scene for render farm"
    tools: tools.yaml
    recipes: RECIPES.yaml
    recipes_undo:
      scene_qa: single-step
---

# Pipeline Publish

Create the manifest after DCC export and before external registration. Validate
it before calling OpenUSD, render-farm, or ShotGrid tools. Follow the detailed
orchestration recipe in `references/WORKFLOW.md`.

## Outcome recipes

`RECIPES.yaml` registers one outcome-level recipe with the core recipe runtime,
reachable through `recipes__list` / `recipes__get` / `recipes__validate` /
`recipes__apply`:

| Recipe | One-line ask | Deliverable | `undo` |
|---|---|---|---|
| `scene_qa` | "Check whether this scene is ready for the render farm" | A digest-backed JSON report listing unsaved state, output path, frame range, missing textures and libraries, naming and duplicate names | `single-step` — delete the report file; the scene is never modified |

Each recipe carries `examplePrompts`, `recovery`, and an `undo` contract in the
P0-B enum (`single-step` \| `none` \| `manual`), mirrored in this file's
`metadata.dcc-mcp.recipes_undo`. `tests/test_pipeline_publish_recipes.py` asserts
the contract and proves every rule can fail.

Core returns the plan verbatim and applies no schema defaults, so materialize
`${x}` placeholders before dispatch:

```bash
python examples/scene_qa/materialize_plan.py --inputs examples/scene_qa/inputs.example.json
```

