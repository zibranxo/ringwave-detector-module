# Audio Deepfake Detection: Two-Stage Cascade Architecture

**Target system:** RingWave (audio calling platform, India deployment)
**Scope:** Architecture recommendation for a cascaded detector that minimizes inference cost without sacrificing detection quality, plus a Hindi/Indic data strategy and deployment plan.

---

## 1. Executive Summary

The proposed two-stage design — a lightweight, high-recall filter followed by a heavyweight, high-precision verifier that only runs on flagged audio — is sound and matches patterns already used in production anti-spoofing systems. The key reframe worth internalizing: **the cascade is primarily a cost-control mechanism, not a latency-reduction trick.** Modern single-stage models can already hit very low latency on their own; the win from cascading comes from never running the expensive model on the ~90%+ of traffic that's genuine.

Recommended shape:

| | Stage 1 (Filter) | Stage 2 (Verifier) |
|---|---|---|
| Objective | Maximize recall (catch nearly all fakes) | Maximize precision (kill false positives) |
| Architecture | Small CNN/conv-recurrent on mel-spectrogram or raw waveform | Pretrained multilingual SSL encoder (XLSR-53 / WavLM-large) + AASIST-style head |
| Training approach | From scratch, retrained frequently on real traffic | Parameter-efficient fine-tuning (prompt/adapter tuning) on top of frozen/lightly-tuned encoder |
| Hosting | CPU, scales with total call volume | GPU, scales with flagged volume only (autoscale-to-zero) |
| Params | ~100K–1M | ~300M frozen + a small trainable head/prompt set |

---

## 2. Why the Cascade Works (Cost Math)

Total inference cost ≈ Cost(Stage 1) × all audio + Cost(Stage 2) × flagged audio.

If real-world deepfake prevalence is low (e.g., 1–2% of calls) and Stage 1 is tuned for high recall with a 5–8% false-positive rate, only roughly 7–10% of total audio ever reaches Stage 2. That's an 85–90%+ reduction in GPU spend versus running the heavy model on everything, with no loss in end-to-end recall (Stage 1's false positives just cost a cheap Stage 2 check, not a missed fake).

A single, well-optimized model can already achieve sub-50ms latency with broad language coverage in commercial systems, so the cascade is not about beating that on a single decision — it's about not paying GPU cost for every call when most calls are genuine.

---

## 3. Stage 1: High-Recall Filter

**Architecture candidates** (any of these are reasonable; differences are marginal at this scale):
- A small conv-recurrent net on raw waveform, in the style of RawNetLite. Reported numbers: ~99.7% F1 / 0.25% EER in-domain, but this drops sharply to ~83% F1 / 16.4% EER on out-of-distribution data — a useful reminder that in-domain benchmark numbers from small models are optimistic and shouldn't be trusted at face value.
- A small CNN on mel-spectrogram features, tuned specifically for telephony-quality audio. A comparable telephony-focused system reported ~96.4% accuracy and ~3.9% EER with ~97.9% recall, which is a more realistic reference point for a calling-platform deployment than generic benchmark numbers.

**Training approach:** Train from scratch. It's cheap, fast to iterate, and lets you control the training distribution exactly (telephony codec artifacts, Hindi/Hinglish speech, background noise) rather than inheriting whatever bias a public checkpoint has. Retrain on a regular cadence (e.g., weekly/biweekly) as real call data and confirmed false positives/negatives accumulate.

**Threshold strategy:** Deliberately bias toward recall. Treat the threshold as a tunable config value, not a fixed constant — see Section 8 on prevalence tuning.

**Don't classify whole calls.** Run Stage 1 (and Stage 2) on overlapping windows, 3–4 seconds with 50% overlap, gated by a cheap voice-activity-detection step (e.g., WebRTC VAD) so neither model spends compute on silence or hold music. Windowing also protects against partial/spliced deepfakes, where only a few seconds of a call are synthetic — a whole-call classifier can dilute a short fake segment into a "mostly real" verdict, while a windowed approach catches and localizes it.

---

## 4. Stage 2: High-Precision Verifier

**Architecture:** A pretrained multilingual self-supervised speech encoder (XLSR-53 or WavLM-large) feeding into an AASIST-style dual-graph spectro-temporal attention classification head. This is the one stage where starting from a pretrained foundation model clearly beats training from scratch — replicating the acoustic representations these models learned from massive unlabeled multilingual audio is not realistic on a project-level compute budget.

**Fine-tuning approach:** Prefer parameter-efficient tuning (prompt tuning / adapter-style tuning on top of a frozen or lightly-tuned encoder) over full fine-tuning. Recent work in this space reports needing roughly 450x fewer trainable parameters than full fine-tuning while still reaching competitive accuracy. This matters most when labeled data is small (your current situation), since full fine-tuning a 300M+ parameter encoder on a small dataset risks overfitting and is also the more expensive path. Start with parameter-efficient tuning; only justify full fine-tuning later if you have enough labeled data to need it.

