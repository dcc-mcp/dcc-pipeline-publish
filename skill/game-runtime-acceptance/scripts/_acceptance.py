"""Engine-neutral acceptance for prebuilt Windows games."""

from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


REPORT_SCHEMA = "dcc-mcp.game-runtime-acceptance.v1"
MAX_LOG_BYTES = 64 * 1024 * 1024
PAIR_PATTERN = re.compile(
    r'(?:^|\s)([A-Za-z][A-Za-z0-9_.-]{0,63})=(?:"([^"]*)"|(\S+))'
)
ENGINES = {"unity", "unreal", "godot", "custom_stdout"}


class AcceptanceFailure(RuntimeError):
    """Acceptance failed after a report was materialized."""

    def __init__(self, report: Dict[str, Any]):
        self.report = report
        failures = report.get("failures") or ["runtime acceptance failed"]
        super().__init__("; ".join(str(item) for item in failures))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bounded_text(path: Path) -> Tuple[str, int]:
    size = path.stat().st_size
    if size > MAX_LOG_BYTES:
        raise ValueError("runtime log exceeds the 64 MiB acceptance limit")
    raw = path.read_bytes()
    return raw.decode("utf-8", errors="replace"), len(raw)


def _event_records(text: str, event_prefix: str) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    for line in text.splitlines():
        if event_prefix and event_prefix not in line:
            continue
        fields: Dict[str, str] = {}
        for match in PAIR_PATTERN.finditer(line):
            fields[match.group(1)] = match.group(2) if match.group(2) is not None else match.group(3)
        if fields.get("event"):
            records.append(fields)
    return records


def _normalized_rule(rule: Mapping[str, Any], label: str) -> Dict[str, Any]:
    event = str(rule.get("event", "")).strip()
    if not event or len(event) > 128:
        raise ValueError("{} event must contain 1-128 characters".format(label))
    minimum = int(rule.get("min_count", 1))
    maximum_raw = rule.get("max_count")
    maximum = int(maximum_raw) if maximum_raw is not None else None
    if minimum < 0 or maximum is not None and maximum < minimum:
        raise ValueError("{} count bounds are invalid".format(label))
    raw_fields = rule.get("fields") or {}
    if not isinstance(raw_fields, Mapping) or len(raw_fields) > 16:
        raise ValueError("{} fields must be an object with at most 16 entries".format(label))
    fields = {str(key): str(value) for key, value in raw_fields.items()}
    return {"event": event, "min_count": minimum, "max_count": maximum, "fields": fields}


def _rule_result(
    records: Iterable[Mapping[str, str]], rule: Mapping[str, Any], label: str
) -> Dict[str, Any]:
    normalized = _normalized_rule(rule, label)
    count = sum(
        1
        for record in records
        if record.get("event") == normalized["event"]
        and all(record.get(key) == value for key, value in normalized["fields"].items())
    )
    passed = count >= normalized["min_count"] and (
        normalized["max_count"] is None or count <= normalized["max_count"]
    )
    return dict(normalized, label=label, observed_count=count, passed=passed)


def _metric_result(
    records: Iterable[Mapping[str, str]], metric: Mapping[str, Any], index: int
) -> Dict[str, Any]:
    event = str(metric.get("event", "")).strip()
    field = str(metric.get("field", "")).strip()
    if not event or not field:
        raise ValueError("metric {} requires event and field".format(index))
    minimum = float(metric["minimum"]) if metric.get("minimum") is not None else None
    maximum = float(metric["maximum"]) if metric.get("maximum") is not None else None
    min_samples = int(metric.get("min_samples", 1))
    if min_samples < 1 or minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("metric {} bounds are invalid".format(index))
    values: List[float] = []
    non_numeric = 0
    for record in records:
        if record.get("event") != event or field not in record:
            continue
        try:
            values.append(float(record[field]))
        except ValueError:
            non_numeric += 1
    observed_min = min(values) if values else None
    observed_max = max(values) if values else None
    passed = len(values) >= min_samples and non_numeric == 0
    if minimum is not None and values:
        passed = passed and observed_min >= minimum
    if maximum is not None and values:
        passed = passed and observed_max <= maximum
    return {
        "event": event,
        "field": field,
        "minimum": minimum,
        "maximum": maximum,
        "min_samples": min_samples,
        "sample_count": len(values),
        "non_numeric_count": non_numeric,
        "observed_min": observed_min,
        "observed_max": observed_max,
        "passed": passed,
    }


