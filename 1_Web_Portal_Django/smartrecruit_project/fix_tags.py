import os, re

def fix_file(p):
    try:
        with open(p, 'r', encoding='utf-8') as f:
            content = f.read()
            
        def repl(m):
            t = m.group(0).replace('\n', ' ')
            t = re.sub(r'\s+', ' ', t)
            return t
        
        new_content = re.sub(r'\{%[\s\S]*?%\}', repl, content)
        
        if new_content != content:
            print(f'Fixed {p}')
            with open(p, 'w', encoding='utf-8') as f:
                f.write(new_content)
    except Exception as e:
        print(f"Error reading {p}: {e}")

for r, _, fs in os.walk('.'):
    for f in fs:
        if f.endswith('.html'):
            fix_file(os.path.join(r, f))
