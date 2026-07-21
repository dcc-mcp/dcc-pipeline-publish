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
        release.package_release(str(source), "Example.exe", str(source / "release"), "wegame")


def test_writes_steam_preview_scripts(tmp_path):
    source, _ = _game(tmp_path)
    result = release.package_release(
        str(source),
        "Example.exe",
        str(tmp_path / "release"),
        "steam",
        steam_app_id="123456",
        steam_depot_id="123457",
    )
    app = Path(result["artifacts"][0])
    assert '"Preview" "1"' in app.read_text(encoding="utf-8")
    assert str(source).replace("\\", "/") in app.read_text(encoding="utf-8")


def test_writes_wegame_hash_preflight(tmp_path):
    source, executable = _game(tmp_path)
    result = release.package_release(
        str(source), "Example.exe", str(tmp_path / "release"), "wegame", product_name="Example"
    )
    manifest = json.loads(Path(result["artifacts"][0]).read_text(encoding="utf-8"))
    assert manifest["schema"] == "dcc-mcp.game-release.wegame-preflight.v1"
    assert manifest["executable_sha256"] == hashlib.sha256(executable.read_bytes()).hexdigest()


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
