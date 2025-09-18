import os
import json
import re
import platform
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

LOG_FILE = "narrations.txt"

# --- PROMPT TEMPLATES (Narrations Only) ---

PROMPT_TEMPLATES = {
    "Instructional / How-To": """
    You are a professional YouTube scriptwriter who transforms instructions into captivating storytelling.
    Your task is to write a narration-only script on: "{topic}".
    
    Guidelines:
    - Begin with a story-driven HOOK.
    - Present steps as part of a flowing narrative, not a bullet list.
    - Use everyday language, short sentences, direct tone.
    - End with an encouraging conclusion.
    - Return JSON:
       "narrations": 5 narrations (30–40 words each, story-style).
    """,

    "Explanatory / Deep Dive": """
    You are a master storyteller who explains complex ideas in a cinematic way.
    Topic: "{topic}".
    
    Guidelines:
    - Structure: Hook → Exploration → Deeper Insight → Conclusion.
    - Each narration must feel like a mini-story full of wonder.
    - Keep language simple, emotional, conversational.
    - Return JSON:
       "narrations": 5 narrations (30–40 words each).
    """,

    "Listicle / Factual": """
    You are a YouTube scriptwriter creating factual listicle narrations.
    Topic: "{topic}".
    
    Guidelines:
    - Structure: Intro → 3 distinct facts/items → Outro.
    - Each point should feel like uncovering a hidden gem.
    - Keep narration short, engaging, and story-driven.
    - Return JSON:
       "narrations": 5 narrations (30–40 words each).
    """,

    "Narration / Storytelling": """
    You are a professional narrator who creates cinematic journey-style scripts.
    Topic: "{topic}".
    
    Guidelines:
    - Story arc: Hook → Build → Insight → Conclusion.
    - Keep tone vivid, visual, immersive.
    - No bullet lists or step numbers.
    - Return JSON:
       "narrations": 4 narrations (30–40 words each).
    """,

    "Motivational / Inspirational": """
    You are a narrator who creates uplifting, motivational narrations for faceless videos.
    Topic: "{topic}".
    
    Guidelines:
    - Structure: Hook → Struggle → Breakthrough → Empowering Conclusion.
    - Keep narration emotional, powerful, rhythmic.
    - Return JSON:
       "narrations": 4 narrations (30–40 words each).
    """,

    "Mystery / Unsolved": """
    You are a storyteller who creates suspenseful narrations about mysteries and unsolved events.
    Topic: "{topic}".
    
    Guidelines:
    - Structure: Hook → Setup mystery → Strange clues → Open-ended conclusion.
    - Keep tone suspenseful and cinematic.
    - Return JSON:
       "narrations": 4 narrations (30–40 words each).
    """,

    "Mythology / Legends": """
    You are a narrator who retells myths and legends in a cinematic, engaging way.
    Topic: "{topic}".
    
    Guidelines:
    - Structure: Intro → Main story beats → Lesson or symbolism → Legacy.
    - Use vivid imagery and timeless narration style.
    - Return JSON:
       "narrations": 4 narrations (30–40 words each).
    """,

    "Science / Future Tech": """
    You are a scriptwriter who explains science and technology in a fascinating, simple, futuristic way.
    Topic: "{topic}".
    
    Guidelines:
    - Structure: Hook → Basic explanation → Deeper insight → Application → Conclusion.
    - Keep language simple, inspiring, visual.
    - Return JSON:
       "narrations": 5 narrations (30–40 words each).
    """
}

# --- Agent Tools ---

def log_narrations_to_file(topic, script_data):
    """Appends the generated topic and narrations to narrations.txt, then opens it."""
    print(f"📝 Logging narrations to {LOG_FILE}...")
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write("==================================================\n")
            f.write(f"Topic: {topic}\n")
            f.write(f"Generated On: {timestamp}\n")
            f.write("--------------------------------------------------\n\n")
            
            for i, narration in enumerate(script_data.get("narrations", []), 1):
                f.write(f"{i}. {narration}\n")
            
            f.write("\n==================================================\n\n")
        print("✅ Logging successful.")

        # Auto-open file cross-platform
        system = platform.system()
        if system == "Windows":
            os.startfile(LOG_FILE)
        elif system == "Darwin":  # macOS
            subprocess.call(["open", LOG_FILE])
        else:  # Linux and others
            subprocess.call(["xdg-open", LOG_FILE])

    except Exception as e:
        print(f"❌ Failed to write/open {LOG_FILE}: {e}")

def analyze_topic_type(topic: str):
    """Uses an LLM to classify the topic into a specific category."""
    print(f"🔬 Analyzing topic type for: '{topic}'")
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    prompt = f"""
    You are an intelligent content strategist. Your job is to analyze a video topic and classify it into one of eight categories.

Categories:
- Instructional / How-To
- Explanatory / Deep Dive
- Listicle / Factual
- Narration / Storytelling
- Motivational / Inspirational
- Mystery / Unsolved
- Mythology / Legends
- Science / Future Tech

Topic: "{topic}"

Return only the category name (exactly as written above).
"""
    try:
        response = model.generate_content(prompt)
        category = response.text.strip()
        if category in PROMPT_TEMPLATES:
            print(f"✅ Topic classified as: {category}")
            return category
        else:
            print("⚠️ Could not determine category, defaulting to 'Explanatory / Deep Dive'.")
            return "Explanatory / Deep Dive"
    except Exception as e:
        print(f"❌ Error during topic analysis: {e}")
        return "Explanatory / Deep Dive"

def get_script_and_prompts(topic: str, prompt_template: str):
    """Generates narrations using a dynamically selected prompt template."""
    model = genai.GenerativeModel("gemini-2.5-flash")

    print(f"🎬 Generating narrations for topic: '{topic}'")
    prompt = prompt_template.format(topic=topic)

    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response.text, re.DOTALL)
        if json_match:
            json_response = json_match.group(1)
        else:
            json_response = response.text.strip()
        
        data = json.loads(json_response)
        print("✅ Narrations generated successfully.")
        return data
    except Exception as e:
        print(f"❌ An error occurred while generating narrations: {e}")
        return {"narrations": []}

# --- Main Agent Node ---
def scriptwriter_node(state):
    """
    Analyzes the topic, selects the best prompt, generates narrations,
    logs the output, and updates the state.
    """
    print("\n--- Running Scriptwriter Agent ---")
    
    topic = state.get("topic", "No topic found")
    if topic == "No topic found":
        print("Error: Topic not found in state.")
        return state

    topic_type = analyze_topic_type(topic)
    prompt_template = PROMPT_TEMPLATES.get(topic_type)
    
    script_data = get_script_and_prompts(topic, prompt_template)
    
    if script_data.get("narrations"):
        log_narrations_to_file(topic, script_data)
    
    state.update(script_data)
    
    print("--- Scriptwriter Agent Finished ---")
    return state

# --- Main block for direct testing ---
if __name__ == "__main__":
    load_dotenv()
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    print("🚀 --- Testing the Scriptwriter Agent --- 🚀")
    
    test_topic = "The Lost City of Atlantis"
    test_state = {"topic": test_topic}
    scriptwriter_node(test_state)
    
    print("\n=============================================")
    print(f"✅ Scriptwriter test complete. Check '{LOG_FILE}' for outputs.")
    print("=============================================")
