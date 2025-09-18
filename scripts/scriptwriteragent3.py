import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

LOG_FILE = "content_log.txt"

# --- PROMPT TEMPLATES ---

PROMPT_TEMPLATES = {
    "Instructional / How-To": """
    You are a professional YouTube scriptwriter who transforms simple instructions into captivating storytelling.
    Your task is to write a how-to video script on: "{topic}".
    
    Guidelines:
    - Begin with a story-driven HOOK (relatable, curious, surprising).
    - Present steps as part of a flowing narrative, not a bullet list.
    - Use everyday language, short sentences, direct tone.
    - End with an encouraging conclusion.
    - Return JSON:
       "narrations": 5 narrations (30–40 words each, story-style),
       "search_queries": 4 descriptive portrait-optimized queries.
    """,

    "Explanatory / Deep Dive": """
    You are a master storyteller who explains complex ideas in a cinematic way.
    Topic: "{topic}".
    
    Guidelines:
    - Structure: Hook → Exploration → Deeper Insight → Conclusion.
    - Each narration must feel like a mini-story full of wonder.
    - Keep language simple, emotional, conversational.
    - Return JSON:
       "narrations": 5 narrations (30–40 words each),
       "search_queries": 4 vivid descriptive portrait-optimized queries.
    """,

    "Listicle / Factual": """
    You are a YouTube scriptwriter creating factual listicle videos.
    Topic: "{topic}".
    
    Guidelines:
    - Structure: Intro → 3 distinct facts/items → Outro.
    - Each point should feel like uncovering a hidden gem.
    - Keep narration short, engaging, and story-driven.
    - Return JSON:
       "narrations": 5 narrations (30–40 words each),
       "search_queries": 4 portrait-optimized queries.
    """,

    "Narration / Storytelling": """
    You are a professional narrator who creates cinematic journey-style scripts.
    Topic: "{topic}".
    
    Guidelines:
    - Story arc: Hook → Build → Insight → Conclusion.
    - Keep tone vivid, visual, immersive.
    - No bullet lists or step numbers.
    - Return JSON:
       "narrations": 4 narrations (30–40 words each),
       "search_queries": 4 portrait-optimized queries.
    """,

    "Motivational / Inspirational": """
    You are a narrator who creates uplifting, motivational scripts for short faceless videos.
    Topic: "{topic}".
    
    Guidelines:
    - Structure: Hook → Struggle → Breakthrough → Empowering Conclusion.
    - Keep narration emotional, powerful, rhythmic.
    - Return JSON:
       "narrations": 4 narrations (30–40 words each),
       "search_queries": 4 vivid portrait-optimized queries.
    """,

    "Mystery / Unsolved": """
    You are a storyteller who creates suspenseful scripts about mysteries and unsolved events.
    Topic: "{topic}".
    
    Guidelines:
    - Structure: Hook → Setup mystery → Strange clues → Open-ended conclusion.
    - Keep tone suspenseful and cinematic.
    - Return JSON:
       "narrations": 4 narrations (30–40 words each),
       "search_queries": 4 descriptive portrait-optimized queries.
    """,

    "Mythology / Legends": """
    You are a narrator who retells myths and legends in a cinematic, engaging way.
    Topic: "{topic}".
    
    Guidelines:
    - Structure: Intro → Main story beats → Lesson or symbolism → Legacy.
    - Use vivid imagery and timeless narration style.
    - Return JSON:
       "narrations": 4 narrations (30–40 words each),
       "search_queries": 4 portrait-optimized queries.
    """,

    "Science / Future Tech": """
    You are a scriptwriter who explains science and technology in a fascinating, simple, futuristic way.
    Topic: "{topic}".
    
    Guidelines:
    - Structure: Hook → Basic explanation → Deeper insight → Application → Conclusion.
    - Keep language simple, inspiring, visual.
    - Return JSON:
       "narrations": 5 narrations (30–40 words each),
       "search_queries": 4 portrait-optimized queries.
    """,

    "Search Query Master": """
    You are a visual prompt engineer.
    Task: Generate highly descriptive, cinematic search queries for stock media engines like Pexels and Hugging Face.
    
    Guidelines:
    - Each query must visually match the narration.
    - Must be portrait (9:16), cinematic, stock-media friendly.
    - Include setting, mood, subject, action.
    - Return JSON:
       "search_queries": 4 refined portrait-optimized queries.
    """
}

# --- Agent Tools ---

