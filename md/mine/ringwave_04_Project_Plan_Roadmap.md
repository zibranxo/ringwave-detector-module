# Project Plan and Roadmap

**Project:** RingWave  
**Prepared for:** Internal engineering and product team  
**Prepared on:** 2026-06-06  
**Document status:** Draft for implementation planning

---

## 1. Delivery approach

RingWave is delivered across three phases:

**Phase 1 — Core calling foundation.** This phase establishes the entire WebRTC-based calling infrastructure: user auth, contacts, one-to-one audio calls, push notifications, and call history. The product ships as a functional calling app with no detection layer. This gives the team a stable base to verify calling quality independently before the detection layer is added.

**Phase 2 — Deepfake detection layer.** This phase adds the AI inference service, the audio tapping pipeline, the real-time score delivery system, and the in-call detection UI. The detection layer is integrated only after Phase 1 calls are stable and the ML model benchmarks are met.

**Phase 3 — Group calling and production hardening.** This phase adds the SFU-based group calling infrastructure, per-participant detection in group calls, operational hardening, load testing, and DPDP compliance verification before a production launch.

Each phase ends with a milestone review. Phase 1 must be fully tested before Phase 2 begins. Phase 2 must meet the model EER target before Phase 3 begins.

---

## 2. Workstreams

| ID | Workstream | Owner |
|---|---|---|
| WS-1 | Android application | Android engineer(s) |
| WS-2 | Backend: signaling and REST API | Backend engineer(s) |
| WS-3 | Backend: SFU media server | Backend engineer(s) |
| WS-4 | AI module: model training and evaluation | ML engineer(s) |
| WS-5 | AI module: inference service and pipeline | ML / backend engineer |
| WS-6 | Web dashboard | Frontend engineer(s) |
| WS-7 | Infrastructure and DevOps | DevOps engineer |
| WS-8 | QA and testing | QA engineer |

---

## 3. Milestones

### Phase 1 — Core calling foundation

| ID | Milestone | Workstreams | Target |
|---|---|---|---|
| M1 | Project setup, repo, CI/CD pipelines, dev environments | WS-7 | Week 1 |
| M2 | Auth API complete: register, OTP, login, token rotation, logout | WS-2 | Week 2 |
| M3 | Android auth screens complete: register, OTP, login, home | WS-1 | Week 3 |
| M4 | Contact API complete: search, request, accept, block, presence | WS-2 | Week 3 |
| M5 | Android contact screens complete: list, search, profile, requests | WS-1 | Week 4 |
| M6 | Signaling server complete: one-to-one call events, session state, STUN/TURN | WS-2 | Week 5 |
| M7 | SFU media server: one-to-one transport, audio routing, PlainTransport tap stub | WS-3 | Week 5 |
| M8 | Android WebRTC engine: SDP negotiation, ICE, audio, call screens | WS-1 | Week 6 |
| M9 | Android push notifications: FCM, ConnectionService, foreground service | WS-1 | Week 6 |
| M10 | Call history API and Android history screens | WS-2, WS-1 | Week 7 |
| M11 | Web dashboard Phase 1: auth, contacts, one-to-one calls | WS-6 | Week 7 |
| M12 | Phase 1 integration test and QA sign-off | WS-8 | Week 8 |

**Phase 1 gate:** All Phase 1 integration tests pass. One-to-one calls work reliably on physical Android devices and in the web dashboard. FCM push delivers incoming calls when the app is closed on a minimum of 5 test devices across different OEMs.

---

### Phase 2 — Deepfake detection layer

| ID | Milestone | Workstreams | Target |
|---|---|---|---|
| M13 | Dataset preparation: download and augment ASVspoof 2019/2021, WaveFake with VoIP augmentation | WS-4 | Week 9 |
| M14 | Feature extraction pipeline: LFCC extractor, data loader, augmentation pipeline | WS-4 | Week 10 |
| M15 | Model training: AASIST baseline trained on augmented dataset | WS-4 | Week 11 |
| M16 | Model evaluation: EER on ASVspoof 2021 eval set and VoIP-augmented eval set | WS-4 | Week 12 |
| M17 | Model EER target met (< 5% on ASVspoof 2021 LA) — Phase 2 gate check | WS-4 | Week 12 |
| M18 | ONNX export and INT8 quantization; inference time benchmark | WS-4, WS-5 | Week 13 |
| M19 | Python FastAPI inference service: queue consumer, model runner, score publisher | WS-5 | Week 13 |
| M20 | RabbitMQ setup; audio chunk queue and score queue integration | WS-5, WS-7 | Week 13 |
| M21 | SFU audio tap: PlainTransport → 16 kHz PCM → chunker → queue publisher | WS-3, WS-5 | Week 14 |
| M22 | Signaling server: score consumer, detection:score and detection:alert event emission | WS-2 | Week 14 |
| M23 | Android detection UI: in-call badge, alert banners, post-call report | WS-1 | Week 15 |
| M24 | Detection log API and Android detection report screen | WS-2, WS-1 | Week 15 |
| M25 | Web dashboard detection UI: badge, alerts, report page | WS-6 | Week 15 |
| M26 | End-to-end detection pipeline test: synthetic audio through full pipeline | WS-8 | Week 16 |
| M27 | Phase 2 integration test and QA sign-off | WS-8 | Week 16 |

