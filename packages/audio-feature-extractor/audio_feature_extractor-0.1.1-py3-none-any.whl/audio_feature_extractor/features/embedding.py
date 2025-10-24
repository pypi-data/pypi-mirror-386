from typing import Optional
import numpy as np
import torch
from speechbrain.inference import EncoderClassifier


class EmbeddingFeatureExtractor:
    def __init__(self, model_name: str = "speechbrain/spkrec-xvect-voxceleb"):
        classifier = EncoderClassifier.from_hparams(source=model_name)
        if classifier is None:
            raise RuntimeError("Failed to load EncoderClassifier.")
        self.classifier: EncoderClassifier = classifier

    @torch.no_grad()
    def extract_features(
        self,
        audio_path: Optional[str] = None,
        audio: Optional[np.ndarray] = None,
        sample_rate: int = 16000,
    ) -> torch.Tensor:
        assert (
            audio_path is not None or audio is not None
        ), "Either audio_path or audio must be provided."
        if audio_path is not None:
            signal = self.classifier.load_audio(audio_path)
        else:
            signal = torch.tensor(audio).unsqueeze(0)
        embeddings = self.classifier.encode_batch(signal)
        embeddings = torch.nn.functional.normalize(embeddings, dim=-1).cpu()
        return embeddings
