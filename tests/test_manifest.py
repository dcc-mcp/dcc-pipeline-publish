import importlib.util
from pathlib import Path


MODULE = Path(__file__).parents[1] / "skill/pipeline-publish/scripts/_manifest.py"
SPEC = importlib.util.spec_from_file_location("_manifest", MODULE)
manifest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manifest)


def test_manifest_detects_changed_file(tmp_path):
    asset = tmp_path / "asset.usda"
    asset.write_text("#usda 1.0")
    data = {
        "schema": manifest.SCHEMA,
        "project": "demo",
        "entity": {"type": "Asset", "name": "robot"},
        "version": 1,
        "files": [manifest.file_record(str(asset), "usd")],
    }
    assert manifest.validate(data) == []
    asset.write_text("changed")
    assert "hash changed" in manifest.validate(data)[0]


def test_manifest_requires_files():
    errors = manifest.validate({"schema": manifest.SCHEMA, "project": "demo", "entity": {}, "version": 1, "files": []})
    assert errors == ["files must be a non-empty list"]
