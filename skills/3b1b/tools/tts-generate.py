#!/usr/bin/env python3
"""
TTS generator for the 3b1b voiceover pipeline.

Reads the SubtitleSpec from narration.txt, synthesizes one MP3 per subtitle,
measures exact durations with ffprobe, concatenates them into voiceover.mp3,
and writes per-subtitle timings to timestamps.json.

Three engines. `--engine auto` (default) picks the first one that is available:
    gemini      GEMINI_API_KEY or ~/.gemini_api_key   (cloud, best quality/cost)
    elevenlabs  ELEVENLABS_API_KEY                    (cloud, Karpathy's pick)
    kokoro      local `kokoro` package                (offline, free)

    python tts-generate.py --narration narration.txt
    python tts-generate.py --engine kokoro --voice am_adam
    python tts-generate.py --engine gemini --voice Charon
    python tts-generate.py --bust 2                     # drop one cached clip, then exit

Per-line audio is cached in .tts-cache/, so re-runs only regenerate changed
lines. The Kokoro model is loaded once per run (in-process); if every line is a
cache hit it is not loaded at all. Requires ffmpeg/ffprobe and:
    uv add "kokoro>=0.9.4" soundfile
"""

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_VOICES = {"kokoro": "am_michael", "gemini": "Iapetus", "elevenlabs": "JBFqnCBsd6RMkjVDRZzb"}
GEMINI_MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts")
ELEVEN_MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
KOKORO_MODEL_ID = "hexgrad/Kokoro-82M"
KOKORO_LANG_CODES = {"a", "b", "e", "f", "h", "i", "j", "p", "z"}
CACHE_DIR = Path(".tts-cache")
_PIPELINES = {}


def model_id(engine: str) -> str:
    return {"kokoro": KOKORO_MODEL_ID, "gemini": GEMINI_MODEL, "elevenlabs": ELEVEN_MODEL}[engine]


def gemini_key() -> str | None:
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if not k:
        p = Path.home() / ".gemini_api_key"
        k = p.read_text().strip() if p.exists() else ""
    return k or None


def kokoro_available() -> bool:
    try:
        import kokoro  # noqa: F401
        return True
    except ImportError:
        return False


def pick_engine(requested: str) -> str:
    if requested != "auto":
        return requested
    if gemini_key():
        return "gemini"
    if os.environ.get("ELEVENLABS_API_KEY"):
        return "elevenlabs"
    if kokoro_available():
        return "kokoro"
    sys.exit("Error: no TTS engine. Set GEMINI_API_KEY or ELEVENLABS_API_KEY, "
             "or run setup.sh --kokoro for the offline voice.")


def cache_path(text: str, voice_id: str, engine: str = "kokoro", cache_dir: Path = CACHE_DIR) -> Path:
    obj = {"model_id": model_id(engine), "text": text, "voice_id": voice_id,
           "speed": os.environ.get("KOKORO_SPEED", "1"),
           "style": STYLE if engine == "gemini" else ""}
    key = hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return cache_dir / f"{key}.mp3"


def parse_subtitles(narration_path: str) -> list[str]:
    """
    Parse the SubtitleSpec from narration.txt: lines prefixed with `- ` under a
    `subtitles:` heading (inside or outside a fenced code block).
    """
    text = Path(narration_path).read_text()
    stripped = re.sub(r"```[^\n]*\n", "", text).replace("```", "")
    match = re.search(r"^subtitles:\s*\n(.*?)(?=\n[^\s\-\n]|\Z)", stripped, re.MULTILINE | re.DOTALL)
    if not match:
        sys.exit(f"Error: No 'subtitles:' block found in {narration_path}")
    items = [re.sub(r"^[ \t]*-\s*", "", line).strip()
             for line in match.group(1).splitlines()
             if re.match(r"^[ \t]*-", line)]
    if not items:
        sys.exit("Error: Empty subtitles list in narration.txt")
    return items


def get_pipeline(voice_id: str):
    lang_code = voice_id[:1].lower()
    if lang_code not in KOKORO_LANG_CODES:
        lang_code = "a"
    pipeline = _PIPELINES.get(lang_code)
    if pipeline is not None:
        return pipeline
    try:
        from kokoro import KPipeline
    except ImportError as e:
        raise RuntimeError(
            'Kokoro is not installed. Install it with: uv add "kokoro>=0.9.4" soundfile'
        ) from e
    pipeline = KPipeline(lang_code=lang_code, repo_id=KOKORO_MODEL_ID, device="cpu")
    _PIPELINES[lang_code] = pipeline
    return pipeline


