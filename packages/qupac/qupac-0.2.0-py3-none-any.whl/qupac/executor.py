from __future__ import annotations

import os
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import Optional

from .parser import parse_qupac
from .transpiler import transpile_to_python


def _write_temp_py(code: str, base_dir: Path, stem: str = "qupac_gen") -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=f"{stem}_", suffix=".py", dir=str(base_dir))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(code)
    return Path(tmp_path)


def run_python_code_bg(code: str, workdir: Path, log_path: Optional[Path] = None, python_exe: Optional[Path] = None) -> int:
    """Run generated Python code in the background. Returns the spawned PID.

    On Windows, we detach the process so the CLI returns immediately.
    Output is redirected to log_path if provided; otherwise to NUL.
    """
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    tmp_py = _write_temp_py(code, base_dir=workdir)

    if log_path is None:
        # Default log next to script
        log_path = tmp_py.with_suffix(".log")

    # Open log file for both stdout and stderr
    log_fh = open(log_path, "a", encoding="utf-8")

    creationflags = 0
    startupinfo = None
    kwargs = {}

    if os.name == "nt":
        # Windows specific flags to detach
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        creationflags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        # Hide console window popup if any
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    else:
        kwargs["start_new_session"] = True  # Unix: detach from current session

    py = str(python_exe) if python_exe else sys.executable

    # Log header for easier diagnostics
    try:
        log_fh.write(f"[Qupac] Starting: {py} {tmp_py}\n")
        log_fh.flush()
    except Exception:
        pass

    proc = subprocess.Popen(  # type: ignore[call-overload]
        [py, str(tmp_py)],
        cwd=str(workdir),
        stdout=log_fh,
        stderr=log_fh,
        creationflags=creationflags,
        startupinfo=startupinfo,
        **kwargs,
    )
    # We do not wait; we leave the log file open so output is flushed; but we can close safely
    log_fh.close()
    return proc.pid


def run_python_code_fg(code: str, workdir: Path, python_exe: Optional[Path] = None) -> int:
    """Run generated Python code in the foreground (blocking). Returns exit code."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    tmp_py = _write_temp_py(code, base_dir=workdir)
    py = str(python_exe) if python_exe else sys.executable
    proc = subprocess.run([py, str(tmp_py)], cwd=str(workdir))
    return proc.returncode


def run_qupac_file(
    file_path: str | Path,
    background: bool = True,
    log_path: Optional[str | Path] = None,
    python_exe: Optional[str | Path] = None,
) -> int:
    """Parse and transpile a Qupac file, then execute the generated Python.

    Returns PID if background=True, otherwise returns the exit code.
    """
    src_path = Path(file_path)
    ir = parse_qupac(src_path)
    code = transpile_to_python(ir)

    run_dir = src_path.parent / ".qupac_build"
    run_dir.mkdir(parents=True, exist_ok=True)

    py_path = Path(python_exe) if python_exe else None

    if background:
        pid = run_python_code_bg(code, workdir=run_dir, log_path=Path(log_path) if log_path else None, python_exe=py_path)
        return pid
    else:
        rc = run_python_code_fg(code, workdir=run_dir, python_exe=py_path)
        return rc
