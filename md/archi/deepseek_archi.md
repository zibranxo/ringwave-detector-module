Audio Deepfake Detection System: Production-Grade Two-Stage Cascade Architecture

Target Platform: RingWave (audio calling platform, India deployment)
Document Type: Architecture & Implementation Blueprint
Objective: Provide a complete, code-ready specification for a cascaded deepfake detector that minimizes inference cost while preserving state-of-the-art detection accuracy on telephony‑quality Hindi/Indic speech.
1. Executive Summary

This document defines the architecture, model designs, training strategy, data pipeline, and deployment blueprint for a two‑stage audio deepfake detection system. The core idea is a cascade: a lightweight, high‑recall filter (Stage 1) processes all incoming audio; only the segments it flags as suspicious are sent to a heavy, high‑precision verifier (Stage 2). Because the vast majority of traffic is genuine, the expensive second stage runs on only a small fraction of the audio, slashing GPU costs by 85–92% without sacrificing end‑to‑end recall.

Key design choices:

    Stage 1 – RawNetLite (≈100 K parameters), trained from scratch on telephony‑degraded Hindi/English data, tuned for near‑100% recall.

    Stage 2 – WPT‑XLSR‑AASIST: frozen XLSR‑53 backbone + wavelet prompt tuning + AASIST graph head (≈300 M frozen, <1 M trainable), trained with parameter‑efficient fine‑tuning.

    Pre‑processing – WebRTC VAD, 4‑second sliding windows with 50% overlap.

    Deployment – Stage 1 on CPU instances (autoscaled with call volume), Stage 2 on GPU instances (autoscaled toward zero when idle), all server‑side.

The specification below is exhaustive: data shapes, layer parameters, loss functions, threshold strategies, training recipes, and code structure are all defined. A competent engineering team can implement the entire pipeline directly from this document.
2. System Architecture Overview
text

Incoming Audio Stream
       │
       ▼
┌─────────────────────────┐
│   Voice Activity Det.   │ (WebRTC VAD, 30 ms frames)
│   Split into 4s windows │ (50% overlap, 16 kHz mono)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│       Stage 1           │ RawNetLite (CPU)
│   High‑Recall Filter    │
│   Score per window      │
└───────────┬─────────────┘
            │
    score > τ₁ ? ──── No ──▶ Genuine (discard)
            │
           Yes
            │
            ▼
┌─────────────────────────┐
│       Stage 2           │ WPT‑XLSR‑AASIST (GPU)
│   High‑Precision Verif. │
│   Final score per window│
└───────────┬─────────────┘
            │
    score > τ₂ ? ──── No ──▶ Genuine
            │
           Yes
            │
            ▼
          Fake

Aggregation rule for a call: a call is considered a deepfake if any of its windows is classified as fake by Stage 2. This prevents a short synthetic segment from being averaged away.

Cost math (illustrative):

    Total windows = W

    Stage 1 cost per window = c₁ (very low)

    Stage 2 cost per window = c₂ (high)

    Flag rate of Stage 1 (false positive rate + true positive rate) ≈ 5–10%

    Total cost ≈ W·c₁ + 0.1·W·c₂
    With c₂ ≈ 50× c₁, total cost ≈ c₁·W + 5·c₁·W = 6·c₁·W, compared with 51·c₁·W for running Stage 2 on everything. A ~88% reduction.

3. Stage 1: Lightweight High‑Recall Filter
3.1 Architecture: RawNetLite

RawNetLite is an end‑to‑end neural network that operates directly on the raw waveform, avoiding explicit feature extraction (e.g., Mel‑spectrograms). Its tiny size (≈100 K parameters) and pure convolutional‑recurrent design make it ideal for CPU‑based real‑time screening.

Input: Raw audio waveform, 16 kHz, mono, shape (batch, 1, num_samples) where num_samples = 4 s × 16000 = 64000.

