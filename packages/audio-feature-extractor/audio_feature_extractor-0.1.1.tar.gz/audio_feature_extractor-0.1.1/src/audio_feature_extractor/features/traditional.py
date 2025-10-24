import os

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import parselmouth
from parselmouth.praat import call
from typing import Optional
from scipy import signal
import logging


def _to_serializable(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.floating, float)):
        return float(obj)
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_to_serializable(v) for v in obj]
    else:
        # 对于不能序列化的对象，返回字符串描述
        try:
            import json

            json.dumps(obj)
            return obj
        except Exception:
            return str(obj)


class TraditionalFeatureExtractor:
    """语音听感量化分析工具"""

    def __init__(
        self,
        sample_rate: float | int = 16000,
        frame_length: int = 2048,
        hop_length: int = 512,
    ) -> None:
        self.sample_rate = int(sample_rate)
        self.frame_length = frame_length
        self.hop_length = hop_length

    def _praat_time_step(self) -> float:
        """将 hop_length/frame_length 转换为 Praat 的 time_step（秒）"""
        hop_seconds = max(self.hop_length / self.sample_rate, 1e-4)
        frame_seconds = max(self.frame_length / self.sample_rate, hop_seconds)
        return min(frame_seconds, hop_seconds)

    def get_all_features(
        self,
        audio: Optional[np.ndarray] = None,
        audio_path: Optional[str] = None,
        filename="unknown",
    ):
        if audio is None and audio_path is None:
            raise ValueError("Either audio data or audio_path must be provided.")
        if audio_path is not None:
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
        """获取所有特征"""
        features = (
            self.analyze_loudness(audio, filename)
            | self.get_pitch(audio, filename)
            | self.analyze_timbre(audio, filename)
            | self.analyze_speech_clarity(audio, filename)
            | self.analyze_comfort(audio, filename)
        )
        return features

    def analyze_loudness(self, audio=None, filename="unknown"):
        """分析响度（忽略静音区）"""
        logging.debug(f"Analyzing loudness for file: {filename}")
        assert audio is not None, "Audio data must be provided for loudness analysis."

        # 找出非静音区（以 top_db 为阈值，相对于峰值）
        intervals = librosa.effects.split(
            audio, top_db=40, frame_length=self.frame_length, hop_length=self.hop_length
        )  # intervals 为采样点索引对 [[s,e], ...]

        # 计算帧 RMS 与 dB
        rms = librosa.feature.rms(
            y=audio, frame_length=self.frame_length, hop_length=self.hop_length
        )[0]
        rms_db_seq = librosa.amplitude_to_db(rms, ref=1.0)
        times = librosa.frames_to_time(
            np.arange(len(rms)),
            sr=self.sample_rate,
            hop_length=self.hop_length,
            n_fft=self.frame_length,
        )

        # 如果没有检测到非静音区，则返回默认值
        if intervals.size == 0:
            return {
                "mean_rms_db": (
                    float(np.mean(rms_db_seq)) if rms_db_seq.size > 0 else 0.0
                ),
                "mean_intensity_db": 0.0,
                "rms_values": rms,
                "rms_db_values": rms_db_seq,
                "time": times,
                "non_silent_intervals": [],
                "intensity_seq": np.array([]),
            }

        # 为每一帧建立是否在非静音区的掩码
        frame_starts = (np.arange(len(rms)) * self.hop_length).astype(int)
        mask = np.zeros_like(rms, dtype=bool)
        for s, e in intervals:
            mask |= (frame_starts >= s) & (frame_starts < e)

        intensity_values = np.array([], dtype=float)

        # 如果掩码全部为 False，则视为无有效信号
        if not np.any(mask):
            mean_rms_db = float(np.mean(rms_db_seq)) if rms_db_seq.size > 0 else 0.0
            mean_intensity = 0.0
        else:
            mean_rms_db = float(np.mean(rms_db_seq[mask]))
            # 将非静音段拼接，用于计算强度的均值（避免用整个音频包含静音区）
            non_silent_segments = [audio[s:e] for s, e in intervals if e > s]
            if len(non_silent_segments) == 0:
                mean_intensity = 0.0
            else:
                audio_ns = np.concatenate(non_silent_segments)
                try:
                    sound_ns = parselmouth.Sound(
                        audio_ns, sampling_frequency=self.sample_rate
                    )
                    intensity_seq = sound_ns.to_intensity()
                    intensity_values = np.asarray(intensity_seq.values, dtype=float)
                    mean_intensity = float(np.mean(intensity_values))
                except Exception as ex:
                    logging.warning(
                        f"Failed to compute intensity for non-silent audio {filename}: {ex}"
                    )
                    mean_intensity = 0.0

        # 将 intervals 转为秒便于外部使用
        intervals_sec = [
            (float(s) / self.sample_rate, float(e) / self.sample_rate)
            for s, e in intervals
        ]

        return {
            "mean_rms_db": mean_rms_db,
            "mean_intensity_db": mean_intensity,
            "rms_values": rms,
            "intensity_seq": intensity_values,
            "rms_db_values": rms_db_seq,
            "time": times,
            "non_silent_intervals": intervals_sec,
        }

    def get_pitch(
        self,
        audio: Optional[np.ndarray] = None,
        filename="unknown",
        engine: str = "praat",
    ):
        """分析音调"""
        logging.debug(f"Analyzing pitch for file: {filename}")
        f0_mean = 0.0
        f0_std = 0.0
        f0 = np.array([])

        if audio is None:
            audio = getattr(self, "audio", None)
        if audio is None or len(audio) == 0:
            logging.warning(f"No audio available for pitch analysis: {filename}")

            return {
                "f0_mean": 0.0,
                "f0_std": 0.0,
                "f0": np.array([]),
            }
        try:
            if engine == "librosa":
                f0, voiced_flag, voiced_probs = librosa.pyin(
                    audio,
                    fmin=float(librosa.note_to_hz("C2")),  # ~65 Hz
                    fmax=float(librosa.note_to_hz("C7")),  # ~2093 Hz
                    sr=self.sample_rate,
                    frame_length=self.frame_length,
                    hop_length=self.hop_length,
                )
            elif engine == "praat":
                # 使用 Praat 计算音高更精确
                sound = parselmouth.Sound(audio, sampling_frequency=self.sample_rate)
                pitch_praat = sound.to_pitch(
                    time_step=self._praat_time_step(),
                    pitch_floor=65.0,
                    pitch_ceiling=500.0,
                )
                f0 = np.asarray(pitch_praat.selected_array["frequency"], dtype=float)

            else:
                raise ValueError(f"Unsupported pitch engine: {engine}")

            # 将 0 和 NaN 视为无声区域，忽略它们再计算均值和标准差
            f0_clean = np.where(np.isnan(f0) | (f0 == 0), np.nan, f0)
            if np.all(np.isnan(f0_clean)):
                f0_mean = 0.0
                f0_std = 0.0
            else:
                f0_mean = float(np.nanmean(f0_clean))
                f0_std = float(np.nanstd(f0_clean))
        except Exception as e:
            raise RuntimeError(
                f"Failed to compute pitch with {engine} for {filename}: {e}"
            )

        return {
            "f0_mean": f0_mean,
            "f0_std": f0_std,
            "f0": f0,
        }

    def analyze_timbre(self, audio=None, filename="unknown"):
        """分析音色"""
        logging.debug(f"Analyzing timbre for file: {filename}")
        assert audio is not None, "Audio data must be provided for timbre analysis."

        intervals = librosa.effects.split(
            audio, top_db=40, frame_length=self.frame_length, hop_length=self.hop_length
        )

        mfccs = librosa.feature.mfcc(
            y=audio,
            sr=self.sample_rate,
            n_mfcc=13,
            n_fft=self.frame_length,
            hop_length=self.hop_length,
        )

        spectral_centroids = librosa.feature.spectral_centroid(
            y=audio,
            sr=self.sample_rate,
            n_fft=self.frame_length,
            hop_length=self.hop_length,
        )[0]

        spectral_bandwidth = librosa.feature.spectral_bandwidth(
            y=audio,
            sr=self.sample_rate,
            n_fft=self.frame_length,
            hop_length=self.hop_length,
        )[0]

        frames = mfccs.shape[1] if mfccs.ndim == 2 else 0
        frame_starts = (
            (np.arange(frames) * self.hop_length).astype(int)
            if frames > 0
            else np.array([], dtype=int)
        )
        mask = np.zeros(frames, dtype=bool)
        for s, e in intervals:
            mask |= (frame_starts >= s) & (frame_starts < e)

        if frames == 0 or not np.any(mask):
            mfccs_mean = (
                np.mean(mfccs, axis=1) if frames > 0 else np.zeros(13, dtype=float)
            )
            centroid_mean = (
                float(np.mean(spectral_centroids)) if spectral_centroids.size else 0.0
            )
            bandwidth_mean = (
                float(np.mean(spectral_bandwidth)) if spectral_bandwidth.size else 0.0
            )
        else:
            mfccs_mean = np.mean(mfccs[:, mask], axis=1)
            centroid_mean = float(np.mean(spectral_centroids[mask]))
            bandwidth_mean = float(np.mean(spectral_bandwidth[mask]))

        self.mfcc = mfccs
        time_axis = librosa.times_like(
            spectral_centroids, sr=self.sample_rate, hop_length=self.hop_length
        )

        return {
            "mfccs": mfccs,
            "mfccs_mean": mfccs_mean,
            "spectral_centroid_mean": centroid_mean,
            "spectral_bandwidth_mean": bandwidth_mean,
            "spectral_centroids": spectral_centroids,
            "spectral_bandwidth": spectral_bandwidth,
            "time": time_axis,
        }

    def analyze_speech_clarity(
        self, audio: Optional[np.ndarray] = None, filename="unknown"
    ):
        """分析语音清晰度（仅在均值等统计量中过滤静音）"""
        logging.debug(f"Analyzing speech clarity for file: {filename}")

        if audio is None:
            audio = getattr(self, "audio", None)
        if audio is None or len(audio) == 0:
            return {
                "snr_db": float("inf"),
                "signal_power": 0.0,
                "noise_power": 0.0,
                "rms_values": np.array([]),
                "time": np.array([]),
                "non_silent_intervals": [],
                "noise_intervals": [],
                "non_silent_mask": np.array([], dtype=bool),
            }

        intervals = librosa.effects.split(
            audio, top_db=40, frame_length=self.frame_length, hop_length=self.hop_length
        )

        rms = librosa.feature.rms(
            y=audio, frame_length=self.frame_length, hop_length=self.hop_length
        )[0]
        times = librosa.frames_to_time(
            np.arange(len(rms)),
            sr=self.sample_rate,
            hop_length=self.hop_length,
            n_fft=self.frame_length,
        )

        frame_starts = (np.arange(len(rms)) * self.hop_length).astype(int)
        mask = np.zeros(len(rms), dtype=bool)
        for s, e in intervals:
            mask |= (frame_starts >= s) & (frame_starts < e)

        signal_segments = [audio[s:e] for s, e in intervals if e > s]
        signal_concat = (
            np.concatenate(signal_segments) if signal_segments else np.array([])
        )

        silent_intervals = []
        prev_end = 0
        for s, e in intervals:
            if s > prev_end:
                silent_intervals.append((prev_end, s))
            prev_end = e
        if prev_end < len(audio):
            silent_intervals.append((prev_end, len(audio)))
        noise_segments = [audio[s:e] for s, e in silent_intervals if e > s]
        noise_concat = (
            np.concatenate(noise_segments) if noise_segments else np.array([])
        )

        signal_power = float(np.mean(signal_concat**2)) if signal_concat.size else 0.0
        noise_power = float(np.mean(noise_concat**2)) if noise_concat.size else 0.0
        snr_db = (
            float("inf")
            if noise_power == 0.0
            else float(10 * np.log10(max(signal_power, 1e-12) / noise_power))
        )

        intervals_sec = [
            (float(s) / self.sample_rate, float(e) / self.sample_rate)
            for s, e in intervals
        ]
        noise_intervals_sec = [
            (float(s) / self.sample_rate, float(e) / self.sample_rate)
            for s, e in silent_intervals
        ]

        return {
            "snr_db": snr_db,
            "signal_power": signal_power,
            "noise_power": noise_power,
            "rms_values": rms,
            "time": times,
            "non_silent_intervals": intervals_sec,
            "noise_intervals": noise_intervals_sec,
            "non_silent_mask": mask,
        }

    def analyze_comfort(self, audio=None, filename="unknown"):
        """分析舒适度（统计量过滤静音，序列完整保留）"""
        logging.debug(f"Analyzing comfort for file: {filename}")

        if audio is None:
            audio = getattr(self, "audio", None)
        if audio is None or len(audio) == 0:
            return {
                "jitter_local": 0.0,
                "shimmer_local": 0.0,
                "pitch_range_hz": 0.0,
                "pitch_mean_hz": 0.0,
                "pitch_std_hz": 0.0,
                "pitch_values": np.array([]),
                "pitch_times": np.array([]),
                "non_silent_intervals": [],
            }

        intervals = librosa.effects.split(
            audio, top_db=40, frame_length=self.frame_length, hop_length=self.hop_length
        )
        non_silent_segments = [audio[s:e] for s, e in intervals if e > s]
        audio_ns = np.concatenate(non_silent_segments) if non_silent_segments else audio

        sound: Optional[parselmouth.Sound] = None
        pitch = None
        point_process = None

        try:
            sound = parselmouth.Sound(audio_ns, sampling_frequency=self.sample_rate)
            point_process = call(sound, "To PointProcess (periodic, cc)", 75.0, 500.0)
            jitter_local = float(
                call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
            )
        except Exception as e:
            logging.warning(f"Failed to compute jitter for {filename}: {e}")
            jitter_local = 0.0

        if sound is not None and point_process is not None:
            try:
                shimmer_local = float(
                    call(
                        [sound, point_process],
                        "Get shimmer (local)",
                        0,
                        0,
                        0.0001,
                        0.02,
                        1.3,
                        1.6,
                    )
                )
            except Exception as e:
                logging.warning(f"Failed to compute shimmer for {filename}: {e}")
                shimmer_local = 0.0
        else:
            shimmer_local = 0.0

        intervals_sec = [
            (float(s) / self.sample_rate, float(e) / self.sample_rate)
            for s, e in intervals
        ]

        return {
            "jitter_local": jitter_local,
            "shimmer_local": shimmer_local,
            "non_silent_intervals": intervals_sec,
        }

    def get_duration(self, audio):
        """获取音频时长"""
        duration = librosa.get_duration(y=audio, sr=self.sample_rate)
        return duration

    def generate_analysis_report(self, audio, output_file=None):
        """生成分析报告"""
        results = {
            "时长(秒)": self.get_duration(audio),
            "采样率(Hz)": self.sample_rate,
            "响度分析": self.analyze_loudness(audio),
            "音调分析": self.get_pitch(audio),
            "音色分析": self.analyze_timbre(audio),
            "语音清晰度分析": self.analyze_speech_clarity(audio),
            "舒适度分析": self.analyze_comfort(audio),
        }

        if output_file:
            # 保存为 JSON 格式
            import json

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(
                    _to_serializable(results),
                    f,
                    ensure_ascii=False,
                    indent=4,
                )
            print(f"分析结果已保存至 {output_file}")

        return results


if __name__ == "__main__":
    filepath = "data/somos/audios/booksent_2012_0005_001.wav"
    extractor = TraditionalFeatureExtractor(sample_rate=16000)
    report = extractor.get_all_features(audio_path=filepath)
    breakpoint()
