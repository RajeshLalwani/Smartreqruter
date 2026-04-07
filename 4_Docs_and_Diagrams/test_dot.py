import urllib.request, zlib, base64

def encode_puml(text):
    compressed = zlib.compress(text.encode('utf-8'))[2:-4]
    b64 = base64.b64encode(compressed).decode('utf-8')
    return b64.translate(str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/', '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'))

dot = """@startdot
digraph G {
    node [shape=none];
    DB1 [label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" COLOR="black">
         <TR><TD SIDES="T,B,L">D1</TD><TD SIDES="T,B">Candidate DB</TD></TR>
         </TABLE>>];
    User [shape=box];
    User -> DB1;
}
@enddot"""
try:
    url = "http://www.plantuml.com/plantuml/png/" + encode_puml(dot)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open("test_dot.png", "wb") as f:
        f.write(response.read())
    print("Success")
except Exception as e:
    print(e)
