import os
import re
import time
import json
import base64
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
ELEVEN_API_KEY = os.getenv("ElevenLabs_API_KEY")
EL_VOICE_ID = os.getenv("EL_VOICE_ID")

NARRATIONS_FILE = os.path.join(os.getcwd(), "narrations.txt")

OUTPUT_AUDIO_DIR = os.path.join("output", "audio")
os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)

BARK_SPEAKER_TAG = "[speaker_4] "


def sanitize_filename(text, max_len=80):
    safe = re.sub(r'[^\w\s-]', '', text).strip()
    safe = re.sub(r'[-\s]+', '_', safe)
    return safe[:max_len]


def load_latest_narrations(topic: str):
    """
    Fetches the most recent narrations for the given topic from narrations.txt.
    Matching is done by comparing only the topic name value, case-insensitively.
    """
    if not os.path.exists(NARRATIONS_FILE):
        print(f"❌ {NARRATIONS_FILE} not found at {NARRATIONS_FILE}")
        return None

    with open(NARRATIONS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Split blocks using the separator lines
    blocks = re.split(r"=+\s*\n", content)

    matched_blocks = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Extract the topic line for this block
        topic_match = re.search(r"Topic:\s*(.*)", block, re.IGNORECASE)
        if not topic_match:
            continue

        block_topic = topic_match.group(1).strip()

        # Compare normalized topics
        if block_topic.lower() == topic.strip().lower():
            # Find timestamp if available
            ts_match = re.search(r"Generated On:\s*([\d\-:\s]+)", block)
            timestamp = ts_match.group(1).strip() if ts_match else "Unknown"
            matched_blocks.append((timestamp, block))

    if not matched_blocks:
        print(f"❌ No matching block found for topic: {topic}")
        return None

    # Pick the latest by timestamp
    matched_blocks.sort(key=lambda x: x[0], reverse=True)
    _, latest_block = matched_blocks[0]

    # Now extract the actual narrations
    lines = latest_block.splitlines()
    narrations = []
    for line in lines:
        # Each narration line looks like "1. ..."
        m = re.match(r"^\d+\.\s+(.*)$", line)
        if m:
            narrations.append(m.group(1).strip())

    if not narrations:
        print(f"❌ No narrations found in the matching block for topic: {topic}")
        return None

    return narrations

def download_bytes_to_file(b, path):
    try:
        with open(path, "wb") as f:
            f.write(b)
        return True
    except Exception as e:
        print(f"❌ Write failed: {e}")
        return False


def run_ffmpeg_concat(input_files, out_path):
    if not input_files:
        return False
    list_file = os.path.join(OUTPUT_AUDIO_DIR, f"concat_list_{int(time.time())}.txt")
    try:
        with open(list_file, "w", encoding="utf-8") as f:
            for p in input_files:
                f.write(f"file '{os.path.abspath(p)}'\n")
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", out_path]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode == 0
    finally:
        if os.path.exists(list_file):
            os.remove(list_file)


def run_ffmpeg_concat_reencode(input_files, out_path):
    list_file = os.path.join(OUTPUT_AUDIO_DIR, f"concat_list2_{int(time.time())}.txt")
    try:
        with open(list_file, "w", encoding="utf-8") as f:
            for p in input_files:
                f.write(f"file '{os.path.abspath(p)}'\n")
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
            "-c:a", "libmp3lame", "-q:a", "4", out_path
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode == 0
    finally:
        if os.path.exists(list_file):
            os.remove(list_file)


def generate_bark_clip(narration, out_path, retries=2):
    if not HF_API_TOKEN:
        return False
    url = "https://api-inference.huggingface.co/models/suno/bark"
    payload = {"inputs": BARK_SPEAKER_TAG + narration}
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    for i in range(retries):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            if r.status_code == 503:
                time.sleep(10)
                continue
            if r.status_code != 200:
                time.sleep(2)
                continue
            ctype = r.headers.get("content-type", "")
            if ctype.startswith("audio/") or ctype == "application/octet-stream":
                return download_bytes_to_file(r.content, out_path)
            try:
                j = r.json()
                cand = None
                for k in ("audio", "wav", "b64", "base64"):
                    if k in j and j[k]:
                        cand = j[k]
                        break
                if cand:
                    data = base64.b64decode(cand)
                    return download_bytes_to_file(data, out_path)
            except:
                pass
        except:
            time.sleep(2)
    return False


def generate_elevenlabs_clip(narration, out_path):
    if not ELEVEN_API_KEY or not EL_VOICE_ID:
        return False
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{EL_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json"
    }
    data = {"text": narration, "voice_settings": {"stability": 0.6, "similarity_boost": 0.75}}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        if r.status_code != 200:
            return False
        ctype = r.headers.get("content-type", "")
        if ctype.startswith("audio/") or ctype == "application/octet-stream":
            return download_bytes_to_file(r.content, out_path)
        try:
            j = r.json()
            if "audio" in j:
                audio_b64 = j["audio"]
                data = base64.b64decode(audio_b64)
                return download_bytes_to_file(data, out_path)
        except:
            return False
    except:
        return False
    return False


def voiceover_agent(state):
    print("\n--- Running Voiceover Agent ---")
    topic = state.get("topic")
    if not topic:
        print("❌ No topic in state.")
        return state

    narrations = load_latest_narrations(topic)
    if not narrations:
        print("❌ No narrations found for this topic.")
        return state

    safe_topic = sanitize_filename(topic, 60)
    final_out = os.path.join(OUTPUT_AUDIO_DIR, f"{safe_topic}_narrations.mp3")
    if os.path.exists(final_out):
        os.remove(final_out)

    temp_files = []
    for i, n in enumerate(narrations, start=1):
        part_path = os.path.join(OUTPUT_AUDIO_DIR, f"{safe_topic}_part_{i}.mp3")
        ok = generate_bark_clip(n, part_path)
        if not ok:
            ok = generate_elevenlabs_clip(n, part_path)
        if not ok:
            silent_path = os.path.join(OUTPUT_AUDIO_DIR, f"{safe_topic}_part_{i}_silent.mp3")
            try:
                cmd = [
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                    "-t", "1", "-q:a", "9", "-acodec", "libmp3lame", silent_path
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                temp_files.append(silent_path)
            except:
                temp_files.append(silent_path)
        else:
            temp_files.append(part_path)

    stitched = run_ffmpeg_concat(temp_files, final_out)
    if not stitched:
        stitched = run_ffmpeg_concat_reencode(temp_files, final_out)

    if stitched and os.path.exists(final_out):
        for p in temp_files:
            if os.path.exists(p):
                os.remove(p)
        state["audio_paths"] = [final_out]
        print(f"✅ Final audio saved: {final_out}")
    else:
        print("❌ Failed to create final audio.")
        state["audio_paths"] = []

    print("\n📦 Current State After Voiceover Agent:")
    print(json.dumps(state, indent=2))
    print("--- Voiceover Agent Finished ---")
    return state


if __name__ == "__main__":
    
    print("🚀 --- Testing Voice Agent --- 🚀")
    test_state = {"topic": "The Lost City of Atlantis"}
    result = voiceover_agent(test_state)
    print("Result paths:", result.get("audio_paths"))
    print("\n=============================================")
    print("✅ Visual Agent test complete. Check the 'output/audio' folder.")
    print("Final visual paths collected:")
