import torch
from ringwave_deepfake.models.stage2_encoder import PromptedEncoder
from ringwave_deepfake.models.stage2_verifier import Stage2Verifier

def test_stage2_verifier():
    print("Testing Stage 2 Verifier (AASIST backend)...")
    
    encoder = PromptedEncoder(n_prompts=2, use_wavelet_prompts=False)
    model = Stage2Verifier(encoder)
    
    # Dummy audio: batch=2, length=16000 (1 sec)
    dummy_audio = torch.randn(2, 16000)
    
    out = model(dummy_audio)
    print(f"Output shape: {out.shape}")
    assert out.shape == (2,), "Output shape must be (B,)"
    
    # Check backward pass
    loss = out.sum()
    loss.backward()
    
    assert model.adapter.weight.grad is not None, "Adapter did not receive gradients!"
    assert encoder.prompts.grad is not None, "Prompts did not receive gradients!"
    print("Gradients flow to prompts and adapter successfully.")
    
    print("Stage 2 Verifier test passed.\n")

if __name__ == "__main__":
    test_stage2_verifier()
