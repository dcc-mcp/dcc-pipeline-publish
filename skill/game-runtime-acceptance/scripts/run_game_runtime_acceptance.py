"""Launch and evaluate a prebuilt Windows game."""

from __future__ import annotations

from typing import Any, Dict, List

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success
from dcc_mcp_core.skills_helper import check_dcc_cancelled

from _acceptance import AcceptanceFailure, run_acceptance


@skill_entry
def main(
    request_id: str,
    source_directory: str,
    executable_relative_path: str,
    evidence_directory: str,
    engine: str,
    completion_event: Dict[str, Any],
    arguments: List[str] | None = None,
    timeout_seconds: int = 600,
    event_prefix: str = "",
    required_events: List[Dict[str, Any]] | None = None,
    metrics: List[Dict[str, Any]] | None = None,
    required_markers: List[str] | None = None,
    forbidden_markers: List[str] | None = None,
    leave_running_on_success: bool = True,
    **_: Any,
) -> Dict[str, Any]:
    try:
        result = run_acceptance(
            request_id=request_id,
            source_directory=source_directory,
            executable_relative_path=executable_relative_path,
            evidence_directory=evidence_directory,
            engine=engine,
            arguments=arguments or [],
            timeout_seconds=timeout_seconds,
            event_prefix=event_prefix,
            completion_event=completion_event,
            required_events=required_events or [],
            metrics=metrics or [],
            required_markers=required_markers or [],
            forbidden_markers=forbidden_markers or [],
            leave_running_on_success=leave_running_on_success,
            check_cancelled=check_dcc_cancelled,
        )
        return skill_success(
            "Game runtime acceptance passed",
            prompt="Bind canonical ui-control to the returned process_id for visual proof, or package the exact accepted build.",
            **result,
        )
    except AcceptanceFailure as exc:
        return skill_error(
            "Game runtime acceptance failed",
            str(exc),
            report=exc.report,
        )
    except Exception as exc:
        return skill_exception(exc, message="Game runtime acceptance could not run")


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
