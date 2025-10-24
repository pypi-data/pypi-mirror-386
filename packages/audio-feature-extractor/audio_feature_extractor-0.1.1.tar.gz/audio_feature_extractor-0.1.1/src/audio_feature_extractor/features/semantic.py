from typing import Optional, Dict, Any
from unittest import result
import numpy as np
import librosa
from g2p_en import G2p as G2P_EN
from g2pw import G2PWConverter as G2P_ZH
from torch import device
import whisperx
from whisperx.diarize import DiarizationPipeline
from whisperx.types import TranscriptionResult, AlignedTranscriptionResult
import os


class SemanticFeatureExtractor:
    def __init__(
        self,
        sample_rate: float | int = 16000,
        frame_length: int = 2048,
        hop_length: int = 512,
        device="cuda",
        batch_size=16,
        compute_type="float16",
        whisper_model_name="large-v3",
    ) -> None:
        """_summary_

        Args:
            sample_rate (float | int, optional): _description_. Defaults to 16000.
            frame_length (int, optional): _description_. Defaults to 2048.
            hop_length (int, optional): _description_. Defaults to 512.
            device (str, optional): _description_. Defaults to "cuda".
            batch_size (int, optional): _description_. Defaults to 16.
            compute_type (str, optional): _description_. Defaults to "float16".
            whisper_model_name (str, optional): _description_. Defaults to "large-v3".
        """
        self.sample_rate = int(sample_rate)
        self.frame_length = frame_length
        self.hop_length = hop_length
        self.batch_size = batch_size
        self.device = device
        self.compute_type = compute_type
        self.g2p_en = G2P_EN()
        self.g2p_zh = G2P_ZH(style="pinyin", enable_non_tradional_chinese=True)
        self.whisper_model = whisperx.load_model(
            whisper_model_name, device, compute_type=compute_type
        )
        model_a, metadata = whisperx.load_align_model(language_code="en", device=device)
        self.align_model = model_a
        self.metadata = metadata
        self.diarize_model = DiarizationPipeline(
            use_auth_token=os.getenv("HF_TOKEN"), device=device
        )

    def extract_all(
        self,
        audio_path: Optional[str] = None,
        audio: Optional[np.ndarray] = None,
    ) -> dict:
        # Placeholder for semantic feature extraction logic
        result = {}
        if audio is None and audio_path is None:
            raise ValueError("Either audio data or audio_path must be provided.")
        result = self.whisperx_pipeline(audio_path=audio_path)
        return result

    def get_syllable_rate(self, result_item: dict) -> float:
        # Placeholder for syllable rate extraction logic
        phonemes = result_item.get("phonemes", [])
        duration = result_item.get("end", 0) - result_item.get("start", 0)
        if duration > 0:
            syllable_rate = len(phonemes) / duration
            return syllable_rate
        return 0.0

    def get_phonemes(self, text: Optional[str] = None, language: str = "en") -> list:
        assert text is not None, "text must be provided to extract phonemes."
        if language == "en":
            phonemes = self.g2p_en(text)
        elif language == "zh":
            phonemes = self.g2p_zh(text)[0]
        else:
            phonemes = text.split()
        return phonemes

    def get_text(self, audio_path: Optional[str] = None) -> TranscriptionResult:
        assert audio_path is not None, "audio_path must be provided to extract text."

        audio = whisperx.load_audio(audio_path)
        result = self.whisper_model.transcribe(audio, batch_size=self.batch_size)
        return result

    def get_word_alignment(
        self,
        audio: np.ndarray,
        asr_result: TranscriptionResult,
    ) -> AlignedTranscriptionResult:
        assert audio is not None, "audio must be provided to extract text."
        if asr_result["language"] != "en":
            align_model, metadata = whisperx.load_align_model(
                language_code=asr_result["language"], device=self.device
            )
            result = whisperx.align(
                asr_result["segments"],
                align_model,
                metadata,
                audio,
                self.device,
                return_char_alignments=False,
            )
        else:
            result = whisperx.align(
                asr_result["segments"],
                self.align_model,
                self.metadata,
                audio,
                self.device,
                return_char_alignments=False,
            )
        return result

    def diarize_audio(
        self,
        audio: Optional[np.ndarray] = None,
        result: Optional[AlignedTranscriptionResult] = None,
    ) -> Dict[str, Any]:
        assert audio is not None, "audio must be provided for diarization."
        assert (
            result is not None
        ), "AlignedTranscriptionResult or TranscriptionResult must be provided for diarization."

        diarize_segments = self.diarize_model(audio)
        diarize_result = whisperx.assign_word_speakers(diarize_segments, result)
        return diarize_result

    def whisperx_pipeline(
        self,
        audio_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        assert audio_path is not None, "audio_path must be provided for pipeline."

        audio = whisperx.load_audio(audio_path)
        result = self.whisper_model.transcribe(audio, batch_size=self.batch_size)
        language = result.get("language", "en")
        result = self.get_word_alignment(audio, result)
        result = self.diarize_audio(audio, result)
        result = self.merge_result(result)
        phonemes = self.get_phonemes(
            text=result["segments"]["text"],
            language=language,
        )
        result["segments"]["phonemes"] = phonemes
        result["segments"]["syllable_rate"] = self.get_syllable_rate(result["segments"])
        result["segments"]["language"] = language
        return result

    def merge_result(self, result):
        """Whisper will automaticlly split one audio into many though you know it is one speaker audio.
        This function will merge all segments into one segment."""
        end = result["segments"][-1]["end"] if result["segments"] else 0.0
        start = result["segments"][0]["start"] if result["segments"] else 0.0
        text = " ".join([seg["text"] for seg in result.get("segments", [])])
        merged_result = {
            "segments": {
                "start": start,
                "end": end,
                "text": text,
            },
            "word_segments": result.get("word_segments", []),
        }
        return merged_result


if __name__ == "__main__":
    # Example usage
    audio_path = "data/somos/audios/booksent_2012_0005_001.wav"

    extractor = SemanticFeatureExtractor()
    result = extractor.whisperx_pipeline(audio_path=audio_path)
    print("WhisperX pipeline result:", result)
