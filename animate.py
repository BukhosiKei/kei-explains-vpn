"""
animate.py — reusable motion primitives for Kei Explains videos.

Alpha-based primitives build an explicit mask so they work on
MoviePy 1.0.3 + Pillow 10+, where set_opacity(lambda) is broken.
"""
from moviepy.editor import ColorClip, CompositeVideoClip
import numpy as np


# ---------------------------------------------------------------
# internal helper: attach a time-based alpha mask to a clip
# ---------------------------------------------------------------
def _apply_alpha(clip, alpha_fn):
    """
    Build a proper MoviePy mask (ismask=True) whose frame at time t is
    alpha_fn(t) * 255, then attach it to the clip.
    """
    from moviepy.editor import VideoClip
    w, h = clip.size

    def make_frame(t):
        a = float(alpha_fn(t))
        a = max(0.0, min(1.0, a))
        return np.ones((h, w), dtype=float) * a

    mask = VideoClip(make_frame, duration=clip.duration)
    mask.ismask = True
    return clip.set_mask(mask)


# ---------------------------------------------------------------
# slide_in
# ---------------------------------------------------------------
def slide_in(clip, offset_px=60, delay=0.0, duration=0.6, axis="x"):
    final_pos = clip.pos(0)

    def pos(t):
        if t <= delay:
            dx = offset_px
        elif t >= delay + duration:
            dx = 0
        else:
            p = (t - delay) / duration
            eased = 1 - (1 - p) ** 3
            dx = offset_px * (1 - eased)

        if axis == "x":
            return (final_pos[0] - dx, final_pos[1])
        return (final_pos[0], final_pos[1] - dx)

    return clip.set_position(pos)


# ---------------------------------------------------------------
# fade_in
# ---------------------------------------------------------------
def fade_in(clip, delay=0.0, duration=0.5):
    def alpha(t):
        if t <= delay:
            return 0.0
        if t >= delay + duration:
            return 1.0
        return (t - delay) / duration

    return _apply_alpha(clip, alpha)


# ---------------------------------------------------------------
# fade_out
# ---------------------------------------------------------------
def fade_out(clip, delay=0.0, duration=0.5):
    clip_dur = clip.duration
    start = clip_dur - duration - delay

    def alpha(t):
        if t <= start:
            return 1.0
        if t >= start + duration:
            return 0.0
        return 1.0 - (t - start) / duration

    return _apply_alpha(clip, alpha)


# ---------------------------------------------------------------
# pop_in (scale + fade)
# ---------------------------------------------------------------
def pop_in(clip, delay=0.0, duration=0.35, scale_from=0.7):
    def factor(t):
        if t <= delay:
            return scale_from
        if t >= delay + duration:
            return 1.0
        p = (t - delay) / duration
        eased = 1 - (1 - p) ** 3
        return scale_from + (1.0 - scale_from) * eased

    scaled = clip.resize(factor)

    def alpha(t):
        if t <= delay:
            return 0.0
        if t >= delay + duration:
            return 1.0
        return (t - delay) / duration

    return _apply_alpha(scaled, alpha)


# ---------------------------------------------------------------
# pulse_glow
# ---------------------------------------------------------------
def pulse_glow(clip, period=2.0, min_opacity=0.4, max_opacity=1.0):
    def alpha(t):
        phase = (t % period) / period
        return min_opacity + (max_opacity - min_opacity) * (
            0.5 - 0.5 * np.cos(2 * np.pi * phase)
        )

    return _apply_alpha(clip, alpha)


# ---------------------------------------------------------------
# drift_up
# ---------------------------------------------------------------
def drift_up(clip, px=12):
    dur = clip.duration
    base_pos = clip.pos(0)
    if isinstance(base_pos[0], str) or isinstance(base_pos[1], str):
        return clip
    bx, by = base_pos
    def pos(t):
        return (bx, by - (px * t / dur))
    return clip.set_position(pos)


# ---------------------------------------------------------------
# stagger
# ---------------------------------------------------------------
def stagger(clips, delay_each=0.2, start=0.0):
    out = []
    t = start
    for c in clips:
        out.append(c.set_start(t))
        t += delay_each
    return out
