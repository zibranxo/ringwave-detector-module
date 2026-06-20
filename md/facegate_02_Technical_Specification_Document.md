# Technical Specification Document

**Project:** FaceGate Attendance  
**Prepared for:** Internal engineering team  
**Prepared on:** 2026-06-04  
**Document status:** Draft for implementation planning

---

## 1. Technical objective

Build a standalone Android tablet application that performs face-based attendance fully on-device. The application must detect a face through the front camera, generate a face embedding, compare it against locally stored encrypted embeddings, mark daily attendance automatically when confidence is sufficient, and provide a complete admin mode for enrollment, reports, holidays, conflict resolution, manual edits, exports, and audit logs.

The app must not depend on internet connectivity or a remote backend. All recognition, storage, admin workflows, and export generation must run locally on the device.

---

## 2. Recommended architecture summary

### 2.1 Preferred architecture

Use a native Android architecture:

| Layer | Recommended choice |
|---|---|
| Platform | Android tablet, Android phone compatible |
| Language | Kotlin |
| UI | Jetpack Compose |
| Camera | CameraX Preview + ImageAnalysis |
| Face detection | On-device detector such as ML Kit Face Detection or equivalent local detector |
| Embedding runtime | LiteRT / TensorFlow Lite runtime or equivalent on-device inference runtime |
| Recognition model | Mobile-optimized face embedding model, selected after benchmark and licensing review |
| Local database | Room over encrypted SQLite / SQLCipher-compatible storage |
| Key management | Android Keystore-backed encryption keys |
| File import/export | XLSX and CSV support through local file picker / Android Storage Access Framework |
| Kiosk | Android Lock Task Mode where device-owner provisioning is possible; fallback in-app kiosk guard otherwise |
| Logging | Local structured logs with admin-accessible diagnostics and audit logs |

### 2.2 Why this architecture

The main requirement is full offline operation. A server-side stack such as FastAPI + Milvus + MinIO, as used by ZepIris, is useful for cloud/server deployments but not ideal as the primary architecture for this app because the tablet must perform matching without internet or LAN dependency. For more than 100 students, local embedding comparison is technically feasible and simpler than operating a local vector database.

---

## 3. ZepIris evaluation

The provided ZepIris repository is a strong reference implementation for a face-authentication pipeline. It includes face embeddings, vector search, CRUD operations, image quality checks, and a production-shaped microservice design. However, its default architecture uses server-side services, Milvus, MinIO, and FastAPI endpoints. This conflicts with the hard requirement that the school-camp product must perform full face matching on-device for weeks without internet.

### 3.1 Recommended use of ZepIris

Use ZepIris as a reference for:

1. Recognition pipeline structure.
2. Quality checks before enrollment and matching.
3. Similarity thresholds and top-k candidate handling.
4. Embedding-based identity matching.
5. Conflict patterns such as low-quality image, ambiguous match, and duplicate enrollment.
6. Optional future server-side edition if the product later supports multi-device sync.

### 3.2 Not recommended for first release

Do not directly require ZepIris server services in the first release because:

1. The app must work fully offline.
2. Deploying Milvus and MinIO on a school tablet is operationally inappropriate.
3. The expected local dataset size does not require a dedicated vector database.
4. The admin and attendance workflows are standalone.

### 3.3 Adaptation option

If the engineering team wants to reuse ideas from ZepIris, the correct direction is to port the recognition model and quality-check logic to mobile inference, not to embed the full server stack into the tablet app.

---

## 4. System components

### 4.1 Android app modules

