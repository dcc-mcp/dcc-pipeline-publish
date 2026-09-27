# `scene_qa` host-run evidence

Status: **not run on a real host** (B-class, non-blocking).

No DCC host, scene, or render farm was available on the machine that authored
this recipe, so the deliverable is the plan plus the gate that will judge the
receipt — not a recorded run. Nothing below is a synthesized artifact passed off
as a real one.

## What is reproducible today

```bash
python examples/scene_qa/materialize_plan.py --inputs examples/scene_qa/inputs.example.json
```

Resolves `tool_routing` for `--adapter`, applies `inputs_schema` defaults,
substitutes every `${x}` placeholder, and prints the dispatch plan together with
the `undo_steps` and the `output_contract` the receipt will be validated against.
No host is required; it runs in CI.

## What a real run must produce

Dispatch the plan to a live instance, then validate the observed receipt against
`skill/pipeline-publish/RECIPES.yaml` → `recipes[scene_qa].output_contract`:

| Field | Evidence it carries | Fails when |
|---|---|---|
| `checked_count` | number of checks that actually executed (1-8) | the scan ran nothing |
| `finding_count`, `blocking_finding_count` | what the sweep found | the report is empty |
| `report_sha256` | SHA-256 of the written JSON report, `^[0-9a-f]{64}$` | the report was not written or was truncated |
| `scene_changed` | `const: false` — read-only proof | the recipe mutated the scene |

Record here: host and version, the command, the run log, the report file, and its
`sha256sum`. A run that cannot produce all four fields has not delivered the
recipe.