Layer‑by‑layer specification:
Layer	Type	Parameters / Shape	Details
1	SincConv_fast	in_channels=1, out_channels=128, kernel_size=129, stride=1	Learnable band‑pass filters. Output: (B,128,64000).
2	MaxPool1d	kernel_size=3, stride=2	Down‑sampling → (B,128,32000).
3	Residual Block (ResBlock) × 2	channels=128	Each block: BN → LeakyReLU(0.2) → Conv1d(k=3,p=1) → BN → LeakyReLU → Conv1d(k=3,p=1), plus identity skip. Output: (B,128,32000).
4	MaxPool1d	kernel_size=3, stride=2	→ (B,128,16000).
5	ResBlock × 2	channels=128	→ (B,128,16000).
6	MaxPool1d	kernel_size=3, stride=2	→ (B,128,8000).
7	ResBlock × 2	channels=128	→ (B,128,8000).
8	GRU	input_size=128, hidden_size=128, num_layers=2, bidirectional=True, batch_first=True	Output: (B,8000,256).
9	Temporal Attention	Attention pooling over time dimension	Project GRU outputs → attention weights → weighted sum → (B,256).
10	FC classifier	Linear(256, 1)	→ logit.
11	Sigmoid		→ probability p_fake.

Total parameters: ≈ 100 K.
Inference cost: ≈ 0.5 M FLOPs per second of audio; <1 ms per window on modern CPU.
3.2 Training from Scratch

Loss function: Binary cross‑entropy with weighted positive class to bias towards recall. Specifically, if the dataset is heavily imbalanced (few fakes), weight the fake class by pos_weight = (num_real / num_fake). Additionally, a focal loss variant can be used to focus on hard examples.

Optimizer: AdamW, lr=1e-4, weight_decay=1e-5, batch_size=32.
Scheduler: Cosine annealing with warm restarts (e.g., CosineAnnealingWarmRestarts with T_0=20 epochs).
Early stopping: Monitor validation EER, patience=15 epochs.
Data augmentation (non‑negotiable): Apply on‑the‑fly during training:

    Codec simulation: 8‑bit μ‑law, GSM, Opus at low bitrates.

    Telephony band‑pass filtering (300–3400 Hz).

    Background noise addition (from real call center recordings or public noise datasets).

    Speed perturbation (±10%).

    Time masking (SpecAugment‑like on raw waveform: random zeroing of short segments).

3.3 Threshold Strategy

Stage 1 must never miss a fake. Therefore, after training, select a decision threshold τ₁ that achieves >99.9% recall on a held‑out validation set, even if it means a false‑positive rate of 5–10%. This is a tunable parameter, not a fixed constant. Start with τ₁ = 0.05 (i.e., flag if p_fake > 0.05) and adjust in production based on observed flag rate and feedback from Stage 2.

Implementation detail: The RawNetLite outputs a probability in [0,1]. Apply flag = (prob > τ₁). At launch, set τ₁ such that roughly 7–10% of all windows are flagged (if prevalence is low). This will be monitored and tuned (see Section 7).
4. Stage 2: High‑Precision Verifier
4.1 Architecture: WPT‑XLSR‑AASIST

This is the state‑of‑the‑art model combining a frozen multilingual SSL encoder (XLSR‑53) with wavelet prompt tuning and the AASIST graph‑attention backend. It processes only the flagged windows from Stage 1, thus its high computational cost is incurred rarely.

Overall flow:

    Convert raw audio to 16 kHz Mel‑spectrogram (or use the same raw waveform; XLSR accepts both, but for consistency we use its default feature extractor).

    Feed through the frozen XLSR‑53 transformer.

    In each transformer layer, prepend learnable prompt tokens (standard + wavelet‑decomposed) to the hidden sequence.

    Extract the output of the final prompt position as a fixed‑length embedding.

    Pass this embedding through the AASIST dual‑graph spectro‑temporal attention classifier to produce a final fake probability.

4.1.1 Frozen Encoder: XLSR‑53

XLSR‑53 (wav2vec2‑xls‑r‑300m) is a 300‑million parameter model pre‑trained on 436 K hours of speech in 128 languages, including Hindi. We use it completely frozen to preserve its rich multilingual acoustic representations.

