# Technical Specification Document

**Project:** RingWave  
**Prepared for:** Internal engineering team  
**Prepared on:** 2026-06-06  
**Document status:** Draft for implementation planning

---

## 1. Technical objective

Build a production-grade internet audio calling platform with an integrated AI-powered voice deepfake detection layer. The system comprises an Android application, a React web application, a Node.js signaling and API backend, a Selective Forwarding Unit media server for group calls, a Python AI inference microservice for real-time deepfake detection, and a MongoDB database. All components must be independently deployable and horizontally scalable. The detection pipeline must be fully decoupled from the call audio path so that inference failures cannot degrade call quality.

---

## 2. Architecture summary

### 2.1 Preferred architecture

| Layer | Recommended choice |
|---|---|
| Android app | Kotlin, Jetpack Compose, MVVM, Hilt dependency injection |
| Web app | React.js, TypeScript, TailwindCSS |
| Signaling and REST API | Node.js, Express.js, Socket.io |
| Media server (SFU) | Mediasoup 3.x (Node.js native) |
| AI inference service | Python, FastAPI, PyTorch or ONNX Runtime |
| Audio analysis queue | RabbitMQ |
| Database | MongoDB Atlas (replica set, AWS region: ap-south-1) |
| Cache and session store | Redis (for shared Socket.io adapter, rate limiting, refresh token revocation list) |
| TURN server | Coturn on AWS EC2 (t3.small) with time-limited HMAC credentials |
| Push notifications | Firebase Cloud Messaging (Android + Web Push) |
| Cloud provider | AWS (EC2, ECS, S3 for static assets, CloudFront CDN, Route 53) |
| Containerization | Docker, Docker Compose for local development; ECS Fargate for production |

### 2.2 Why this architecture

The signaling server and the media server are separated because they have different scaling characteristics. The signaling server handles lightweight WebSocket events; the media server handles heavy RTP forwarding and must scale on a per-call basis. Mediasoup is chosen over LiveKit for the first release because it is a Node.js library that shares the backend team's existing language expertise, is self-hosted (no managed service cost), and gives fine-grained control over SFU routing behavior.

The AI inference service is a separate Python process because the deepfake detection models (AASIST, RawNet2) are PyTorch-based and the Python ML ecosystem is where these models are actively maintained. Decoupling via RabbitMQ ensures the inference service can be restarted, updated, or scaled independently without affecting in-progress calls. The queue also provides natural backpressure if inference demand temporarily exceeds capacity.

---

## 3. System components

### 3.1 Backend services

| Service | Language | Responsibility |
|---|---|---|
| Signaling and API Server | Node.js / Express | REST API (auth, contacts, call history, detection reports), Socket.io signaling events, call session state management, rate limiting |
| Media Server (SFU) | Node.js / Mediasoup | WebRTC RTP forwarding for group and one-to-one calls, audio stream tapping for detection pipeline, ICE/DTLS termination |
| AI Inference Service | Python / FastAPI | Consume audio chunks from RabbitMQ, run deepfake detection model, publish scores back to signaling server |
| Audio Queue | RabbitMQ | Decouple media server audio output from AI inference service input |
| TURN Server | Coturn | TURN relay for clients behind symmetric NAT; STUN for NAT discovery |
| Push Gateway | Firebase Cloud Messaging | Deliver high-priority incoming call notifications to Android and web clients |

### 3.2 Android app modules

| Module | Responsibility |
|---|---|
| Auth Module | Registration, OTP verification, login, token management, logout |
| Contact Module | Contact list, search, request flow, block/unblock, presence display |
| Call Module | Outgoing call, incoming call screen, active call screen, call controls |
| WebRTC Engine | SDP negotiation, ICE candidate exchange, audio track management, DTLS-SRTP |
| Detection UI Module | In-call badge, alert banners, post-call report screen |
| History Module | Call history list, call detail, detection report |
| Notification Module | FCM push receiver, ConnectionService integration, foreground service |
| Settings Module | Profile editing, presence, notification preferences, account deletion |

### 3.3 Web app modules

| Module | Responsibility |
|---|---|
| Auth Pages | Register, OTP verify, login, token management |
| Contact Pages | Contact list, search, request management |
| Call Pages | Outgoing/incoming call UI, active call UI with detection badge |
| History Pages | Call history, detection report view |
| Settings Pages | Profile, presence, account management |
| WebRTC Hook | Browser WebRTC adapter, SDP/ICE management |
| Push Service | Web Push registration and notification handler |

---

## 4. Runtime flows

### 4.1 User registration and login flow

