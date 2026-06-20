# UI/UX Design Document

**Project:** RingWave  
**Prepared for:** Internal design and engineering team  
**Prepared on:** 2026-06-06  
**Document status:** Draft for implementation planning

---

## 1. UX principles

1. **The call is primary.** The calling experience must feel as natural and low-friction as any consumer VoIP app. Detection is a layer on top of the call, not a replacement for call clarity.
2. **Detection must inform, not alarm.** Authenticity scores should be visible and readable without creating anxiety on every call. Alerts fire only when genuinely warranted and must never disrupt the call controls.
3. **Never block the call controls.** The mute button, speakerphone, and end-call button must always be reachable in one tap. Nothing — not an alert, not a score update, not an animation — may cover them.
4. **Status through color and text together.** Every detection state is expressed with both a color and a label. Color alone is never the sole indicator, because users with color vision deficiencies must receive the same information.
5. **Offline and degraded states are first-class citizens.** The app must behave predictably and display useful UI when the connection is slow, the AI service is unavailable, or the call is reconnecting. Blank screens or frozen states are not acceptable.
6. **Minimal taps to reach a call.** From the home screen, a user must be able to place a call to a recent contact in at most two taps.

---

## 2. Information architecture

```
RingWave (Android App)
├── Auth Flow (unauthenticated)
│   ├── Welcome / Landing Screen
│   ├── Register Screen
│   ├── OTP Verification Screen
│   └── Login Screen
│
└── Main App (authenticated)
    ├── Home — Recent + Contacts
    ├── Contacts
    │   ├── Contact List
    │   ├── Contact Search
    │   ├── Contact Profile
    │   ├── Contact Requests (incoming)
    │   └── Block List
    ├── Calls
    │   ├── Outgoing Call Screen
    │   ├── Incoming Call Screen (system overlay)
    │   ├── Active Call Screen — 1:1
    │   ├── Active Call Screen — Group
    │   └── DTMF Keypad (sheet within active call)
    ├── History
    │   ├── Call History List
    │   ├── Call Detail
    │   └── Detection Report
    └── Settings
        ├── Profile
        ├── Presence
        ├── Notifications
        ├── Account and Privacy
        └── About
```

---

## 3. Auth screens

### 3.1 Welcome screen

```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│         [RingWave wordmark]         │
│                                     │
│   Internet calling with voice       │
│   authenticity protection           │
│                                     │
│                                     │
│   ┌─────────────────────────────┐   │
│   │         Create account      │   │
│   └─────────────────────────────┘   │
│                                     │
│         Already have an account?    │
│              Sign in                │
│                                     │
└─────────────────────────────────────┘
```

### 3.2 Register screen

```
┌─────────────────────────────────────┐
│  ←  Create your account            │
│                                     │
│   Display name                      │
│   ┌─────────────────────────────┐   │
│   │ Enter your name             │   │
│   └─────────────────────────────┘   │
│                                     │
│   Username                          │
│   ┌─────────────────────────────┐   │
│   │ Choose a username           │   │
│   └─────────────────────────────┘   │
│                                     │
│   Phone or email                    │
│   ┌─────────────────────────────┐   │
│   │ +91 9xxxxxxxxx              │   │
│   └─────────────────────────────┘   │
│                                     │
│   Password                          │
│   ┌─────────────────────────────┐   │
│   │ ••••••••••                  │   │
│   └─────────────────────────────┘   │
│                                     │
│   ┌─────────────────────────────┐   │
│   │          Continue           │   │
│   └─────────────────────────────┘   │
│                                     │
│   By continuing you agree that      │
│   RingWave will analyze call audio  │
│   for deepfake detection. Audio is  │
│   not stored. Read privacy policy   │
│                                     │
└─────────────────────────────────────┘
```

**Notes:** The consent notice is required, not optional, and must appear on this screen before the Continue button, not after. The privacy policy link must open a full in-app browser view.

### 3.3 OTP verification screen

