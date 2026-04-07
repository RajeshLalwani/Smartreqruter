import os
import re

def fix_split_template_tags(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Regex to find multi-line {% ... %} and {{ ... }} tags and collapse them safely
    # This uses a non-greedy approach.
    
    # 1. Fix {% tags %}
    content = re.sub(
        r'\{%([\s\S]*?)%\}', 
        lambda m: '{% ' + ' '.join(m.group(1).split()) + ' %}', 
        content
    )

    # 2. Fix {{ variables }}
    content = re.sub(
        r'\{\{([\s\S]*?)\}\}', 
        lambda m: '{{ ' + ' '.join(m.group(1).split()) + ' }}', 
        content
    )

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def sweep_directory(directory="."):
    print(f"Sweeping thoroughly across {directory} for broken template tags...")
    fixed_count = 0
    scanned_count = 0

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                scanned_count += 1
                try:
                    was_fixed = fix_split_template_tags(file_path)
                    if was_fixed:
                        fixed_count += 1
                        print(f"Fixed: {file_path}")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

    print("-" * 40)
    print(f"Scanned {scanned_count} HTML files.")
    print(f"Successfully repaired {fixed_count} files with broken/split multi-line tags.")
    print("-" * 40)

if __name__ == "__main__":
    # Start the sweep from the Django project root where manage.py is
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sweep_directory(base_dir)