| Module | Responsibility |
|---|---|
| Kiosk UI Module | Student attendance screen, camera preview, oval guide, green/red status, sound feedback |
| Admin UI Module | Login, dashboard, students, enrollment, holidays, reports, conflicts, settings, audit logs |
| Camera Pipeline | Camera lifecycle, preview, frame analysis, auto-capture, manual capture |
| Face Quality Engine | Single-face validation, blur, brightness, pose, face size, occlusion/glasses tolerance |
| Face Detection Engine | Detects face bounding box and landmarks/alignment inputs |
| Embedding Engine | Converts aligned face crop into normalized embedding vector |
| Matching Engine | Compares probe embedding against active student templates |
| Attendance Engine | Applies daily attendance rules and writes records transactionally |
| Enrollment Engine | Captures/imports reference images, validates quality, creates templates |
| Conflict Engine | Creates and resolves low-confidence, ambiguous, and duplicate-risk cases |
| Report Engine | Builds attendance matrix, daily logs, summary, audit, holiday, and conflict exports |
| Import Engine | Parses roster XLSX/CSV and validates required columns |
| Security Engine | Encryption, password hashing, session timeout, app lock, export authorization |
| Audit Engine | Records admin changes and sensitive actions |
| Settings Engine | Local configurable thresholds, device settings, attendance mode toggles |
| Diagnostics Engine | Model version, performance stats, camera status, database health |

---

## 5. Runtime flow

### 5.1 Attendance marking flow

1. Open kiosk screen.
2. Initialize CameraX front camera.
3. Process preview frames at a throttled interval to avoid CPU saturation.
4. Detect face.
5. Validate frame quality.
6. If one good face is detected, auto-capture the best frame.
7. Align and crop face.
8. Generate embedding on-device.
9. Retrieve active encrypted face templates from local database cache.
10. Compute cosine similarity against templates.
11. Select best candidate and second-best candidate.
12. Evaluate thresholds:
    - acceptance threshold;
    - rejection threshold;
    - ambiguity margin;
    - same-day duplicate rule.
13. If accepted, write attendance record in a database transaction.
14. Show green oval, play success sound, display student name.
15. If rejected or ambiguous, show red oval and route to retry or conflict queue.

### 5.2 Enrollment flow

1. Admin opens student profile.
2. Admin selects “Enroll face” or “Update face”.
3. App displays enrollment camera screen.
4. App captures recommended multiple samples:
    - straight face;
    - slight left;
    - slight right;
    - slight up/down or glasses-on variation;
    - automatically selected best neutral sample.
5. Each sample is quality checked.
6. Embeddings are generated.
7. New embeddings are compared against existing students to detect duplicate-risk.
8. Admin is warned if duplicate-risk exists.
9. On save, old templates can be deactivated and new templates stored.
10. Audit log records enrollment or update.

### 5.3 Passport-image enrollment flow

1. Admin imports roster and image or selects image on student profile.
2. App validates that the image contains exactly one clear frontal face.
3. App generates one embedding.
4. App checks duplicate-risk.
5. App stores template if accepted.
6. Admin can later improve the template by capturing multiple samples in the app.

---

## 6. Performance strategy

### 6.1 Target budget

| Operation | Target |
|---|---|
| Face detection on preview frame | 50-150 ms on target device |
| Quality checks | 20-100 ms |
| Face crop and alignment | 10-50 ms |
| Embedding inference | 100-500 ms depending on model/device |
| Local matching for 100-500 students | 5-100 ms |
| End-to-end usable-frame to result | Less than 1 second |

### 6.2 Optimizations

1. Use CameraX ImageAnalysis with backpressure strategy `KEEP_ONLY_LATEST`.
2. Process detection at a controlled frame rate, for example 5-10 analyzed frames per second.
3. Use minimum viable resolution for face detection, then capture or crop sufficient resolution for embedding.
4. Keep active embeddings decrypted only in memory while app is unlocked and protected.
5. Store normalized embeddings to make cosine similarity a dot product.
6. Use vectorized Kotlin/NDK operations if matching becomes slow.
7. Use FP16 or INT8 model where accuracy remains acceptable.
8. Preload model during app startup.
9. Warm up model with a dummy inference after camera initialization.
10. Avoid blocking the UI thread; run ML and DB work on dedicated dispatchers.
11. Use a short cooldown after a successful mark to avoid duplicate scans.

