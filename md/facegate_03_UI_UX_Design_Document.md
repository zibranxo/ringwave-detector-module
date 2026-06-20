# UI/UX Design Document

**Project:** FaceGate Attendance  
**Prepared for:** Internal product and design team  
**Prepared on:** 2026-06-04  
**Document status:** Draft for implementation planning

---

## 1. UX principles

The app has two very different UX surfaces: a student-facing kiosk mode and an admin mode. The student-facing mode must be extremely fast, obvious, and nearly instruction-free. The admin mode must be complete but mobile-first, because it will usually be operated on the same Android tablet.

Design principles:

1. One primary action per screen.
2. Large visual feedback for students.
3. Minimal text during attendance marking.
4. Use color, shape, sound, and name confirmation for success.
5. Use short actionable failure messages.
6. Avoid exposing admin complexity to students.
7. Make admin workflows searchable and recoverable.
8. Do not require internet, external keyboard, mouse, or desktop screen.
9. Keep all sensitive admin screens behind password authentication.
10. Treat conflict resolution as a normal admin workflow, not an exceptional engineering task.

---

## 2. Information architecture

```text
App Launch
└── Kiosk Attendance Screen
    ├── Auto Scan
    ├── Manual Capture
    ├── Result Feedback
    └── Hidden/Admin Entry
        └── Admin Login
            └── Admin Dashboard
                ├── Students
                │   ├── Student List
                │   ├── Student Profile
                │   ├── Add/Edit Student
                │   └── Enroll/Update Face
                ├── Attendance
                │   ├── Today
                │   ├── Date Range Report
                │   └── Manual Edit
                ├── Conflicts
                │   ├── Open Conflicts
                │   └── Resolve Conflict
                ├── Holidays
                │   ├── Holiday List
                │   └── Add/Edit Holiday
                ├── Import/Export
                │   ├── Import Roster
                │   ├── Export Attendance
                │   └── Export History
                ├── Audit Logs
                ├── Settings
                │   ├── Attendance Mode
                │   ├── Matching Thresholds
                │   ├── Kiosk Settings
                │   └── Security Settings
                └── Diagnostics
```

---

## 3. Student-facing kiosk mode

### 3.1 Screen goals

The kiosk screen must answer only three questions for the student:

1. Where should I stand/look?
2. Is the app processing me?
3. Has my attendance been marked?

### 3.2 Default kiosk screen

Text wireframe:

```text
┌─────────────────────────────────────────────┐
│                                             │
│              FaceGate Attendance           │
│                                             │
│         ┌─────────────────────────┐         │
│         │                         │         │
│         │       CAMERA VIEW       │         │
│         │                         │         │
│         │     (large face oval)   │         │
│         │                         │         │
│         └─────────────────────────┘         │
│                                             │
│          Place your face inside the oval    │
│                                             │
│              [ Capture Manually ]           │
│                                             │
│                              Admin          │
└─────────────────────────────────────────────┘
```

### 3.3 Visual states

| State | Oval color | Sound | Text | Attendance action |
|---|---|---|---|---|
| Idle | Neutral | None | “Place your face inside the oval” | None |
| Detecting | Neutral animated | None | “Hold still” | None |
| Processing | Neutral/blue pulse | None | “Checking…” | None |
| Success | Green | Short success tone | “Marked: [Name]” | Save present |
| Already marked | Green | Softer success tone | “Already marked today: [Name]” | No duplicate save |
| Warning/retry | Red | Optional low warning tone | Actionable instruction | None |
| Admin review | Red | Optional low warning tone | “Admin review needed” | Create conflict |

### 3.4 Success screen

```text
┌─────────────────────────────────────────────┐
│                                             │
│             ✓ Attendance Marked             │
│                                             │
│           ┌─────────────────────┐           │
│           │     GREEN OVAL      │           │
│           │   face preview      │           │
│           └─────────────────────┘           │
│                                             │
│              Aarav Sharma                   │
│              09:01 AM                       │
│                                             │
│          Returning to scan...               │
│                                             │
└─────────────────────────────────────────────┘
```

