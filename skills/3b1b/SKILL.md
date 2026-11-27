---
name: 3b1b
description: Make a narrated explainer video in the visual style of 3Blue1Brown with Manim Community Edition - intuition first, color-coded math, smooth transforms, voiceover with synced subtitles. Use when the user says "/3b1b", "3b1b style", "3Blue1Brown style", "make a video explainer of X", "animate this concept", "manim", or wants a math, algorithm, ML, or system explained as an animation. Karpathy's prompt "Create a 3b1b style video explainer on X" lands here.
---

# 3b1b

You make one thing: a short explainer video that builds intuition the way 3Blue1Brown does.
The deliverable is `video.mp4` (plus `script.py`) in a session folder.
Keep going until `video.mp4` exists. If you are blocked, give the exact blocker in one line.

Use the *style* of 3Blue1Brown: its pedagogy, palette, and motion.
Never copy its characters (no pi creatures), logo, intro, music, or a specific video's scenes.
The house cast is the original brace characters in `tools/characters.py`.
Every video carries a small text credit, "Style inspired by 3Blue1Brown", bottom-right (added by `mix-audio.py`); never their logo.

Read these before you write code:
- [references/style.md](references/style.md) - story arc, palette, typography, motion. Read it every time.
- [references/cookbook.md](references/cookbook.md) - Manim patterns for the moves in style.md, and the known traps.
- [references/narration-style.md](references/narration-style.md) - how 3b1b narration is written (measured), the reveal recipe, pacing, and the Iapetus delivery note. Read it before Step 3.

## Step 0: environment (once per machine)

```bash
TOOLS_DIR="<absolute path of tools/ next to this file>"
"$TOOLS_DIR/setup.sh"          # idempotent; prints DOCTOR ... READY
export PATH="$(cat ~/.manim-skill/.texbin 2>/dev/null):$HOME/.manim-skill/.venv/bin:$PATH"
```

Export that PATH line in every shell you render from.
`python` below means `~/.manim-skill/.venv/bin/python`.

## Step 1: session folder

Never write outputs into the user's working directory.

```bash
SESSION_DIR="${MANIM_SKILL_HOME:-$HOME/.manim-skill}/<topic-slug>"   # add -2, -3 on collision
mkdir -p "$SESSION_DIR" && cd "$SESSION_DIR"
```

```
narration.txt    spoken lines
voiceover.mp3    TTS audio
timestamps.json  per-line timing
script.py        Manim code, one class per scene
concat.txt       ffmpeg scene order
video.mp4        the deliverable
sheet.png        contact sheet for your own review
```

## Step 2: the beat sheet (in your head, not a file)

Before any narration, decide these five things. Do not write a plan file unless asked.

1. **The one question** the video answers, as a viewer would ask it.
2. **The concrete example** you start with - a specific number, shape, or case, never the general definition.
3. **The aha** - the single picture that makes the answer feel obvious.
4. **The color key** - one color per recurring quantity, fixed for the whole video (see style.md).
5. **The payoff** - the formula or general rule, which arrives *last*, as a summary of what the viewer already saw.

Target 60-120 s and 3-6 scenes unless the user asks for more.

## Step 3: narration

Write `narration.txt` in this exact format. Each `- ` line becomes one TTS clip and one subtitle.

```
subtitles:
- What happens if you keep adding half of what is left?
- Start with one whole square.
```

Rules for the lines:
- Follow the `ste100` skill in **relaxed** mode: one idea per line, short sentences, active voice, one word for one thing.
- Speak to the viewer ("you", "notice", "let's"), like 3b1b, not like a textbook.
- Every line names something the viewer can *see* on screen at that moment.
- Write numbers and symbols as spoken words ("x squared", not "x^2").
- Budget about 2.5 words per second.
- Follow references/narration-style.md: concrete case first, the viewer's guess, one short question then a hold, name the idea after the picture.

## Step 4: TTS

```bash
python "$TOOLS_DIR/tts-generate.py" --narration narration.txt
```

`--engine auto` picks Gemini (key set), then ElevenLabs, then local Kokoro.
The default Gemini voice is Iapetus (clear, light, curious).
For a steered read, use `GEMINI_TTS_MODEL=gemini-2.5-pro-preview-tts` with `--style "<delivery note from narration-style.md>"`; the 3.x models read any style text aloud, so the tool drops it there. Override with `--engine gemini --voice Charon`, `--engine elevenlabs --voice <id>`, or `--engine kokoro --voice am_michael`.
Unchanged lines come from `.tts-cache/`. `--bust <index|text>` drops one clip.
Check the printed clip count matches your line count.
**Read `timestamps.json` before you write code.** Each `duration_s` is the time budget for that line.

## Step 5: code

Write `script.py`:

1. **One class per scene**, named `Scene1_Question`, `Scene2_Example`, and so on.
2. **Render config at the top of `script.py`:**
   - draft: `config.pixel_width, config.pixel_height = 854, 480`; `config.frame_rate = 15`
   - final (user asked, or after feedback settles): 1920x1080 at 30 fps
   - `config.background_color = "#0f0f14"`; frame 14.22x8 for 16:9 (Manim default). For 9:16 use frame 8x14.22.
