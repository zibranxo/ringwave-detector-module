# Project Plan / Roadmap

**Project:** FaceGate Attendance  
**Prepared for:** Internal product and engineering team  
**Prepared on:** 2026-06-04  
**Document status:** Draft for implementation planning

---

## 1. Delivery approach

The product should be built as an enterprise-grade offline Android application from the start. The roadmap is not structured as an MVP with reduced capability; it is structured as parallel workstreams leading to a production-ready release.

The implementation team should prioritize the highest-risk items first: on-device face-recognition accuracy, latency on target hardware, local encryption, and enrollment quality. UI and reporting work can proceed in parallel once the data model and recognition contracts are stable.

---

## 2. Recommended workstreams

| Workstream | Owner profile | Outcome |
|---|---|---|
| Product and requirements | Product owner / tech lead | Finalized scope, rules, acceptance criteria |
| Android app foundation | Android engineer | App shell, navigation, kiosk mode, admin mode |
| Camera and ML pipeline | Android ML engineer | CameraX, detection, embedding, matching |
| Local data and security | Android/backend engineer | Encrypted DB, Room schema, audit logs, keys |
| Enrollment and student management | Android engineer | Roster import, student CRUD, template management |
| Attendance and conflict engine | Android engineer | Auto marking, daily rules, conflicts, manual edits |
| Reporting and export | Android engineer | Excel export, reports, summaries |
| UI/UX implementation | Product designer + Android engineer | Kiosk and admin UI |
| QA and field validation | QA engineer | Device testing, recognition testing, offline testing |
| Deployment and operations | DevOps/support engineer | Device setup, kiosk provisioning, backups, handover |

---

## 3. Milestones

### Milestone 1 — Product and technical lock

Deliverables:

1. Finalized attendance rules.
2. Finalized enrollment process.
3. Finalized import/export formats.
4. Confirmed target Android tablet model.
5. Confirmed kiosk-mode strategy.
6. Confirmed data-retention and biometric-consent handling.
7. Approved PRD and technical specification.

Exit criteria:

1. Engineering can build without major unresolved workflow questions.
2. Target device is available for benchmark testing.
3. App name, package name, and deployment model are confirmed.

### Milestone 2 — ML and hardware benchmark

Deliverables:

1. CameraX proof-of-concept on target tablet.
2. Face detection benchmark.
3. Face embedding model benchmark.
4. Matching benchmark with 100, 250, and 500 student-template simulations.
5. Lighting, blur, side-face, and glasses test results.
6. Initial threshold recommendations.
7. Decision on final model/runtime.

Exit criteria:

1. End-to-end scan can complete under one second under normal conditions.
2. Selected model is legally usable in the product.
3. False rejection and false acceptance tradeoffs are documented.
4. Enrollment-quality gates are validated.

### Milestone 3 — App foundation and security

Deliverables:

1. Android app shell.
2. Kiosk screen route.
3. Admin login route.
4. Local encrypted database setup.
5. Android Keystore integration.
6. Admin password hashing.
7. Audit-log framework.
8. Device ID generation.
9. App settings store.

Exit criteria:

1. App works offline from first launch after setup.
2. Admin mode is password protected.
3. Database encryption is verified.
4. Audit logs can be written and queried.

### Milestone 4 — Student roster and enrollment

Deliverables:

1. Student list, search, filters, profile.
2. Add/edit/deactivate student.
3. Roster XLSX/CSV import with validation.
4. Camera enrollment flow with multiple samples.
5. Passport-image enrollment flow.
6. Poor-image rejection.
7. Duplicate enrollment warning.
8. Template update/deactivation.

Exit criteria:

1. Admin can import 100+ students.
2. Admin can enroll a student using the tablet camera.
3. Admin can enroll from one passport-style image.
4. Poor enrollment images are rejected.
5. Duplicate-risk enrollment creates a warning.

### Milestone 5 — Attendance kiosk and recognition

Deliverables:

1. Camera preview with oval guide.
2. Auto-capture logic.
3. Manual capture fallback.
4. On-device face detection.
5. On-device embedding generation.
6. Local matching engine.
7. Daily attendance rules.
8. Success state with green oval, name, and sound.
9. Red warning states with corrective copy.
10. Already-marked handling.

Exit criteria:

1. A properly enrolled student can mark attendance without admin intervention.
2. Duplicate same-day marking is prevented.
3. Multiple faces, no face, blur, low light, and side face are handled.
4. The app returns to scan mode automatically after success.

### Milestone 6 — Conflict resolution and manual edits

Deliverables:

1. Recognition-attempt logging.
2. Low-confidence handling.
3. Ambiguous-match handling.
4. Conflict queue.
5. Conflict detail screen.
6. Conflict resolution actions.
7. Manual attendance editing.
8. Reason-required edit dialog.
9. Audit logs for all admin actions.

Exit criteria:

1. Ambiguous matches are not auto-marked.
2. Admin can resolve or dismiss conflicts.
3. Admin can manually edit attendance with reason.
4. Every manual or conflict-driven change is auditable.

### Milestone 7 — Holidays, reports, and Excel export

Deliverables:

1. Holiday management.
2. Holiday-aware kiosk behavior.
3. Attendance report preview.
4. Date-range selection.
5. Excel export generation.
6. Export sheets: Summary, Attendance Matrix, Daily Logs, Students, Manual Edits & Audit, Holidays, Conflicts.
7. Export audit logging.
8. Export error handling.

Exit criteria:

1. Admin can define holidays.
2. Holiday dates are excluded or marked correctly.
3. Admin can export clean Excel attendance records for any date range.
4. Export works without internet.

### Milestone 8 — Kiosk hardening and device operations

Deliverables:

1. Lock Task Mode support where available.
2. In-app kiosk fallback.
3. Admin-only kiosk exit.
4. App restart recovery.
5. Local diagnostics screen.
6. Storage usage warning.
7. Backup/export operating procedure.
8. Device setup checklist.

Exit criteria:

1. Student users cannot access admin screens without password.
2. App returns to kiosk mode after restart/resume.
3. Admin can inspect diagnostics and export data.
4. Device setup can be repeated by support staff.

### Milestone 9 — QA, security review, and field validation

Deliverables:

1. Unit test suite.
2. Instrumented Android test suite.
3. ML benchmark report.
4. Offline test report.
5. Security review report.
6. Field test with representative students.
7. Bug-fix closure.
8. Release candidate build.

Exit criteria:

1. Critical and high-severity defects are closed.
2. Offline operation is verified for long-duration simulation.
3. Recognition latency target is met on target hardware.
4. Export accuracy is verified against manual spot checks.
5. Data-at-rest encryption is verified.

### Milestone 10 — Production release and handover

Deliverables:

1. Signed production build.
2. Admin user guide.
3. Device setup guide.
4. Emergency recovery guide.
5. QA sign-off.
6. Product sign-off.
7. Deployment checklist.
8. Support handover.

Exit criteria:

1. Production APK/AAB is signed and archived.
2. Device is provisioned and tested.
3. Admin knows how to enroll, export, resolve conflicts, and set holidays.
4. Support team knows how to diagnose common failures.

---

## 4. Responsibility matrix

| Area | Product Owner | Android Engineer | ML Engineer | QA | Support/Ops |
|---|---|---|---|---|---|
| Attendance rules | Accountable | Consulted | Consulted | Consulted | Consulted |
| UI flows | Accountable | Responsible | Consulted | Consulted | Consulted |
| Camera pipeline | Consulted | Responsible | Responsible | Consulted | Informed |
| Model selection | Consulted | Responsible | Accountable | Consulted | Informed |
| Local database | Consulted | Accountable | Consulted | Consulted | Informed |
| Encryption | Consulted | Accountable | Consulted | Consulted | Consulted |
| Import/export | Accountable | Responsible | Informed | Consulted | Consulted |
| Conflict engine | Accountable | Responsible | Responsible | Consulted | Consulted |
| QA scenarios | Consulted | Consulted | Consulted | Accountable | Consulted |
| Deployment | Informed | Consulted | Informed | Consulted | Accountable |

