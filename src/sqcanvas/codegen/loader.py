"""Script loader and fault-tolerant diagnostic engine for SQCanvas Python scripts."""

from __future__ import annotations

import os
import runpy
import sys
import traceback
from pathlib import Path
from typing import Any

from sqcanvas.designs.design_base import Design


class ScriptLoadError(Exception):
    """Exception raised when loading a SQCanvas Python script fails."""

    def __init__(
        self,
        message: str,
        *,
        filepath: Path | str,
        line_number: int | None = None,
        error_type: str = "ScriptError",
        code_snippet: str | None = None,
        traceback_str: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.filepath = Path(filepath)
        self.line_number = line_number
        self.error_type = error_type
        self.code_snippet = code_snippet
        self.traceback_str = traceback_str

    def format_diagnostic_report(self) -> str:
        """Return a structured, human-readable error diagnostic report."""
        report = [
            f"❌ [{self.error_type}] Failed to load: {self.filepath.name}",
            f"File: {self.filepath}",
        ]
        if self.line_number is not None:
            report.append(f"Line: {self.line_number}")
        report.append(f"Details: {self.message}")

        if self.code_snippet:
            report.append("\nCode Context:")
            report.append(self.code_snippet)

        if self.traceback_str:
            report.append("\nTraceback:")
            report.append(self.traceback_str)

        return "\n".join(report)


def _extract_error_details(exc: Exception, filepath: Path) -> dict[str, Any]:
    """Extract line number, snippet, and traceback from an execution exception."""
    err_type = type(exc).__name__
    msg = str(exc)
    line_no = None
    snippet = None

    if isinstance(exc, SyntaxError):
        line_no = exc.lineno
        if exc.text:
            snippet = f"  Line {line_no}: {exc.text.rstrip()}"
            if exc.offset:
                snippet += "\n" + " " * (exc.offset + 9) + "^"
    else:
        # Extract line from traceback matching target filepath
        tb = exc.__traceback__
        extracted = traceback.extract_tb(tb)
        target_str = str(filepath.resolve())

        for frame in reversed(extracted):
            if Path(frame.filename).resolve() == Path(target_str):
                line_no = frame.lineno
                if frame.line:
                    snippet = f"  Line {line_no}: {frame.line.strip()}"
                break

    tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    return {
        "error_type": err_type,
        "message": msg,
        "line_number": line_no,
        "code_snippet": snippet,
        "traceback_str": tb_str,
    }


def load_design_from_script(filepath: str | Path) -> Design:
    """Execute a Python script and extract its SQCanvas Design instance with error diagnostics."""
    path = Path(filepath).resolve()
    if not path.exists():
        raise ScriptLoadError(
            f"File not found: '{path}'",
            filepath=path,
            error_type="FileNotFoundError",
        )

    # Prepend directory to sys.path so sibling imports in script resolve properly
    script_dir = str(path.parent)
    sys_path_modified = False
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
        sys_path_modified = True

    prev_headless = os.environ.get("SQCANVAS_HEADLESS_LOAD")
    os.environ["SQCANVAS_HEADLESS_LOAD"] = "1"
    try:
        try:
            context = runpy.run_path(str(path), run_name="__main__")
        except Exception as e:
            details = _extract_error_details(e, path)
            raise ScriptLoadError(
                message=details["message"],
                filepath=path,
                line_number=details["line_number"],
                error_type=details["error_type"],
                code_snippet=details["code_snippet"],
                traceback_str=details["traceback_str"],
            ) from e
        finally:
            if sys_path_modified:
                try:
                    sys.path.remove(script_dir)
                except ValueError:
                    pass

        # 1. Look for known factory builder functions
        for func_name in ("build_design", "make_design", "create_design", "get_design"):
            if func_name in context and callable(context[func_name]):
                try:
                    res = context[func_name]()
                    if isinstance(res, Design):
                        return res
                except Exception as e:
                    details = _extract_error_details(e, path)
                    raise ScriptLoadError(
                        message=f"Error executing factory '{func_name}()': {details['message']}",
                        filepath=path,
                        line_number=details["line_number"],
                        error_type=details["error_type"],
                        code_snippet=details["code_snippet"],
                        traceback_str=details["traceback_str"],
                    ) from e
    finally:
        if prev_headless is None:
            os.environ.pop("SQCANVAS_HEADLESS_LOAD", None)
        else:
            os.environ["SQCANVAS_HEADLESS_LOAD"] = prev_headless

    # 2. Look for global variables of type Design
    for var_name in ("design", "d", "layout", "chip", "main_design"):
        if var_name in context and isinstance(context[var_name], Design):
            return context[var_name]

    # 3. Fallback search through all values in context
    for var_name, val in context.items():
        if isinstance(val, Design):
            return val

    raise ScriptLoadError(
        "No SQCanvas Design instance found in script. Define a 'build_design()' function or a global 'design = PlanarDesign()' variable.",
        filepath=path,
        error_type="DesignNotFoundError",
    )
