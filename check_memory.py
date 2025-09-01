import chromadb

# --- Configuration ---
DB_PATH = "./chroma_db"
COLLECTION_NAME = "used_topics_memory"

def view_used_topics():
    """
    Connects to the persistent ChromaDB database and prints all
    documents (used topics) stored in the agent's memory.
    """
    print(f"🔎 Accessing agent memory from: {DB_PATH}")

    try:
        # Connect to the same persistent database the agent uses
        client = chromadb.PersistentClient(path=DB_PATH)
        
        # Get the collection where topics are stored
        topic_collection = client.get_collection(name=COLLECTION_NAME)
        
        # Retrieve all items from the collection
        memory = topic_collection.get()
        
        used_topics = memory.get('documents')

        if not used_topics:
            print("✅ The agent's memory is currently empty.")
            return

        print("\n--- 📝 Topics Used by the Agent ---")
        for i, topic in enumerate(used_topics, 1):
            print(f"{i}. {topic}")
        print("------------------------------------")

    except Exception as e:
        print(f"\n❌ An error occurred. The database might not exist yet.")
        print(f"   Please run the main agent script at least once to create the memory.")
        # print(f"   Error details: {e}") # Uncomment for debugging

if __name__ == "__main__":
    view_used_topics()