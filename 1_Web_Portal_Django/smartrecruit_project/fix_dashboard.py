import re

with open('core/templates/recruiter_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix default spacing: |default: "0" -> |default:"0"
content = re.sub(r'\|default:\s+', '|default:', content)

# Fix multiline tags: collapse any newlines inside {{ ... }} just for these keys
content = re.sub(r'\{\{\s*job\.title\s*\}\}', '{{ job.title }}', content, flags=re.MULTILINE|re.DOTALL)

# Fix job.deadline with |default
content = re.sub(r'\{\{\s*job\.deadline\|date:"M d, Y"\|default:"--"\s*\}\}', '{{ job.deadline|date:"M d, Y"|default:"--" }}', content, flags=re.MULTILINE|re.DOTALL)

# Fix pipeline multiline tags
content = re.sub(r'\{\{\s*pipeline_screening\|default:"0"\s*\}\}', '{{ pipeline_screening|default:"0" }}', content, flags=re.MULTILINE|re.DOTALL)
content = re.sub(r'\{\{\s*pipeline_assessment\|default:"0"\s*\}\}', '{{ pipeline_assessment|default:"0" }}', content, flags=re.MULTILINE|re.DOTALL)
content = re.sub(r'\{\{\s*pipeline_interview\|default:"0"\s*\}\}', '{{ pipeline_interview|default:"0" }}', content, flags=re.MULTILINE|re.DOTALL)
content = re.sub(r'\{\{\s*pipeline_offered\|default:"0"\s*\}\}', '{{ pipeline_offered|default:"0" }}', content, flags=re.MULTILINE|re.DOTALL)

with open('core/templates/recruiter_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed successfully')
