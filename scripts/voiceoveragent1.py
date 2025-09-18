import os
import re
from gtts import gTTS

# --- Helper Function ---

def create_safe_filename(topic: str, max_length: int = 50):
    """
    Cleans a topic string to create a safe filename base.
    Removes special characters, replaces spaces with underscores, and truncates.
    """
    # Remove special characters except spaces, letters, and numbers
    sanitized = re.sub(r'[^\w\s-]', '', topic).strip().lower()
    # Replace spaces and hyphens with underscores
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    # Truncate to the max length
    return sanitized[:max_length]

# --- Agent Tool ---

def generate_audio_files(topic: str, narrations: list, output_dir: str):
    """
    Generates a descriptively named MP3 audio file for each narration string.
    
    Args:
        topic (str): The main topic title for naming the files.
        narrations (list): A list of narration strings.
        output_dir (str): The directory to save the audio files in.
        
    Returns:
        list: A list of file paths to the created audio files.
    """
    audio_paths = []
    print(f"🔊 Generating {len(narrations)} audio files with descriptive names...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a safe base name from the topic
    topic_filename_base = create_safe_filename(topic)
    
    for i, narration in enumerate(narrations):
        # Create a descriptive filename, e.g., "roman_concrete_subphase_1.mp3"
        file_name = f"{topic_filename_base}_subphase_{i+1}.mp3"
        file_path = os.path.join(output_dir, file_name)
        
        try:
            tts = gTTS(text=narration, lang='en', tld='co.in', slow=False)
            tts.save(file_path)
            audio_paths.append(file_path)
            print(f"✅ Saved audio: {file_path}")
        except Exception as e:
            print(f"❌ Failed to generate audio for narration {i+1}: {e}")
            audio_paths.append(None) 
            
    return audio_paths

# --- Main Agent Node ---

def voice_director_node(state):
    """
    The agent node for LangGraph. It generates audio files with descriptive names
    and updates the state with the file paths.
    """
    print("\n--- Running Voice Director Agent ---")
    
    topic = state.get("topic")
    narrations = state.get("narrations")
    
    if not topic or not narrations:
        print("Error: Topic or narrations not found in state.")
        state["audio_paths"] = []
        return state

    output_directory = os.path.join("output", "audio")

    audio_paths = generate_audio_files(topic, narrations, output_directory)
    
    state["audio_paths"] = audio_paths
    
    print("--- Voice Director Agent Finished ---")
    return state

# --- Main block for direct testing ---

if __name__ == "__main__":
    print("🚀 --- Testing the Voice Director Agent directly --- 🚀")
    
    # Simulate the input from the Scriptwriter Agent
    test_topic = "The Roman Concrete Recipe That Scientists Still Can't Replicate"
    test_narrations = [
         "Imagine structures standing strong for two millennia, surviving earthquakes and the relentless sea. That's the Roman Empire's legacy, built with a material so advanced, modern science is still scratching its head. Their concrete wasn't just good; it was revolutionary, defying time itself.",
         "The secret lies in volcanic ash, or 'pozzolana,' mixed with lime and seawater. This blend wasn't just a binder; it actively reacted, forming new, strong minerals over centuries. Unlike modern concrete, which degrades, Roman concrete actually strengthens over time, especially near water!",
         "Scientists have analyzed countless samples, identifying the raw materials, but perfectly replicating its self-healing magic remains elusive. It’s not just the ingredients; it’s likely the specific mineral composition, the long curing process, and the chemical reactions unfolding over centuries.",
         "From the Pantheon's mighty dome to coastal breakwaters, Roman concrete stands as a testament to ancient ingenuity. It challenges our assumptions about progress, reminding us that sometimes, the past still holds secrets that could revolutionize our future. A true marvel, lost to time, yet standing firm."
    ]
    
    current_state = {
        "topic": test_topic,
        "narrations": test_narrations
    }
    
    result_state = voice_director_node(current_state)
    
    print("\n=============================================")
    print("✅ Final Output from Voice Director:")
    print(f"Audio Paths: {result_state.get('audio_paths')}")
    print("=============================================")
    print("Check the 'output/audio' folder for files like 'the_roman_concrete_recipe_subphase_1.mp3'")