```
┌─────────────────────────────────────┐
│  ←  Verify your number             │
│                                     │
│   We sent a code to                 │
│   +91 98XXXXXXXX                    │
│                                     │
│   ┌────┐  ┌────┐  ┌────┐  ┌────┐   │
│   │    │  │    │  │    │  │    │   │
│   └────┘  └────┘  └────┘  └────┘   │
│   ┌────┐  ┌────┐                   │
│   │    │  │    │                   │
│   └────┘  └────┘                   │
│                                     │
│   Resend code in 45 s               │
│                                     │
│   ┌─────────────────────────────┐   │
│   │           Verify            │   │
│   └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

**Error state:** If OTP is wrong, each digit box turns red and a message reads "Incorrect code. X attempts remaining."

---

## 4. Home screen

```
┌─────────────────────────────────────┐
│  RingWave          [avatar]  [⚙]    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 🔍  Search or add contact  │    │
│  └─────────────────────────────┘    │
│                                     │
│  Recent                             │
│  ─────────────────────────────────  │
│  [avatar]  Priya Sharma      [📞]   │
│            ✓ Missed · 2h ago        │
│            ● Likely real            │
│                                     │
│  [avatar]  Rahul Mehta      [📞]   │
│            Incoming · 1d ago        │
│            ● Likely real            │
│                                     │
│  [avatar]  Unknown number   [📞]   │
│            Outgoing · 3d ago        │
│            ⚠ Suspicious            │
│                                     │
│  ─────────────────────────────────  │
│  All contacts  ›                    │
│  ─────────────────────────────────  │
│  [avatar]  Amit Verma       [📞]   │
│            ● Online                 │
│  [avatar]  Sneha Iyer       [📞]   │
│            ○ Offline 2h ago         │
│                                     │
│─────────────────────────────────────│
│  [🏠 Home]  [👥 Contacts]  [🕐 Calls] │
└─────────────────────────────────────┘
```

**Notes:** The detection verdict shown in recent calls is the overall verdict for that call, not a live score. The call button on each row initiates an immediate call. The search bar supports username and phone search.

---

## 5. Contact profile screen

```
┌─────────────────────────────────────┐
│  ←  Contact                        │
│                                     │
│              [large avatar]         │
│           Priya Sharma              │
│           @priyasharma              │
│            ● Online                 │
│                                     │
│   ┌─────────────────────────────┐   │
│   │        Audio call           │   │
│   └─────────────────────────────┘   │
│                                     │
│  Call history with Priya            │
│  ─────────────────────────────────  │
│  Today, 2:14 PM · 8m 32s           │
│  Incoming  ● Likely real            │
│  ─────────────────────────────────  │
│  Yesterday · 6m 01s                 │
│  Outgoing  ● Likely real            │
│                                     │
│  ─────────────────────────────────  │
│  Block Priya Sharma                 │
│  Remove contact                     │
│                                     │
└─────────────────────────────────────┘
```

---

## 6. Outgoing call screen

```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│           [large avatar]            │
│         Priya Sharma                │
│         @priyasharma                │
│                                     │
│           Calling...                │
│                                     │
│                                     │
│                                     │
│                                     │
│             [  🔴  ]                │
│            End call                 │
│                                     │
└─────────────────────────────────────┘
```

**States:**
- **Calling...** → waiting for callee to respond.
- **Ringing...** → signaling server confirmed the callee received the call.
- **Call rejected** → callee declined; auto-returns to previous screen after 2 seconds.
- **Not available** → timeout or callee unreachable; shows missed call message.
- **Reconnecting...** → network dropped; timer counts down.

---

## 7. Active call screen — one-to-one

```
┌─────────────────────────────────────┐
│                                     │
│   ┌─────────────────────────────┐   │
│   │  ● Likely real   Priya S.  │   │  ← Detection badge (top of card)
│   └─────────────────────────────┘   │
│                                     │
│           [large avatar]            │
│         Priya Sharma                │
│                                     │
│           00:03:42                  │
│                                     │
│         [ ~~~ waveform ~~~ ]        │  ← Active speaking waveform
│                                     │
│                                     │
│   ┌───────┐  ┌───────┐  ┌───────┐  │
│   │  🎤   │  │  🔊   │  │  ⌨   │  │
│   │  Mute │  │Speaker│  │  Pad  │  │
│   └───────┘  └───────┘  └───────┘  │
│                                     │
│   ┌───────┐             ┌───────┐  │
│   │  ⏸   │             │  🔴   │  │
│   │  Hold │             │  End  │  │
│   └───────┘             └───────┘  │
│                                     │
└─────────────────────────────────────┘
```

### 7.1 Detection badge states

| State | Color | Label |
|---|---|---|
| Initializing | Grey | Analyzing... |
| Likely real | Green | ● Likely real |
| Suspicious | Amber | ⚠ Suspicious |
| Likely synthetic | Red | ✕ Likely synthetic |
| Silence | Grey | — Silent |
| Unavailable | Grey | Analysis unavailable |
| Reconnecting | Grey | Reconnecting... |

The badge is tappable. Tapping opens a bottom sheet with a brief explanation: "RingWave analyzes voice patterns to detect AI-generated or cloned speech. This score is based on the last few seconds of audio and updates continuously."

### 7.2 Alert banner (suspicious)

```
┌─────────────────────────────────────────────────────┐
│  ⚠  Voice sounds suspicious. Stay cautious.   [✕]  │
└─────────────────────────────────────────────────────┘
```

- Appears at the top of the screen, below the status bar.
- Does not cover any call control buttons.
- Auto-dismisses after 5 seconds or on user tap of ✕.
- Shown once per threshold crossing per call.

### 7.3 Alert banner (synthetic)

```
┌─────────────────────────────────────────────────────┐
│  ✕  Voice likely synthetic. This may be a deepfake.  [✕]  │
└─────────────────────────────────────────────────────┘
```

- Same placement rules as the suspicious banner.
- Red background; does not auto-dismiss. User must tap ✕.
- Shown once per synthetic crossing per call, regardless of subsequent score fluctuations.

### 7.4 Hold state

```
│           [large avatar, desaturated]               │
│         Priya Sharma                                │
│           Call on hold — 00:01:14                   │
│                                                     │
│   ┌───────┐             ┌───────┐                  │
│   │  ▶    │             │  🔴   │                  │
│   │ Resume│             │  End  │                  │
│   └───────┘             └───────┘                  │
```

Detection badge shows paused state during hold since no audio is flowing.

---

## 8. Active call screen — group

```
┌─────────────────────────────────────┐
│   Group call  3/8              [+]  │  ← Add participant
│                                     │
│  ┌─────────────────────────────┐    │
│  │ [av] Rahul       ● Real    │    │
│  │       Speaking...          │    │
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ [av] Priya    ⚠ Suspicious │    │
│  │       Muted                │    │  ← Mute indicator
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ [av] You (host)  ● Real    │    │
│  │       Active               │    │
│  └─────────────────────────────┘    │
│                                     │
│   00:05:21                          │
│                                     │
│   ┌───────┐  ┌───────┐  ┌───────┐  │
│   │  🎤   │  │  🔊   │  │  ⌨   │  │
│   │  Mute │  │Speaker│  │  Pad  │  │
│   └───────┘  └───────┘  └───────┘  │
│                                     │
│   ┌──────────────┐  ┌───────────┐  │
│   │  Leave call  │  │  End for  │  │
│   │              │  │   all ⚑  │  │
│   └──────────────┘  └───────────┘  │
│                                     │
└─────────────────────────────────────┘
```

**Notes:**
- Each participant row shows: avatar, display name, detection badge, speaking or muted state.
- Host has "End for all" button in addition to "Leave call."
- Tapping a participant row (for host) opens a bottom sheet with Mute and Remove options.
- The [+] button opens a contact picker limited to contacts not already in the call, disabled if participant count is 8.
- Detection badge updates per-participant independently.
- Speaking indicator is driven by Mediasoup's AudioLevelObserver.

---

## 9. DTMF keypad sheet

Triggered by the keypad button during an active call. Slides up as a bottom sheet over the call screen, leaving the end-call button visible.

```
┌─────────────────────────────────────┐
│  ─────────────────────              │
│                                     │
│   ┌─────────────────────────────┐   │
│   │       1 2 3 4 5             │   │  ← Digit display
│   └─────────────────────────────┘   │
│                                     │
│    ┌───┐   ┌───┐   ┌───┐           │
│    │ 1 │   │ 2 │   │ 3 │           │
│    └───┘   └───┘   └───┘           │
│    ┌───┐   ┌───┐   ┌───┐           │
│    │ 4 │   │ 5 │   │ 6 │           │
│    └───┘   └───┘   └───┘           │
│    ┌───┐   ┌───┐   ┌───┐           │
│    │ 7 │   │ 8 │   │ 9 │           │
│    └───┘   └───┘   └───┘           │
│    ┌───┐   ┌───┐   ┌───┐           │
│    │ * │   │ 0 │   │ # │           │
│    └───┘   └───┘   └───┘           │
│                          [⌫]       │
│                                     │
└─────────────────────────────────────┘
```

---

## 10. Call history screen

```
┌─────────────────────────────────────┐
│  Call history                [🔍]   │
│                                     │
│  [All] [Missed] [Incoming] [Outgoing]│
│                                     │
│  Today                              │
│  ─────────────────────────────────  │
│  [av]  Priya Sharma                 │
│        Incoming · 2:14 PM · 8m 32s  │
│        ● Likely real         [📞]   │
│  ─────────────────────────────────  │
│  [av]  Unknown +91 98XXXXXXXX       │
│        Outgoing · 11:02 AM · 1m 4s  │
│        ⚠ Suspicious         [📞]   │
│                                     │
│  Yesterday                          │
│  ─────────────────────────────────  │
│  [av]  Rahul Mehta                  │
│        Missed · 8:45 PM             │
│                              [📞]   │
│  ─────────────────────────────────  │
│  [av]  Group call (Priya, Rahul +1) │
│        Outgoing · 7:30 PM · 22m 15s │
│        ● Likely real         [📞]   │
│                                     │
└─────────────────────────────────────┘
```

**Notes:**
- The call-back button (📞) on each row immediately initiates an outgoing call to that contact.
- Tapping the row body opens the Call Detail screen.
- Missed calls show no detection verdict because no audio flowed.
- Swipe left on a row reveals a Delete option.

---

## 11. Call detail and detection report screen

```
┌─────────────────────────────────────┐
│  ←  Call detail                    │
│                                     │
│  With: Priya Sharma                 │
│  Today, 2:14 PM — 2:22 PM          │
│  Duration: 8 minutes 32 seconds     │
│  Type: Incoming one-to-one          │
│  Status: Completed                  │
│                                     │
│  Detection report                   │
│  ─────────────────────────────────  │
│                                     │
│  Overall verdict: ● Likely real     │
│  Peak score: 0.21                   │
│  Average score: 0.13                │
│                                     │
│  Score timeline                     │
│  ┌─────────────────────────────┐    │
│  │  1.0                        │    │
│  │  0.65 ─ ─ ─ ─ ─ ─ ─ ─ ─   │    │  ← Synthetic threshold line
│  │  0.35 ─ ─ ─ ─ ─ ─ ─ ─ ─   │    │  ← Suspicious threshold line
│  │  0.0  ___________________  │    │
│  │       0   2   4   6   8min │    │
│  └─────────────────────────────┘    │
│                                     │
│  Model: aasist-v1.0.0               │
│                                     │
│  Was this detection accurate?       │
│  [Yes, looks right]  [Flag as wrong]│
│                                     │
│  ─────────────────────────────────  │
│            Delete this record       │
│                                     │
└─────────────────────────────────────┘
```

**Notes:**
- The timeline chart is a line chart of smoothed scores over the call duration. The two threshold lines are drawn as dashed horizontal rules.
- The y-axis is fixed at 0–1.0. The x-axis is the call duration.
- "Flag as wrong" opens a short sheet asking: "What was wrong?" with two options — "Real voice was flagged as suspicious/synthetic" and "Synthetic voice was not flagged." An optional free text field allows the user to add context. Submitting requires the user to confirm they are submitting feedback to the RingWave team.
- The model version is displayed so users and support can identify which model version produced the result.

---

## 12. Settings screens

### 12.1 Settings root

```
┌─────────────────────────────────────┐
│  ←  Settings                       │
│                                     │
│  [large avatar]  Arnav Sharma       │
│                  @arnav             │
│                  Edit profile  ›    │
│                                     │
│  ─────────────────────────────────  │
│  Presence                       ›   │
│  Notifications                  ›   │
│  Account and privacy            ›   │
│  About RingWave                 ›   │
│                                     │
│  ─────────────────────────────────  │
│            Sign out                 │
│                                     │
└─────────────────────────────────────┘
```

### 12.2 Account and privacy

```
┌─────────────────────────────────────┐
│  ←  Account and privacy            │
│                                     │
│  Detection settings                 │
│  ─────────────────────────────────  │
│  Alert sensitivity                  │
│  Standard (recommended)         ›   │
│                                     │
│  Data and privacy                   │
│  ─────────────────────────────────  │
│  View privacy policy            ›   │
│  Export my data                 ›   │
│  Delete all detection logs          │
│                                     │
│  ─────────────────────────────────  │
│  ─────────────────────────────────  │
│                                     │
│  ⚠  Danger zone                    │
│  Delete account and all data        │
│                                     │
└─────────────────────────────────────┘
```

**Note on alert sensitivity:** This allows the user to adjust the suspicious threshold. Standard is the default (0.35). Strict lowers the threshold to 0.25, generating more alerts. Relaxed raises it to 0.50, generating fewer. This preference is stored server-side so that it applies on all devices.

---

## 13. Contact management screens

### 13.1 Contact search and add

```
┌─────────────────────────────────────┐
│  ←  Add contact                    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 🔍  Search by username or   │    │
│  │     phone number            │    │
│  └─────────────────────────────┘    │
│                                     │
│  Results                            │
│  ─────────────────────────────────  │
│  [av]  Priya Sharma                 │
│        @priyasharma · ● Online      │
│                       [Add contact] │
│  ─────────────────────────────────  │
│  [av]  Priya Patel                  │
│        @priyapatel · ○ Offline      │
│                       [Add contact] │
│                                     │
└─────────────────────────────────────┘
```

### 13.2 Contact requests screen

```
┌─────────────────────────────────────┐
│  ←  Contact requests               │
│                                     │
│  Received                           │
│  ─────────────────────────────────  │
│  [av]  Vikram Singh                 │
│        @vikrams                     │
│        [Accept]         [Decline]   │
│                                     │
│  Sent                               │
│  ─────────────────────────────────  │
│  [av]  Neha Joshi                   │
│        @nehajoshi · Pending         │
│                       [Withdraw]    │
│                                     │
└─────────────────────────────────────┘
```

---

## 14. Web dashboard layout

The web dashboard follows the same information architecture as the Android app but uses a two-panel layout on desktop screens.

```
┌──────────────┬───────────────────────────────────────┐
│  RingWave    │                                        │
│              │                                        │
│  [Search]    │        Select a contact or             │
│              │        recent call to start.           │
│  Contacts    │                                        │
│  ──────────  │                                        │
│  [av] Priya  │                                        │
│  ● Online    │                                        │
│              │                                        │
│  [av] Rahul  │                                        │
│  ○ Offline   │                                        │
│              │                                        │
│  ──────────  │                                        │
│  History     │                                        │
│  Settings    │                                        │
└──────────────┴───────────────────────────────────────┘
```

When a call is active, the right panel shows the active call view. On mobile browser, the layout collapses to single-column, matching the Android layout closely.

---

## 15. Design system draft

### 15.1 Color tokens

| Token | Purpose | Value |
|---|---|---|
| `color-brand-primary` | Primary CTA, links | #5B5BF5 |
| `color-brand-secondary` | Secondary accent | #A78BFA |
| `color-verdict-real` | Detection badge: real | #16A34A |
| `color-verdict-suspicious` | Detection badge: suspicious | #D97706 |
| `color-verdict-synthetic` | Detection badge: synthetic | #DC2626 |
| `color-verdict-neutral` | Badge: unavailable, silence, initializing | #6B7280 |
| `color-surface-primary` | Card and sheet backgrounds | #FFFFFF (light), #1C1C1E (dark) |
| `color-surface-secondary` | Screen backgrounds | #F3F4F6 (light), #2C2C2E (dark) |
| `color-text-primary` | Primary text | #111827 (light), #F9FAFB (dark) |
| `color-text-secondary` | Secondary text, timestamps | #6B7280 |
| `color-border` | Dividers, input borders | #E5E7EB (light), #3A3A3C (dark) |
| `color-alert-suspicious-bg` | Suspicious alert banner background | #FEF3C7 |
| `color-alert-synthetic-bg` | Synthetic alert banner background | #FEE2E2 |
| `color-destructive` | Delete and danger actions | #DC2626 |

### 15.2 Typography

| Token | Usage | Size / Weight |
|---|---|---|
| `type-title-large` | Screen titles | 22 sp / Medium |
| `type-title-medium` | Section headers | 18 sp / Medium |
| `type-body-primary` | Contact names, call details | 16 sp / Regular |
| `type-body-secondary` | Timestamps, subtitles | 14 sp / Regular |
| `type-label` | Badge labels, button text | 13 sp / Medium |
| `type-caption` | Model version, legal | 12 sp / Regular |
| `type-mono` | DTMF digit display, scores | 16 sp / Monospace |

### 15.3 Spacing

Base unit: 4 dp. All spacing values are multiples of 4: 4, 8, 12, 16, 20, 24, 32, 48, 64.

Screen horizontal padding: 20 dp. Card internal padding: 16 dp. Row divider height: 1 dp.

### 15.4 Component specifications

**Detection badge:** Height 32 dp, horizontal padding 12 dp, border radius 16 dp. Contains a status dot (8 dp) and a label string. Background is a 10% opacity tint of the verdict color. Text uses `color-verdict-*` at full opacity. The badge must have a minimum touch target of 48 dp when tappable.

**Call control buttons:** Minimum 56 dp × 56 dp, border radius 28 dp. Mute and Speakerphone use an outlined style when inactive, filled when active. End call button uses `color-destructive` background always.

**Alert banner:** Full width, 52 dp height minimum, 16 dp horizontal padding, 12 dp vertical padding. Appears below the status bar. Icon on the left (16 dp), message text in the center, dismiss icon (24 dp) on the right. Must not be taller than 20% of the screen height.

---

## 16. Accessibility

1. All touch targets must be at least 48 dp × 48 dp.
2. All color-based state indicators (detection badge, alert banners) must include a text label. The app must not rely solely on color to convey call or detection state.
3. The incoming call screen must support TalkBack. Call accept and reject buttons must have content descriptions.
4. The DTMF keypad must produce both audible tones and haptic feedback on each key press.
5. The active call screen must announce significant detection state changes through accessibility announcements (e.g., `accessibilityLiveRegion` or equivalent): "Voice now suspicious" and "Voice likely synthetic" as accessible announcements.
6. Font size scaling must be respected. The layout must not break when the system font size is set to 1.3× or 1.5×.
7. The detection report timeline chart must have an accessible text summary: "Average score: 0.13. Peak score: 0.21. Overall verdict: Likely real." for screen reader users.
8. All images and avatars must have content descriptions.

---

## 17. UX acceptance criteria

1. Given the app is cold-started, when the home screen appears, then recent contacts and call history are visible and interactive within 3 seconds.
2. Given a user taps a contact's call button, when the outgoing call screen appears, then the ringing animation plays within 500 ms.
3. Given an active call, when the detection badge changes from green to amber, then the color and label update is visible within 2 seconds and the change is perceptible without tapping the badge.
4. Given a synthetic alert is shown, when the user taps the end-call button, then the button responds immediately; the alert must not block or delay the tap.
5. Given a user taps the detection badge, when the explanation sheet opens, then the sheet appears within 200 ms.
6. Given a detection report is opened, when the score timeline chart is rendered, then both threshold lines and the score trace are visible without horizontal scrolling.
7. Given the app is in dark mode, when any screen is displayed, then no text uses a contrast ratio below 4.5:1 against its background.
8. Given TalkBack is enabled, when the incoming call screen appears, then the Accept and Reject buttons are announced clearly with their action labels.
