import torch
from transformers import Wav2Vec2Model, Wav2Vec2Config

# Load an empty small wav2vec2 model
config = Wav2Vec2Config()
model = Wav2Vec2Model(config)

# We will hook into the first attention layer's forward pass
# and print the attention mask that it receives.

def hook_fn(module, args, kwargs):
    # args: (hidden_states, attention_mask, output_attentions)
    # kwargs: may contain attention_mask
    attention_mask = kwargs.get('attention_mask', args[1] if len(args) > 1 else None)
    
    if attention_mask is not None:
        print("====== INTERCEPTED ATTENTION MASK in Wav2Vec2Attention ======")
        print(f"Shape: {attention_mask.shape}")
        print(f"Dtype: {attention_mask.dtype}")
        print(f"Values (slice):\n{attention_mask[0, 0, :2, :10]}")
        print("===============================================================")
        # Remove hook to only print once
        hook.remove()

# Register the hook on the first encoder layer's attention mechanism
hook = model.encoder.layers[0].attention.register_forward_pre_hook(hook_fn, with_kwargs=True)

# Create dummy input with sequence length 50
batch_size = 1
seq_length = 50000 # raw audio
input_values = torch.randn(batch_size, seq_length)
attention_mask = torch.ones(batch_size, seq_length, dtype=torch.long)
# Make some part of the mask 0 to see padding effect
attention_mask[0, 40000:] = 0

print("Running forward pass...")
with torch.no_grad():
    model(input_values=input_values, attention_mask=attention_mask)