### 6.3 Dataset-size strategy

For the target size of greater than 100 students, linear scan over all active templates is acceptable. If the product later grows above several thousand templates on the same device, add an approximate nearest-neighbor index or optimized native vector search.

---

## 7. Matching logic

### 7.1 Embedding representation

Each face template stores a normalized vector. Expected dimension depends on chosen model, commonly 128, 192, 256, or 512 dimensions. The implementation must not hard-code one dimension outside the model configuration.

Recommended template metadata:

1. Model name.
2. Model version.
3. Embedding dimension.
4. Normalization method.
5. Quality score.
6. Enrollment source.
7. Capture timestamp.

### 7.2 Score calculation

Use cosine similarity:

```text
similarity = dot(normalized_probe_embedding, normalized_template_embedding)
```

For a student with multiple templates, compute either:

1. maximum similarity across that student’s active templates; or
2. average of top-N similarities; or
3. centroid embedding plus individual-template fallback.

Initial recommendation: use maximum similarity per student and retain the actual matched template for audit/debug.

### 7.3 Decision thresholds

The following are names, not final numeric values. Final values must be calibrated on real device and sample student images.

| Setting | Purpose |
|---|---|
| `acceptance_threshold` | Minimum score required to auto-mark attendance |
| `rejection_threshold` | Score below which the app should immediately reject |
| `ambiguity_margin` | Minimum required gap between best and second-best student |
| `duplicate_enrollment_threshold` | Score above which a new enrollment may duplicate another student |
| `quality_min_score` | Minimum image/frame quality required before embedding |

### 7.4 Decision table

| Best score | Best-second margin | Action |
|---|---|---|
| High | High | Auto-mark attendance |
| High | Low | Create ambiguous-match conflict |
| Medium | High | Ask retry; optional admin review after repeated failures |
| Low | Any | Reject and ask retry |
| Already marked | High-confidence same student | Show already marked |

---

## 8. Conflict handling

### 8.1 Conflict types

| Type | Created when | Default behavior |
|---|---|---|
| LOW_CONFIDENCE | Best match below acceptance threshold after repeated attempts | No attendance marked; admin may resolve |
| AMBIGUOUS_MATCH | Top candidates too close | No attendance marked; admin may choose student or dismiss |
| MULTIPLE_FACES | Multiple faces in frame | No conflict unless repeated; show immediate warning |
| DUPLICATE_ENROLLMENT_RISK | New template too similar to existing student | Admin must confirm or cancel enrollment |
| MANUAL_OVERRIDE | Admin edits attendance | Audit-only conflict record optional |
| TEMPLATE_QUALITY_REJECTED | Enrollment image is poor | Ask retake; not stored |

### 8.2 Conflict resolution actions

1. Mark as selected student.
2. Dismiss as failed scan.
3. Re-enroll selected student.
4. Merge duplicate student records, if duplicate roster entry exists.
5. Deactivate wrong face template.
6. Add manual attendance with reason.

Every resolution must create an audit log.

---

## 9. Attendance rules engine

### 9.1 Default mode

Default is single daily check-in. A student can have at most one active attendance record per local date.

### 9.2 Advanced mode toggle

Admin settings can include an advanced toggle for:

1. check-in/check-out;
2. multiple sessions per day.

These features should be present in architecture and schema but disabled by default to keep the first production workflow simple.

### 9.3 Holiday handling

1. Admin can create holidays by date and name.
2. Kiosk screen should show “Holiday: attendance not required” when current date is configured as holiday.
3. Admin can override and still mark attendance if an emergency setting is enabled, but default should be no attendance on holidays.
4. Exports must mark holiday dates as `H` or `Holiday`.

---

## 10. Local database schema

The schema below is implementation-facing and can be mapped to Room entities.

### 10.1 `students`