def log_script_to_file(topic, script_data):
    """Appends the generated topic, script, and prompts to a log file."""
    print(f"📝 Logging content to {LOG_FILE}...")
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write("==================================================\n")
            f.write(f"Topic: {topic}\n")
            f.write(f"Generated On: {timestamp}\n")
            f.write("--------------------------------------------------\n\n")
            
            f.write("--- Script ---\n\n")
            for i, narration in enumerate(script_data.get("narrations", []), 1):
                f.write(f"{i}. Narration: {narration}\n")
            
            f.write("\n--- Image Prompts ---\n\n")
            for i, prompt in enumerate(script_data.get("search_queries", []), 1):
                f.write(f"{i}. Prompt: {prompt}\n")
            
            f.write("\n==================================================\n\n")
        print("✅ Logging successful.")
    except Exception as e:
        print(f"❌ Failed to write to log file: {e}")

def analyze_topic_type(topic: str):
    """Uses an LLM to classify the topic into a specific category."""
    print(f"🔬 Analyzing topic type for: '{topic}'")
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    prompt = f"""
    You are an intelligent content strategist. Your job is to analyze a video topic and classify it into one of eight categories.

Categories:
- Instructional / How-To: Teaches the viewer how to do something step by step.
- Explanatory / Deep Dive: Explains the "why/what/how" of a concept, event, or phenomenon.
- Listicle / Factual: Presents a list of items or surprising facts.
- Narration / Storytelling: Cinematic journey or documentary-style narration.
- Motivational / Inspirational: Emotional, uplifting, life-changing content.
- Mystery / Unsolved: Suspense-driven, unresolved mysteries.
- Mythology / Legends: Ancient myths, folklore, or legends retold.
- Science / Future Tech: Science or technology explained simply, with wonder.

---
Examples:
Topic: "The Lost City of Atlantis"
Category: Mystery / Unsolved

Topic: "5 Animals That Can Survive in Space"
Category: Listicle / Factual

Topic: "How to Meditate in 5 Minutes"
Category: Instructional / How-To

Topic: "The Secrets of Ancient Libraries"
Category: Narration / Storytelling

Topic: "Why Failure is the Best Teacher"
Category: Motivational / Inspirational

Topic: "The Story of Hercules"
Category: Mythology / Legends

Topic: "How Quantum Computers Work"
Category: Science / Future Tech

---
Your Task:
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
    """Generates a script and prompts using a dynamically selected prompt template."""
    model = genai.GenerativeModel("gemini-2.5-flash")

    print(f"🎬 Generating script for topic: '{topic}'")
    prompt = prompt_template.format(topic=topic)

    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response.text, re.DOTALL)
        if json_match:
            json_response = json_match.group(1)
        else:
            json_response = response.text.strip()
        
        data = json.loads(json_response)
        print("✅ Script and prompts generated successfully.")
        return data
    except Exception as e:
        print(f"❌ An error occurred while generating the script: {e}")
        return {"narrations": [], "search_queries": []}

# --- Main Agent Node ---
def scriptwriter_node(state):
    """
    Analyzes the topic, selects the best prompt, generates the script,
    logs the output, and updates the state.
    """
    print("\n--- Running Intelligent Scriptwriter Agent ---")
    
    topic = state.get("topic", "No topic found")
    if topic == "No topic found":
        print("Error: Topic not found in state.")
        return state

    topic_type = analyze_topic_type(topic)
    prompt_template = PROMPT_TEMPLATES.get(topic_type)
    
    script_data = get_script_and_prompts(topic, prompt_template)
    
    if script_data.get("narrations"):
        log_script_to_file(topic, script_data)
    
    state.update(script_data)
    
    print("--- Intelligent Scriptwriter Agent Finished ---")
    return state

# --- Main block for direct testing ---
if __name__ == "__main__":
    load_dotenv()
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    print("🚀 --- Testing the Intelligent Scriptwriter Agent --- 🚀")
    
    # Test Case 1: Instructional
    print("\n--- Test Case 1: Instructional ---")
    test_topic1 = "How to Meditate in 5 Minutes"
    test_state1 = {"topic": test_topic1}
    scriptwriter_node(test_state1)

    # Test Case 2: Mystery
    print("\n--- Test Case 2: Mystery ---")
    test_topic2 = "The Lost City of Atlantis"
    test_state2 = {"topic": test_topic2}
    scriptwriter_node(test_state2)
    
    print("\n=============================================")
    print(f"✅ Scriptwriter tests complete. Check '{LOG_FILE}' for outputs.")
    print("=============================================")