def write_mp3(audio_chunks, out_path: Path) -> None:
    import numpy as np
    import soundfile as sf

    if not audio_chunks:
        raise RuntimeError("Kokoro returned no audio")
    chunks = []
    for audio in audio_chunks:
        if hasattr(audio, "detach"):
            audio = audio.detach().cpu().numpy()
        chunks.append(np.asarray(audio, dtype=np.float32))
    audio_out = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
    try:
        sf.write(wav_path, audio_out, 24000)
        subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-q:a", "2", str(out_path)],
            check=True, capture_output=True,
        )
    finally:
        if os.path.exists(wav_path):
            os.unlink(wav_path)


def http_post(url: str, body: dict, headers: dict) -> bytes:
    """POST JSON with 3 tries and backoff on 429/5xx and network errors."""
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", **headers})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and attempt < 2:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"{url.split('/')[2]} {e.code}: {e.read().decode()[:400]}")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt == 2:
                raise RuntimeError(f"request failed after 3 tries: {e}")
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("unreachable")


def pcm_to_mp3(pcm: bytes, out_path: Path, rate: int = 24000) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(rate), "-ac", "1", "-i", "-",
                    "-codec:a", "libmp3lame", "-q:a", "2", str(out_path)],
                   input=pcm, check=True, capture_output=True)


STYLE = os.environ.get("GEMINI_TTS_STYLE", "")  # delivery note; set by --style


def gemini_one(text: str, voice: str, out_path: Path) -> None:
    """One Gemini TTS clip. 2.x uses generateContent; 3.x uses the Interactions API.
    A delivery note (STYLE) only works on 2.x: there it steers the read and is not spoken.
    3.x speaks any prefix aloud and rejects system_instruction, so the note is dropped there."""
    key = gemini_key()
    if STYLE and GEMINI_MODEL.startswith("gemini-2."):
        text = f"{STYLE}: {text}"
    headers = {"x-goog-api-key": key}
    for attempt in range(3):  # a 200 with no audio part happens; it renders on a re-roll
        seed = 42 + attempt
        if GEMINI_MODEL.startswith("gemini-2."):
            d = json.loads(http_post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
                {"contents": [{"parts": [{"text": text}]}],
                 "generationConfig": {"responseModalities": ["AUDIO"], "seed": seed,
                                      "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}},
                headers))
            try:
                inline = d["candidates"][0]["content"]["parts"][0]["inlineData"]
                pcm = base64.b64decode(inline["data"])
            except (KeyError, IndexError):
                continue
            # read the real sample rate: a wrong guess would play the voice sped up or slowed down
            rate = int(re.search(r"rate=(\d+)", inline.get("mimeType", "")).group(1)) if "rate=" in inline.get("mimeType", "") else 24000
            pcm_to_mp3(pcm, out_path, rate)
            return
        else:
            d = json.loads(http_post(
                "https://generativelanguage.googleapis.com/v1beta/interactions",
                {"model": GEMINI_MODEL, "input": [{"type": "user_input", "content": [{"type": "text", "text": text}]}],
                 "response_format": {"type": "audio", "mime_type": "audio/wav"},
                 "generation_config": {"speech_config": [{"voice": voice}], "seed": seed}, "store": False},
                headers))
            parts = [p for st in d.get("steps", []) if st.get("type") == "model_output"
                     for p in st.get("content", []) if p.get("type") == "audio" and p.get("data")]
            if not parts:
                continue
            pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", "-", "-f", "s16le", "-ar", "24000", "-ac", "1", "-"],
                                 input=base64.b64decode(parts[0]["data"]), check=True, capture_output=True).stdout
        pcm_to_mp3(pcm, out_path)
        return
    raise RuntimeError(f"Gemini returned no audio 3 times for: {text[:60]!r}")


def elevenlabs_one(text: str, voice: str, out_path: Path) -> None:
    mp3 = http_post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
                    {"text": text, "model_id": ELEVEN_MODEL},
                    {"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Accept": "audio/mpeg"})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(mp3)


def synthesize(items: list[tuple[int, str, Path]], voice_id: str, engine: str = "kokoro") -> dict[int, str]:
    """Synthesize each (index, text, out_path). Cloud engines run 4 clips in parallel."""
    if not items:
        return {}
    if engine in ("gemini", "elevenlabs"):
        import concurrent.futures as cf
        fn = gemini_one if engine == "gemini" else elevenlabs_one
        with cf.ThreadPoolExecutor(4) as ex:
            futs = {ex.submit(fn, text, voice_id, out): (index, out) for index, text, out in items}
            paths = {}
            for f in cf.as_completed(futs):
                f.result()
                index, out = futs[f]
                paths[index] = str(out)
                print(f"  [{index}] done")
        return paths
    pipeline = get_pipeline(voice_id)
    speed = float(os.environ.get("KOKORO_SPEED", "1"))
    joined = "\n".join(text for _, text, _ in items)
    audio_by_pos: dict[int, list] = {i: [] for i in range(len(items))}
    for result in pipeline(joined, voice=voice_id, speed=speed, split_pattern=r"\n+"):
        audio_by_pos[result.text_index].append(result.audio)

    paths = {}
    for pos, (index, _, out_path) in enumerate(items):
        write_mp3(audio_by_pos[pos], out_path)
        paths[index] = str(out_path)
        print(f"  [{index}] done")
    return paths


