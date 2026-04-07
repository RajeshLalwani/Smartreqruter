import os
import re

root = r'c:\Users\ASUS\Documents\Tech Elecon Pvt. Ltd\Project\SmartRecruit\1_Web_Portal_Django\smartrecruit_project'

def fix_split_tags(content):
    # Join split {{ ... }}
    content = re.sub(r'\{\{([^}]*)\n([^}]*)\}\}', r'{{\1 \2}}', content)
    # Join split {% ... %}
    content = re.sub(r'\{%([^%]*)\n([^%]*)%\}', r'{%\1 \2%}', content)
    # Keep doing it until no more matches (for tags split across 3+ lines)
    for _ in range(5):
        content = re.sub(r'\{\{([^}]*)\n([^}]*)\}\}', r'{{\1 \2}}', content)
        content = re.sub(r'\{%([^%]*)\n([^%]*)%\}', r'{%\1 \2%}', content)
    return content

count = 0
for r_dir, _, files in os.walk(root):
    for f in files:
        if f.endswith('.html'):
            path = os.path.join(r_dir, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    old_content = file.read()
                
                new_content = fix_split_tags(old_content)
                
                if old_content != new_content:
                    with open(path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    print(f"FIXED: {path}")
                    count += 1
            except Exception as e:
                print(f"Error processing {path}: {e}")

print(f"TOTAL FILES CLEANED: {count}")