3. **Each narration line is exactly one `self.add_subcaption(text, duration=dur)`**, same text, same order. Inline each `duration_s` as a literal.
   Give every `play()` an explicit `run_time`, and end each line with `self.wait(max(0, dur - used))`.
   Never burn subtitles in as text.
4. `MathTex` for math, `Tex` for prose labels. Color math with `tex_to_color_map` / `substrings_to_isolate` so the symbol color matches the picture.

```python
from manim import *
config.pixel_width, config.pixel_height, config.frame_rate = 854, 480, 15
config.background_color = "#0f0f14"

class Scene1_Question(Scene):
    def construct(self):
        q = Tex(r"What is $\tfrac12 + \tfrac14 + \tfrac18 + \cdots$ ?", font_size=56)
        dur = 3.1; used = 0
        self.add_subcaption("What happens if you keep adding half of what is left?", duration=dur)
        self.play(Write(q), run_time=2.0); used += 2.0
        self.wait(max(0, dur - used))
```

### Cast and motion (Step 5 rules)

- Use the cast from `tools/characters.py` (`sys.path.insert(0, TOOLS_DIR)`; `from characters import cast, react, idle_blinks`): three listeners bottom-left (curious, skeptic, eager) and a calm narrator bottom-right.
- The cast reacts every line or two, each by its own temperament: `look_at`, `lean_in`, `nod`, `shrug`, `scratch_head`, `squint`, `surprise`, `smile`, `hop`, `blink`. Use `react(chars, "confused"|"reveal"|"agree"|"doubt")` for a staggered group reaction.
- Fill holds over 0.6 s with `idle_blinks(chars, seconds)` instead of `self.wait`, so nobody freezes.
- Ease every move (`rate_functions.ease_in_out_cubic` or the default smooth; never `linear` except steady sweeps).
- Overlap moves: play the content animation and the cast reaction in the same `play`, or use `LaggedStart` / `Succession(Wait(x), ...)`, instead of one after another.
- Key reveals run slower (2-2.5 s) and get a 0.5-1.3 s hold after them.
- Small labels (under ~40 pt) enter with `FadeIn(label, shift=UP * 0.15)`, not `Write`: the first frames of `Write` read as stray glyphs ("interface" starts as "1ı"). Edges and rules use `GrowFromCenter`, not `Create`, which starts as a lone tick on a corner. Keep `Write` for titles and equations.
- Prefer one continuous scene per section. Where you cut, end the scene in the pose the next one starts in, then run `tools/check-seams.py concat.txt` (exit 1 = a visible pop).

## Step 6: lint, render, check

```bash
python "$TOOLS_DIR/lint-subtitles.py" script.py          # narrated only; exit 1 timing, 2 invalid
manim script.py Scene1_Question Scene2_Example ...       # renders to media/videos/script/<h>p<fps>/
```

Write `concat.txt` in scene order, then join and mux:

```bash
ffmpeg -y -v error -f concat -safe 0 -i concat.txt -c copy video_silent.mp4
python "$TOOLS_DIR/mix-audio.py" --video video_silent.mp4 --voice voiceover.mp3 \
  [--voice-offset <music-only open, s>] [--bed <music file> --bed-start <s>] --out video.mp4
```

Always mux with `mix-audio.py`, never a bare ffmpeg `-map`. It does three things on every video:
- The voice fades in at the first word, then holds one level (loudnorm -16 LUFS). It never cuts in.
- The music bed (if any) is loud in the open, then ramps down smoothly over 1.5 s, centered on the first word, to a constant low level under the narration. It does not pump between lines. It ramps back up only in gaps longer than 3 s.
- A short whoosh (`whoosh.py`, swept noise panned left to right) peaks on the first spoken word.

Use a bed when the user gives one or names a track; a soft piano bed suits this style.
To give the music a solo open, start Scene 1 with a few seconds of picture and no subcaption, and pass that length as `--voice-offset`.
Flags: `--no-whoosh`, `--whoosh-db`, `--bed-high-db`, `--bed-low-db`, `--ramp`, `--merge-gap`.

Silent video: write `video.mp4` from the concat step and skip the mux.

**Look at your own output before you show anyone.** Make a contact sheet and Read it:

```bash
"$TOOLS_DIR/contact-sheet.sh" video.mp4 sheet.png     # 12 evenly spaced frames, 4x3
```

Run `python "$TOOLS_DIR/check-seams.py" concat.txt` and fix every POP.
Fix anything on the style.md "reject" list (overlaps, text off frame, tiny labels, frozen frames, a color that changes meaning) and re-render only those scenes.
Also check the durations: `ffprobe` video and audio lengths must match within 0.2 s.

## Step 7: show and iterate

```bash
python "$TOOLS_DIR/video_viewer.py" video.mp4 --order concat.txt --script script.py [--no-open]
```

Run it in the background. It prints `VIDEO_READY http://localhost:<port>`.
Pass `--no-open` when you run as a background agent or the user is not at this machine, and give the URL plus `SESSION_DIR` instead.

The viewer's Capture button (`T`) writes lines like `[0:07] Scene3_Identity: label overlaps the triangle`.
For each one, pull that frame (`ffmpeg -y -ss 7 -i video.mp4 -frames:v 1 f.png`) and Read it before you change code.
Then edit narration and re-run TTS if words changed, fix the named scenes, lint, re-render only those scenes, re-mux.
The viewer serves the new `video.mp4` on reload.
