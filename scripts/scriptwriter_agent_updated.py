import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

LOG_FILE = "content_log.txt"

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

def get_script_and_prompts(topic: str):
    """
    Generates a curiosity-driven video script and image search prompts
    based on a given evergreen topic.
    """
    load_dotenv()
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-1.5-flash")

    print(f"🎬 Generating script for topic: '{topic}'")

    prompt = f"""
    You are an expert scriptwriter for a "faceless" YouTube channel specializing in captivating, evergreen content.
    Your task is to generate a script and visually descriptive image search terms for a video about the topic: "{topic}".
    The tone should be full of wonder, slightly mysterious, and designed to make the viewer say "wow, I didn't know that!".

    Follow these instructions precisely:
    1.  Create exactly 4 subpoints. The first should be a strong hook, and the last should be a memorable concluding thought.
    2.  For each subpoint, write a concise narration of 30-40 words.
    3.  For each subpoint, create a highly descriptive and specific image search query that would find a compelling, high-quality visual.
    4.  The output MUST be a valid JSON object containing two keys: "narrations" (a list of 4 strings) and "search_queries" (a list of 4 strings).
    """

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

def scriptwriter_node(state):
    """
    The agent node for LangGraph. It calls the script generation tool,
    logs the output, and updates the state.
    """
    print("\n--- Running Scriptwriter Agent ---")
    
    topic = state.get("topic", "No topic found")
    if topic == "No topic found":
        print("Error: Topic not found in state.")
        return {"narrations": [], "search_queries": []}

    script_data = get_script_and_prompts(topic)
    
    # NEW STEP: Log the output to the file if script generation was successful
    if script_data.get("narrations"):
        log_script_to_file(topic, script_data)
    
    state.update(script_data)
    
    print("--- Scriptwriter Agent Finished ---")
    return state

# --- Main block for direct testing ---
if __name__ == "__main__":
    print("🚀 --- Testing the Scriptwriter Agent directly --- 🚀")
    
    test_topic = "The Antikythera mechanism, an ancient Greek analog computer"
    current_state = {"topic": test_topic}
    
    scriptwriter_node(current_state)
    
    print("\n=============================================")
    print(f"✅ Scriptwriter test complete. Check '{LOG_FILE}' for the output.")
    print("=============================================")