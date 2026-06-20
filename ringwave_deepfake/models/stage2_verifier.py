import torch
import torch.nn as nn
from ringwave_deepfake.models.stage2_encoder import PromptedEncoder
from ringwave_deepfake.models.aasist_backend import AASISTBackend

class Stage2Verifier(nn.Module):
    def __init__(self, encoder: PromptedEncoder, aasist_channels=64, use_cnn_frontend=False):
        super().__init__()
        self.encoder = encoder
        self.adapter = nn.Linear(1024, aasist_channels)  # per-frame projection
        self.backend = AASISTBackend(in_channels=aasist_channels, use_cnn_frontend=use_cnn_frontend)

    def forward(self, waveform: torch.Tensor, attention_mask: torch.Tensor = None) -> torch.Tensor:
        seq = self.encoder(waveform, attention_mask=attention_mask)        # (B, T, 1024)
        seq = self.adapter(seq)             # (B, T, 64)
        
        if attention_mask is not None:
            # Wav2Vec2 downsamples the sequence. We must mask the output before pooling in AASIST.
            n_prompts = self.encoder._n_tokens_per_layer if hasattr(self.encoder, '_n_tokens_per_layer') and self.encoder._n_tokens_per_layer else 0
            audio_len = seq.shape[1] - n_prompts
            
            # Robustly downsample the mask to match the audio features length
            down_mask = torch.nn.functional.adaptive_avg_pool1d(
                attention_mask.float().unsqueeze(1), audio_len
            ).squeeze(1) > 0.5
            
            # Prepend True for the prompts so they aren't masked out
            if n_prompts > 0:
                prompt_mask = torch.ones(down_mask.size(0), n_prompts, dtype=torch.bool, device=down_mask.device)
                down_mask = torch.cat([prompt_mask, down_mask], dim=1)
                
            seq = seq * down_mask.unsqueeze(-1).to(seq.dtype)
            
        seq = seq.transpose(1, 2)           # (B, 64, T) -- AASIST's native layout
        return self.backend(seq)            # (B,) raw logit
