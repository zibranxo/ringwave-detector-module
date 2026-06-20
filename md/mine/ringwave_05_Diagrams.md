# Diagrams

**Project:** RingWave  
**Prepared for:** Internal product and engineering team  
**Prepared on:** 2026-06-06  
**Document status:** Draft for implementation planning

---

## 1. High-level system architecture

```mermaid
flowchart TB
    User[End User] --> Android[Android App]
    User --> Web[Web Dashboard - React]

    subgraph ClientLayer[Client Layer]
        Android
        Web
    end

    subgraph BackendLayer[Backend Layer - AWS ECS Fargate]
        SignalingAPI[Signaling and REST API\nNode.js + Express + Socket.io]
        SFU[SFU Media Server\nMediasoup]
        AIService[AI Inference Service\nPython + FastAPI]
        Queue[Message Queue\nRabbitMQ]
        Cache[Cache and Session\nRedis]
        TURN[TURN Server\nCoturn on EC2]
    end

    subgraph DataLayer[Data Layer]
        MongoDB[(MongoDB Atlas\nReplica Set)]
        S3[(AWS S3\nAvatars and static assets)]
    end

    subgraph PushLayer[Push Delivery]
        FCM[Firebase Cloud Messaging]
    end

    Android -->|WSS Socket.io| SignalingAPI
    Android -->|HTTPS REST| SignalingAPI
    Web -->|WSS Socket.io| SignalingAPI
    Web -->|HTTPS REST| SignalingAPI

    Android -->|WebRTC DTLS-SRTP| SFU
    Web -->|WebRTC DTLS-SRTP| SFU

    Android -->|STUN/TURN| TURN
    Web -->|STUN/TURN| TURN

    SignalingAPI --> Cache
    SignalingAPI --> MongoDB
    SignalingAPI --> Queue
    SignalingAPI --> FCM

    SFU --> Queue
    Queue --> AIService
    AIService --> Queue

    FCM --> Android
    FCM --> Web
    S3 --> Android
    S3 --> Web
```

---

## 2. Outgoing one-to-one call signaling flow

```mermaid
sequenceDiagram
    participant CallerApp as Caller (Android)
    participant SigServer as Signaling Server
    participant SFU as SFU Media Server
    participant FCM as FCM
    participant CalleeApp as Callee (Android)

    CallerApp->>SigServer: call:initiate { targetUserId, sdpOffer }
    SigServer->>SigServer: Create CallSession (status: ringing)
    SigServer->>FCM: Send high-priority push { sessionId, callerId }
    SigServer->>CallerApp: call:ringing { sessionId }
    FCM->>CalleeApp: Wake device, show system incoming call screen

    alt Callee accepts
        CalleeApp->>SigServer: call:accept { sessionId, sdpAnswer }
        SigServer->>SFU: Create transports for both parties
        SFU-->>SigServer: Transport parameters
        SigServer->>CallerApp: call:accepted { sessionId, sdpAnswer }
        CallerApp->>SigServer: call:ice-candidate { sessionId, candidate }
        CalleeApp->>SigServer: call:ice-candidate { sessionId, candidate }
        SigServer->>CallerApp: call:ice-candidate (from callee)
        SigServer->>CalleeApp: call:ice-candidate (from caller)
        SigServer->>SigServer: Update session status: connected
        Note over CallerApp,CalleeApp: Audio flows via SFU (DTLS-SRTP)

    else Callee rejects
        CalleeApp->>SigServer: call:reject { sessionId }
        SigServer->>CallerApp: call:rejected { sessionId }
        SigServer->>SigServer: Update session status: rejected

    else No answer within 30 s
        SigServer->>SigServer: Timeout → status: missed
        SigServer->>CallerApp: call:missed { sessionId }
        SigServer->>FCM: Missed call notification to callee
    end
```

---

## 3. Deepfake detection pipeline flow

