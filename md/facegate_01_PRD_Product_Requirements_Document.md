# PRD — Product Requirements Document

**Project:** FaceGate Attendance  
**Prepared for:** Internal product and engineering team  
**Prepared on:** 2026-06-04  
**Document status:** Draft for implementation planning

---

## 1. Product summary

FaceGate Attendance is an offline-first Android tablet application for marking school-camp attendance using face matching. The product is intended for a camp-like setting where more than 100 students may mark attendance on a shared Android tablet. The primary attendance experience must be extremely simple: a student stands in front of the tablet camera, aligns their face inside an on-screen oval, the app automatically recognizes the student in less than one second on average hardware, and attendance is marked for that day with a green confirmation and a short sound. If a problem is detected, the oval turns red and the app gives a clear corrective instruction.

The same application also contains an admin mode protected by password and kiosk controls. Admin users can enroll students, import rosters, manage face templates, configure holidays, resolve recognition conflicts, manually edit attendance with audit logs, and export clean Excel attendance reports.

The system must operate fully without internet. All face matching, attendance marking, conflict handling, and reporting must work on-device. Data from multiple devices does not need to sync; if multiple devices are ever used, they are considered independent installations.

---

## 2. Problem statement

School-camp attendance is often taken manually, which creates delays, queues, transcription errors, proxy attendance, and administrative friction when attendance records need to be exported later. The camp context also creates real-world constraints: lighting may vary, students may queue in groups, the device may be a budget Android tablet, internet may be unavailable for weeks, and a non-technical admin may need to run the system with minimal training.

The product must replace manual attendance with a fast face-matching experience while preserving administrative control for edge cases.

---

## 3. Goals

The product must achieve the following goals:

1. Mark daily attendance automatically through on-device face matching.
2. Complete the recognition and marking loop in less than one second under normal conditions on average Android hardware.
3. Work fully offline for more than several weeks.
4. Support more than 100 enrolled students on one shared Android tablet.
5. Use a simple kiosk-style student experience with minimal visible controls.
6. Provide a mobile-first admin mode in the same app.
7. Allow roster import, student enrollment, face-template update, holidays, manual corrections, conflict resolution, and Excel export.
8. Store biometric templates and attendance data securely with encryption.
9. Keep a complete audit trail for admin actions and attendance changes.
10. Provide robust handling of blur, low light, shadows, glasses, side face, no face, multiple faces, duplicate-looking students, and low-confidence matches.

---

## 4. Non-goals

The following are explicitly out of scope for the first enterprise-grade release:

1. Cloud sync across multiple devices.
2. External HRMS, ERP, payroll, LMS, or notification integrations.
3. GPS, Wi-Fi, QR code, or geofence attendance constraints.
4. Shift-based attendance, late marks, half-day, leave, overtime, or absence workflows beyond present/not present reporting.
5. Real-time parent/student notifications.
6. Liveness detection for print/photo spoofing prevention.
7. Multi-organization tenancy.
8. Public web admin portal.
9. Internet-dependent face recognition.

---

## 5. Target users

### 5.1 Student / attendee

The student does not log in. The student only stands in front of the tablet, aligns their face within the oval, waits for the green confirmation, sees their name, and leaves.

### 5.2 Camp admin

The admin is responsible for setup and operations. The admin logs in with a password, imports the student roster, enrolls or updates faces, configures holidays, reviews reports, resolves conflicts, and exports attendance.

### 5.3 Internal engineering/support operator

The internal team is responsible for deployment, model calibration, device preparation, backups, and troubleshooting.

---

## 6. Operating context

| Area | Requirement |
|---|---|
| Environment | School/camp setting |
| Primary device | Android tablet |
| Secondary compatible device | Budget Android phone |
| User pattern | One shared device used by many students |
| Enrollment size | More than 100 students |
| Connectivity | Fully offline-first; internet not required |
| Multi-device behavior | Independent devices; no sync required |
| Admin location | Same app, same device preferred |
| Attendance format | Single daily attendance status: present or not present |
| Export format | Excel report generated on demand |
| Country | India |

---

## 7. Product assumptions

1. Consent for biometric attendance has already been collected by the school/camp authority.
2. Each deployment is for a single organization on a single device.
3. Face embeddings are preferred over storing full raw face images.
4. Admin may optionally store encrypted reference thumbnails if needed for review, but raw face-image storage should be minimized.
5. The attendance device can be prepared before camp with app installation, admin password setup, kiosk configuration, and optional roster import.
6. Students can be enrolled either through one passport-style photo or through the app camera on the first day.
7. If enrollment happens through the app camera, multiple reference samples should be captured to improve robustness.
8. Because the dataset is expected to be greater than 100 students but not massive, a local vector comparison over normalized embeddings is sufficient if optimized.

---

## 8. Core attendance experience