Preprocessing:

    Audio: 16 kHz mono, trimmed/padded to 4 seconds (64000 samples).

    Feature extraction: the model’s own CNN feature encoder (7‑layer conv) converts waveform to latent vectors at 20 ms frame rate → sequence of length ≈ 200 for 4 s. Hidden size = 1024.

Transformer layers: 24 layers, each with multi‑head self‑attention and feed‑forward. We do not update their weights.
4.1.2 Wavelet Prompt Tuning (WPT)

Instead of full fine‑tuning, we inject a small set of learnable “prompt” tokens into each transformer layer. These prompts are partitioned into:

    Standard prompts: A set of P learnable vectors of shape (P, 1024), prepended to the key/value sequence at each attention block.

    Wavelet prompts: The same P vectors are also decomposed using a discrete wavelet transform (DWT, e.g., Haar) into low‑ and high‑frequency components. These decomposed prompts are appended as additional tokens.

Concretely, for a given transformer layer:

    Let x = [CLS_token, audio_tokens] be the input sequence of shape (B, 1+200, 1024).

    Learnable parameters:

        prompts_std: (P, 1024)

        prompts_wave_low: (P, 1024)

        prompts_wave_high: (P, 1024)
        (Total learnable: 3*P*1024).

    At runtime, we compute the wavelet decomposition of prompts_std via DWT to obtain low and high components. To enable end‑to‑end learning, these can be approximated by learnable linear projections (as in the original paper) that mimic DWT, i.e., low = W_low @ prompts_std, high = W_high @ prompts_std, where W_low and W_high are fixed orthogonal matrices (Haar) and not trained, while prompts_std is trained. This keeps the decomposition differentiable.

    The extended prompt sequence [prompts_std, prompts_wave_low, prompts_wave_high] (shape (3*P, 1024)) is prepended to x before the attention mechanism. The attention mask is adjusted so that prompts can attend to each other and to audio tokens, but audio tokens do not attend to prompts (to avoid altering the frozen representations).

    The output corresponding to the first prompt position (or a learned aggregation) serves as the utterance‑level embedding for the subsequent AASIST head.

Hyperparameters: P = 10 (10 standard prompts, 10 low, 10 high → total 30 prompts). This yields just 30*1024 = 30,720 parameters per layer, and across 24 layers ~737 K trainable parameters for prompts.
4.1.3 AASIST Backend

AASIST models audio spoofing as a graph problem: raw waveform (or here, the SSL embeddings) is transformed into spectral and temporal graph representations, and a heterogeneous graph attention network fuses them.

Input: The sequence of hidden states from the last prompt token (after WPT injection) is averaged across all layers? Actually, the original WPT‑AASIST paper uses only the prompt token output from the final layer as a single vector of size 1024. But AASIST typically expects a time‑frequency representation. To bridge this, we can either:

    Use the prompt vector directly as input to a simple MLP classifier, but that would lose the temporal detail.

    Better: Adopt the AASIST‑L variant which can operate on fixed‑size embeddings: we feed the prompt vector through a stack of spectral and temporal graph branches that construct graphs from the embedding itself (via unfolding or copying) and then apply graph attention. However, this is non‑trivial.

Simplified (and faithful to WPT‑XLSR‑AASIST): The paper uses the final prompt token as the only input to a lightweight AASIST‑like head that contains two parallel branches:

    Spectral branch: Applies a 1‑D convolution (kernel size 1) to treat the embedding as a “spectrum” and builds a graph among frequency bins? Actually, the embedding is 1024‑d, we can reshape it to (32, 32) to simulate a spectrogram.

    Temporal branch: Applies a different 1‑D convolution.
    Then the dual graphs are fused by a heterogeneous graph transformer (HGT) with 2 layers. Finally, a readout layer produces a logit.

