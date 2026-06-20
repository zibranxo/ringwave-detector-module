# PRD — Product Requirements Document

**Project:** RingWave  
**Prepared for:** Internal product and engineering team  
**Prepared on:** 2026-06-06  
**Document status:** Draft for implementation planning

---

## 1. Product summary

RingWave is an internet audio calling platform for Android and web that combines real-time voice communication with an AI-powered voice authenticity layer. Users can register, search contacts, and place one-to-one or group audio calls over WebRTC. During every call, an on-server deepfake detection engine continuously analyzes each participant's audio stream and surfaces an authenticity score — classified as likely real, suspicious, or likely synthetic — directly within the call UI. If the score crosses a suspicious or synthetic threshold during a call, the app shows a non-disruptive alert so the user can make an informed decision about the conversation.

The product targets individual users who are aware of voice cloning threats and want a calling platform that gives them an authenticity signal. The Android app is the primary delivery surface. A React web dashboard provides the secondary access point with identical calling and detection capability.

---

## 2. Problem statement

Voice cloning technology is now widely accessible and is being actively used for fraud. An attacker can clone a target's voice from a few seconds of public audio, then impersonate that person in a phone call with high fidelity. Existing calling applications — including consumer VoIP apps and cellular calls — provide no mechanism to identify synthetic or cloned voices during a live call. A user has no way of knowing whether the voice they are hearing is genuine.

Common fraud vectors that RingWave directly addresses:

1. Impersonation of a family member in a distress or emergency scenario.
2. Impersonation of a company executive to authorize a financial transaction.
3. Fake customer support calls using a cloned brand voice.
4. Social engineering using a synthesized version of a trusted contact's voice.
5. Identity theft through synthesized speech in verification calls.

---

## 3. Goals

1. Enable one-to-one and group internet audio calling over WebRTC on Android and web.
2. Continuously analyze each participant's audio stream during a call and generate an authenticity score.
3. Surface the authenticity score in the call UI, updating every one to two seconds.
4. Alert the user when the score crosses a suspicious or synthetic threshold in a non-disruptive way that does not interrupt the call.
5. Record a full detection log for every call so the user can review the score timeline post-call.
6. Reach the AI model's first authenticity score within five seconds of sustained speech starting.
7. Provide a complete contact management system with presence awareness, contact requests, and blocking.
8. Deliver incoming call notifications reliably on Android even when the app is not in the foreground.
9. Store call history, detection logs, and user flags to support both the user experience and model improvement over time.
10. Comply with the Indian Digital Personal Data Protection Act, 2023 for all personal and voice-analysis data.

---

## 4. Non-goals

The following are explicitly out of scope for the first production release:

1. Video calling or video deepfake detection.
2. End-to-end encryption of call audio at the application layer. DTLS-SRTP protects media in transit; application-layer E2EE is a future milestone.
3. iOS application. iOS is a stretch goal and may be planned after Android reaches production.
4. Voice biometric authentication for login.
5. On-device deepfake detection inference. The detection model runs server-side.
6. Scam or spam call detection beyond voice authenticity scoring.
7. Sentiment analysis or speech transcription.
8. Multi-tenancy or enterprise deployment with organizational user management.
9. Call recording for playback purposes. Audio is analyzed in transit and not stored.
10. Real-time speech translation or multilingual captions.

---

## 5. Target users

### 5.1 End user — caller and callee

The primary user is an individual who installs RingWave to make internet audio calls. The user is aware of voice cloning risks or has encountered coverage of voice fraud. The user expects a calling experience similar to WhatsApp or Signal, with an additional authenticity layer they can see during and after calls. The user does not need to understand how the detection works; they need to trust and act on the score it produces.

### 5.2 Internal engineering and ML team

The internal team is responsible for training and evaluating the deepfake detection model, operating the backend infrastructure, monitoring detection accuracy in production, processing user-flagged detection errors, and retraining the model when false positive or false negative rates exceed acceptable targets.

