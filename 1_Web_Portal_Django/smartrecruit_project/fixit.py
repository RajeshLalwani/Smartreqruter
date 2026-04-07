import re

with open('core/templates/recruiter_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('{{ pipeline_screening|default: "0"', '{{ pipeline_screening|default:"0"')
content = content.replace('{{ pipeline_assessment|default: "0" }', '{{ pipeline_assessment|default:"0" }')
content = content.replace('{{ pipeline_interview|default: "0" }}', '{{ pipeline_interview|default:"0" }}')
content = content.replace('{{ pipeline_offered|default: "0" }}', '{{ pipeline_offered|default:"0" }}')

# And clean up the tags themselves
content = re.sub(r'\{\{\s*pipeline_screening\|default:"0"\s*\}\},', '{{ pipeline_screening|default:"0" }},', content)
content = re.sub(r'\{\{\s*pipeline_assessment\|default:"0"\s*\}\s*\},', '{{ pipeline_assessment|default:"0" }},', content)

# just to be sure, let's look for the whole block
block = """                        data: [
                            {{ pipeline_screening|default:"0"
                    }},
                            {{ pipeline_assessment|default:"0" }
    },
        {{ pipeline_interview|default:"0" }},
        {{ pipeline_offered|default:"0" }}
                        ],"""

good_block = """                        data: [
                            {{ pipeline_screening|default:"0" }},
                            {{ pipeline_assessment|default:"0" }},
                            {{ pipeline_interview|default:"0" }},
                            {{ pipeline_offered|default:"0" }}
                        ],"""

content = content.replace(block, good_block)

with open('core/templates/recruiter_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("done")