### 8.1 Default student flow

1. App opens directly into attendance kiosk mode.
2. Front camera preview is shown.
3. A large oval guide is shown in the center of the screen.
4. Student aligns face inside the oval.
5. App detects a single usable face.
6. App auto-captures the best frame.
7. App creates a face embedding on-device.
8. App compares the embedding against locally stored encrypted student embeddings.
9. If confidence is high and unambiguous, attendance is automatically marked.
10. Oval turns green.
11. A short success sound plays.
12. App displays: “Marked: [Student Name]”.
13. App returns to scanning state after a short delay.

### 8.2 Failure flow

1. App detects an issue.
2. Oval turns red.
3. A clear short message is shown.
4. No attendance is marked.
5. Student retries automatically or presses the fallback capture button.

Examples of failure messages:

| Condition | Message |
|---|---|
| No face | “Place your face inside the oval.” |
| Multiple faces | “Only one face at a time.” |
| Blur | “Hold still.” |
| Low light | “Move to better light.” |
| Side face | “Look straight at the camera.” |
| Face too small | “Move closer.” |
| Face too large | “Move back slightly.” |
| Low confidence | “Could not confirm identity. Try again.” |
| Ambiguous match | “Match unclear. Admin review needed.” |
| Already marked | “Already marked today: [Student Name].” |

---

## 9. Functional requirements

### 9.1 Kiosk attendance mode

| ID | Requirement | Priority |
|---|---|---|
| FR-K01 | The app shall open into kiosk attendance mode by default. | Must |
| FR-K02 | The app shall display front-camera preview with an oval alignment guide. | Must |
| FR-K03 | The app shall auto-capture when one good-quality face is detected. | Must |
| FR-K04 | The app shall provide a manual capture button for difficult cases. | Must |
| FR-K05 | The app shall show green visual confirmation after successful attendance. | Must |
| FR-K06 | The app shall play a short success sound after successful attendance. | Must |
| FR-K07 | The app shall show the matched student name after successful attendance. | Must |
| FR-K08 | The app shall show red visual feedback when an issue is detected. | Must |
| FR-K09 | The app shall prevent more than one attendance mark per student per day. | Must |
| FR-K10 | The app shall work without internet for all attendance operations. | Must |

### 9.2 Face matching

| ID | Requirement | Priority |
|---|---|---|
| FR-F01 | The app shall perform face detection fully on-device. | Must |
| FR-F02 | The app shall generate face embeddings fully on-device. | Must |
| FR-F03 | The app shall compare captured embeddings against locally stored embeddings. | Must |
| FR-F04 | The app shall support more than 100 enrolled students. | Must |
| FR-F05 | The app shall target less than one second from usable frame to result. | Must |
| FR-F06 | The app shall prioritize avoiding false rejection while controlling false acceptance through confidence and ambiguity checks. | Must |
| FR-F07 | The app shall detect and warn on poor-quality frames. | Must |
| FR-F08 | The app shall detect multiple faces and block marking. | Must |
| FR-F09 | The app shall support glasses and reasonable real-world lighting variation. | Must |
| FR-F10 | The app shall not require liveness detection in the first release. | Must |

### 9.3 Enrollment

| ID | Requirement | Priority |
|---|---|---|
| FR-E01 | Admin shall be able to import student roster using Excel or CSV. | Must |
| FR-E02 | Admin shall be able to enroll a student using the tablet camera. | Must |
| FR-E03 | Admin shall be able to enroll a student using one passport-style reference image. | Must |
| FR-E04 | App-camera enrollment shall capture multiple samples per student. | Must |
| FR-E05 | The app shall reject poor-quality enrollment images and request retake. | Must |
| FR-E06 | Only admin shall be able to add, update, or remove face templates. | Must |
| FR-E07 | The app shall warn admin if a newly enrolled face is very similar to an existing student. | Must |
| FR-E08 | The app shall allow admin to delete a student and associated templates. | Must |
| FR-E09 | The app shall allow admin to export student data and attendance data. | Must |

Recommended camera enrollment sample set:

1. Straight face, neutral expression.
2. Slight left turn.
3. Slight right turn.
4. Slight up/down variation or glasses-on image if applicable.
5. Best automatically selected still frame from the enrollment stream.

The app should store embeddings for all accepted samples and optionally store one encrypted thumbnail for admin confirmation.

### 9.4 Admin mode