**Phase 2 gate:** Model EER < 5% on ASVspoof 2021 LA. First detection score delivered within 5 seconds of speech start in a live test call. Synthetic audio (from WaveFake) triggers a suspicious or synthetic alert in a test call. False positive rate on genuine voice test calls < 3%.

---

### Phase 3 — Group calling and production hardening

| ID | Milestone | Workstreams | Target |
|---|---|---|---|
| M28 | SFU group call routing: Mediasoup Router, multi-transport, participant management | WS-3 | Week 17 |
| M29 | Signaling server group call events: create, join, add participant, leave, remove, end, host transfer | WS-2 | Week 17 |
| M30 | Android group call screens: participant list, per-participant detection badges, host controls | WS-1 | Week 18 |
| M31 | Web dashboard group call | WS-6 | Week 18 |
| M32 | Per-participant detection in group calls: independent audio streams for each participant | WS-3, WS-5 | Week 19 |
| M33 | Load testing: 500 concurrent calls, 50 simultaneous group calls | WS-8, WS-7 | Week 20 |
| M34 | AI inference load test: 500 concurrent chunk streams at < 500 ms | WS-8, WS-5 | Week 20 |
| M35 | DPDP Act compliance review: consent flow, data export, deletion, retention policy | WS-2, WS-1 | Week 20 |
| M36 | OEM push notification testing: top 5 Android OEMs in India (Xiaomi, Samsung, OnePlus, Realme, Vivo) | WS-1, WS-8 | Week 20 |
| M37 | Security review: transport, token lifecycle, rate limiting, penetration test | WS-7, WS-2 | Week 21 |
| M38 | Beta release: closed group of test users | All | Week 22 |
| M39 | Beta feedback triage and hotfix | All | Week 23 |
| M40 | Production release — canary 10% then 100% | WS-7 | Week 24 |

---

## 4. Responsibility matrix

| Area | Primary | Supporting |
|---|---|---|
| Android app | Android engineer | QA engineer |
| Backend API | Backend engineer | DevOps |
| SFU media server | Backend engineer | ML/Backend |
| AI model training | ML engineer | — |
| AI inference service | ML/Backend engineer | Backend engineer |
| Web dashboard | Frontend engineer | QA engineer |
| Infrastructure and CI/CD | DevOps engineer | Backend engineer |
| QA and testing | QA engineer | All workstreams |
| DPDP compliance | Backend engineer + legal review | Product |
| Security review | DevOps + external reviewer | Backend engineer |
| Documentation | All engineers | Product |

---

## 5. Engineering task breakdown by workstream

### WS-1 Android application

| Task | Phase | Week |
|---|---|---|
| Project setup: Kotlin, Jetpack Compose, MVVM, Hilt, Gradle | 1 | 1 |
| Auth screens: register, OTP, login | 1 | 3 |
| Auth ViewModel and repository: JWT, token storage in EncryptedSharedPreferences | 1 | 3 |
| Contact list, search, and profile screens | 1 | 4 |
| Contact ViewModel and API integration | 1 | 4 |
| WebRTC engine module: SDP, ICE, audio track | 1 | 6 |
| Outgoing call screen and ViewModel | 1 | 6 |
| Incoming call screen using ConnectionService | 1 | 6 |
| Active call screen: controls, timer, waveform | 1 | 6 |
| FCM service: high-priority push handler, full-screen intent | 1 | 6 |
| Android foreground service for active calls | 1 | 6 |
| Call history list and filter | 1 | 7 |
| Detection badge component: states, colors, tappable explanation | 2 | 15 |
| Alert banner component: suspicious and synthetic states | 2 | 15 |
| Socket.io detection:score and detection:alert event handler | 2 | 15 |
| Detection report screen: timeline chart, verdict, flag action | 2 | 15 |
| Group call screen: participant list, speaking indicator, host controls | 3 | 18 |
| Group call detection: per-participant badge updates | 3 | 19 |
| DTMF keypad bottom sheet | 1 | 7 |
| Settings screens: profile, presence, alert sensitivity, data export, account deletion | 1 | 7 |
| OEM-specific push notification testing and fixes | 3 | 20 |

