from collections import deque
from dataclasses import dataclass

@dataclass
class WindowVerdict:
    start_s: float
    end_s: float
    stage: int          # 1 or 2
    label: str          # "clear" | "verified-genuine" | "verified-fake"
    score: float

class CallSession:
    def __init__(self, call_id: str, debounce_window_s: float = 10.0,
                 debounce_count: int = 2, high_confidence: float = 0.9):
        self.call_id = call_id
        self.log: list[WindowVerdict] = []          # forensic record, append-only
        self.recent_fakes: deque = deque()           # for live debounce only
        self.debounce_window_s = debounce_window_s
        self.debounce_count = debounce_count
        self.high_confidence = high_confidence
        self.alert_fired = False

    def record(self, v: WindowVerdict):
        self.log.append(v)
        if v.label == "verified-fake":
            self.recent_fakes.append(v)
            cutoff = v.end_s - self.debounce_window_s
            while self.recent_fakes and self.recent_fakes[0].end_s < cutoff:
                self.recent_fakes.popleft()
            if (len(self.recent_fakes) >= self.debounce_count
                    or v.score > self.high_confidence):
                self._fire_live_alert(v)

    def _fire_live_alert(self, trigger: WindowVerdict):
        if not self.alert_fired:
            self.alert_fired = True
            print(f"[ALERT] Call {self.call_id}: Deepfake detected! Triggered by score {trigger.score:.2f} at {trigger.start_s:.2f}s - {trigger.end_s:.2f}s")
            # surface in-call UI warning, e.g. via the existing RTC signalling channel
        # (left to RingWave's call UI layer to implement)

    def call_level_verdict(self) -> str:
        """Post-call / report-level decision: any confirmed-fake window flags
        the whole call. Do not average scores across windows for this -- a
        short spliced fake diluted into a 'mostly real' average is exactly
        the partial-deepfake failure mode every source document (correctly)
        warns about."""
        return "fake" if any(v.label == "verified-fake" for v in self.log) else "genuine"
