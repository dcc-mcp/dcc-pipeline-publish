"""Engine-neutral Windows game release packaging."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import uuid
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple


PROFILES = {"installer", "steam", "wegame"}
CONTENT_LICENSE_MODES = {"original_only", "third_party_notices"}
MAX_NOTICES_BYTES = 2 * 1024 * 1024


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_inputs(
    source_directory: str,
    executable_relative_path: str,
    output_directory: str,
) -> Tuple[Path, Path, Path]:
    source = Path(source_directory).expanduser().resolve()
    if not source.is_dir():
        raise FileNotFoundError("Prebuilt game directory not found: {}".format(source))

    relative_executable = Path(executable_relative_path)
    if relative_executable.is_absolute() or ".." in relative_executable.parts:
        raise ValueError("executable_relative_path must stay inside source_directory")
    executable = (source / relative_executable).resolve()
    if source not in executable.parents or executable.suffix.lower() != ".exe" or not executable.is_file():
        raise FileNotFoundError("Windows game executable not found under source_directory")

    output = Path(output_directory).expanduser().resolve()
    if output == source or source in output.parents:
        raise ValueError("output_directory must be outside source_directory")
    return source, executable, output


def _release_metadata(
    product_name: str,
    product_version: str,
    publisher: str,
    default_name: str,
) -> Tuple[str, str, str]:
    resolved_name = product_name.strip() or default_name
    resolved_publisher = publisher.strip() or resolved_name
    values = {
        "product_name": resolved_name,
        "product_version": product_version.strip(),
        "publisher": resolved_publisher,
    }
    for field_name, value in values.items():
        if not value or any(character in value for character in "\r\n\0"):
            raise ValueError("{} must be a non-empty single line".format(field_name))
    return values["product_name"], values["product_version"], values["publisher"]


def _resolve_license_evidence(
    source: Path,
    content_license_mode: str,
    third_party_notices_relative_path: str,
) -> Optional[Dict[str, object]]:
    if content_license_mode not in CONTENT_LICENSE_MODES:
        raise ValueError(
            "content_license_mode must be one of: {}".format(
                ", ".join(sorted(CONTENT_LICENSE_MODES))
            )
        )

    raw_notices_path = third_party_notices_relative_path.strip()
    if content_license_mode == "original_only":
        if raw_notices_path:
            raise ValueError(
                "third_party_notices_relative_path requires third_party_notices mode"
            )
        return None

    if not raw_notices_path:
        raise ValueError(
            "third_party_notices_relative_path is required for third_party_notices mode"
        )
    relative_path = Path(raw_notices_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("third_party_notices_relative_path must stay inside source_directory")
    notices_path = (source / relative_path).resolve()
    if source not in notices_path.parents:
        raise ValueError("third_party_notices_relative_path must stay inside source_directory")
    if notices_path.suffix.lower() not in {".md", ".txt"}:
        raise ValueError("third-party notices must be a .md or .txt file")
    if not notices_path.is_file():
        raise FileNotFoundError("Third-party notices file not found under source_directory")
    size = notices_path.stat().st_size
    if size <= 0 or size > MAX_NOTICES_BYTES:
        raise ValueError("third-party notices must be non-empty and no larger than 2 MiB")
    return {
        "relative_path": str(notices_path.relative_to(source)).replace("\\", "/"),
        "bytes": size,
        "sha256": _sha256(notices_path),
    }


def _write_license_provenance(
    source: Path,
    executable: Path,
    output: Path,
    product_name: str,
    product_version: str,
    content_license_mode: str,
    third_party_notices: Optional[Dict[str, object]],
) -> Path:
    provenance = output / "license-provenance.json"
    provenance.write_text(
        json.dumps(
            {
                "schema": "dcc-mcp.game-release.license-provenance.v1",
                "product_name": product_name,
                "product_version": product_version,
                "executable": str(executable.relative_to(source)).replace("\\", "/"),
                "executable_sha256": _sha256(executable),
                "content_license_mode": content_license_mode,
                "third_party_notices": third_party_notices,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return provenance


def _resolve_iscc(raw_path: str) -> Path:
    candidates = [Path(raw_path).expanduser()] if raw_path else []
    discovered = shutil.which("ISCC.exe") or shutil.which("iscc")
    if discovered:
        candidates.append(Path(discovered))
    for variable in ("ProgramFiles(x86)", "ProgramFiles"):
        root = os.environ.get(variable)
        if root:
            candidates.append(Path(root) / "Inno Setup 6" / "ISCC.exe")
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "Programs" / "Inno Setup 6" / "ISCC.exe")
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError("Inno Setup 6 ISCC.exe was not found")


def _inno_value(value: str) -> str:
    return value.replace("{", "{{").replace('"', '""')


def _windows_file_version(value: str) -> str:
    parts = value.split(".")
    if not 1 <= len(parts) <= 4 or not all(part.isdigit() for part in parts):
        return "1.0.0.0"
    return ".".join(parts + ["0"] * (4 - len(parts)))


def _safe_file_component(value: str, fallback: str) -> str:
    sanitized = "".join(character if character.isalnum() or character in "-_." else "-" for character in value)
    return sanitized.strip("-.") or fallback


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


def _run_logged(
    command: Sequence[str],
    cwd: Path,
    log_path: Path,
    check_cancelled: Optional[Callable[[], None]],
) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    process_options = {}
    if os.name == "nt":
        process_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        process_options["start_new_session"] = True
    with log_path.open("wb") as log:
        log.write(("command: " + subprocess.list2cmdline(list(command)) + "\n\n").encode("utf-8"))
        log.flush()
        process = subprocess.Popen(
            list(command),
            cwd=str(cwd),
            stdout=log,
            stderr=subprocess.STDOUT,
            **process_options,
        )
        try:
            while process.poll() is None:
                if check_cancelled is not None:
                    check_cancelled()
                try:
                    process.wait(timeout=0.25)
                except subprocess.TimeoutExpired:
                    continue
        except Exception:
            _terminate_process_tree(process)
            raise
    return int(process.returncode or 0)


def _write_installer_script(
    source: Path,
    executable: Path,
    installer_dir: Path,
    product_name: str,
    product_version: str,
    publisher: str,
    vc_redist: Optional[Path],
) -> Tuple[Path, Path]:
    relative_executable = executable.relative_to(source)
    safe_product_name = _safe_file_component(product_name, "Game")
    base_name = "{}-Setup-{}".format(
        safe_product_name,
        _safe_file_component(product_version, "1.0.0"),
    )
    installer = installer_dir / "{}.exe".format(base_name)
    app_id = uuid.uuid5(uuid.NAMESPACE_URL, "dcc-mcp-game-release:{}:{}".format(publisher, product_name))
    prerequisite_file = ""
    prerequisite_run = ""
    if vc_redist is not None:
        prerequisite_file = (
            'Source: "{}"; DestDir: "{{tmp}}"; DestName: "vc_redist.x64.exe"; '
            "Flags: ignoreversion deleteafterinstall"
        ).format(_inno_value(str(vc_redist)))
        prerequisite_run = (
            'Filename: "{{tmp}}\\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; '
            "Flags: runhidden waituntilterminated"
        )
    script = installer_dir / "game-installer.iss"
    script.write_text(
        """[Setup]
