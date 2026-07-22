import importlib.util
import os
from pathlib import Path

import pytest


MODULE = Path(__file__).parents[1] / "skill/game-runtime-acceptance/scripts/_acceptance.py"
SPEC = importlib.util.spec_from_file_location("_acceptance", MODULE)
acceptance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(acceptance)


def _rules():
    return {
        "event_prefix": "[GAME]",
        "completion_event": {"event": "run_ended", "fields": {"result": "victory"}},
        "required_events": [
            {"event": "boss_spawned", "min_count": 3, "max_count": 3},
            {"event": "chest_opened", "min_count": 3},
        ],
        "metrics": [
            {"event": "snapshot", "field": "fps", "minimum": 50, "min_samples": 2},
            {"event": "snapshot", "field": "managed_mb", "maximum": 128, "min_samples": 2},
        ],
        "required_markers": ["engine=unity"],
        "forbidden_markers": ["NullReferenceException"],
    }


def _successful_log(path):
    path.write_text(
        "\n".join(
            [
                "[GAME] event=run_started engine=unity",
                "[GAME] event=boss_spawned tier=1",
                "[GAME] event=boss_spawned tier=2",
                "[GAME] event=boss_spawned tier=3",
                "[GAME] event=chest_opened tier=1",
                "[GAME] event=chest_opened tier=2",
                "[GAME] event=chest_opened tier=3",
                "[GAME] event=snapshot fps=60.3 managed_mb=0.9",
                "[GAME] event=snapshot fps=60.4 managed_mb=1.0",
                "[GAME] event=run_ended result=victory time=150.0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_evaluates_structured_milestones_metrics_and_hashes(tmp_path):
    log = tmp_path / "runtime.log"
    executable = tmp_path / "Game.exe"
    executable.write_bytes(b"game")
    _successful_log(log)
    report = acceptance.evaluate_log(
        str(log), executable_path=str(executable), **_rules()
    )
    assert report["passed"] is True
    assert report["event_counts"]["boss_spawned"] == 3
    assert report["metrics"][0]["observed_min"] == 60.3
    assert len(report["executable_sha256"]) == 64
    assert len(report["log_sha256"]) == 64


def test_reports_forbidden_marker_and_metric_failure(tmp_path):
    log = tmp_path / "runtime.log"
    _successful_log(log)
    log.write_text(
        log.read_text(encoding="utf-8")
        .replace("fps=60.3", "fps=12.0")
        + "NullReferenceException\n",
        encoding="utf-8",
    )
    report = acceptance.evaluate_log(str(log), **_rules())
    assert report["passed"] is False
    assert any("forbidden marker" in failure for failure in report["failures"])
    assert any("metric snapshot/fps" in failure for failure in report["failures"])


def test_rejects_evidence_inside_source(tmp_path):
    source = tmp_path / "build"
    source.mkdir()
    (source / "Game.exe").write_bytes(b"game")
    with pytest.raises(ValueError, match="outside source_directory"):
        acceptance._resolve_launch_paths(
            str(source), "Game.exe", str(source / "Evidence"),
            "01234567-89ab-4cde-8fab-0123456789ab",
        )


def test_launch_contract_uses_exact_executable_without_shell(tmp_path, monkeypatch):
    source = tmp_path / "build"
    source.mkdir()
    (source / "Game.exe").write_bytes(b"game")
    observed = {}

    class FakeProcess:
        pid = 4242
        returncode = None

        def poll(self):
            return None

    def fake_popen(command, **options):
        observed["command"] = command
        observed["shell"] = options["shell"]
        options["stdout"].write(
            "\n".join(
                [
                    "[GAME] event=run_started engine=unity",
                    "[GAME] event=boss_spawned tier=1",
                    "[GAME] event=boss_spawned tier=2",
                    "[GAME] event=boss_spawned tier=3",
                    "[GAME] event=chest_opened tier=1",
                    "[GAME] event=chest_opened tier=2",
                    "[GAME] event=chest_opened tier=3",
                    "[GAME] event=snapshot fps=60.3 managed_mb=0.9",
                    "[GAME] event=snapshot fps=60.4 managed_mb=1.0",
                    "[GAME] event=run_ended result=victory",
                ]
            ).encode("utf-8")
            + b"\n"
        )
        options["stdout"].flush()
        return FakeProcess()

    monkeypatch.setattr(acceptance.subprocess, "Popen", fake_popen)
    result = acceptance.run_acceptance(
        request_id="01234567-89ab-4cde-8fab-0123456789ab",
        source_directory=str(source),
        executable_relative_path="Game.exe",
        evidence_directory=str(tmp_path / "evidence"),
        engine="custom_stdout",
        arguments=["--validation"],
        timeout_seconds=5,
        leave_running_on_success=True,
        check_cancelled=None,
        **_rules(),
    )
    assert observed["shell"] is False
    assert observed["command"] == [str((source / "Game.exe").resolve()), "--validation"]
    assert result["process_id"] == 4242
    assert result["process_running"] is True


def test_acceptance_failure_terminates_the_exact_launched_process(tmp_path, monkeypatch):
    source = tmp_path / "build"
    source.mkdir()
    (source / "Game.exe").write_bytes(b"game")
    terminated = []

    class FakeProcess:
        pid = 4343
        returncode = None

        def poll(self):
            return None

    def fake_popen(_command, **options):
        options["stdout"].write(
            b"[GAME] event=run_started engine=unity\n"
            b"[GAME] event=run_ended result=victory\n"
        )
        options["stdout"].flush()
        return FakeProcess()

    monkeypatch.setattr(acceptance.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(
        acceptance, "_terminate_process_tree", lambda process: terminated.append(process.pid)
    )
    with pytest.raises(acceptance.AcceptanceFailure) as failure:
        acceptance.run_acceptance(
            request_id="11234567-89ab-4cde-8fab-0123456789ab",
            source_directory=str(source),
            executable_relative_path="Game.exe",
            evidence_directory=str(tmp_path / "evidence"),
            engine="custom_stdout",
            arguments=[],
            timeout_seconds=5,
            leave_running_on_success=True,
            check_cancelled=None,
            **_rules(),
        )
    assert terminated == [4343]
    assert failure.value.report["passed"] is False
    assert failure.value.report["process_running"] is False


@pytest.mark.skipif(os.name == "nt", reason="portable shebang probe is for POSIX CI")
def test_launches_without_shell_and_writes_request_scoped_report(tmp_path):
    source = tmp_path / "build"
    source.mkdir()
    executable = source / "Game.exe"
    executable.write_text(
        "#!/usr/bin/env python3\n"
        "import time\n"
        "print('[GAME] event=run_started engine=unity', flush=True)\n"
        "print('[GAME] event=boss_spawned tier=1', flush=True)\n"
        "print('[GAME] event=boss_spawned tier=2', flush=True)\n"
        "print('[GAME] event=boss_spawned tier=3', flush=True)\n"
        "print('[GAME] event=chest_opened tier=1', flush=True)\n"
        "print('[GAME] event=chest_opened tier=2', flush=True)\n"
        "print('[GAME] event=chest_opened tier=3', flush=True)\n"
        "print('[GAME] event=snapshot fps=60.3 managed_mb=0.9', flush=True)\n"
        "print('[GAME] event=snapshot fps=60.4 managed_mb=1.0', flush=True)\n"
        "print('[GAME] event=run_ended result=victory', flush=True)\n"
        "time.sleep(30)\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    request_id = "01234567-89ab-4cde-8fab-0123456789ab"
    result = acceptance.run_acceptance(
        request_id=request_id,
        source_directory=str(source),
        executable_relative_path="Game.exe",
        evidence_directory=str(tmp_path / "evidence"),
        engine="custom_stdout",
        arguments=[],
        timeout_seconds=10,
        leave_running_on_success=False,
        check_cancelled=None,
        **_rules(),
    )
    assert result["report"]["passed"] is True
    assert result["process_running"] is False
    assert Path(result["report_path"]).parent.name == request_id
    assert Path(result["report_path"]).is_file()
