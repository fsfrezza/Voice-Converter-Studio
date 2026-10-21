"""Run a locally installed RVC CLI with an authorized voice model."""
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
    index_value = os.environ.get("RVC_INDEX", "").strip()
    index = Path(index_value).expanduser() if index_value else None
    if index is not None and not index.is_absolute():
        index = root / index
    return {
        "root": root,
        "model": model.resolve(),
        "python": os.environ.get("RVC_PYTHON", sys.executable).strip(),
        "index": index,
        "speaker_id": os.environ.get("RVC_SPEAKER_ID", "0").strip(),
        "f0_method": os.environ.get("RVC_F0_METHOD", "pm").strip().lower(),
    }


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
    if not config["speaker_id"].isdigit():
        return False, "RVC_SPEAKER_ID deve ser um inteiro não negativo."
    if config["f0_method"] not in ("pm", "rmvpe"):
        return False, "RVC_F0_METHOD deve ser pm ou rmvpe."
    if not Path(config["python"]).is_file():
        return False, "RVC_PYTHON não aponta para um executável Python existente."
    return True, "Arquivos do modelo encontrados (inferência ainda não validada)."


def build_command(source: Path, output: Path, preset: str):
    config = configuration()
    ready, reason = availability()
    if not ready or config is None:
        raise RVCError(reason)
    if preset not in ("conversation", "presentation", "combat"):
        raise RVCError("Perfil desconhecido.")
    # No automatic pitch change: it distorted the earlier neural demonstration.
    command = [
        config["python"], "-m", "infer.cli",
        "--model", str(config["model"]),
        "--speaker-id", config["speaker_id"],
        "--input", str(source.resolve()),
        "--output", str(output.resolve()),
        "--pitch", "0",
        "--f0-method", config["f0_method"],
        "--index-rate", "0.65" if config["index"] else "0",
        "--overwrite",
    ]
    if config["index"] is not None:
        command += ["--index", str(config["index"].resolve())]
    return command, config["root"]


def convert(source: Path, output: Path, preset: str) -> None:
    command, root = build_command(source, output, preset)
    try:
        result = subprocess.run(
            command, cwd=root, check=False, capture_output=True,
            text=True, errors="replace", timeout=2400,
            env={**os.environ, "PYTHONPATH": str(root)},
        )
    except subprocess.TimeoutExpired as exc:
        raise RVCError("Conversão RVC excedeu o limite de 40 minutos.") from exc
    except OSError as exc:
        raise RVCError("Não foi possível iniciar o motor RVC.") from exc
    if result.returncode != 0 or "Estado：Falha" in result.stdout:
        detail = (result.stderr + "\n" + result.stdout)[-1200:]
        raise RVCError("Falha no motor RVC: " + detail)
    if not output.is_file() or output.stat().st_size < 44:
        raise RVCError("RVC não produziu um WAV válido.")
