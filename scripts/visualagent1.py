import os
import re
import base64
import json
import requests
from dotenv import load_dotenv
from pexels_api import API

# --- Helper Function ---

def create_safe_filename(text: str, max_length: int = 50):
    """Cleans a string to create a safe filename base."""
    sanitized = re.sub(r'[^\w\s-]', '', text).strip().lower()
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized[:max_length]

# # --- Agent Tool 1: Google Imagen (Corrected) ---

# def generate_ai_images_with_imagen(topic: str, prompts: list, output_dir: str):
#     """Generates AI images for each prompt using Google's Imagen model."""
#     print(f"🎨 Generating {len(prompts)} AI images for '{topic}' using Google Imagen...")
#     api_key = os.getenv("GOOGLE_API_KEY")
#     if not api_key:
#         print("❌ Google API key not found in .env file.")
#         return [None] * len(prompts)

#     # Note: Ensure the "Vertex AI API" is enabled in your Google Cloud project.
#     api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={api_key}" # Using a specific, known model
#     headers = {"Content-Type": "application/json"}
    
#     os.makedirs(output_dir, exist_ok=True)
#     image_paths = []
#     topic_filename_base = create_safe_filename(topic)

#     for i, prompt in enumerate(prompts):
#         full_prompt = f"{prompt}, 3d animation style, cinematic lighting, hyperrealistic, epic, 8k"
#         file_name = f"{topic_filename_base}_image_{i+1}.png"
#         file_path = os.path.join(output_dir, file_name)
#         payload = {"instances": [{"prompt": full_prompt}], "parameters": {"sampleCount": 1}}

#         try:
#             response = requests.post(api_url, headers=headers, data=json.dumps(payload))
#             response.raise_for_status()
#             result = response.json()

#             if result.get("predictions") and result["predictions"][0].get("bytesBase64Encoded"):
#                 image_data = base64.b64decode(result["predictions"][0]["bytesBase64Encoded"])
#                 with open(file_path, "wb") as f:
#                     f.write(image_data)
#                 image_paths.append(file_path)
#                 print(f"✅ [Imagen] Saved AI-generated image: {file_path}")
#             else:
#                 image_paths.append(None)
#         except requests.exceptions.RequestException as e:
#             print(f"❌ [Imagen] Failed to generate AI image. Status Code: {e.response.status_code if e.response else 'N/A'}.")
#             print("   Ensure the Vertex AI API is enabled in your Google Cloud project.")
#             image_paths.append(None)
#     return image_paths

# --- Agent Tool 1: Hugging Face Image Generation (Final Version) ---
import requests
import time

def generate_ai_images_with_hf(topic: str, prompts: list, output_dir: str):
    """Generates AI images for each prompt using the Hugging Face Inference API."""
    print(f"🎨 Generating {len(prompts)} AI images for '{topic}' using Hugging Face...")
    api_token = os.getenv("HF_API_TOKEN")
    if not api_token:
        print("❌ Hugging Face API token not found in .env file.")
        return [None] * len(prompts)

    # We will use the official Stable Diffusion XL model from Stability AI on Hugging Face
    model_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {api_token}"}
    
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []
    topic_filename_base = create_safe_filename(topic)

    for i, prompt in enumerate(prompts):
        full_prompt = f"{prompt}, 3d animation style, cinematic lighting, hyperrealistic, epic, 8k, beautiful"
        file_name = f"{topic_filename_base}_image_{i+1}.png"
        file_path = os.path.join(output_dir, file_name)

        payload = {"inputs": full_prompt}

        try:
            # Send the request to the Hugging Face API
            response = requests.post(model_url, headers=headers, json=payload)
            
            # This API can sometimes be loading a model, so we add a simple retry logic
            if response.status_code == 503: # 503 Service Unavailable indicates the model is loading
                print("⏳ Model is loading, waiting and retrying in 20 seconds...")
                time.sleep(20)
                response = requests.post(model_url, headers=headers, json=payload)

            response.raise_for_status() # Raise an exception for other bad status codes
            
            # The API returns the raw image data directly
            image_data = response.content
            
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            image_paths.append(file_path)
            print(f"✅ [Hugging Face] Saved AI-generated image: {file_path}")

        except requests.exceptions.RequestException as e:
            print(f"❌ [Hugging Face] Failed to generate AI image for prompt '{prompt}': {e}")
            if e.response:
                print(f"   Response Body: {e.response.text}")
            image_paths.append(None)
            
    return image_paths

# --- Agent Tool 2: Pexels Video (Corrected) ---

# --- Agent Tool 2: Pexels Video (Corrected with Direct API Call) ---
import requests