1. Client sends POST /api/auth/register with username, phone/email, password.
2. Server validates input, hashes password with bcrypt (cost factor 12), creates user record with `isVerified: false`.
3. Server sends OTP to phone or email.
4. Client submits OTP via POST /api/auth/verify-otp.
5. Server validates OTP, sets `isVerified: true`.
6. Client logs in via POST /api/auth/login.
7. Server returns access token (JWT, 15-minute expiry, RS256 signed) and refresh token (opaque random string, stored as hash in RefreshTokens collection, 7-day expiry).
8. Android app stores access token in memory and refresh token in Android EncryptedSharedPreferences. Web app stores refresh token in httpOnly cookie.
9. Before the access token expires, the client silently calls POST /api/auth/refresh. Server validates refresh token hash, issues new access token and new refresh token (rotating), revokes old refresh token.

### 4.2 Outgoing one-to-one call flow

1. Caller taps call button. App creates a Mediasoup device and generates SDP offer.
2. App emits `call:initiate` over Socket.io: `{ targetUserId, sdpOffer }`.
3. Signaling server validates the caller is authenticated and not blocked by the callee.
4. Signaling server creates a call session record (status: ringing), generates a `sessionId`, and forwards `call:incoming` to the callee's socket: `{ sessionId, callerId, callerProfile, sdpOffer }`.
5. Signaling server emits `call:ringing` back to the caller.
6. Callee receives incoming call screen. Callee accepts.
7. Callee generates SDP answer and emits `call:accept`: `{ sessionId, sdpAnswer }`.
8. Signaling server forwards `call:accepted` to the caller with the SDP answer.
9. Both sides exchange ICE candidates via `call:ice-candidate` events.
10. Mediasoup SFU establishes the RTP transport. Audio flows between both parties.
11. Signaling server updates session status to `connected`, records `connectedAt`.
12. Media server begins audio tapping (see Section 4.5).

### 4.3 Incoming call flow (Android, app not running)

1. FCM delivers a high-priority data message to the device with `callerId`, `sessionId`, and `callerDisplayName`.
2. Android OS wakes the app process.
3. The `FirebaseMessagingService` receives the message and calls `startActivity` with a full-screen intent to trigger the incoming call screen.
4. The Android ConnectionService API shows the system incoming call UI.
5. If the callee accepts, the app connects to the signaling server and proceeds from step 7 of the outgoing call flow.
6. If the callee rejects, the app emits `call:reject` and the server notifies the caller.
7. If no action within 30 seconds, the server sets session status to `missed`, emits `call:missed` to both parties, and sends a missed call FCM notification to the callee.

### 4.4 Group call flow

1. Host emits `call:group-create` with a list of participant user IDs.
2. Server creates a Mediasoup Router and a session record with all participant IDs.
3. Each participant receives `call:incoming` with the `sessionId` and host profile.
4. As each participant accepts, the server creates Mediasoup WebRtcTransport and Producer/Consumer pairs for that participant.
5. Each accepting participant sends and receives audio streams via the SFU.
6. For every newly joined participant, the server emits `call:participant-joined` to all existing participants.
7. When a participant leaves, their transport is closed and `call:participant-left` is emitted to remaining participants.
8. When the host emits `call:end` with `{ sessionId }`, the server closes all transports, ends the session, and notifies all participants.
9. If the host leaves without ending the call, the server assigns host role to the next participant in join order and continues the session.

### 4.5 Audio detection pipeline flow

1. Mediasoup media server, for each active participant transport, subscribes to the participant's audio Producer using a PlainTransport.
2. RTP audio is forwarded to the audio tap module, which decodes and converts it to 16 kHz mono PCM.
3. The tap module maintains a sliding buffer: it accumulates 1.5 seconds of audio with a 0.5-second hop (i.e., a new chunk is published every 0.5 seconds, with the last 1.0 seconds overlapping with the previous chunk).
4. Each chunk is published to RabbitMQ queue `detection.audio.{sessionId}.{participantId}` as a binary payload with metadata: `{ sessionId, participantId, chunkIndex, startMs, endMs, sampleRate: 16000, channels: 1 }`.
5. The Python AI inference service consumes from the queue. It preprocesses the chunk (normalize amplitude, extract LFCC features), runs the detection model, and produces a raw score (0.0–1.0).
6. The service applies exponential moving average: `smoothed = 0.3 * raw + 0.7 * previous_smoothed`. On the first chunk, smoothed equals raw.
7. The service classifies the smoothed score: real (< 0.35), suspicious (0.35–0.65), synthetic (> 0.65).
8. The service publishes the result to RabbitMQ queue `detection.scores.{sessionId}.{participantId}`.
9. The signaling server consumes scores and emits `detection:score` to the relevant participant sockets: `{ sessionId, participantId, smoothedScore, verdict, chunkIndex, chunkTimestamp }`.
10. If the verdict is suspicious or synthetic and the threshold-crossing condition is met (two consecutive updates above threshold), the server also emits `detection:alert` to all participants in the session who are not the source participant.
11. After the call ends, the signaling server flushes the chunk score buffer and writes the complete detection log to MongoDB.