### 5.3 Internal operations and support

The operations team is responsible for infrastructure deployment, monitoring server health, responding to service degradation incidents, and managing user account issues that require backend intervention.

---

## 6. Operating context

| Area | Requirement |
|---|---|
| Primary platform | Android (Kotlin, Jetpack Compose, MVVM) |
| Secondary platform | Web browser (React.js, WebRTC) |
| Connectivity | Always-online. All calling and detection require active internet. |
| Call types | One-to-one audio, group audio (up to 8 participants) |
| Detection mode | Server-side real-time streaming analysis during active call |
| Notification delivery | FCM push for Android; Web Push for browser |
| Primary market | India |
| Regulatory context | Indian DPDP Act, 2023 |
| Backend deployment | AWS (Node.js signaling server, Python AI service, MongoDB Atlas) |
| Media topology | SFU (Selective Forwarding Unit) for group calls; direct peer-to-peer for one-to-one where NAT permits, TURN relay as fallback |

---

## 7. Product assumptions

1. Call audio is processed server-side for deepfake analysis and is not stored after the call ends. Only the scores and timestamps are persisted in detection logs.
2. Users explicitly consent at registration to voice stream analysis for the purpose of deepfake detection.
3. Each user account is tied to a verified phone number or email address.
4. The AI inference service may occasionally be unavailable due to maintenance or overload. When unavailable, calls proceed normally and the detection indicator shows "analysis unavailable" rather than a score.
5. Group calls use a Selective Forwarding Unit architecture. Peer-to-peer mesh is not used for groups because it is not scalable beyond three to four participants.
6. The deepfake detection model is trained on ASVspoof and WaveFake benchmark datasets with VoIP-specific augmentation and will require periodic retraining as voice cloning technology evolves.
7. The Android app targets Android 8.0 (API 26) and above to ensure ConnectionService API support for system-level incoming call UI.
8. DTLS-SRTP is the baseline for media encryption in transit. Application-layer end-to-end encryption is a future scope item.

---

## 8. Core calling experience

### 8.1 Outgoing call flow

1. User navigates to a contact or searches for a user.
2. User taps the call button.
3. App generates a WebRTC SDP offer and sends a `call:initiate` event to the signaling server.
4. Signaling server delivers a `call:incoming` event to the callee.
5. Calling screen shows ringing state with caller name and avatar.
6. If callee accepts within 30 seconds, the app exchanges SDP answer and ICE candidates.
7. Audio connection is established and both parties hear each other.
8. Detection indicator appears on the active call screen and begins updating.
9. Call ends when either party taps end, the network drops unrecoverably, or the session times out.

### 8.2 Incoming call flow

1. Callee receives an FCM high-priority push notification (device locked or app closed).
2. Android ConnectionService API triggers the system-level incoming call screen.
3. Callee accepts or rejects the call.
4. If accepted, the app opens the active call screen and establishes WebRTC audio.
5. If rejected, the caller sees a "call rejected" state.
6. If not answered within 30 seconds, the call is marked as missed and a missed call notification is shown.

### 8.3 Group call flow

1. User creates a group call and selects participants from contacts.
2. Each invited participant receives an incoming call notification.
3. As participants accept, they join the SFU session and their audio stream is forwarded to all other participants.
4. The detection indicator shows a per-participant score row.
5. The host sees additional controls: mute a participant, remove a participant, end call for everyone.
6. Any participant can add further contacts up to the eight-participant limit.
7. If the host leaves, host role transfers to the next participant in join order.

### 8.4 Deepfake detection experience

