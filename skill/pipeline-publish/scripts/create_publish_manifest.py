from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success

from _manifest import SCHEMA, file_record, validate


@skill_entry
def main(
    output_path: str,
    project: str,
    entity_type: str,
    entity_name: str,
    version: int,
    files: list[dict[str, str]],
    task: str | None = None,
    render_job_id: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    try:
        manifest = {
            "schema": SCHEMA,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "project": project,
            "entity": {"type": entity_type, "name": entity_name},
            "task": task,
            "version": int(version),
            "files": [file_record(item["path"], item["role"]) for item in files],
            "render_job_id": render_job_id,
        }
        errors = validate(manifest)
        if errors:
            raise ValueError("; ".join(errors))
        target = Path(output_path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return skill_success("Publish manifest created", file=str(target), manifest=manifest)
    except Exception as exc:
        return skill_exception(exc, message="Publish manifest creation failed")


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main
    run_main(main)

