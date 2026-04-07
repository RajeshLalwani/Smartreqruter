import urllib.request
import urllib.parse
import zlib
import base64
import os
import string

def encode_plantuml(text):
    zlibbed_str = zlib.compress(text.encode('utf-8'))
    compressed_string = zlibbed_str[2:-4]
    
    # Base64 encoding for PlantUML
    b64 = base64.b64encode(compressed_string).decode('utf-8')
    b64 = b64.translate(str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/',
                                      '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'))
    return b64

def generate_png(plantuml_text, filename):
    encoded = encode_plantuml(plantuml_text)
    url = f"http://www.plantuml.com/plantuml/png/{encoded}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        print(f"Generated {filename}")
    except Exception as e:
        print(f"Error generating {filename}: {e}")

# Ensure target directory exists
target_dir = r"C:\Users\ASUS\Documents\Tech Elecon Pvt. Ltd\Project\SmartRecruit\4_Docs_and_Diagrams"
os.chdir(target_dir)

# 1. DFD Level 0
dfd_0 = """
@startuml
!theme toy
skinparam backgroundColor transparent
skinparam componentStyle rectangle

agent Candidate
agent Recruiter
component "SmartRecruit\\nSystem" as System
agent "Notification API" as Notification

Candidate --> System : Resumes, Action
Recruiter --> System : Evaluation Rules
System --> Candidate : Status Updates
System --> Recruiter : Analytical Reports
System --> Notification : Trigger SMS/Email

@enduml
"""

# 2. DFD Level 1
dfd_1 = """
@startuml
!theme toy
skinparam backgroundColor transparent

agent Candidate
agent Recruiter

rectangle "SmartRecruit System" {
    usecase "1.0 Profile Parsing" as P1
    usecase "2.0 Assessment Gen" as P2
    usecase "3.0 Code Eval" as P3
    usecase "4.0 Analytics" as P4
    
    database "Candidate DB" as DB1
    database "Question Bank" as DB2
}

Candidate --> P1 : Upload CV
P1 --> DB1 : Save Parsed Skills
DB1 --> P2 : Retrieve Domain Exp
DB2 --> P2 : Fetch Qs
P2 --> Candidate : Provide Test
Candidate --> P3 : Submit Code
P3 --> DB1 : Update Score
DB1 --> P4 : Aggregate Data
P4 --> Recruiter : Dashboards
@enduml
"""

# 3. DFD Level 2 (Detailed Assessment)
dfd_2 = """
@startuml
!theme toy
skinparam backgroundColor transparent

agent Candidate
usecase "3.1 Submit Code" as P31
usecase "3.2 Piston API" as P32
usecase "3.3 Result Parse" as P33
usecase "3.4 Calc Score" as P34
database "Candidate DB" as DB1

Candidate --> P31 : Raw Snippet
P31 --> P32 : Payload Const
P32 --> P33 : Output Logs
P33 --> P34 : Metrics (Time/Mem)
P34 --> DB1 : Save Interview Result
@enduml
"""

# 4. Use Case
use_case = """
@startuml
!theme toy
left to right direction
skinparam backgroundColor transparent

actor Candidate
actor Recruiter
actor "AI Agent\\n(Gemini/n8n)" as AI

rectangle "SmartRecruit" {
  usecase "Upload CV" as UC1
  usecase "Semantic Parse" as UC2
  usecase "View Dashboard" as UC3
  usecase "Execute Test" as UC4
  
  usecase "Review Profiles" as UC5
  usecase "Override Status" as UC6
  usecase "Monitor Analytics" as UC7
  usecase "Generate Reports" as UC8
}

Candidate --> UC1
UC1 .> UC2 : <<include>>
Candidate --> UC3
Candidate --> UC4

Recruiter --> UC5
Recruiter --> UC6
Recruiter --> UC7
Recruiter --> UC8

AI --> UC2
AI --> UC8
@enduml
"""

# 5. Activity Flow (A, B, C)
activity_flow = """
@startuml
!theme plain
skinparam backgroundColor transparent

|Candidate|
start
:Register & Upload CV;
|AI Engine|
:Parse CV (Gemini);
if (Match > 60%?) then (yes)
  :Auto-Shortlist;
else (no)
  |Recruiter|
  :Manual Review;
  if (Approve?) then (yes)
  else (no)
    :Reject;
    stop
  endif
endif

|Candidate|
:Open Assessment;
:Type Code in IDE;
:Submit to Sandbox;

|Piston API|
:Execute Sandbox;

|System Backend|
if (Exit == 0 & Correct?) then (yes)
  :Status = Pass;
else (no)
  :Status = Fail;
endif
:Trigger n8n Alert;

|Recruiter|
if (Select Candidate?) then (yes)
  :Click 'Selected';
  |System Backend|
  :Gen PDF Report;
  :Webhook via Twilio;
  :Dispatch Offer Email;
else (no)
endif
stop
@enduml
"""

# 6. Class Diagram
class_diagram = """
@startuml
!theme plain
skinparam backgroundColor transparent

class Candidate {
  +id: UUID
  +name: String
  +domain: String
  +experience: Int
  +upload_cv()
  +view_dashboard()
}

class QuestionBank {
  +id: UUID
  +difficulty: String
  +text: String
  +expected_output: String
  +get_questions()
}

class Interview {
  +score: Float
  +code: String
  +timestamp: DateTime
  +calculate_score()
}

class SentimentLog {
  +id: UUID
  +raw_text: String
  +score: Float
  +flag: Boolean
  +log_sentiment()
}

Candidate "1" -- "0..*" Interview : takes >
Interview "0..*" -- "1" QuestionBank : includes >
Candidate "1" -- "0..*" SentimentLog : has >

@enduml
"""

# 7. Sequence Diagram
sequence_diagram = """
@startuml
!theme plain
skinparam backgroundColor transparent

actor Candidate
participant UI
participant Backend
participant "Piston API" as Piston
database DB

Candidate -> UI: Submit Code()
UI -> Backend: POST Code Payload
Backend -> Piston: Exec JSON
Piston --> Backend: Output (stdout, exit_code)
Backend -> DB: Save Interview Results
Backend -> UI: Display Result
UI --> Candidate: Feedback Update
@enduml
"""

diagrams = {
    "dfd_level_0.png": dfd_0,
    "dfd_level_1.png": dfd_1,
    "dfd_level_2.png": dfd_2,
    "use_case.png": use_case,
    "activity_flow.png": activity_flow,
    "class_diagram.png": class_diagram,
    "sequence_diagram.png": sequence_diagram
}

for filename, text in diagrams.items():
    generate_png(text, filename)

print("Diagram generation completed.")
