"""SQCanvas Command-Line Interface (CLI).

Subcommands:
    sqcanvas [file] [--theme THEME] [--new-instance]  -> Launch CAD GUI (Default)
    sqcanvas export <script.py> [-o OUTPUT] [-f {gds,png,pdf,svg}] [--theme THEME] [--dpi DPI]
    sqcanvas inspect <script.py>                     -> Inspect chip geometry & components
    sqcanvas doctor                                   -> Diagnose environment & dependencies
"""

from __future__ import annotations

import argparse
import os
import platform
import sys
from collections.abc import Sequence
from pathlib import Path

from sqcanvas import __version__


def run_doctor() -> int:
    """Run an environment and dependency health check for SQCanvas."""
    print("=" * 60)
    print(f"[SQCanvas Doctor] Health Diagnostics (v{__version__})")
    print("=" * 60)

    # 1. System Platform
    os_name = platform.system()
    arch = platform.machine()
    py_ver = sys.version.split()[0]
    print(f"* Platform       : {os_name} ({arch})")
    print(f"* Python         : {py_ver} ({sys.executable})")

    # 2. Dependencies Checks
    packages = [
        ("shapely", "Geometric boolean & spatial engine"),
        ("numpy", "Numerical vector & tensor computing"),
        ("matplotlib", "CAD rendering & scientific export engine"),
        ("gdstk", "GDSII/OASIS semiconductor lithography engine"),
        ("PySide6", "Qt6 Desktop GUI Client"),
        ("IPython", "Jupyter/IPython interactive kernel (Optional)"),
    ]

    all_core_ok = True
    print("\n[Dependencies]")
    for pkg_name, desc in packages:
        try:
            mod = __import__(pkg_name)
            ver = getattr(mod, "__version__", "installed")
            print(f"  [OK]      {pkg_name:<12} : {ver:<12} ({desc})")
        except ImportError:
            is_optional = pkg_name in ("IPython",)
            if is_optional:
                print(f"  [OPTIONAL]{pkg_name:<12} : NOT INSTALLED ({desc})")
            else:
                all_core_ok = False
                print(f"  [MISSING] {pkg_name:<12} : MISSING ({desc})")

    # 3. GUI Environment Check
    print("\n[Display & GUI Environment]")
    if os.environ.get("SQCANVAS_HEADLESS_LOAD") == "1":
        print("  [INFO] Headless mode forced via SQCANVAS_HEADLESS_LOAD=1")
    else:
        try:
            from PySide6.QtWidgets import QApplication

            _app = QApplication.instance() or QApplication(["sqcanvas", "-platform", "offscreen"])
            print("  [OK] Qt6 GUI subsystem initialized successfully")
        except Exception as e:  # noqa: BLE001
            print(f"  [WARN] Qt6 GUI subsystem error: {e}")

    print("-" * 60)
    if all_core_ok:
        print("Status: ALL HEALTHY! Ready for quantum chip design.")
        return 0
    else:
        print("Status: Some required packages are missing.")
        print("Run: uv sync  (or: uv tool install --editable .) to repair.")
        return 1