Display duration: 1.0-1.5 seconds. The app should then return to scanning mode automatically.

### 3.5 Red warning examples

```text
┌─────────────────────────────────────────────┐
│                                             │
│           ┌─────────────────────┐           │
│           │      RED OVAL       │           │
│           │   camera preview    │           │
│           └─────────────────────┘           │
│                                             │
│             Only one face at a time         │
│                                             │
│              [ Capture Manually ]           │
│                                             │
└─────────────────────────────────────────────┘
```

Warning copy must be short and operational:

| Condition | Copy |
|---|---|
| No face | Place your face inside the oval. |
| Multiple faces | Only one face at a time. |
| Face too small | Move closer. |
| Face too large | Move back slightly. |
| Blur | Hold still. |
| Low light | Move to better light. |
| Side face | Look straight at the camera. |
| Low confidence | Could not confirm identity. Try again. |
| Ambiguous match | Match unclear. Admin review needed. |
| Holiday | Holiday today. Attendance not required. |

---

## 4. Admin access pattern

Admin entry should not distract students. Recommended methods:

1. Small “Admin” text button in bottom corner.
2. Long press on app title for 3 seconds.
3. Optional PIN/password prompt after tapping Admin.

Admin login wireframe:

```text
┌─────────────────────────────────────────────┐
│              Admin Login                    │
│                                             │
│  Username                                   │
│  ┌───────────────────────────────────────┐  │
│  │ admin                                 │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Password                                   │
│  ┌───────────────────────────────────────┐  │
│  │ •••••••••                             │  │
│  └───────────────────────────────────────┘  │
│                                             │
│              [ Login ]                      │
│                                             │
│              Back to Attendance             │
└─────────────────────────────────────────────┘
```

Session behavior:

1. Admin session expires after inactivity.
2. Returning from background should require re-authentication for sensitive screens.
3. Export, delete, reset, and threshold changes should require password confirmation.

---

## 5. Admin dashboard

### 5.1 Dashboard goals

The dashboard should show operational status without overwhelming the admin.

Primary metrics:

1. Today’s present count.
2. Total active students.
3. Not marked today.
4. Open conflicts.
5. Holiday status.
6. Last export date.
7. Device/storage status.

Wireframe:

```text
┌─────────────────────────────────────────────┐
│ Admin Dashboard                     Logout  │
│                                             │
│ Today: 04 Jun 2026                          │
│                                             │
│ ┌──────────────┐ ┌──────────────┐           │
│ │ Present       │ │ Not Marked    │          │
│ │ 83            │ │ 42            │          │
│ └──────────────┘ └──────────────┘           │
│                                             │
│ ┌──────────────┐ ┌──────────────┐           │
│ │ Students      │ │ Conflicts     │          │
│ │ 125           │ │ 3 open        │          │
│ └──────────────┘ └──────────────┘           │
│                                             │
│ [ Students ] [ Attendance ] [ Conflicts ]   │
│ [ Holidays ] [ Import/Export ] [ Settings ] │
│ [ Audit Logs ] [ Diagnostics ]              │
│                                             │
│                 Back to Kiosk               │
└─────────────────────────────────────────────┘
```

---

## 6. Student management

### 6.1 Student list

Features:

1. Search by name or student ID.
2. Filter by group.
3. Filter by enrolled/not enrolled.
4. Filter by active/inactive.
5. Quick action to enroll missing faces.

Wireframe:

```text
┌─────────────────────────────────────────────┐
│ Students                            + Add   │
│ ┌───────────────────────────────────────┐   │
│ │ Search name or ID                     │   │
│ └───────────────────────────────────────┘   │
│ [All] [Not Enrolled] [Group] [Inactive]     │
│                                             │
│ Aarav Sharma        CAMP-001   Enrolled     │
│ Meera Iyer          CAMP-002   Not Enrolled │
│ Kabir Khan          CAMP-003   Enrolled     │
│                                             │
│ [Import Roster]                            │
└─────────────────────────────────────────────┘
```