```mermaid
flowchart TD
    A[Audio flows via WebRTC] --> B[SFU PlainTransport taps RTP stream]
    B --> C[Decode RTP to PCM]
    C --> D[Resample to 16 kHz mono]
    D --> E[Sliding window chunker\n1.5 s window, 0.5 s hop]
    E --> F[Publish chunk to RabbitMQ\ndetection.audio.sessionId.participantId]
    F --> G[AI Inference Service consumes chunk]
    G --> H[Normalize amplitude]
    H --> I[Extract LFCC features\n60 coefficients + delta + delta-delta]
    I --> J[Run AASIST model\nONNX Runtime INT8]
    J --> K[Raw score 0.0 – 1.0]
    K --> L[Apply EMA smoothing\nsmoothed = 0.3 × raw + 0.7 × previous]
    L --> M{{Classify smoothed score}}
    M -- < 0.35 --> N[Verdict: Likely real]
    M -- 0.35 – 0.65 --> O[Verdict: Suspicious]
    M -- > 0.65 --> P[Verdict: Likely synthetic]
    N --> Q[Publish score to RabbitMQ\ndetection.scores.sessionId.participantId]
    O --> Q
    P --> Q
    Q --> R[Signaling server consumes score]
    R --> S[Emit detection:score to client Socket.io]
    S --> T[Android/Web: update detection badge]
    R --> U{{Alert condition?\n2 consecutive updates ≥ suspicious}}
    U -- Yes --> V[Emit detection:alert to client]
    V --> W[Show alert banner in call UI]
    U -- No --> X[No alert]
    R --> Y{{Call ended?}}
    Y -- Yes --> Z[Flush score buffer to MongoDB\nDetectionLog record]
```

---

## 4. Call state machine

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> Dialing: User initiates call
    Idle --> Ringing: Incoming call received

    Dialing --> Ringing_Caller: Signaling server confirms callee reached
    Ringing_Caller --> Connected: Callee accepts
    Ringing_Caller --> Rejected: Callee rejects
    Ringing_Caller --> Missed: 30 s timeout, no answer

    Ringing --> Connected: User accepts
    Ringing --> Rejected_Local: User rejects

    Connected --> OnHold: User places on hold
    OnHold --> Connected: User resumes

    Connected --> Reconnecting: Network drop detected
    Reconnecting --> Connected: ICE restart succeeds within 30 s
    Reconnecting --> Dropped: 30 s reconnection timeout

    Connected --> Ended: Either party ends the call
    OnHold --> Ended: Either party ends the call

    Rejected --> [*]
    Rejected_Local --> [*]
    Missed --> [*]
    Ended --> [*]
    Dropped --> [*]