### WS-2 Backend signaling and API

| Task | Phase | Week |
|---|---|---|
| Project setup: Node.js, Express, Socket.io, MongoDB, Redis | 1 | 1 |
| Auth endpoints: register, OTP, login, refresh, logout, account delete | 1 | 2 |
| JWT issuance and validation middleware | 1 | 2 |
| Refresh token rotation and revocation | 1 | 2 |
| Rate limiting middleware (express-rate-limit + Redis) | 1 | 2 |
| User profile and presence endpoints | 1 | 3 |
| Contact endpoints: search, request, accept, reject, block, remove | 1 | 3 |
| Socket.io signaling: one-to-one call events | 1 | 5 |
| Call session state management in Redis and MongoDB | 1 | 5 |
| TURN credential generation (time-limited HMAC) | 1 | 5 |
| Call history and call detail endpoints | 1 | 7 |
| RabbitMQ consumer for detection scores | 2 | 14 |
| detection:score and detection:alert Socket.io emission | 2 | 14 |
| Detection log flush on call end | 2 | 14 |
| Detection log endpoints: report, flag, delete | 2 | 15 |
| Group call signaling events: create, join, add, remove, end, host transfer | 3 | 17 |
| DPDP compliance: data export endpoint, deletion cascade | 3 | 20 |

### WS-3 SFU media server

| Task | Phase | Week |
|---|---|---|
| Mediasoup 3 setup: Worker, Router, WebRtcServer | 1 | 5 |
| One-to-one WebRtcTransport creation and ICE/DTLS parameters | 1 | 5 |
| Producer and Consumer creation for one-to-one audio | 1 | 5 |
| AudioLevelObserver for speaking detection | 1 | 6 |
| PlainTransport stub for audio tap | 1 | 5 |
| Audio tap module: PlainTransport → decode → 16 kHz PCM conversion | 2 | 14 |
| Chunker: sliding 1.5s window with 0.5s hop | 2 | 14 |
| RabbitMQ chunk publisher | 2 | 14 |
| Group call Router creation and multi-transport management | 3 | 17 |
| Per-participant producer/consumer pairs for group calls | 3 | 17 |
| Independent audio tap per participant stream in group calls | 3 | 19 |

### WS-4 AI module — model training

| Task | Phase | Week |
|---|---|---|
| Dataset download and preprocessing: ASVspoof 2019 LA, ASVspoof 2021 LA, WaveFake | 2 | 9 |
| Augmentation pipeline: Opus codec, MUSAN noise, RIR convolution | 2 | 9–10 |
| LFCC feature extractor implementation and validation | 2 | 10 |
| PyTorch DataLoader and training loop | 2 | 10 |
| AASIST model training on augmented dataset | 2 | 11 |
| EER evaluation on ASVspoof 2019 and 2021 eval sets | 2 | 12 |
| Internal VoIP-augmented benchmark evaluation | 2 | 12 |
| False positive evaluation on genuine call sample set | 2 | 12 |
| DET curve and threshold calibration | 2 | 12 |
| ONNX export and INT8 quantization | 2 | 13 |
| Inference time benchmark on target EC2 instance | 2 | 13 |
| Model versioning documentation and handoff to WS-5 | 2 | 13 |
| Quarterly model review cycle documentation | 3 | 21 |

### WS-5 AI inference service and pipeline

| Task | Phase | Week |
|---|---|---|
| Python FastAPI service setup | 2 | 13 |
| RabbitMQ consumer for audio chunks | 2 | 13 |
| ONNX Runtime integration for model inference | 2 | 13 |
| EMA smoothing and threshold classification logic | 2 | 13 |
| RabbitMQ score publisher | 2 | 13 |
| Silence detection logic (no audio for 10s → paused state) | 2 | 14 |
| Alert condition logic (two consecutive updates above threshold) | 2 | 14 |
| Inference service health check endpoint | 2 | 13 |
| Multi-worker configuration (one worker per CPU core) | 2 | 13 |
| Docker image and ECS Fargate task definition | 2 | 13 |
| Group call: multi-queue handling (one queue per participant stream) | 3 | 19 |
| Inference load test and worker scaling validation | 3 | 20 |

### WS-6 Web dashboard

