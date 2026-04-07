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
    node [fontname="Helvetica", fontsize=12];
    edge [fontname="Helvetica", fontsize=10];
    rankdir=LR;
    
    Candidate [shape=box];
    Recruiter [shape=box];
    Notification [shape=box];
    
    System [shape=circle, label="0.0\\nSmartRecruit\\nSystem"];
    
    Candidate -> System [label="Resumes, Applications"];
    Recruiter -> System [label="Evaluation Rules\\nJob Posts"];
    System -> Candidate [label="Status Updates\\nTest Links"];
    System -> Recruiter [label="Analytical Reports\\nScores"];
    System -> Notification [label="Trigger SMS/Email"];
}
@enddot"""

# ─── DFD Level 1 - Graphviz DOT ───
dfd_1 = """@startdot
digraph G {
    node [fontname="Helvetica", fontsize=11];
    edge [fontname="Helvetica", fontsize=9];
    rankdir=LR;
    
    Candidate [shape=box];
    Recruiter [shape=box];
    
    P1 [shape=circle, label="1.0\\nProfile Parsing"];
    P2 [shape=circle, label="2.0\\nAssessment Gen"];
    P3 [shape=circle, label="3.0\\nCode Eval \\n& Interview"];
    P4 [shape=circle, label="4.0\\nAnalytics & Reports"];
    
    DB1 [shape=none, label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="4"><tr><td sides="T,B,L">D1</td><td sides="T,B">Candidate DB</td></tr></table>>];
    DB2 [shape=none, label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="4"><tr><td sides="T,B,L">D2</td><td sides="T,B">Question Bank DB</td></tr></table>>];
    
    Candidate -> P1 [label="Upload CV"];
    P1 -> DB1 [label="Save Parsed Skills"];
    DB1 -> P2 [label="Domain Experience"];
    DB2 -> P2 [label="Fetch Questions"];
    P2 -> Candidate [label="Provide Test"];
    Candidate -> P3 [label="Submit Code & Audio"];
    P3 -> DB1 [label="Update Score & Sentiment"];
    DB1 -> P4 [label="Aggregate Data"];
    P4 -> Recruiter [label="Dashboards & Reports"];
    Recruiter -> DB2 [label="Add New Questions"];
}
@enddot"""

# ─── DFD Level 2 - Graphviz DOT ───
dfd_2 = """@startdot
digraph G {
    node [fontname="Helvetica", fontsize=11];
    edge [fontname="Helvetica", fontsize=9];
    rankdir=LR;
    
    Candidate [shape=box];
    
    P31 [shape=circle, label="3.1\\nSubmit Code"];
    P32 [shape=circle, label="3.2\\nPiston Sandbox"];
    P33 [shape=circle, label="3.3\\nParse Results"];
    P34 [shape=circle, label="3.4\\nCalc Score & Sentiment"];
    
    DB1 [shape=none, label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="4"><tr><td sides="T,B,L">D1</td><td sides="T,B">Candidate DB</td></tr></table>>];
    
    Candidate -> P31 [label="Raw Snippet/Audio"];
    P31 -> P32 [label="Payload Const"];
    P32 -> P33 [label="Output Logs/Audio Stream"];
    P33 -> P34 [label="Metrics (Time/Mem/Emotion)"];
    P34 -> DB1 [label="Save Interview Results"];
}
@enddot"""

# ─── ER Diagram - PlantUML ───
er_diagram = """@startuml
!theme plain
skinparam backgroundColor white
skinparam classAttributeIconSize 0

entity "User" as user {
  * UserID : int <<PK>>
  --
  * Name : varchar
  * Email : varchar
  * Phone : varchar
  * Role : varchar
}

entity "JobPosting" as job {
  * JobID : int <<PK>>
  --
  * Title : varchar
  * Description : text
  * Requirements : text
  * PostedBy : int <<FK>>
}

entity "Application" as app {
  * AppID : int <<PK>>
  --
  * JobID : int <<FK>>
  * CandidateID : int <<FK>>
  * MatchScore : float
  * Status : varchar
}