---

## 5. Engineering task breakdown

### 5.1 Android foundation

1. Create Kotlin Android project.
2. Configure Compose navigation.
3. Add app architecture layers.
4. Add dependency injection.
5. Add Room entities and DAOs.
6. Add encrypted database layer.
7. Add admin authentication.
8. Add audit-log infrastructure.
9. Add app settings.
10. Add diagnostics base screen.

### 5.2 Camera and ML

1. Build CameraX preview.
2. Add ImageAnalysis pipeline.
3. Add face detector integration.
4. Add oval-position validation.
5. Add quality checks.
6. Add embedding model runtime.
7. Add embedding normalization.
8. Add matching engine.
9. Add threshold decision logic.
10. Add latency telemetry.

### 5.3 Enrollment

1. Build student list and profile.
2. Add roster import.
3. Add manual student create/edit.
4. Build camera enrollment steps.
5. Build image-import enrollment.
6. Add quality rejection.
7. Add duplicate-risk detection.
8. Add template replacement/deactivation.
9. Add audit logs.

### 5.4 Attendance

1. Build kiosk UI.
2. Add auto-capture.
3. Add manual capture.
4. Add recognition-to-attendance transaction.
5. Add one-per-day constraint.
6. Add already-marked logic.
7. Add green/red states.
8. Add sound feedback.
9. Add holiday-aware kiosk state.

### 5.5 Admin reports

1. Build dashboard.
2. Build attendance date-range report.
3. Build attendance matrix query.
4. Build manual edit flow.
5. Build conflict queue.
6. Build conflict detail and resolution.
7. Build holiday management.
8. Build Excel export.
9. Build export history.

### 5.6 QA and release

1. Add automated unit tests.
2. Add test data fixtures.
3. Add instrumented app tests.
4. Run target-device benchmark.
5. Run offline simulation.
6. Run security checks.
7. Fix release blockers.
8. Prepare signed release.

---

## 6. Risk register

| ID | Risk | Probability | Impact | Mitigation | Owner |
|---|---|---:|---:|---|---|
| R-01 | On-device model is not accurate enough for students in real camp conditions | Medium | High | Benchmark multiple models with representative student data before final release | ML Engineer |
| R-02 | Target tablet cannot meet less-than-one-second recognition | Medium | High | Benchmark early, optimize frame size, quantize model, preload runtime | Android/ML Engineer |
| R-03 | Similar-looking students cause wrong attendance | Medium | High | Use ambiguity margin, conflict queue, duplicate enrollment warning | ML Engineer |
| R-04 | Poor enrollment creates repeated false rejection | High | High | Guided multi-sample enrollment and quality gates | Product/ML Engineer |
| R-05 | No liveness detection permits photo spoof | Medium | Medium | Document accepted tradeoff; optionally add liveness later | Product Owner |
| R-06 | Device is lost or stolen | Low | High | Encrypt DB, require device lock, protect keys | Android Engineer/Ops |
| R-07 | Admin forgets password | Medium | Medium | Define recovery/reset process before deployment | Product/Ops |
| R-08 | Export is incorrect or misunderstood | Medium | High | Validate against manual samples; include legend and audit sheets | QA/Product |
| R-09 | Kiosk mode not enforceable on chosen device | Medium | Medium | Test Lock Task Mode; provide in-app fallback | Android/Ops |
| R-10 | Legal/privacy requirements are incomplete | Medium | High | Review consent, retention, deletion, and privacy notice with legal counsel in India | Product Owner |
| R-11 | App storage fills after long use | Low | Medium | Avoid raw frames, provide storage diagnostics, export/delete workflows | Android Engineer |
| R-12 | Model upgrade invalidates templates | Medium | High | Version model and templates; require re-enrollment or migration plan | ML Engineer |
| R-13 | Admin manually edits attendance incorrectly | Medium | Medium | Require reason, audit logs, report change history | Product/Android |
| R-14 | Bulk roster import has bad data | High | Medium | Preview import, validate duplicates, create error report | Android Engineer |
| R-15 | App crashes during attendance queue | Medium | High | Automated tests, transaction safety, restart recovery | QA/Android |

