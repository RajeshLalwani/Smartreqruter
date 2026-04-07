import urllib.request
import zlib
import base64
import os

sequence_diagram = """@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontColor black
skinparam sequenceParticipantBackgroundColor white
skinparam sequenceParticipantBorderColor black
skinparam sequenceLifeLineBackgroundColor white
skinparam sequenceLifeLineBorderColor black
skinparam sequenceArrowColor black
autonumber

actor "Candidate" as cand
participant "Frontend UI" as front
participant "Backend Engine" as back
participant "AI DeepFace" as ai
database "MySQL" as db

cand -> front : 1. Apply (Upload CV)
activate front
front -> back : 2. Application JSON Payload
activate back
back -> ai : 3. Extract NLP Embeddings
activate ai
ai --> back : 4. Return Match Score
deactivate ai
back -> db : 5. INSERT Application
activate db
db --> back : 6. Acknowledge Write
deactivate db
back --> front : 7. 201 Created
deactivate back
front --> cand : 8. Status Update
deactivate front

cand -> front : 9. Join Live Interview
activate front
front -> back : 10. WebRTC Stream
activate back
back -> ai : 11. Audio/Video Code
activate ai
ai --> back : 12. Sentiment & Logs
deactivate ai
back -> db : 13. STORE Metrics
activate db
db --> back : 14. Acknowledge Write
deactivate db
back --> front : 15. Realtime Socket
deactivate back
front --> cand : 16. Validations
deactivate front
@enduml"""

code_bytes = sequence_diagram.encode('utf-8')
compressed_bytes = zlib.compress(code_bytes)
b64_str = base64.urlsafe_b64encode(compressed_bytes).decode('utf-8')

url = f"https://kroki.io/plantuml/png/{b64_str}"

try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(r"Diagrams\sequence_diagram.png", 'wb') as out_file:
        out_file.write(response.read())
    print("Successfully generated sequence diagram via Kroki!")
except Exception as e:
    print(f"Error: {e}")
