# Tools

Pipeline scripts and the local viewer used by the `3b1b` skill.

## video_viewer.py

Browser-based viewer for Manim videos with Code / Preview tabs, chapter
navigation, subtitles, and feedback capture — styled to match the Manimate app.

```bash
python3 video_viewer.py <video.mp4> --order <concat.txt> [--script script.py] [--srt subtitles.srt]
```

**Options:**
- `--order` - video order file (same format as ffmpeg concat.txt), required for chapters
- `--script` - Manim script, shown in the viewer's Code tab
- `--srt` - subtitle file; if omitted, per-scene `.srt` files are concatenated automatically
- `--port` - server port (default: auto)

Renders `ui.html` (which lives next to this script). Prints
`VIDEO_READY http://localhost:<port>` when ready and opens the browser.

### Shortcuts

| Key | Action |
|-----|--------|
| `Space` / `K` | Play/Pause |
| `←` / `J` | Back 5s |
| `→` / `L` | Forward 5s |
| `C` | Toggle subtitles |
| `T` | Insert timestamp into feedback |
| `F` | Fullscreen |

## tts-generate.py

Reads the SubtitleSpec from `narration.txt`, generates per-line audio locally with
Kokoro, measures exact durations with ffprobe, concatenates to `voiceover.mp3`,
and writes `timestamps.json`.

```bash
python3 tts-generate.py --narration narration.txt                 # default voice af_heart
python3 tts-generate.py --narration narration.txt --voice am_adam # another Kokoro voice
```

`--narration` defaults to `narration.txt`; `--plan` remains a compatibility alias.
Audio clips are decoded, padded to their measured durations, and encoded once
when joined to preserve subtitle timing.

Per-line results are cached in `.tts-cache/`, so re-runs only regenerate changed
lines (and the model loads only when there's something to generate). Drop one
clip with `--bust <index or text fragment>`.

## lint-subtitles.py

Simulates a Manim script's scene timelines without rendering (sub-second) and
reports overlapping subtitles, animations that overflow their subtitle window,
and subtitles extending beyond the scene. Invalid timings, incomplete simulations,
and scenes without subtitles cannot pass. Run only for narrated videos; verify
rendered audio/video sync separately.

```bash
python3 lint-subtitles.py script.py    # 0 = clean, 1 = issues, 2 = incomplete/invalid check
```

## Requirements

- Python 3.10+, ffmpeg/ffprobe
- Voiceover: `uv add "kokoro>=0.9.4" soundfile` (local Kokoro, no API key)

## Added in this fork

- `setup.sh` - one-time venv + TinyTeX + LaTeX packages, prints a doctor report. `--kokoro` adds the offline voice.
- `contact-sheet.sh video.mp4 [sheet.png]` - 12 evenly spaced frames tiled 4x3 for self-review.
- `mix-audio.py --video v.mp4 --voice vo.mp3 [--bed m.mp3] --out video.mp4` - voice fade-in + steady level, smooth bed duck, whoosh on the first word.
- `whoosh.py out.wav` - the whoosh alone (peak at 60% of its 0.9 s).
- `tts-generate.py --engine auto|gemini|elevenlabs|kokoro` - auto picks Gemini, then ElevenLabs, then Kokoro.
- `video_viewer.py --no-open` - serve without opening a browser.
