# Manim cookbook (Community Edition 0.19+)

Patterns for the moves in style.md, then the traps that cost the most re-renders.

## Color-coded equation that morphs

```python
t2c = {"x": BLUE, "y": YELLOW}
a = MathTex("x", "+", "y", "=", "10", tex_to_color_map=t2c)
b = MathTex("x", "=", "10", "-", "y", tex_to_color_map=t2c)
self.play(Write(a), run_time=1.2)
self.play(TransformMatchingTex(a, b), run_time=1.5)
```

Split the TeX into the pieces you want to match. `TransformMatchingTex` pairs pieces by their TeX string.
For one long string use `substrings_to_isolate=["x", "y"]` instead of splitting by hand.

## A parameter slides, the picture follows

```python
k = ValueTracker(1)
ax = Axes(x_range=[-3, 3], y_range=[-1, 9], x_length=7, y_length=4.5)
curve = always_redraw(lambda: ax.plot(lambda x: k.get_value() * x**2, color=BLUE))
label = always_redraw(lambda: MathTex(f"k = {k.get_value():.1f}", color=BLUE).to_corner(UR))
self.add(ax, curve, label)
self.play(k.animate.set_value(2.5), run_time=2)
```

For a live number use `DecimalNumber` with `add_updater(lambda m: m.set_value(k.get_value()))`.

## Point at something

```python
self.play(Indicate(term), run_time=0.8)
self.play(Circumscribe(term, color=GOLD), run_time=1)
box = SurroundingRectangle(term, color=GOLD, buff=0.15); self.play(Create(box), run_time=0.6)
brace = Brace(segment, DOWN); txt = brace.get_tex(r"\tfrac12"); self.play(GrowFromCenter(brace), Write(txt))
```

## Zoom the camera

```python
class Scene3_Zoom(MovingCameraScene):
    def construct(self):
        self.play(self.camera.frame.animate.scale(0.5).move_to(target), run_time=1.5)
        self.play(Restore(self.camera.frame), run_time=1.5)   # after self.camera.frame.save_state()
```

## Linear algebra grid

```python
plane = NumberPlane(background_line_style={"stroke_opacity": 0.4})
v = Vector([1, 2], color=YELLOW)
self.add(plane, v)
self.play(ApplyMatrix([[1, 1], [0, 1]], VGroup(plane, v)), run_time=2)
```

## 3D

```python
class Scene4_Surface(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=65 * DEGREES, theta=-45 * DEGREES)
        s = Surface(lambda u, v: np.array([u, v, np.sin(u) * np.cos(v)]),
                    u_range=[-3, 3], v_range=[-3, 3], resolution=(24, 24))
        s.set_fill_by_checkerboard(BLUE_D, BLUE_E, opacity=0.7)
        self.play(Create(s), run_time=2)
        self.begin_ambient_camera_rotation(rate=0.15); self.wait(3)
```

Text in 3D scenes: `self.add_fixed_in_frame_mobjects(label)` so it faces the viewer.
`move_camera(..., run_time=)` counts toward the line's time budget.

## Layout helpers

- `VGroup(a, b, c).arrange(DOWN, buff=0.4)`; `.next_to(obj, RIGHT, buff=0.3)`; `.to_edge(UP, buff=0.5)`.
- `.scale_to_fit_width(config.frame_width - 1)` for anything that might run off frame.
- `self.play(FadeOut(*self.mobjects), run_time=0.6)` to clear between ideas.

## Traps

- `MathTex` needs LaTeX on PATH. If you see `latex: not found`, export the PATH line from SKILL.md Step 0.
- A `&` or `%` in `Tex` must be escaped (`\&`, `\%`).
- `always_redraw` objects still need `self.add(...)` once.
- `TransformMatchingTex` falls back to a plain fade when pieces do not match. Split the TeX so they do.
- `Transform(a, b)` leaves `a` on screen under `b`'s shape; use `ReplacementTransform` when you reference `b` later.
- Updaters keep running during `wait()`; remove them (`clear_updaters()`) when the motion should stop.
- The lint script reads literal durations only. Keep `dur = 3.1` style literals, not values loaded from JSON at runtime.
- Draft at 480p15. Re-render final at 1080p30 once only, after feedback settles.
