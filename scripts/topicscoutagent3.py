import os
import praw
import random
import json
from dotenv import load_dotenv
import google.generativeai as genai
import chromadb
from chromadb.utils import embedding_functions

# --- Configuration ---

# Google Generative AI setup
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")
genai.configure(api_key=GOOGLE_API_KEY)

# NEW: Define the embedding function using your Google API Key
google_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=GOOGLE_API_KEY)

# ChromaDB setup for semantic memory
client = chromadb.PersistentClient(path="./chroma_db")
# In-memory database; for persistence, use: chromadb.PersistentClient(path="./chroma_db")
try:
    # UPDATED: Tell the collection to use our Google embedding function
    topic_collection = client.get_collection(
        name="used_topics_memory",
        embedding_function=google_ef
    )
except Exception:
    # UPDATED: Tell the collection to use our Google embedding function on creation
    topic_collection = client.create_collection(
        name="used_topics_memory",
        embedding_function=google_ef
    )

# Google Generative AI for brainstorming
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Evergreen Categories Knowledge Base ---
EVERGREEN_CATEGORIES = {
    # 🔬 Science & Knowledge
    'Amazing Physics Explained': [
        'askscience', 'physics', 'explainlikeimfive', 'quantum', 'astrophysics',
        'PhysicsStudents', 'learnmath'
    ],
    'Biology\'s Strangest Creatures': [
        'naturewasmetal', 'biology', 'deepsea', 'whatsthisbug', 'zoology',
        'AnimalFacts', 'paleontology'
    ],
    'Everyday Tech Secrets': [
        'technology', 'howstuffworks', 'gadgets', 'techsupport', 'Futurology',
        'todayilearned', 'computers'
    ],
    'Medical Marvels & Mysteries': [
        'medicine', 'todayilearned', 'science', 'HealthAnxiety', 'AskDocs',
        'nursing', 'medicalschool'
    ],
    'Space Discoveries & Phenomena': [
        'space', 'astronomy', 'spaceporn', 'astrophotography', 'Hubble',
        'universetoday', 'nasa'
    ],
    'Chemistry in Action': [
        'chemistry', 'chemicalreactiongifs', 'science', 'labporn', 'OrganicChemistry',
        'materials', 'periodictable'
    ],
    'Forgotten Inventions': [
        'history', 'inventions', 'retrofuturism', 'obscuremedia', 'mechanicalkeyboards',
        'Museum', 'engineering'
    ],
    'Architectural Masterpieces': [
        'architecture', 'architectureporn', 'bizarrebuildings', 'urbanexploration',
        'interiordesign', 'urbanplanning'
    ],
    'Hidden Historical Events': [
        'history', 'todayilearned', 'unsolvedmysteries', 'AskHistorians',
        'historywhatif', 'ancientrome'
    ],
    'Ancient Engineering Marvels': [
        'ancienthistory', 'engineeringporn', 'artefactporn', 'Archaeology',
        'lostcivilizations', 'ancientegypt'
    ],
    'Mythology Explained': [
        'mythology', 'folklore', 'legends', 'religion', 'occult',
        'Hinduism', 'GreekMythology'
    ],
    'Lost Civilizations': [
        'lostcivilizations', 'archaeology', 'ancientmysteries', 'Atlantis',
        'ancientrome', 'AskHistorians'
    ],
    'Incredible Natural Phenomena': [
        'natureisfuckinglit', 'earthporn', 'weathergifs', 'VolcanoPorn',
        'SevereWeather', 'geology'
    ],
    'Clever Psychology Hacks': [
        'psychology', 'lifeprotips', 'socialskills', 'getdisciplined',
        'selfimprovement', 'neuropsychology'
    ],
    'Cognitive Biases Explained': [
        'cognitivebias', 'philosophy', 'criticalthinking', 'psychology',
        'rational', 'changemyview'
    ],
    'Common Misconceptions Debunked': [
        'mythbusters', 'todayilearned', 'confidentlyincorrect', 'explainlikeimfive',
        'skeptic', 'AskScienceDiscussion'
    ],
    'Famous Unsolved Mysteries': [
        'unsolvedmysteries', 'truecrime', 'conspiracy', 'creepy',
        'Paranormal', 'highstrangeness'
    ],

    # 🧠 Self-Improvement & Habits
    'Self Improvement & Habits': [
        'selfimprovement', 'getdisciplined', 'DecidingToBeBetter',
        'Productivity', 'Habits', 'GoodHabits', 'motivation',
        'selfhelp', 'Stoicism'
    ],
    'Productivity & Hacks': [
        'productivity', 'lifehacks', 'LifeProTips', 'Notion',
        'ObsidianMD', 'SecondBrain', 'SideProject'
    ],

    # 💪 Fitness & Health
    'Fitness & Health': [
        'Fitness', 'loseit', 'gainit', 'xxfitness',
        'bodyweightfitness', 'Stronglifts5x5', 'running', 'yoga',
        'HealthyFood', 'nutrition'
    ],

    # 📚 Study & Learning
    'Study & Learning': [
        'GetStudying', 'StudyTips', 'Anki', 'college',
        'GradSchool', 'LanguageLearning', 'learnprogramming',
        'math', 'edtech', 'LearnUselessTalents'
    ],

    # 💼 Money & Career
    'Money & Career': [
        'personalfinance', 'financialindependence', 'povertyfinance',
        'investing', 'stocks', 'startups', 'entrepreneur',
        'careerguidance', 'resumes', 'jobs'
    ],

    # ❤️ Relationships & Social Skills
    'Relationships & Social Skills': [
        'socialskills', 'dating_advice', 'relationships',
        'longdistance', 'FriendshipAdvice', 'confidence',
        'menslib', 'femalefashionadvice', 'malegrooming'
    ],

    # 🌱 Mindset & Motivation
    'Mindset & Motivation': [
        'GetMotivated', 'inspiration', 'MotivationAndMindset',
        'MotivateInspire', 'Mindfulness', 'Meditation', 'OvercomingThings',
        'stoicism', 'decidingtobebetter'
    ],

    # 🎨 Creativity & Skills
    'Creativity & Skills': [
        'DIY', 'cooking', 'learnart', 'ArtFundamentals',
        'DrawForMe', 'photography', 'Filmmakers',
        'writing', 'MusicProduction', 'edmproduction'
    ],

    # 💻 Technology & Tools
    'Technology & Tools': [
        'ChatGPT', 'PromptEngineering', 'programming',
        'Apple', 'iPhone', 'androidapps', 'Futurology',
        'SideProject', 'computers'
    ]
}

