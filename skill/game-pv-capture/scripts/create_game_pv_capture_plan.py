"""Create a request-scoped exact-window game PV capture plan."""

from __future__ import annotations

from typing import Any, Dict, List

from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success

from _capture import create_capture_plan


@skill_entry
def main(
    request_id: str,
    evidence_directory: str,
    instance_id: str,
    session_id: str,
    process_id: int,
    window_handle: int,
    shots: List[Dict[str, Any]],
    **_: Any,
) -> Dict[str, Any]:
    try:
        result = create_capture_plan(
            request_id=request_id,
            evidence_directory=evidence_directory,
            instance_id=instance_id,
            session_id=session_id,
            process_id=process_id,
            window_handle=window_handle,
            shots=shots,
        )
        return skill_success(
            "Game PV capture plan created",
            prompt="Call canonical ui_control__record_clip once per returned shot using the exact instance_id and arguments, then finalize the manifests.",
            **result,
        )
    except Exception as exc:
        return skill_exception(exc, message="Game PV capture plan could not be created")


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