### 4.6 Call reconnection flow

1. The client detects a network disruption via a WebRTC `iceconnectionstatechange` event reaching `disconnected` or `failed`.
2. The client emits `call:reconnect-attempt` to the signaling server and begins ICE restart.
3. The signaling server holds the session in `reconnecting` status for up to 30 seconds.
4. If ICE restart succeeds, the session resumes and both parties receive `call:reconnected`.
5. If 30 seconds pass without a successful reconnect, the server emits `call:ended` with `endReason: network_drop` to both parties and finalizes the session.
6. During the reconnection window, audio detection is paused and the badge shows "reconnecting."

---

## 5. Performance strategy

### 5.1 Target latency budget

| Step | Target |
|---|---|
| FCM delivery to on-screen incoming call | < 2 seconds |
| SDP offer/answer exchange and ICE | < 1 second (fast path), < 3 seconds (TURN path) |
| Total call setup (initiate to audio) | < 3 seconds |
| End-to-end audio latency | < 200 ms (WebRTC target) |
| Audio tap to chunk publication | < 50 ms |
| AI inference per 1.5s chunk | < 500 ms |
| Score publication to client display | < 100 ms |
| Detection first-score display | < 5 seconds from speech start |
| Score update interval on client | Every 1–2 seconds |

### 5.2 Detection pipeline optimizations

1. Use ONNX Runtime for model serving where possible — it is 2–5x faster than raw PyTorch for inference-only workloads on CPU.
2. Run the inference service with multiple worker processes (one per CPU core) to handle concurrent calls.
3. Use INT8 quantization on the model if accuracy remains within the EER target; this reduces inference time and memory footprint significantly.
4. Use persistent RabbitMQ connections with a prefetch count of 1 per worker to ensure even distribution of chunks across workers.
5. Keep the scoring buffer in memory for the duration of the call; flush to MongoDB only on call end, not per-chunk, to reduce database write pressure.

### 5.3 WebRTC optimizations

1. Prefer OPUS codec with FEC (Forward Error Correction) enabled for audio — this reduces perceptible quality loss under packet loss.
2. Enable TURN server credential caching so clients do not re-fetch credentials on every call setup.
3. Use Mediasoup's built-in audio level observer to determine which participants are actively speaking, enabling the detection badge to show a paused state during silence.
4. Preconnect the Socket.io session on app start so that `call:initiate` does not have to wait for WebSocket handshake.

---

## 6. Database schema

### 6.1 Collection: users

| Field | Type | Notes |
|---|---|---|
| _id | ObjectId | Primary key |
| username | String | Unique, lowercase, 3–30 chars |
| phone | String | Unique, E.164 format, optional |
| email | String | Unique, lowercase, optional |
| passwordHash | String | bcrypt hash |
| passwordSalt | String | bcrypt salt |
| displayName | String | Up to 50 chars |
| avatarUrl | String | S3 URL or null |
| presenceStatus | Enum | online, offline, busy, dnd |
| isVerified | Boolean | True after OTP confirmation |
| isActive | Boolean | False on account deletion |
| createdAt | Date | |
| updatedAt | Date | |

Indexes: `username` (unique), `phone` (unique, sparse), `email` (unique, sparse).

### 6.2 Collection: contacts

| Field | Type | Notes |
|---|---|---|
| _id | ObjectId | Primary key |
| userId | ObjectId | References users._id |
| contactUserId | ObjectId | References users._id |
| status | Enum | pending, accepted, blocked |
| initiatedBy | ObjectId | References users._id |
| createdAt | Date | |
| updatedAt | Date | |

Indexes: `{ userId, contactUserId }` (unique compound), `{ contactUserId, status }`.

### 6.3 Collection: callsessions

| Field | Type | Notes |
|---|---|---|
| _id | ObjectId | Primary key |
| sessionType | Enum | one_to_one, group |
| initiatorId | ObjectId | References users._id |
| participants | Array | [{ userId, joinedAt, leftAt, status: invited/joined/left/rejected }] |
| status | Enum | ringing, connected, reconnecting, ended, missed, rejected, dropped |
| startedAt | Date | When `call:initiate` was received |
| connectedAt | Date | When first audio was established |
| endedAt | Date | |
| durationSeconds | Number | Seconds from connectedAt to endedAt |
| endReason | Enum | normal, missed, rejected, network_drop, error |

