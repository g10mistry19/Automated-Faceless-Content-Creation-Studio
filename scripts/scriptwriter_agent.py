import os
import google.generativeai as genai
from dotenv import load_dotenv

def get_script_and_prompts(topic: str):
    """
    This function generates the video script and image search prompts
    based on the given topic.

    It's engineered to create a script for a video of approx. 45-50 seconds.
    """
    # Load environment variables for the Google API key
    load_dotenv()
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash")

    print(f"🎬 Generating script for topic: '{topic}'")

    # --- Enhanced prompt for controlled output ---
    # We ask for exactly 4 subpoints and a specific word count per narration.
    # 4 narrations * ~35 words/narration = ~140 words.
    # At a speaking rate of ~150 words/minute, this gives ~56 seconds of audio.
    # This is a good target to land in our 45-50 second final video.
    prompt = f"""
    You are an expert scriptwriter for short, engaging faceless educational videos.
    Your task is to generate a script and image search terms for a video about the topic: "{topic}".

    Follow these instructions precisely:
    1.  Create exactly 4 engaging subpoints for the topic.
    2.  For each subpoint, write a concise narration of 30-40 words.
    3.  For each subpoint, create a visually descriptive image search query that would find a relevant, high-quality image.
    4.  The output MUST be a JSON object containing two keys: "narrations" (a list of 4 strings) and "search_queries" (a list of 4 strings).

    Example Output Format:
    {{
        "narrations": [
            "Narration for subpoint 1...",
            "Narration for subpoint 2...",
            "Narration for subpoint 3...",
            "Narration for subpoint 4..."
        ],
        "search_queries": [
            "image search query for subpoint 1",
            "image search query for subpoint 2",
            "image search query for subpoint 3",
            "image search query for subpoint 4"
        ]
    }}
    """

    try:
        response = model.generate_content(prompt)
        # Clean up the response to extract the JSON part
        json_response = response.text.strip().replace("```json", "").replace("```", "")
        
        import json
        data = json.loads(json_response)
        
        print("✅ Script and prompts generated successfully.")
        return data

    except Exception as e:
        print(f"❌ An error occurred while generating the script: {e}")
        return {
            "narrations": [],
            "search_queries": []
        }

# This is the agent function that will be a node in our LangGraph
def scriptwriter_node(state):
    """
    The agent node for LangGraph. It calls the script generation tool
    and updates the state with the narrations and search queries.
    """
    print("\n--- Running Scriptwriter Agent ---")
    
    # In a real graph, the topic would come from the state dictionary
    topic = state.get("topic", "No topic found")
    
    if topic == "No topic found":
        print("Error: Topic not found in state.")
        return {"narrations": [], "search_queries": []}

    # Call the tool to get the script and prompts
    script_data = get_script_and_prompts(topic)
    
    print("--- Scriptwriter Agent Finished ---")
    
    # For testing, we return the data directly
    return script_data

# --- Main block for direct testing ---
if __name__ == "__main__":
    print("🚀 --- Testing the Scriptwriter Agent directly --- 🚀")
    
    # --- Simulate the input from the Topic Scout Agent ---
    test_topic = "The Great Stink of 1858 in London"
    
    # The state is a dictionary that gets passed between agents
    # We simulate the state after the Topic Scout has run
    current_state = {"topic": test_topic}
    
    # Run the scriptwriter node with the simulated state
    result = scriptwriter_node(current_state)
    
    print("\n=============================================")
    print("✅ Final Output from Scriptwriter:")
    import json
    print(json.dumps(result, indent=2))
    print("=============================================")