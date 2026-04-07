import os

PROJECT_DIR = r"C:\Users\ASUS\Documents\Tech Elecon Pvt. Ltd\Project\SmartRecruit\1_Web_Portal_Django\smartrecruit_project"

replacements = [
    ("Isha Info Tech Private Limited", "IR Info Tech Private Limited"),
    ("Isha Info Tech Pvt. Ltd.", "IR Info Tech Pvt Ltd"),
    ("Isha Info Tech", "IR Info Tech"),
    ("ishainfotech.com", "irinfotech.com"),
    ("img/Isha_Logo.png", "images/ir_logo.png")
]

def process_file(filepath):
    # Skip the script itself
    if os.path.abspath(filepath) == os.path.abspath(__file__):
        return
        
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original = content
        for old_str, new_str in replacements:
            content = content.replace(old_str, new_str)
            
        if original != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

for root, dirs, files in os.walk(PROJECT_DIR):
    if any(x in root for x in ['venv', '.git', '__pycache__', 'migrations', 'node_modules', 'staticfiles']):
        continue
    for file in files:
        if file.endswith(('.html', '.py', '.txt', '.md', '.js', '.css', '.json')):
            process_file(os.path.join(root, file))

print("Branding update complete.")