**On benchmark numbers:** Recent literature reports an average EER around 3.6% for a wavelet-prompt-tuned XLSR+AASIST setup — but that number is from a much harder "all-type" benchmark covering speech, singing, music, and sound deepfakes combined. For pure speech anti-spoofing (your actual use case), fine-tuned SSL+AASIST setups typically land well under 2% EER. Don't anchor expectations to cross-type numbers.

**Don't over-rely on ASVspoof 2019.** It's old enough that modern voice-cloning tools (ElevenLabs-class, neural-codec TTS) reliably beat detectors trained only on it. Evaluate on more recent in-the-wild and codec-augmented sets, and weight your own collected data heavily once you have it.

---

## 5. Multilingual / Hindi Data Strategy

You currently have no labeled Hindi/Indic audio for fine-tuning — this is a known and real gap. Public anti-spoofing data and checkpoints are heavily English/Chinese-skewed, and detection performance degrades on language mismatch; existing Hindi-specific deepfake datasets are thin and report harder detection conditions than English-centric ones.

**Bootstrap plan:**
- **Genuine speech:** AI4Bharat's open corpora (IndicVoice, Shrutilipi, IndicSUPERB) and the Hindi portion of M-AILABS. Free, reasonably large, good starting point.
- **Synthetic/fake speech:** Generate it yourself, since labeled Hindi fake data barely exists publicly. Run open multilingual TTS/voice-clone models (XTTS-v2, Indic Parler-TTS, AI4Bharat's TTS stack) against your genuine Hindi clips. Supplement with the Hindi slice of MLAAD (a 40-language synthetic-speech anti-spoofing dataset built from ~119 TTS models).
- **Augmentation is non-negotiable:** Apply telephony-style degradation to all of it — 8kHz narrowband resampling, codec compression, background noise injection. A model trained only on clean studio audio will look great in testing and fail on real calls.
- **Stage 2 isn't starting from zero on Hindi** even without labeled Hindi data: XLSR-53 and WavLM were pretrained on multilingual audio that includes Hindi, so the encoder already carries useful Hindi acoustic representations. Fine-tune the head on whatever data you have first, layer in Hindi-specific data as you generate it. Ship v1 on cross-lingual transfer rather than waiting for a large Hindi-labeled set.

---

## 6. Deployment Architecture (Both Stages Server-Side)

With both stages on your own servers, the design simplifies:
- **Stage 1:** CPU instances, autoscaled with total call volume. Cheap enough to run on every window of every call.
- **Stage 2:** Separate GPU-backed service, autoscaled toward zero when idle. Connected to Stage 1 via a queue or internal routing call rather than baked into one monolith — this keeps GPU cost tracking *flagged* volume, not total volume, which is the entire point of the cascade.
- No edge/cloud security or transmission concerns to design around, since nothing leaves your own infrastructure between stages.

---

## 7. Prevalence and Threshold Tuning

Fake prevalence in real traffic is currently unknown — don't hardcode a guess into the architecture.

- Launch with a conservative assumption (low prevalence, general screening).
- Set Stage 1 to flag roughly 5–10% of traffic as a starting point.
- Instrument both stages from day one: log Stage 1's flag rate and Stage 2's accept/reject rate continuously.
- After a few weeks of real traffic, you'll have actual prevalence and false-positive data. Tune the threshold against that, not against EER numbers from a paper.

---

## 8. Risks and Operational Watchpoints

- **Stage 1 is the single point of failure for recall.** An attacker who specifically tunes an attack to slip under the cheap filter's threshold never reaches Stage 2 at all. It needs its own adversarial red-teaming, not just accuracy metrics on a clean test set.
- **Operational complexity:** two models to keep versioned and in sync, two sets of false positive/negative monitoring, and ideally a feedback loop where Stage 2's confirmed verdicts feed back into Stage 1's retraining (hard-negative mining) so the cheap filter keeps tightening over time.
- **Stale benchmarks give false confidence.** Cross-check against recent in-the-wild/codec-augmented data, not just legacy academic sets.

---

## 9. Train-from-Scratch vs. Fine-Tune — Verdict

- **Stage 1: train from scratch.** Cheap, fast to retrain, full control over training distribution. No reason to inherit a public checkpoint's biases here.
- **Stage 2: fine-tune a pretrained multilingual SSL encoder.** Training an encoder of this scale from scratch is not a realistic option at project scope. Use parameter-efficient tuning first; escalate to full fine-tuning only once labeled data volume justifies it.

---

## 10. Next Steps

1. Stand up Stage 1 training pipeline on synthetic + scratch-collected telephony data; ship with a conservative flag rate.
2. Stand up Stage 2 as a frozen/lightly-tuned XLSR or WavLM encoder + AASIST head, parameter-efficient tuning.
3. Build the Hindi data pipeline (AI4Bharat sources + self-generated TTS attacks + MLAAD Hindi slice + telephony augmentation).
4. Instrument flag rate / accept-reject rate from day one; revisit thresholds once real traffic data exists.
5. Schedule periodic adversarial testing specifically against Stage 1's blind spots.
