import os
import urllib.request
import time

diagrams_dir = r'C:\Users\ASUS\Documents\Tech Elecon Pvt. Ltd\Project\SmartRecruit\4_Docs_and_Diagrams\Diagrams'
os.makedirs(diagrams_dir, exist_ok=True)
os.chdir(diagrams_dir)

print('Downloading plantuml-1.2024.3.jar...')
jar_url = 'https://github.com/plantuml/plantuml/releases/download/v1.2024.3/plantuml-1.2024.3.jar'
if not os.path.exists('plantuml.jar'):
    urllib.request.urlretrieve(jar_url, 'plantuml.jar')
print('Downloaded.')

usecase = """@startuml
skinparam backgroundColor white
skinparam usecase {
    BackgroundColor white
    BorderColor black
}
skinparam actor {
    BackgroundColor white
    BorderColor black
}
left to right direction
actor "Candidate" as C
actor "Recruiter" as R
actor "Admin" as A

rectangle "SmartRecruit AI Platform" {
    usecase "Register / Login" as UC1
    usecase "Manage Profile" as UC2
    usecase "Browse Jobs" as UC3
    usecase "Apply / Submit Resume" as UC4
    usecase "Take AI Prep / Interview" as UC5
    usecase "Post Requisitions" as UC6
    usecase "Review AI Ranked Candidates" as UC7
    usecase "Schedule Interviews" as UC8
    usecase "Manage Users & Data" as UC9
}

C --> UC1
C --> UC2
C --> UC3
C --> UC4
C --> UC5

R --> UC1
R --> UC2
R --> UC6
R --> UC7
R --> UC8

A --> UC1
A --> UC9
@enduml"""

dfd0 = """@startuml
skinparam backgroundColor white
skinparam rectangle {
    BackgroundColor white
    BorderColor black
}
skinparam circle {
    BackgroundColor white
    BorderColor black
}
rectangle "Candidate" as Can
rectangle "Recruiter" as Rec
rectangle "Admin" as Adm

circle "SmartRecruit System" as Sys

Can --> Sys : Resume, Application, Answers
Sys --> Can : Job Matches, AI Feedback
Rec --> Sys : Job Posts, Feedback
Sys --> Rec : Ranked Applications
Adm --> Sys : Settings, Approvals
Sys --> Adm : Reports
@enduml"""

dfd1 = """@startuml
skinparam backgroundColor white
skinparam rectangle {
    BackgroundColor white
    BorderColor black
}
skinparam node {
    BackgroundColor white
    BorderColor black
}
skinparam storage {
    BackgroundColor white
    BorderColor black
    Shape folder
}

rectangle "Candidate" as C
rectangle "Recruiter" as R

node "1.0\\nUser Management" as P1
node "2.0\\nJob Matching" as P2
node "3.0\\nAI Resume Parser" as P3
node "4.0\\nInterview Analysis" as P4

storage "User DB" as D1
storage "Job DB" as D2
storage "Application DB" as D3

C --> P1 : Credentials
P1 --> D1 : Store User
C --> P2 : Search Filters
P2 <-- D2 : Return Listings
C --> P3 : Upload Resume
P3 --> D3 : Store Parsed Data
R --> P2 : Post Job
P2 --> D2 : Save Job
R <-- D3 : View Rankings
C --> P4 : Session Video/Audio
P4 --> D3 : Save Score
@enduml"""

dfd2 = """@startuml
skinparam backgroundColor white
skinparam rectangle {
    BackgroundColor white
    BorderColor black
}
skinparam node {
    BackgroundColor white
    BorderColor black
}
skinparam storage {
    BackgroundColor white
    BorderColor black
}

rectangle "Candidate" as C
node "3.1\\nExtract Text from PDF" as 31
node "3.2\\nAnalyze Skills (RAG)" as 32
node "3.3\\nCalculate Matrix Score" as 33
storage "Resume File DB" as D3a
storage "Parsed Skills DB" as D3b

C --> 31 : Upload CV
31 --> D3a : Save PDF
31 --> 32 : Raw Text
32 --> 33 : Semantic Vector
33 --> D3b : Save Final Score
@enduml"""

er = """@startuml
skinparam backgroundColor white
skinparam class {
    BackgroundColor white
    BorderColor black
}
entity "User" as U {
  * id : UUID
  --
  name : String
  email : String
  role : Enum(Candidate, Recruiter, Admin)
}
entity "Job" as J {
  * id : UUID
  --
  title : String
  description : Text
  recruiter_id : UUID
}
entity "Application" as A {
  * id : UUID
  --
  candidate_id : UUID
  job_id : UUID
  ai_score : Float
}

U ||--o{ J : posts
U ||--o{ A : submits
J ||--o{ A : receives
@enduml"""

seq = """@startuml
skinparam backgroundColor white
skinparam participant {
    BackgroundColor white
    BorderColor black
}
actor Candidate
participant "Frontend" as F
participant "AI Controller" as C
participant "Resume Parser" as R
database "PostgreSQL" as DB

Candidate -> F : Upload Resume
F -> C : POST /upload/
C -> R : Extract text & skills
R --> C : Parsed JSON
C -> DB : Save Candidate Profile
DB --> C : Status 200
C --> F : Application Successful
F --> Candidate : Show Success Dialog
@enduml"""

activity = """@startuml
skinparam backgroundColor white
skinparam activity {
    BackgroundColor white
    BorderColor black
}
start
:Candidate logs in;
:Search for Jobs;
if (Job matched?) then (yes)
  :Click Apply;
  :Upload Resume;
  :System Parses Resume;
  if (Score > Threshold?) then (High)
    :Ranked Top Tier;
  else (Low)
    :Ranked Standard;
  endif
  :Application Saved;
else (no)
  :Refine Filters;
endif
stop
@enduml"""

cls = """@startuml
skinparam backgroundColor white
skinparam class {
    BackgroundColor white
    BorderColor black
}
class Candidate {
  +resumeUrl : String
  +skills : List
  +applyForJob(jobId)
}
class Recruiter {
  +company : String
  +postJob(details)
}
class User {
  +id : Integer
  +email : String
  +login()
}
class Job {
  +title : String
  +analyzeMatch()
}

User <|-- Candidate
User <|-- Recruiter
Recruiter "1" *-- "*" Job : creates
Candidate "*" -- "*" Job : applies
@enduml"""

files = {
    'UseCase.puml': usecase,
    'DFD0.puml': dfd0,
    'DFD1.puml': dfd1,
    'DFD2.puml': dfd2,
    'ER.puml': er,
    'Sequence.puml': seq,
    'Activity.puml': activity,
    'Class.puml': cls
}

for name, content in files.items():
    with open(name, 'w', encoding='utf-8') as f:
        f.write(content)
        
print('PlantUML scripts saved. Now running PlantUML generation...')
os.system('java -jar plantuml.jar -tpng *.puml')
print('PlantUML generation complete.')