entity "InterviewResult" as interview {
  * ResultID : int <<PK>>
  --
  * AppID : int <<FK>>
  * CodeScore : float
  * InterviewSentiment : float
  * FinalStatus : varchar
}

user ||--o{ job : creates
user ||--o{ app : applies
job ||--o{ app : receives
app ||--|| interview : generates
@enduml"""

# ─── Use Case Diagram ───
use_case = """@startuml
!theme plain
skinparam backgroundColor white
left to right direction

actor Candidate
actor Recruiter
actor "AI Agent\\n(Gemini/DeepFace)" as AI

rectangle "SmartRecruit System" {
  usecase "Upload Resume" as UC1
  usecase "Semantic Parsing (Score)" as UC2
  usecase "Take Code Assessment" as UC3
  usecase "AI Interview (Sentiment)" as UC4
  usecase "Post Job" as UC5
  usecase "Review Applicants" as UC6
  usecase "Generate Insights" as UC7
}

Candidate --> UC1
UC1 .> UC2 : <<include>>
Candidate --> UC3
Candidate --> UC4

Recruiter --> UC5
Recruiter --> UC6
Recruiter --> UC7

AI --> UC2
AI --> UC4
AI --> UC7
@enduml"""

# ─── Activity Diagram ───
activity_flow = """@startuml
!theme plain
skinparam backgroundColor white

|Candidate|
start
:Register & Apply;
:Upload Resume;

|AI Engine|
:Extract Skills & Calculate Match;
if (Match > 70%?) then (yes)
  :Auto-Shortlist to Round 2;
else (no)
  |Recruiter|
  :Manual Screen;
  if (Approve?) then (yes)
  else (no)
    :Reject;
    stop
  endif
endif

|Candidate|
:Take Coding Assessment;
:Submit Sandbox Code;

|Piston / AI Engine|
:Evaluate Code syntax & execution;
:Proceed to AI Video Interview;
:Stream Webcam + Audio;
:Analyze Real-time Sentiment (DeepFace);

|System Backend|
:Aggregate Scores;
:Generate Final Selection Report;

|Recruiter|
if (Select Candidate?) then (yes)
  :Send Offer Letter;
else (no)
  :Send Rejection Email;
endif
stop
@enduml"""

# ─── Class Diagram ───
class_diagram = """@startuml
!theme plain
skinparam backgroundColor white

class User {
  +user_id: Int
  +name: String
  +email: String
  +role: String
  +login()
  +register()
}

class Candidate {
  +resume_text: String
  +skills: List
  +match_score: Float
  +apply_for_job()
  +take_assessment()
}

class Recruiter {
  +company: String
  +post_job()
  +review_candidates()
}

class JobPosting {
  +job_id: Int
  +title: String
  +requirements: String
  +get_matches()
}

class AIEngine {
  +parse_resume()
  +evaluate_code()
  +analyze_sentiment()
}

class Application {
  +app_id: Int
  +status: String
  +code_score: Float
  +sentiment_score: Float
  +update_status()
}

User <|-- Candidate
User <|-- Recruiter
Recruiter "1" --> "0..*" JobPosting : posts
Candidate "1" --> "0..*" Application : submits
Application "0..*" --> "1" JobPosting : belongs to
AIEngine ..> Application : evaluates
@enduml"""

# ─── Sequence Diagram ───
sequence_diagram = """@startuml
!theme plain
skinparam backgroundColor white

actor Candidate
participant Frontend
participant Backend
participant "AI Engine / Piston" as AI
database MySQL

Candidate -> Frontend: Upload Resume & Apply
Frontend -> Backend: POST Application Data
Backend -> AI: Process Resume (Gemini)
AI --> Backend: Skills & Score
Backend -> MySQL: Save Application Status
Backend --> Frontend: 200 OK (Round 2 Unlock)

Candidate -> Frontend: Start Video Interview
Frontend -> Backend: Send Base64 Frame (WebSocket/API)
Backend -> AI: Analyze Emotion (DeepFace)
AI --> Backend: Sentiment Metrics
Backend -> MySQL: Log Sentiment Score
Backend --> Frontend: Bubble UI Update
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

print("Diagram generation completed successfully in light theme with strict DFD rules.")
