#!/usr/bin/env python3
"""Mux narration, an optional music bed and a whoosh onto a silent video.

Rules this enforces (every 3b1b video):
- The voice fades in at its first word, then holds one level (loudnorm, -16 LUFS).
- The bed plays loud in the music-only open, then RAMPS down (default 1.5 s) to a low,
  constant level under the narration. It does not pump between lines: speech gaps
  under --merge-gap seconds count as speech. It ramps back up in long gaps and at the end.
- No whoosh by default. --whoosh adds a short one that peaks at the first spoken word.
- A small, low-opacity text credit sits bottom-right for the whole video:
  "Style inspired by 3Blue1Brown". Text only, never their logo (a logo implies
  the video is theirs or endorsed by them). --no-credit turns it off.

usage:
  mix-audio.py --video video_silent.mp4 --voice voiceover.mp3 [--voice-offset 5.0] \
               [--bed bed.m4a --bed-start 60] [--whoosh] --out video.mp4
Speech intervals come from silencedetect on the voice, so any voice track works.
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(*a):
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", *map(str, a)], check=True)


def duration(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(p)]))


def speech_intervals(voice_wav, total, merge_gap):
    log = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", str(voice_wav), "-af",
                          "silencedetect=noise=-45dB:d=0.25", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    # speech = complement of silence
    sil = list(zip(starts, ends + [total] * (len(starts) - len(ends))))
    speech, t = [], 0.0
    for s, e in sil:
        if s > t:
            speech.append([t, s])
        t = e
    if t < total:
        speech.append([t, total])
    merged = []
    for s, e in speech:
        if merged and s - merged[-1][1] < merge_gap:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    return merged


def duck_expr(intervals, ramp, high_db, low_db):
    """gain(t) in dB: high outside speech, low inside; each linear ramp is centered on the speech edge,
    so the music hands off to the first word with no quiet dip."""
    terms = []
    for s, e in intervals:
        down = f"clip((t-{s - ramp / 2:.3f})/{ramp},0,1)"
        up = f"clip(({e + ramp / 2:.3f}-t)/{ramp},0,1)"
        terms.append(f"min({down},{up})")
    d = "+".join(terms) if terms else "0"
    return f"pow(10,({high_db}-({high_db - low_db})*min(1,{d}))/20)"


def credit_png(text, w, h, path, opacity):
    from PIL import Image, ImageDraw, ImageFont
    size = max(12, round(h * 0.022))
    try:
        font = ImageFont.truetype("/Library/Fonts/Inter-Medium.ttf", size)
    except OSError:
        font = ImageFont.load_default(size=size)
    tw = int(font.getlength(text)) + 4
    img = Image.new("RGBA", (tw, int(size * 1.4)), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((2, 0), text, font=font, fill=(255, 255, 255, int(255 * opacity)))
    img.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--voice", required=True)
    ap.add_argument("--voice-offset", type=float, default=0.0, help="seconds before the voice track starts")
    ap.add_argument("--bed", help="music bed (any format); omit for voice only")
    ap.add_argument("--bed-start", type=float, default=0.0, help="seconds into the bed file to start")
    ap.add_argument("--bed-high-db", type=float, default=0.0, help="bed gain with no speech (bed is normalized to -18 LUFS first)")
    ap.add_argument("--bed-low-db", type=float, default=-15.0, help="bed gain under speech")
    ap.add_argument("--ramp", type=float, default=1.5, help="seconds for each duck ramp")
    ap.add_argument("--merge-gap", type=float, default=3.0, help="speech gaps shorter than this stay ducked")
    ap.add_argument("--voice-fade", type=float, default=0.35, help="fade-in at the first word")
    ap.add_argument("--whoosh", action="store_true", help="opt in: a whoosh that peaks on the first word")
    ap.add_argument("--whoosh-db", type=float, default=-3.0)
    ap.add_argument("--credit", default="Style inspired by 3Blue1Brown")
    ap.add_argument("--credit-opacity", type=float, default=0.45)
    ap.add_argument("--no-credit", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    total = duration(a.video)
    tmp = Path(tempfile.mkdtemp(prefix="mix-audio-"))
    voice = tmp / "voice.wav"
    ms = int(a.voice_offset * 1000)
    # the voice plays at 1x: never atempo or time-stretch it; scenes stretch to fit the voice
    run("-i", a.voice, "-af", f"loudnorm=I=-16:TP=-1.5:LRA=7,aresample=48000,adelay={ms}|{ms},apad",
        "-ac", "2", "-t", f"{total:.3f}", voice)
    speech = speech_intervals(voice, total, a.merge_gap)
    first = speech[0][0] if speech else a.voice_offset

    inputs = ["-i", a.video, "-i", voice]
    chains = [f"[1:a]afade=t=in:st={max(first - 0.05, 0):.3f}:d={a.voice_fade}[vo]"]
    mixin = ["[vo]"]
    k = 2
    if a.bed:
        inputs += ["-ss", f"{a.bed_start}", "-stream_loop", "-1", "-i", a.bed]
        chains.append(
            f"[{k}:a]aresample=48000,loudnorm=I=-18:TP=-2:LRA=11,"
            f"volume='{duck_expr(speech, a.ramp, a.bed_high_db, a.bed_low_db)}':eval=frame,"
            f"afade=t=in:d=1.5,afade=t=out:st={max(total - 4, 0):.3f}:d=4,atrim=0:{total:.3f}[bed]")
        mixin.append("[bed]")
        k += 1
    if a.whoosh and speech:
        wav = tmp / "whoosh.wav"
        subprocess.run([sys.executable, str(HERE / "whoosh.py"), str(wav)], check=True, capture_output=True)
        at = max(first - 0.6 * 0.9, 0)  # whoosh peak (60% of 0.9 s) lands on the first word
        wms = int(at * 1000)
        inputs += ["-i", wav]
        chains.append(f"[{k}:a]volume={a.whoosh_db}dB,adelay={wms}|{wms}[wh]")
        mixin.append("[wh]")
        k += 1
    chains.append("".join(mixin) + f"amix=inputs={len(mixin)}:normalize=0,alimiter=limit=0.9,atrim=0:{total:.3f}[a]")
    vmap, vcodec = "0:v", ["-c:v", "copy"]
    if not a.no_credit:
        w, h = map(int, subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                                 "stream=width,height", "-of", "csv=p=0", a.video]).decode().split(","))
        png = tmp / "credit.png"
        credit_png(a.credit, w, h, png, a.credit_opacity)
        m = round(h * 0.018)
        inputs += ["-i", png]
        chains.append(f"[0:v][{k}:v]overlay=x=W-w-{m}:y=H-h-{m}[v]")
        vmap, vcodec = "[v]", ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p"]
    run(*inputs, "-filter_complex", ";".join(chains), "-map", vmap, "-map", "[a]", *vcodec,
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", a.out)
    print(f"wrote {a.out} ({total:.1f}s) speech runs: {[(round(s, 1), round(e, 1)) for s, e in speech]}")


if __name__ == "__main__":
    main()
