import os, re

template_dirs = ['core/templates', 'jobs/templates']

url_names = set()
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules']]
    for f in files:
        if f == 'urls.py':
            content = open(os.path.join(root,f), encoding='utf-8', errors='ignore').read()
            for m in re.finditer(r"name=['\"]([^'\"]+)['\"]", content):
                url_names.add(m.group(1))

broken = []
for tdir in template_dirs:
    for root, dirs, files in os.walk(tdir):
        for f in files:
            if f.endswith('.html'):
                path = os.path.join(root, f)
                content = open(path, encoding='utf-8', errors='ignore').read()
                for m in re.finditer(r"{%-?\s+url\s+['\"]([^'\"]+)['\"]", content):
                    name = m.group(1)
                    if name not in url_names:
                        broken.append((path, name))

if broken:
    seen = set()
    for path, name in sorted(broken):
        key = (os.path.basename(path), name)
        if key not in seen:
            seen.add(key)
            print(f"{path}: BROKEN -> '{name}'")
else:
    print("All template URL references look valid.")
