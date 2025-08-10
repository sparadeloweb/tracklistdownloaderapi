from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from pathlib import Path
import sys
import shutil as _shutil
from typing import List, Optional


SUPPORTED_AUDIO_SUFFIXES = {".mp3", ".m4a", ".opus", ".flac", ".wav", ".ogg"}


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _resolve_scdl_executable() -> str:
    """Return absolute path to scdl console executable inside current venv if available,
    otherwise fall back to PATH lookup. On Windows, prefers scdl.exe/scdl.cmd.
    """
    python_path = Path(sys.executable)
    candidates = []
    # venv Scripts directory on Windows, bin on POSIX
    scripts_dir = python_path.parent
    candidates.append(scripts_dir / "scdl.exe")
    candidates.append(scripts_dir / "scdl.cmd")
    candidates.append(scripts_dir / "scdl")
    for cand in candidates:
        if cand.exists():
            return str(cand)
    found = _shutil.which("scdl")
    if found:
        return found
    # Last resort: will likely fail, but be explicit
    return "scdl"


def run_scdl(
    url: str,
    output_parent_dir: Path,
    *,
    only_mp3: bool = True,
    prefer_opus: bool = False,
    auth_token: Optional[str] = None,
    additional_args: Optional[List[str]] = None,
    timeout_sec: int = 900,
) -> List[Path]:
    """Download using scdl into a unique subfolder and return downloaded audio files.

    Creates a per-invocation subdirectory to isolate artifacts (covers, txt, etc.).
    """

    _ensure_directory(output_parent_dir)
    request_dir = output_parent_dir / f"scdl_{uuid.uuid4().hex}"
    _ensure_directory(request_dir)

    scdl_exec = _resolve_scdl_executable()
    cmd: List[str] = [
        scdl_exec,
        "-l",
        url,
        "--path",
        str(request_dir),
        "--hide-progress",
    ]

    # Format preferences: choose one.
    if prefer_opus and not only_mp3:
        cmd.append("--opus")
    elif only_mp3:
        cmd.append("--onlymp3")

    if additional_args:
        cmd.extend(additional_args)

    if auth_token:
        cmd.extend(["--auth-token", auth_token])

    env = os.environ.copy()
    if auth_token and not env.get("SCDL_AUTH_TOKEN"):
        env["SCDL_AUTH_TOKEN"] = auth_token

    process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout_sec,
        check=False,
        env=env,
    )

    if process.returncode != 0:
        # Surface scdl output to caller for troubleshooting
        raise RuntimeError(f"scdl failed (code {process.returncode}):\n{process.stdout}")

    # Collect audio files produced
    audio_files: List[Path] = []
    for path in request_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_SUFFIXES:
            audio_files.append(path)

    if not audio_files:
        raise RuntimeError("No audio files were produced by scdl for the given URL.")

    return audio_files


def cleanup_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


