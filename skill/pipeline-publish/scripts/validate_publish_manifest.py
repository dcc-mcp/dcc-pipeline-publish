from __future__ import annotations

from typing import Any

from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success

from _manifest import load, validate


@skill_entry
def main(manifest_path: str, **_: Any) -> dict[str, Any]:
    try:
        source, manifest = load(manifest_path)
        errors = validate(manifest)
        if errors:
            raise ValueError("; ".join(errors))
        return skill_success("Publish manifest is valid", file=str(source), manifest=manifest)
    except Exception as exc:
        return skill_exception(exc, message="Publish manifest validation failed")


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main
    run_main(main)

