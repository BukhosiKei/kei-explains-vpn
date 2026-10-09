"""
render_video_final.py — stitch composed scenes + VO + music + captions.
MoviePy only concatenates finished MP4s, so no alpha/transparency bugs.
"""
from pathlib import Path
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    CompositeAudioClip, concatenate_videoclips, TextClip, afx,
)

ROOT    = Path(__file__).parent
SCENES  = ROOT / "scenes_composed"
VO      = ROOT / "vo.mp3"
MUSIC   = ROOT / "music.mp3"
ENDCARD = ROOT / "assets_layers" / "endcard.png"   # optional
OUT     = ROOT / "Video_06_What_Is_a_VPN_animated.mp4"

W, H, FPS = 1080, 1920, 30

# ---------------------------------------------------------------
# Load composed scenes
# ---------------------------------------------------------------
scene_files = sorted(SCENES.glob("scene*.mp4"))
if not scene_files:
    raise SystemExit(f"No scenes found in {SCENES}")

print("Loaded scenes:")
scene_clips = []
for f in scene_files:
    clip = VideoFileClip(str(f))
    scene_clips.append(clip)
    print(f"  {f.name}: {clip.duration:.2f}s")

timeline = concatenate_videoclips(scene_clips, method="compose")
print(f"Total timeline: {timeline.duration:.2f}s")

# ---------------------------------------------------------------
# VO — everything hinges on this being present
# ---------------------------------------------------------------
if not VO.exists():
    raise SystemExit(f"Missing VO: {VO}")
vo = AudioFileClip(str(VO))
print(f"VO duration: {vo.duration:.3f}s")

# Final video duration = VO + small tail for the endcard
DURATION = round(max(timeline.duration, vo.duration + 0.4), 2)

# ---------------------------------------------------------------
# Captions — one per scene, timed to the composed scene lengths
# ---------------------------------------------------------------
CAPTIONS = [
    "WHAT IS A VPN?",
    "PUBLIC ROAD",
    "WHO'S WATCHING?",
    "EXPOSED?",
    "A VPN CHANGES THAT",
    "ENCRYPTED TUNNEL",
    "VPN SERVER",
    "YOU → VPN → WEB",
    "VPN IP SHOWN",
    "REAL IP HIDDEN",
    "PRIVATE TUNNEL",
    "",   # endcard — no caption
]

# compute caption timings from actual scene boundaries
cap_times = []
t = 0
for clip in scene_clips:
    cap_times.append((t, t + clip.duration))
    t += clip.duration

CAP_Y = 1500
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

cap_clips = []
for (s, e), text in zip(cap_times, CAPTIONS):
    if not text.strip():
        continue   # skip empty captions
    cap = (TextClip(text, fontsize=64, color="white", font=FONT,
                    stroke_color="black", stroke_width=4,
                    method="caption", size=(W - 120, None))
           .set_start(s).set_end(e).set_position(("center", CAP_Y)))
    cap_clips.append(cap)

# ---------------------------------------------------------------
# Audio — VO + music with ducking
# ---------------------------------------------------------------
tracks = [vo.volumex(0.707)]  # ~ -3 dB peak
if MUSIC.exists():
    m = (AudioFileClip(str(MUSIC))
         .volumex(0.079)  # ~ -22 dB
         .fx(afx.audio_loop, duration=DURATION)
         .audio_fadeout(2.0))
    tracks.append(m)
    print(f"Music: {MUSIC.name}")
else:
    print("No music.mp3 — VO only")

mixed = CompositeAudioClip(tracks).set_duration(DURATION)

# ---------------------------------------------------------------
# Compose final
# ---------------------------------------------------------------
final = (CompositeVideoClip([timeline, *cap_clips], size=(W, H))
         .set_audio(mixed)
         .set_duration(DURATION))

print(f"Rendering {DURATION}s final video...")
final.write_videofile(
    str(OUT),
    fps=FPS,
    codec="libx264",
    audio_codec="aac",
    bitrate="10M",
    preset="medium",
    threads=4,
    temp_audiofile=str(ROOT / "temp_audio.m4a"),
    remove_temp=True,
)

print(f"\nOK: {OUT}  ({DURATION}s)")