| Task | Phase | Week |
|---|---|---|
| React project setup: TypeScript, TailwindCSS, WebRTC | 1 | 1 |
| Auth pages: register, OTP, login | 1 | 7 |
| Contact pages: list, search, profile, requests | 1 | 7 |
| WebRTC hook: SDP, ICE, audio | 1 | 7 |
| Active call page: controls, timer | 1 | 7 |
| Call history pages | 1 | 7 |
| Web Push registration and incoming call notification | 1 | 7 |
| Detection badge and alert banner components | 2 | 15 |
| Detection report page with timeline chart | 2 | 15 |
| Group call page with participant list | 3 | 18 |

### WS-7 Infrastructure and DevOps

| Task | Phase | Week |
|---|---|---|
| AWS environment setup: VPC, subnets, security groups | 1 | 1 |
| GitHub Actions CI/CD pipelines for all services | 1 | 1 |
| Docker Compose for local development environment | 1 | 1 |
| MongoDB Atlas cluster setup (ap-south-1, M10 tier, replica set) | 1 | 1 |
| Redis ElastiCache setup | 1 | 1 |
| ECR repositories and ECS Fargate task definitions | 1 | 1 |
| Coturn TURN server deployment on EC2, HMAC credentials | 1 | 5 |
| FCM service account configuration | 1 | 6 |
| AWS Secrets Manager integration for all services | 1 | 1 |
| CloudFront CDN for web dashboard | 1 | 7 |
| CloudWatch dashboards and alarms | 1 | 7 |
| RabbitMQ setup (Amazon MQ or self-hosted) | 2 | 13 |
| ECS auto-scaling policy for inference service | 2 | 13 |
| Load balancer for Socket.io (sticky sessions) | 1 | 5 |
| Production canary deployment setup | 3 | 23 |
| Rollback procedure documentation and drill | 3 | 23 |

---

## 6. Risk register

| ID | Risk | Impact | Probability | Mitigation | Owner |
|---|---|---|---|---|---|
| R-01 | AASIST inference time > 500 ms on target hardware | Detection latency > 5 s | Medium | Benchmark early (Week 13) before committing; fallback to LCNN is pre-planned | ML engineer |
| R-02 | VoIP augmented false positive rate > 3% | Users distrust detection | Medium | Augment training with Opus/GSM codecs; measure on internal VoIP benchmark before Phase 2 gate | ML engineer |
| R-03 | FCM fails to wake app on Xiaomi / Realme / OPPO OEMs | Users miss incoming calls | Medium | Test on 5 OEM devices in Week 20; implement background polling fallback | Android engineer |
| R-04 | Novel voice cloning tools render model obsolete | Detection misses new attacks | High (long-term) | Quarterly model review; user-flag feedback loop; benchmark against new WaveFake vocoders | ML engineer |
| R-05 | Mediasoup SFU audio tap adds perceptible call latency | Audio quality degradation | Low | Use PlainTransport zero-copy; benchmark tap overhead under load before Phase 3 | Backend engineer |
| R-06 | RabbitMQ queue backlog under peak load | Score delivery delays | Low | Auto-scale inference workers on queue depth; TTL on chunks (discard if > 5 s old) | DevOps, ML/Backend |
| R-07 | DPDP Act implementation rules change before launch | Compliance gap | Medium | Track MeitY notifications; legal review scheduled Week 20 | Product + legal |
| R-08 | TURN relay bandwidth cost exceeds infrastructure budget | Operational overspend | Medium | Monitor TURN relay percentage during beta; implement daily cap if needed | DevOps |
| R-09 | Phase 1 calling quality issues delay Phase 2 start | Schedule overrun by 2–3 weeks | Medium | Phase 1 gate must be passed before Phase 2 begins; buffer built into schedule | All |
| R-10 | MongoDB write throughput limit during call peaks | Detection logs lost | Low | Use Atlas auto-scaling; batch-write chunk arrays per call end | DevOps |
| R-11 | Web dashboard WebRTC compatibility differences across browsers | Web calls fail on some browsers | Low | Test on Chrome, Firefox, Safari (desktop) before launch; document unsupported browsers | Frontend engineer |

---

## 7. Dependencies

| Dependency | Required by | Notes |
|---|---|---|
| Firebase project with FCM enabled | WS-1, WS-6 (M9) | Must be set up before Week 6 |
| ASVspoof 2019 and 2021 dataset access | WS-4 (M13) | Register for dataset access; download may take 1–2 days |
| WaveFake dataset | WS-4 (M13) | Available on GitHub; large download |
| MUSAN noise dataset and RIR-Noisy | WS-4 (M13) | Required for augmentation |
| GPU compute for model training | WS-4 (M15) | AWS EC2 p3.2xlarge or equivalent; provision before Week 11 |
| Coturn TURN server | WS-3, WS-1 (M6, M8) | Must be live before call integration testing begins in Week 5 |
| MongoDB Atlas cluster | WS-2 (M2) | Must be live before auth API work; provision in Week 1 |
| AWS Secrets Manager | WS-7 (M1) | Required for all service deployments |
| ONNX Runtime | WS-5 (M18) | Must be benchmarked before inference service deployment |
| Legal review of DPDP consent notice | WS-2, WS-1 (M35) | Must be completed before beta release |

