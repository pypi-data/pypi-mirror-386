from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from .executor import run_qupac_file
from .parser import parse_qupac
from .transpiler import transpile_to_python


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="qupac",
        description="Qupac: compile and run .qu files with Qiskit (background by default)",
    )
    p.add_argument("file", help="Path to Qupac source (.qu)")
    p.add_argument("--fg", action="store_true", help="Run in foreground (block until finished)")
    p.add_argument("--log", help="Optional log file path (background mode). Default: .qupac_build/<source>.log")
    p.add_argument("--python", help="Path to Python interpreter to use (helpful if Qiskit is installed in a different env)")
    p.add_argument("--precheck", action="store_true", help="Preflight check that qiskit and qiskit_aer can be imported with the chosen Python")
    p.add_argument("--emit", action="store_true", help="Only transpile and print the generated Python (no execution)")
    return p


def _precheck_python(py: Path) -> bool:
    try:
        proc = subprocess.run(
            [str(py), "-c", "import qiskit, qiskit_aer; print('OK')"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0 and "OK" in proc.stdout:
            return True
        else:
            print(proc.stdout)
            print(proc.stderr)
            return False
    except Exception as e:
        print(f"Precheck failed to execute: {e}")
        return False


def main(argv: list[str] | None = None) -> int:
    ap = _build_parser()
    args = ap.parse_args(argv)

    src = Path(args.file)
    if not src.exists():
        ap.error(f"File not found: {src}")

    if args.emit:
        ir = parse_qupac(src)
        code = transpile_to_python(ir)
        print(code)
        return 0

    py_path = Path(args.python).resolve() if args.python else None

    if args.precheck:
        py_for_check = py_path if py_path else Path("python")
        print(f"Prechecking Python: {py_for_check}")
        ok = _precheck_python(py_for_check)
        if not ok:
            print("Precheck failed: qiskit and/or qiskit_aer not importable in the selected Python. Use --python to select the correct interpreter or install dependencies.")
            return 1
        else:
            print("Precheck passed.")

    if args.fg:
        if py_path:
            print(f"Using Python: {py_path}")
        rc = run_qupac_file(src, background=False, python_exe=py_path)
        return rc
    else:
        # Determine default log path if not provided
        if args.log:
            log_path = Path(args.log)
        else:
            log_path = (src.parent / ".qupac_build" / f"{src.stem}.log").resolve()
        pid = run_qupac_file(src, background=True, log_path=log_path, python_exe=py_path)
        if py_path:
            print(f"Started background Python (PID {pid}). Log: {log_path}\nUsing Python: {py_path}")
        else:
            print(f"Started background Python (PID {pid}). Log: {log_path}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
