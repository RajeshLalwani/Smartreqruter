import os, re

# Search all html files for broken default filters
problems = []
for r, _, fs in os.walk('.'):
    for f in fs:
        if f.endswith('.html'):
            path = os.path.join(r, f)
            try:
                with open(path, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                # Find all {{ ... }} expressions and check for "default:" with no argument
                matches = re.findall(r'\{\{[^}]+\}\}', content)
                for m in matches:
                    if 'default:' in m:
                        # Check: default:arg where arg is nothing (another filter or end)
                        bad = re.search(r'default:\s*(\||\})', m)
                        if bad:
                            problems.append((path, m.strip()))
            except Exception as e:
                print(f"Error {path}: {e}")

print("Problems found:")
for p, m in problems:
    print(f"  {p}: {m}")
