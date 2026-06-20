import torch
from ringwave_deepfake.models.stage2_encoder import PromptedEncoder

def test_stage2_encoder():
    print("Testing Stage 2 Encoder (Prompted XLSR)...")
    
    # 1. Plain Prompt Tuning
    print("Testing plain prompt tuning...")
    encoder = PromptedEncoder(n_prompts=10, use_wavelet_prompts=False)
    
    # Verify backbone is frozen
    frozen = True
    for p in encoder.encoder.parameters():
        if p.requires_grad:
            frozen = False
            break
    assert frozen, "Backbone has requires_grad=True!"
    print("Backbone successfully frozen.")
    
    # Prompt params
    assert encoder.prompts.requires_grad
    print(f"Prompt shape: {encoder.prompts.shape} -> trainable.")
    
    # Dummy audio: batch_size=2, length=16000 (1 second @ 16kHz)
    dummy_audio = torch.randn(2, 16000)
    
    # Forward pass without attention mask
    out = encoder(dummy_audio)
    print(f"Output shape (no mask): {out.shape}")
    
    # Forward pass with attention mask
    mask = torch.ones(2, 16000, dtype=torch.long)
    mask[1, 10000:] = 0 # pad second item
    out_mask = encoder(dummy_audio, attention_mask=mask)
    print(f"Output shape (with mask): {out_mask.shape}")
    
    # Backprop test
    loss = out.sum()
    loss.backward()
    assert encoder.prompts.grad is not None, "Prompts did not receive gradients!"
    print("Gradients flow to prompts successfully.")
    
    # 2. Wavelet Prompt Tuning
    print("\nTesting wavelet prompt tuning...")
    encoder_wav = PromptedEncoder(n_prompts=10, use_wavelet_prompts=True)
    out_wav = encoder_wav(dummy_audio)
    print(f"Wavelet output shape: {out_wav.shape}")
    
    print("Stage 2 Encoder test passed.\n")

if __name__ == "__main__":
    test_stage2_encoder()
