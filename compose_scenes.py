"""
compose_scenes.py — bake each scene's animation into a self-contained MP4.

Uses PIL for image compositing (correct alpha handling) and MoviePy only
for encoding the resulting frames. Bypasses MoviePy's composite bugs with
transparent layers.
"""
from pathlib import Path
import numpy as np
from PIL import Image
from moviepy.editor import VideoClip

ROOT = Path(__file__).parent
L    = ROOT / "assets_layers"
OUT_DIR = ROOT / "scenes_composed"
OUT_DIR.mkdir(exist_ok=True)

W, H, FPS = 1080, 1920, 30

# Scene durations (seconds). Sum should be ≤ your target runtime.
SCENE_DURATIONS = {
    1: 3.0,
    2: 2.5,
    3: 2.5,
    4: 2.5,
    5: 2.5,
    6: 3.0,
    7: 2.5,
    8: 2.5,
    9: 3.0,
    10: 3.0,
    11: 3.0,
}

# Per-scene layer list. Order matters — later layers draw on top.
SCENES = {
    1: [
        ("scene01_base",       "fade",   0.0, 0.4),
        ("scene01_layer1_boy", "slide_x", 0.25, 0.9, 140),
        ("scene01_layer2_title","pop",   0.7, 0.6, 0.7),
    ],
    2: [
        ("scene02_base",        "fade",   0.0, 0.4),
        ("scene02_layer1_cars", "slide_x", 0.2, 1.0, 400),
        ("scene02_layer2_label","fade",   0.9, 0.5),
    ],
    3: [
        ("scene03_base",           "fade",   0.0, 0.4),
        ("scene03_layer1_watcher", "slide_x", 0.25, 0.9, -200),
        ("scene03_layer2_question","pop",   0.8, 0.55, 0.5),
        ("scene03_layer3_tagline", "fade",   1.4, 0.5),
    ],
    4: [
        ("scene04_base",           "fade",   0.0, 0.4),
        ("scene04_layer1_hacker",  "slide_x", 0.2, 0.9, -240),
        ("scene04_layer2_exposed", "pop",   0.85, 0.5, 0.55),
        ("scene04_layer3_tagline", "fade",   1.5, 0.5),
    ],
    5: [
        ("scene05_base",         "fade", 0.0, 0.4),
        ("scene05_layer1_shield","pop",  0.3, 0.7, 0.55),
        ("scene05_layer2_tagline","fade",1.1, 0.5),
    ],
    6: [
        ("scene06_base",         "fade",   0.0, 0.4),
        ("scene06_layer1_cars",  "slide_x", 0.2, 0.8, 220),
        ("scene06_layer2_badge", "pop",   0.85, 0.5, 0.6),
        ("scene06_layer3_tagline","fade",  1.5, 0.5),
    ],
    7: [
        ("scene07_base",          "fade",   0.0, 0.4),
        ("scene07_layer1_packets","slide_x", 0.3, 0.9, 260),
        ("scene07_layer2_tagline","fade",   1.3, 0.5),
    ],
    8: [
        ("scene08_base",         "fade", 0.0, 0.4),
        ("scene08_layer1_arrows","fade", 0.5, 0.6),
        ("scene08_layer2_tagline","fade",1.2, 0.5),
    ],
    9: [
        ("scene09_base",         "fade", 0.0, 0.4),
        ("scene09_layer1_bubble","pop",  0.4, 0.5, 0.7),
        ("scene09_layer2_badge", "pop",  0.9, 0.5, 0.7),
        ("scene09_layer3_tagline","fade",1.5, 0.5),
    ],
    10: [
        ("scene10_base",         "fade",   0.0, 0.4),
        ("scene10_layer1_boy",   "slide_x", 0.3, 0.9, 160),
        ("scene10_layer2_ipcards","pop",   1.0, 0.6, 0.7),
    ],
    11: [
        ("scene11_base",         "fade",   0.0, 0.4),
        ("scene11_layer1_text",  "slide_y", 0.3, 0.8, 120),
        ("scene11_layer2_lock",  "pop",   0.9, 0.6, 0.5),
    ],
}


