"""Minimal local recording-to-conversion service; Python standard-library WAV parsing."""
from __future__ import annotations

import os
import shutil
import subprocess
import uuid
import wave
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from app.rvc_engine import RVCError, availability as rvc_availability, convert as rvc_convert
from app.voice_style import PRESETS, render

BASE = Path(__file__).resolve().parent.parent
STORE = Path(os.environ.get("VOICE_CONVERTER_STORE", str(BASE / "data"))).resolve()
MAX_UPLOAD = 25 * 1024 * 1024
ENGINE = os.environ.get("VOICE_CONVERTER_COMMAND", "").strip()

app = FastAPI(title="Voice Converter", version="0.1.0")


def validate_wav(path: Path) -> None:
    try:
        with wave.open(str(path), "rb") as stream:
            if stream.getnframes() < 1 or stream.getnchannels() not in (1, 2):
                raise ValueError("O WAV deve conter áudio mono ou estéreo.")
            if stream.getcomptype() != "NONE" or stream.getsampwidth() not in (1, 2, 3, 4):
                raise ValueError("É necessário um WAV PCM sem compressão.")
    except (wave.Error, EOFError, ValueError) as exc:
        raise HTTPException(422, f"WAV inválido: {exc}") from exc


@app.get("/api/health")
def health():
    ready, reason = rvc_availability()
    return {"status": "ok", "engine": "rvc" if ready else "external" if ENGINE else "announcer-dsp", "neural_ready": ready, "neural_message": reason, "presets": list(PRESETS)}


@app.post("/api/convert", status_code=201)
async def convert(file: UploadFile = File(...), preset: str = Form("presentation"), engine_mode: str = Form("auto")):
    if preset not in PRESETS:
        raise HTTPException(422, "Perfil de narração desconhecido.")
    if engine_mode not in ("auto", "neural", "dsp"):
        raise HTTPException(422, "Motor de conversão desconhecido.")
    neural_ready, neural_reason = rvc_availability()
    if engine_mode == "neural" and not neural_ready:
        raise HTTPException(409, "Modelo neural não disponível: " + neural_reason)
    chosen = ("rvc" if neural_ready else "external" if ENGINE else "announcer-dsp") if engine_mode == "auto" else ("rvc" if engine_mode == "neural" else "announcer-dsp")
    if not file.filename or not file.filename.lower().endswith(".wav"):
        raise HTTPException(415, "Envie um arquivo WAV PCM.")
    job_id = uuid.uuid4().hex
    job_dir = STORE / job_id
    job_dir.mkdir(parents=True, exist_ok=False)
    source = job_dir / "source.wav"
    output = job_dir / "converted.wav"
    size = 0
    try:
        with source.open("wb") as target:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD:
                    raise HTTPException(413, "Arquivo excede o limite de 25 MiB.")
                target.write(chunk)
        validate_wav(source)
        if chosen == "rvc":
            try:
                await run_in_threadpool(rvc_convert, source, output, preset)
            except RVCError as exc:
                raise HTTPException(502, str(exc)) from exc
            validate_wav(output)
        elif chosen == "external":
            try:
                subprocess.run(
                    [ENGINE, "--input", str(source), "--output", str(output)],
                    timeout=180, check=True, capture_output=True, text=True,
                )
            except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                raise HTTPException(502, "O motor de conversão falhou ou excedeu o tempo limite.") from exc
            if not output.is_file():
                raise HTTPException(502, "O motor não produziu um arquivo WAV.")
            validate_wav(output)
        else:
            try:
                await run_in_threadpool(render, source, output, preset)
            except (ValueError, TypeError) as exc:
                raise HTTPException(422, str(exc)) from exc
    except Exception:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise
    finally:
        await file.close()
    return {"id": job_id, "status": "ready", "engine": chosen, "preset": preset, "audio_url": f"/api/jobs/{job_id}/audio"}


@app.get("/api/jobs/{job_id}")
def job(job_id: str):
    if len(job_id) != 32 or any(c not in "0123456789abcdef" for c in job_id):
        raise HTTPException(404, "Trabalho não encontrado.")
    if not (STORE / job_id / "converted.wav").is_file():
        raise HTTPException(404, "Trabalho não encontrado.")
    return {"id": job_id, "status": "ready", "audio_url": f"/api/jobs/{job_id}/audio"}


@app.get("/api/jobs/{job_id}/audio")
def audio(job_id: str):
    info = job(job_id)
    return FileResponse(STORE / info["id"] / "converted.wav", media_type="audio/wav", filename="voz-convertida.wav")


app.mount("/", StaticFiles(directory=BASE / "web", html=True), name="web")
