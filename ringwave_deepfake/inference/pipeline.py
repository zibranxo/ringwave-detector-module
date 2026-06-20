import torch
import torchaudio
import numpy as np
from ringwave_deepfake.audio.vad import VADGate, SAMPLE_RATE
from ringwave_deepfake.audio.windowing import sliding_windows
from ringwave_deepfake.audio.features import LFCCFrontend
from ringwave_deepfake.models.stage1_lcnn import Stage1LCNN
from ringwave_deepfake.models.stage2_encoder import PromptedEncoder
from ringwave_deepfake.models.stage2_verifier import Stage2Verifier
from ringwave_deepfake.inference.session import CallSession, WindowVerdict

class DeepfakePipeline:
    def __init__(self, tau1=0.05, tau2=0.5):
        self.tau1 = tau1
        self.tau2 = tau2
        
        self.vad = VADGate()
        self.frontend = LFCCFrontend()
        self.stage1 = Stage1LCNN()
        
        encoder = PromptedEncoder(n_prompts=10, use_wavelet_prompts=False)
        self.stage2 = Stage2Verifier(encoder)
        
        self.stage1.eval()
        self.stage2.eval()

    def process_call(self, call_id: str, waveform_i16_bytes: bytes) -> CallSession:
        session = CallSession(call_id=call_id)
        
        # 1. VAD Masking
        mask = self.vad.speech_mask(waveform_i16_bytes)
        frame_samples = self.vad.frame_samples
        
        # Convert bytes to tensor
        waveform = torch.from_numpy(np.frombuffer(waveform_i16_bytes, dtype=np.int16)).float() / 32768.0
        
        active_samples = []
        for i, is_speech in enumerate(mask):
            if is_speech:
                start = i * frame_samples
                end = start + frame_samples
                active_samples.append(waveform[start:end])
                
        if not active_samples:
            return session
            
        active_speech = torch.cat(active_samples).unsqueeze(0)
        
        # 2. Windowing
        windows = list(sliding_windows(active_speech))
        
        for win, start_sample, end_sample in windows:
            start_s = start_sample / SAMPLE_RATE
            end_s = end_sample / SAMPLE_RATE
            
            # 3. Stage 1 (LFCC + LCNN)
            with torch.no_grad():
                feat = self.frontend(win)
                logit1 = self.stage1(feat)
                p_fake1 = torch.sigmoid(logit1).item()
                
            if p_fake1 < self.tau1:
                verdict = WindowVerdict(start_s, end_s, 1, "clear", p_fake1)
            else:
                # 4. Stage 2 (Prompted XLSR + AASIST)
                with torch.no_grad():
                    logit2 = self.stage2(win)
                    p_fake2 = torch.sigmoid(logit2).item()
                    
                if p_fake2 < self.tau2:
                    verdict = WindowVerdict(start_s, end_s, 2, "verified-genuine", p_fake2)
                else:
                    verdict = WindowVerdict(start_s, end_s, 2, "verified-fake", p_fake2)
                    
            session.record(verdict)
            
        return session
