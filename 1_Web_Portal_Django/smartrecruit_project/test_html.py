import os

base_dir = r'c:\Users\ASUS\Documents\Tech Elecon Pvt. Ltd\Project\SmartRecruit\1_Web_Portal_Django\smartrecruit_project'
html_files = []
for root, _, files in os.walk(base_dir):
    if 'site-packages' in root or 'venv' in root or '.git' in root or 'media' in root: continue
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

for file in html_files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        div_open = content.count('<div')
        div_close = content.count('</div')
        if div_open != div_close:
            print(f'{os.path.basename(file)}: div count mismatch ({div_open} vs {div_close})')
            
        span_open = content.count('<span')
        span_close = content.count('</span')
        if span_open != span_close:
            print(f'{os.path.basename(file)}: span count mismatch ({span_open} vs {span_close})')
    except Exception as e:
        pass
