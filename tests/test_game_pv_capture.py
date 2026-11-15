import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


MODULE = Path(__file__).parents[1] / "skill/game-pv-capture/scripts/_capture.py"
SPEC = importlib.util.spec_from_file_location("_capture", MODULE)
capture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture)


REQUEST_ID = "01234567-89ab-4cde-8fab-0123456789ab"


def _shot(**overrides):
    value = {
        "shot_id": "combat",
        "purpose": "gameplay",
        "duration_ms": 1000,
        "frames_per_second": 2,
        "jpeg_quality": 92,
        "minimum_unique_frames": 2,
    }
    value.update(overrides)
    return value


def _write_clip(root, *, process_id=4242, window_handle=8192, payloads=None):
    root.mkdir(parents=True)
    payloads = payloads or [b"first", b"second"]
    frames = []
    for index, payload in enumerate(payloads):
        data = b"\xff\xd8" + payload + b"\xff\xd9"
        name = "frame-{:06d}.jpg".format(index)
        (root / name).write_bytes(data)
        frames.append(
            {
                "index": index,
                "path": name,
                "timestamp_ms": 1000 + index * 500,
                "byte_length": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    manifest = {
        "manifest_version": 1,
        "recording_id": root.name,
        "target": {
            "process_id": process_id,
            "window_handle": window_handle,
            "window_title": "Test Game",
        },
        "encoding": {
            "format": "jpeg_sequence",
            "frames_per_second": 2,
            "jpeg_quality": 92,
        },
        "dimensions": {"width": 1280, "height": 720},
        "started_at_ms": 1000,
        "ended_at_ms": 2000,
        "frames": frames,
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _plan(tmp_path, shots=None):
    return capture.create_capture_plan(
        request_id=REQUEST_ID,
        evidence_directory=str(tmp_path / "evidence"),
        instance_id="unity-instance-a",
        session_id="pv",
        process_id=4242,
        window_handle=8192,
        shots=shots or [_shot()],
    )


def test_plan_preserves_two_level_route_and_exact_record_arguments(tmp_path):
    result = _plan(tmp_path)
    plan = result["plan"]

    assert plan["schema"] == "dcc-mcp.game-pv-capture-plan.v1"
    assert plan["route"] == {
        "instance_id": "unity-instance-a",
        "session_id": "pv",
    }
    assert plan["target"] == {"process_id": 4242, "window_handle": 8192}
    assert plan["shots"][0]["ui_control_record_clip_arguments"] == {
        "session_id": "pv",
        "process_id": 4242,
        "window_handle": 8192,
        "duration_ms": 1000,
        "frames_per_second": 2,
        "jpeg_quality": 92,
    }
    assert Path(result["plan_path"]).is_file()
    assert len(result["plan_sha256"]) == 64


def test_finalize_verifies_and_materializes_hash_bearing_shot(tmp_path):
    planned = _plan(tmp_path)
    manifest = _write_clip(tmp_path / "recordings" / "clip-a")

    result = capture.finalize_capture(
        plan_path=planned["plan_path"],
        captured_shots=[{"shot_id": "combat", "manifest_path": str(manifest)}],
    )

    assert result["report"]["passed"] is True
    shot = result["report"]["shots"][0]
    assert shot["frame_count"] == 2
    assert shot["unique_frame_count"] == 2
    assert len(shot["source_manifest_sha256"]) == 64
    materialized = Path(shot["materialized_directory"])
    assert (materialized / "manifest.json").is_file()
    assert (materialized / "frame-000000.jpg").read_bytes().startswith(b"\xff\xd8")
    assert shot["hyperframes_input"]["frames_pattern"].endswith("frame-%06d.jpg")
    assert Path(result["report_path"]).is_file()


def test_finalize_rejects_target_mismatch_and_frame_tampering(tmp_path):
    planned = _plan(tmp_path)
    wrong_target = _write_clip(tmp_path / "recordings" / "clip-wrong", process_id=9999)
    with pytest.raises(ValueError, match="target does not match"):
        capture.finalize_capture(
            plan_path=planned["plan_path"],
            captured_shots=[{"shot_id": "combat", "manifest_path": str(wrong_target)}],
        )

    manifest = _write_clip(tmp_path / "recordings" / "clip-tampered")
    (manifest.parent / "frame-000001.jpg").write_bytes(b"\xff\xd8tamper\xff\xd9")
    with pytest.raises(ValueError, match="hash mismatch"):
        capture.finalize_capture(
            plan_path=planned["plan_path"],
            captured_shots=[{"shot_id": "combat", "manifest_path": str(manifest)}],
        )


def test_finalize_rejects_manifest_path_escape_and_static_fake_shot(tmp_path):
    planned = _plan(tmp_path)
    escaped = _write_clip(tmp_path / "recordings" / "clip-escape")
    manifest = json.loads(escaped.read_text(encoding="utf-8"))
    manifest["frames"][0]["path"] = "../outside.jpg"
    escaped.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="relative frame filename"):
        capture.finalize_capture(
            plan_path=planned["plan_path"],
            captured_shots=[{"shot_id": "combat", "manifest_path": str(escaped)}],
        )

    static_manifest = _write_clip(
        tmp_path / "recordings" / "clip-static", payloads=[b"same", b"same"]
    )
    with pytest.raises(ValueError, match="unique frame"):
        capture.finalize_capture(
            plan_path=planned["plan_path"],
            captured_shots=[
                {"shot_id": "combat", "manifest_path": str(static_manifest)}
            ],
        )


def test_plan_is_idempotent_for_same_contract_and_conflicts_on_reuse(tmp_path):
    first = _plan(tmp_path)
    second = _plan(tmp_path)
    assert second["plan_sha256"] == first["plan_sha256"]

    with pytest.raises(ValueError, match="different capture contract"):
        _plan(tmp_path, shots=[_shot(duration_ms=2000, frames_per_second=1)])
