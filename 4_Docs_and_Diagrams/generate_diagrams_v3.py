import urllib.request
import zlib
import base64
import os

def encode_plantuml(text):
    compressed_string = zlib.compress(text.encode('utf-8'))[2:-4]
    b64 = base64.b64encode(compressed_string).decode('utf-8')
    b64 = b64.translate(str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/',
                                      '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'))
    return b64

def generate_png(code_text, filename):
    encoded = encode_plantuml(code_text)
    url = f"http://www.plantuml.com/plantuml/png/{encoded}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
            out_file.write(response.read())
        print(f"Generated {filename}")
    except Exception as e:
        print(f"Error generating {filename}: {e}")

target_dir = r"C:\Users\ASUS\Documents\Tech Elecon Pvt. Ltd\Project\SmartRecruit\4_Docs_and_Diagrams\Diagrams"
if not os.path.exists(target_dir):
    os.makedirs(target_dir)
os.chdir(target_dir)

# ─── DFD Level 0 (Context Diagram) - Graphviz DOT ───
dfd_0 = """@startdot
digraph G {
    node [fontname="Arial", fontsize=12, style=solid, color=black];
    edge [fontname="Arial", fontsize=10, color=black];
    rankdir=LR;
    bgcolor="white";
    
    Candidate [shape=box, width=1.5, height=0.6];
    Recruiter [shape=box, width=1.5, height=0.6];
    
    System [shape=circle, margin=0.2, label="0.0\\nSmartRecruit\\nSystem"];
    
    Candidate -> System [label="Resumes\\nApplications"];
    Recruiter -> System [label="Job Posts\\nSettings"];
    System -> Candidate [label="Status Updates\\nAssessments"];
    System -> Recruiter [label="Evaluation Reports"];
}
@enddot"""

# ─── DFD Level 1 - Graphviz DOT ───
dfd_1 = """@startdot
digraph G {
    node [fontname="Arial", fontsize=11, color=black];
    edge [fontname="Arial", fontsize=10, color=black];
    rankdir=LR;
    bgcolor="white";
    
    Candidate [shape=box, width=1.2];
    Recruiter [shape=box, width=1.2];
    
    P1 [shape=circle, label="1.0\\nProfile\\nParsing"];
    P2 [shape=circle, label="2.0\\nAssessment\\nGeneration"];
    P3 [shape=circle, label="3.0\\nInterview\\n& Coding"];
    P4 [shape=circle, label="4.0\\nReporting\\nAnalytics"];
    
    DB1 [shape=none, label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="8"><tr><td sides="LTB">D1</td><td sides="TB">Candidate DB</td></tr></table>>];
    DB2 [shape=none, label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="8"><tr><td sides="LTB">D2</td><td sides="TB">Evaluation DB</td></tr></table>>];
    
    Candidate -> P1 [label="Upload Info"];
    P1 -> DB1 [label="Insert Profile"];
    DB1 -> P2 [label="Experience Data"];
    P2 -> Candidate [label="Serve Test"];
    Candidate -> P3 [label="Submit Interaction"];
    P3 -> DB2 [label="Save Sentiment\\n& Score"];
    DB2 -> P4 [label="Fetch Records"];
    P4 -> Recruiter [label="Provide Summary"];
    Recruiter -> DB1 [label="Manage Postings"];
}
@enddot"""

# ─── DFD Level 2 - Graphviz DOT ───
dfd_2 = """@startdot
digraph G {
    node [fontname="Arial", fontsize=11, color=black];
    edge [fontname="Arial", fontsize=10, color=black];
    rankdir=LR;
    bgcolor="white";
    
    Candidate [shape=box, width=1.2];
    
    P31 [shape=circle, label="3.1\\nCapture\\nAudio/Video"];
    P32 [shape=circle, label="3.2\\nPiston\\nExecution"];
    P33 [shape=circle, label="3.3\\nAI Sentiment\\nAnalysis"];
    P34 [shape=circle, label="3.4\\nCompute\\nFinal Score"];
    
    DB2 [shape=none, label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="8"><tr><td sides="LTB">D2</td><td sides="TB">Evaluation DB</td></tr></table>>];
    
    Candidate -> P31 [label="Webcam Feed"];
    Candidate -> P32 [label="Raw Code"];
    P31 -> P33 [label="Extracted Frames"];
    P32 -> P34 [label="Execution Log"];
    P33 -> P34 [label="Emotion Matrix"];
    P34 -> DB2 [label="Store Metrics"];
}
@enddot"""

# ─── ER Diagram - PlantUML ───
er_diagram = """@startuml
skinparam backgroundColor white
skinparam monochrome true
skinparam shadowing false
skinparam classAttributeIconSize 0

entity "User" as user {
  * UserID : INT
  --
  Name : VARCHAR
  Role : VARCHAR
}

entity "JobPosting" as job {
  * JobID : INT
  --
  Title : VARCHAR
  Status : VARCHAR
}

entity "Application" as app {
  * AppID : INT
  --
  MatchScore : FLOAT
  Status : VARCHAR
}

entity "InterviewResult" as interview {
  * ResultID : INT
  --
  CodeScore : FLOAT
  Sentiment : FLOAT
}

user ||--o{ job : "posts"
user ||--o{ app : "applies"
job ||--o{ app : "receives"
app ||--|| interview : "has"
@enduml"""

