import os
import requests
from dotenv import load_dotenv

# Load Hugging Face API key
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

def generate_hf_videos(prompts, output_dir="output/video_tests"):
    """
    Generate short videos from text prompts using Hugging Face Zeroscope.
    Saves MP4s in the given output directory and returns their paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for i, prompt in enumerate(prompts):
        print(f"\n🎬 Generating video {i+1}/{len(prompts)}: {prompt}")

        url = "https://api-inference.huggingface.co/models/cerspense/zeroscope_v2_576w"
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        payload = {"inputs": prompt}

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code} {response.text}")
            results.append(None)
            continue

        video_path = os.path.join(output_dir, f"video_{i}.mp4")
        with open(video_path, "wb") as f:
            f.write(response.content)

        print(f"✅ Saved: {video_path}")
        results.append(video_path)

    return results


# --- Run Test ---
if __name__ == "__main__":
    prompts = [
        "A majestic eagle soaring above snow-covered mountains, cinematic",
        "A futuristic city skyline at sunset with flying cars"
    ]
    print("🚀 --- Testing Hugging Face Zeroscope Text-to-Video --- 🚀")
    generate_hf_videos(prompts)
