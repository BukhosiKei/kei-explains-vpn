# Kei Explains — Video 06: What is a VPN?

An animated 30-second explainer built as code — no video editor, no stock footage.

## Watch

[Video_06_What_Is_a_VPN_animated.mp4](./Video_06_What_Is_a_VPN_animated.mp4)

## What this is

A programmatic video pipeline that builds a vertical (1080×1920) explainer from:

- Hand-authored SVG scene layers
- A Python animation module (`animate.py`)
- Edge-TTS for voiceover
- PIL for alpha-correct compositing
- MoviePy + ffmpeg for encoding and audio mix

Every scene is layered: a base, plus animated elements that slide, pop, and fade.

## Pipeline

vo_script.txt ──► edge-tts ──► vo.mp3
│
SVG layers ─► rsvg-convert ─► PNG ──┤
├──► compose_scenes.py ──► scenes_composed/*.mp4
animate.py (motion primitives) ────┘
│
└──► render_video_final.py ──► Video_06.mp4


## Reproduce

```bash
# 1. Generate voiceover
edge-tts --voice en-US-GuyNeural --rate +5% \
  -f vo_script.txt --write-media vo.mp3

# 2. Rasterize SVG layers to PNGs
for f in assets_layers/*.svg; do
  rsvg-convert -w 1080 -h 1920 -b none "$f" -o "${f%.svg}.png"
done

# 3. Compose animated scenes (PIL)
python compose_scenes.py

# 4. Final render (MoviePy + ffmpeg)
python render_video_final.py

```

Requires: ffmpeg, rsvg-convert (librsvg), Python 3.11+, and the packages in requirements.txt

License
Code: MIT.
Content (script, VO, video): © Kei Explains.