Indexes: `{ initiatorId, startedAt }`, `{ "participants.userId": 1, startedAt: -1 }`.

### 6.4 Collection: detectionlogs

| Field | Type | Notes |
|---|---|---|
| _id | ObjectId | Primary key |
| sessionId | ObjectId | References callsessions._id |
| participantId | ObjectId | References users._id |
| modelName | String | e.g., "aasist-v1" |
| modelVersion | String | Semantic version |
| chunks | Array | [{ chunkIndex, startMs, endMs, rawScore, smoothedScore }] |
| overallVerdict | Enum | real, suspicious, synthetic, unavailable |
| peakScore | Number | Highest smoothed score in the call |
| averageScore | Number | Mean of all smoothed scores |
| userFlagged | Boolean | |
| userFlaggedAt | Date | Null if not flagged |
| createdAt | Date | |

Indexes: `{ sessionId, participantId }` (unique compound), `{ participantId, createdAt: -1 }`.

### 6.5 Collection: refreshtokens

| Field | Type | Notes |
|---|---|---|
| _id | ObjectId | Primary key |
| userId | ObjectId | References users._id |
| tokenHash | String | SHA-256 hash of the opaque token |
| expiresAt | Date | TTL index set on this field |
| revokedAt | Date | Null if active |
| createdAt | Date | |

Indexes: `tokenHash` (unique), TTL index on `expiresAt`.

---

## 7. Signaling API — Socket.io events

### 7.1 Client to server events

| Event | Payload | Description |
|---|---|---|
| `call:initiate` | `{ targetUserId, sdpOffer }` | Start an outgoing one-to-one call |
| `call:group-create` | `{ participantIds[], groupName? }` | Create a group call |
| `call:accept` | `{ sessionId, sdpAnswer }` | Accept an incoming call |
| `call:reject` | `{ sessionId }` | Decline an incoming call |
| `call:end` | `{ sessionId }` | End the call |
| `call:ice-candidate` | `{ sessionId, candidate }` | Trickle ICE candidate |
| `call:hold` | `{ sessionId }` | Place call on hold |
| `call:resume` | `{ sessionId }` | Resume from hold |
| `call:add-participant` | `{ sessionId, userId }` | Add a contact to a group call |
| `call:remove-participant` | `{ sessionId, userId }` | Host removes a participant |
| `call:mute-participant` | `{ sessionId, userId }` | Host mutes a participant |
| `call:reconnect-attempt` | `{ sessionId }` | Signal reconnection attempt |
| `presence:update` | `{ status }` | Update user presence |

### 7.2 Server to client events

| Event | Payload | Description |
|---|---|---|
| `call:incoming` | `{ sessionId, callerId, callerProfile, sdpOffer, sessionType }` | Delivered to callee on incoming call |
| `call:ringing` | `{ sessionId }` | Delivered to caller confirming callee was reached |
| `call:accepted` | `{ sessionId, sdpAnswer }` | Callee accepted; contains SDP answer |
| `call:rejected` | `{ sessionId }` | Callee rejected the call |
| `call:ended` | `{ sessionId, endReason }` | Call ended by any party or by the system |
| `call:missed` | `{ sessionId }` | Timeout; call not answered |
| `call:ice-candidate` | `{ sessionId, candidate }` | Trickle ICE from remote party |
| `call:hold-ack` | `{ sessionId }` | Hold acknowledged by server |
| `call:participant-joined` | `{ sessionId, userId, userProfile }` | A participant joined a group call |
| `call:participant-left` | `{ sessionId, userId }` | A participant left a group call |
| `call:participant-muted` | `{ sessionId, userId }` | Host muted a participant |
| `call:host-transferred` | `{ sessionId, newHostId }` | Host role transferred |
| `call:reconnected` | `{ sessionId }` | Reconnection succeeded |
| `detection:score` | `{ sessionId, participantId, smoothedScore, verdict, chunkIndex, chunkTimestamp }` | Authenticity score update |
| `detection:alert` | `{ sessionId, participantId, verdict, alertType }` | Threshold-crossing alert |
| `user:presence` | `{ userId, status }` | A contact's presence changed |

---

## 8. REST API specification

All endpoints require `Authorization: Bearer <accessToken>` unless marked as public.

