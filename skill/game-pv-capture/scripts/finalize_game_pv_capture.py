"""Verify and preserve exact-window game PV shot artifacts."""

from __future__ import annotations

from typing import Any, Dict, List

from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success
from dcc_mcp_core.skills_helper import check_dcc_cancelled

from _capture import finalize_capture


@skill_entry
def main(
    plan_path: str,
    captured_shots: List[Dict[str, str]],
    **_: Any,
) -> Dict[str, Any]:
    try:
        result = finalize_capture(
            plan_path=plan_path,
            captured_shots=captured_shots,
            check_cancelled=check_dcc_cancelled,
        )
        return skill_success(
            "Game PV capture evidence finalized",
            prompt="Inspect every returned poster frame, then hand the verified JPEG sequences to HyperFrames for editing and final encoding.",
            **result,
        )
    except Exception as exc:
        return skill_exception(
            exc, message="Game PV capture evidence could not be finalized"
        )


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
