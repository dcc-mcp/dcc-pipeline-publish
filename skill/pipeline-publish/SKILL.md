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
    version: "0.1.0"
    tags: [publish, shotgrid, fpt, openusd, deadline, render-farm, pipeline]
    search-hint: "publish asset or shot, create publish manifest, register PublishedFile, link render job, production tracking"
    tools: tools.yaml
---

# Pipeline Publish

Create the manifest after DCC export and before external registration. Validate
it before calling OpenUSD, render-farm, or ShotGrid tools. Follow the detailed
orchestration recipe in `references/WORKFLOW.md`.