### 8.1 Authentication endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /api/auth/register | Public | Register new user |
| POST | /api/auth/verify-otp | Public | Confirm OTP |
| POST | /api/auth/login | Public | Login; returns access + refresh token |
| POST | /api/auth/refresh | Public (refresh token in body or cookie) | Rotate token pair |
| POST | /api/auth/logout | Required | Revoke refresh token |
| DELETE | /api/auth/account | Required | Delete account and all data |

### 8.2 User endpoints

| Method | Path | Description |
|---|---|---|
| GET | /api/users/search?q={query} | Search users by username or phone |
| GET | /api/users/:userId/profile | Get a user's public profile |
| PUT | /api/users/me/profile | Update own display name or avatar |
| PUT | /api/users/me/presence | Set own presence status |

### 8.3 Contact endpoints

| Method | Path | Description |
|---|---|---|
| GET | /api/contacts | List accepted contacts with presence |
| GET | /api/contacts/requests | List pending incoming requests |
| POST | /api/contacts/request | Send a contact request `{ targetUserId }` |
| PUT | /api/contacts/:contactId/accept | Accept a contact request |
| PUT | /api/contacts/:contactId/reject | Reject a contact request |
| PUT | /api/contacts/:contactId/block | Block a contact |
| PUT | /api/contacts/:contactId/unblock | Unblock a contact |
| DELETE | /api/contacts/:contactId | Remove a contact |

### 8.4 Call history endpoints

| Method | Path | Description |
|---|---|---|
| GET | /api/calls?filter={all|missed|incoming|outgoing}&page=N | Paginated call history |
| GET | /api/calls/:sessionId | Single call detail |
| DELETE | /api/calls/:sessionId | Delete call record and detection log |

### 8.5 Detection endpoints

| Method | Path | Description |
|---|---|---|
| GET | /api/detection/:sessionId | Full detection report for a call |
| POST | /api/detection/:sessionId/flag | Flag detection as incorrect `{ reason? }` |
| DELETE | /api/detection/:sessionId | Delete detection log for a call |

---

## 9. AI module specification

### 9.1 Problem framing

The deepfake detection model performs binary classification on short speech segments: genuine human speech vs synthesized or cloned speech. The model must handle audio that has passed through VoIP codecs (Opus at 8–24 kbps, GSM, G.711), background noise, and transmission artifacts, as these conditions degrade features that simpler models rely on.

### 9.2 Training datasets

| Dataset | Description | Use |
|---|---|---|
| ASVspoof 2019 Logical Access (LA) | Genuine and TTS/VC speech; standard anti-spoofing benchmark | Primary training and validation |
| ASVspoof 2021 LA | Adds telephone and codec channel conditions; closer to VoIP reality | Primary evaluation and fine-tuning |
| WaveFake | Deepfakes from 6 vocoders (WaveGlow, MelGAN, Parallel WaveGAN, HiFi-GAN, MB-MelGAN, Full-band MelGAN) | Supplementary training for vocoder diversity |
| In-The-Wild | Real-world voice deepfake samples collected from the internet | Supplementary training for real-world distribution |

**Augmentation strategy:** All training samples must be augmented with: Opus codec encoding/decoding at 8 kbps and 16 kbps (simulating VoIP compression), additive background noise at SNR 0–20 dB using MUSAN, and room impulse response convolution using the RIR-Noisy dataset. This augmentation is critical to avoid model degradation when applied to actual VoIP audio.

### 9.3 Feature extraction

The recommended feature pipeline:

1. **LFCC (Linear Frequency Cepstral Coefficients):** 60 coefficients with delta and delta-delta, 25 ms frame length, 10 ms hop. LFCC is preferred over MFCC for anti-spoofing because the linear filter bank better captures high-frequency artifacts introduced by neural vocoders.
2. **Log Mel-spectrogram:** 80 mel bins as an auxiliary feature for ensemble or multi-branch models.
3. **Raw waveform:** Used directly if RawNet2 is selected as the model architecture.

### 9.4 Model architecture candidates

| Model | Architecture | Strengths | Weaknesses |
|---|---|---|---|
| AASIST | Graph Attention Network on spectro-temporal features | State-of-the-art EER on ASVspoof 2021; robust to codec artifacts | Higher inference latency (~300 ms per chunk at INT8) |
| RawNet2 | End-to-end CNN on raw waveform | No feature engineering; learns its own representations | Slightly higher EER than AASIST on codec-degraded audio |
| LCNN | Light CNN on LFCC | Fast inference (<100 ms); good baseline | Lower accuracy than AASIST/RawNet2 on diverse spoofing |
| Ensemble (AASIST + LCNN) | Score average of two models | Best EER; more robust to novel attacks | Double inference cost |