```sql
CREATE TABLE students (
    id TEXT PRIMARY KEY,
    external_student_id TEXT UNIQUE,
    full_name TEXT NOT NULL,
    group_name TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    enrollment_status TEXT NOT NULL DEFAULT 'NOT_ENROLLED',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
);
```

### 10.2 `face_templates`

```sql
CREATE TABLE face_templates (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    embedding_dimension INTEGER NOT NULL,
    encrypted_embedding BLOB NOT NULL,
    embedding_hash TEXT,
    quality_score REAL,
    source_type TEXT NOT NULL, -- CAMERA, IMAGE_IMPORT
    pose_label TEXT, -- FRONT, LEFT, RIGHT, UP_DOWN, UNKNOWN
    encrypted_thumbnail BLOB,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    deactivated_at TEXT,
    FOREIGN KEY(student_id) REFERENCES students(id)
);
```

### 10.3 `attendance_records`

```sql
CREATE TABLE attendance_records (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    student_name_snapshot TEXT NOT NULL,
    attendance_date TEXT NOT NULL,
    first_marked_at TEXT,
    status TEXT NOT NULL, -- PRESENT, ABSENT, HOLIDAY, MANUAL_PRESENT, MANUAL_ABSENT
    source TEXT NOT NULL, -- AUTO_FACE, MANUAL_ADMIN, CONFLICT_RESOLUTION, IMPORT
    match_score REAL,
    matched_template_id TEXT,
    recognition_attempt_id TEXT,
    session_type TEXT NOT NULL DEFAULT 'CHECK_IN',
    device_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id),
    UNIQUE(student_id, attendance_date, session_type)
);
```

### 10.4 `attendance_sessions`