1. As soon as audio is flowing in a call, the media server taps each participant's RTP stream.
2. Audio is normalized to 16 kHz mono PCM and segmented into 1.5-second overlapping chunks.
3. Each chunk is dispatched to the Python AI inference service via a message queue.
4. The model returns a raw confidence score (0.0 to 1.0, where 1.0 is maximally synthetic).
5. Scores are smoothed using an exponential moving average and classified into real, suspicious, or synthetic.
6. The signaling server emits `detection:score` to the relevant client every one to two seconds.
7. The call screen updates the detection badge color: green for real, amber for suspicious, red for synthetic.
8. If the score crosses the suspicious threshold and holds for two consecutive updates, a non-disruptive banner alert is shown once per threshold crossing per call.
9. After the call ends, a detection summary is stored as a log and is accessible from call history.

---

## 9. Functional requirements

### 9.1 User authentication

| ID | Requirement | Priority |
|---|---|---|
| FR-A01 | The app shall allow a new user to register with a phone number or email address and a password. | Must |
| FR-A02 | The app shall require OTP verification of the phone number or email address before activating the account. | Must |
| FR-A03 | The app shall allow a registered user to log in with their credentials. | Must |
| FR-A04 | The backend shall issue a short-lived JWT access token (15-minute expiry) and a rotating refresh token (7-day expiry) on successful login. | Must |
| FR-A05 | The app shall silently refresh the access token using the refresh token before it expires. | Must |
| FR-A06 | Logging out shall revoke the current refresh token server-side. | Must |
| FR-A07 | The app shall allow the user to delete their account, which removes all personal data, call history, and detection logs. | Must |
| FR-A08 | The backend shall rate-limit login and OTP endpoints to prevent brute-force attacks. | Must |
| FR-A09 | The app shall display a consent notice at registration explaining that call audio is analyzed for deepfake detection and is not stored. | Must |

### 9.2 User profile and presence

| ID | Requirement | Priority |
|---|---|---|
| FR-P01 | The app shall allow the user to set a display name and avatar. | Must |
| FR-P02 | The app shall allow the user to set a username that other users can search by. | Must |
| FR-P03 | The app shall display the user's presence status to contacts: online, offline, busy, or do-not-disturb. | Must |
| FR-P04 | The app shall allow the user to manually set their presence status. | Must |
| FR-P05 | The app shall automatically set presence to offline when the app is backgrounded for more than five minutes. | Should |

### 9.3 Contact management

| ID | Requirement | Priority |
|---|---|---|
| FR-C01 | The app shall allow the user to search for other registered users by username or phone number. | Must |
| FR-C02 | The app shall allow the user to send a contact request to another user. | Must |
| FR-C03 | The app shall allow the recipient to accept or decline a contact request. | Must |
| FR-C04 | The app shall display the user's accepted contact list with presence indicators. | Must |
| FR-C05 | The app shall allow the user to block a contact, preventing that contact from calling or searching for them. | Must |
| FR-C06 | The app shall allow the user to unblock a previously blocked contact. | Must |
| FR-C07 | The app shall allow the user to remove a contact from their list. | Must |
| FR-C08 | The app shall notify the user of pending incoming contact requests. | Must |

### 9.4 One-to-one audio call

| ID | Requirement | Priority |
|---|---|---|
| FR-CA01 | The app shall allow the user to initiate an outgoing audio call to any accepted contact. | Must |
| FR-CA02 | The app shall show a ringing state to the caller while waiting for the callee to answer. | Must |
| FR-CA03 | The callee shall receive an incoming call notification via FCM even when the app is closed. | Must |
| FR-CA04 | The app shall present the system-level incoming call screen using the Android ConnectionService API. | Must |
| FR-CA05 | The app shall allow the callee to accept or reject an incoming call. | Must |
| FR-CA06 | The app shall mark a call as missed if the callee does not answer within 30 seconds. | Must |
| FR-CA07 | The app shall allow either party to end the call at any time. | Must |
| FR-CA08 | The app shall allow the user to mute and unmute their own microphone during a call. | Must |
| FR-CA09 | The app shall allow the user to toggle the speakerphone on and off. | Must |
| FR-CA10 | The app shall allow the user to place the call on hold and resume it. | Must |
| FR-CA11 | The app shall show a DTMF keypad during a call for numeric input. | Must |
| FR-CA12 | If the user receives an incoming call while already on a call, the app shall show a call-waiting notification. The user may reject the new call or end the current call to answer. | Should |
| FR-CA13 | The app shall attempt automatic reconnection for up to 30 seconds if the network drops during an active call before marking the call as dropped. | Must |