def _validate_contract(
    event_prefix: str,
    completion_event: Mapping[str, Any],
    required_events: Sequence[Mapping[str, Any]],
    metrics: Sequence[Mapping[str, Any]],
    required_markers: Sequence[str],
    forbidden_markers: Sequence[str],
) -> None:
    if len(event_prefix) > 128:
        raise ValueError("event_prefix must contain at most 128 characters")
    if len(required_events) > 128 or len(metrics) > 64:
        raise ValueError("runtime acceptance rule count exceeds the bounded contract")
    _normalized_rule(completion_event, "completion_event")
    for index, rule in enumerate(required_events):
        _normalized_rule(rule, "required_events[{}]".format(index))
    for index, metric in enumerate(metrics):
        _metric_result([], metric, index)
    for name, markers in (
        ("required_markers", required_markers),
        ("forbidden_markers", forbidden_markers),
    ):
        if len(markers) > 64 or any(not str(value) or len(str(value)) > 512 for value in markers):
            raise ValueError("{} exceeds the bounded marker contract".format(name))


def evaluate_log(
    log_path: str,
    event_prefix: str,
    completion_event: Mapping[str, Any],
    required_events: Sequence[Mapping[str, Any]],
    metrics: Sequence[Mapping[str, Any]],
    required_markers: Sequence[str],
    forbidden_markers: Sequence[str],
    executable_path: str = "",
) -> Dict[str, Any]:
    """Evaluate one bounded log without launching a process."""
    _validate_contract(
        event_prefix,
        completion_event,
        required_events,
        metrics,
        required_markers,
        forbidden_markers,
    )
    path = Path(log_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError("runtime log not found: {}".format(path))
    text, byte_count = _bounded_text(path)
    records = _event_records(text, event_prefix.strip())
    completion = _rule_result(records, completion_event, "completion_event")
    event_results = [
        _rule_result(records, rule, "required_events[{}]".format(index))
        for index, rule in enumerate(required_events)
    ]
    metric_results = [
        _metric_result(records, metric, index) for index, metric in enumerate(metrics)
    ]
    marker_results = []
    failures: List[str] = []
    if not completion["passed"]:
        failures.append(
            "completion event {} observed {} time(s)".format(
                completion["event"], completion["observed_count"]
            )
        )
    for result in event_results:
        if not result["passed"]:
            failures.append(
                "event {} observed {} time(s) outside [{}, {}]".format(
                    result["event"],
                    result["observed_count"],
                    result["min_count"],
                    result["max_count"] if result["max_count"] is not None else "unbounded",
                )
            )
    for marker in required_markers:
        value = str(marker)
        count = text.count(value)
        marker_results.append({"marker": value, "kind": "required", "count": count})
        if count == 0:
            failures.append("required marker was not observed: {}".format(value))
    for marker in forbidden_markers:
        value = str(marker)
        count = text.count(value)
        marker_results.append({"marker": value, "kind": "forbidden", "count": count})
        if count:
            failures.append("forbidden marker was observed: {}".format(value))
    for result in metric_results:
        if not result["passed"]:
            failures.append(
                "metric {}/{} failed with {} numeric sample(s), min={}, max={}".format(
                    result["event"],
                    result["field"],
                    result["sample_count"],
                    result["observed_min"],
                    result["observed_max"],
                )
            )
    event_counts: Dict[str, int] = {}
    for record in records:
        name = record["event"]
        event_counts[name] = event_counts.get(name, 0) + 1
    report: Dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "passed": not failures,
        "log_path": str(path),
        "log_sha256": _sha256(path),
        "log_bytes": byte_count,
        "event_prefix": event_prefix,
        "event_counts": event_counts,
        "completion": completion,
        "required_events": event_results,
        "markers": marker_results,
        "metrics": metric_results,
        "failures": failures,
    }
    if executable_path:
        executable = Path(executable_path).expanduser().resolve()
        if not executable.is_file():
            raise FileNotFoundError("game executable not found: {}".format(executable))
        report["executable_path"] = str(executable)
        report["executable_sha256"] = _sha256(executable)
    return report


