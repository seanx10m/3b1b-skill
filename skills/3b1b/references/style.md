# The 3b1b style

What makes a 3Blue1Brown video feel like one, written as rules you can check.

## Story

- **Open on a question, not a title card.** The first line is a puzzle the viewer wants answered.
- **Concrete before abstract.** Show one specific case (n = 3, this triangle, these two vectors) before the general rule.
- **Let the viewer almost invent it.** Lead them to the step just before the insight, pause, then show it. "You could have discovered this."
- **The picture carries the argument.** The narration points at the picture; it never explains something that is not on screen.
- **Formula last.** The equation shows up as a compact name for what the viewer already watched happen.
- **One idea per scene.** A scene ends when its idea lands. Do not cram.
- **Linger on the aha.** After the key transform, hold 1-2 s of stillness before the next line.
- **End with a wider view.** One closing line on where this idea leads next, not a recap.

## Palette

Dark background, a few saturated colors, each with one fixed meaning for the whole video.

| Role | Manim constant | Hex |
|---|---|---|
| background | - | `#0f0f14` |
| primary quantity | `BLUE` (`BLUE_C`) | `#58C4DD` |
| second quantity | `YELLOW` | `#FFFF00` |
| third quantity | `TEAL` | `#5CD0B3` |
| contrast / error / warning | `RED` | `#FC6255` |
| result / highlight | `GOLD` | `#F0AC5F` |
| neutral text and axes | `WHITE`, `GREY_B` | |

- Decide the color key in the beat sheet and never change it. If `x` is blue in the picture, `x` is blue in every equation.
- At most 3 meaning-colors on screen at once. Everything else is white or grey.
- Fills are translucent (`fill_opacity` 0.3-0.6) so overlaps stay readable.

## Typography

- Math is LaTeX (`MathTex`), always. Prose labels are `Tex`. Avoid `Text` except for code.
- Sizes at 480p draft: titles 48-56, body 36-40, labels 28-32. Nothing under 24.
- Labels sit next to the thing they name and move with it (`always_redraw` or `add_updater`).
- Keep 0.5 units of margin from every frame edge.

## Motion

- **Transform, do not replace.** When an expression changes, morph it (`TransformMatchingTex`) so the viewer sees which part moved. Never fade one equation out and another in.
- **Draw in the order you would explain.** `Create` for shapes, `Write` for text, `GrowFromCenter` / `GrowArrow` for arrows.
- **Continuous change uses a `ValueTracker`.** Sliding a parameter and watching the picture respond is the signature 3b1b move.
- **Point with motion, not arrows of text.** `Indicate`, `Circumscribe`, `SurroundingRectangle`, `Flash` say "look here".
- **Smooth by default.** `rate_func=smooth` (Manim's default); `there_and_back` for a demo wiggle; `linear` only for steady sweeps.
- **The camera moves with purpose.** Zoom into the part that matters (`MovingCameraScene`); do not drift for effect.
- Typical run times: write a short equation 1-1.5 s, a transform 1-2 s, an emphasis 0.6-1 s.
- Clean up: `FadeOut` what is no longer needed before the next idea. The frame never fills with leftovers.

## Reject list (check the contact sheet against this)

- Text or shapes overlapping each other or touching the frame edge.
- A label too small to read at 480p.
- A color whose meaning changed between scenes.
- A wall of text, or a full sentence on screen that the voice is also saying.
- A frame frozen for more than 3 s with no reason.
- An equation that appears without the picture it describes.
- Generic "AI slop": gradient titles, emoji, bullet lists on screen, decorative particles, glowing logos.
