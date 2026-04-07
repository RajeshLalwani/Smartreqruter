import re
content = open('jobs/templates/jobs/application_details.html', encoding='utf-8').read()
matches = re.findall(r'\{%[^%]+%\}', content)
for m in matches:
    if '\n' in m:
        print('MULTILINE TAG FOUND:', repr(m))
