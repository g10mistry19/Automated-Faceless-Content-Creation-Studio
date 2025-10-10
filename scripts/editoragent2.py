import os
import random
import re
from moviepy import *
from gtts import gTTS
from mutagen.mp3 import MP3

# --- Helper Function ---
def create_safe_filename(text: str, max_length: int = 50):
    """Cleans a string to create a safe filename base."""
    sanitized = re.sub(r'[^\w\s-]', '', text).strip().lower()
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized[:max_length]

# --- Main Agent Node ---
def editor_agent_node(state):
    """
    The main agent node that assembles all assets into the final video.
    """
    print("\n--- Running Editor Agent ---")
    
    topic = state.get("topic")
    visual_paths = state.get("visual_paths")
    audio_paths = state.get("audio_paths")
    narration_timings = state.get("narration_timings")

    if not all([topic, visual_paths, audio_paths, narration_timings]):
        print("❌ Error: Missing required assets in state. Cannot build video.")
        return state

    # DEFINITIVE FIX: Define the path to our bundled font file.
    font_path = os.path.join("assets", "InterVariable.ttf")
    if not os.path.exists(font_path):
        print(f"❌ FATAL ERROR: Font file not found at '{font_path}'.")
        print("   Please download the 'Inter' font and place 'Inter-Bold.otf' in the 'assets' folder.")
        return state

    scene_clips = []
    print("🎬 Assembling individual video scenes...")
    for i, timing in enumerate(narration_timings):
        try:
            visual_path = visual_paths[i]; audio_path = audio_paths[i]; duration = timing["duration"]
            audio_clip = AudioFileClip(audio_path)
            if visual_path.endswith(('.png', '.jpg', '.jpeg')):
                visual_clip = ImageClip(visual_path).set_duration(duration)
                visual_clip = visual_clip.resize(width=int(1080 * 1.15))
                visual_clip = visual_clip.fx(vfx.crop, x_center=visual_clip.w/2, y_center=visual_clip.h/2, width=1080, height=1920)
            else:
                visual_clip = VideoFileClip(visual_path)
                if visual_clip.duration < duration: visual_clip = visual_clip.fx(vfx.loop, duration=duration)
                else: visual_clip = visual_clip.subclip(0, duration)
                visual_clip = visual_clip.resize(height=1920).crop(x_center=visual_clip.w/2, width=1080)
            visual_clip = visual_clip.set_audio(audio_clip)
            scene_clips.append(visual_clip)
        except Exception as e:
            print(f"⚠️ Warning: Could not process scene {i+1}: {e}")

    if not scene_clips: print("❌ Error: No scenes could be created."); return state
    final_video = concatenate_videoclips(scene_clips)

    print("✍️ Creating and adding animated subtitles...")
    subtitle_clips = []
    for timing in narration_timings:
        subtitle = TextClip(timing["text"], font = font_path, font_size=70, color='white',
                            stroke_color='black', stroke_width=3, method='caption', size=(900, None))
        subtitle = subtitle.set_position(('center', 0.8), relative=True)
        subtitle = subtitle.set_start(timing["start"]).set_duration(timing["duration"])
        subtitle = subtitle.crossfadein(0.3).crossfadeout(0.3)
        subtitle_clips.append(subtitle)

    print("🎵 Adding background music...")
    try:
        music_folder = os.path.join("assets", "music")
        music_files = [f for f in os.listdir(music_folder) if f.endswith('.mp3')]
        if music_files:
            music_path = os.path.join(music_folder, random.choice(music_files))
            music_clip = AudioFileClip(music_path).fx(afx.volumex, 0.1)
            if music_clip.duration > final_video.duration: music_clip = music_clip.subclip(0, final_video.duration)
            final_audio = CompositeAudioClip([final_video.audio, music_clip])
            final_video.audio = final_audio
    except Exception as e: print(f"⚠️ Warning: Could not add background music: {e}")

    print("💧 Adding watermark...")
    logo_path = os.path.join("assets", "logo1.png")
    composite_layers = [final_video]
    if os.path.exists(logo_path):
        logo = (ImageClip(logo_path).set_duration(final_video.duration).resize(height=80)
                .margin(right=20, top=20, opacity=0).set_pos(("right","top")))
        composite_layers.append(logo)
    composite_layers.extend(subtitle_clips)
    final_video = CompositeVideoClip(composite_layers)

    output_filename = f"{create_safe_filename(topic)}.mp4"
    output_path = os.path.join("output", output_filename)
    print(f"⏳ Rendering final video to: {output_path} (Using GPU)...")
    
    try:
        final_video.write_videofile(output_path, codec="h264_nvenc", audio_codec="aac", fps=24, preset="fast", ffmpeg_params=['-profile:v', 'high'])
        state["final_video_path"] = output_path
    except Exception as e:
        print(f"❌ GPU rendering failed: {e}. Attempting CPU fallback...")
        try:
            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
            state["final_video_path"] = output_path
        except Exception as e2: print(f"❌ CPU rendering also failed: {e2}")

    print("--- Editor Agent Finished ---")
    return state

