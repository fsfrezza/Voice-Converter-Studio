import io
import wave

from fastapi.testclient import TestClient
from app.main import app

def make_audio():
    payload = io.BytesIO()
    with wave.open(payload, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00\x01\x00" * 4000)
    return payload.getvalue()

def test_health():
    result = TestClient(app).get("/api/health")
    assert result.status_code == 200
    assert "presentation" in result.json()["presets"]

def test_reject_invalid_format():
    result = TestClient(app).post("/api/convert", files={"file": ("voice.txt", b"x")})
    assert result.status_code == 415

def test_reject_invalid_preset():
    result = TestClient(app).post("/api/convert", files={"file": ("voice.wav", make_audio())}, data={"preset": "unknown"})
    assert result.status_code == 422

def test_convert_and_download(tmp_path, monkeypatch):
    monkeypatch.setattr("app.main.STORE", tmp_path)
    client = TestClient(app)
    result = client.post("/api/convert", files={"file": ("voice.wav", make_audio())}, data={"preset": "combat"})
    assert result.status_code == 201, result.text
    data = result.json()
    assert data["preset"] == "combat"
    audio = client.get(data["audio_url"])
    assert audio.status_code == 200
    with wave.open(io.BytesIO(audio.content), "rb") as wav:
        assert wav.getnframes() == 8000

def test_combat_pitch_is_lowered(tmp_path):
    import numpy as np
    from scipy.io import wavfile
    from app.voice_style import render

    rate = 16000
    t = np.arange(rate, dtype=np.float32) / rate
    signal = np.round(np.sin(2 * np.pi * 220 * t) * 12000).astype(np.int16)
    source = tmp_path / "tone.wav"
    output = tmp_path / "shifted.wav"
    wavfile.write(source, rate, signal)
    render(source, output, "combat")
    actual_rate, shifted = wavfile.read(output)
    assert actual_rate == rate
    assert shifted.shape == signal.shape
    spectrum = np.abs(np.fft.rfft(shifted.astype(np.float64)))
    dominant_hz = np.fft.rfftfreq(len(shifted), 1 / rate)[np.argmax(spectrum)]
    assert 170 < dominant_hz < 200, f"Esperado tom mais grave, encontrado {dominant_hz} Hz"