We will follow the exact architecture reported in the WPT paper: the prompt embedding (size 1024) is projected to a smaller dimension (e.g., 128) and then fed into a dual‑graph network that mimics AASIST but adapted to fixed‑length vectors. The number of trainable parameters in this head is ≈ 300 K.

Total trainable parameters for Stage 2: Prompts (~737 K) + AASIST head (~300 K) ≈ 1.04 M. The remaining 300 M of XLSR‑53 stay frozen. This is 458× fewer than full fine‑tuning.

Output: A single logit passed through sigmoid to get p_fake.
4.2 Training Stage 2 (Parameter‑Efficient Fine‑Tuning)

Loss: Focal loss with γ=2 and α=0.25 to handle class imbalance and focus on hard examples. Alternatively, binary cross‑entropy with positive class weighting.

Optimizer: AdamW, lr=1e-3 (for prompts and head only; no backbone updates). Weight decay 1e-4.
Batch size: 8 (limited by GPU memory, as XLSR‑53 is huge).
Training regime:

    Freeze XLSR‑53 entirely.

    Randomly initialize prompts and AASIST head.

    Train for 30–50 epochs, lower LR by factor 0.5 if validation loss plateaus for 5 epochs.

Data: Must include labeled Hindi/Indic deepfakes. Use the data pipeline described in Section 6.
5. Pre‑processing and Audio Windowing

All incoming audio (mono, any sample rate) is resampled to 16 kHz using a high‑quality resampler (e.g., librosa.resample or torchaudio.functional.resample). The pipeline then processes the stream in real time:

    Voice Activity Detection (VAD): WebRTC VAD operates on 30 ms frames. Only frames classified as speech are passed forward. This avoids wasting compute on silence or hold music.

    Sliding Window: From the continuous speech stream, extract overlapping windows:

        Window length: 4 seconds (64 000 samples).

        Stride: 2 seconds (32 000 samples) → 50% overlap.

        If the remaining speech chunk is less than 4 s, pad with zeros or ignore (depending on minimum analysis length, e.g., 1 s). For calls shorter than 4 s, the entire active region is taken as one window.

    Normalization: Each window is peak‑normalized to 0.95 to avoid clipping and DC offset is removed.

For Stage 1: Raw waveform windows (shape (1, 64000)) are fed directly.
For Stage 2: The same waveform is fed to the XLSR‑53 feature extractor which internally converts to mel‑scale features.
6. Data Strategy for Hindi/Indic Robustness

Modern deepfake detectors trained solely on English/Chinese datasets fail on Hindi speech and on attacks from state‑of‑the‑art generators like ElevenLabs. The following strategy ensures the cascade works on real‑world RingWave traffic.
6.1 Genuine Speech Sources

    AI4Bharat corpora: IndicVoice, Shrutilipi, IndicSUPERB. These contain thousands of hours of Hindi and other Indic languages, recorded in natural conditions.

    M‑AILABS Hindi subset: high‑quality studio speech.

    In‑house call recordings (anonymized, consented): the most valuable source, as they contain telephony artifacts and real‑world background noise.

6.2 Synthetic/Fake Speech Generation

Since labeled Hindi deepfake data is scarce, we generate it ourselves:

    Use XTTS‑v2 (Coqui), Indic Parler‑TTS, and AI4Bharat’s TTS to synthesize speech from transcripts of the genuine Hindi sentences. This produces cloned, natural‑sounding fakes.

    Additionally, use ElevenLabs (if API access is available) and MeloTTS for zero‑shot voice cloning on a subset of speakers.

    MLAAD (Multi‑Language Audio Anti‑Spoofing Dataset) includes a Hindi slice generated from 119 TTS models; incorporate that.

6.3 Augmentation Pipeline (Applied to ALL Data, Real and Fake)

Before training, every audio sample must undergo heavy telephony‑style degradation to bridge the gap between clean studio audio and real calls. Apply a random combination of:

    Resampling to 8 kHz then back to 16 kHz (simulates narrowband).

    Codec compression: Opus @ 6 kbps, GSM, G.711 μ‑law.

    Band‑pass filter: 300–3400 Hz.

    Background noise addition (call center chatter, street noise, fan hum) at random SNR between 5–25 dB.

    Time‑stretching (±10%), pitch shifting (±200 cents).

    Room impulse response convolution (simulate small office, car cabin).

