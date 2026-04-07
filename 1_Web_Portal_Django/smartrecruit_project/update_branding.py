import os

PROJECT_DIR = r"c:\Users\ASUS\Documents\IR Info Tech Pvt Ltd\Project\SmartRecruit\1_Web_Portal_Django\smartrecruit_project"

replacements = [
    ("IR Info Tech Pvt Ltd", "IR Info Tech Pvt Ltd"),
    ("IR Info Tech Pvt Ltd", "IR Info Tech Pvt Ltd"),
    ("IR Info Tech", "IR Info Tech"),
    ("irinfotech.com", "irinfotech.com")
]

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    original = content
    for old_str, new_str in replacements:
        content = content.replace(old_str, new_str)
        
    if original != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filepath}")

for root, dirs, files in os.walk(PROJECT_DIR):
    if 'venv' in root or '.git' in root or '__pycache__' in root or 'migrations' in root or 'node_modules' in root:
        continue
    for file in files:
        if file.endswith(('.html', '.py', '.txt', '.md', '.js', '.css')):
            process_file(os.path.join(root, file))

print("Branding update complete.")
