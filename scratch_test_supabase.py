import os
import sys
from dotenv import load_dotenv

# Load env
load_dotenv()

# Import the service
import supabase_service as db

print("=== Supabase Connection & Service Diagnostics ===")
print(f"Supabase configured: {db.is_supabase_configured()}")
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
print(f"SUPABASE_KEY: {'[SET]' if os.getenv('SUPABASE_KEY') else '[NOT SET]'}")

if not db.is_supabase_configured():
    print("\n[WARNING] Supabase is not fully configured. Running mock test with custom/local variables...")
    # Inject mock credentials for testing the client parsing / requests structure
    db.SUPABASE_URL = "https://mockproject.supabase.co"
    db.SUPABASE_KEY = "mockanonkey"
    print(f"Injected Mock SUPABASE_URL: {db.SUPABASE_URL}")
    print(f"Supabase configured: {db.is_supabase_configured()}")
else:
    print("\n[SUCCESS] Configuration active! Executing DB operation checks...")

# Test 1: Recent Audits fetch
print("\n--- Test 1: Fetching recent history ---")
recent = db.get_recent_audits(limit=3)
print(f"Recent runs: {recent}")

# Test 2: Inserting mock audit
print("\n--- Test 2: Saving mock audit ---")
mock_raw_posts = [
    {
        "likesCount": 10500,
        "commentsCount": 150,
        "timestamp": "2026-05-23T11:00:00Z",
        "type": "Image",
        "caption": "Testing Supabase Cache #test",
        "url": "https://instagram.com/p/test",
        "shortcode": "test"
    }
]
mock_report = "## 1. Core Performance Matrix\nMock report data."
mock_pipeline = {
    "handle": "supabase_test_user",
    "chart_data": [{"Metric": "Engagement %", "Value": 4.5}],
    "insights": {
        "handle": "supabase_test_user",
        "language_strategy": "Authority-led strategy",
        "top_hooks": ["Test Hook"],
        "metrics_summary": {"Engagement": "4.5%", "Followers": "100K", "Avg Likes": "10K"}
    }
}

success = db.save_audit_to_cache(
    profile_url="https://instagram.com/supabase_test_user",
    handle="supabase_test_user",
    raw_posts=mock_raw_posts,
    audit_report=mock_report,
    pipeline_data=mock_pipeline
)
print(f"Insert status: {'SUCCESS' if success else 'FAILED/OFFLINE'}")

# Test 3: Querying the cached audit
print("\n--- Test 3: Retrieving cached audit ---")
cache = db.get_cached_audit("supabase_test_user")
if cache:
    print("[SUCCESS] Cache retrieved successfully!")
    print(f"  Handle: {cache['handle']}")
    print(f"  Age: {cache['cache_age_hours']} hours ({cache['cache_age_days']} days)")
    print(f"  Scraped Posts Count: {len(cache['raw_posts'])}")
else:
    print("[INFO] Cache not retrieved (Either insert failed, offline, or expired).")

print("\nDiagnostics complete!")
