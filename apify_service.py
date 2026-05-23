import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient

# Load .env so APIFY_API_TOKEN is available regardless of import order
load_dotenv()
CSV_PATH     = r"c:\Users\user\Desktop\Client Audit\instagram_posts_dataset.csv"
ACTOR_ID     = "apify/instagram-scraper"   # Official Apify Instagram scraper actor
MAX_POSTS    = 15


def _extract_username(profile_url: str) -> str:
    """Pull clean username out of any Instagram URL variant."""
    return profile_url.strip().rstrip("/").split("/")[-1].split("?")[0].lower()


def _load_csv_for_profile(username: str) -> list | None:
    """
    Return cached posts from CSV if they exist for this username.
    Returns None if no rows are found.
    """
    if not os.path.exists(CSV_PATH):
        return None
    try:
        df = pd.read_csv(CSV_PATH).fillna("")
        df_filtered = df[df["profile_url"].str.contains(username, case=False, na=False)]
        if df_filtered.empty:
            return None
        posts = []
        for _, row in df_filtered.iterrows():
            posts.append({
                "likesCount":    int(row.get("likes", 0)),
                "commentsCount": int(row.get("comments", 0)),
                "timestamp":     str(row.get("timestamp", "")),
                "type":          str(row.get("type", "Image")),
                "caption":       str(row.get("caption", "")),
                "url":           str(row.get("url", "")),
                "shortcode":     str(row.get("shortcode", "")),
            })
        print(f"[Cache HIT] Loaded {len(posts)} posts for '{username}' from CSV.")
        return posts[:MAX_POSTS]
    except Exception as e:
        print(f"[Cache] Error reading CSV: {e}")
        return None


def _save_to_csv(profile_url: str, posts: list):
    """Persist freshly scraped posts to CSV so future requests are instant."""
    try:
        rows = []
        for p in posts:
            rows.append({
                "profile_url": profile_url,
                "likes":       p.get("likesCount", 0),
                "comments":    p.get("commentsCount", 0),
                "timestamp":   p.get("timestamp", ""),
                "type":        p.get("type", "Image"),
                "caption":     p.get("caption", ""),
                "url":         p.get("url", ""),
                "shortcode":   p.get("shortcode", ""),
            })
        df_new = pd.DataFrame(rows)

        if os.path.exists(CSV_PATH):
            df_old = pd.read_csv(CSV_PATH).fillna("")
            username = _extract_username(profile_url)
            # Remove stale rows for this profile before appending fresh ones
            df_old = df_old[~df_old["profile_url"].str.contains(username, case=False, na=False)]
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
            df_combined.to_csv(CSV_PATH, index=False)
        else:
            df_new.to_csv(CSV_PATH, index=False)

        print(f"[Cache] Saved {len(rows)} posts for '{profile_url}' to CSV.")
    except Exception as e:
        print(f"[Cache] Error saving to CSV: {e}")


def _scrape_via_apify(profile_url: str) -> list:
    """
    Run the official Apify Instagram Scraper actor and return raw post dicts.
    Raises an exception if scraping fails so the caller can handle it.
    """
    # Read token lazily so dotenv has time to load
    token = os.getenv("APIFY_API_TOKEN", "")
    if not token:
        raise RuntimeError("APIFY_API_TOKEN is not set in .env")

    print(f"[Apify] Starting live scrape for: {profile_url}")
    client = ApifyClient(token)

    run_input = {
        "directUrls":        [profile_url],
        "resultsType":       "posts",
        "resultsLimit":      MAX_POSTS,
        "addParentData":     False,
    }

    run = client.actor(ACTOR_ID).call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"[Apify] Scrape complete. Got {len(items)} items.")

    posts = []
    for item in items:
        # Apify Instagram Scraper field names
        shortcode  = item.get("shortCode") or item.get("shortcode") or ""
        post_url   = item.get("url") or (f"https://www.instagram.com/p/{shortcode}/" if shortcode else "")
        timestamp  = item.get("timestamp") or item.get("taken_at_timestamp") or datetime.utcnow().isoformat()
        post_type  = item.get("type") or ("Video" if item.get("isVideo") else "Image")

        posts.append({
            "likesCount":    int(item.get("likesCount") or item.get("likes_count") or 0),
            "commentsCount": int(item.get("commentsCount") or item.get("comments_count") or 0),
            "timestamp":     str(timestamp),
            "type":          post_type,
            "caption":       str(item.get("caption") or ""),
            "url":           post_url,
            "shortcode":     shortcode,
        })

    if not posts:
        raise RuntimeError(f"Apify returned 0 posts for {profile_url}. Profile may be private or URL is incorrect.")

    return posts[:MAX_POSTS]


def scrape_latest_15_posts(profile_url: str) -> list:
    """
    Main entry point called by main.py.

    Flow:
      1. Check CSV cache — if posts exist for this profile, return instantly.
      2. If not cached, call Apify to scrape real Instagram data.
      3. Save scraped posts to CSV for future instant loads.
      4. Return the real post data.
    """
    username = _extract_username(profile_url)

    # ── Step 1: Try CSV cache first ──
    cached = _load_csv_for_profile(username)
    if cached:
        return cached

    # ── Step 2: Live Apify scrape ──
    print(f"[Cache MISS] No data for '{username}'. Triggering Apify live scrape...")
    posts = _scrape_via_apify(profile_url)

    # ── Step 3: Cache to CSV ──
    _save_to_csv(profile_url, posts)

    return posts