### 9.5 Group audio call

| ID | Requirement | Priority |
|---|---|---|
| FR-GC01 | The app shall allow the user to create a group call by selecting multiple contacts. | Must |
| FR-GC02 | Each invited participant shall receive an incoming call notification. | Must |
| FR-GC03 | The call shall connect with any subset of invited participants who accept. | Must |
| FR-GC04 | The group call shall support a maximum of 8 participants simultaneously. | Must |
| FR-GC05 | The app shall allow any participant to add a further contact to an ongoing group call, up to the 8-participant limit. | Must |
| FR-GC06 | The app shall display a participant list showing each participant's name, mute state, and active-speaking indicator. | Must |
| FR-GC07 | The host shall be able to mute any individual participant. | Must |
| FR-GC08 | The host shall be able to remove any participant from the call. | Must |
| FR-GC09 | The host shall be able to end the call for all participants. | Must |
| FR-GC10 | If the host leaves the call without ending it, host role shall transfer to the participant who joined next after the original host. | Must |
| FR-GC11 | The app shall allow any participant to leave a group call without ending it for others. | Must |

### 9.6 Deepfake detection

| ID | Requirement | Priority |
|---|---|---|
| FR-DD01 | The system shall begin analyzing audio for each call participant as soon as audio is flowing. | Must |
| FR-DD02 | The system shall produce a first authenticity score within 5 seconds of sustained speech starting. | Must |
| FR-DD03 | The system shall update the displayed authenticity score every 1 to 2 seconds during active speech. | Must |
| FR-DD04 | The system shall classify each score into one of three verdicts: likely real (score < 0.35), suspicious (score 0.35–0.65), or likely synthetic (score > 0.65). | Must |
| FR-DD05 | The system shall apply exponential moving average smoothing to raw chunk scores before displaying them, to prevent rapid flickering. | Must |
| FR-DD06 | The app shall display an authenticity badge for each participant visible throughout the active call. | Must |
| FR-DD07 | The app shall show a non-disruptive in-call banner alert when a participant's score first crosses the suspicious threshold and holds for two consecutive updates. | Must |
| FR-DD08 | The app shall show a distinct non-disruptive in-call banner alert when a participant's score crosses the synthetic threshold. | Must |
| FR-DD09 | In a group call, the system shall analyze each participant's audio stream independently and show a per-participant detection badge. | Must |
| FR-DD10 | If the AI inference service is unavailable, the call shall proceed normally and the detection badge shall show "analysis unavailable" rather than a score. | Must |
| FR-DD11 | The app shall allow the user to tap the detection badge to view a brief explanation of what the score means. | Must |

### 9.7 Call history

| ID | Requirement | Priority |
|---|---|---|
| FR-CH01 | The app shall record every call with participant identities, call type, start time, end time, duration, and call status. | Must |
| FR-CH02 | The app shall display a call history list with the ability to filter by all, missed, incoming, and outgoing. | Must |
| FR-CH03 | Each call history entry shall show the overall authenticity verdict for that call. | Must |
| FR-CH04 | The user shall be able to open a full detection report from any call history entry. | Must |
| FR-CH05 | The user shall be able to delete individual call history entries, which also deletes the associated detection log. | Must |

### 9.8 Detection logs and reporting

| ID | Requirement | Priority |
|---|---|---|
| FR-DL01 | The system shall store a detection log for every completed call, including per-chunk raw scores, smoothed scores, and timestamps. | Must |
| FR-DL02 | Each detection log record shall store the model version that produced the scores. | Must |
| FR-DL03 | The app shall display the detection report as a score timeline chart for the call duration. | Must |
| FR-DL04 | The report shall show the overall verdict and the peak score reached during the call. | Must |
| FR-DL05 | The user shall be able to flag a detection report as incorrect. The flag shall be stored and surfaced to the internal ML team. | Must |
| FR-DL06 | Detection logs shall be deleted when the user deletes the associated call history entry or when the account is deleted. | Must |

