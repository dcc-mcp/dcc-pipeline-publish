"""Evaluate an existing structured game runtime log."""

from __future__ import annotations

from typing import Any, Dict, List

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success

from _acceptance import evaluate_log


@skill_entry
def main(
    log_path: str,
    completion_event: Dict[str, Any],
    event_prefix: str = "",
    required_events: List[Dict[str, Any]] | None = None,
    metrics: List[Dict[str, Any]] | None = None,
    required_markers: List[str] | None = None,
    forbidden_markers: List[str] | None = None,
    executable_path: str = "",
    **_: Any,
) -> Dict[str, Any]:
    try:
        report = evaluate_log(
            log_path=log_path,
            event_prefix=event_prefix,
            completion_event=completion_event,
            required_events=required_events or [],
            metrics=metrics or [],
            required_markers=required_markers or [],
            forbidden_markers=forbidden_markers or [],
            executable_path=executable_path,
        )
        if not report["passed"]:
            return skill_error(
                "Game runtime log failed acceptance",
                "; ".join(report["failures"]),
                report=report,
            )
        return skill_success("Game runtime log passed acceptance", report=report)
    except Exception as exc:
        return skill_exception(exc, message="Game runtime log validation failed")


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
