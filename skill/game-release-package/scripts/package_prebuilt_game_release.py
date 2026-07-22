"""Create distribution artifacts from a prebuilt Windows game directory."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success
from dcc_mcp_core.skills_helper import check_dcc_cancelled

from _release import package_release


@skill_entry
def main(
    source_directory: str,
    executable_relative_path: str,
    output_directory: str,
    release_profile: str,
    content_license_mode: str,
    third_party_notices_relative_path: str = "",
    product_name: str = "",
    product_version: str = "1.0.0",
    publisher: str = "",
    installer_compiler_path: str = "",
    vc_redist_path: str = "",
    steam_app_id: str = "",
    steam_depot_id: str = "",
    **_: Any,
) -> Dict[str, Any]:
    try:
        result = package_release(
            source_directory=source_directory,
            executable_relative_path=executable_relative_path,
            output_directory=output_directory,
            release_profile=release_profile,
            content_license_mode=content_license_mode,
            third_party_notices_relative_path=third_party_notices_relative_path,
            product_name=product_name,
            product_version=product_version,
            publisher=publisher,
            installer_compiler_path=installer_compiler_path,
            vc_redist_path=vc_redist_path,
            steam_app_id=steam_app_id,
            steam_depot_id=steam_depot_id,
            check_cancelled=check_dcc_cancelled,
        )
        return skill_success("Game release package created", **result)
    except Exception as exc:
        return skill_exception(exc, message="Game release packaging failed")


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
