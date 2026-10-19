"""Adapter for the official RVC offline inference CLI.

RVC and user-authorized model files are separate installations.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


class RVCError(RuntimeError):
    pass


def configuration():
    root_value = os.environ.get("RVC_ROOT", "").strip()
    model_value = os.environ.get("RVC_MODEL", "").strip()
    if not root_value or not model_value:
        return None
    root = Path(root_value).expanduser().resolve()
    model = Path(model_value).expanduser()
    if not model.is_absolute():
        model = root / model
    python = os.environ.get("RVC_PYTHON", sys.executable).strip()
    index_value = os.environ.get("RVC_INDEX", "").strip()
    index = Path(index_value).expanduser() if index_value else None
    if index is not None and not index.is_absolute():
        index = root / index
    return {"root": root, "model": model.resolve(), "python": python, "index": index}


def availability():
    config = configuration()
    if config is None:
        return False, "Configure RVC_ROOT e RVC_MODEL."
    if not (config["root"] / "infer" / "cli.py").is_file():
        return False, "RVC_ROOT não contém infer/cli.py."
    if not config["model"].is_file() or config["model"].suffix.lower() != ".pth":
        return False, "Modelo RVC (.pth) não encontrado."
    if config["index"] is not None and not config["index"].is_file():
        return False, "Índice RVC (.index) não encontrado."
    return True, "Modelo neural configurado."


def build_command(source: Path, output: Path, preset: str):
    config = configuration()
    ready, reason = availability()
    if not ready or config is None:
        raise RVCError(reason)
    pitch = {"conversation": "0", "presentation": "-1", "combat": "-2"}[preset]
    index_rate = "0.65" if config["index"] else "0"
    command = [
        config["python"], str(config["root"] / "infer" / "cli.py"),
        "--model", str(config["model"]),
        "--input", str(source.resolve()),
        "--output", str(output.resolve()),
        "--pitch", pitch,
        "--f0-method", "rmvpe",
        "--index-rate", index_rate,
    ]
    if config["index"] is not None:
        command += ["--index", str(config["index"].resolve())]
    return command, config["root"]


def convert(source: Path, output: Path, preset: str) -> None:
    command, root = build_command(source, output, preset)
    try:
        subprocess.run(command, cwd=root, check=True, capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RVCError("Falha na conversão RVC. Verifique a instalação e o modelo.") from exc
    if not output.is_file() or output.stat().st_size == 0:
        raise RVCError("RVC não produziu um WAV de saída.")
