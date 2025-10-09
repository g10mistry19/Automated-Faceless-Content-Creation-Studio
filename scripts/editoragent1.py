import os
import random
import re
#import moviepy.editor as mpe
from moviepy import *

# --- Helper Function ---
def create_safe_filename(text: str, max_length: int = 50):
    """Cleans a string to create a safe filename base."""
    print("helper fxn")
    sanitized = re.sub(r'[^\w\s-]', '', text).strip().lower()
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized[:max_length]

# --- Main Agent Node ---
def editor_agent_node(state):
    """
    The main agent node that assembles all assets into the final video.
    """
    print("\n--- Running Editor Agent ---")
    
    # --- 1. Ingest all assets from the state ---
    topic = state.get("topic")
    visual_paths = state.get("visual_paths")
    audio_paths = state.get("audio_paths")
    narration_timings = state.get("narration_timings")

    # Validate that all necessary assets are present
    if not all([topic, visual_paths, audio_paths, narration_timings]):
        print("❌ Error: Missing required assets in state. Cannot build video.")
        print(f"   Topic: {'Exists' if topic else 'Missing'}")
        print(f"   Visuals: {'Exists' if visual_paths else 'Missing'}")
        print(f"   Audios: {'Exists' if audio_paths else 'Missing'}")
        print(f"   Timings: {'Exists' if narration_timings else 'Missing'}")
        return state

    # --- 2. Create a sequence of visual clips, timed to the narrations ---
    scene_clips = []
    print("🎬 Assembling individual video scenes...")
    for i, timing in enumerate(narration_timings):
        try:
            visual_path = visual_paths[i]
            audio_path = audio_paths[i]
            duration = timing["duration"]
            
            # Load the corresponding audio clip for this scene
            audio_clip = AudioFileClip(audio_path)

            # --- HYBRID VISUAL LOGIC ---
            if visual_path.endswith(('.png', '.jpg', '.jpeg')):
                # It's an image: apply Ken Burns effect (zoom in)
                visual_clip = ImageClip(visual_path).set_duration(duration)
                # Resize to be slightly larger than the final frame for the zoom
                visual_clip = visual_clip.resize(width=int(1080 * 1.15))
                # Animate the zoom by cropping
                visual_clip = visual_clip.fx(vfx.crop, x_center=visual_clip.w/2, y_center=visual_clip.h/2, 
                               width=1080, height=1920)
            else:
                # It's a video: trim, resize, and crop
                visual_clip = VideoFileClip(visual_path)
                # Ensure the video is long enough, otherwise loop it
                if visual_clip.duration < duration:
                    visual_clip = visual_clip.fx(vfx.loop, duration=duration)
                else:
                    visual_clip = visual_clip.subclip(0, duration)
                
                visual_clip = visual_clip.resize(height=1920).crop(x_center=visual_clip.w/2, width=1080)

            # Set the audio for this specific scene
            visual_clip = visual_clip.set_audio(audio_clip)
            scene_clips.append(visual_clip)
            
        except IndexError:
            print(f"⚠️ Warning: Not enough visuals or audios for narration {i+1}. Skipping this scene.")
        except Exception as e:
            print(f"⚠️ Warning: Could not process scene {i+1}: {e}")

    if not scene_clips:
        print("❌ Error: No scenes could be created. Stopping video production.")
        return state
    
    # --- 3. Assemble the main video timeline ---
    final_video = concatenate_videoclips(scene_clips)

    # --- 4. Create animated subtitles ---
    print("✍️ Creating and adding animated subtitles...")
    subtitle_clips = []
    for timing in narration_timings:
        subtitle = TextClip(
            timing["text"],
            fontsize=70, color='white', font='Arial-Bold',
            stroke_color='black', stroke_width=3,
            method='caption', size=(900, None) # 900px width allows text to wrap
        )
        subtitle = subtitle.set_position(('center', 0.8), relative=True) # Positioned at 80% from the top
        subtitle = subtitle.set_start(timing["start"]).set_duration(timing["duration"])
        # Fade in/out for a smooth appearance
        subtitle = subtitle.crossfadein(0.3).crossfadeout(0.3)
        subtitle_clips.append(subtitle)

    # --- 5. Add background music ---
    print("🎵 Adding background music...")
    try:
        music_folder = os.path.join("assets", "music")
        music_files = [f for f in os.listdir(music_folder) if f.endswith('.mp3')]
        if music_files:
            music_path = os.path.join(music_folder, random.choice(music_files))
            music_clip = AudioFileClip(music_path).fx(afx.volumex, 0.1) # Set volume to 10%
            
            # Make music match video length
            if music_clip.duration > final_video.duration:
                music_clip = music_clip.subclip(0, final_video.duration)
            
            # Combine the main narration audio with the background music
            final_audio = CompositeAudioClip([final_video.audio, music_clip])
            final_video.audio = final_audio
    except Exception as e:
        print(f"⚠️ Warning: Could not add background music: {e}")

    # --- 6. Add watermark ---
    print("💧 Adding watermark...")
    logo_path = os.path.join("assets", "logo.png")
    if os.path.exists(logo_path):
        logo = (ImageClip(logo_path)
                .set_duration(final_video.duration)
                .resize(height=80) # Set logo height to 80 pixels
                .margin(right=20, top=20, opacity=0) # Add margin
                .set_pos(("right","top")))
        # Composite all layers: the video, the logo, and all the subtitle clips
        final_video = CompositeVideoClip([final_video, logo, *subtitle_clips])
    else:
        print("⚠️ Warning: 'assets/logo.png' not found. Skipping watermark.")
        final_video = CompositeVideoClip([final_video, *subtitle_clips])

    # --- 7. Render the final video ---
    output_filename = f"{create_safe_filename(topic)}.mp4"
    output_path = os.path.join("output", output_filename)
    print(f"⏳ Rendering final video to: {output_path} (This may take a while)...")
    
    # Use standard presets for high compatibility
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)

    state["final_video_path"] = output_path
    print("--- Editor Agent Finished ---")
    return state

# --- Main block for direct testing ---
if __name__ == '__main__':
    # This agent is complex and relies on the outputs of all previous agents.
    # A direct test would require creating many dummy asset files.
    # It's best tested as part of the full agent graph after running other agents.
    print("\n=============================================")
    print("✅ Editor Agent is ready to be integrated into the main workflow.")
    print("   To test directly, you must create dummy asset files (visuals, audios)")
    print("   and populate a 'test_state' dictionary with their paths and timings.")
    print("=============================================")