**Recommended for first release:** AASIST with INT8 quantization. Benchmark on VoIP-augmented eval set before finalizing. If inference time exceeds 500 ms at target hardware spec, fall back to LCNN or the ensemble is deferred to a later model version.

### 9.5 Inference strategy for real-time detection

1. Segment audio into 1.5-second chunks with 0.5-second hop. Each chunk overlaps with the previous by 1.0 seconds.
2. For each chunk, extract LFCC features and run the model. Output is a scalar score in [0, 1] where 1 is maximally synthetic.
3. Apply EMA smoothing: `smoothed[t] = α * raw[t] + (1 − α) * smoothed[t−1]`, where α = 0.3. This gives significant weight to recent history and prevents the displayed score from responding to single noisy chunks.
4. Classify using fixed thresholds: real if smoothed < 0.35; suspicious if 0.35 ≤ smoothed ≤ 0.65; synthetic if smoothed > 0.65.
5. Alert condition: emit `detection:alert` when two consecutive score updates are above the suspicious threshold. Do not re-alert until the score falls below real and then crosses suspicious again within the same call.
6. If no speech is detected (silence or near-silence) for 10 consecutive seconds, pause scoring and set status to `silence` in the badge display.

### 9.6 Performance targets

| Metric | Target |
|---|---|
| Equal Error Rate (EER) on ASVspoof 2021 LA eval set | < 5% |
| EER on VoIP-augmented ASVspoof 2021 LA (internal benchmark) | < 8% |
| Inference time per 1.5s chunk (ONNX Runtime, INT8, 2 vCPU) | < 500 ms |
| False positive rate on genuine RingWave call sample | < 3% of chunks classified as suspicious or above |
| Detection first-score latency from speech start | < 5 seconds |

### 9.7 AI inference service API

The Python FastAPI service exposes a health check endpoint only. All chunk intake and score output happens via RabbitMQ, not HTTP, to avoid the latency and overhead of per-chunk HTTP round trips.

| Queue | Direction | Message format |
|---|---|---|
| `detection.audio.{sessionId}.{participantId}` | Media server → AI service | `{ sessionId, participantId, chunkIndex, startMs, endMs, pcmBase64 }` |
| `detection.scores.{sessionId}.{participantId}` | AI service → Signaling server | `{ sessionId, participantId, chunkIndex, startMs, endMs, rawScore, smoothedScore, verdict }` |

The signaling server maintains a RabbitMQ consumer per active detection session. On call end, the consumer is closed and the score buffer is flushed to MongoDB.

---

## 10. Security specification

### 10.1 Transport security

1. All REST API and WebSocket connections use TLS 1.2 or higher.
2. WebRTC media is encrypted with DTLS-SRTP, enforced by the Mediasoup SFU. Unencrypted media connections must be rejected.
3. The TURN server requires HMAC-SHA1 time-limited credentials. Credentials are generated by the signaling server and are valid for 1 hour per session.
4. RabbitMQ connections use TLS with client certificate authentication between internal services.

### 10.2 Authentication and authorization

1. Passwords are hashed with bcrypt at cost factor 12. The plaintext password is never logged or persisted.
2. Access tokens are RS256-signed JWTs containing: `sub` (user ID), `iat`, `exp` (15 minutes from issue), `jti` (unique token ID for revocation if needed).
3. Refresh tokens are cryptographically random 256-bit values stored in the database as SHA-256 hashes. A new refresh token is issued on every use (rotation). The old token is immediately marked revoked.
4. The Redis revocation list is checked on every access token validation as a defense against stolen tokens before the 15-minute expiry.
5. Admin account operations (account deletion, data export) require re-authentication within the last 5 minutes.

### 10.3 Rate limiting

| Endpoint group | Limit |
|---|---|
| POST /api/auth/login | 10 attempts per 15 minutes per IP; 5 per account |
| POST /api/auth/verify-otp | 5 attempts per OTP; OTP expires in 10 minutes |
| POST /api/auth/register | 20 registrations per hour per IP |
| `call:initiate` Socket.io event | 30 calls initiated per user per hour |
| POST /api/contacts/request | 50 requests per user per hour |
| GET /api/users/search | 60 searches per user per minute |

### 10.4 Data privacy

1. Call audio is never written to disk or object storage. It is processed in-memory through the RTP tap pipeline and discarded after chunking and queuing.
2. Detection logs store only scores and timestamps. No audio samples, voice prints, or biometric templates are retained.
3. User data deletion (triggered by DELETE /api/auth/account) must cascade delete: user record, contacts, call sessions where the user is a participant, detection logs, and refresh tokens. Deletion must complete within 30 days and an immediate logical deletion flag must be applied instantly.
4. Data export must be provided via GET /api/users/me/export and must include all user profile data, call history metadata, and detection log verdicts in a machine-readable format.
5. The consent notice shown at registration must describe: what data is collected, how voice analysis works, that audio is not stored, how to delete data, and a reference to the privacy policy.

