import torch
from ringwave_deepfake.models.stage1_lcnn import Stage1LCNN

def test_stage1_backend():
    print("Testing Stage 1 Backend (LCNN)...")
    
    model = Stage1LCNN()
    
    param_count = sum(p.numel() for p in model.parameters())
    print(f"LCNN Parameter count: {param_count:,}")
    
    # Expected input shape from Stage 1 Frontend
    # B=2, 3 channels, T=401, n_lfcc=60
    dummy_input = torch.randn(2, 3, 401, 60)
    
    # Forward pass
    out = model(dummy_input)
    print(f"Output shape: {out.shape}")
    assert out.shape == (2,)
    
    # Check variable length input (tail window)
    short_input = torch.randn(2, 3, 151, 60)
    out_short = model(short_input)
    assert out_short.shape == (2,)
    
    # Check backward pass
    loss = out.sum()
    loss.backward()
    
    has_grad = False
    for p in model.parameters():
        if p.grad is not None:
            has_grad = True
            break
            
    assert has_grad, "No gradients were computed in backward pass!"
    print("Gradients computed successfully.")
    
    print("Stage 1 Backend test passed.\n")

if __name__ == "__main__":
    test_stage1_backend()
