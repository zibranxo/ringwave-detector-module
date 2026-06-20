# FaceGate Attendance Documentation Package

Prepared on: 2026-06-04

This ZIP contains Markdown planning documents for an offline-first Android tablet face-matching attendance app for a school/camp setting.

## Files

1. `01_PRD_Product_Requirements_Document.md` — what the app should do and why.
2. `02_Technical_Specification_Document.md` — architecture, tech stack, API/service contracts, database schema, security, offline behavior, and implementation notes.
3. `03_UI_UX_Design_Document.md` — user flows, text wireframes, screens, feedback states, and design-system draft.
4. `04_Project_Plan_Roadmap.md` — workstreams, milestones, responsibilities, risk register, QA, and release readiness.
5. `05_Diagrams.md` — Mermaid diagrams for architecture, flows, matching logic, ERD, export, and security boundaries.

## Important architectural decision

The documents prioritize a native Android on-device implementation. ZepIris is treated as a useful reference, not a required production dependency, because the project must perform full face matching offline on the tablet.