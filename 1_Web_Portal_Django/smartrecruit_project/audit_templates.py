import os
import re

root = r'c:\Users\ASUS\Documents\Tech Elecon Pvt. Ltd\Project\SmartRecruit\1_Web_Portal_Django\smartrecruit_project'
patterns = [
    r'\{\{[^}]*\n[^}]*\}\}',
    r'\{%[^%]*\n[^%]*%\}',
    r'\{% if [^%]* %\}(?!.*\{% endif %\})', # Very basic unclosed if check (naive)
]

issues = []
for r_dir, _, files in os.walk(root):
    for f in files:
        if f.endswith('.html'):
            path = os.path.join(r_dir, f)
            try:
                c = open(path, 'r', encoding='utf-8').read()
                for p in patterns:
                    if re.search(p, c, re.MULTILINE):
                        issues.append(f"{path} (Pattern: {p})")
                        break
            except Exception as e:
                print(f"Error reading {path}: {e}")

if issues:
    print("ISSUES FOUND:")
    for issue in issues:
        print(issue)
else:
    print("NO SYNTAX ISSUES FOUND.")
