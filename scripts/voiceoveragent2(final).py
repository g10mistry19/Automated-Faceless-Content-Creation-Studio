import os
import re
import requests
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ELEVEN_API_KEY = os.getenv("ElevenLabs_API_KEY")
ELEVEN_VOICE_ID = os.getenv("EL_VOICE_ID")
NARRATIONS_FILE = "narrations.txt"
OUTPUT_DIR = "output/audio"


def load_latest_narration_block(topic: str):
    """
    Extract the latest narration block for the given topic.
    """
    if not os.path.exists(NARRATIONS_FILE):
        print(f"❌ {NARRATIONS_FILE} not found in project root.")
        return None, None

    with open(NARRATIONS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Split blocks using the separator
    blocks = re.split(r"=+\s*\n", content)

    topic = topic.strip().lower()
    matched_blocks = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Match topic line
        match_topic = re.search(r"^Topic:\s*(.+)$", block, re.MULTILINE)
        if not match_topic:
            continue
        block_topic = match_topic.group(1).strip().lower()

        if block_topic == topic:
            # Extract timestamp
            match_time = re.search(r"Generated On:\s*(.+)$", block, re.MULTILINE)
            if match_time:
                timestamp = match_time.group(1).strip()
            else:
                timestamp = "0000-00-00 00:00:00"

            matched_blocks.append((timestamp, block))

    if not matched_blocks:
        print(f"❌ No matching block found for topic: {topic}")
        return None, None

    # Pick block with latest timestamp
    matched_blocks.sort(key=lambda x: x[0], reverse=True)
    latest_ts, latest_block = matched_blocks[0]
    return latest_ts, latest_block


def extract_narrations(block: str):
    """
    Extract narration lines, strip numbering, merge into one string.
    """
    narrations = []
    for line in block.splitlines():
        m = re.match(r"^\d+\.\s+(.*)$", line.strip())
        if m:
            narrations.append(m.group(1).strip())
    if not narrations:
        return None
    return " ".join(narrations)


def generate_speech_elevenlabs(text: str, output_path: str):
    """
    Generate speech from ElevenLabs API and save to file.
    """
    if not ELEVEN_API_KEY or not ELEVEN_VOICE_ID:
        print("❌ ElevenLabs API key or voice ID missing in .env")
        return None

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_API_KEY,
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.7, "similarity_boost": 0.7}
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"❌ ElevenLabs request failed: {response.status_code} {response.text}")
        return None

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"✅ Audio saved: {output_path}")
    return output_path


def voiceover_agent(state: dict):
    """
    Main Voiceover Agent function.
    - Finds latest narrations for topic
    - Generates TTS audio
    - Updates state with audio path
    """
    print("\n--- Running Voiceover Agent ---")

    topic = state.get("topic")
    if not topic:
        print("❌ No topic found in state.")
        return state

    ts, block = load_latest_narration_block(topic)
    if not block:
        print("❌ No narrations found for this topic.")
        return state

    text = extract_narrations(block)
    if not text:
        print("❌ Could not extract narration text.")
        return state

    safe_topic = re.sub(r"[^\w\s-]", "", topic).strip().replace(" ", "_")
    output_path = os.path.join(OUTPUT_DIR, f"{safe_topic}_narrations.mp3")

    audio_path = generate_speech_elevenlabs(text, output_path)
    if not audio_path:
        print("❌ Audio generation failed.")
        return state

    # Update state
    state["audio_paths"] = [audio_path]

    print("✅ Voiceover agent finished successfully.")
    print("📌 Final State:", state)
    return state


# Standalone run test
if __name__ == "__main__":
    test_state = {"topic": "The Lost City of Atlantis"}
    result = voiceover_agent(test_state)
    print("\nResult paths:", result.get("audio_paths"))
