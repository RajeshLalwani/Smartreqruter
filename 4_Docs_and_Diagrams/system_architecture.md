# System Architecture

## High-Level Overview

```mermaid
graph TD
    subgraph "Frontend Layer (Django Templates)"
        A[Candidate UI]
        B[Recruiter Dashboard]
    end

    subgraph "Application Layer (Django)"
        C[Core App (Auth)]
        D[Jobs App (Logic)]
        E[Views & Forms]
        F[Utils / Helpers]
    end

    subgraph "AI Processing Layer (Python Modules)"
        G[Resume Parser (SpaCy/PyPDF)]
        H[Interview Bot (NLP/Logic)]
        I[Proctoring System (JS/OpenCV)]
    end

    subgraph "Data Layer"
        J[(Database - SQLite/Postgres)]
        K[Media Storage (Resumes/Profiles)]
    end

    %% Interactions
    A -->|HTTP Requests| E
    B -->|HTTP Requests| E
    E -->|Auth Checks| C
    E -->|Business Logic| D
    
    %% AI Integrations
    D -->|Import & Call| G
    D -->|Import & Call| H
    A -->|Client-Side Monitoring| I
    
    %% Data Access
    D -->|ORM Queries| J
    D -->|File I/O| K
    C -->|ORM Queries| J

    %% Styling
    classDef frontend fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef app fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef ai fill:#fff3e0,stroke:#ef6c00,stroke-width:2px;
    classDef data fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;

    class A,B frontend;
    class C,D,E,F app;
    class G,H,I ai;
    class J,K data;
```