| ID | Requirement | Priority |
|---|---|---|
| FR-A01 | Admin mode shall be accessible only through password authentication. | Must |
| FR-A02 | Admin mode shall be mobile-first and usable on the same tablet. | Must |
| FR-A03 | Admin shall see a minimal dashboard with today’s attendance count and unresolved conflicts. | Must |
| FR-A04 | Admin shall manage students. | Must |
| FR-A05 | Admin shall manage face templates. | Must |
| FR-A06 | Admin shall configure holidays. | Must |
| FR-A07 | Admin shall manually edit attendance. | Must |
| FR-A08 | Manual edits shall create audit logs. | Must |
| FR-A09 | Admin shall resolve conflicts from low-confidence or ambiguous matches. | Must |
| FR-A10 | Admin shall export attendance to Excel on demand. | Must |
| FR-A11 | Admin shall change kiosk and matching settings only after password entry. | Must |

### 9.5 Attendance rules

| ID | Requirement | Priority |
|---|---|---|
| FR-R01 | Attendance is recorded once per student per calendar day. | Must |
| FR-R02 | Default attendance mode is check-in only. | Must |
| FR-R03 | Admin can enable check-in/check-out and multiple sessions in settings. | Should |
| FR-R04 | Holidays shall not require attendance. | Must |
| FR-R05 | Holiday dates shall be excluded or marked as holiday in exports. | Must |
| FR-R06 | Manual attendance changes shall preserve original record history through audit logs. | Must |
| FR-R07 | If the same student is recognized again on the same day, the app shall show “Already marked” without creating a duplicate. | Must |

### 9.6 Export and reporting

| ID | Requirement | Priority |
|---|---|---|
| FR-X01 | Admin shall export attendance for any selected date range. | Must |
| FR-X02 | Export shall be an Excel file. | Must |
| FR-X03 | Export shall include each student and each selected date. | Must |
| FR-X04 | Export shall include name, present/absent, date, and time. | Must |
| FR-X05 | Export shall include holidays distinctly. | Must |
| FR-X06 | Export shall include manual edits and audit information in a separate sheet. | Must |
| FR-X07 | Export shall be clean and systematic for administrative use. | Must |

Recommended Excel workbook sheets:

1. **Summary** — date range, total students, days, present counts, holiday counts.
2. **Attendance Matrix** — students as rows and dates as columns.
3. **Daily Logs** — one row per attendance event.
4. **Students** — roster snapshot.
5. **Manual Edits & Audit** — changed records with reason and timestamp.
6. **Holidays** — configured holiday dates.
7. **Conflicts** — resolved and unresolved recognition conflicts.

---

## 10. Conflict and edge-case requirements

### 10.1 Recognition confidence states

| State | Condition | Result |
|---|---|---|
| High-confidence match | Top match score above acceptance threshold and sufficiently above second match | Mark attendance automatically |
| Already marked | High-confidence match but student has attendance for the day | Show green “Already marked” confirmation |
| Low-confidence match | Top match below acceptance threshold | Do not mark; request retry; log failed attempt |
| Ambiguous match | Top two candidates are too close | Do not mark; create conflict case |
| Duplicate enrollment risk | New enrollment is too close to existing student | Warn admin before saving |
| Multiple faces | More than one face visible | Do not mark; ask for one student only |
| Poor-quality frame | Blur, low light, side face, face too small/large | Do not mark; guide user |

### 10.2 Mitigation requirements

1. The app must use both a similarity threshold and a top-1/top-2 margin threshold.
2. The app must keep configurable thresholds in admin settings, but defaults should be locked after calibration.
3. The app must not mark attendance when two candidates are too close, even if the top score is above threshold.
4. During enrollment, the app must check whether the new face template is too close to an existing template.
5. The app must keep an unresolved conflict queue for admin review.
6. Admin conflict resolution must create audit logs.
7. The app must provide direct feedback to improve the next capture attempt instead of generic errors.
8. The app must prefer retrying capture automatically before escalating to admin conflict.

---

## 11. Data requirements

### 11.1 Student data

Minimum student fields:

1. Student ID.
2. Full name.
3. Active/inactive status.
4. Optional group/class/batch.
5. Face enrollment status.
6. Created timestamp.
7. Updated timestamp.

### 11.2 Attendance data

Minimum attendance fields:

1. Student ID.
2. Student name snapshot.
3. Attendance date.
4. Present/absent state.
5. Attendance timestamp.
6. Match confidence.
7. Marking source: auto, manual, conflict resolution, import.
8. Device ID.
9. Edit/audit status.

### 11.3 Face-template data

Minimum face-template fields:

1. Template ID.
2. Student ID.
3. Model version.
4. Embedding vector.
5. Quality score.
6. Capture method: camera or image upload.
7. Created timestamp.
8. Active/inactive flag.

### 11.4 Audit data

Minimum audit-log fields:

1. Admin ID.
2. Action type.
3. Entity type.
4. Entity ID.
5. Before value.
6. After value.
7. Reason, where applicable.
8. Timestamp.
9. Device ID.

---

## 12. Security and privacy requirements