### 6.2 Student profile

Wireframe:

```text
┌─────────────────────────────────────────────┐
│ Aarav Sharma                         Edit   │
│ CAMP-001 | Group A                          │
│                                             │
│ Face status: Enrolled                       │
│ Templates: 5 active                         │
│ Last attendance: Today, 09:01 AM            │
│                                             │
│ [ Enroll / Update Face ]                    │
│ [ Mark Attendance Manually ]                │
│ [ View Attendance History ]                 │
│ [ Deactivate Student ]                      │
│                                             │
│ Recent Attendance                           │
│ 04 Jun 2026   Present   09:01 AM            │
│ 03 Jun 2026   Present   09:04 AM            │
│ 02 Jun 2026   Absent                        │
└─────────────────────────────────────────────┘
```

---

## 7. Enrollment UX

### 7.1 Enrollment from camera

The enrollment flow must guide the admin through multiple samples. It should not require the admin to understand embeddings or model quality.

Recommended sample steps:

1. Straight face.
2. Slight left.
3. Slight right.
4. Slight up/down or natural variation.
5. Best neutral sample selected by app.

Wireframe:

```text
┌─────────────────────────────────────────────┐
│ Enroll Face: Aarav Sharma                   │
│ Step 1 of 5: Straight face                  │
│                                             │
│         ┌─────────────────────────┐         │
│         │     CAMERA + OVAL       │         │
│         └─────────────────────────┘         │
│                                             │
│ Quality: Good                               │
│                                             │
│ [ Retake ]                         [ Save ] │
└─────────────────────────────────────────────┘
```

Quality states:

| State | Copy |
|---|---|
| Good | Quality good. Save this sample. |
| Blur | Hold still and retake. |
| Low light | Improve lighting and retake. |
| Multiple faces | Only the selected student should be visible. |
| Duplicate risk | This face looks similar to [Name]. Review before saving. |

### 7.2 Enrollment from photo

Wireframe:

```text
┌─────────────────────────────────────────────┐
│ Import Face Photo                           │
│                                             │
│ Student: Aarav Sharma                       │
│                                             │
│ [ Select Image ]                            │
│                                             │
│ Preview                                     │
│ ┌───────────────────────┐                   │
│ │ passport photo        │                   │
│ └───────────────────────┘                   │
│                                             │
│ Quality: Good                               │
│ Duplicate risk: None                        │
│                                             │
│ [ Cancel ]                         [ Save ] │
└─────────────────────────────────────────────┘
```

---

## 8. Attendance reports UX

### 8.1 Report selection

Wireframe:

```text
┌─────────────────────────────────────────────┐
│ Attendance Reports                          │
│                                             │
│ Date from: [ 01 Jun 2026 ]                  │
│ Date to:   [ 30 Jun 2026 ]                  │
│ Group:     [ All groups     v ]             │
│                                             │
│ [ Generate Preview ]                        │
│ [ Export Excel ]                            │
│                                             │
│ Summary                                     │
│ Students: 125                               │
│ Days: 30                                    │
│ Holidays: 2                                 │
│ Present records: 2,980                      │
└─────────────────────────────────────────────┘
```

### 8.2 Attendance matrix preview

Wireframe:

```text
┌─────────────────────────────────────────────┐
│ Attendance: 01 Jun - 30 Jun                 │
│                                             │
│ Search: [ Name or ID ]                      │
│                                             │
│ Name            01 Jun  02 Jun  03 Jun      │
│ Aarav Sharma    P 09:01 A       H           │
│ Meera Iyer      P 09:04 P 09:02 H           │
│ Kabir Khan      A       P 09:10 H           │
│                                             │
│ [ Export Excel ]                            │
└─────────────────────────────────────────────┘
```

---

## 9. Manual attendance edit UX

Manual edits are required but should feel controlled and auditable.

Wireframe:

```text
┌─────────────────────────────────────────────┐
│ Manual Attendance Edit                      │
│                                             │
│ Student: Aarav Sharma                       │
│ Date: 04 Jun 2026                           │
│ Current: Absent                             │
│                                             │
│ New status                                  │
│ ( ) Absent                                  │
│ (•) Present                                 │
│                                             │
│ Time: [ 09:05 AM ]                          │
│ Reason:                                     │
│ ┌───────────────────────────────────────┐   │
│ │ Recognition failed, admin confirmed    │   │
│ └───────────────────────────────────────┘   │
│                                             │
│ [ Cancel ]                    [ Save Edit ] │
└─────────────────────────────────────────────┘
```

Validation:

1. Reason is required.
2. Admin must confirm password for sensitive edit if session is old.
3. Audit log must be created.

---

## 10. Conflict resolution UX

### 10.1 Conflict list

Wireframe:

```text
┌─────────────────────────────────────────────┐
│ Conflicts                                   │
│ [Open] [Resolved] [Dismissed]               │
│                                             │
│ Ambiguous Match     Today 09:12 AM          │
│ Aarav Sharma 0.81 / Aryan Sharma 0.79       │
│                                             │
│ Low Confidence      Today 09:20 AM          │
│ Best match: Meera Iyer 0.62                 │
└─────────────────────────────────────────────┘
```

### 10.2 Resolve ambiguous match

Wireframe:

```text
┌─────────────────────────────────────────────┐
│ Resolve Conflict                            │
│ Type: Ambiguous Match                       │
│ Time: 09:12 AM                              │
│                                             │
│ Candidate 1                                 │
│ Aarav Sharma             Score 0.81         │
│ [ Select Aarav ]                            │
│                                             │
│ Candidate 2                                 │
│ Aryan Sharma             Score 0.79         │
│ [ Select Aryan ]                            │
│                                             │
│ [ Dismiss ] [ Re-enroll Student ]           │
│                                             │
│ Reason                                      │
│ ┌───────────────────────────────────────┐   │
│ │ Admin confirmed from queue             │   │
│ └───────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

Admin should see reference thumbnails only if encrypted thumbnails are enabled. Otherwise, conflict resolution should rely on candidate names, student IDs, and optionally rescanning the student.

---

## 11. Holidays UX

Wireframe:

```text
┌─────────────────────────────────────────────┐
│ Holidays                              + Add │
│                                             │
│ 10 Jun 2026    Camp Rest Day                │
│ 15 Jun 2026    Local Holiday                │
│                                             │
│ [ Export Holiday List ]                     │
└─────────────────────────────────────────────┘
```

Add/edit holiday:

```text
┌─────────────────────────────────────────────┐
│ Add Holiday                                 │
│                                             │
│ Date:  [ 10 Jun 2026 ]                      │
│ Title: [ Camp Rest Day ]                    │
│ Notes: [ No attendance required ]           │
│                                             │
│ [ Cancel ]                         [ Save ] │
└─────────────────────────────────────────────┘
```

---

## 12. Import/export UX

### 12.1 Import roster

Wireframe:

```text
┌─────────────────────────────────────────────┐
│ Import Roster                               │
│                                             │
│ File: students.xlsx                         │
│                                             │
│ Column mapping                              │
│ Student ID: [ Student ID v ]                │
│ Name:       [ Name       v ]                │
│ Group:      [ Group      v ]                │
│                                             │
│ Preview: 125 rows                           │
│ Issues: 2 duplicate IDs                     │
│                                             │
│ [ Cancel ]                 [ Import Valid ] │
└─────────────────────────────────────────────┘
```

### 12.2 Export attendance

Wireframe:

```text
┌─────────────────────────────────────────────┐
│ Export Attendance                           │
│                                             │
│ Date from: [ 01 Jun 2026 ]                  │
│ Date to:   [ 30 Jun 2026 ]                  │
│                                             │
│ Include:                                    │
│ [✓] Attendance Matrix                       │
│ [✓] Daily Logs                              │
│ [✓] Manual Edits & Audit                    │
│ [✓] Holidays                                │
│ [✓] Conflicts                               │
│                                             │
│ [ Export Excel ]                            │
└─────────────────────────────────────────────┘
```

After export:

```text
Export complete
attendance_2026-06-01_to_2026-06-30.xlsx

