import os
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import yt_dlp

# -----------------------------------------------------------------------------
# Tor Proxy Configuration & Check
# -----------------------------------------------------------------------------
# The script will connect to the Tor Browser's SOCKS5 proxy.
# Ensure Tor Browser is running before starting this script.
TOR_SOCKS_HOST = "127.0.0.1"
TOR_SOCKS_PORT = 9150  # Default port for Tor Browser
TOR_PROXY = f"socks5h://{TOR_SOCKS_HOST}:{TOR_SOCKS_PORT}"

def check_tor_connection():
    """
    Verifies that the script can connect to the Tor network.
    Raises an exception if the connection fails.
    """
    print("Checking Tor connection...")
    proxies = {
        'http': TOR_PROXY,
        'https': TOR_PROXY
    }
    try:
        # We use a reliable service to check our external IP address
        response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=10)
        response.raise_for_status()
        print(f"✅ Successfully connected to Tor. Your IP is: {response.json()['origin']}")
        return True
    except requests.exceptions.RequestException as e:
        print("\n" + "="*50)
        print("❌ CRITICAL ERROR: Could not connect to the Tor network.")
        print(f"   Please ensure the Tor Browser is running and listening on port {TOR_SOCKS_PORT}.")
        print(f"   Error details: {e}")
        print("="*50 + "\n")
        raise SystemExit("Exiting: Tor connection failed.")


# -----------------------------------------------------------------------------
# Evergreen Hashtags Tool
# -----------------------------------------------------------------------------
def get_evergreen_hashtags(niche: str) -> list:
    """
    Provides a list of popular, evergreen hashtags for a given niche.
    """
    evergreen = {
        "pets": ["#pets", "#dogsoftiktok", "#catsoftiktok", "#petlovers", "#cutepets"],
        "fitness": ["#fitness", "#workout", "#fitlife", "#gymmotivation", "#healthylifestyle"],
        "cooking": ["#cooking", "#foodie", "#easyrecipes", "#tiktokfood", "#homemade"],
        "travel": ["#travel", "#wanderlust", "#explore", "#nature", "#adventure"],
        "education": ["#learnontiktok", "#study", "#education", "#motivation", "#knowledge"]
    }
    return evergreen.get(niche.lower(), ["#foryou", "#trending", "#viral"])

# -----------------------------------------------------------------------------
# Scrape TikTok by Hashtag using Selenium (via Tor)
# -----------------------------------------------------------------------------
def get_tiktok_videos_by_hashtag(hashtag: str, limit: int = 5, scroll_pause_time: int = 4):
    """
    Uses Selenium with a Tor proxy to scrape video URLs from a TikTok hashtag page.
    This version runs in a visible browser and waits for content to load.
    """
    print(f"Initializing Tor-enabled browser to scrape {hashtag}...")
    url = f"https://www.tiktok.com/tag/{hashtag.lstrip('#')}"
    
    # --- Selenium Setup with Tor Proxy ---
    chrome_options = Options()
    # IMPORTANT: The '--headless' argument is now commented out.
    # A browser window will open so you can see what's happening.
    # chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f'--proxy-server={TOR_PROXY}')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument("--window-size=1280,720") # Set a standard window size

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"❌ Error setting up WebDriver: {e}")
        return []

    video_links = set()
    try:
        driver.get(url)
        
        # --- NEW: Wait for the main video container to be visible ---
        print("Waiting for video grid to load...")
        # TikTok uses 'data-e2e' attributes which are more stable than class names
        video_grid_selector = (By.CSS_SELECTOR, '[data-e2e="search-video-list"]')
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(video_grid_selector)
        )
        print("✅ Video grid found. Starting to scrape links.")

        last_height = driver.execute_script("return document.body.scrollHeight")
        while len(video_links) < limit:
            # NEW: More specific selector for video links
            video_elements = driver.find_elements(By.CSS_SELECTOR, 'div[data-e2e="search-video-list"] a')
            for elem in video_elements:
                href = elem.get_attribute('href')
                if href and "/video/" in href:
                    video_links.add(href)
                    if len(video_links) >= limit:
                        break
            
            if len(video_links) >= limit:
                break

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time) # Pause to let new videos load

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("Reached the end of the page.")
                break
            last_height = new_height

    except TimeoutException:
        print("❌ Timed out waiting for the video content to load.")
        print("   This is likely due to a CAPTCHA or a block page.")
        print("   Please observe the browser window to see the issue.")
    except Exception as e:
        print(f"❌ An unexpected error occurred while scraping {hashtag}: {e}")
    finally:
        print("Closing browser window...")
        # Give a moment to see the final state before closing
        time.sleep(3) 
        driver.quit()

    return list(video_links)[:limit]

# -----------------------------------------------------------------------------
# Download TikTok Video using yt-dlp (via Tor)
# -----------------------------------------------------------------------------
def download_tiktok_video(video_url: str, save_path: str = "downloads"):
    """
    Downloads a TikTok video without a watermark using yt-dlp, routing the
    download through the Tor proxy.
    """
    os.makedirs(save_path, exist_ok=True)
    
    # --- yt-dlp Configuration with Tor Proxy ---
    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        # This is the crucial line to route yt-dlp's traffic through Tor
        'proxy': TOR_PROXY,
    }

    try:
        print(f"Attempting to download via Tor: {video_url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info_dict)
            print(f"✅ Downloaded: {filename}")
            return filename
    except Exception as e:
        # Don't print the full error by default as it can be very verbose
        print(f"❌ Failed to download {video_url}. It might be unavailable or blocked.")
        return None

# -----------------------------------------------------------------------------
# TikTok Scraper Agent (Main)
# -----------------------------------------------------------------------------
def tiktok_scraper_agent(niche: str, videos_per_hashtag: int = 2, max_hashtags: int = 2):
    """
    The main agent that orchestrates the scraping and downloading process via Tor.
    """
    # --- CRITICAL FIRST STEP: VERIFY TOR CONNECTION ---
    check_tor_connection()

    hashtags = get_evergreen_hashtags(niche)
    hashtags_to_process = hashtags[:max_hashtags]
    print(f"\n🔎 Using hashtags for niche '{niche}': {hashtags_to_process}")

    all_downloads = []
    for hashtag in hashtags_to_process:
        print(f"\n📂 Fetching videos for {hashtag}...")
        video_urls = get_tiktok_videos_by_hashtag(hashtag, limit=videos_per_hashtag)

        if not video_urls:
            print(f"No videos found for {hashtag}. Moving to the next.")
            continue

        for url in video_urls:
            print(f"➡️ Found video: {url}")
            file_path = download_tiktok_video(url)
            if file_path:
                all_downloads.append(file_path)
            time.sleep(random.randint(2, 5)) # Increase delay for Tor stability

    return all_downloads

# -----------------------------------------------------------------------------
# Example Run
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Before running, make sure you have the required libraries installed:
    # pip install selenium webdriver-manager yt-dlp requests "requests[socks]"
    
    # --- IMPORTANT ---
    # You MUST start the Tor Browser and leave it running in the background
    # for this script to work.
    
    downloaded_files = tiktok_scraper_agent("travel", videos_per_hashtag=1, max_hashtags=2)
    
    if downloaded_files:
        print("\n🎉 --- All Downloads Complete! --- 🎉")
        for f in downloaded_files:
            print(f" - {f}")
    else:
        print("\n⚠️ --- No videos were downloaded. --- ⚠️")
