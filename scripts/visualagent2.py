import os
import re
import requests
import time
from dotenv import load_dotenv

# --- Helper Function ---

def create_safe_filename(text: str, max_length: int = 50):
    """Cleans a string to create a safe filename base."""
    sanitized = re.sub(r'[^\w\s-]', '', text).strip().lower()
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized[:max_length]

def download_media(url: str, file_path: str):
    """Downloads a media file from a URL."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

# --- Visual Tools ---

# --- Stock Image Tools ---
def fetch_pexels_images(queries: list, output_dir: str):
    api_key = os.getenv("PEXELS_API_KEY")
    headers = {"Authorization": api_key}
    paths = []
    for i, query in enumerate(queries):
        try:
            res = requests.get(f"https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=portrait", headers=headers).json()
            if res.get('photos'):
                url = res['photos'][0]['src']['portrait']
                path = os.path.join(output_dir, f"pexels_image_{i+1}.jpg")
                download_media(url, path)
                paths.append(path)
                print(f"✅ [Pexels Image] Downloaded: {path}")
        except Exception as e:
            print(f"❌ [Pexels Image] Failed for query '{query}': {e}")
    return paths

def fetch_pixabay_images(queries: list, output_dir: str):
    api_key = os.getenv("PIXABAY_API_KEY")
    paths = []
    for i, query in enumerate(queries):
        try:
            res = requests.get(f"https://pixabay.com/api/?key={api_key}&q={query}&per_page=3&orientation=vertical").json()
            if res.get('hits'):
                url = res['hits'][0]['largeImageURL']
                path = os.path.join(output_dir, f"pixabay_image_{i+1}.jpg")
                download_media(url, path)
                paths.append(path)
                print(f"✅ [Pixabay Image] Downloaded: {path}")
        except Exception as e:
            print(f"❌ [Pixabay Image] Failed for query '{query}': {e}")
    return paths

# def fetch_unsplash_images(queries: list, output_dir: str):
#     api_key = os.getenv("UNSPLASH_API_KEY")
#     headers = {"Authorization": f"Client-ID {api_key}"}
#     paths = []
#     for i, query in enumerate(queries):
#         try:
#             res = requests.get(f"https://api.unsplash.com/search/photos?query={query}&per_page=1&orientation=portrait", headers=headers).json()
#             if res.get('results'):
#                 url = res['results'][0]['urls']['regular']
#                 path = os.path.join(output_dir, f"unsplash_image_{i+1}.jpg")
#                 download_media(url, path)
#                 paths.append(path)
#                 print(f"✅ [Unsplash Image] Downloaded: {path}")
#         except Exception as e:
#             print(f"❌ [Unsplash Image] Failed for query '{query}': {e}")
#     return paths

def fetch_unsplash_images(queries: list, output_dir: str):
    # Unsplash uses an "Access Key" which functions as the API key.
    access_key = os.getenv("UNSPLASH_API_KEY")
    if not access_key:
        print("❌ [Unsplash] Access Key (UNSPLASH_API_KEY) not found in .env file.")
        return []
        
    # The header must be in the format "Client-ID YOUR_ACCESS_KEY"
    headers = {"Authorization": f"Client-ID {access_key}"}
    paths = []
    
    for i, query in enumerate(queries):
        try:
            params = {
                'query': query,
                'per_page': 1,
                'orientation': 'portrait'
            }
            res = requests.get("https://api.unsplash.com/search/photos", params=params, headers=headers).json()
            
            if res.get('results'):
                url = res['results'][0]['urls']['regular']
                path = os.path.join(output_dir, f"unsplash_image_{i+1}.jpg")
                download_media(url, path)
                paths.append(path)
                print(f"✅ [Unsplash Image] Downloaded: {path}")
            else:
                 print(f"⚠️ [Unsplash Image] No results found for query: '{query}'")

        except Exception as e:
            print(f"❌ [Unsplash Image] Failed for query '{query}': {e}")
            
    return paths

# --- AI Image Tools ---
def generate_hf_sdxl_images(prompts: list, output_dir: str):
    api_token = os.getenv("HF_API_TOKEN")
    headers = {"Authorization": f"Bearer {api_token}"}
    model_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    paths = []
    for i, prompt in enumerate(prompts):
        try:
            payload = {"inputs": f"{prompt}, vertical portrait, cinematic"}
            response = requests.post(model_url, headers=headers, json=payload)
            if response.status_code == 503:
                time.sleep(15)
                response = requests.post(model_url, headers=headers, json=payload)
            response.raise_for_status()
            path = os.path.join(output_dir, f"hf_sdxl_image_{i+1}.png")
            with open(path, "wb") as f:
                f.write(response.content)
            paths.append(path)
            print(f"✅ [HF SDXL] Generated: {path}")
        except Exception as e:
            print(f"❌ [HF SDXL] Failed for prompt '{prompt}': {e}")
    return paths

# --- Stock Video Tools ---
def fetch_pexels_videos(queries: list, output_dir: str):
    api_key = os.getenv("PEXELS_API_KEY")
    headers = {"Authorization": api_key}
    paths = []
    for i, query in enumerate(queries):
        try:
            res = requests.get(f"https://api.pexels.com/videos/search?query={query}&per_page=1&orientation=portrait", headers=headers).json()
            if res.get('videos'):
                url = res['videos'][0]['video_files'][0]['link']
                path = os.path.join(output_dir, f"pexels_video_{i+1}.mp4")
                download_media(url, path)
                paths.append(path)
                print(f"✅ [Pexels Video] Downloaded: {path}")
        except Exception as e:
            print(f"❌ [Pexels Video] Failed for query '{query}': {e}")
    return paths

def fetch_pixabay_videos(queries: list, output_dir: str):
    api_key = os.getenv("PIXABAY_API_KEY")
    paths = []
    for i, query in enumerate(queries):
        try:
            res = requests.get(f"https://pixabay.com/api/videos/?key={api_key}&q={query}&per_page=3&orientation=vertical").json()
            if res.get('hits'):
                url = res['hits'][0]['videos']['medium']['url']
                path = os.path.join(output_dir, f"pixabay_video_{i+1}.mp4")
                download_media(url, path)
                paths.append(path)
                print(f"✅ [Pixabay Video] Downloaded: {path}")
        except Exception as e:
            print(f"❌ [Pixabay Video] Failed for query '{query}': {e}")
    return paths

# --- AI Video Tools ---
def generate_hf_zeroscope_videos(prompts: list, output_dir: str):
    # This is a placeholder as Zeroscope API often requires async polling.
    # For now, we simulate the process. A full implementation would be more complex.
    print("⚠️ [HF Zeroscope] AI video generation is a complex process. This is a placeholder.")
    return ["path/to/placeholder_video.mp4"] * len(prompts)


# --- Main Agent Node ---

def visual_agent_node(state):
    """
    The agent node that orchestrates fetching and generating all visuals
    based on the shot list from the Query Agent.
    """
    print("\n--- Running Visual Agent (Camera Crew) ---")
    
    all_visual_paths = []
    base_output_dir = os.path.join("output", "visuals")

    # --- Process Image Queries ---
    image_queries = state.get("image_queries", {})
    for platform, queries in image_queries.items():
        if queries:
            output_dir = os.path.join(base_output_dir, "images", platform)
            os.makedirs(output_dir, exist_ok=True)
            if platform == "pexels":
                all_visual_paths.extend(fetch_pexels_images(queries, output_dir))
            elif platform == "pixabay":
                all_visual_paths.extend(fetch_pixabay_images(queries, output_dir))
            elif platform == "unsplash":
                all_visual_paths.extend(fetch_unsplash_images(queries, output_dir))

    # --- Process Image Prompts (AI) ---
    image_prompts = state.get("image_prompts", {})
    for model, prompts in image_prompts.items():
        if prompts:
            output_dir = os.path.join(base_output_dir, "images", model)
            os.makedirs(output_dir, exist_ok=True)
            if model == "huggingface_sdxl":
                all_visual_paths.extend(generate_hf_sdxl_images(prompts, output_dir))

    # --- Process Video Queries ---
    video_queries = state.get("video_queries", {})
    for platform, queries in video_queries.items():
        if queries:
            output_dir = os.path.join(base_output_dir, "videos", platform)
            os.makedirs(output_dir, exist_ok=True)
            if platform == "pexels":
                all_visual_paths.extend(fetch_pexels_videos(queries, output_dir))
            elif platform == "pixabay":
                all_visual_paths.extend(fetch_pixabay_videos(queries, output_dir))

    # --- Process Video Prompts (AI) ---
    video_prompts = state.get("video_prompts", {})
    for model, prompts in video_prompts.items():
        if prompts:
            output_dir = os.path.join(base_output_dir, "videos", model)
            os.makedirs(output_dir, exist_ok=True)
            if model == "huggingface_zeroscope":
                all_visual_paths.extend(generate_hf_zeroscope_videos(prompts, output_dir))

    state["visual_paths"] = all_visual_paths
    print("--- Visual Agent Finished ---")
    return state

# --- Main block for direct testing ---

if __name__ == "__main__":
    load_dotenv()
    print("🚀 --- Testing Visual Agent --- 🚀")

    # A mock state object, simulating the output from the Query Agent
    test_state = {
        "image_queries": {
            "pexels": ["ancient rome colosseum", "roman soldier portrait"],
            "pixabay": ["parthenon", "scrolls on a table"],
            "unsplash": ["ancient greek statue", "volcano erupting"]
        },
        "image_prompts": {
            "huggingface_sdxl": ["A philosopher contemplating under an olive tree, detailed oil painting"]
        },
        "video_queries": {
            "pexels": ["waves crashing on a beach", "time-lapse of clouds"],
            "pixabay": ["eagle flying", "waterfall in a forest"]
        },
        "video_prompts": {
            "huggingface_zeroscope": ["a futuristic city with flying cars"]
        }
    }

    result_state = visual_agent_node(test_state)
    print("\n=============================================")
    print("✅ Visual Agent test complete. Check the 'output/visuals' folder.")
    print("Final visual paths collected:")
    for path in result_state.get("visual_paths", []):
        print(f"  - {path}")
    print("=============================================")