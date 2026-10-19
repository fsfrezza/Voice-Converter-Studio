"""Original announcer-style sound design; no identity cloning."""
from pathlib import Path

import librosa
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

PRESETS = {
    "conversation": {"bass": 1.05, "presence": 1.10, "drive": 1.10, "pitch": 0.0},
    "presentation": {"bass": 1.28, "presence": 1.40, "drive": 1.65, "pitch": -1.25},
    "combat": {"bass": 1.48, "presence": 1.80, "drive": 2.40, "pitch": -3.0},
}


def render(source: Path, output: Path, preset: str) -> None:
    """Give speech a stronger announcer sound, preserving spoken content and duration."""
    settings = PRESETS[preset]
    rate, samples = wavfile.read(source)
    if samples.dtype.kind not in "iu":
        raise ValueError("Use áudio WAV PCM inteiro.")
    if samples.ndim > 2 or rate < 8000:
        raise ValueError("Formato de áudio incompatível.")

    if samples.dtype.kind == "u":
        audio = (samples.astype(np.float32) - 128.0) / 128.0
    else:
        max_value = float(max(abs(np.iinfo(samples.dtype).min), np.iinfo(samples.dtype).max))
        audio = samples.astype(np.float32) / max_value
    was_mono = audio.ndim == 1
    if was_mono:
        audio = audio[:, None]

    # Shift pitch in an audible way without changing the words' timing.
    if settings["pitch"]:
        channels = []
        for c in range(audio.shape[1]):
            shifted = librosa.effects.pitch_shift(
                audio[:, c].astype(np.float32), sr=rate, n_steps=settings["pitch"]
            )
            channels.append(shifted[: len(audio)])
        audio = np.column_stack(channels)

    # Boost the announcer's lower body and articulate the upper range.
    bass = sosfilt(butter(2, min(250, 0.12 * rate), fs=rate, output="sos"), audio, axis=0)
    high = sosfilt(
        butter(2, min(1500, 0.30 * rate), fs=rate, btype="highpass", output="sos"),
        audio, axis=0,
    )
    colored = audio + (settings["bass"] - 1) * bass + (settings["presence"] - 1) * high

    # Smooth drive and loudness normalization. No digital clipping.
    drive = settings["drive"]
    shaped = np.tanh(colored * drive) / np.tanh(drive)
    peak = float(np.max(np.abs(shaped))) if shaped.size else 0.0
    if peak > 0:
        shaped *= 0.94 / peak
    pcm = np.round(np.clip(shaped, -1.0, 1.0) * 32767).astype(np.int16)
    wavfile.write(output, rate, pcm[:, 0] if was_mono else pcm)