### 10.5 Input validation

1. All user-supplied strings must be validated for type, length, and character set at the Express middleware layer.
2. MongoDB queries must use parameterized operators. String interpolation into query objects must never be used.
3. SDP and ICE candidate payloads from clients must be validated against the WebRTC SDP grammar before being forwarded.
4. File uploads (avatar images) must be validated for MIME type, size limit (2 MB), and image dimensions before storage.

---

## 11. Error handling

| Scenario | Client behavior | Server action |
|---|---|---|
| Network drop during call | Show "reconnecting" overlay, start reconnection timer | Hold session in reconnecting state for 30 s, then end if no success |
| AI service unavailable | Badge shows "analysis unavailable"; call continues | Log service health event; skip score publishing for this session |
| FCM delivery failure | Callee misses the call | Server marks call as missed; sends notification retry via next app open |
| SDP negotiation failure | Show "call failed" error and return to contacts | Log SDP error, end session |
| TURN server unreachable | Show "connection error" and prompt retry | Log TURN credential failure |
| 401 on REST API call | Attempt token refresh; if that fails, redirect to login | Return 401 with `WWW-Authenticate` header |
| 429 rate limit | Show "too many requests" message, disable button for backoff duration | Return 429 with `Retry-After` header |
| Invalid SDP or ICE candidate | Silently discard invalid payload | Log validation failure with session ID |
| RabbitMQ queue backlog | Detection latency increases; badge shows delayed state | Monitor queue depth; auto-scale inference workers on depth threshold |
| Duplicate call session | Merge or reject the second initiation | Detect duplicate (same pair, within 5 seconds) and return existing session ID |

---

## 12. Testing strategy

### 12.1 Unit tests

1. JWT issuance, expiry, and validation logic.
2. Refresh token rotation and revocation.
3. Rate limiter logic per endpoint and per account.
4. Call session state transition rules.
5. EMA smoothing algorithm.
6. Detection threshold classification.
7. Alert condition (two consecutive updates above threshold).
8. Silence detection (no speech for 10 seconds → paused state).
9. Group call host transfer logic.
10. Participant limit enforcement.

### 12.2 Integration tests

1. Full registration and OTP verification flow.
2. Login → token issuance → token refresh → logout → token revoked.
3. One-to-one call: initiate → ring → accept → ICE exchange → audio → end → history recorded.
4. Call missed: initiate → ring → 30-second timeout → missed record → notification.
5. Call rejected: initiate → ring → reject → caller notified.
6. Group call: create → multiple participants join → host removes one → call ends → all sessions closed.
7. Detection: call starts → chunks queued → scores received → badge updated → call ends → log written.
8. Block flow: user A blocks user B → B cannot initiate call to A → B cannot find A in search.
9. Account deletion: delete account → confirm all associated data removed from all collections.

### 12.3 AI model evaluation

1. Evaluate EER on ASVspoof 2019 LA evaluation partition.
2. Evaluate EER on ASVspoof 2021 LA evaluation partition.
3. Evaluate EER on VoIP-augmented evaluation set (Opus 8 kbps + MUSAN noise).
4. Measure false positive rate on a held-out set of 500 genuine RingWave call segments.
5. Measure inference time per 1.5-second chunk at INT8 on the target EC2 instance type.
6. Plot DET (Detection Error Trade-off) curve to characterize the false-positive vs false-negative tradeoff at threshold values.
7. Run detection on a call with a gradual voice quality degradation to validate graceful score degradation rather than a false synthetic classification.

### 12.4 Load testing

1. 500 simultaneous one-to-one calls: verify audio quality and no dropped sessions.
2. 50 simultaneous group calls with 6 participants each: verify SFU routing stability.
3. AI inference service: 500 concurrent chunk streams; verify all chunks are processed within 500 ms at the 95th percentile.
4. Socket.io signaling server: 5,000 simultaneous connected clients; verify event delivery latency.
5. MongoDB: write throughput for 500 simultaneous call session and detection log writes.

### 12.5 Call quality testing

1. MOS (Mean Opinion Score) assessment using PESQ (ITU-T P.862) on test call recordings.
2. Target: MOS > 3.5 under normal conditions (no packet loss).
3. Test under simulated 5% packet loss: verify Opus FEC maintains perceptible quality.
4. Test audio interruption when the detection pipeline is under artificial delay.

