import os
import praw
import random
from dotenv import load_dotenv

def get_trending_topic_from_reddit():
    """
    This function connects to the Reddit API and fetches a top trending topic
    from a list of suitable subreddits for faceless video content.
    """
    # Load environment variables from .env file
    load_dotenv()

    # --- Securely load credentials ---
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    # --- Validate credentials ---
    if not all([client_id, client_secret, user_agent]):
        raise ValueError("Reddit API credentials not found in .env file.")

    print("✅ Reddit credentials loaded.")

    try:
        # --- Initialize PRAW (Python Reddit API Wrapper) ---
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        print("✅ Connected to Reddit API.")

        # --- Define subreddits suitable for faceless content ---
        subreddits = [
            'todayilearned',
            'Damnthatsinteresting',
            'explainlikeimfive',
            'LifeProTips',
            'YouShouldKnow'
        ]
        
        # --- Select a random subreddit ---
        selected_subreddit_name = random.choice(subreddits)
        subreddit = reddit.subreddit(selected_subreddit_name)
        print(f"🔎 Searching for top post in r/{selected_subreddit_name}...")

        # --- Fetch the top 5 hot posts and select the one with the most upvotes ---
        top_posts = list(subreddit.hot(limit=5))
        if not top_posts:
            return "Could not find any hot posts. Please try again."

        # Find the post with the highest score (upvotes)
        most_popular_post = max(top_posts, key=lambda post: post.score)
        
        topic = most_popular_post.title
        print(f"🏆 Found topic: '{topic}'")
        
        return topic

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return "Failed to fetch a topic from Reddit."

# This is the agent function that will be a node in our LangGraph
def topic_scout_node(state):
    """
    The agent node function for LangGraph. It calls the tool and updates the state.
    """
    print("\n--- Running Topic Scout Agent ---")
    
    # Call the tool to get the topic
    topic = get_trending_topic_from_reddit()
    
    # Update the state with the new topic
    # In a real LangGraph app, the state is a dictionary or a class instance
    print("--- Topic Scout Agent Finished ---")
    
    # For now, we just return the topic for testing
    return topic

# --- Main block for direct testing ---
if __name__ == "__main__":
    print("🚀 --- Testing the Topic Scout Agent directly --- 🚀")
    
    # Run the agent node function to test its functionality
    found_topic = topic_scout_node({}) # Pass an empty dict as a placeholder for the state
    
    print("\n=============================================")
    print(f"✅ Final Topic Selected: {found_topic}")
    print("=============================================")