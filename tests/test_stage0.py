import torch
import math
from ringwave_deepfake.audio.vad import VADGate, SAMPLE_RATE
from ringwave_deepfake.audio.windowing import sliding_windows, MIN_WINDOW_SAMPLES

def generate_test_audio():
    # Generate 10 seconds of audio:
    # 0-2s: Silence (zeros)
    # 2-7s: 440Hz sine wave (Speech)
    # 7-10s: Silence
    
    t_total = 10
    n_samples = t_total * SAMPLE_RATE
    waveform = torch.zeros(n_samples)
    
    # 2 to 7 seconds is speech
    start_idx = 2 * SAMPLE_RATE
    end_idx = 7 * SAMPLE_RATE
    t = torch.linspace(0, 5, end_idx - start_idx)
    waveform[start_idx:end_idx] = torch.sin(2 * math.pi * 440 * t) * 0.8
    
    return waveform

def test_stage0():
    print("Testing Stage 0: VAD and Windowing...")
    waveform = generate_test_audio()
    
    # Convert float waveform (-1.0 to 1.0) to PCM 16-bit bytes for VAD
    waveform_i16 = (waveform * 32767).to(torch.int16)
    waveform_bytes = waveform_i16.numpy().tobytes()
    
    # Run VAD
    vad = VADGate(aggressiveness=2)
    mask = vad.speech_mask(waveform_bytes)
    
    print(f"Total VAD frames: {len(mask)}")
    active_frames = sum(mask)
    print(f"Active VAD frames: {active_frames}")
    
    # For testing windowing properly, we will just use a dummy active speech tensor
    # Let's say 7.5 seconds of active speech
    active_speech = torch.randn(1, int(7.5 * SAMPLE_RATE))
    print(f"\nMocking active speech length: {active_speech.shape[-1]} samples ({active_speech.shape[-1]/SAMPLE_RATE:.2f}s)")
    
    windows = list(sliding_windows(active_speech))
    print(f"Generated {len(windows)} sliding windows.")
    for i, (win, start, end) in enumerate(windows):
        print(f"  Window {i}: shape {win.shape}, start_sample {start}, end_sample {end}, duration {win.shape[-1]/SAMPLE_RATE:.2f}s")
        assert win.shape[-1] >= MIN_WINDOW_SAMPLES, f"Window {i} too short!"
    
    print("Stage 0 test passed.\n")

if __name__ == "__main__":
    test_stage0()
