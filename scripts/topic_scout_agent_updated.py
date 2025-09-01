import os
import praw
import random
import json
from dotenv import load_dotenv
from pytrends.request import TrendReq
import google.generativeai as genai

# --- Configuration ---
USED_TOPICS_FILE = "used_topics.txt"

# --- Tool 1: Load and Save Used Topics (Agent's Memory) ---
def load_used_topics():
    """Loads the list of used topics from the memory file."""
    if not os.path.exists(USED_TOPICS_FILE):
        return set()
    with open(USED_TOPICS_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def save_used_topic(topic):
    """Appends a new topic to the memory file."""
    with open(USED_TOPICS_FILE, 'a', encoding='utf-8') as f:
        f.write(topic + "\n")

# --- Tool 2: Fetch Google Trends ---
def get_google_trends_topics(region='IN'):
    """Fetches top daily search trends for a specific region using a stable method."""
    print(f"🔎 Searching for Google Trends in {region}...")
    try:
        pytrends = TrendReq(hl='en-US', tz=330)
        
        # FIX: Use today_searches() with the two-letter region code
        trending_searches_df = pytrends.today_searches(pn=region)
        
        # The result is a simple list of strings, so .tolist() is perfect
        trends = trending_searches_df.tolist()
        
        print(f"✅ Found {len(trends)} Google Trends.")
        return trends
    except Exception as e:
        print(f"❌ Could not fetch Google Trends: {e}")
        return []

# --- Tool 3: Fetch Reddit Topics ---
def get_reddit_popular_topics(subreddits=[ 'todayilearned',
            'Damnthatsinteresting',
            'explainlikeimfive',
            'LifeProTips',
            'YouShouldKnow','popular'], limit=15):
    """Fetches top post titles from a list of subreddits."""
    print(f"🔎 Searching for top posts in subreddits: {subreddits}...")
    load_dotenv()
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    if not all([client_id, client_secret, user_agent]):
        print("⚠️ Reddit credentials not found, skipping Reddit search.")
        return []
    
    all_titles = []
    try:
        reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
        for sub in subreddits:
            subreddit = reddit.subreddit(sub)
            top_posts = list(subreddit.hot(limit=limit))
            all_titles.extend([post.title for post in top_posts])
        
        print(f"✅ Found {len(all_titles)} Reddit topics.")
        return all_titles
    except Exception as e:
        print(f"❌ Could not fetch Reddit topics: {e}")
        return []

# --- Tool 4: AI Brainstorming and Validation ---
def brainstorm_and_validate_topics(themes):
    """Uses an LLM to brainstorm and rank video ideas from a list of themes."""
    print("🧠 Using AI to brainstorm and validate topics...")
    load_dotenv()
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
    You are a Viral Video Strategist for a faceless YouTube channel targeting the Indian audience.
    Analyze the following list of raw trending themes. Your task is to brainstorm specific, curiosity-driven video titles based on these themes.

    Themes:
    {', '.join(themes)}

    Instructions:
    1.  Generate a list of 5 to 7 distinct and highly engaging video titles.
    2.  For each title, assign a 'virality_score' from 1 to 10.
    3.  For each title, provide a brief 'justification' explaining why it would work for a short, faceless video.
    4.  The output MUST be a valid JSON object containing a single key "ideas", which is a list of objects, each with "title", "virality_score", and "justification".
    """
    try:
        response = model.generate_content(prompt)
        json_response = response.text.strip().replace("```json", "").replace("```", "")
        validated_ideas = json.loads(json_response)
        print(f"✅ AI generated {len(validated_ideas.get('ideas', []))} validated ideas.")
        return validated_ideas.get("ideas", [])
    except Exception as e:
        print(f"❌ AI brainstorming failed: {e}")
        return []

# --- Main Agent Node ---
def content_strategist_node(state):
    """
    The main agent node that orchestrates the topic discovery and selection process.
    """
    print("\n--- Running Content Strategist Agent ---")
    
    # Step 1: Broad Thematic Discovery
    google_themes = get_google_trends_topics(region='IN')
    reddit_themes = get_reddit_popular_topics(subreddits=[ 'todayilearned',
            'Damnthatsinteresting',
            'explainlikeimfive',
            'LifeProTips',
            'YouShouldKnow','popular'], limit=10)
    all_themes = list(set(google_themes + reddit_themes))
    
    if not all_themes:
        print("❌ No themes found. Stopping.")
        return {"topic": "Could not find any trending topics."}

    # Step 2: AI Brainstorming
    ranked_ideas = brainstorm_and_validate_topics(all_themes)
    if not ranked_ideas:
        print("❌ No ideas generated by AI. Stopping.")
        return {"topic": "AI failed to generate video ideas."}

    # Step 3: Filter against Memory
    used_topics = load_used_topics()
    fresh_ideas = [idea for idea in ranked_ideas if idea['title'] not in used_topics]
    
    if not fresh_ideas:
        print("⚠️ All generated ideas have already been used. Picking a random theme as fallback.")
        topic = random.choice(all_themes)
        save_used_topic(topic) # Save the fallback topic to memory
        return {"topic": topic}

    # Step 4: Final Selection
    fresh_ideas.sort(key=lambda x: x['virality_score'], reverse=True)
    selected_topic = fresh_ideas[0]['title']
    print(f"🏆 Selected Topic: '{selected_topic}' (Score: {fresh_ideas[0]['virality_score']})")

    # Step 5: Update Memory
    save_used_topic(selected_topic)
    print(f"💾 Saved '{selected_topic}' to memory file.")
    
    print("--- Content Strategist Agent Finished ---")
    return {"topic": selected_topic}

# --- Main block for direct testing ---
if __name__ == "__main__":
    print("🚀 --- Testing the Content Strategist Agent directly --- 🚀")
    
    final_result = content_strategist_node({})
    
    print("\n=============================================")
    print(f"✅ Final Topic Selected: {final_result.get('topic')}")
    print("=============================================")