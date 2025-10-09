import os
import re
import requests
import json
import shutil
from datetime import datetime
from dotenv import load_dotenv
from mutagen.mp3 import MP3

# --- Configuration & Setup ---
load_dotenv()
NARRATIONS_FILE = "narrations.txt"
ELEVEN_API_KEY = os.getenv("ElevenLabs_API_KEY")
ELEVEN_VOICE_ID = os.getenv("EL_VOICE_ID")

# --- Helper Functions ---
def create_safe_filename(text: str, max_length: int = 50):
    """Cleans a string to create a safe filename base."""
    sanitized = re.sub(r'[^\w\s-]', '', text).strip().lower()
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized[:max_length]

# --- Agent Tools ---

def get_latest_narrations_from_file(file_path=NARRATIONS_FILE):
    """
    Parses a file to find the most recent entry, extracts the topic and
    individual, cleaned narration lines.
    """
    print(f"🔎 Reading narrations from {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        blocks = content.strip().split('==================================================')
        latest_block = None; latest_timestamp = None

        for block in blocks:
            if not block.strip(): continue
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
        # Find all numbered narration lines
        narration_matches = re.findall(r'^\d+\.\s*Narration:\s*(.+)$', latest_block, re.MULTILINE)
        for match in narration_matches:
            narrations.append(match.strip())
        
        if not narrations:
            print("❌ No narration lines found in the latest block.")
            return topic, None

        print(f"✅ Found latest topic: '{topic}' with {len(narrations)} narrations.")
        return topic, narrations

    except FileNotFoundError:
        print(f"❌ Error: The file '{file_path}' was not found.")
        return None, None
    except Exception as e:
        print(f"❌ An error occurred while parsing the narration file: {e}")
        return None, None

def generate_speech_elevenlabs(text: str, output_path: str):
    """
    Generates speech for a single text line using ElevenLabs API.
    """
    if not ELEVEN_API_KEY or not ELEVEN_VOICE_ID:
        print("❌ ElevenLabs API key or voice ID missing in .env. Cannot generate audio.")
        return False

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
    headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": ELEVEN_API_KEY}
    payload = {"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.7, "similarity_boost": 0.7}}

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status() # Will raise an error for bad status codes

    with open(output_path, "wb") as f:
        f.write(response.content)
    return True

# --- Main Agent Node ---
def voice_director_node(state):
    """
    Main Voice Director Agent. Reads narrations, generates individual audio clips,
    calculates timings, and updates the state.
    """
    print("\n--- Running Voice Director Agent ---")

    # This agent will now get its narrations directly from the file, making it more independent
    topic, narrations = get_latest_narrations_from_file()
    if not topic or not narrations:
        # If we can't get it from the file, try getting it from the state as a fallback
        topic = state.get("topic")
        narrations = state.get("narrations")
        if not topic or not narrations:
            print("❌ No topic or narrations found in state or file. Stopping agent.")
            return state

    temp_audio_dir = os.path.join("output", "audio", "temp")
    os.makedirs(temp_audio_dir, exist_ok=True)
    
    individual_paths = []
    narration_timings = []
    current_time = 0.0

    print(f"🎤 Generating {len(narrations)} individual audio clips with ElevenLabs...")
    for i, text in enumerate(narrations):
        temp_path = os.path.join(temp_audio_dir, f"temp_audio_{i+1}.mp3")
        try:
            if generate_speech_elevenlabs(text, temp_path):
                individual_paths.append(temp_path)
                # Calculate and store timing information for the Editor Agent
                audio_duration = MP3(temp_path).info.length
                narration_timings.append({
                    "text": text,
                    "start": current_time,
                    "end": current_time + audio_duration,
                    "duration": audio_duration
                })
                current_time += audio_duration
                print(f"✅ Generated audio for narration {i+1}. Duration: {audio_duration:.2f}s")
            else:
                # Append a placeholder if generation fails
                narration_timings.append(None)
        except Exception as e:
            print(f"❌ Failed to generate or process audio for narration {i+1}: {e}")
            narration_timings.append(None)
    
    if not any(narration_timings): # If all generations failed
        print("❌ No audio clips were successfully generated. Stopping.")
        if os.path.exists(temp_audio_dir): shutil.rmtree(temp_audio_dir)
        return state

    # This agent will pass the individual paths and timings to the editor
    # The Editor agent will be responsible for merging them.
    state["topic"] = topic
    state["narrations"] = narrations
    state["audio_paths"] = individual_paths
    state["narration_timings"] = narration_timings
    
    print("--- Voice Director Agent Finished ---")
    
    # Prints full state at the end
    print("\n--- Final State ---")
    print(json.dumps(state, indent=2))
    print("-------------------")
    
    return state

# --- Main block for direct testing ---
if __name__ == "__main__":
    print("🚀 --- Testing the Voice Director Agent directly --- 🚀")

    # Create a dummy narrations.txt file for testing
    dummy_content = """
==================================================
Topic: The Lost City of Atlantis
Generated On: 2025-10-08 09:00:00
--------------------------------------------------

--- Script ---

1. Narration: Legends speak of a great city, lost beneath the waves.
2. Narration: A civilization said to be more advanced than any other of its time.
3. Narration: To this day, explorers and dreamers search for its sunken ruins, a mystery that endures.
==================================================
"""
    with open(NARRATIONS_FILE, "w", encoding='utf-8') as f:
        f.write(dummy_content)
    
    # We can start with an empty state, as the agent reads from the file
    initial_state = {}
    voice_director_node(initial_state)