def _resolve_launch_paths(
    source_directory: str,
    executable_relative_path: str,
    evidence_directory: str,
    request_id: str,
) -> Tuple[Path, Path, Path]:
    source = Path(source_directory).expanduser().resolve()
    if not source.is_dir():
        raise FileNotFoundError("prebuilt game directory not found: {}".format(source))
    relative = Path(executable_relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("executable_relative_path must stay inside source_directory")
    executable = (source / relative).resolve()
    if source not in executable.parents or executable.suffix.lower() != ".exe" or not executable.is_file():
        raise FileNotFoundError("Windows game executable not found under source_directory")
    canonical_request = str(uuid.UUID(request_id))
    if canonical_request.lower() != request_id.lower():
        raise ValueError("request_id must be a canonical UUID")
    evidence_root = Path(evidence_directory).expanduser().resolve()
    if evidence_root == source or source in evidence_root.parents:
        raise ValueError("evidence_directory must be outside source_directory")
    request_directory = evidence_root / canonical_request
    if request_directory.exists():
        raise FileExistsError("acceptance request directory already exists: {}".format(request_directory))
    request_directory.mkdir(parents=True)
    return source, executable, request_directory


def _command(engine: str, executable: Path, arguments: Sequence[str], log_path: Path) -> List[str]:
    if engine not in ENGINES:
        raise ValueError("engine must be one of: {}".format(", ".join(sorted(ENGINES))))
    if len(arguments) > 64:
        raise ValueError("arguments must contain at most 64 items")
    normalized = []
    for argument in arguments:
        value = str(argument)
        if len(value) > 1024 or any(character in value for character in "\r\n\0"):
            raise ValueError("each argument must be a single line of at most 1024 characters")
        normalized.append(value)
    command = [str(executable)] + normalized
    if engine == "unity":
        command.extend(["-logFile", str(log_path)])
    elif engine == "unreal":
        command.extend(["-log", "-abslog={}".format(log_path)])
    elif engine == "godot":
        command.extend(["--log-file", str(log_path)])
    return command


def _terminate_process_tree(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _write_report(path: Path, report: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def run_acceptance(
    request_id: str,
    source_directory: str,
    executable_relative_path: str,
    evidence_directory: str,
    engine: str,
    arguments: Sequence[str],
    timeout_seconds: int,
    event_prefix: str,
    completion_event: Mapping[str, Any],
    required_events: Sequence[Mapping[str, Any]],
    metrics: Sequence[Mapping[str, Any]],
    required_markers: Sequence[str],
    forbidden_markers: Sequence[str],
    leave_running_on_success: bool,
    check_cancelled: Optional[Callable[[], None]] = None,
) -> Dict[str, Any]:
    """Launch an exact game executable, wait for completion, and write evidence."""
    if not 1 <= int(timeout_seconds) <= 7200:
        raise ValueError("timeout_seconds must be between 1 and 7200")
    _validate_contract(
        event_prefix,
        completion_event,
        required_events,
        metrics,
        required_markers,
        forbidden_markers,
    )
    if engine not in ENGINES:
        raise ValueError("engine must be one of: {}".format(", ".join(sorted(ENGINES))))
    if len(arguments) > 64 or any(
        len(str(value)) > 1024 or any(character in str(value) for character in "\r\n\0")
        for value in arguments
    ):
        raise ValueError("arguments exceed the bounded single-line contract")
    source, executable, request_directory = _resolve_launch_paths(
        source_directory, executable_relative_path, evidence_directory, request_id
    )
    log_path = request_directory / "runtime.log"
    report_path = request_directory / "acceptance-report.json"
    command = _command(engine, executable, arguments, log_path)
    process_options: Dict[str, Any] = {}
    if os.name == "nt":
        process_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        process_options["start_new_session"] = True
    output_stream = log_path.open("wb") if engine == "custom_stdout" else None
    try:
        process = subprocess.Popen(
            command,
            cwd=str(source),
            stdout=output_stream if output_stream is not None else subprocess.DEVNULL,
            stderr=subprocess.STDOUT if output_stream is not None else subprocess.DEVNULL,
            shell=False,
            **process_options,
        )
    except Exception:
        if output_stream is not None:
            output_stream.close()
        raise
    started = time.monotonic()
    try:
        while True:
            if check_cancelled is not None:
                check_cancelled()
            report = None
            if log_path.is_file():
                report = evaluate_log(
                    str(log_path),
                    event_prefix,
                    completion_event,
                    required_events,
                    metrics,
                    required_markers,
                    forbidden_markers,
                    str(executable),
                )
                if report["completion"]["passed"]:
                    time.sleep(0.25)
                    report = evaluate_log(
                        str(log_path),
                        event_prefix,
                        completion_event,
                        required_events,
                        metrics,
                        required_markers,
                        forbidden_markers,
                        str(executable),
                    )
                    report.update(
                        request_id=request_id,
                        engine=engine,
                        process_id=process.pid,
                        process_running=process.poll() is None,
                    )
                    _write_report(report_path, report)
                    if not report["passed"]:
                        _terminate_process_tree(process)
                        report["process_running"] = False
                        _write_report(report_path, report)
                        raise AcceptanceFailure(report)
                    if not leave_running_on_success:
                        _terminate_process_tree(process)
                        report["process_running"] = False
                        _write_report(report_path, report)
                    return {
                        "report": report,
                        "report_path": str(report_path),
                        "log_path": str(log_path),
                        "process_id": process.pid,
                        "process_running": report["process_running"],
                    }
            if process.poll() is not None:
                if report is None and log_path.is_file():
                    report = evaluate_log(
                        str(log_path), event_prefix, completion_event, required_events,
                        metrics, required_markers, forbidden_markers, str(executable)
                    )
                if report is None:
                    report = {"schema": REPORT_SCHEMA, "passed": False, "failures": []}
                report.setdefault("failures", []).append(
                    "game process exited before acceptance with code {}".format(process.returncode)
                )
                report.update(
                    passed=False,
                    request_id=request_id,
                    engine=engine,
                    process_id=process.pid,
                    process_running=False,
                )
                _write_report(report_path, report)
                raise AcceptanceFailure(report)
            if time.monotonic() - started >= timeout_seconds:
                _terminate_process_tree(process)
                if report is None:
                    report = {"schema": REPORT_SCHEMA, "passed": False, "failures": []}
                report.setdefault("failures", []).append(
                    "runtime acceptance timed out after {} seconds".format(timeout_seconds)
                )
                report.update(
                    passed=False,
                    request_id=request_id,
                    engine=engine,
                    process_id=process.pid,
                    process_running=False,
                )
                _write_report(report_path, report)
                raise AcceptanceFailure(report)
            time.sleep(0.25)
    except AcceptanceFailure:
        raise
    except Exception:
        _terminate_process_tree(process)
        raise
    finally:
        if output_stream is not None:
            output_stream.close()
