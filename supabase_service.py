import os
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environmental variables from both .env (root) and premium-dashboard/.env.local
# First, try the .env file in the project root (if present)
load_dotenv()
# Then explicitly load the .env.local file used by the Next.js dev server
premium_env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'premium-dashboard', '.env.local'))
if os.path.exists(premium_env_path):
    load_dotenv(dotenv_path=premium_env_path, override=True)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def is_supabase_configured() -> bool:
    """Checks if Supabase configuration credentials are present in the environment."""
    return bool(
        SUPABASE_URL 
        and SUPABASE_KEY 
        and SUPABASE_URL != "your_supabase_project_url" 
        and SUPABASE_KEY != "your_supabase_anon_key"
        and "supabase.co" in SUPABASE_URL
    )

def _get_headers():
    """Generates the authorization headers required for Supabase PostgREST REST API."""
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def _extract_username(profile_url: str) -> str:
    """Surgically extracts the clean handle/username from any Instagram URL variant."""
    return profile_url.strip().rstrip("/").split("/")[-1].split("?")[0].lower()

def get_cached_audit(profile_url_or_handle: str) -> dict | None:
    """
    Queries Supabase for the most recent completed audit run matching the target handle.
    If a record exists and was created within the last 7 days, returns it.
    Otherwise, returns None.
    """
    if not is_supabase_configured():
        return None
    
    # Extract clean handle
    if "instagram.com" in profile_url_or_handle:
        handle = _extract_username(profile_url_or_handle)
    else:
        handle = profile_url_or_handle.strip().lower()
        
    try:
        url = f"{SUPABASE_URL}/rest/v1/instagram_audits?handle=eq.{handle}&order=created_at.desc&limit=1"
        response = requests.get(url, headers=_get_headers(), timeout=8)
        if response.status_code == 200:
            records = response.json()
            if records:
                record = records[0]
                created_at_str = record.get("created_at")
                if not created_at_str:
                    return None
                
                # Parse ISO-8601 timestamp safely in a timezone-aware fashion
                created_at_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                now_dt = datetime.now(timezone.utc)
                
                age = now_dt - created_at_dt
                if age < timedelta(days=7):
                    print(f"[Supabase Cache HIT] Valid cache found for '{handle}' (Audited: {created_at_str})")
                    
                    # Convert raw_posts if string, otherwise return as-is
                    raw_posts = record.get("raw_posts")
                    if isinstance(raw_posts, str):
                        import json
                        raw_posts = json.loads(raw_posts)
                        
                    pipeline_data = record.get("pipeline_data")
                    if isinstance(pipeline_data, str):
                        import json
                        pipeline_data = json.loads(pipeline_data)

                    return {
                        "handle": record.get("handle"),
                        "profile_url": record.get("profile_url"),
                        "raw_posts": raw_posts,
                        "audit_report": record.get("audit_report"),
                        "pipeline_data": pipeline_data,
                        "created_at": created_at_str,
                        "cache_age_days": age.days,
                        "cache_age_hours": int(age.total_seconds() // 3600)
                    }
                else:
                    print(f"[Supabase Cache EXPIRED] Stale cache found for '{handle}' ({age.days} days old)")
        else:
            print(f"[Supabase Cache] Check failed (status {response.status_code}): {response.text}")
    except Exception as e:
        print(f"[Supabase Exception] Failed to query cached audits: {e}")
        
    return None

def save_audit_to_cache(profile_url: str, handle: str, raw_posts: list, audit_report: str, pipeline_data: dict) -> bool:
    """
    Saves a completed Instagram audit run (raw posts, AI report, and pipeline data)
    to Supabase for 7-day caching.
    """
    if not is_supabase_configured():
        return False
        
    try:
        payload = {
            "handle": handle.lower(),
            "profile_url": profile_url,
            "raw_posts": raw_posts,
            "audit_report": audit_report,
            "pipeline_data": pipeline_data,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        url = f"{SUPABASE_URL}/rest/v1/instagram_audits"
        response = requests.post(url, headers=_get_headers(), json=payload, timeout=8)
        
        if response.status_code in [200, 201]:
            print(f"[Supabase Cache] Successfully saved completed audit for '{handle}' to database.")
            return True
        else:
            print(f"[Supabase Cache] Failed to insert audit (status {response.status_code}): {response.text}")
    except Exception as e:
        print(f"[Supabase Exception] Failed to cache completed audit: {e}")
        
    return False

def get_recent_audits(limit: int = 5) -> list:
    """
    Fetches a unique list of the most recently audited handles in Supabase
    to populate the interactive sidebar history dashboard.
    """
    if not is_supabase_configured():
        return []
        
    try:
        url = f"{SUPABASE_URL}/rest/v1/instagram_audits?select=handle,profile_url,created_at&order=created_at.desc&limit=25"
        response = requests.get(url, headers=_get_headers(), timeout=8)
        if response.status_code == 200:
            records = response.json()
            seen_handles = set()
            unique_records = []
            for r in records:
                h = r.get("handle")
                if h and h not in seen_handles:
                    seen_handles.add(h)
                    unique_records.append(r)
                    if len(unique_records) >= limit:
                        break
            return unique_records
    except Exception as e:
        print(f"[Supabase Exception] Failed to query recent history: {e}")
        
    return []