### 9.9 Push notifications and background behavior

| ID | Requirement | Priority |
|---|---|---|
| FR-NF01 | The app shall deliver incoming call notifications via FCM high-priority push even when the app process is not running. | Must |
| FR-NF02 | The app shall use the Android ConnectionService API to show the system incoming call screen for incoming calls. | Must |
| FR-NF03 | The app shall run audio and signaling in an Android foreground service for the duration of an active call. | Must |
| FR-NF04 | The app shall send a missed call notification when a call is not answered within the timeout. | Must |
| FR-NF05 | The app shall send a post-call notification summarizing the detection verdict when the call ends, if the verdict was suspicious or synthetic. | Should |
| FR-NF06 | The web dashboard shall use the Web Push API to deliver incoming call notifications in the browser. | Must |

### 9.10 Web dashboard

| ID | Requirement | Priority |
|---|---|---|
| FR-WD01 | The web dashboard shall provide the same user registration, login, and profile management as the Android app. | Must |
| FR-WD02 | The web dashboard shall support one-to-one and group audio calling with identical detection capability. | Must |
| FR-WD03 | The web dashboard shall show the in-call detection badge and alerts identically to the Android app. | Must |
| FR-WD04 | The web dashboard shall display call history and detection reports. | Must |
| FR-WD05 | The web dashboard shall support Web Push notifications for incoming calls on desktop browsers. | Must |

---

## 10. Edge cases and conflict handling

1. If both parties initiate a call to each other simultaneously, the signaling server shall detect the collision and accept one call session while notifying both parties that their call is connecting.
2. If a participant's audio stream is silent for more than 10 consecutive seconds, the detection badge shall show a paused state rather than maintaining the last score, because silence does not contain analyzable voice characteristics.
3. If a participant joins a group call after it has started, detection begins for that participant's stream from the moment they join.
4. If the deepfake model produces a score above 0.9 on two consecutive chunks, the system shall log this as a high-confidence synthetic event regardless of the smoothed display score, for post-call audit purposes.
5. If the score fluctuates across the suspicious threshold repeatedly within a single call, the alert banner shall be shown only on the first crossing and on the first synthetic crossing, not on every fluctuation.
6. If a user's account is deleted while they are on an active call, the call shall be ended with reason "user unavailable" and the other participants shall see a notification.

---

## 11. Data requirements

### 11.1 User data

Minimum user fields:

1. User ID.
2. Username.
3. Phone number or email address (at least one required).
4. Password hash and salt.
5. Display name.
6. Avatar URL.
7. Presence status.
8. Account verification status.
9. Account active status.
10. Created timestamp.
11. Updated timestamp.

### 11.2 Call session data

Minimum call session fields:

1. Session ID.
2. Session type: one-to-one or group.
3. Initiator user ID.
4. Participant list: user ID, join timestamp, leave timestamp, participation status.
5. Session status: ringing, connected, on-hold, ended, missed, rejected, dropped.
6. Started timestamp.
7. Connected timestamp.
8. Ended timestamp.
9. Duration in seconds.
10. End reason: normal, missed, rejected, network-drop, error.

### 11.3 Detection log data

Minimum detection log fields:

1. Log ID.
2. Session ID.
3. Participant user ID.
4. Model name and version.
5. Chunk records: start timestamp, end timestamp, raw score, smoothed score.
6. Overall verdict.
7. Overall score (peak and average).
8. User-flagged boolean.
9. User-flagged timestamp.
10. Created timestamp.

### 11.4 Contact relationship data

Minimum contact relationship fields:

1. Relationship ID.
2. User A ID.
3. User B ID.
4. Relationship status: pending, accepted, blocked.
5. Initiated-by user ID.
6. Created timestamp.
7. Updated timestamp.

### 11.5 Refresh token data

Minimum refresh token fields:

1. Token ID.
2. User ID.
3. Token hash.
4. Expiry timestamp.
5. Revoked timestamp.
6. Created timestamp.

---

## 12. Security and privacy requirements

| ID | Requirement | Priority |
|---|---|---|
| SEC-01 | All WebRTC media streams shall be protected by DTLS-SRTP as mandated by the WebRTC specification. | Must |
| SEC-02 | All signaling WebSocket connections shall use WSS (TLS). All REST API endpoints shall use HTTPS. | Must |
| SEC-03 | User passwords shall be stored as salted hashes using a memory-hard algorithm such as bcrypt or Argon2. | Must |
| SEC-04 | JWT tokens shall be signed with RS256 or HS256 and validated server-side on every protected request. | Must |
| SEC-05 | Refresh tokens shall be stored server-side as hashes, not plaintext, and shall be rotated on every use. | Must |
| SEC-06 | Auth endpoints and OTP endpoints shall be rate-limited per IP and per account. | Must |
| SEC-07 | Call initiation shall be rate-limited per user to prevent abuse of the calling infrastructure. | Must |
| SEC-08 | Call audio shall not be stored server-side. Only scores, timestamps, and verdicts shall be persisted after the call ends. | Must |
| SEC-09 | The app shall present a clear, plain-language consent notice at registration explaining voice analysis, data use, and deletion rights. | Must |
| SEC-10 | The system shall comply with the Indian Digital Personal Data Protection Act, 2023 for all user and detection data. | Must |
| SEC-11 | Users shall be able to export their personal data, delete detection logs, and delete their account via in-app controls. | Must |
| SEC-12 | Blocked users shall have no visibility into the blocker's presence or contact profile. | Must |
| SEC-13 | Detection logs shall be accessible only to the call participants whose streams they describe. | Must |
| SEC-14 | The TURN server shall use time-limited credentials rather than a shared static secret. | Must |

---

## 13. Non-functional requirements

### 13.1 Performance

| Metric | Target |
|---|---|
| Call setup time (initiate to audio flowing) | Less than 3 seconds on a good connection |
| End-to-end audio latency | Less than 200 ms |
| Detection first-score latency | Less than 5 seconds from sustained speech start |
| Score update interval during speech | Every 1–2 seconds |
| AI inference time per chunk (server-side) | Less than 500 ms |
| App cold start to home screen ready | Less than 3 seconds |
| API response for auth and contact endpoints | Less than 500 ms at 95th percentile |
| FCM notification delivery to on-screen incoming call | Less than 2 seconds |

### 13.2 Reliability

1. Call audio must not be interrupted by detection processing — the two pipelines are fully decoupled.
2. Failure of the AI inference service must not cause calls to fail or degrade.
3. The app must recover from a transient network drop during a call and attempt automatic reconnection for up to 30 seconds.
4. Detection logs must be written transactionally; partial logs are preferable to data loss.
5. Duplicate call sessions for the same pair of participants at the same time must be prevented at the signaling layer.
6. The FCM push notification must be delivered reliably even when the app is force-stopped, using FCM high-priority data messages.

### 13.3 Usability

1. The in-call detection badge must be readable without interrupting attention to the conversation.
2. Alert banners must not block the end-call button or the mute button.
3. The detection badge color must be paired with a text label; color alone must not be the only indicator.
4. Detection score explanations must be accessible in one tap from the active call screen.
5. Call history must be searchable or filterable; a user with hundreds of calls must be able to find a specific entry quickly.

### 13.4 Scalability

1. The signaling server must be horizontally scalable across multiple Node.js processes with a shared session store.
2. The AI inference service must be horizontally scalable independently of the signaling server.
3. The SFU media server must be independently scalable to handle peak concurrent group calls.
4. The system must support a target of 500 simultaneous calls in the initial production deployment, with the architecture capable of scaling further.