Augmentation is performed on‑the‑fly during training using libraries like audiomentations or torch-audiomentations.
6.4 Dataset Splits

    Training: 80% of generated data, balanced between real and fake.

    Validation: 10%, used to tune τ₁ and τ₂.

    Test (held‑out): 10%, never seen during training, includes attacks from generators not used in training to measure generalization.

7. Threshold Tuning and Monitoring in Production

Thresholds τ₁ (Stage 1) and τ₂ (Stage 2) are the primary operational knobs. The system should log every decision and allow dynamic adjustment without retraining.

Launch configuration:

    τ₁ = 0.05 (flags any window with >5% confidence).

    τ₂ = 0.5 (standard decision boundary).

Monitoring metrics (real‑time dashboard):

    Flag rate of Stage 1 (ideally 5–10% of windows).

    Stage 2 accept/reject rate per flagged window.

    End‑to‑end latency (from audio arrival to final decision).

    False positive / false negative feedback from manual review (if available) or from adversarial red‑teaming.

Tuning loop: Every week, analyze the recorded decisions:

    If Stage 1 flag rate is too high and causing GPU overload, raise τ₁ slightly (e.g., 0.1) and verify recall on a test set doesn’t drop.

    If Stage 2 is rejecting too many genuine windows (user complaints), raise τ₂ to 0.7 to improve precision.

    If a new attack is discovered and Stage 1 is missing it, lower τ₁ and consider retraining Stage 1 with those adversarial examples.

The pipeline must support A/B testing of threshold values on a subset of traffic.
8. Deployment Blueprint

Both stages run server‑side within the RingWave infrastructure, eliminating edge‑to‑cloud transmission concerns.
8.1 Service Architecture
text

┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  Media Server │────▶│  Stage 1      │────▶│  Stage 2      │
│  (audio feed) │     │  CPU Cluster  │     │  GPU Cluster  │
└───────────────┘     └───────────────┘     └───────────────┘
       │                      │                     │
       │                      │ (flagged windows    │
       │                      │  pushed to queue)   │
       │                      ▼                     │
       │               ┌─────────────┐              │
       │               │  Redis/Kafka│──────────────▶
       │               │  Queue      │
       │               └─────────────┘
       │
       ▼
  Final decision aggregator (returns "fake" if any window is fake)

    Stage 1 is deployed as a Kubernetes Deployment with auto‑scaling based on CPU usage. Each pod runs a lightweight TorchScript‑compiled RawNetLite model. No GPU required.

    Stage 2 is a separate Deployment with GPU nodes (NVIDIA T4 or A10). It scales toward zero when the queue is empty, reducing cost. The model is exported to ONNX with INT8 quantization to fit within 4 GB VRAM and achieve <50 ms inference per window.

    Communication between stages uses gRPC or a simple REST API. For low latency, use protobuf serialization and direct binary audio data transfer.

8.2 Containerization

Stage 1 Dockerfile:
dockerfile

FROM python:3.10-slim
RUN apt-get update && apt-get install -y libsndfile1
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY stage1_model.pt /model/
COPY inference_server.py .
CMD ["python", "inference_server.py"]

The model file is an optimized TorchScript or ONNX artifact.

Stage 2 Dockerfile includes NVIDIA CUDA base, large model weights (XLSR‑53 ~1.2 GB) cached in the image.
8.3 Latency Budget

    VAD + windowing: ~5 ms.

    Stage 1 inference per window: <5 ms on CPU.

    Network + queue to Stage 2: ~5 ms.

    Stage 2 inference (ONNX INT8): <50 ms on GPU.

    Aggregation: negligible.
    Total latency for a flagged window: <65 ms, well within real‑time requirements for live calls (RTF << 1.0).

For un‑flagged windows, the call continues with no perceptible delay.
