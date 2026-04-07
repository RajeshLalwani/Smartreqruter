import re

path = 'jobs/templates/jobs/candidate_applications.html'
with open(path, encoding='utf-8') as f:
    content = f.read()

# Fix: status=='VALUE' -> status == 'VALUE'
fixed = re.sub(r"(\w+)=='", r"\1 == '", content)
# Fix: "VALUE"== -> "VALUE" ==  (reverse)
fixed = re.sub(r"'==(\w)", r"' == \1", fixed)

with open(path, 'w', encoding='utf-8') as f:
    f.write(fixed)

print("Done")
