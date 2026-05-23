import os
from dotenv import load_dotenv
load_dotenv()

from auditor import run_single_post_audit

# Sample post data matching Post 8 from the screenshot
sample_post = {
    "index": "Post 8",
    "type": "Image",
    "likes": 13118,
    "comments": 255,
    "caption": "Hottest Places In India 🌡️ #rvcjinsta"
}

print("Running test audit for Post 8...")
result = run_single_post_audit(
    post_data=sample_post,
    is_above_baseline=True,
    median_likes=10600,
    median_comments=146
)

print("Writing result to result.txt...")
with open("result.txt", "w", encoding="utf-8") as f:
    f.write(result)
print("Done!")
