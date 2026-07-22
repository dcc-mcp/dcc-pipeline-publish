import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


MODULE = Path(__file__).parents[1] / "skill/game-release-package/scripts/_release.py"
SPEC = importlib.util.spec_from_file_location("_release", MODULE)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


def _game(tmp_path):
    source = tmp_path / "build"
    source.mkdir()
    executable = source / "Example.exe"
    executable.write_bytes(b"portable game")
    return source, executable


def test_rejects_output_inside_source(tmp_path):
    source, _ = _game(tmp_path)
    with pytest.raises(ValueError, match="outside source_directory"):
        release.package_release(
            str(source),
            "Example.exe",
            str(source / "release"),
            "wegame",
            content_license_mode="original_only",
        )


def test_writes_steam_preview_scripts(tmp_path):
    source, _ = _game(tmp_path)
    result = release.package_release(
        str(source),
        "Example.exe",
        str(tmp_path / "release"),
        "steam",
        content_license_mode="original_only",
        steam_app_id="123456",
        steam_depot_id="123457",
    )
    app = Path(result["artifacts"][0])
    assert '"Preview" "1"' in app.read_text(encoding="utf-8")
    assert str(source).replace("\\", "/") in app.read_text(encoding="utf-8")


def test_writes_wegame_hash_preflight(tmp_path):
    source, executable = _game(tmp_path)
    result = release.package_release(
        str(source),
        "Example.exe",
        str(tmp_path / "release"),
        "wegame",
        content_license_mode="original_only",
        product_name="Example",
    )
    manifest = json.loads(Path(result["artifacts"][0]).read_text(encoding="utf-8"))
    assert manifest["schema"] == "dcc-mcp.game-release.wegame-preflight.v1"
    assert manifest["executable_sha256"] == hashlib.sha256(executable.read_bytes()).hexdigest()


def test_requires_explicit_content_license_mode(tmp_path):
    source, _ = _game(tmp_path)

    with pytest.raises(ValueError, match="content_license_mode"):
        release.package_release(
            str(source),
            "Example.exe",
            str(tmp_path / "release"),
            "wegame",
        )


def test_third_party_mode_requires_bounded_notice_and_writes_provenance(tmp_path):
    source, executable = _game(tmp_path)
    notices = source / "THIRD-PARTY-NOTICES.txt"
    notices.write_text("Example Dependency\nMIT\n", encoding="utf-8")

    result = release.package_release(
        str(source),
        "Example.exe",
        str(tmp_path / "release"),
        "wegame",
        content_license_mode="third_party_notices",
        third_party_notices_relative_path=notices.name,
    )

    provenance = json.loads(Path(result["license_provenance_path"]).read_text(encoding="utf-8"))
    assert provenance["schema"] == "dcc-mcp.game-release.license-provenance.v1"
    assert provenance["content_license_mode"] == "third_party_notices"
    assert provenance["executable_sha256"] == hashlib.sha256(executable.read_bytes()).hexdigest()
    assert provenance["third_party_notices"] == {
        "relative_path": notices.name,
        "bytes": notices.stat().st_size,
        "sha256": hashlib.sha256(notices.read_bytes()).hexdigest(),
    }
    assert Path(result["license_provenance_path"]) in [
        Path(path) for path in result["artifacts"]
    ]


def test_third_party_notice_cannot_escape_source(tmp_path):
    source, _ = _game(tmp_path)
    outside = tmp_path / "NOTICE.txt"
    outside.write_text("outside", encoding="utf-8")

    with pytest.raises(ValueError, match="stay inside source_directory"):
        release.package_release(
            str(source),
            "Example.exe",
            str(tmp_path / "release"),
            "wegame",
            content_license_mode="third_party_notices",
            third_party_notices_relative_path="../NOTICE.txt",
        )


def test_installer_script_supports_vc_redist(tmp_path):
    source, executable = _game(tmp_path)
    installer_dir = tmp_path / "release" / "Installer"
    installer_dir.mkdir(parents=True)
    redist = tmp_path / "vc_redist.x64.exe"
    redist.write_bytes(b"runtime")
    script, installer = release._write_installer_script(
        source, executable, installer_dir, "Example Game", "2.1.0", "Studio", redist
    )
    content = script.read_text(encoding="utf-8-sig")
    assert "vc_redist.x64.exe" in content
    assert 'Parameters: "/install /quiet /norestart"' in content
    assert installer.name == "Example-Game-Setup-2.1.0.exe"