# --- Agent Tools ---

def get_reddit_gems(category, subreddits, limit=25):
    """Fetches top, fascinating post titles from a list of niche subreddits."""
    print(f"🔎 Diving deep into '{category}' via subreddits: {subreddits}...")
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    if not all([client_id, client_secret, user_agent]):
        print("⚠️ Reddit credentials not found. Skipping Reddit search.")
        return []
    
    all_titles = []
    try:
        reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
        for sub in subreddits:
            subreddit = reddit.subreddit(sub)
            top_posts = list(subreddit.top(time_filter = 'year', limit=limit // len(subreddits)))
            all_titles.extend([post.title for post in top_posts])
        print(f"✅ Found {len(all_titles)} potential gems.")
        return all_titles
    except Exception as e:
        print(f"❌ Could not fetch Reddit gems: {e}")
        return []

def brainstorm_and_validate_topics(themes):
    """Uses an LLM to brainstorm and rank video ideas from a list of themes."""
    print("🤖 Using AI to brainstorm and validate video titles...")
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""
    You are a Viral Video Strategist for a faceless YouTube channel specializing in Evergreen Content.
    Your primary goal is to generate titles that evoke curiosity and surprise based on the following themes.
    Themes: {', '.join(themes)}
    Instructions:
    1. Generate a list of 5 to 7 distinct and engaging video titles.
    2. Prioritize topics that reveal little-known facts or explain complex things simply.
    3. For each title, assign a 'virality_score' from 1 to 10 and a brief 'justification'.
    4. The output MUST be a valid JSON object with a single key "ideas", which is a list of objects.
    """
    try:
        response = model.generate_content(prompt)
        json_response = response.text.strip().replace("```json", "").replace("```", "")
        validated_ideas = json.loads(json_response)
        return validated_ideas.get("ideas", [])
    except Exception as e:
        print(f"❌ AI brainstorming failed: {e}")
        return []

def get_unique_topics(ideas: list, similarity_threshold=0.87):
    """Filters a list of topic ideas against the ChromaDB memory of used topics."""
    if not ideas:
        return []
    print(f"🧠 Checking {len(ideas)} ideas against semantic memory...")
    fresh_ideas = []
    titles_to_check = [idea['title'] for idea in ideas]

    # Check if collection is empty, if so, all ideas are fresh
    if topic_collection.count() == 0:
        print("✅ Memory is empty. All ideas are considered fresh.")
        return ideas
        
    # Query ChromaDB for semantically similar topics for the whole batch
    results = topic_collection.query(query_texts=titles_to_check, n_results=1)
    
    for i, idea in enumerate(ideas):
        distance = results['distances'][i][0] if results['distances'][i] else 1.0
        # ChromaDB distance is L2, 0 is identical. We check if the distance is low.
        if distance < (1 - similarity_threshold):
             print(f"⚠️ Rejecting similar topic: '{idea['title']}' (Similarity Distance: {distance:.2f})")
        else:
            fresh_ideas.append(idea)
            
    print(f"✅ Found {len(fresh_ideas)} unique, fresh ideas.")
    return fresh_ideas

# --- Main Agent Node ---
def curiosity_engine_node(state):
    """The main agent node that finds a fascinating, evergreen topic."""
    print("\n--- Running Curiosity Engine Agent ---")
    
    # Step 1: Select a random evergreen category and perform a deep dive
    selected_category, target_subreddits = random.choice(list(EVERGREEN_CATEGORIES.items()))
    gems = get_reddit_gems(selected_category, target_subreddits)
    if not gems:
        print("❌ No gems found in deep dive. Stopping.")
        return {"topic": "Could not find any topics from Reddit."}

    # Step 2: AI Brainstorming
    ranked_ideas = brainstorm_and_validate_topics(gems)
    if not ranked_ideas:
        print("❌ No ideas generated by AI. Stopping.")
        return {"topic": "AI failed to generate video ideas."}

    # Step 3: Filter against Semantic Memory
    fresh_ideas = get_unique_topics(ranked_ideas, similarity_threshold=0.95)
    if not fresh_ideas:
        print("⚠️ All generated ideas were too similar to previously used topics. Stopping.")
        return {"topic": "All generated ideas were duplicates."}

    # Step 4: Final Selection
    fresh_ideas.sort(key=lambda x: x['virality_score'], reverse=True)
    selected_topic_obj = fresh_ideas[0]
    selected_topic = selected_topic_obj['title']
    print(f"🏆 Selected Topic: '{selected_topic}' (Score: {selected_topic_obj['virality_score']})")

    # Step 5: Update Semantic Memory
    topic_collection.add(
        documents=[selected_topic],
        ids=[str(hash(selected_topic))] # Create a unique ID from the topic
    )
    print(f"💾 Saved '{selected_topic}' to semantic memory.")
    
    print("--- Curiosity Engine Agent Finished ---")
    return {"topic": selected_topic}

# --- Main block for direct testing ---
if __name__ == "__main__":
    print("🚀 --- Testing the Curiosity Engine Agent directly --- 🚀")
    final_result = curiosity_engine_node({})
    print("\n=============================================")
    print(f"✅ Final Topic Selected: {final_result.get('topic')}")
    print("=============================================")