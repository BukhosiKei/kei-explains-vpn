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