```

---

## 5. Group call flow

```mermaid
flowchart TD
    A[Host creates group call\ncall:group-create] --> B[Server creates Mediasoup Router\nand call session record]
    B --> C[Server sends call:incoming to all invitees via FCM]
    C --> D{Each invitee}
    D -- Accepts --> E[Server creates WebRtcTransport\nfor accepting participant]
    D -- Rejects --> F[Update participant status: rejected]
    D -- No answer 30s --> G[Update participant status: missed]
    E --> H[Participant's Producer added to Router]
    H --> I[All other active Consumers receive new stream]
    I --> J[Server emits call:participant-joined\nto all existing participants]
    J --> K{Is call still active?}
    K -- Yes --> D
    K -- No --> L[Session ended]

    H --> M[Audio tap → detection pipeline\nper participant stream]

    N[Host taps End for all] --> O[Server closes all transports]
    O --> P[Emit call:ended to all participants]
    P --> L

    Q[Participant leaves] --> R[Server closes participant transport]
    R --> S[Emit call:participant-left to others]
    S --> T{Was this the host?}
    T -- Yes --> U[Transfer host to next joined participant]
    U --> V[Emit call:host-transferred to all]
    T -- No --> K
```

---

## 6. Database entity relationship diagram

```mermaid
erDiagram
    USERS ||--o{ CONTACTS : has
    USERS ||--o{ CALLSESSIONS : initiates
    USERS ||--o{ DETECTIONLOGS : described_by
    USERS ||--o{ REFRESHTOKENS : owns
    CALLSESSIONS ||--o{ DETECTIONLOGS : generates
    CALLSESSIONS }o--|| USERS : includes_participants

    USERS {
        ObjectId _id PK
        string username
        string phone
        string email
        string passwordHash
        string passwordSalt
        string displayName
        string avatarUrl
        enum presenceStatus
        boolean isVerified
        boolean isActive
        date createdAt
        date updatedAt
    }

    CONTACTS {
        ObjectId _id PK
        ObjectId userId FK
        ObjectId contactUserId FK
        enum status
        ObjectId initiatedBy
        date createdAt
        date updatedAt
    }

    CALLSESSIONS {
        ObjectId _id PK
        enum sessionType
        ObjectId initiatorId FK
        array participants
        enum status
        date startedAt
        date connectedAt
        date endedAt
        number durationSeconds
        enum endReason
    }

    DETECTIONLOGS {
        ObjectId _id PK
        ObjectId sessionId FK
        ObjectId participantId FK
        string modelName
        string modelVersion
        array chunks
        enum overallVerdict
        number peakScore
        number averageScore
        boolean userFlagged
        date userFlaggedAt
        date createdAt
    }

    REFRESHTOKENS {
        ObjectId _id PK
        ObjectId userId FK
        string tokenHash
        date expiresAt
        date revokedAt
        date createdAt
    }
```

---

## 7. Audio analysis pipeline — component interaction

```mermaid
flowchart LR
    subgraph SFU[SFU Media Server]
        Producer[Audio Producer\nper participant]
        PlainT[PlainTransport\naudio tap]
        Chunker[Chunker\n1.5 s / 0.5 s hop]
    end

    subgraph MQ[RabbitMQ]
        AudioQ[(detection.audio\n.sessionId\n.participantId)]
        ScoreQ[(detection.scores\n.sessionId\n.participantId)]
    end

    subgraph AIService[Python AI Inference Service]
        Consumer[Queue Consumer]
        Preprocess[Preprocess\n16 kHz PCM → LFCC]
        Model[AASIST Model\nONNX Runtime INT8]
        EMA[EMA Smoother\nα = 0.3]
        Classify[Threshold Classifier]
        Publisher[Score Publisher]
    end

    subgraph Backend[Signaling Server]
        ScoreConsumer[Score Consumer]
        Emitter[Socket.io Emitter\ndetection:score]
        AlertLogic[Alert Logic\n2 consecutive ≥ suspicious]
        LogWriter[Log Writer\non call end]
    end

    Producer --> PlainT
    PlainT --> Chunker
    Chunker --> AudioQ
    AudioQ --> Consumer
    Consumer --> Preprocess
    Preprocess --> Model
    Model --> EMA
    EMA --> Classify
    Classify --> Publisher
    Publisher --> ScoreQ
    ScoreQ --> ScoreConsumer
    ScoreConsumer --> Emitter
    ScoreConsumer --> AlertLogic
    ScoreConsumer --> LogWriter
```

---

## 8. Security boundary diagram

```mermaid
flowchart TB
    subgraph PublicInternet[Public Internet]
        Android[Android Client]
        Browser[Web Browser Client]
    end

    subgraph TLSBoundary[TLS-Protected Transport Layer]
        WSS[WSS WebSocket\nSignaling]
        HTTPS[HTTPS REST API]
        DTLS[DTLS-SRTP\nWebRTC Media]
    end

    subgraph AuthBoundary[JWT-Authenticated API Layer]
        AuthAPI[Auth Endpoints\nPublic — rate limited]
        ProtectedAPI[Protected Endpoints\nJWT required]
        SocketEvents[Socket.io Events\nJWT on connect]
    end

    subgraph InternalServices[Internal Services — Not Public]
        SFU[SFU Media Server\nNo direct public access]
        AIService[AI Inference Service\nNo direct public access]
        MQ[RabbitMQ\nTLS + client cert]
        Redis[Redis\nInternal VPC only]
    end

    subgraph DataBoundary[Encrypted Data Layer]
        MongoDB[(MongoDB Atlas\nEncryption at rest)]
        S3[(AWS S3\nSSE-S3)]
    end

    Android --> TLSBoundary
    Browser --> TLSBoundary
    TLSBoundary --> AuthBoundary
    AuthBoundary --> InternalServices
    InternalServices --> DataBoundary

    Android -. No direct access .-> InternalServices
    Browser -. No direct access .-> InternalServices
    Android -. No direct access .-> DataBoundary
    Browser -. No direct access .-> DataBoundary
```

---

## 9. Contact relationship and call initiation permission flow

```mermaid
flowchart TD
    A[User A wants to call User B] --> B{{Are A and B\naccepted contacts?}}
    B -- No --> C[Call blocked — show error:\nAdd as contact first]
    B -- Yes --> D{{Has B blocked A?}}
    D -- Yes --> E[Call blocked — show:\nUser unavailable]
    D -- No --> F{{Is B's status Do Not Disturb?}}
    F -- Yes --> G[Call blocked — show:\nUser is unavailable right now]
    F -- No --> H{{Is B already on a call?}}
    H -- Yes --> I[Show B as busy\nCall not connected]
    H -- No --> J[Proceed with call:initiate]
```

---

## 10. Token lifecycle and refresh flow

```mermaid
sequenceDiagram
    participant App as Client App
    participant API as Auth API
    participant Redis as Redis\nRevocation Cache
    participant DB as MongoDB\nRefreshTokens

    App->>API: POST /api/auth/login
    API->>API: Validate credentials
    API->>DB: Create refresh token record (hash stored)
    API->>App: { accessToken (15 min JWT), refreshToken (opaque) }

    Note over App: Stores access token in memory\nStores refresh token in EncryptedSharedPreferences

    App->>API: Any protected request\nAuthorization: Bearer accessToken
    API->>Redis: Check token not revoked
    API->>API: Verify JWT signature and expiry
    API->>App: 200 OK with response

    Note over App: Access token about to expire

    App->>API: POST /api/auth/refresh { refreshToken }
    API->>DB: Lookup token by hash
    API->>DB: Check not revoked, not expired
    API->>DB: Mark old refresh token as revoked
    API->>DB: Create new refresh token record
    API->>App: { new accessToken, new refreshToken }

    Note over App: Logout

    App->>API: POST /api/auth/logout { refreshToken }
    API->>DB: Mark refresh token as revoked
    API->>Redis: Add access token jti to revocation list (until JWT expiry)
    API->>App: 200 OK
```

---

## 11. Model lifecycle diagram

```mermaid
flowchart TD
    A[Dataset collection\nASVspoof + WaveFake + augmentation] --> B[Model training\nPyTorch, AASIST]
    B --> C[Internal evaluation\nEER on ASVspoof 2021 + VoIP benchmark]
    C --> D{{EER < 5%\nFPR < 3%?}}
    D -- No --> E[Tune hyperparameters\nor revise augmentation]
    E --> B
    D -- Yes --> F[ONNX export + INT8 quantization]
    F --> G[Inference time benchmark\non target EC2 instance]
    G --> H{{Inference < 500 ms?}}
    H -- No --> I[Optimize: ONNX graph, batch size\nor switch to LCNN]
    I --> F
    H -- Yes --> J[Assign semantic version\ne.g., aasist-v1.0.0]
    J --> K[Deploy to staging\nSide-by-side with current model]
    K --> L[Shadow testing\nCompare scores on live calls without client display]
    L --> M{{Shadow results acceptable?}}
    M -- No --> E
    M -- Yes --> N[Deploy to production\nCanary 10% → 100%]
    N --> O[Monitor: user flag rate,\nFPR, score distribution]
    O --> P{{Flag rate > 10%\nor distribution shift?}}
    P -- Yes --> Q[Trigger retraining cycle]
    Q --> A
    P -- No --> R[Quarterly review\ncheck against new WaveFake vocoders]
    R --> P
```