def run_inspect(script_path: str) -> int:
    """Inspect a SQCanvas design script and print a detailed netlist summary."""
    from sqcanvas.codegen import ScriptLoadError, load_design_from_script

    path = Path(script_path).resolve()
    if not path.exists():
        print(f"[ERROR] Design script not found: {script_path}", file=sys.stderr)
        return 1

    print(f"[INFO] Loading SQCanvas design from: {path.name} ...")
    try:
        design = load_design_from_script(path)
    except ScriptLoadError as err:
        print(f"[ERROR] Script Load Error (Line {err.lineno}): {err.message}", file=sys.stderr)
        if err.traceback_text:
            print(err.traceback_text, file=sys.stderr)
        return 1
    except Exception as err:  # noqa: BLE001
        print(f"[ERROR] Unexpected Error while loading design: {err}", file=sys.stderr)
        return 1

    components = getattr(design, "components", {})
    records = getattr(getattr(design, "shapes", None), "records", [])

    print("=" * 65)
    print(f"Quantum Chip Design Summary: {path.name}")
    print("=" * 65)

    # Substrate & Dimensions
    chip_x = getattr(design, "chip_size_x", "N/A")
    chip_y = getattr(design, "chip_size_y", "N/A")
    print(f"* Substrate Die Size : {chip_x} x {chip_y}")
    print(f"* Total Components   : {len(components)}")
    print(f"* Total Shape Records: {len(records)}")

    # Bounding Box
    if records:
        all_polys = [r.geometry for r in records if r.geometry is not None]
        if all_polys:
            from shapely.ops import unary_union

            merged = unary_union(all_polys)
            minx, miny, maxx, maxy = merged.bounds
            print(
                f"* Physical Bounds    : X in [{minx:.1f} um, {maxx:.1f} um], Y in [{miny:.1f} um, {maxy:.1f} um]"
            )
            print(f"* Bounding Box Size  : {maxx - minx:.1f} um x {maxy - miny:.1f} um")

    # Component Breakdown
    if components:
        print("\nPlaced Component Netlist:")
        print(f"  {'#':<3} {'Name':<22} {'Type':<20} {'Position (X, Y)':<18}")
        print(f"  {'-'*3} {'-'*22} {'-'*20} {'-'*18}")
        for idx, (c_name, comp) in enumerate(components.items(), 1):
            c_type = type(comp).__name__
            opts = getattr(comp, "options", {})
            pos_x = opts.get("pos_x", "0um")
            pos_y = opts.get("pos_y", "0um")
            pos_str = f"({pos_x}, {pos_y})"
            print(f"  {idx:<3} {c_name:<22} {c_type:<20} {pos_str:<18}")

    print("=" * 65)
    return 0


def run_export(
    script_path: str,
    output: str | None = None,
    fmt: str | None = None,
    theme: str = "paper",
    dpi: int = 300,
    ground_plane: bool = True,
    ground_layer: int = 1,
) -> int:
    """Headlessly export a SQCanvas design to GDS, PNG, PDF, or SVG."""
    from sqcanvas.codegen import ScriptLoadError, load_design_from_script

    path = Path(script_path).resolve()
    if not path.exists():
        print(f"[ERROR] Script not found: {script_path}", file=sys.stderr)
        return 1

    # Infer format and output path
    if output:
        out_path = Path(output).resolve()
        if fmt is None:
            ext = out_path.suffix.lstrip(".").lower()
            fmt = ext if ext in ("gds", "png", "pdf", "svg") else "gds"
    else:
        fmt = fmt or "gds"
        out_path = path.with_suffix(f".{fmt}")

    print(f"[INFO] Loading design '{path.name}' for {fmt.upper()} export...")
    try:
        design = load_design_from_script(path)
    except ScriptLoadError as err:
        print(f"[ERROR] Script Load Error (Line {err.lineno}): {err.message}", file=sys.stderr)
        return 1
    except Exception as err:  # noqa: BLE001
        print(f"[ERROR] Load error: {err}", file=sys.stderr)
        return 1

    try:
        if fmt == "gds":
            from sqcanvas.exporters import export_gds

            export_gds(
                design,
                filepath=out_path,
                ground_plane=ground_plane,
                ground_layer=ground_layer,
            )
            print(f"[OK] GDSII mask successfully exported to: {out_path}")
        elif fmt in ("png", "pdf", "svg"):
            from sqcanvas.exporters.mpl import export_scene

            fig = export_scene(design, theme=theme)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
            import matplotlib.pyplot as plt

            plt.close(fig)
            print(f"[OK] {fmt.upper()} visualization successfully exported to: {out_path}")
        else:
            print(f"[ERROR] Unsupported export format: {fmt}", file=sys.stderr)
            return 1
        return 0
    except Exception as err:  # noqa: BLE001
        print(f"[ERROR] Export failed: {err}", file=sys.stderr)
        return 1


def _get_gui_python_executable() -> str:
    """Return pythonw.exe on Windows to ensure zero console window popup."""
    if sys.platform == "win32":
        py_path = Path(sys.executable)
        pythonw = py_path.with_name("pythonw.exe")
        if pythonw.exists():
            return str(pythonw)
    return sys.executable