### 13.5 Maintainability

1. Model version must be recorded in every detection log so that logs remain interpretable after model upgrades.
2. Detection thresholds for the three classification bands must be externally configurable without a code deployment.
3. The AI service must support hot model swapping without dropping in-progress calls.
4. Application and service logs must be structured and shipped to a centralized log aggregation system.

---

## 14. Acceptance criteria

### 14.1 Calling acceptance criteria

1. Given a registered user calls an accepted contact, when the callee accepts, then audio flows in both directions within 3 seconds.
2. Given a callee's device is locked and the app is closed, when a call is initiated, then the system incoming call screen appears within 2 seconds.
3. Given a callee does not answer within 30 seconds, when the timeout expires, then the call is marked as missed and the caller sees "missed" state.
4. Given a user is on an active call and the network drops, when the network is restored within 30 seconds, then the call reconnects without user action.
5. Given a group call is created with 8 participants, when a 9th participant is invited, then the app prevents adding them and displays the participant limit message.

### 14.2 Detection acceptance criteria

1. Given a call is active and a participant is speaking, when 5 seconds of sustained speech have passed, then an authenticity score is visible in the call UI.
2. Given a synthetic voice is played during a test call, when the detection engine processes the stream, then the score must cross the suspicious threshold within 8 seconds of the synthetic speech starting.
3. Given the AI inference service is unavailable, when a call is active, then the call continues normally and the badge shows "analysis unavailable."
4. Given a detection score crosses the suspicious threshold, when two consecutive updates confirm it, then a banner alert appears without blocking or ending the call.
5. Given a call has ended, when the user opens call history, then the detection report is accessible and shows the score timeline.

### 14.3 Security acceptance criteria

1. Given a user is not authenticated, when they attempt to call or access contact data, then the API returns 401.
2. Given an attacker submits more than 10 incorrect passwords in succession, when the rate limiter fires, then the endpoint returns 429 for the lockout duration.
3. Given a call ends, when the call session is finalized server-side, then no audio data is retained; only scores and timestamps exist in the detection log.
4. Given a user deletes their account, when deletion completes, then all call history, detection logs, and personal profile data are removed from the system.

### 14.4 Push notification acceptance criteria

1. Given the Android app is closed and a call is initiated, when the FCM push is delivered, then the system incoming call screen appears within 2 seconds.
2. Given a call is missed, when the timeout expires, then a missed call notification appears in the notification tray.

---

## 15. Open decisions for the implementation team

These are not blockers for document creation but must be finalized during engineering planning:

1. SFU media server selection: Mediasoup (Node.js native) vs LiveKit (higher-level managed) vs Janus. Decision affects backend team's Node.js vs Go expertise and operational complexity.
2. Message queue selection for the audio analysis pipeline: RabbitMQ vs Redis Streams vs Kafka. RabbitMQ is recommended for the initial scale; decision must be finalized before AI service integration work starts.
3. Deepfake detection model architecture: AASIST vs RawNet2 vs ensemble. Decision should follow benchmark evaluation on VoIP-augmented test data before the ML module milestone.
4. Whether user-flagged detection errors are automatically submitted to the retraining pipeline or require manual ML team review first. Privacy and consent implications must be reviewed.
5. Whether the web dashboard supports group calls at launch or only one-to-one, given the complexity of multi-party WebRTC in the browser.
6. Exact OTP provider: Firebase Authentication OTP vs a direct SMS gateway (e.g., Twilio, Msg91). Firebase simplifies Android integration but adds a dependency.
7. iOS support timeline: whether to architect the Android and backend for iOS compatibility from day one (shared API, no Android-specific contracts) or defer iOS scaffolding.
8. TURN server: self-hosted Coturn on AWS vs a managed TURN provider. Cost and control tradeoffs to be reviewed.
