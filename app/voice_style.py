"""Original announcer-style audio processing; does not imitate a named person."""
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

PRESETS = {
    "conversation": {"bass": 1.10, "presence": 1.12, "drive": 1.10},
    "presentation": {"bass": 1.22, "presence": 1.35, "drive": 1.45},
    "combat": {"bass": 1.28, "presence": 1.55, "drive": 1.85},
}


def render(source: Path, output: Path, preset: str) -> None:
    """EQ and soft dynamic compression; preserves words, tempo and natural pitch."""
    settings = PRESETS[preset]
    rate, samples = wavfile.read(source)
    if samples.dtype.kind not in "iu":
        raise ValueError("Use áudio PCM de 8, 16 ou 32 bits.")
    if samples.ndim > 2 or rate < 8000:
        raise ValueError("Formato de áudio incompatível.")

    if samples.dtype.kind == "u":
        audio = (samples.astype(np.float64) - 128.0) / 128.0
    else:
        audio = samples.astype(np.float64) / float(max(abs(np.iinfo(samples.dtype).min), np.iinfo(samples.dtype).max))
    if audio.ndim == 1:
        audio = audio[:, None]

    # Two gentle shelves, approximated by splitting low/mid/high bands.
    bass_cutoff = min(210, 0.12 * rate)
    presence_cutoff = min(1800, 0.30 * rate)
    bass = sosfilt(butter(2, bass_cutoff, fs=rate, output="sos"), audio, axis=0)
    high = sosfilt(butter(2, presence_cutoff, fs=rate, btype="highpass", output="sos"), audio, axis=0)
    colored = audio + (settings["bass"] - 1) * bass + (settings["presence"] - 1) * high

    # Smooth saturation is deterministic and avoids hard clipping.
    drive = settings["drive"]
    shaped = np.tanh(colored * drive) / np.tanh(drive)
    peak = float(np.max(np.abs(shaped))) if shaped.size else 0.0
    if peak > 0:
        shaped *= min(0.92 / peak, 1.0)
    pcm = np.round(shaped * 32767).astype(np.int16)
    wavfile.write(output, rate, pcm[:, 0] if samples.ndim == 1 else pcm)
