import os
import subprocess

def generate_mermaid(mermaid_text, filename):
    with open("temp.mmd", "w", encoding="utf-8") as f:
        f.write(mermaid_text)
    
    cmd = f'cmd.exe /c "npx mmdc -i temp.mmd -o {filename} -b transparent"'
    print(f"Generating {filename}...")
    try:
        subprocess.run(cmd, check=True, shell=True)
        print(f"Successfully generated {filename}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to generate {filename}: {e}")

# 1. DFD Level 0 (using flowchart)
dfd_0 = """
flowchart LR
    C[Candidate]
    R[Recruiter]
    S((SmartRecruit\\nSystem))
    N[Notification API]

    C -->|Resumes, Action| S
    R -->|Evaluation Rules| S
    S -->|Status Updates| C
    S -->|Analytical Reports| R
    S -->|Trigger SMS/Email| N
"""

# 2. DFD Level 1
dfd_1 = """
flowchart TD
    C[Candidate]
    R[Recruiter]
    
    subgraph SmartRecruit
        P1(1.0 Profile Parsing)
        P2(2.0 Assessment Gen)
        P3(3.0 Code Eval)
        P4(4.0 Analytics)
        DB1[(Candidate DB)]
        DB2[(Question Bank)]
    end
    
    C -->|Upload CV| P1
    P1 -->|Save Parsed Skills| DB1
    DB1 -->|Retrieve Domain Exp| P2
    DB2 -->|Fetch Qs| P2
    P2 -->|Provide Test| C
    C -->|Submit Code| P3
    P3 -->|Update Score| DB1
    DB1 -->|Aggregate Data| P4
    P4 -->|Dashboards| R
"""

# 3. DFD Level 2
dfd_2 = """
flowchart TD
    C[Candidate]
    DB1[(Candidate DB)]
    
    subgraph 3.0 Code Evaluation
        P31(3.1 Submit Code)
        P32(3.2 Piston API)
        P33(3.3 Result Parse)
        P34(3.4 Calc Score)
    end
    
    C -->|Raw Snippet| P31
    P31 -->|Payload Const| P32
    P32 -->|Output Logs| P33
    P33 -->|Metrics Time/Mem| P34
    P34 -->|Save Interview Result| DB1
"""

# 4. Use Case
use_case = """
flowchart LR
    C((Candidate))
    R((Recruiter))
    A((AI Agent))
    
    subgraph SmartRecruit
        UC1([Upload CV])
        UC2([Semantic Parse])
        UC3([View Dashboard])
        UC4([Execute Test])
        
        UC5([Review Profiles])
        UC6([Override Status])
        UC7([Monitor Analytics])
        UC8([Generate Reports])
    end
    
    C --- UC1
    UC1 -.->|includes| UC2
    C --- UC3
    C --- UC4
    
    R --- UC5
    R --- UC6
    R --- UC7
    R --- UC8
    
    A --- UC2
    A --- UC8
"""

# 5. Activity Flow
activity_flow = """
flowchart TD
    Start((Start)) --> Reg[Register & Upload CV]
    Reg --> Parse{AI Engine: Match > 60%?}
    Parse -->|Yes| AutoShort[Auto-Shortlist]
    Parse -->|No| Manual[Recruiter: Manual Review]
    Manual --> Appr{Approve?}
    Appr -->|Yes| AutoShort
    Appr -->|No| Reject[Reject] --> Stop((Stop))
    
    AutoShort --> Open[Open Assessment]
    Open --> Type[Type Code in IDE]
    Type --> Submit[Submit to Sandbox]
    Submit --> API[Piston API Execute]
    API --> SystemCheck{Exit == 0 & Correct?}
    SystemCheck -->|Yes| Pass[Status = Pass]
    SystemCheck -->|No| Fail[Status = Fail]
    
    Pass --> Alert[Trigger n8n Alert]
    Fail --> Alert
    
    Alert --> Select{Select Candidate?}
    Select -->|Yes| GenPDF[Gen PDF Report]
    GenPDF --> Webhook[Webhook via Twilio]
    Webhook --> Email[Dispatch Offer Email] --> End((End))
    Select -->|No| End
"""

# 6. Class Diagram
class_diagram = """
classDiagram
    class Candidate {
        +UUID id
        +String name
        +String domain
        +Int experience
        +upload_cv()
        +view_dashboard()
    }
    class QuestionBank {
        +UUID id
        +String difficulty
        +String text
        +String expected_output
        +get_questions()
    }
    class Interview {
        +Float score
        +String code
        +DateTime timestamp
        +calculate_score()
    }
    class SentimentLog {
        +UUID id
        +String raw_text
        +Float score
        +Boolean flag
        +log_sentiment()
    }
    
    Candidate "1" -- "0..*" Interview : takes
    Interview "0..*" -- "1" QuestionBank : includes
    Candidate "1" -- "0..*" SentimentLog : has
"""

# 7. Sequence Diagram
sequence_diagram = """
sequenceDiagram
    actor C as Candidate
    participant UI as SmartRecruit UI
    participant BE as Django Backend
    participant P as Piston API
    participant DB as PostgreSQL DB
    
    C->>UI: Submit Code()
    UI->>BE: POST Code Payload
    BE->>P: Execute JSON
    P-->>BE: Output (stdout, exit_code)
    BE->>DB: Save Interview Results
    BE-->>UI: Display Result
    UI-->>C: Feedback Update
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

os.chdir(r"C:\Users\ASUS\Documents\Tech Elecon Pvt. Ltd\Project\SmartRecruit\4_Docs_and_Diagrams")
for filename, text in diagrams.items():
    generate_mermaid(text, filename)

if os.path.exists("temp.mmd"):
    os.remove("temp.mmd")
print("Done!")
