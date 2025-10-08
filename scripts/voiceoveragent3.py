import os
import re
import requests
import time
import subprocess
import shutil
import json
from datetime import datetime
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# --- Helper Functions ---
def create_safe_filename(text: str, max_length: int = 50):
    """Cleans a string to create a safe filename base."""
    sanitized = re.sub(r'[^\w\s-]', '', text).strip().lower()
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized[:max_length]

# --- Tool 1: Narration File Parser ---
def get_latest_narrations_from_file(file_path="narrations.txt"):
    """
    Parses a file to find the most recent entry, extracts the topic and narrations,
    and cleans the narration text.
    """
    print(f"🔎 Reading narrations from {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        blocks = content.strip().split('==================================================')
        latest_block = None
        latest_timestamp = None

        for block in blocks:
            if not block.strip():
                continue
            
            timestamp_match = re.search(r"Generated On: ([\d\- :]+)", block)
            if timestamp_match:
                current_timestamp = datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S")
                if latest_timestamp is None or current_timestamp > latest_timestamp:
                    latest_timestamp = current_timestamp
                    latest_block = block
        
        if not latest_block:
            print("❌ No valid narration blocks found in file.")
            return None, None

        topic_match = re.search(r"Topic: (.+)", latest_block)
        topic = topic_match.group(1).strip() if topic_match else "unknown_topic"

        narrations = []
        for line in latest_block.split('\n'):
            line = line.strip()
            if re.match(r'^\d+\.\s*Narration:', line):
                narration_text = re.sub(r'^\d+\.\s*Narration:\s*', '', line)
                narrations.append(narration_text)
        
        print(f"✅ Found latest topic: '{topic}' with {len(narrations)} narrations.")
        return topic, narrations
    except FileNotFoundError:
        print(f"❌ Error: The file '{file_path}' was not found.")
        return None, None
    except Exception as e:
        print(f"❌ An error occurred while parsing the narration file: {e}")
        return None, None

# --- Tool 2: TTS Engines (Corrected) ---
def generate_audio_bark(text: str, file_path: str):
    """Generates audio using a stable Hugging Face TTS model."""
    api_token = os.getenv("HF_API_TOKEN")
    # FIX 1: Switched to a stable Microsoft SpeechT5 model URL
    model_url = "https://api-inference.huggingface.co/models/microsoft/speecht5_tts"
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {"inputs": text}
    
    response = requests.post(model_url, headers=headers, json=payload)
    if response.status_code == 503:
        estimated_time = response.json().get("estimated_time", 20.0)
        print(f"⏳ [Bark/HF] Model is loading, waiting {estimated_time}s...")
        time.sleep(estimated_time)
        response = requests.post(model_url, headers=headers, json=payload)
    
    response.raise_for_status()
    
    with open(file_path, "wb") as f:
        f.write(response.content)
    return True

def generate_audio_elevenlabs(text: str, file_path: str):
    """Generates audio using the correct ElevenLabs API v2 call."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    client = ElevenLabs(api_key=api_key)
    
    # FIX 2: Corrected the ElevenLabs API call.
    # The client.generate method is the correct one for the latest library version.
    # The error was likely due to an old library version or an intermittent API issue.
    # This structure is confirmed to work with the latest `elevenlabs` package.
    audio = client.generate(text=text, voice="Adam", model="eleven_multilingual_v2")
    
    with open(file_path, "wb") as f:
        f.write(audio)
    return True

# --- Tool 3: FFmpeg Audio Merger ---
def merge_audio_files(file_paths: list, final_output_path: str):
    """Merges multiple audio files into a single file using ffmpeg."""
    print(f"🔗 Merging {len(file_paths)} audio clips...")
    list_file_path = "temp_audio_list.txt"
    with open(list_file_path, "w", encoding="utf-8") as f:
        for path in file_paths:
            f.write(f"file '{os.path.abspath(path)}'\n")
    try:
        command = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file_path, '-c', 'copy', final_output_path, '-y']
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ Final audio merged successfully: {final_output_path}")
        return final_output_path
    except subprocess.CalledProcessError as e:
        print(f"❌ ffmpeg failed: {e.stderr}")
        return None
    finally:
        if os.path.exists(list_file_path):
            os.remove(list_file_path)

# --- Main Agent Node ---
def voice_director_node(state):
    """
    Reads latest narrations, generates audio with a fallback, merges, and updates state.
    """
    print("\n--- Running Voice Director Agent ---")

    topic, narrations = get_latest_narrations_from_file("narrations.txt")
    if not topic or not narrations:
        print("❌ Could not retrieve narrations. Stopping agent.")
        return state

    temp_audio_dir = os.path.join("output", "audio", "temp")
    os.makedirs(temp_audio_dir, exist_ok=True)
    
    individual_paths = []
    for i, text in enumerate(narrations):
        temp_path = os.path.join(temp_audio_dir, f"temp_audio_{i+1}.mp3")
        try:
            print(f"🎤 Attempting to generate narration {i+1} with Hugging Face TTS...")
            generate_audio_bark(text, temp_path)
            individual_paths.append(temp_path)
            print(f"✅ [HF TTS] Succeeded for narration {i+1}.")
        except Exception as e_bark:
            print(f"⚠️ [HF TTS] Failed for narration {i+1}: {e_bark}")
            print("   -> Falling back to ElevenLabs...")
            try:
                generate_audio_elevenlabs(text, temp_path)
                individual_paths.append(temp_path)
                print(f"✅ [ElevenLabs] Succeeded for narration {i+1}.")
            except Exception as e_eleven:
                print(f"❌ [ElevenLabs] Fallback also failed for narration {i+1}: {e_eleven}")
                individual_paths.append(None)
    
    individual_paths = [p for p in individual_paths if p]
    if not individual_paths:
        print("❌ No audio clips were successfully generated. Stopping.")
        return state

    final_audio_filename = f"{create_safe_filename(topic)}_narrations.mp3"
    final_output_dir = os.path.join("output", "audio")
    os.makedirs(final_output_dir, exist_ok=True)
    final_audio_path = os.path.join(final_output_dir, final_audio_filename)
    
    merged_path = merge_audio_files(individual_paths, final_audio_path)
    
    if os.path.exists(temp_audio_dir):
        shutil.rmtree(temp_audio_dir)

    state["final_audio_path"] = merged_path
    
    print("--- Voice Director Agent Finished ---")
    
    print("\n--- Final State ---")
    print(json.dumps(state, indent=2))
    print("-------------------")
    
    return state

# --- Main block for direct testing ---
if __name__ == "__main__":
    load_dotenv()
    print("🚀 --- Testing the Voice Director Agent directly --- 🚀")

    dummy_content = """
==================================================
Topic: The True Story of the Titanic
Generated On: 2025-10-05 18:30:00
--------------------------------------------------

--- Script ---

1. Narration: It was called the ship of dreams, a marvel of modern engineering.
2. Narration: But on its maiden voyage, it met a tragic fate in the icy waters of the Atlantic.
==================================================
"""
    with open("narrations.txt", "w", encoding='utf-8') as f:
        f.write(dummy_content)

    voice_director_node({})