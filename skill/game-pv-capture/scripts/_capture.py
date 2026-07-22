"""Plan and preserve exact-window gameplay shots for a game PV."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence


PLAN_SCHEMA = "dcc-mcp.game-pv-capture-plan.v1"
REPORT_SCHEMA = "dcc-mcp.game-pv-capture-report.v1"
MAX_PLAN_BYTES = 1024 * 1024
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_SHOTS = 16
MAX_TOTAL_FRAMES = 21_600
MAX_PIXELS = 16_777_216
SHOT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
PURPOSES = {"gameplay", "upgrade", "boss", "victory", "title", "custom"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json_idempotent(path: Path, value: Mapping[str, Any], conflict: str) -> None:
    payload = _json_bytes(value)
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != payload:
            raise ValueError(conflict)
        return
    temporary = path.with_name(".{}.{}.tmp".format(path.name, uuid.uuid4().hex))
    try:
        temporary.write_bytes(payload)
        os.replace(str(temporary), str(path))
    finally:
        if temporary.exists():
            temporary.unlink()


def _bounded_json(path: Path, maximum: int, label: str) -> Dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError("{} not found: {}".format(label, path))
    if path.stat().st_size > maximum:
        raise ValueError("{} exceeds the bounded size limit".format(label))
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("{} must contain a JSON object".format(label))
    return value


def _wire_label(value: Any, name: str, maximum: int = 128) -> str:
    text = str(value).strip()
    if (
        not text
        or len(text) > maximum
        or any(ord(character) < 32 for character in text)
    ):
        raise ValueError("{} must contain 1-{} safe characters".format(name, maximum))
    return text


def _positive_integer(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise ValueError("{} must be a positive integer".format(name))
    parsed = int(value)
    if parsed <= 0:
        raise ValueError("{} must be a positive integer".format(name))
    return parsed


def _canonical_request_id(value: str) -> str:
    try:
        parsed = uuid.UUID(str(value))
    except (ValueError, AttributeError) as exc:
        raise ValueError("request_id must be a canonical UUID") from exc
    canonical = str(parsed)
    if canonical != str(value).lower():
        raise ValueError("request_id must be a canonical UUID")
    return canonical


def _normalized_shots(
    shots: Sequence[Mapping[str, Any]], session_id: str, target: Mapping[str, int]
) -> List[Dict[str, Any]]:
    if not isinstance(shots, Sequence) or isinstance(shots, (str, bytes)):
        raise ValueError("shots must be an array")
    if not 1 <= len(shots) <= MAX_SHOTS:
        raise ValueError("shots must contain 1-{} entries".format(MAX_SHOTS))
    normalized: List[Dict[str, Any]] = []
    seen = set()
    total_frames = 0
    for index, raw in enumerate(shots):
        if not isinstance(raw, Mapping):
            raise ValueError("shots[{}] must be an object".format(index))
        shot_id = str(raw.get("shot_id", "")).strip()
        if not SHOT_ID_PATTERN.fullmatch(shot_id) or shot_id in seen:
            raise ValueError("shot_id must be unique lower-case kebab-case")
        seen.add(shot_id)
        purpose = str(raw.get("purpose", "custom")).strip()
        if purpose not in PURPOSES:
            raise ValueError("shots[{}].purpose is unsupported".format(index))
        duration_ms = int(raw.get("duration_ms", 0))
        frames_per_second = int(raw.get("frames_per_second", 30))
        jpeg_quality = int(raw.get("jpeg_quality", 92))
        if not 1000 <= duration_ms <= 180000:
            raise ValueError(
                "shots[{}].duration_ms must be 1000..=180000".format(index)
            )
        if not 1 <= frames_per_second <= 60:
            raise ValueError("shots[{}].frames_per_second must be 1..=60".format(index))
        if not 70 <= jpeg_quality <= 100:
            raise ValueError("shots[{}].jpeg_quality must be 70..=100".format(index))
        frame_count = (duration_ms * frames_per_second + 999) // 1000
        minimum_unique_frames = int(
            raw.get("minimum_unique_frames", min(2, frame_count))
        )
        if not 1 <= minimum_unique_frames <= frame_count:
            raise ValueError(
                "shots[{}].minimum_unique_frames exceeds its frame count".format(index)
            )
        total_frames += frame_count
        normalized.append(
            {
                "shot_id": shot_id,
                "purpose": purpose,
                "duration_ms": duration_ms,
                "frames_per_second": frames_per_second,
                "jpeg_quality": jpeg_quality,
                "expected_frame_count": frame_count,
                "minimum_unique_frames": minimum_unique_frames,
                "ui_control_record_clip_arguments": {
                    "session_id": session_id,
                    "process_id": target["process_id"],
                    "window_handle": target["window_handle"],
                    "duration_ms": duration_ms,
                    "frames_per_second": frames_per_second,
                    "jpeg_quality": jpeg_quality,
                },
            }
        )
    if total_frames > MAX_TOTAL_FRAMES:
        raise ValueError(
            "capture plan exceeds the {}-frame aggregate limit".format(MAX_TOTAL_FRAMES)
        )
    return normalized


def create_capture_plan(
    request_id: str,
    evidence_directory: str,
    instance_id: str,
    session_id: str,
    process_id: int,
    window_handle: int,
    shots: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Write one deterministic, request-scoped exact-window capture plan."""
    canonical_id = _canonical_request_id(request_id)
    route = {
        "instance_id": _wire_label(instance_id, "instance_id"),
        "session_id": _wire_label(session_id, "session_id"),
    }
    target = {
        "process_id": _positive_integer(process_id, "process_id"),
        "window_handle": _positive_integer(window_handle, "window_handle"),
    }
    root = Path(evidence_directory).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    request_root = root / canonical_id
    if request_root.exists() and (
        not request_root.is_dir() or request_root.is_symlink()
    ):
        raise ValueError("request evidence path must be a real directory")
    request_root.mkdir(exist_ok=True)
    plan = {
        "schema": PLAN_SCHEMA,
        "request_id": canonical_id,
        "route": route,
        "target": target,
        "shots": _normalized_shots(shots, route["session_id"], target),
    }
    plan_path = request_root / "capture-plan.json"
    _write_json_idempotent(
        plan_path,
        plan,
        "request_id already exists with a different capture contract",
    )
    return {
        "plan": plan,
        "plan_path": str(plan_path),
        "plan_sha256": _sha256(plan_path),
        "request_directory": str(request_root),
    }


