"""Original curly-brace characters with personality, for 3b1b-style videos.

Never draw pi creatures; these braces are the house cast.

    from characters import Buddy, cast, react, Reaction
    trio, nar = cast()                       # three listeners bottom-left, narrator bottom-right
    self.add(*trio, nar)
    self.play(trio[0].scratch_head())        # every reaction is an Animation
    self.play(*react([*trio, nar], "reveal"))  # each one reacts by its temperament, staggered

Reactions read the character's state when they START, so you can build them early
(e.g. as arguments to a helper) and still chain them safely.
Two reactions on the SAME character must not run at once; different characters can overlap.

Temperaments: curious (leans in, looks, nods), skeptic (squints, shrugs, scratches head),
eager (hops, gasps, smiles big), calm (narrator: slow blinks, small nods, smiles).
"""
import random

import numpy as np
from manim import (DOWN, LEFT, ORIGIN, RIGHT, TAU, UP, DL, DR, WHITE, Animation, AnimationGroup,
                   ArcBetweenPoints, Circle, Dot, LaggedStart, MathTex, Mobject, VGroup, VMobject,
                   rate_functions)

NARRATOR = "#D97757"


def _mouth(width, kind):
    angle = {"flat": -0.25, "smile": -1.6, "grin": -2.4, "frown": 1.1, "o": -TAU * 0.92}[kind]
    w = width * (0.45 if kind == "o" else 1.0)
    m = ArcBetweenPoints(LEFT * w / 2, RIGHT * w / 2, angle=angle, num_components=12)
    return m


class Buddy(VGroup):
    def __init__(self, color="#58C4DD", height=1.4, flip=False, temperament="curious", **kw):
        super().__init__(**kw)
        self.temperament = temperament
        self.h = height
        body = MathTex(r"\{", color=color).set_stroke(color, width=7)
        body.set_fill(color, opacity=1).stretch_to_fit_height(height).stretch_to_fit_width(height * 0.42)
        if flip:
            body.flip(UP)
        r = height * 0.1
        eyes, pupils = VGroup(), VGroup()
        top = body.get_top() + DOWN * height * 0.18
        for dx in (-0.55, 0.55):
            e = Circle(radius=r, color=WHITE, fill_opacity=1, stroke_width=0).move_to(top + RIGHT * dx * r * 2.1)
            eyes.add(e)
            pupils.add(Dot(radius=r * 0.5, color="#111111").move_to(e))
        self.mouth_w = r * 2.1
        mouth = _mouth(self.mouth_w, "flat").set_stroke("#111111", width=4.5)
        mouth.move_to(eyes.get_center() + DOWN * r * 1.75)
        mouth_bg = mouth.copy().set_stroke(color, width=12)  # halo so the mouth reads on the body
        hands = VGroup(*[ArcBetweenPoints(ORIGIN, UP * r * 1.6, angle=-1.2 * s).set_stroke(color, width=7)
                         for s in (1, -1)])
        hands[0].next_to(body, LEFT, buff=0.02).shift(UP * height * 0.05)
        hands[1].next_to(body, RIGHT, buff=0.02).shift(UP * height * 0.05)
        hands.set_stroke(opacity=0)
        self.body, self.eyes, self.pupils, self.mouth_bg, self.mouth, self.hands = body, eyes, pupils, mouth_bg, mouth, hands
        self.add(body, hands, eyes, pupils, mouth_bg, mouth)

    # ---- low-level pose edits (applied to a fresh copy of the start state each frame) ----
    def _set_mouth(self, kind, a, start):
        tgt = _mouth(self.mouth_w, kind).move_to(start.mouth.get_center())
        tgt.match_style(start.mouth)
        self.mouth.interpolate(start.mouth, tgt, a)
        self.mouth_bg.interpolate(start.mouth_bg, tgt.copy().match_style(start.mouth_bg), a)

    def _look(self, point, a, start):
        for e, p, p0 in zip(self.eyes, self.pupils, start.pupils):
            v = np.array(point) - e.get_center()
            n = np.linalg.norm(v)
            off = v / n * e.width * 0.22 if n > 1e-6 else ORIGIN
            p.move_to(p0.get_center() * (1 - a) + (e.get_center() + off) * a)

    # ---- reactions (each returns an Animation) ----
    def look_at(self, target, run_time=0.5):
        p = target.get_center() if isinstance(target, Mobject) else np.array(target)
        return Reaction(self, lambda m, a, s: m._look(p, a, s), run_time=run_time)

    def blink(self, run_time=0.25):
        def f(m, a, s):
            k = 1 - 0.9 * rate_functions.there_and_back(a)
            for part in [*m.eyes, *m.pupils]:
                part.stretch(k, 1)
        return Reaction(self, f, run_time=run_time, rate_func=rate_functions.linear)

    def nod(self, times=2, run_time=0.8):
        def f(m, a, s):
            d = abs(np.sin(a * times * np.pi)) * self.h * 0.06
            VGroup(m.eyes, m.pupils, m.mouth, m.mouth_bg).shift(DOWN * d)
            for p in m.pupils:
                p.shift(DOWN * d * 0.6)
        return Reaction(self, f, run_time=run_time, rate_func=rate_functions.linear)

    def lean_in(self, target, angle=0.18, run_time=1.2):
        p = target.get_center() if isinstance(target, Mobject) else np.array(target)
        side = -1 if p[0] > self.get_center()[0] else 1
        def f(m, a, s):
            k = rate_functions.there_and_back_with_pause(a, pause_ratio=0.5)
            m.rotate(side * angle * k, about_point=s.body.get_bottom())
            m._look(p, min(1, a * 3), s)
        return Reaction(self, f, run_time=run_time, rate_func=rate_functions.linear)

    def shrug(self, run_time=1.0):
        def f(m, a, s):
            k = rate_functions.there_and_back_with_pause(a, pause_ratio=0.4)
            m.hands.set_stroke(opacity=k)
            m.hands[0].shift(UP * k * self.h * 0.12)
            m.hands[1].shift(UP * k * self.h * 0.12)
            for p, e in zip(m.pupils, m.eyes):
                p.shift(UP * e.width * 0.2 * k)
            m._set_mouth("frown", k, s)
        return Reaction(self, f, run_time=run_time, rate_func=rate_functions.linear)

    def scratch_head(self, run_time=1.4):
        def f(m, a, s):
            show = rate_functions.there_and_back_with_pause(a, pause_ratio=0.7)
            hand = m.hands[1]
            hand.set_stroke(opacity=show)
            hand.move_to(s.body.get_corner(UP + RIGHT) + RIGHT * 0.05)
            hand.shift(UP * np.sin(a * 6 * np.pi) * self.h * 0.03 * show)
            m.eyes[0].stretch(1 - 0.5 * show, 1)
            m.pupils[0].stretch(1 - 0.5 * show, 1)
            m._look(s.eyes.get_center() + UP * 2 + RIGHT, show, s)
            m._set_mouth("frown", show * 0.6, s)
        return Reaction(self, f, run_time=run_time, rate_func=rate_functions.linear)

    def squint(self, run_time=1.0):
        def f(m, a, s):
            k = rate_functions.there_and_back_with_pause(a, pause_ratio=0.5)
            for part in [*m.eyes, *m.pupils]:
                part.stretch(1 - 0.55 * k, 1)
        return Reaction(self, f, run_time=run_time, rate_func=rate_functions.linear)

    def surprise(self, run_time=0.9):
        def f(m, a, s):
            k = rate_functions.there_and_back_with_pause(a, pause_ratio=0.4)
            for e in m.eyes:
                e.scale(1 + 0.35 * k)
            for p in m.pupils:
                p.scale(1 - 0.3 * k)
            m.shift(UP * self.h * 0.12 * rate_functions.there_and_back(a))
            m._set_mouth("o", k, s)
        return Reaction(self, f, run_time=run_time, rate_func=rate_functions.linear)

    def smile(self, kind="smile", run_time=0.6):
        """Persistent: the mouth stays in `kind` (smile, grin, flat, frown) after the animation."""
        return Reaction(self, lambda m, a, s: m._set_mouth(kind, a, s), run_time=run_time)

    def hop(self, height=0.3, run_time=0.5):
        return Reaction(self, lambda m, a, s: m.shift(UP * height * rate_functions.there_and_back(a)),
                        run_time=run_time, rate_func=rate_functions.linear)