---

## 8. Definition of done

A feature is considered done when all of the following are true:

1. The feature is implemented and passes all relevant unit tests.
2. The feature is covered by an integration test in the QA suite.
3. The feature has been tested on at least two physical Android devices (different OEMs) by the QA engineer.
4. All API contracts and Socket.io events for the feature are documented in the Technical Specification.
5. No known P1 (critical) or P2 (major) bugs remain open against the feature.
6. The feature has been reviewed and approved by at least one other engineer in a pull request.

A milestone is considered done when all features in that milestone meet the definition of done above, and the QA engineer has signed off on that milestone's test results.

---

## 9. QA strategy and test environments

### 9.1 Environments

| Environment | Purpose | Refresh |
|---|---|---|
| Local (Docker Compose) | Individual developer testing | On demand |
| Dev | Continuous integration; runs on every PR merge | Automated on deploy |
| Staging | Pre-release integration and QA | On milestone completion |
| Production | Live users | Canary + full rollout |

### 9.2 Test data

The staging environment must be seeded with:
1. 20 test user accounts with varied contact graphs.
2. Pre-recorded call sessions with known detection verdicts for regression testing.
3. Synthetic voice audio samples from WaveFake for detection pipeline testing.
4. A test admin account for internal ML team monitoring.

### 9.3 Physical device test matrix (Android)

| Device | OEM | Android version |
|---|---|---|
| Redmi Note 13 | Xiaomi | MIUI 14 / Android 13 |
| Galaxy A54 | Samsung | One UI 5.1 / Android 13 |
| OnePlus Nord CE 3 | OnePlus | OxygenOS 13 |
| Realme 11 | Realme | Realme UI 4 / Android 13 |
| Pixel 7a | Google | Android 14 |

FCM high-priority push delivery must be verified on all five devices with the app in the foreground, background, and force-stopped states.

---

## 10. Release readiness checklist

The following must be complete before production release:

**Functionality:**
- [ ] All Phase 1, 2, and 3 milestones complete with QA sign-off
- [ ] One-to-one and group calls verified on all 5 test devices
- [ ] Detection pipeline tested end-to-end with both genuine and synthetic audio
- [ ] DTMF keypad working on all 5 test devices
- [ ] Call reconnection tested under simulated network drop
- [ ] Account deletion cascade verified

**Performance:**
- [ ] Load test: 500 simultaneous calls without degradation
- [ ] AI inference: < 500 ms per chunk at 95th percentile under 500 concurrent streams
- [ ] Call setup: < 3 s on 4G (tested on physical devices, not just Wi-Fi)
- [ ] App cold start: < 3 s on all 5 test devices

**Security:**
- [ ] Security review completed
- [ ] Penetration test completed (at minimum, OWASP API Security Top 10 coverage)
- [ ] All secrets confirmed in Secrets Manager, not in code or environment files
- [ ] Rate limiting verified on auth, OTP, and call initiation endpoints
- [ ] DTLS-SRTP verified as enforced in Mediasoup configuration

**Compliance:**
- [ ] DPDP Act legal review completed
- [ ] Consent notice reviewed and approved by legal
- [ ] Privacy policy published and linked from app
- [ ] Data export endpoint working and producing correct output
- [ ] Account deletion tested with full data cascade

**Operations:**
- [ ] CloudWatch dashboards and alarms active for all services
- [ ] Rollback procedure documented and rehearsed for each service
- [ ] On-call rotation established for first two weeks post-launch
- [ ] Canary deployment plan and success criteria defined
- [ ] Incident response runbook completed

---

## 11. Suggested implementation sequencing (first 8 weeks summary)

| Week | Focus |
|---|---|
| 1 | Infrastructure setup, repos, CI/CD, MongoDB, Redis, local Docker Compose |
| 2 | Auth API: register, OTP, login, tokens, rate limiting |
| 3 | Android auth screens; contact API |
| 4 | Android contact screens |
| 5 | Signaling server one-to-one events; Mediasoup setup; TURN server |
| 6 | Android WebRTC engine; call screens; FCM and ConnectionService |
| 7 | Call history; web dashboard Phase 1; DTMF; settings |
| 8 | Phase 1 integration test and QA sign-off |
