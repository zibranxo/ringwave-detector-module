# Diagrams

**Project:** FaceGate Attendance  
**Prepared for:** Internal product and engineering team  
**Prepared on:** 2026-06-04  
**Document status:** Draft for implementation planning

---

## 1. High-level system architecture

```mermaid
flowchart TB
    Student[Student / Attendee] --> Tablet[Android Tablet App]
    Admin[Admin] --> Tablet

    subgraph Tablet[Android Tablet App - Offline First]
        Kiosk[Kiosk Attendance UI]
        AdminUI[Admin UI]
        Camera[CameraX Front Camera]
        Detector[On-device Face Detection]
        Quality[Face Quality Checks]
        Embedder[On-device Embedding Model]
        Matcher[Local Matching Engine]
        Attendance[Attendance Rules Engine]
        Conflicts[Conflict Engine]
        Reports[Report and Export Engine]
        Security[Security and Encryption Engine]
        DB[(Encrypted Local Database)]
    end

    Kiosk --> Camera
    Camera --> Detector
    Detector --> Quality
    Quality --> Embedder
    Embedder --> Matcher
    Matcher --> Attendance
    Matcher --> Conflicts
    Attendance --> DB
    Conflicts --> DB
    AdminUI --> DB
    AdminUI --> Reports
    Reports --> Export[Excel Export File]
    Security --> DB
```

---

## 2. Attendance scanning flow

```mermaid
flowchart TD
    A[Open kiosk screen] --> B[Start front camera]
    B --> C[Show oval guide]
    C --> D[Analyze frame]
    D --> E{{Face detected?}}
    E -- No --> E1[Red/neutral prompt: Place face inside oval]
    E1 --> D
    E -- Yes --> F{{Exactly one face?}}
    F -- No --> F1[Red prompt: Only one face at a time]
    F1 --> D
    F -- Yes --> G{{Frame quality OK?}}
    G -- No --> G1[Red prompt: Hold still / improve light / look straight]
    G1 --> D
    G -- Yes --> H[Auto-capture best frame]
    H --> I[Generate embedding on device]
    I --> J[Compare with local encrypted templates]
    J --> K{{High confidence and unambiguous?}}
    K -- Yes --> L{{Already marked today?}}
    L -- No --> M[Write attendance record]
    M --> N[Green oval + success sound + name]
    L -- Yes --> O[Green oval + already marked + name]
    N --> P[Return to scanning]
    O --> P
    K -- Low confidence --> Q[Red prompt: Try again]
    Q --> R[Log recognition attempt]
    R --> D
    K -- Ambiguous --> S[Create conflict case]
    S --> T[Red prompt: Admin review needed]
    T --> D
```

---

## 3. Enrollment flow

```mermaid
flowchart TD
    A[Admin opens student profile] --> B{{Enrollment method}}
    B -- Camera --> C[Guide admin through multiple sample captures]
    C --> D[Quality check each sample]
    D --> E{{All required samples accepted?}}
    E -- No --> C
    E -- Yes --> F[Generate embeddings]
    B -- Passport image --> G[Select image file]
    G --> H[Validate single clear frontal face]
    H --> I{{Image accepted?}}
    I -- No --> G
    I -- Yes --> F
    F --> J[Compare against existing templates]
    J --> K{{Duplicate risk?}}
    K -- Yes --> L[Warn admin and require confirmation]
    L --> M{{Admin confirms?}}
    M -- No --> N[Cancel enrollment]
    M -- Yes --> O[Save encrypted templates]
    K -- No --> O
    O --> P[Deactivate old templates if replacing]
    P --> Q[Write audit log]
    Q --> R[Student marked as enrolled]
```

---

## 4. Matching decision tree

```mermaid
flowchart TD
    A[Probe embedding generated] --> B[Calculate similarity against active templates]
    B --> C[Group scores by student]
    C --> D[Select best and second-best students]
    D --> E{{Best score >= acceptance threshold?}}
    E -- No --> F[Reject / retry]
    E -- Yes --> G{{Best-second margin >= ambiguity margin?}}
    G -- No --> H[Create ambiguous-match conflict]
    G -- Yes --> I{{Student already marked today?}}
    I -- Yes --> J[Show already marked, no duplicate]
    I -- No --> K[Auto-mark present]
```

---

## 5. Admin information architecture

```mermaid
flowchart TD
    A[Admin Login] --> B[Dashboard]
    B --> C[Students]
    B --> D[Attendance]
    B --> E[Conflicts]
    B --> F[Holidays]
    B --> G[Import / Export]
    B --> H[Audit Logs]
    B --> I[Settings]
    B --> J[Diagnostics]

    C --> C1[Student List]
    C --> C2[Student Profile]
    C2 --> C3[Enroll / Update Face]
    C2 --> C4[Attendance History]

    D --> D1[Today]
    D --> D2[Date Range Report]
    D --> D3[Manual Edit]

    E --> E1[Open Conflicts]
    E --> E2[Resolve Conflict]

    F --> F1[Holiday List]
    F --> F2[Add / Edit Holiday]

    G --> G1[Import Roster]
    G --> G2[Export Attendance]
    G --> G3[Export History]

    I --> I1[Attendance Mode]
    I --> I2[Matching Thresholds]
    I --> I3[Kiosk Settings]
    I --> I4[Security Settings]
```

---

## 6. Database ERD

