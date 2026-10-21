"""Inspect PCM WAV reference clips without training or cloning."""
import argparse
import csv
import math
import wave
from pathlib import Path
import numpy as np

def inspect(path):
    with wave.open(str(path), "rb") as stream:
        rate, channels, width, frames = stream.getframerate(), stream.getnchannels(), stream.getsampwidth(), stream.getnframes()
        raw = stream.readframes(frames)
    if width != 2:
        raise ValueError(f"{path.name}: only PCM16 WAV supported")
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768
    if not len(samples):
        raise ValueError(f"{path.name}: empty audio")
    rms = math.sqrt(float(np.mean(samples ** 2)))
    return {
        "file": path.name, "seconds": round(frames / rate, 2), "sample_rate": rate, "channels": channels,
        "rms_dbfs": round(20 * math.log10(max(rms, 1e-12)), 1),
        "peak_dbfs": round(20 * math.log10(max(float(np.max(np.abs(samples))), 1e-12)), 1),
        "samples_near_clipping_pct": round(100 * float(np.mean(np.abs(samples) >= 0.99)), 3),
        "manual_review": "PENDING", "clean_single_speaker": "UNVERIFIED"
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--output", type=Path, default=Path("reference_qc.csv"))
    args = parser.parse_args()
    rows = [inspect(path) for path in sorted(args.folder.glob("*.wav"))]
    if not rows:
        raise SystemExit("No WAV files found")
    with args.output.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} candidates, {sum(row['seconds'] for row in rows):.2f} seconds.")
    print("Metrics do not prove voice purity or licensing; review each segment before any further use.")

if __name__ == "__main__":
    main()