# ─── Use Case Diagram (STICK MAN) ───
use_case = """@startuml
skinparam actorStyle stick
skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontColor black
skinparam actorBackgroundColor white
skinparam actorBorderColor black
skinparam usecaseBackgroundColor white
skinparam usecaseBorderColor black
skinparam ArrowColor black
left to right direction

actor "Candidate" as candidate
actor "Recruiter" as recruiter
actor "System AI" as ai

rectangle "SmartRecruit Ecosystem" {
  usecase "Upload Resume" as UC1
  usecase "Match Analytics" as UC2
  usecase "Participate in AI Interview" as UC3
  usecase "Post Job Requirements" as UC4
  usecase "View Candidate Matrices" as UC5
  usecase "Sentiment Tracking" as UC6
}

candidate --> UC1 : Executes
candidate --> UC3 : Joins

recruiter --> UC4 : Manages
recruiter --> UC5 : Analyzes

ai --> UC2 : Processes
ai --> UC6 : Evaluates

UC1 ..> UC2 : <<include>>
UC3 ..> UC6 : <<extend>>
@enduml"""

# ─── Activity Diagram ───
activity_flow = """@startuml
skinparam backgroundColor white
skinparam monochrome true
skinparam shadowing false

|Candidate|
start
:Register Profile;
:Apply for Job;

|System Backend|
:Run NLP Resume Parser;
if (Match >= Threshold?) then (Yes)
  :Schedule Interview;
else (No)
  :Reject Automatically;
  stop
endif

|Candidate|
:Launch Sandbox;
:Conduct Technical Execution;

|System Backend|
:Process Sentiment via DeepFace;
:Aggregate Assessment Score;
:Notify Recruiter;

|Recruiter|
:Review Aggregated Summary;
if (Acceptable?) then (Yes)
  :Generate Offer;
else (No)
  :Send Rejection;
endif
stop
@enduml"""

# ─── Class Diagram ───
class_diagram = """@startuml
skinparam backgroundColor white
skinparam monochrome true
skinparam shadowing false
hide circle

class User {
  +user_id: int
  +name: string
  +login()
}

class Candidate {
  +resume: file
  +apply_job()
}

class Recruiter {
  +company: string
  +post_job()
}

class JobPosting {
  +job_id: int
  +title: string
  +get_applicants()
}

class Application {
  +status: string
  +score: float
  +update_state()
}

class AIEngine {
  +parse_resume()
  +analyze_sentiment()
}

User <|-- Candidate
User <|-- Recruiter
Recruiter "1" --> "*" JobPosting
Candidate "1" --> "*" Application
JobPosting "1" --> "*" Application
AIEngine ..> Application : "evaluates"
@enduml"""

# ─── Sequence Diagram ───
sequence_diagram = """@startuml
skinparam backgroundColor white
skinparam monochrome true
skinparam shadowing false
autonumber

actor "Candidate" as cand
participant "Frontend UI" as front
participant "Backend Engine" as back
participant "AI DeepFace / Gemini" as ai
database "MySQL" as db

cand -> front : 1. Apply (Upload CV)
activate front
front -> back : 2. Application JSON Payload
activate back
back -> ai : 3. Extract NLP Embeddings
activate ai
ai --> back : 4. Return Resume Vector Match Score
deactivate ai
back -> db : 5. INSERT Application & Score
activate db
db --> back : 6. Acknowledge Complete
deactivate db
back --> front : 7. Return 201 Created
deactivate back
front --> cand : 8. Dashboard Status Update
deactivate front

cand -> front : 9. Join Live Piston Interview
activate front
front -> back : 10. Start WebRTC Stream & Code Sync
activate back
back -> ai : 11. Feed Audio/Video frames & Python Code
activate ai
ai --> back : 12. Return Sentiment & Piston Log
deactivate ai
back -> db : 13. STORE Security and Evaluation Metrics
activate db
db --> back : 14. Acknowledge Write
deactivate db
back --> front : 15. Push WebSocket Realtime Result
deactivate back
front --> cand : 16. Show Live Validations
deactivate front
@enduml"""


diagrams = {
    "dfd_level_0.png": dfd_0,
    "dfd_level_1.png": dfd_1,
    "dfd_level_2.png": dfd_2,
    "er_diagram.png": er_diagram,
    "use_case.png": use_case,
    "activity_flow.png": activity_flow,
    "class_diagram.png": class_diagram,
    "sequence_diagram.png": sequence_diagram
}

for filename, text in diagrams.items():
    generate_png(text, filename)

print("Diagram generation completed with Classic Stickman, and Pure Monochrome themes.")
