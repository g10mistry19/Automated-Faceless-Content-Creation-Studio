import os
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
import yt_dlp

# -----------------------------------------------------------------------------
# --- MANDATORY USER CONFIGURATION ---
# -----------------------------------------------------------------------------
# You MUST update this path to point to the root directory of your Tor Browser installation.
# The script will not work without the correct path.

# --- Examples ---
# Windows: TOR_BROWSER_PATH = r"C:\Users\YourUser\Desktop\Tor Browser"
# macOS:   TOR_BROWSER_PATH = r"/Applications/Tor Browser.app"
# Linux:   TOR_BROWSER_PATH = r"/home/YourUser/tor-browser_en-US"

TOR_BROWSER_PATH = r"D:\Tor\Tor Browser"

# -----------------------------------------------------------------------------
# Tor Proxy Configuration & Check
# -----------------------------------------------------------------------------
TOR_SOCKS_HOST = "127.0.0.1"
TOR_SOCKS_PORT = 9150
TOR_PROXY = f"socks5h://{TOR_SOCKS_HOST}:{TOR_SOCKS_PORT}"

def check_tor_connection():
    """Verifies that the script can connect to the Tor network."""
    print("Checking if Tor network is accessible...")
    proxies = {'http': TOR_PROXY, 'https': TOR_PROXY}
    try:
        response = requests.get("https://check.torproject.org/api/ip", proxies=proxies, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("IsTor"):
            print(f"✅ Successfully connected to Tor. Your IP is: {data.get('IP')}")
            return True
        else:
            print("❌ Connected, but not via Tor. Please check your setup.")
            raise SystemExit("Exiting: Not a Tor connection.")
    except requests.exceptions.RequestException as e:
        print("\n" + "="*50)
        print("❌ CRITICAL ERROR: Could not connect to the Tor network.")
        print("   Please ensure the Tor Browser application is running.")
        print(f"   Error details: {e}")
        print("="*50 + "\n")
        raise SystemExit("Exiting: Tor connection failed.")

# -----------------------------------------------------------------------------
# Evergreen Hashtags Tool
# -----------------------------------------------------------------------------
def get_evergreen_hashtags(niche: str) -> list:
    """Provides a list of popular hashtags for a given niche."""
    evergreen = {
        "pets": ["#pets", "#dogsoftiktok", "#catsoftiktok", "#petlovers", "#cutepets"],
        "fitness": ["#fitness", "#workout", "#fitlife", "#gymmotivation", "#healthylifestyle"],
        "cooking": ["#cooking", "#foodie", "#easyrecipes", "#tiktokfood", "#homemade"],
        "travel": ["#travel", "#wanderlust", "#explore", "#nature", "#adventure"],
        "education": ["#learnontiktok", "#study", "#education", "#motivation", "#knowledge"]
    }
    return evergreen.get(niche.lower(), ["#foryou", "#trending", "#viral"])

# -----------------------------------------------------------------------------
# Scrape TikTok by Hashtag using the ACTUAL TOR BROWSER
# -----------------------------------------------------------------------------
def get_tiktok_videos_by_hashtag(hashtag: str, limit: int = 5, scroll_pause_time: int = 5):
    """
    Automates the actual Tor Browser application to scrape TikTok.
    """
    print(f"Initializing Tor Browser to scrape {hashtag}...")
    url = f"https://www.tiktok.com/tag/{hashtag.lstrip('#')}"

    if not os.path.isdir(TOR_BROWSER_PATH):
        print(f"❌ Error: The Tor Browser path you provided is not a valid directory.")
        print(f"   Your path: '{TOR_BROWSER_PATH}'")
        print("   Please update the TOR_BROWSER_PATH variable at the top of the script.")
        return []

    # --- Define paths based on OS ---
    if "Tor Browser.app" in TOR_BROWSER_PATH: # macOS
        tbb_binary_path = os.path.join(TOR_BROWSER_PATH, "Contents/MacOS/firefox")
        tbb_profile_path = os.path.join(TOR_BROWSER_PATH, "Contents/Resources/TorBrowser/data/Browser/profile.default")
    else: # Windows/Linux
        tbb_binary_path = os.path.join(TOR_BROWSER_PATH, "Browser/firefox.exe") if os.name == 'nt' else os.path.join(TOR_BROWSER_PATH, "Browser/firefox")
        tbb_profile_path = os.path.join(TOR_BROWSER_PATH, "Browser/TorBrowser/Data/Browser/profile.default")

    if not os.path.exists(tbb_binary_path):
        print(f"❌ Error: Could not find the Firefox binary for Tor Browser at '{tbb_binary_path}'")
        return []

    # --- Setup Selenium for Tor Browser ---
    tor_binary = FirefoxBinary(tbb_binary_path)
    tor_profile = FirefoxProfile(tbb_profile_path)
    
    options = FirefoxOptions()
    options.binary = tor_binary
    options.profile = tor_profile

    # Set proxy settings in the profile for explicit control
    tor_profile.set_preference('network.proxy.type', 1)
    tor_profile.set_preference('network.proxy.socks', TOR_SOCKS_HOST)
    tor_profile.set_preference('network.proxy.socks_port', TOR_SOCKS_PORT)
    tor_profile.set_preference('network.proxy.socks_remote_dns', True)
    
    try:
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
    except Exception as e:
        print(f"❌ Error setting up WebDriver for Tor Browser: {e}")
        return []

    video_links = set()
    try:
        # The Tor Browser will now open and connect. This can take a moment.
        print("Tor Browser is starting. Please wait for the connection...")
        driver.get(url)
        
        print("Waiting for video grid to load...")
        video_grid_selector = (By.CSS_SELECTOR, '[data-e2e="search-video-list"]')
        WebDriverWait(driver, 45).until( # Increased wait time for Tor
            EC.presence_of_element_located(video_grid_selector)
        )
        print("✅ Video grid found. Starting to scrape links.")

        last_height = driver.execute_script("return document.body.scrollHeight")
        while len(video_links) < limit:
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
            time.sleep(scroll_pause_time)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("Reached the end of the page.")
                break
            last_height = new_height

    except TimeoutException:
        print("❌ Timed out waiting for content. TikTok may be blocking the request.")
    except Exception as e:
        print(f"❌ An unexpected error occurred while scraping: {e}")
    finally:
        print("Closing Tor Browser window...")
        time.sleep(3)
        driver.quit()

    return list(video_links)[:limit]

# -----------------------------------------------------------------------------
# Download TikTok Video using yt-dlp (via Tor)
# -----------------------------------------------------------------------------
def download_tiktok_video(video_url: str, save_path: str = "downloads"):
    """Downloads a TikTok video using yt-dlp, routing through the Tor proxy."""
    os.makedirs(save_path, exist_ok=True)
    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
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
        print(f"❌ Failed to download {video_url}.")
        return None

# -----------------------------------------------------------------------------
# TikTok Scraper Agent (Main)
# -----------------------------------------------------------------------------
def tiktok_scraper_agent(niche: str, videos_per_hashtag: int = 2, max_hashtags: int = 2):
    """Orchestrates the scraping and downloading process via the Tor Browser."""
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
            time.sleep(random.randint(3, 6))

    return all_downloads

# -----------------------------------------------------------------------------
# Example Run
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Before running, make sure you have the required libraries:
    # pip install selenium webdriver-manager yt-dlp requests "requests[socks]"
    
    # --- IMPORTANT ---
    # 1. You MUST update the TOR_BROWSER_PATH variable at the top of this script.
    # 2. You MUST start the Tor Browser application manually first and leave it running.
    
    downloaded_files = tiktok_scraper_agent("travel", videos_per_hashtag=1, max_hashtags=2)
    
    if downloaded_files:
        print("\n🎉 --- All Downloads Complete! --- 🎉")
        for f in downloaded_files:
            print(f" - {f}")
    else:
        print("\n⚠️ --- No videos were downloaded. --- ⚠️")