def ease_out_cubic(p):
    return 1 - (1 - p) ** 3


def layer_state(t, kind, delay, dur, *args):
    """Return (alpha, x_offset, y_offset, scale) at time t."""
    if t <= delay:
        p = 0.0
    elif t >= delay + dur:
        p = 1.0
    else:
        p = (t - delay) / dur
    eased = ease_out_cubic(p)

    alpha = 1.0
    x = 0
    y = 0
    scale = 1.0

    if kind == "fade":
        alpha = 0.0 if t <= delay else (1.0 if t >= delay + dur else p)
    elif kind == "slide_x":
        offset = args[0]
        x = int(offset * (1 - eased))
        alpha = 0.0 if t <= delay else (1.0 if t >= delay + dur * 0.5 else p * 2)
    elif kind == "slide_y":
        offset = args[0]
        y = int(offset * (1 - eased))
        alpha = 0.0 if t <= delay else (1.0 if t >= delay + dur * 0.5 else p * 2)
    elif kind == "pop":
        start_scale = args[0]
        scale = start_scale + (1 - start_scale) * eased
        alpha = 0.0 if t <= delay else (1.0 if t >= delay + dur * 0.7 else p / 0.7)

    return alpha, x, y, scale


def load_layer(name):
    p = L / f"{name}.png"
    if not p.exists():
        return None
    img = Image.open(str(p)).convert("RGBA")
    if img.size != (W, H):
        img = img.resize((W, H), Image.LANCZOS)
    return img


def compose_scene(scene_num, duration):
    spec = SCENES[scene_num]
    layers = [(load_layer(name), name, kind, delay, dur, *rest)
              for (name, kind, delay, dur, *rest) in spec]
    layers = [l for l in layers if l[0] is not None]
    if not layers:
        return None

    def make_frame(t):
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for img, name, kind, delay, dur, *args in layers:
            alpha, x, y, scale = layer_state(t, kind, delay, dur, *args)
            if alpha <= 0:
                continue

            layer_img = img
            if scale != 1.0:
                new_size = (max(1, int(W * scale)), max(1, int(H * scale)))
                layer_img = layer_img.resize(new_size, Image.LANCZOS)
                # re-center scaled layer
                dx = (W - new_size[0]) // 2
                dy = (H - new_size[1]) // 2
                # create temp canvas at full size, paste scaled into it centered
                tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                tmp.paste(layer_img, (dx, dy), layer_img)
                layer_img = tmp

            # apply alpha
            if alpha < 1.0:
                arr = np.array(layer_img, dtype=np.float32)
                arr[:, :, 3] *= alpha
                layer_img = Image.fromarray(arr.astype(np.uint8))

            # paste with offset (x, y)
            canvas.paste(layer_img, (x, y), layer_img)

        # Flatten over background colour (dark navy)
        bg = Image.new("RGB", (W, H), (7, 20, 38))
        bg.paste(canvas, (0, 0), canvas)
        return np.array(bg)

    return make_frame


def main():
    for num in sorted(SCENES.keys()):
        duration = SCENE_DURATIONS[num]
        print(f"Composing scene {num:02d} ({duration}s)...")
        make_frame = compose_scene(num, duration)
        if make_frame is None:
            print(f"  warn scene {num} empty, skipping")
            continue

        clip = VideoClip(make_frame, duration=duration)
        out = OUT_DIR / f"scene{num:02d}.mp4"
        clip.write_videofile(
            str(out), fps=FPS, codec="libx264", audio=False,
            bitrate="8M", preset="medium", threads=4,
        )
        print(f"  -> {out.name}")

    print("done")


if __name__ == "__main__":
    main()