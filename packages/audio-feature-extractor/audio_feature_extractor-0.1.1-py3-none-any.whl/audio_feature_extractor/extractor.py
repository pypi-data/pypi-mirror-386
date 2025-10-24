import os

import librosa
import numpy as np
from audio_feature_extractor.features import (
    TraditionalFeatureExtractor,
    EmbeddingFeatureExtractor,
    SemanticFeatureExtractor,
)


class FeatureExtractor:
    def __init__(self, sample_rate=16000, hop_length=512, frame_length=2048, **kwargs):
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.frame_length = frame_length
        self.traditional_extractor = TraditionalFeatureExtractor(
            sample_rate=sample_rate, hop_length=hop_length, frame_length=frame_length
        )
        self.embedding_extractor = EmbeddingFeatureExtractor(
            model_name="speechbrain/spkrec-xvect-voxceleb"
        )
        self.semantic_extractor = SemanticFeatureExtractor(
            sample_rate=sample_rate,
            hop_length=hop_length,
            frame_length=frame_length,
            **kwargs,
        )

    def extract_features(self, audio_path: str) -> dict:
        audio = librosa.load(audio_path, sr=self.sample_rate)[0]
        traditional_features = self.traditional_extractor.get_all_features(audio=audio)
        embedding_features = self.embedding_extractor.extract_features(
            audio_path=audio_path
        )
        semantic_features = self.semantic_extractor.extract_all(audio_path=audio_path)

        return {
            "traditional_features": traditional_features,
            "embedding_features": embedding_features,
            "semantic_features": semantic_features,
        }


if __name__ == "__main__":
    # Example usage
    audio_path = "data/somos/audios/booksent_2012_0005_001.wav"

    extractor = FeatureExtractor()
    features = extractor.extract_features(audio_path)
    print(features)