def ffprobe_duration(mp3_path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", mp3_path],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def concat_mp3s(parts: list[str], out_path: str) -> None:
    # Stream-copying MP3 packets accumulates encoder padding at every join.
    # Decode first, preserve each measured timing budget, and encode only once.
    inputs = [arg for part in parts for arg in ("-i", part)]
    filters = [
        f"[{i}:a]apad,atrim=duration={ffprobe_duration(part):.9f},"
        f"asetpts=PTS-STARTPTS[a{i}]"
        for i, part in enumerate(parts)
    ]
    filters.append("".join(f"[a{i}]" for i in range(len(parts)))
                   + f"concat=n={len(parts)}:v=0:a=1[audio]")
    subprocess.run(
        ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters),
         "-map", "[audio]", "-codec:a", "libmp3lame", "-q:a", "2", out_path],
        check=True, capture_output=True,
    )


def bust_cache(subtitles: list[str], target_arg: str, voice_id: str, engine: str) -> None:
    try:
        target = subtitles[int(target_arg)]
    except (ValueError, IndexError):
        matches = [s for s in subtitles if target_arg.lower() in s.lower()]
        if not matches:
            sys.exit(f"Error: no subtitle matching {target_arg!r}")
        target = matches[0]
    cp = cache_path(target, voice_id, engine)
    if cp.exists():
        cp.unlink()
        print(f"Busted cache for: {target!r}")
    else:
        print(f"No cache entry for: {target!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TTS voiceover from narration.txt SubtitleSpec")
    parser.add_argument("--narration", "--plan", dest="narration", default="narration.txt",
                        help="Spoken-line input (default: narration.txt; --plan is a compatibility alias)")
    parser.add_argument("--engine", default=os.environ.get("TTS_ENGINE", "auto"),
                        choices=["auto", "gemini", "elevenlabs", "kokoro"])
    parser.add_argument("--voice", default=None,
                        help="Voice for the engine (defaults: gemini Iapetus, elevenlabs George, kokoro am_michael)")
    parser.add_argument("--style", default=None,
                        help="Gemini 2.x delivery note (director's note); see references/narration-style.md")
    parser.add_argument("--out-audio", default="voiceover.mp3")
    parser.add_argument("--out-timestamps", default="timestamps.json")
    parser.add_argument("--bust", metavar="INDEX_OR_TEXT",
                        help="Drop the cached clip for a subtitle by 0-based index or text match, then exit")
    args = parser.parse_args()

    engine = pick_engine(args.engine)
    voice_id = args.voice or DEFAULT_VOICES[engine]
    global STYLE
    if args.style is not None:
        STYLE = args.style
    subtitles = parse_subtitles(args.narration)

    if args.bust is not None:
        bust_cache(subtitles, args.bust, voice_id, engine)
        return

    print(f"Found {len(subtitles)} subtitle(s). Engine: {engine}. Voice: {voice_id}. Generating TTS...")
    parts = [""] * len(subtitles)
    missing: list[tuple[int, str, Path]] = []
    hits = 0
    for i, text in enumerate(subtitles):
        cached = cache_path(text, voice_id, engine)
        if cached.exists():
            parts[i] = str(cached)
            hits += 1
            print(f"  [{i}] cached")
        else:
            missing.append((i, text, cached))

    started = time.perf_counter()
    for idx, path in synthesize(missing, voice_id, engine).items():
        parts[idx] = path
    print(f"  {hits} cached, {len(missing)} generated in {time.perf_counter() - started:.1f}s")

    print("Measuring durations...")
    durations = [ffprobe_duration(p) for p in parts]

    print(f"Concatenating {len(parts)} clips → {args.out_audio}")
    concat_mp3s(parts, args.out_audio)

    start = 0.0
    entries = []
    for i, (text, dur) in enumerate(zip(subtitles, durations)):
        entries.append({"index": i, "text": text,
                        "start_s": round(start, 3), "end_s": round(start + dur, 3),
                        "duration_s": round(dur, 3)})
        start += dur
    Path(args.out_timestamps).write_text(
        json.dumps({"total_duration_s": round(start, 3), "subtitles": entries}, indent=2))
    print(f"Done. {args.out_audio} + {args.out_timestamps} written. Total: {start:.1f}s audio.")


if __name__ == "__main__":
    main()
