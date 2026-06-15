import os
import sys

search_dirs = [
    r"C:\Users\kamal\AppData\Roaming\Code\User\History",
    r"C:\Users\kamal\.gemini\antigravity\brain"
]

print("Searching for original, untruncated base.html and dashboard.html...")

found_base = []
found_dash = []

for base_dir in search_dirs:
    if not os.path.exists(base_dir):
        print(f"Directory does not exist: {base_dir}")
        continue
    print(f"Scanning {base_dir}...")
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            file_path = os.path.join(root, file)
            # Skip metadata json files
            if file.endswith(".json"):
                continue
            try:
                # Read file content safely
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(100000) # Read up to 100KB
                    
                # Check for base.html signature
                # It should have HTML elements, extended content block, and not be truncated
                if "School Portal" in content and "portal.css" in content and "content" in content:
                    if "<truncated" not in content and len(content) > 500:
                        found_base.append((file_path, len(content), content[:200]))
                        
                # Check for dashboard.html signature
                if "stats.students" in content or ("attendance_pct" in content and "pending_announcements" in content and "announcements" in content):
                    if "<truncated" not in content and len(content) > 1000:
                        found_dash.append((file_path, len(content), content[:200]))
            except Exception:
                continue

print("\n--- Found Potential base.html Files ---")
for path, size, snippet in found_base:
    print(f"Path: {path} (Size: {size} bytes)\nSnippet: {snippet.strip()}\n")

print("--- Found Potential dashboard.html Files ---")
for path, size, snippet in found_dash:
    print(f"Path: {path} (Size: {size} bytes)\nSnippet: {snippet.strip()}\n")
