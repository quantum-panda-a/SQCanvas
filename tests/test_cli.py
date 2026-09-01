import pytest

from sqcanvas import __version__
from sqcanvas.cli import main
from sqcanvas.gui import _try_send_to_existing_instance


@pytest.fixture
def sample_script(tmp_path):
    script_path = tmp_path / "sample_quantum_chip.py"
    script_content = """
from sqcanvas.designs import PlanarDesign
from sqcanvas.components import DualPadTransmon, Launchpad

design = PlanarDesign()
DualPadTransmon(design, name="Q1", options={"pos_x": "0um", "pos_y": "0um"})
Launchpad(design, name="P1", options={"pos_x": "1000um", "pos_y": "500um"})
"""
    script_path.write_text(script_content, encoding="utf-8")
    return script_path


def test_cli_version(capsys):
    """Test that `sqcanvas --version` displays the version and exits cleanly."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert __version__ in captured.out or __version__ in captured.err


def test_cli_help(capsys):
    """Test that `sqcanvas --help` displays help text and exits cleanly."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "SQCanvas" in captured.out
    assert "--theme" in captured.out


def test_cli_invalid_arg():
    """Test that unrecognized CLI arguments raise SystemExit with code 2."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--unknown-option-xyz"])
    assert exc_info.value.code == 2


def test_cli_doctor(capsys):
    """Test that `sqcanvas doctor` checks dependencies and prints healthy report."""
    with pytest.raises(SystemExit) as exc_info:
        main(["doctor"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "SQCanvas Doctor" in captured.out
    assert "shapely" in captured.out
    assert "gdstk" in captured.out
    assert "PySide6" in captured.out


def test_cli_inspect(sample_script, capsys):
    """Test that `sqcanvas inspect <file.py>` prints chip statistics and netlist."""
    with pytest.raises(SystemExit) as exc_info:
        main(["inspect", str(sample_script)])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Quantum Chip Design Summary" in captured.out
    assert "Q1" in captured.out
    assert "DualPadTransmon" in captured.out
    assert "P1" in captured.out
    assert "Launchpad" in captured.out


def test_cli_export_gds(sample_script, tmp_path):
    """Test headlessly exporting a script to a GDSII mask file."""
    out_gds = tmp_path / "output.gds"
    with pytest.raises(SystemExit) as exc_info:
        main(["export", str(sample_script), "-o", str(out_gds), "--format", "gds"])
    assert exc_info.value.code == 0
    assert out_gds.exists()
    assert out_gds.stat().st_size > 0


def test_cli_export_png(sample_script, tmp_path):
    """Test headlessly exporting a script to a PNG figure."""
    out_png = tmp_path / "output.png"
    with pytest.raises(SystemExit) as exc_info:
        main(["export", str(sample_script), "-o", str(out_png), "--theme", "paper", "--dpi", "150"])
    assert exc_info.value.code == 0
    assert out_png.exists()
    assert out_png.stat().st_size > 0


def test_cli_headless_gui(monkeypatch, sample_script):
    """Test GUI invocation in headless test mode."""
    monkeypatch.setenv("SQCANVAS_HEADLESS_LOAD", "1")
    main([])
    main(["--theme", "cyber"])
    main([str(sample_script)])
    main([str(sample_script), "--new-instance"])


def test_cli_ipc_helpers(monkeypatch):
    """Test IPC socket helper in headless environment."""
    monkeypatch.setenv("SQCANVAS_HEADLESS_LOAD", "1")
    assert not _try_send_to_existing_instance("test.py", "cyber")


def test_cli_detach(monkeypatch, capsys):
    """Test that `sqcanvas` launches background worker with pythonw by default."""
    class DummyProc:
        pid = 12345

    def fake_popen(cmd, *args, **kwargs):
        assert "--_gui-worker" in cmd
        return DummyProc()

    monkeypatch.setattr("subprocess.Popen", fake_popen)
    # Ensure headless flag is not set for this test
    monkeypatch.delenv("SQCANVAS_HEADLESS_LOAD", raising=False)
    main(["my_chip.py"])
    captured = capsys.readouterr()
    assert "launched in background" in captured.out
    assert "12345" in captured.out