def main(argv: Sequence[str] | None = None) -> None:
    """Main CLI entry point for SQCanvas."""
    if argv is None:
        argv = sys.argv[1:]

    # Check for direct top-level subcommands
    first_arg = argv[0] if argv else None

    # Handle doctor subcommand
    if first_arg == "doctor":
        sys.exit(run_doctor())

    # Handle inspect subcommand
    if first_arg == "inspect":
        parser = argparse.ArgumentParser(
            prog="sqcanvas inspect",
            description="Inspect a SQCanvas design script and display netlist & geometry statistics.",
        )
        parser.add_argument("script", help="Path to Python design script (.py) to inspect.")
        args = parser.parse_args(argv[1:])
        sys.exit(run_inspect(args.script))

    # Handle export subcommand
    if first_arg == "export":
        parser = argparse.ArgumentParser(
            prog="sqcanvas export",
            description="Headlessly export a SQCanvas design script to GDSII or image figures.",
        )
        parser.add_argument("script", help="Path to Python design script (.py) to export.")
        parser.add_argument("-o", "--output", default=None, help="Output destination filepath.")
        parser.add_argument(
            "-f",
            "--format",
            choices=["gds", "png", "pdf", "svg"],
            default=None,
            help="Target export format (default: inferred from output or 'gds').",
        )
        parser.add_argument(
            "--theme",
            default="paper",
            help="Scientific color theme for image figures (e.g. paper, cyber, nordic, aurora).",
        )
        parser.add_argument(
            "--dpi", type=int, default=300, help="Image resolution DPI (default: 300)."
        )
        parser.add_argument(
            "--ground-plane",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Enable/disable ground plane polygon subtraction for GDS export.",
        )
        parser.add_argument(
            "--ground-layer",
            type=int,
            default=1,
            help="GDS layer number for the ground plane (default: 1).",
        )
        args = parser.parse_args(argv[1:])
        sys.exit(
            run_export(
                script_path=args.script,
                output=args.output,
                fmt=args.format,
                theme=args.theme,
                dpi=args.dpi,
                ground_plane=args.ground_plane,
                ground_layer=args.ground_layer,
            )
        )

    # Otherwise: GUI mode (default behavior)
    parser = argparse.ArgumentParser(
        prog="sqcanvas",
        description="SQCanvas — Desktop CAD Studio & Parametric EDA for Superconducting Quantum Chips.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Optional path to a Python design script (.py) to open immediately.",
    )
    parser.add_argument(
        "--foreground",
        "--fg",
        action="store_true",
        help="Run GUI attached in the current terminal foreground.",
    )
    parser.add_argument(
        "--_gui-worker",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--theme",
        "-t",
        default=None,
        help="Initial CAD color theme preset (e.g. cyber, nordic, aurora, paper, etc.).",
    )
    parser.add_argument(
        "--new-instance",
        action="store_true",
        help="Force launching a fresh new GUI window instead of joining existing window as a tab.",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args(argv)

    # 1. Try to join an existing instance as a new tab via IPC
    is_worker = getattr(args, "_gui_worker", False)
    if not args.new_instance and not is_worker and os.environ.get("SQCANVAS_HEADLESS_LOAD") != "1":
        from sqcanvas.gui import _try_send_to_existing_instance

        resolved_file = str(Path(args.file).resolve()) if args.file else None
        if _try_send_to_existing_instance(filepath=resolved_file, theme=args.theme):
            target_desc = f" and opened '{Path(args.file).name}'" if args.file else ""
            print(f"[INFO] Activated existing SQCanvas CAD window{target_desc}.")
            return

    # 2. Launch detached background process using pythonw.exe by default (no console popup!)
    if not args.foreground and not is_worker and os.environ.get("SQCANVAS_HEADLESS_LOAD") != "1":
        import subprocess

        gui_py = _get_gui_python_executable()
        cmd = [gui_py, "-m", "sqcanvas.cli", "--_gui-worker", *argv]

        if sys.platform == "win32":
            creationflags = (
                subprocess.DETACHED_PROCESS
                | subprocess.CREATE_NEW_PROCESS_GROUP
                | getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            )
            proc = subprocess.Popen(
                cmd,
                creationflags=creationflags,
                close_fds=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
        else:
            proc = subprocess.Popen(
                cmd,
                start_new_session=True,
                close_fds=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )

        target_desc = f" for '{args.file}'" if args.file else ""
        print(f"[INFO] SQCanvas CAD Studio launched in background{target_desc} (PID: {proc.pid}).")
        return

    from sqcanvas.gui import run_gui_with_ipc

    run_gui_with_ipc(
        file=args.file,
        theme=args.theme,
        new_instance=args.new_instance,
    )


if __name__ == "__main__":
    main()