```sql
CREATE TABLE attendance_sessions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mode TEXT NOT NULL, -- CHECK_IN_ONLY, CHECK_IN_OUT, MULTI_SESSION
    is_default INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### 10.5 `holidays`

```sql
CREATE TABLE holidays (
    id TEXT PRIMARY KEY,
    holiday_date TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    notes TEXT,
    created_by_admin_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### 10.6 `recognition_attempts`

```sql
CREATE TABLE recognition_attempts (
    id TEXT PRIMARY KEY,
    attempted_at TEXT NOT NULL,
    result_type TEXT NOT NULL, -- SUCCESS, ALREADY_MARKED, LOW_CONFIDENCE, AMBIGUOUS, MULTIPLE_FACES, QUALITY_REJECTED, NO_FACE
    best_student_id TEXT,
    best_score REAL,
    second_student_id TEXT,
    second_score REAL,
    quality_score REAL,
    failure_reason TEXT,
    device_id TEXT NOT NULL
);
```

### 10.7 `conflict_cases`

```sql
CREATE TABLE conflict_cases (
    id TEXT PRIMARY KEY,
    recognition_attempt_id TEXT,
    conflict_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN', -- OPEN, RESOLVED, DISMISSED
    candidate_student_ids TEXT, -- JSON array
    score_details TEXT, -- JSON object
    admin_resolution TEXT,
    resolved_student_id TEXT,
    resolved_by_admin_id TEXT,
    resolved_at TEXT,
    created_at TEXT NOT NULL
);
```

### 10.8 `admins`

```sql
CREATE TABLE admins (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    password_algorithm TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_login_at TEXT
);
```

### 10.9 `audit_logs`

```sql
CREATE TABLE audit_logs (
    id TEXT PRIMARY KEY,
    admin_id TEXT,
    action_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    before_value TEXT,
    after_value TEXT,
    reason TEXT,
    created_at TEXT NOT NULL,
    device_id TEXT NOT NULL
);
```

### 10.10 `app_settings`

```sql
CREATE TABLE app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    value_type TEXT NOT NULL,
    updated_by_admin_id TEXT,
    updated_at TEXT NOT NULL
);
```

### 10.11 `import_jobs`

```sql
CREATE TABLE import_jobs (
    id TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    import_type TEXT NOT NULL, -- ROSTER, ATTENDANCE_BACKFILL
    status TEXT NOT NULL, -- PENDING, SUCCESS, PARTIAL_SUCCESS, FAILED
    total_rows INTEGER,
    success_rows INTEGER,
    failed_rows INTEGER,
    error_report TEXT,
    created_by_admin_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT
);
```

### 10.12 `export_jobs`

```sql
CREATE TABLE export_jobs (
    id TEXT PRIMARY KEY,
    export_type TEXT NOT NULL,
    date_from TEXT,
    date_to TEXT,
    file_uri TEXT,
    status TEXT NOT NULL,
    created_by_admin_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT
);
```

---

## 11. Internal service/API definitions

This is a standalone mobile app, so these API definitions are intended as internal service contracts, ViewModel/use-case boundaries, or loopback-only interfaces for testing. They must not be exposed on the network in production unless a future backend is explicitly added.

### 11.1 Admin authentication

#### `POST /admin/login`

Request:

```json
{
  "username": "admin",
  "password": "********"
}
```

Response:

```json
{
  "adminId": "adm_001",
  "sessionId": "local_session_uuid",
  "expiresAt": "2026-06-04T18:30:00+05:30"
}
```

Errors:

| Code | Meaning |
|---|---|
| INVALID_CREDENTIALS | Password is incorrect |
| ADMIN_DISABLED | Admin account inactive |
| DEVICE_LOCKED | Too many failed attempts |

### 11.2 Student roster import

#### `POST /students/import`

Request:

```json
{
  "fileUri": "content://.../students.xlsx",
  "mode": "UPSERT",
  "columns": {
    "studentId": "Student ID",
    "fullName": "Name",
    "groupName": "Group"
  }
}
```

Response:

```json
{
  "importJobId": "imp_001",
  "status": "PARTIAL_SUCCESS",
  "totalRows": 125,
  "successRows": 123,
  "failedRows": 2,
  "errorReportAvailable": true
}
```

### 11.3 List students

#### `GET /students?query=&status=ACTIVE&enrollmentStatus=NOT_ENROLLED`

Response:

```json
{
  "items": [
    {
      "id": "stu_001",
      "externalStudentId": "CAMP-001",
      "fullName": "Aarav Sharma",
      "groupName": "Group A",
      "isActive": true,
      "enrollmentStatus": "ENROLLED"
    }
  ],
  "total": 1
}
```

### 11.4 Create or update student

#### `POST /students`

```json
{
  "externalStudentId": "CAMP-001",
  "fullName": "Aarav Sharma",
  "groupName": "Group A"
}
```

#### `PATCH /students/{{studentId}}`

```json
{
  "fullName": "Aarav S.",
  "groupName": "Group B",
  "isActive": true
}
```

### 11.5 Enroll face from camera session

#### `POST /students/{{studentId}}/face-templates/camera-enrollment`

Request:

```json
{
  "samples": [
    {
      "poseLabel": "FRONT",
      "imageFrameRef": "in_memory_frame_1"
    },
    {
      "poseLabel": "LEFT",
      "imageFrameRef": "in_memory_frame_2"
    }
  ],
  "replaceExisting": true
}
```

Response:

```json
{
  "studentId": "stu_001",
  "templatesCreated": 5,
  "duplicateRisk": false,
  "warnings": []
}
```

### 11.6 Enroll face from imported image

#### `POST /students/{{studentId}}/face-templates/image-import`

Request:

```json
{
  "fileUri": "content://.../student_photo.jpg",
  "replaceExisting": true
}
```

Response:

```json
{
  "studentId": "stu_001",
  "templatesCreated": 1,
  "qualityScore": 0.91,
  "duplicateRisk": false
}
```

### 11.7 Recognition scan

#### `POST /recognition/scan`

Request:

```json
{
  "frameRef": "camera_frame_latest",
  "mode": "AUTO_CAPTURE"
}
```

Response for success:

```json
{
  "resultType": "SUCCESS",
  "studentId": "stu_001",
  "studentName": "Aarav Sharma",
  "score": 0.84,
  "margin": 0.12,
  "recognitionAttemptId": "rec_001"
}
```

Response for warning:

```json
{
  "resultType": "QUALITY_REJECTED",
  "message": "Hold still.",
  "qualityDetails": {
    "blur": "HIGH",
    "brightness": "OK",
    "pose": "FRONTAL"
  }
}
```

### 11.8 Mark attendance

#### `POST /attendance/mark`

Request:

```json
{
  "studentId": "stu_001",
  "recognitionAttemptId": "rec_001",
  "source": "AUTO_FACE",
  "attendanceDate": "2026-06-04"
}
```

Response:

```json
{
  "attendanceRecordId": "att_001",
  "status": "PRESENT",
  "studentName": "Aarav Sharma",
  "markedAt": "2026-06-04T09:01:15+05:30",
  "alreadyMarked": false
}
```

### 11.9 Manual attendance edit

#### `PATCH /attendance/{{attendanceRecordId}}`

Request:

```json
{
  "status": "MANUAL_PRESENT",
  "firstMarkedAt": "2026-06-04T09:05:00+05:30",
  "reason": "Admin correction after failed recognition"
}
```

Response:

```json
{
  "attendanceRecordId": "att_001",
  "status": "MANUAL_PRESENT",
  "auditLogId": "aud_001"
}
```

### 11.10 Attendance report

#### `GET /attendance/report?from=2026-06-01&to=2026-06-30&group=Group%20A`

Response:

```json
{
  "dateFrom": "2026-06-01",
  "dateTo": "2026-06-30",
  "students": 125,
  "days": 30,
  "holidays": 2,
  "records": [
    {
      "studentId": "stu_001",
      "name": "Aarav Sharma",
      "date": "2026-06-04",
      "status": "PRESENT",
      "time": "09:01:15"
    }
  ]
}
```

### 11.11 Export attendance

#### `POST /attendance/export`

Request:

```json
{
  "dateFrom": "2026-06-01",
  "dateTo": "2026-06-30",
  "format": "XLSX",
  "includeAudit": true,
  "includeConflicts": true
}
```

Response:

```json
{
  "exportJobId": "exp_001",
  "status": "SUCCESS",
  "fileName": "attendance_2026-06-01_to_2026-06-30.xlsx",
  "fileUri": "content://.../attendance_2026-06-01_to_2026-06-30.xlsx"
}
```

### 11.12 Holidays

#### `POST /holidays`

```json
{
  "holidayDate": "2026-06-10",
  "title": "Camp Rest Day",
  "notes": "No attendance required"
}
```

#### `GET /holidays?from=2026-06-01&to=2026-06-30`

```json
{
  "items": [
    {
      "id": "hol_001",
      "holidayDate": "2026-06-10",
      "title": "Camp Rest Day"
    }
  ]
}
```

### 11.13 Conflicts

#### `GET /conflicts?status=OPEN`

```json
{
  "items": [
    {
      "id": "con_001",
      "conflictType": "AMBIGUOUS_MATCH",
      "createdAt": "2026-06-04T09:12:00+05:30",
      "candidates": [
        {"studentId": "stu_001", "name": "Aarav Sharma", "score": 0.81},
        {"studentId": "stu_002", "name": "Aryan Sharma", "score": 0.79}
      ]
    }
  ]
}
```

#### `POST /conflicts/{{conflictId}}/resolve`

```json
{
  "action": "MARK_SELECTED_STUDENT",
  "studentId": "stu_001",
  "reason": "Admin visually confirmed student"
}
```

### 11.14 Audit logs

#### `GET /audit-logs?from=2026-06-01&to=2026-06-30&entityType=ATTENDANCE`

```json
{
  "items": [
    {
      "id": "aud_001",
      "adminId": "adm_001",
      "actionType": "ATTENDANCE_MANUAL_EDIT",
      "entityType": "ATTENDANCE",
      "entityId": "att_001",
      "reason": "Admin correction after failed recognition",
      "createdAt": "2026-06-04T10:00:00+05:30"
    }
  ]
}
```

---

## 12. Import and export specifications

### 12.1 Roster import file

Supported formats:

1. XLSX.
2. CSV.

Required columns:

| Column | Required | Example |
|---|---|---|
| Student ID | Yes | CAMP-001 |
| Name | Yes | Aarav Sharma |
| Group | No | Group A |

Validation rules:

1. Student ID must be unique.
2. Name cannot be empty.
3. Duplicate rows must be reported.
4. Import must support preview before commit.
5. Import must create an audit log.

### 12.2 Attendance export workbook

File naming:

```text
attendance_YYYY-MM-DD_to_YYYY-MM-DD.xlsx
```

Sheets:

1. Summary.
2. Attendance Matrix.
3. Daily Logs.
4. Students.
5. Manual Edits & Audit.
6. Holidays.
7. Conflicts.

Attendance Matrix format:

| Student ID | Name | Group | 2026-06-01 | 2026-06-02 | 2026-06-03 |
|---|---|---|---|---|---|
| CAMP-001 | Aarav Sharma | Group A | P 09:01 | A | H |
| CAMP-002 | Meera Iyer | Group B | P 09:04 | P 09:00 | H |

Legend:

| Symbol | Meaning |
|---|---|
| P | Present |
| A | Absent / not marked |
| H | Holiday |
| M | Manually edited |
| C | Conflict resolved |

---

## 13. Security specification

### 13.1 Data-at-rest encryption

1. Use encrypted SQLite database or SQLCipher-compatible encrypted database.
2. Encrypt face embeddings before storage.
3. Protect encryption keys using Android Keystore.
4. Rotate export encryption or app backup keys if a backup feature is added.
5. Do not store raw camera frames after recognition.
6. Store encrypted reference thumbnails only if admin review requires them.

### 13.2 Admin password handling

1. Store salted password hash only.
2. Use a memory-hard password hashing algorithm where practical on Android.
3. Lock admin login temporarily after repeated failed attempts.
4. Require re-authentication for exports, settings changes, face-template deletion, and database reset.

### 13.3 Kiosk mode

Preferred deployment:

1. Provision the tablet as a dedicated device.
2. Enable Android Lock Task Mode.
3. Disable notification shade and system settings access where device policy allows.
4. Allow admin-only exit from kiosk.

Fallback:

1. Hide app navigation paths.
2. Require admin password for all sensitive screens.
3. Detect app backgrounding and return to kiosk screen on resume.

### 13.4 Data privacy

1. Process biometric matching locally.
2. Avoid cloud upload by design.
3. Provide export, update, and delete operations.
4. Maintain retention until admin deletes data.
5. Add deployment-level consent and privacy notices for India and review with legal counsel before production use.

---

## 14. Error handling

| Error | User-facing message | System action |
|---|---|---|
| Camera unavailable | “Camera not available. Contact admin.” | Log diagnostics |
| No face | “Place your face inside the oval.” | Continue scanning |
| Multiple faces | “Only one face at a time.” | Block marking |
| Low light | “Move to better light.” | Continue scanning |
| Blur | “Hold still.” | Continue scanning |
| Side face | “Look straight at the camera.” | Continue scanning |
| Low confidence | “Could not confirm identity. Try again.” | Log attempt |
| Ambiguous match | “Match unclear. Admin review needed.” | Create conflict |
| DB write failure | “Could not save. Contact admin.” | Retry transaction/log error |
| Export failure | “Export failed. Try again.” | Keep data unchanged |
| Import failure | “Import failed. Check file format.” | Create error report |

---

## 15. Testing strategy

### 15.1 Unit tests

1. Attendance one-per-day rules.
2. Holiday exclusion rules.
3. Matching threshold decision table.
4. Ambiguity margin logic.
5. Duplicate enrollment detection.
6. Import validation.
7. Export matrix generation.
8. Audit-log creation.
9. Password hashing and login lockout.

### 15.2 Instrumented Android tests

1. Kiosk screen opens by default.
2. Admin login succeeds/fails correctly.
3. Camera permissions flow.
4. Enrollment flow with test images.
5. Offline mode with airplane mode.
6. Database encryption smoke test.
7. Export through Storage Access Framework.

### 15.3 ML benchmark tests

1. Test recognition under bright light, low light, shadows, glasses, slight side face, blur, and movement.
2. Measure latency on target tablet and backup budget phone.
3. Evaluate false rejection and false acceptance using camp-like data.
4. Calibrate thresholds with at least a representative sample of enrolled users.
5. Validate performance with 100, 250, and 500 student templates.

### 15.4 Field test scenarios

1. Student queue with one person at a time.
2. Accidental multiple faces in frame.
3. Same student trying twice.
4. Poor first-day enrollment photo.
5. Admin manual correction.
6. Holiday date.
7. Export after several weeks offline.
8. Device restart during camp day.
9. Storage nearly full.
10. Incorrect roster import file.

---

## 16. Observability and diagnostics

Admin diagnostics should show:

1. App version.
2. Model name and version.
3. Embedding dimension.
4. Database status.
5. Storage usage.
6. Student count.
7. Enrolled student count.
8. Today’s attendance count.
9. Open conflict count.
10. Recent recognition latency percentiles.
11. Camera status.
12. Last export date.

Logs should avoid storing raw biometric images. Recognition attempts may store scores and reason codes.

---

## 17. Model lifecycle

1. Models must be versioned.
2. Templates must record the model version.
3. If the embedding model changes incompatibly, all students must be re-enrolled or templates must be migrated by reprocessing stored encrypted reference thumbnails if available.
4. Thresholds are model-specific and must not be reused blindly across model versions.
5. Model and threshold update must be an admin/audit event.

---

## 18. Build and release requirements

1. Android min SDK should be selected after target device review; avoid excluding budget tablets unnecessarily.
2. Release builds must enable code shrinking and resource shrinking after compatibility testing.
3. ML models must be packaged locally in the APK/AAB or copied into secure app storage during installation.
4. App should not require Play Services for critical offline functionality unless selected face detection dependency requires it and is verified to run offline.
5. Release process must include signing-key protection.
6. QA release must include a seeded test database and demo roster.

---

## 19. Technical risks

| Risk | Impact | Mitigation |
|---|---|---|
| Face embedding model underperforms on children/students | Wrong matches or failed recognition | Benchmark multiple models with representative data |
| Target tablet too slow | Fails <1 sec requirement | Use optimized model, lower detection resolution, preload model, benchmark early |
| Poor enrollment quality | High false rejection | Guided multi-sample enrollment and quality gates |
| Similar-looking students | Ambiguous matches | Top-1/top-2 margin threshold and admin conflict resolution |
| No liveness detection | Photo spoof possible | Accept as product tradeoff; optional future setting |
| Admin forgets password | Data inaccessible | Define reset procedure with data-preservation or secure reset |
| Device loss | Biometric data exposure risk | Full DB encryption and Android device lock |
| Export file leakage | Attendance privacy risk | Admin-only export, audit logs, optional encrypted export setting |
| Model update incompatibility | Templates unusable | Version templates and require migration/re-enrollment plan |

---

## 20. Source references for implementation research

1. ZepIris repository and README: face-authentication pipeline, embeddings, vector search, quality checks, server architecture.
2. Android CameraX documentation: camera preview and ImageAnalysis implementation.
3. Google ML Kit Face Detection documentation: on-device face detection behavior and image-size guidance.
4. LiteRT / TensorFlow Lite documentation: on-device ML runtime and model deployment.
5. Android Keystore and data security documentation: local encryption and key protection.
