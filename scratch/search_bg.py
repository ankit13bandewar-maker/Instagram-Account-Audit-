import re

with open("c:/Users/user/Desktop/Client Audit/premium-dashboard/app/page.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# Find all className attributes
classnames = re.findall(r'className="([^"]+)"', content)

print("Background classes found:")
for cn in classnames:
    bg_classes = [c for c in cn.split() if c.startswith("bg-") or "gradient" in c]
    if bg_classes:
        print(f" - {cn} (Matched: {bg_classes})")