---

## 13. Observability and diagnostics

The following metrics and logs must be available in the centralized monitoring system (CloudWatch or equivalent):

**Signaling server metrics:**
1. Active socket connections.
2. Active call sessions by type.
3. `call:initiate` events per minute.
4. Call setup success rate.
5. Average call duration.
6. Reconnection attempt count and success rate.

**AI inference service metrics:**
1. Queue depth: `detection.audio.*` queues.
2. Average and 95th percentile inference latency per chunk.
3. Throughput: chunks processed per second.
4. Worker error rate.
5. Score distribution histogram (proportion of real/suspicious/synthetic) over rolling 1-hour window.
6. User flag rate per 1000 calls.

**Infrastructure metrics:**
1. EC2 / ECS CPU and memory per service.
2. RabbitMQ connection count and queue depth.
3. MongoDB operation latency and replication lag.
4. Redis hit rate for token validation.
5. FCM delivery success rate.

**Alerts:**
1. AI service queue depth > 500 items for > 60 seconds (scale inference workers).
2. EER on flagged samples > 10% in a rolling 24-hour window (trigger model review).
3. Call setup success rate < 95% over 5 minutes.
4. Any service health check failure.

---

## 14. Model lifecycle

1. Every model release must have a semantic version string (e.g., `aasist-v1.0.0`).
2. Every detection log must store the `modelName` and `modelVersion` fields.
3. Model updates are applied by deploying a new inference service version and updating the model version config. The old model version continues serving until all in-progress calls end.
4. When a model update introduces incompatible score semantics or threshold ranges, the internal ML team must audit historical flagged records before the new model goes to production.
5. User-flagged records are reviewed by the ML team weekly. If the false positive rate on flagged records is consistently below 5%, the current model is considered performing adequately. Above 10% triggers a retraining run.
6. Retraining must use augmented datasets (see Section 9.2) plus any newly collected and reviewed flagged samples for which the user consented to data submission.
7. Every model must be benchmarked on the fixed internal VoIP-augmented evaluation set before deployment to allow performance tracking across model versions.

---

## 15. Build and release requirements

1. Android minimum SDK: API 26 (Android 8.0). This is the minimum for ConnectionService API support.
2. Android release builds must enable R8 minification and resource shrinking.
3. Android APK/AAB must be signed with a Play Store signing key stored in a secrets manager, never in the repository.
4. The Node.js and Python services must be containerized with Docker and deployed via ECS Fargate. Image tags must match the Git release tag.
5. Environment secrets (database URIs, JWT signing key, FCM service account) must be injected at runtime via AWS Secrets Manager, never baked into Docker images or repository code.
6. A QA build must include a seeded test environment (test users, test call history, test detection logs) to enable repeatable end-to-end test runs.
7. Production deployments must use a canary release strategy: route 10% of traffic to the new version, observe metrics for 30 minutes, then promote to 100%.
8. A rollback procedure must be documented and tested for each service before the first production release.

---

## 16. Technical risks

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| AASIST inference exceeds 500 ms at target hardware | Detection first-score > 5 s | Medium | Benchmark with INT8 ONNX before committing to architecture; fallback to LCNN |
| VoIP codec artifacts cause high false positive rate | User distrust of detection | Medium | Augment training data with Opus/GSM codec artifacts; measure on internal VoIP benchmark |
| Mediasoup SFU audio tapping increases call latency | Audio quality degradation | Low | Use PlainTransport (zero-copy) for tapping; benchmark under load before production |
| Novel voice cloning tools released after training | Detection misses new attacks | High (long term) | Monitor WaveFake and ASVspoof community; set up quarterly model review cycle |
| FCM high-priority delivery unreliable on Android OEM builds (e.g., Xiaomi, OPPO) | Users miss incoming calls | Medium | Test on top 5 OEM devices in India; implement fallback polling when app is opened |
| RabbitMQ queue backlog under peak load | Detection scores delayed or dropped | Low | Auto-scale inference workers based on queue depth; set TTL on chunks (discard if > 5 s old) |
| TURN server bandwidth cost exceeds budget | Operational cost overrun | Medium | Monitor TURN relay percentage; encourage P2P paths; cap TURN bandwidth per user per day if needed |
| MongoDB write throughput limit under call peak | Detection logs lost | Low | Use MongoDB Atlas auto-scaling; batch-write chunk arrays per call end rather than per chunk |
| Regulatory change in DPDP Act implementation rules | Compliance gap | Medium | Track DPDP Act notifications; legal review before production launch; DPA registration if required |