[ Share ] [ Save to Device ] [ Done ]
```

---

## 13. Settings UX

Settings should be grouped to prevent accidental configuration changes.

```text
┌─────────────────────────────────────────────┐
│ Settings                                    │
│                                             │
│ Attendance Mode                             │
│  Current: Check-in only                     │
│                                             │
│ Matching                                    │
│  Acceptance threshold: Locked               │
│  Ambiguity margin: Locked                   │
│  [ Advanced Calibration ]                   │
│                                             │
│ Security                                    │
│  Change admin password                      │
│  Kiosk mode: Enabled                        │
│                                             │
│ Data                                       │
│  Export all data                            │
│  Delete student data                        │
│  Reset application                          │
└─────────────────────────────────────────────┘
```

Advanced calibration should require password confirmation and should be hidden unless required by support/engineering.

---

## 14. Audit logs UX

Wireframe:

```text
┌─────────────────────────────────────────────┐
│ Audit Logs                                  │
│                                             │
│ Filter: [ Attendance Edits v ]              │
│ Date:   [ This Month v ]                    │
│                                             │
│ 04 Jun 10:00 AM                             │
│ Admin changed Aarav Sharma to Present       │
│ Reason: Recognition failed, confirmed       │
│                                             │
│ 04 Jun 09:00 AM                             │
│ Admin exported attendance report            │
└─────────────────────────────────────────────┘
```

---

## 15. Accessibility and practical usability

1. Use high contrast for green/red state indicators.
2. Do not rely only on color; also show icon/text.
3. Use large typography on kiosk screen.
4. Keep success and warning tones short and non-intrusive.
5. Manual capture button should be large enough for tablet use.
6. Admin tables should support horizontal scrolling but avoid dense desktop layouts.
7. Critical actions must have confirmation dialogs.
8. Avoid hidden gestures as the only admin access path; include a visible but small Admin option.

---

## 16. UI content standards

Use short commands, not long explanations.

Preferred:

1. “Move closer.”
2. “Hold still.”
3. “Only one face at a time.”
4. “Marked: Aarav Sharma.”
5. “Already marked today.”

Avoid:

1. “The system was unable to detect sufficient biometric markers.”
2. “Face vector similarity is below threshold.”
3. “Recognition pipeline failed.”

---

## 17. Design system draft

### 17.1 Components

1. Kiosk camera frame.
2. Face oval guide.
3. Status banner.
4. Admin metric card.
5. Student list item.
6. Conflict card.
7. Attendance matrix table.
8. Confirmation dialog.
9. Import mapping row.
10. Export option checkbox.
11. Audit log entry.
12. Settings section.

### 17.2 Color semantics

| Semantic | Usage |
|---|---|
| Green | Attendance marked / already marked |
| Red | Blocking issue or failed recognition |
| Neutral | Idle camera state |
| Warning | Admin attention needed |

The implementation can select exact colors during UI development, but color must be paired with text/icon to avoid ambiguity.

### 17.3 Sound semantics

| Sound | Usage |
|---|---|
| Short positive tone | Attendance marked |
| Softer positive tone | Already marked |
| Optional short warning tone | Blocking issue |

Sound should be configurable by admin.

---

## 18. UX acceptance criteria

1. A first-time student can understand where to place their face without admin instruction.
2. A successful scan clearly shows green state, name, and confirmation sound.
3. A failed scan explains the corrective action in fewer than eight words where possible.
4. Admin can import roster, enroll a student, export attendance, and return to kiosk mode without leaving the app.
5. Admin can resolve an ambiguous match without engineering support.
6. Manual edit requires reason and creates an audit log.
7. Holiday setup is discoverable from admin dashboard.
8. The app is usable on a tablet in portrait or landscape, with portrait preferred unless hardware mount dictates otherwise.