AppId=dcc-mcp-game-release-{app_id}
AppName={product_name}
AppVersion={product_version}
AppPublisher={publisher}
VersionInfoVersion={version_info_version}
VersionInfoCompany={publisher}
VersionInfoProductName={product_name}
VersionInfoProductVersion={product_version}
DefaultDirName={{autopf}}\\{install_directory}
DefaultGroupName={product_name}
OutputDir={output_dir}
OutputBaseFilename={base_name}
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "{source}\\*"; DestDir: "{{app}}"; Excludes: "*.pdb"; Flags: ignoreversion recursesubdirs createallsubdirs
{prerequisite_file}

[Icons]
Name: "{{autoprograms}}\\{product_name}"; Filename: "{{app}}\\{executable}"
Name: "{{autodesktop}}\\{product_name}"; Filename: "{{app}}\\{executable}"; Tasks: desktopicon

[Run]
{prerequisite_run}
Filename: "{{app}}\\{executable}"; Description: "Launch {product_name}"; Flags: nowait postinstall skipifsilent
""".format(
            app_id=app_id,
            product_name=_inno_value(product_name),
            install_directory=_inno_value(safe_product_name),
            product_version=_inno_value(product_version),
            publisher=_inno_value(publisher),
            version_info_version=_windows_file_version(product_version),
            output_dir=_inno_value(str(installer_dir)),
            base_name=_inno_value(base_name),
            source=_inno_value(str(source)),
            executable=_inno_value(str(relative_executable)),
            prerequisite_file=prerequisite_file,
            prerequisite_run=prerequisite_run,
        ),
        encoding="utf-8-sig",
    )
    return script, installer


def _build_installer(
    source: Path,
    executable: Path,
    output: Path,
    product_name: str,
    product_version: str,
    publisher: str,
    compiler: Path,
    vc_redist: Optional[Path],
    check_cancelled: Optional[Callable[[], None]],
) -> List[Path]:
    installer_dir = output / "Installer"
    installer_dir.mkdir(parents=True, exist_ok=True)
    script, installer = _write_installer_script(
        source, executable, installer_dir, product_name, product_version, publisher, vc_redist
    )
    log_path = installer_dir / "build-installer.log"
    return_code = _run_logged([str(compiler), str(script)], output, log_path, check_cancelled)
    if return_code or not installer.is_file():
        raise RuntimeError("Inno Setup failed; inspect {}".format(log_path))
    return [installer, script, log_path]


def _write_steam_pipe(
    source: Path,
    output: Path,
    product_name: str,
    product_version: str,
    app_id: str,
    depot_id: str,
) -> List[Path]:
    if not app_id.isdigit() or not depot_id.isdigit():
        raise ValueError("steam_app_id and steam_depot_id must contain digits only")
    root = output / "SteamPipe"
    scripts = root / "scripts"
    build_output = root / "output"
    scripts.mkdir(parents=True, exist_ok=True)
    build_output.mkdir(parents=True, exist_ok=True)
    depot = scripts / "depot_build_{}.vdf".format(depot_id)
    app = scripts / "app_build_{}.vdf".format(app_id)
    depot.write_text(
        '''"DepotBuildConfig"
{{
    "DepotID" "{depot_id}"
    "ContentRoot" "{content_root}"
    "FileMapping"
    {{
        "LocalPath" "*"
        "DepotPath" "."
        "recursive" "1"
    }}
    "FileExclusion" "*.pdb"
}}
'''.format(depot_id=depot_id, content_root=str(source).replace("\\", "/")),
        encoding="utf-8",
    )
    app.write_text(
        '''"AppBuild"
{{
    "AppID" "{app_id}"
    "Desc" "{description}"
    "BuildOutput" "{build_output}"
    "ContentRoot" "{content_root}"
    "Preview" "1"
    "Depots"
    {{
        "{depot_id}" "{depot_script}"
    }}
}}
'''.format(
            app_id=app_id,
            description="{} {}".format(product_name, product_version).replace('"', "'"),
            build_output=str(build_output).replace("\\", "/"),
            content_root=str(source).replace("\\", "/"),
            depot_id=depot_id,
            depot_script=depot.name,
        ),
        encoding="utf-8",
    )
    readme = root / "README.txt"
    readme.write_text(
        'Run steamcmd +login <account> +run_app_build "{}" +quit.\n'
        "Keep Preview=1 until the build is verified. Configure required redistributables "
        "in Steamworks before release.\n".format(app),
        encoding="utf-8",
    )
    return [app, depot, readme]


def _write_wegame_preflight(
    source: Path,
    executable: Path,
    output: Path,
    product_name: str,
    product_version: str,
) -> List[Path]:
    root = output / "WeGame"
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / "release-preflight.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "dcc-mcp.game-release.wegame-preflight.v1",
                "product_name": product_name,
                "product_version": product_version,
                "content_root": os.path.relpath(str(source), str(root)).replace("\\", "/"),
                "executable": str(executable.relative_to(source)).replace("\\", "/"),
                "executable_sha256": _sha256(executable),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    readme = root / "README.txt"
    readme.write_text(
        "This directory is a local preflight record, not a WeGame-owned manifest.\n"
        "Obtain project approval, integrate the Rail SDK, test with the developer client, "
        "then upload through the authenticated developer portal.\n"
        "Developer portal: https://developer.wegame.com/\n",
        encoding="utf-8",
    )
    return [manifest, readme]


def package_release(
    source_directory: str,
    executable_relative_path: str,
    output_directory: str,
    release_profile: str,
    content_license_mode: str = "",
    third_party_notices_relative_path: str = "",
    product_name: str = "",
    product_version: str = "1.0.0",
    publisher: str = "",
    installer_compiler_path: str = "",
    vc_redist_path: str = "",
    steam_app_id: str = "",
    steam_depot_id: str = "",
    check_cancelled: Optional[Callable[[], None]] = None,
) -> Dict[str, object]:
    if release_profile not in PROFILES:
        raise ValueError("release_profile must be one of: {}".format(", ".join(sorted(PROFILES))))
    source, executable, output = _resolve_inputs(
        source_directory, executable_relative_path, output_directory
    )
    resolved_name, resolved_version, resolved_publisher = _release_metadata(
        product_name, product_version, publisher, executable.stem
    )
    third_party_notices = _resolve_license_evidence(
        source,
        content_license_mode,
        third_party_notices_relative_path,
    )
    output.mkdir(parents=True, exist_ok=True)

    if release_profile == "installer":
        compiler = _resolve_iscc(installer_compiler_path)
        vc_redist = Path(vc_redist_path).expanduser().resolve() if vc_redist_path else None
        if vc_redist is not None and not vc_redist.is_file():
            raise FileNotFoundError("VC++ redistributable not found: {}".format(vc_redist))
        artifacts = _build_installer(
            source,
            executable,
            output,
            resolved_name,
            resolved_version,
            resolved_publisher,
            compiler,
            vc_redist,
            check_cancelled,
        )
        prompt = "Install and smoke-test the Setup executable on a clean Windows machine."
    elif release_profile == "steam":
        artifacts = _write_steam_pipe(
            source, output, resolved_name, resolved_version, steam_app_id, steam_depot_id
        )
        prompt = "Review the preview VDF, test it, then use an approved authenticated SteamCMD session."
    else:
        artifacts = _write_wegame_preflight(
            source, executable, output, resolved_name, resolved_version
        )
        prompt = "Complete Rail SDK testing before authenticated WeGame portal submission."

    license_provenance = _write_license_provenance(
        source,
        executable,
        output,
        resolved_name,
        resolved_version,
        content_license_mode,
        third_party_notices,
    )
    artifacts.append(license_provenance)

    return {
        "prompt": prompt,
        "artifacts": [str(path) for path in artifacts],
        "release_profile": release_profile,
        "source_directory": str(source),
        "game_executable_path": str(executable),
        "output_directory": str(output),
        "content_license_mode": content_license_mode,
        "third_party_notices": third_party_notices,
        "license_provenance_path": str(license_provenance),
    }
