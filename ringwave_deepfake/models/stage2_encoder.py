import torch
import torch.nn as nn
from transformers import Wav2Vec2Model

def build_haar_pair(n_prompts: int):
    """Fixed (non-trainable) Haar low/high-pass matrices, used only if
    use_wavelet_prompts=True. n_prompts must be even."""
    h = torch.zeros(n_prompts // 2, n_prompts)
    g = torch.zeros(n_prompts // 2, n_prompts)
    for i in range(n_prompts // 2):
        h[i, 2*i] = h[i, 2*i+1] = 2 ** -0.5
        g[i, 2*i], g[i, 2*i+1] = 2 ** -0.5, -2 ** -0.5
    return h, g

class PromptedEncoder(nn.Module):
    def __init__(self, model_name="facebook/wav2vec2-large-xlsr-53",
                 n_prompts=10, use_wavelet_prompts=False, hidden=1024):
        super().__init__()
        self.encoder = Wav2Vec2Model.from_pretrained(model_name)
        for p in self.encoder.parameters():
            p.requires_grad = False
        self.encoder.eval()

        n_layers = self.encoder.config.num_hidden_layers
        self.prompts = nn.Parameter(torch.randn(n_layers, n_prompts, hidden) * 0.02)
        self.use_wavelet_prompts = use_wavelet_prompts
        if use_wavelet_prompts:
            h, g = build_haar_pair(n_prompts)
            self.register_buffer("haar_low", h)
            self.register_buffer("haar_high", g)

        self._n_tokens_per_layer = None
        self._register_hooks()

    def _register_hooks(self):
        layers = self.encoder.encoder.layers

        def make_pre_hook(i):
            def pre_hook(module, args, kwargs):
                hidden_states = args[0]
                prompt = self.prompts[i].unsqueeze(0).expand(hidden_states.size(0), -1, -1)
                tokens = [prompt]
                if self.use_wavelet_prompts:
                    tokens.append((self.haar_low @ self.prompts[i]).unsqueeze(0)
                                  .expand(hidden_states.size(0), -1, -1))
                    tokens.append((self.haar_high @ self.prompts[i]).unsqueeze(0)
                                  .expand(hidden_states.size(0), -1, -1))
                full_prompt = torch.cat(tokens, dim=1)
                self._n_tokens_per_layer = full_prompt.size(1)
                
                new_hidden = torch.cat([full_prompt, hidden_states], dim=1)
                
                # Check for attention_mask and expand it
                am = kwargs.get('attention_mask', None)
                if am is not None:
                    # am can be (B, 1, 1, seq_len) or (B, 1, seq_len, seq_len)
                    # we must pad it to match the new sequence length (T + n_prompts)
                    # To attend to the prompts, the mask value should be 0.0 (in standard HF inverted mask, 0 means keep, min means drop)
                    b, head, d2, d3 = am.shape
                    new_am = am
                    
                    if d3 > 1:
                        # pad dim 3
                        pad_value = 1 if am.dtype == torch.bool else 0.0
                        extra = torch.full((b, head, d2, self._n_tokens_per_layer), pad_value, dtype=am.dtype, device=am.device)
                        new_am = torch.cat([extra, new_am], dim=3)
                        
                    if d2 > 1:
                        # pad dim 2
                        # We want the prompt queries to attend to the same valid keys as the audio queries.
                        # So we copy the key-mask from the first audio query.
                        extra = new_am[:, :, 0:1, :].expand(b, head, self._n_tokens_per_layer, new_am.size(3))
                        new_am = torch.cat([extra, new_am], dim=2)
                        
                    kwargs['attention_mask'] = new_am
                    
                return (new_hidden,) + args[1:], kwargs
            return pre_hook

        def make_post_hook():
            def post_hook(module, args, output):
                hidden_states = output[0]
                stripped = hidden_states[:, self._n_tokens_per_layer:, :]
                return (stripped,) + output[1:]
            return post_hook

        for i, layer in enumerate(layers):
            layer.register_forward_pre_hook(make_pre_hook(i), with_kwargs=True)
            layer.register_forward_hook(make_post_hook())

    def forward(self, waveform: torch.Tensor, attention_mask: torch.Tensor = None) -> torch.Tensor:
        # waveform is raw audio (B, num_samples)
        out = self.encoder(waveform, attention_mask=attention_mask)
        return out.last_hidden_state