def _validated_frame(
    clip_root: Path,
    raw: Mapping[str, Any],
    index: int,
    started_at_ms: int,
    ended_at_ms: int,
) -> Dict[str, Any]:
    expected_name = "frame-{:06d}.jpg".format(index)
    name = str(raw.get("path", ""))
    if name != expected_name or Path(name).name != name:
        raise ValueError("clip manifest frame path must be a relative frame filename")
    if int(raw.get("index", -1)) != index:
        raise ValueError("clip manifest frame indexes must be contiguous")
    candidate = clip_root / name
    if candidate.is_symlink():
        raise ValueError("clip manifest references a symlink frame")
    frame = candidate.resolve()
    if frame.parent != clip_root or not frame.is_file():
        raise ValueError("clip manifest references a missing or escaped frame")
    byte_length = int(raw.get("byte_length", -1))
    if frame.stat().st_size != byte_length:
        raise ValueError("clip frame byte length mismatch: {}".format(name))
    expected_hash = str(raw.get("sha256", "")).lower()
    if (
        not re.fullmatch(r"[0-9a-f]{64}", expected_hash)
        or _sha256(frame) != expected_hash
    ):
        raise ValueError("clip frame hash mismatch: {}".format(name))
    data = frame.read_bytes()
    if (
        len(data) < 4
        or not data.startswith(b"\xff\xd8")
        or not data.endswith(b"\xff\xd9")
    ):
        raise ValueError("clip frame is not a complete JPEG: {}".format(name))
    timestamp_ms = int(raw.get("timestamp_ms", -1))
    if not started_at_ms <= timestamp_ms <= ended_at_ms:
        raise ValueError("clip frame timestamp is outside the recording interval")
    return {
        "index": index,
        "path": name,
        "timestamp_ms": timestamp_ms,
        "byte_length": byte_length,
        "sha256": expected_hash,
    }