```mermaid
erDiagram
    STUDENTS ||--o{{ FACE_TEMPLATES : has
    STUDENTS ||--o{{ ATTENDANCE_RECORDS : receives
    STUDENTS ||--o{{ CONFLICT_CASES : may_resolve_to
    ATTENDANCE_RECORDS ||--o{{ AUDIT_LOGS : changes_logged_by
    ADMINS ||--o{{ AUDIT_LOGS : performs
    ADMINS ||--o{{ HOLIDAYS : creates
    RECOGNITION_ATTEMPTS ||--o{{ CONFLICT_CASES : creates
    FACE_TEMPLATES ||--o{{ ATTENDANCE_RECORDS : matched_by
    IMPORT_JOBS ||--o{{ AUDIT_LOGS : logged_by
    EXPORT_JOBS ||--o{{ AUDIT_LOGS : logged_by

    STUDENTS {
        string id PK
        string external_student_id
        string full_name
        string group_name
        boolean is_active
        string enrollment_status
        datetime created_at
        datetime updated_at
    }

    FACE_TEMPLATES {
        string id PK
        string student_id FK
        string model_name
        string model_version
        int embedding_dimension
        blob encrypted_embedding
        float quality_score
        string source_type
        boolean is_active
        datetime created_at
    }

    ATTENDANCE_RECORDS {
        string id PK
        string student_id FK
        string attendance_date
        string status
        string source
        float match_score
        string matched_template_id FK
        datetime first_marked_at
        string device_id
    }

    RECOGNITION_ATTEMPTS {
        string id PK
        datetime attempted_at
        string result_type
        string best_student_id
        float best_score
        string second_student_id
        float second_score
        string failure_reason
    }

    CONFLICT_CASES {
        string id PK
        string recognition_attempt_id FK
        string conflict_type
        string status
        string candidate_student_ids
        string resolved_student_id
        string resolved_by_admin_id
        datetime resolved_at
    }

    ADMINS {
        string id PK
        string username
        string password_hash
        string password_salt
        boolean is_active
        datetime last_login_at
    }

    AUDIT_LOGS {
        string id PK
        string admin_id FK
        string action_type
        string entity_type
        string entity_id
        string before_value
        string after_value
        string reason
        datetime created_at
    }

    HOLIDAYS {
        string id PK
        string holiday_date
        string title
        string notes
        string created_by_admin_id FK
    }

    IMPORT_JOBS {
        string id PK
        string file_name
        string import_type
        string status
        int total_rows
        int success_rows
        int failed_rows
    }

    EXPORT_JOBS {
        string id PK
        string export_type
        string date_from
        string date_to
        string file_uri
        string status
    }
```

---

## 7. Conflict lifecycle

```mermaid
stateDiagram-v2
    [*] --> Open
    Open --> Resolved: Admin selects student / marks attendance
    Open --> Dismissed: Admin dismisses failed scan
    Open --> ReEnrollmentRequested: Admin chooses re-enroll
    ReEnrollmentRequested --> Resolved: New template saved and attendance marked
    ReEnrollmentRequested --> Open: Re-enrollment cancelled
    Resolved --> [*]
    Dismissed --> [*]
```

---

## 8. Export generation flow

```mermaid
flowchart TD
    A[Admin selects date range] --> B[Validate date range]
    B --> C[Load active students]
    C --> D[Load attendance records]
    D --> E[Load holidays]
    E --> F[Load manual edits and audit logs]
    F --> G[Load conflict records]
    G --> H[Generate workbook sheets]
    H --> I[Summary]
    H --> J[Attendance Matrix]
    H --> K[Daily Logs]
    H --> L[Students]
    H --> M[Manual Edits and Audit]
    H --> N[Holidays]
    H --> O[Conflicts]
    I --> P[Write XLSX file]
    J --> P
    K --> P
    L --> P
    M --> P
    N --> P
    O --> P
    P --> Q[Create export job record]
    Q --> R[Write audit log]
    R --> S[Show Save / Share options]
```

---

## 9. Security boundary diagram

```mermaid
flowchart TB
    subgraph PublicStudentArea[Student-accessible kiosk area]
        Kiosk[Kiosk Attendance Screen]
        Camera[Camera Preview]
    end

    subgraph AdminProtectedArea[Password-protected admin area]
        Dashboard[Admin Dashboard]
        Students[Student Management]
        Reports[Reports and Export]
        Settings[Settings]
        Audit[Audit Logs]
    end

    subgraph SecureStorage[Encrypted local storage]
        DB[(Encrypted Database)]
        Keys[Android Keystore Protected Keys]
        Templates[Encrypted Face Embeddings]
    end

    Kiosk -->|Recognition only| Templates
    Kiosk -->|Writes attendance transaction| DB
    Dashboard --> DB
    Students --> DB
    Reports --> DB
    Settings --> DB
    Audit --> DB
    Keys --> DB
    Keys --> Templates

    Kiosk -. No direct access .-> AdminProtectedArea
```

---

## 10. Kiosk mode operational diagram

```mermaid
flowchart TD
    A[Device boots or app opens] --> B[App launches]
    B --> C[Kiosk Attendance Screen]
    C --> D{{Admin entry requested?}}
    D -- No --> C
    D -- Yes --> E[Admin login]
    E --> F{{Password valid?}}
    F -- No --> C
    F -- Yes --> G[Admin dashboard]
    G --> H{{Admin exits admin mode?}}
    H -- Yes --> C
    H -- No --> G
    C --> I{{App backgrounded/restarted?}}
    I -- Yes --> B
    I -- No --> C
```