class Reaction(Animation):
    """Rebuilds the character from its START state every frame, then applies fn(mob, alpha, start)."""

    def __init__(self, mob, fn, **kw):
        self.fn = fn
        super().__init__(mob, **kw)

    def begin(self):
        self.start = self.mobject.copy()
        super().begin()

    def interpolate_mobject(self, alpha):
        m = self.mobject
        m.become(self.start)
        # become() copies points/style but keeps attribute links to OUR submobjects
        self.fn(m, self.rate_func(alpha), self.start)


TEMPERAMENT_MOVES = {
    #            confused                  reveal                       agree / point     doubt
    "curious": {"confused": "squint",      "reveal": "nod",             "agree": "nod",   "doubt": "lean_in"},
    "skeptic": {"confused": "scratch_head", "reveal": "squint",         "agree": "nod",   "doubt": "shrug"},
    "eager":   {"confused": "shrug",       "reveal": "surprise",        "agree": "hop",   "doubt": "scratch_head"},
    "calm":    {"confused": "blink",       "reveal": "smile",           "agree": "nod",   "doubt": "blink"},
}


def react(chars, event, target=None, lag=0.15):
    """Each character reacts to `event` by its temperament, slightly staggered. Returns [Animation]."""
    anims = []
    for c in chars:
        move = TEMPERAMENT_MOVES[c.temperament][event]
        fn = getattr(c, move)
        anims.append(fn(target if target is not None else ORIGIN) if move == "lean_in" else fn())
    return [LaggedStart(*anims, lag_ratio=lag)]


def cast(seed=0):
    """Three listeners (curious blue, skeptic dark blue, eager teal) bottom-left; calm narrator bottom-right."""
    trio = VGroup(Buddy("#58C4DD", 1.2, temperament="curious"),
                  Buddy("#3d7fa3", 1.1, temperament="skeptic"),
                  Buddy("#5CD0B3", 1.3, temperament="eager")).arrange(RIGHT, buff=0.35, aligned_edge=DOWN)
    trio.to_corner(DL, buff=0.3)
    nar = Buddy(NARRATOR, 1.5, flip=True, temperament="calm").to_corner(DR, buff=0.3).shift(UP * 0.3)  # room for the credit
    return trio, nar


def idle_blinks(chars, seconds, rng=random.Random(1)):
    """Fill a hold with one or two staggered blinks so nobody looks frozen. Returns [Animation] of `seconds`."""
    from manim import Wait
    if seconds < 0.6:
        return [Wait(seconds)]
    who = rng.sample(list(chars), k=min(2, len(chars)))
    starts = sorted(rng.uniform(0.1, max(0.15, seconds - 0.35)) for _ in who)
    parts = []
    for c, st in zip(who, starts):
        parts.append(AnimationGroup(Wait(st), c.blink(), lag_ratio=1.0))
    return [AnimationGroup(*parts, Wait(seconds))]