def _validate_clip(
    manifest_path: Path, shot: Mapping[str, Any], target: Mapping[str, int]
) -> Dict[str, Any]:
    manifest_path = manifest_path.expanduser()
    if manifest_path.is_symlink() or manifest_path.parent.is_symlink():
        raise ValueError("clip manifest and directory must not be symlinks")
    manifest_path = manifest_path.resolve()
    if manifest_path.name != "manifest.json":
        raise ValueError("captured shot must reference manifest.json")
    manifest = _bounded_json(manifest_path, MAX_MANIFEST_BYTES, "clip manifest")
    clip_root = manifest_path.parent.resolve()
    if (
        manifest.get("manifest_version") != 1
        or manifest.get("recording_id") != clip_root.name
    ):
        raise ValueError("clip manifest identity is invalid")
    raw_target = manifest.get("target") or {}
    if (
        int(raw_target.get("process_id", 0)) != target["process_id"]
        or int(raw_target.get("window_handle", 0)) != target["window_handle"]
    ):
        raise ValueError("clip target does not match the planned PID/HWND")
    encoding = manifest.get("encoding") or {}
    if (
        encoding.get("format") != "jpeg_sequence"
        or int(encoding.get("frames_per_second", 0)) != shot["frames_per_second"]
        or int(encoding.get("jpeg_quality", 0)) != shot["jpeg_quality"]
    ):
        raise ValueError("clip encoding does not match the capture plan")
    dimensions = manifest.get("dimensions") or {}
    width = int(dimensions.get("width", 0))
    height = int(dimensions.get("height", 0))
    if width <= 0 or height <= 0 or width * height > MAX_PIXELS:
        raise ValueError("clip dimensions exceed the exact-window capture boundary")
    started_at_ms = int(manifest.get("started_at_ms", -1))
    ended_at_ms = int(manifest.get("ended_at_ms", -1))
    if started_at_ms < 0 or ended_at_ms < started_at_ms:
        raise ValueError("clip recording interval is invalid")
    raw_frames = manifest.get("frames")
    if (
        not isinstance(raw_frames, list)
        or len(raw_frames) != shot["expected_frame_count"]
    ):
        raise ValueError("clip frame count does not match the capture plan")
    frames = [
        _validated_frame(clip_root, raw, index, started_at_ms, ended_at_ms)
        for index, raw in enumerate(raw_frames)
    ]
    timestamps = [frame["timestamp_ms"] for frame in frames]
    if timestamps != sorted(timestamps):
        raise ValueError("clip frame timestamps must be monotonic")
    unique_frame_count = len({frame["sha256"] for frame in frames})
    if unique_frame_count < shot["minimum_unique_frames"]:
        raise ValueError(
            "clip unique frame count {} is below {}".format(
                unique_frame_count, shot["minimum_unique_frames"]
            )
        )
    return {
        "manifest": manifest,
        "manifest_path": manifest_path,
        "manifest_sha256": _sha256(manifest_path),
        "clip_root": clip_root,
        "frames": frames,
        "unique_frame_count": unique_frame_count,
        "width": width,
        "height": height,
    }


def _materialize_clip(
    request_root: Path,
    shot_id: str,
    validated: Mapping[str, Any],
    check_cancelled: Optional[Callable[[], None]],
) -> Path:
    shots_root = request_root / "shots"
    if shots_root.exists() and (shots_root.is_symlink() or not shots_root.is_dir()):
        raise ValueError("request shot evidence root must be a real directory")
    shots_root.mkdir(exist_ok=True)
    destination = shots_root / shot_id
    if destination.exists():
        if destination.is_symlink() or not destination.is_dir():
            raise ValueError("materialized shot path must be a real directory")
        existing_manifest = destination / "manifest.json"
        if (
            not existing_manifest.is_file()
            or _sha256(existing_manifest) != validated["manifest_sha256"]
        ):
            raise ValueError(
                "materialized shot conflicts with existing evidence: {}".format(shot_id)
            )
        for index, frame in enumerate(validated["frames"]):
            if check_cancelled and index % 32 == 0:
                check_cancelled()
            copied = destination / frame["path"]
            if not copied.is_file() or _sha256(copied) != frame["sha256"]:
                raise ValueError(
                    "materialized shot frame conflicts with existing evidence"
                )
        return destination
    staging = destination.parent / ".{}.{}.tmp".format(shot_id, uuid.uuid4().hex)
    staging.mkdir()
    try:
        for index, frame in enumerate(validated["frames"]):
            if check_cancelled and index % 32 == 0:
                check_cancelled()
            copied = staging / frame["path"]
            shutil.copyfile(validated["clip_root"] / frame["path"], copied)
            if (
                copied.stat().st_size != frame["byte_length"]
                or _sha256(copied) != frame["sha256"]
            ):
                raise ValueError("copied shot frame failed integrity verification")
        shutil.copyfile(validated["manifest_path"], staging / "manifest.json")
        os.replace(str(staging), str(destination))
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return destination


