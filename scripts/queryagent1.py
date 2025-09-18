import os
import json
import re
import platform
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

LOG_FILE = "queries.txt"

# --- PROMPT TEMPLATE FOR QUERY GENERATION ---

QUERY_PROMPT = """
You are a Query Engineer Agent.
Your task is to generate **platform-specific search queries and prompts** for finding or generating visuals
(images and videos) for YouTube shorts content.

Inputs:
- Topic: "{topic}"
- Narrations: {narrations}

Your task:
1. Use both the topic AND narrations to design relevant queries.
2. Create separate queries/prompts for each platform/model.

Output Format (strict JSON only):
{{
  "image_queries": {{
    "pexels": ["portrait photo search query 1", "portrait photo search query 2"],
    "pixabay": ["portrait/vertical search query 1", "portrait/vertical search query 2"],
    "unsplash": ["portrait cinematic still query 1", "portrait cinematic still query 2"]
  }},
  "image_prompts": {{
    "huggingface_sdxl": ["detailed AI prompt for SDXL image gen 1", "detailed AI prompt 2"]
  }},
  "video_queries": {{
    "pexels": ["portrait video search query 1", "portrait video search query 2"],
    "pixabay": ["short portrait video query 1", "short portrait video query 2"]
  }},
  "video_prompts": {{
    "huggingface_zeroscope": ["cinematic AI video prompt 1", "cinematic AI video prompt 2"]
  }}
}}

Guidelines:
- All queries for stock sites (pexels, pixabay, unsplash) must be short, SEO-style,
  portrait/vertical optimized, and realistic.
- All prompts for AI models (huggingface_sdxl, huggingface_zeroscope) must be detailed,
  cinematic, descriptive, and artistic.
- DO NOT include explanations or text outside the JSON.
"""

def log_queries_to_file(topic, query_data):
    """Appends queries/prompts to queries.txt"""
    print(f"📝 Logging queries to {LOG_FILE}...")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write("==================================================\n")
            f.write(f"Topic: {topic}\n")
            f.write(f"Generated On: {timestamp}\n")
            f.write("--------------------------------------------------\n\n")

            f.write("--- Image Queries ---\n")
            for platform, queries in query_data.get("image_queries", {}).items():
                f.write(f"{platform}:\n")
                for q in queries:
                    f.write(f"  - {q}\n")
                f.write("\n")

            f.write("--- Image Prompts (AI) ---\n")
            for model, prompts in query_data.get("image_prompts", {}).items():
                f.write(f"{model}:\n")
                for p in prompts:
                    f.write(f"  - {p}\n")
                f.write("\n")

            f.write("--- Video Queries ---\n")
            for platform, queries in query_data.get("video_queries", {}).items():
                f.write(f"{platform}:\n")
                for q in queries:
                    f.write(f"  - {q}\n")
                f.write("\n")

            f.write("--- Video Prompts (AI) ---\n")
            for model, prompts in query_data.get("video_prompts", {}).items():
                f.write(f"{model}:\n")
                for p in prompts:
                    f.write(f"  - {p}\n")
                f.write("\n")

            f.write("==================================================\n\n")

        print("✅ Queries logged successfully.")
    except Exception as e:
        print(f"❌ Failed to write {LOG_FILE}: {e}")


# --- Query Agent ---

def generate_queries(topic, narrations):
    """Generates narration-aware search queries and prompts for visuals."""
    model = genai.GenerativeModel("gemini-2.5-flash")

    narrations_str = json.dumps(narrations, ensure_ascii=False, indent=2)
    prompt = QUERY_PROMPT.format(topic=topic, narrations=narrations_str)

    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response.text, re.DOTALL)
        if json_match:
            json_response = json_match.group(1)
        else:
            json_response = response.text.strip()

        data = json.loads(json_response)
        print("✅ Queries generated successfully.")
        return data
    except Exception as e:
        print(f"❌ Error generating queries: {e}")
        return {
            "image_queries": {"pexels": [], "pixabay": [], "unsplash": []},
            "image_prompts": {"huggingface_sdxl": []},
            "video_queries": {"pexels": [], "pixabay": []},
            "video_prompts": {"huggingface_zeroscope": []}
        }

# --- Main Agent Node ---
def queryagent_node(state):
    """
    Generates platform-specific image/video queries and prompts
    based on narrations + topic.
    """
    print("\n--- Running Query Agent ---")

    topic = state.get("topic", "No topic found")
    narrations = state.get("narrations", [])

    if topic == "No topic found" or not narrations:
        print("Error: Missing topic or narrations in state.")
        return state

    query_data = generate_queries(topic, narrations)
    if query_data:
        log_queries_to_file(topic, query_data)

    state.update(query_data)

    print("--- Query Agent Finished ---")
    return state

# --- Main block for direct testing ---
if __name__ == "__main__":
    load_dotenv()
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    print("🚀 --- Testing Query Agent --- 🚀")

    test_state = {
        "topic": "The Lost City of Atlantis",
        "narrations": [
            "Legends speak of a great city lost beneath the sea...",
            "Some say it was advanced beyond its time...",
            "Divers and dreamers still search for its ruins...",
            "The myth endures, forever unsolved..."
        ]
    }

    queryagent_node(test_state)

    print("\n=============================================")
    print(f"✅ Query Agent test complete. Check '{LOG_FILE}' for outputs.")
    print("=============================================")