---

## 7. Dependencies

### 7.1 Technical dependencies

1. Target Android tablet procurement.
2. CameraX compatibility verification.
3. On-device face detector selection.
4. On-device embedding model selection.
5. Encryption library finalization.
6. XLSX import/export library finalization.
7. Kiosk/device-owner provisioning approach.

### 7.2 Product dependencies

1. Final roster file format.
2. Consent/privacy text.
3. Attendance export expectations.
4. Admin password recovery policy.
5. Device setup and support ownership.

---

## 8. Definition of done

A work item is done only when:

1. It is implemented.
2. It works offline.
3. It has unit or instrumented tests where applicable.
4. It handles expected error states.
5. It writes audit logs if it changes sensitive data.
6. It does not expose student or biometric data without admin authentication.
7. It has been tested on the target tablet or representative budget device.
8. Product acceptance criteria are satisfied.

---

## 9. Release readiness checklist

### Product readiness

- [ ] Attendance rules confirmed.
- [ ] Enrollment method confirmed.
- [ ] Holiday behavior confirmed.
- [ ] Export format approved.
- [ ] Conflict-resolution behavior approved.
- [ ] Consent/privacy handling approved.

### Engineering readiness

- [ ] App works fully offline.
- [ ] Face recognition works on target tablet.
- [ ] End-to-end result is under one second in normal conditions.
- [ ] Database encryption verified.
- [ ] Admin password is hashed and protected.
- [ ] Kiosk mode tested.
- [ ] Manual edits audit logged.
- [ ] Export generation tested.
- [ ] App restart recovery tested.

### QA readiness

- [ ] Unit tests pass.
- [ ] Instrumented tests pass.
- [ ] Field scenarios pass.
- [ ] Import validation tested.
- [ ] Export accuracy tested.
- [ ] Conflict scenarios tested.
- [ ] Low light and blur scenarios tested.
- [ ] Multiple-face scenario tested.
- [ ] Same-day duplicate scenario tested.

### Operations readiness

- [ ] Device setup guide complete.
- [ ] Admin guide complete.
- [ ] Recovery procedure complete.
- [ ] Signed build archived.
- [ ] Support contact/process defined.
- [ ] Backup/export process defined.

---

## 10. Suggested implementation sequencing

Although the product is enterprise-grade from day one, engineering should reduce risk by sequencing work in this order:

1. Confirm hardware and recognition performance.
2. Build secure local data foundation.
3. Build enrollment and template storage.
4. Build kiosk attendance loop.
5. Build admin workflows.
6. Build export and audit completeness.
7. Harden kiosk and offline reliability.
8. Complete field QA and release.

This sequencing does not reduce final scope; it ensures that the most uncertain technical risks are resolved early.

---

## 11. Acceptance criteria summary

The release is acceptable when:

1. A properly enrolled student can mark attendance automatically on the tablet without internet.
2. The green success state shows the student name and plays a short sound.
3. The app blocks or warns for no face, multiple faces, blur, poor light, side face, low confidence, and ambiguous matches.
4. The app prevents duplicate attendance for the same student on the same day.
5. Admin can import students, enroll/update faces, set holidays, edit attendance, resolve conflicts, and export Excel reports.
6. Manual edits and admin-sensitive actions are audit logged.
7. The local database and biometric templates are encrypted.
8. The app remains usable after weeks offline.
9. Kiosk mode prevents student access to admin functions.
10. QA has validated the app on the target budget Android tablet.