def finalize_capture(
    plan_path: str,
    captured_shots: Sequence[Mapping[str, Any]],
    check_cancelled: Optional[Callable[[], None]] = None,
) -> Dict[str, Any]:
    """Verify Core clip manifests and preserve immutable PV shot inputs."""
    path = Path(plan_path).expanduser().resolve()
    plan = _bounded_json(path, MAX_PLAN_BYTES, "capture plan")
    if plan.get("schema") != PLAN_SCHEMA or path.name != "capture-plan.json":
        raise ValueError("capture plan schema or path is invalid")
    request_root = path.parent.resolve()
    if request_root.name != plan.get("request_id") or request_root.is_symlink():
        raise ValueError("capture plan is not in its request-scoped evidence directory")
    planned_shots = plan.get("shots") or []
    if not isinstance(captured_shots, Sequence) or isinstance(
        captured_shots, (str, bytes)
    ):
        raise ValueError("captured_shots must be an array")
    provided: Dict[str, str] = {}
    for item in captured_shots:
        if not isinstance(item, Mapping):
            raise ValueError("captured_shots entries must be objects")
        shot_id = str(item.get("shot_id", ""))
        manifest_path = str(item.get("manifest_path", "")).strip()
        if (
            not SHOT_ID_PATTERN.fullmatch(shot_id)
            or not manifest_path
            or shot_id in provided
        ):
            raise ValueError(
                "captured_shots must contain unique shot_id and manifest_path values"
            )
        provided[shot_id] = manifest_path
    expected = {str(shot.get("shot_id")) for shot in planned_shots}
    if set(provided) != expected:
        raise ValueError("captured_shots must match every planned shot exactly once")
    report_shots = []
    total_frames = 0
    total_bytes = 0
    for shot in planned_shots:
        if check_cancelled:
            check_cancelled()
        shot_id = shot["shot_id"]
        validated = _validate_clip(Path(provided[shot_id]), shot, plan["target"])
        destination = _materialize_clip(
            request_root, shot_id, validated, check_cancelled
        )
        frame_count = len(validated["frames"])
        byte_count = sum(frame["byte_length"] for frame in validated["frames"])
        total_frames += frame_count
        total_bytes += byte_count
        poster_indexes = sorted({0, frame_count // 2, frame_count - 1})
        report_shots.append(
            {
                "shot_id": shot_id,
                "purpose": shot["purpose"],
                "target": validated["manifest"]["target"],
                "source_manifest_path": str(validated["manifest_path"]),
                "source_manifest_sha256": validated["manifest_sha256"],
                "materialized_directory": str(destination),
                "materialized_manifest_path": str(destination / "manifest.json"),
                "frame_count": frame_count,
                "unique_frame_count": validated["unique_frame_count"],
                "byte_count": byte_count,
                "dimensions": {
                    "width": validated["width"],
                    "height": validated["height"],
                },
                "poster_frames": [
                    str(destination / validated["frames"][index]["path"])
                    for index in poster_indexes
                ],
                "hyperframes_input": {
                    "kind": "jpeg_sequence",
                    "frames_pattern": str(destination / "frame-%06d.jpg"),
                    "frames_per_second": shot["frames_per_second"],
                    "duration_ms": shot["duration_ms"],
                },
            }
        )
    report = {
        "schema": REPORT_SCHEMA,
        "passed": True,
        "request_id": plan["request_id"],
        "plan_path": str(path),
        "plan_sha256": _sha256(path),
        "route": plan["route"],
        "target": plan["target"],
        "shots": report_shots,
        "total_frame_count": total_frames,
        "total_frame_bytes": total_bytes,
        "failures": [],
    }
    report_path = request_root / "capture-report.json"
    _write_json_idempotent(
        report_path,
        report,
        "capture report conflicts with existing request evidence",
    )
    return {"report": report, "report_path": str(report_path)}
