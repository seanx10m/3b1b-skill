#!/usr/bin/env bash
# One-time setup for the 3b1b skill. Safe to re-run: every step checks first.
#   - Python venv with manim (+ kokoro when --kokoro) at $MANIM_SKILL_HOME/.venv
#   - TinyTeX (no sudo) at ~/Library/TinyTeX on macOS, ~/.TinyTeX on Linux, for MathTex/Tex
# Prints a final DOCTOR block. Exit 0 = ready to render.
set -euo pipefail

HOME_DIR="${MANIM_SKILL_HOME:-$HOME/.manim-skill}"
VENV="$HOME_DIR/.venv"
WITH_KOKORO=0
[ "${1:-}" = "--kokoro" ] && WITH_KOKORO=1

mkdir -p "$HOME_DIR"

# 1. System libs manim links against.
if [ "$(uname)" = "Darwin" ] && command -v brew >/dev/null; then
  for f in cairo pango pkgconf ffmpeg; do
    brew list --formula "$f" >/dev/null 2>&1 || brew install "$f"
  done
fi
command -v ffmpeg >/dev/null || { echo "BLOCKER: ffmpeg missing"; exit 1; }

# 2. Python venv with manim.
command -v uv >/dev/null || { echo "BLOCKER: uv missing (https://docs.astral.sh/uv/)"; exit 1; }
[ -x "$VENV/bin/python" ] || uv venv -q --python 3.12 "$VENV"
"$VENV/bin/python" -c "import manim" 2>/dev/null || uv pip install -q --python "$VENV/bin/python" "manim>=0.19"
if [ "$WITH_KOKORO" = 1 ]; then
  "$VENV/bin/python" -c "import kokoro" 2>/dev/null || uv pip install -q --python "$VENV/bin/python" "kokoro>=0.9.4" soundfile
fi

# 3. LaTeX via TinyTeX (user-space, no sudo).
if ! command -v latex >/dev/null; then
  if [ "$(uname)" = "Darwin" ]; then TT="$HOME/Library/TinyTeX"; else TT="$HOME/.TinyTeX"; fi
  TT_BIN="$(ls -d "$TT"/bin/* 2>/dev/null | head -1 || true)"
  if [ -z "$TT_BIN" ]; then
    tag="$(curl -fsSL https://api.github.com/repos/rstudio/tinytex-releases/releases/latest | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p')"
    [ -n "$tag" ] || { echo "BLOCKER: could not resolve TinyTeX release"; exit 1; }
    if [ "$(uname)" = "Darwin" ]; then asset="TinyTeX-1-darwin-$tag.tar.xz"; else asset="TinyTeX-1-linux-x86_64-$tag.tar.xz"; fi
    tmp="$(mktemp -d)"
    curl -fsSL -o "$tmp/tt.tar.xz" "https://github.com/rstudio/tinytex-releases/releases/download/$tag/$asset"
    mkdir -p "$(dirname "$TT")"
    tar -xJf "$tmp/tt.tar.xz" -C "$(dirname "$TT")"
    [ -d "$(dirname "$TT")/.TinyTeX" ] && [ ! -d "$TT" ] && mv "$(dirname "$TT")/.TinyTeX" "$TT"
    TT_BIN="$(ls -d "$TT"/bin/* | head -1)"
  fi
  echo "$TT_BIN" > "$HOME_DIR/.texbin"
fi

# 3b. LaTeX packages manim needs. tlmgr refuses installs until it updates itself.
TT_BIN="$(dirname "$(command -v latex 2>/dev/null || echo "$(cat "$HOME_DIR/.texbin")/latex")")"
if ! "$TT_BIN/kpsewhich" standalone.cls >/dev/null 2>&1; then
  "$TT_BIN/tlmgr" update --self >/dev/null
  "$TT_BIN/tlmgr" install standalone preview doublestroke relsize fundus-calligra \
    wasysym physics dvisvgm rsfs wasy cm-super setspace everysel babel-english >/dev/null
  "$TT_BIN/kpsewhich" standalone.cls >/dev/null || { echo "BLOCKER: LaTeX packages did not install"; exit 1; }
fi

# 4. Doctor.
echo "DOCTOR"
echo "  python : $VENV/bin/python ($("$VENV/bin/python" -c 'import manim;print("manim",manim.__version__)'))"
echo "  latex  : $(command -v latex || echo "$(cat "$HOME_DIR/.texbin" 2>/dev/null)/latex")"
echo "  ffmpeg : $(command -v ffmpeg)"
if "$VENV/bin/python" -c "import kokoro" 2>/dev/null; then k=yes; else k=no; fi
echo "  tts    : kokoro=$k gemini=$([ -n "${GEMINI_API_KEY:-}" ] || [ -f "$HOME/.gemini_api_key" ] && echo yes || echo no) elevenlabs=$([ -n "${ELEVENLABS_API_KEY:-}" ] && echo yes || echo no)"
echo "READY"