def get_pexels_videos(topic: str, prompts: list, output_dir: str):
    """
    Searches and downloads royalty-free stock videos from Pexels
    by making a direct API call with the requests library.
    """
    print(f"📹 Searching for {len(prompts)} stock videos for '{topic}' using Pexels...")
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print("❌ Pexels API key not found in .env file.")
        return [None] * len(prompts)
    
    # Pexels API endpoint for video search
    search_url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": api_key}
    
    os.makedirs(output_dir, exist_ok=True)
    video_paths = []
    topic_filename_base = create_safe_filename(topic)

    for i, prompt in enumerate(prompts):
        file_name = f"{topic_filename_base}_video_{i+1}.mp4"
        file_path = os.path.join(output_dir, file_name)
        
        params = {
            'query': prompt,
            'per_page': 1,
            'orientation': 'portrait' # Prioritize vertical videos for shorts
        }

        try:
            # Step 1: Search for the video
            response = requests.get(search_url, headers=headers, params=params)
            response.raise_for_status()
            results = response.json()
            
            if not results.get('videos'):
                print(f"⚠️ [Pexels] No video found for prompt: '{prompt}'")
                video_paths.append(None)
                continue
            
            video_files = results['videos'][0]['video_files']
            
            # Step 2: Find the best quality video link
            video_url = None
            for video_file in video_files:
                # Look for a common HD portrait resolution
                if video_file.get('quality') == 'hd' and video_file.get('height', 0) >= 1920:
                    video_url = video_file.get('link')
                    break
            
            if not video_url: # Fallback to the first available link
                video_url = video_files[0].get('link')

            # Step 3: Download the video
            if video_url:
                download_response = requests.get(video_url, stream=True)
                download_response.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in download_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                video_paths.append(file_path)
                print(f"✅ [Pexels] Saved stock video: {file_path}")
            else:
                 video_paths.append(None)

        except requests.exceptions.RequestException as e:
            print(f"❌ [Pexels] Failed to download video for prompt '{prompt}': {e}")
            video_paths.append(None)
            
    return video_paths

# --- Main Agent Node ---

def media_sourcer_node(state):
    """
    The agent node. It chooses between generating AI images or fetching
    stock videos based on the state.
    """
    print("\n--- Running Hybrid Media Sourcer Agent ---")
    
    topic = state.get("topic")
    prompts = state.get("search_queries")
    media_type = state.get("media_type", "imagen") # Default to AI images

    if not topic or not prompts:
        print("Error: Topic or prompts (search_queries) not found in state.")
        state["media_paths"] = []
        return state

    if media_type == "imagen":
        output_dir = os.path.join("output", "visuals", "imagen")
        media_paths = generate_ai_images_with_hf(topic, prompts, output_dir)
    elif media_type == "pexels":
        output_dir = os.path.join("output", "visuals", "pexels")
        media_paths = get_pexels_videos(topic, prompts, output_dir)
    else:
        print(f"❌ Unknown media_type: '{media_type}'. No visuals will be sourced.")
        media_paths = []
    
    state["media_paths"] = media_paths
    
    print("--- Hybrid Media Sourcer Agent Finished ---")
    return state

# --- Main block for direct testing ---

if __name__ == "__main__":
    load_dotenv()
    print("🚀 --- Testing the Hybrid Media Sourcer Agent --- 🚀")
    
    test_topic = "The Secret Science of Geysers"
    test_prompts = [
        "A vast geothermal landscape with steam rising from the ground, cinematic.",
        "An underground chamber of superheated water bubbling violently.",
        "A massive geyser erupting powerfully into a blue sky.",
        "Tourists watching a geyser erupt from a safe distance."
    ]
    
    # --- Test Case 1: Using Hugging Face ---
    print("\n--- Test Case 1: Generating AI Images with Hugging Face ---")
    hf_state = {
        "topic": test_topic,
        "search_queries": test_prompts,  
        "media_type": "huggingface"
    }
    result_hf = media_sourcer_node(hf_state)
    print(f"Imagen Output Paths: {result_hf.get('media_paths')}")

    # --- Test Case 2: Using Pexels ---
    print("\n--- Test Case 2: Fetching Stock Videos with Pexels ---")
    pexels_state = {
        "topic": test_topic,
        "search_queries": test_prompts,
        "media_type": "pexels"
    }
    result_pexels = media_sourcer_node(pexels_state)
    print(f"Pexels Output Paths: {result_pexels.get('media_paths')}")

    print("\n=============================================")
    print("✅ Media Sourcer test complete. Check the 'output/visuals' folder.")
    print("=============================================")