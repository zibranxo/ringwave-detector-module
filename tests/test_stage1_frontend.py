import torch
from ringwave_deepfake.audio.features import LFCCFrontend

def test_stage1_frontend():
    print("Testing Stage 1 Frontend (LFCC)...")
    
    frontend = LFCCFrontend()
    
    # 4 second window @ 16kHz
    batch_size = 2
    dummy_waveform = torch.randn(batch_size, 64000)
    
    out = frontend(dummy_waveform)
    print(f"Output shape: {out.shape}")
    
    # Expected: (B, 3, T, 60)
    assert out.shape[0] == batch_size
    assert out.shape[1] == 3
    assert out.shape[3] == 60
    
    # Check shape for a shorter window (e.g. 1.5s tail)
    short_waveform = torch.randn(batch_size, 24000)
    out_short = frontend(short_waveform)
    print(f"Short window output shape: {out_short.shape}")
    
    assert out_short.shape[0] == batch_size
    assert out_short.shape[1] == 3
    assert out_short.shape[3] == 60
    
    print("Stage 1 Frontend test passed.\n")

if __name__ == "__main__":
    test_stage1_frontend()
