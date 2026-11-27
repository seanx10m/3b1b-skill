#!/usr/bin/env python3
"""Flag visual jumps between scenes: compares the last frame of each scene with the first frame of the next.

usage: check-seams.py concat.txt [--max 6.0]
Prints mean absolute pixel difference (0-255) per seam; exit 1 if any seam is over --max.
A seam over the limit means something popped in or out at the cut. End each scene in the pose the next one
starts in (same cast, same positions, content faded out), or FadeIn the new scene's first content.
"""
import argparse, re, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image


def frame(path, last, out):
    args = ["-sseof", "-0.05"] if last else ["-ss", "0"]
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", *args, "-i", str(path), "-frames:v", "1",
                    "-vf", "scale=480:-1", str(out)], check=True)
    return np.asarray(Image.open(out).convert("L"), dtype=np.float32)


ap = argparse.ArgumentParser(); ap.add_argument("concat"); ap.add_argument("--max", type=float, default=6.0)
a = ap.parse_args()
base = Path(a.concat).resolve().parent
files = [base / f for f in re.findall(r"file '([^']+)'", Path(a.concat).read_text())]
tmp = Path(tempfile.mkdtemp()); bad = 0
for i, (x, y) in enumerate(zip(files, files[1:])):
    d = float(np.abs(frame(x, True, tmp / "a.png") - frame(y, False, tmp / "b.png")).mean())
    flag = "POP" if d > a.max else "ok"
    bad += d > a.max
    print(f"{flag:4} {d:6.2f}  {x.stem} -> {y.stem}")
sys.exit(1 if bad else 0)
