#!/usr/bin/env python3
"""Make a short, soft whoosh (swept band-passed noise, panned left to right).

usage: whoosh.py out.wav [--dur 0.9] [--seed 3]
The peak lands at 60% of --dur. mix-audio.py places it so the peak hits the first spoken word.
"""
import argparse
import wave

import numpy as np

SR = 48000


def one_pole(x, fc):
    """Lowpass with a per-sample cutoff (Hz)."""
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def whoosh(dur=0.9, seed=3):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n)
    peak = 0.6
    # cutoff sweeps up to the peak, then falls: 250 Hz -> 5 kHz -> 900 Hz
    rise = np.clip(t / peak, 0, 1)
    fall = np.clip((t - peak) / (1 - peak), 0, 1)
    fc = np.where(t < peak, 250 * (5000 / 250) ** rise, 5000 * (900 / 5000) ** fall)
    band = one_pole(noise, fc) - one_pole(noise, fc / 5)
    env = np.where(t < peak, rise ** 2.2, (1 - fall) ** 1.6)
    mono = band * env
    mono /= np.max(np.abs(mono)) + 1e-9
    pan = np.clip(t, 0, 1)  # left -> right
    left, right = mono * np.cos(pan * np.pi / 2), mono * np.sin(pan * np.pi / 2)
    st = np.stack([left, right], axis=1) * 10 ** (-6 / 20)
    return (st * 32767).astype(np.int16)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--dur", type=float, default=0.9)
    ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()
    data = whoosh(a.dur, a.seed)
    with wave.open(a.out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print(f"wrote {a.out} ({a.dur:.2f}s, peak at {0.6 * a.dur:.2f}s)")