# --- Main block for direct testing ---
if __name__ == '__main__':
    print("🚀 --- Testing the Editor Agent directly --- 🚀")
    
    # Import additional libraries needed ONLY for the test setup
    from PIL import Image, ImageDraw, ImageFont
    
    # DEFINITIVE FIX: Define the font path once for the test setup.
    font_path = os.path.join("assets", "InterVariable.ttf")
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"FATAL: Font file not found at '{font_path}'. Please follow the setup instructions.")

    print("\n--- Setting up a dummy test environment ---")
    os.makedirs("output/audio/test_assets", exist_ok=True)
    os.makedirs("output/visuals/test_assets", exist_ok=True)
    os.makedirs("assets/music", exist_ok=True)
    
    dummy_narrations = ["This is the first test sentence.", "And this is the second part of the story."]
    dummy_audio_paths = []
    for i, text in enumerate(dummy_narrations):
        path = f"output/audio/test_assets/dummy_audio_{i+1}.mp3"
        gTTS(text=text, lang='en').save(path)
        dummy_audio_paths.append(path)
    
    dummy_visual_path = "output/visuals/test_assets/dummy_visual.jpg"
    ColorClip(size=(1080, 1920), color=(100, 100, 255), duration=1).save_frame(dummy_visual_path)
    dummy_visual_paths = [dummy_visual_path, dummy_visual_path]
    
    dummy_music_path = "assets/music/background_music.mp3"
    AudioClip(lambda t: 0, duration=10).write_audiofile(dummy_music_path, fps=44100)
    
    # --- DEFINITIVE FIX: Create the dummy logo using Pillow to bypass the MoviePy bug ---
    dummy_logo_path = "assets/logo.png"
    try:
        # Create a new transparent image
        img = Image.new('RGBA', (300, 100), (255, 255, 255, 0))
        d = ImageDraw.Draw(img)
        # Load the font
        fnt = ImageFont.truetype(font_path, 50)
        # Draw the text
        d.text((10,10), "Test Logo", font=fnt, fill=(255, 255, 255, 255))
        # Save the image
        img.save(dummy_logo_path, 'PNG')
    except Exception as e:
        print(f"❌ Failed to create dummy logo with Pillow: {e}")
        # As a fallback, create a simple color clip if Pillow fails
        ColorClip(size=(300, 100), color=(255, 255, 255), duration=1).save_frame(dummy_logo_path)


    # dummy_logo_path = "assets/logo1.png"
    # TextClip("Test Logo", font = font_path, font_size=50, color='white').save_frame(dummy_logo_path)

    print("✅ Dummy assets created successfully.")

    dummy_timings = []
    current_time = 0.0
    for i, path in enumerate(dummy_audio_paths):
        duration = MP3(path).info.length
        dummy_timings.append({"text": dummy_narrations[i], "start": current_time, "end": current_time + duration, "duration": duration})
        current_time += duration

    test_state = { "topic": "A Fully Automated Test Video", "visual_paths": dummy_visual_paths, "audio_paths": dummy_audio_paths, "narration_timings": dummy_timings, "narrations": dummy_narrations }

    print("\n--- Running the Editor Agent with dummy data ---")
    result_state = editor_agent_node(test_state)

    print("\n=============================================")
    final_path = result_state.get("final_video_path")
    if final_path: print(f"✅ Editor Agent test complete. Final video rendered at: {final_path}")
    else: print("❌ Editor Agent test failed to render a video.")
    print("=============================================")