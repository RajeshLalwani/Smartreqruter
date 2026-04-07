import io
with io.open('test_output_details2.txt', encoding='utf-16le') as f:
    lines = f.readlines()
curr_html = ''
for l in lines:
    if '.html' in l:
        curr_html = l.strip()
    if 'TemplateSyntaxError' in l:
        print(f'{curr_html}: {l.strip()}')
