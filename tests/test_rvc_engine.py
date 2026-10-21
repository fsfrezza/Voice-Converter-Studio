from pathlib import Path
from app import rvc_engine


def test_build_command_uses_module_and_cpu_friendly_defaults(tmp_path, monkeypatch):
    root = tmp_path / "RVC"
    (root / "infer").mkdir(parents=True)
    (root / "infer" / "cli.py").write_text("# test")
    (root / "assets" / "weights").mkdir(parents=True)
    (root / "assets" / "weights" / "voice.pth").write_bytes(b"fixture")
    python_path = tmp_path / "python.exe"
    python_path.write_bytes(b"fixture")
    monkeypatch.setenv("RVC_ROOT", str(root))
    monkeypatch.setenv("RVC_MODEL", "assets/weights/voice.pth")
    monkeypatch.setenv("RVC_PYTHON", str(python_path))
    monkeypatch.delenv("RVC_INDEX", raising=False)
    monkeypatch.delenv("RVC_F0_METHOD", raising=False)
    monkeypatch.setenv("RVC_SPEAKER_ID", "2")
    command, cwd = rvc_engine.build_command(tmp_path / "input.wav", tmp_path / "output.wav", "combat")
    assert command[1:3] == ["-m", "infer.cli"]
    assert command[command.index("--speaker-id") + 1] == "2"
    assert command[command.index("--f0-method") + 1] == "pm"
    assert command[command.index("--pitch") + 1] == "0"
    assert cwd == root


def test_missing_model_is_not_neural_ready(tmp_path, monkeypatch):
    monkeypatch.setenv("RVC_ROOT", str(tmp_path))
    monkeypatch.setenv("RVC_MODEL", "nonexistent.pth")
    ready, message = rvc_engine.availability()
    assert not ready
    assert "infer/cli.py" in message or ".pth" in message


def test_invalid_speaker_id_rejected(tmp_path, monkeypatch):
    root = tmp_path / "RVC"
    (root / "infer").mkdir(parents=True)
    (root / "infer" / "cli.py").write_text("# fixture")
    (root / "voice.pth").write_bytes(b"fixture")
    python_path = tmp_path / "python.exe"
    python_path.write_bytes(b"fixture")
    monkeypatch.setenv("RVC_ROOT", str(root))
    monkeypatch.setenv("RVC_MODEL", "voice.pth")
    monkeypatch.setenv("RVC_PYTHON", str(python_path))
    monkeypatch.setenv("RVC_SPEAKER_ID", "bad")
    ready, _ = rvc_engine.availability()
    assert not ready