| ID | Requirement | Priority |
|---|---|---|
| SEC-01 | Local database shall be encrypted at rest. | Must |
| SEC-02 | Face embeddings shall be encrypted at rest. | Must |
| SEC-03 | Admin password shall be salted and hashed, not stored as plaintext. | Must |
| SEC-04 | Encryption keys shall be protected through Android Keystore where available. | Must |
| SEC-05 | Kiosk mode shall prevent unauthorized app exit and settings access where device policy allows. | Must |
| SEC-06 | Admin actions shall be audit logged. | Must |
| SEC-07 | Exports shall be explicitly generated by admin only. | Must |
| SEC-08 | App shall support data export, update, and deletion. | Must |
| SEC-09 | App shall minimize storage of raw face images. | Must |
| SEC-10 | Face thumbnails, if stored, shall be encrypted and admin-only. | Must |
| SEC-11 | The app shall not require or silently transmit biometric data to a server. | Must |
| SEC-12 | Deployment shall include a consent and retention policy reviewed for Indian legal requirements. | Must |

---

## 13. Non-functional requirements

### 13.1 Performance

| Requirement | Target |
|---|---|
| Recognition loop | Less than 1 second from usable frame to result under normal conditions |
| App launch to ready | Less than 5 seconds after cold start on target tablet |
| Enrollment save | Less than 3 seconds per accepted sample |
| Report export | Less than 30 seconds for 100 students over 60 attendance days |
| Local search | Less than 100 ms for 100-500 students after embedding generation |

### 13.2 Reliability

1. App must not crash when camera permission, storage permission, or file import fails.
2. Attendance records must be transactionally saved.
3. Duplicate daily attendance must be prevented at database level.
4. Export failures must not corrupt attendance data.
5. The app must recover gracefully from restart and continue offline.

### 13.3 Usability

1. Student screen must be readable from one to two meters away.
2. Admin screen must be usable on tablet without external keyboard.
3. Error messages must be short and action-oriented.
4. Admin workflows must not require technical knowledge.

### 13.4 Maintainability

1. Matching thresholds and model version must be visible in admin diagnostics.
2. Model upgrades must be versioned.
3. Face templates must record the model version used to generate them.
4. Test mode must allow sample images or replay frames for QA.

---

## 14. Acceptance criteria

### 14.1 Attendance acceptance criteria

1. Given a properly enrolled student stands alone in front of the tablet, when their face is aligned inside the oval, then attendance is marked automatically and the oval turns green.
2. Given a student has already been marked today, when the student is recognized again, then no duplicate record is created and the app displays “Already marked today.”
3. Given two faces are visible, when the scanner detects them, then no attendance is marked and the app displays “Only one face at a time.”
4. Given a face is blurred or poorly lit, when the scanner evaluates the frame, then no attendance is marked and the app provides corrective guidance.
5. Given the top two match candidates are too close, when matching completes, then the app creates a conflict case instead of marking attendance.

### 14.2 Admin acceptance criteria

1. Admin can import a roster file and see all students in the app.
2. Admin can enroll a student using the tablet camera.
3. Admin can update a student’s face template.
4. Admin can set a holiday and the export marks that date as holiday.
5. Admin can manually edit a student’s attendance and the audit log records the edit.
6. Admin can export attendance for a selected date range as an Excel file.
7. Admin can delete or deactivate a student and their face templates.

### 14.3 Security acceptance criteria

1. Without admin password, a user cannot access roster, attendance reports, face templates, holidays, exports, or settings.
2. Local database and biometric templates are encrypted at rest.
3. Admin password is stored as a password hash with salt.
4. Export action creates an audit-log entry.
5. Delete, update, and export actions are available for student data.

### 14.4 Offline acceptance criteria

1. Attendance marking works when airplane mode is enabled.
2. Enrollment works when airplane mode is enabled.
3. Admin reporting and export work when airplane mode is enabled.
4. App continues to work after more than two weeks without internet.

---

## 15. Open decisions for implementation team

These are not blockers for document creation, but they must be finalized during engineering planning:

1. Exact on-device face embedding model and licensing.
2. Final acceptance and ambiguity thresholds after benchmark testing.
3. Whether encrypted face thumbnails are stored or disabled by default.
4. Whether roster import uses XLSX only, CSV only, or both.
5. Whether admin password recovery is supported or handled by app reset.
6. Whether device-owner kiosk mode is used or lightweight in-app kiosk mode is enough.
7. Whether check-in/check-out and multiple sessions are hidden behind advanced settings or shipped disabled.

---

## 16. External reference notes

1. ZepIris is useful as an architectural and model-pipeline reference for face authentication, especially around quality checks, face embeddings, and vector matching, but its published architecture is server-oriented and should not be used as the hard dependency for this fully offline on-device product unless ported or heavily adapted.
2. The production implementation should benchmark an on-device face detector and an on-device embedding model on the actual target Android tablet before finalizing thresholds.
