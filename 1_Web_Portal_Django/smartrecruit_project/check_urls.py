import os
import re
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

template_dirs = ['core/templates', 'jobs/templates', 'interview/templates']
url_pattern = re.compile(r"{%\s*url\s+['\"]([^'\"]+)['\"]")

broken = set()

for d in template_dirs:
    if not os.path.exists(d): continue
    for root, _, files in os.walk(d):
        for f in files:
            if f.endswith('.html'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    matches = url_pattern.findall(content)
                    for m in matches:
                        try:
                            # Try resolving without args. If it needs args, NoReverseMatch will say "Reverse for 'x' with arguments '...' not found."
                            # But if the name doesn't exist AT ALL, it says "Reverse for 'x' not found. 'x' is not a valid view function or pattern name."
                            reverse(m)
                        except NoReverseMatch as e:
                            # Check if the error completely rejects the URL name
                            msg = str(e)
                            if "is not a valid view function or pattern name" in msg:
                                broken.add((m, path))

if broken:
    print("Found invalid URL names in templates:")
    for m, p in broken:
        print(f"URL Name: {m} in Template: {p}")
else:
    print("All URLs in templates are valid and registered!")
