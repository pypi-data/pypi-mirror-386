import os
from typing import Optional, Dict, Any, Union
import numpy as np
from .video_base import VideoBase

try:
    import mutagen
    from mutagen import File as MutagenFile
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False


class AudioElement(VideoBase):
    def __init__(self, audio_path: str, volume: float = 1.0) -> None:
        super().__init__()
        self.audio_path: str = audio_path
        self.volume: float = volume
        self.original_volume: float = volume
        self.sample_rate: int = 44100
        self.total_samples: int = 0
        self.channels: int = 2
        self.current_audio_data: Optional[np.ndarray] = None
        self.fade_in_duration: float = 0.0
        self.fade_out_duration: float = 0.0
        self.is_muted: bool = False
        self.loop_until_scene_end: bool = False
        self.original_duration: float = 0.0
        self._load_audio_info()
        self.calculate_size()

    def _load_audio_info(self) -> None:
        if not os.path.exists(self.audio_path):
            print(f"Warning: Audio file not found: {self.audio_path}")
            return

        try:
            if HAS_MUTAGEN:
                audio_file = MutagenFile(self.audio_path)
                if audio_file is not None and hasattr(audio_file, 'info'):
                    self.duration = float(audio_file.info.length)
                    self.original_duration = self.duration
                    return

            if HAS_LIBROSA:
                try:
                    y, sr = librosa.load(self.audio_path, sr=None)
                    self.duration = len(y) / sr
                    self.original_duration = self.duration
                    self.sample_rate = sr
                    return
                except Exception as librosa_error:
                    print(f"Librosa failed: {librosa_error}")

            print(f"Warning: Could not determine audio duration for {self.audio_path}")
            print("Install 'mutagen' or 'librosa' for proper audio file support:")
            print("  pip3 install mutagen")
            print("  pip3 install librosa")
            self.duration = 10.0
            self.original_duration = self.duration

        except Exception as e:
            print(f"Error loading audio info {self.audio_path}: {e}")
            self.duration = 10.0
            self.original_duration = self.duration

    def set_volume(self, volume: float) -> 'AudioElement':
        self.volume = max(0.0, volume)
        self.original_volume = self.volume
        return self

    def set_fade_in(self, duration: float) -> 'AudioElement':
        self.fade_in_duration = max(0.0, duration)
        return self

    def set_fade_out(self, duration: float) -> 'AudioElement':
        self.fade_out_duration = max(0.0, duration)
        return self

    def mute(self) -> 'AudioElement':
        self.is_muted = True
        return self

    def unmute(self) -> 'AudioElement':
        self.is_muted = False
        return self

    def set_loop_until_scene_end(self, loop: bool = True) -> 'AudioElement':
        self.loop_until_scene_end = loop
        return self

    def update_duration_for_scene(self, scene_duration: float) -> None:
        if self.loop_until_scene_end and scene_duration > 0:
            self.duration = scene_duration

    def get_effective_volume(self, audio_time: float) -> float:
        if self.is_muted:
            return 0.0

        effective_volume = self.volume

        if self.fade_in_duration > 0 and audio_time < self.fade_in_duration:
            fade_in_factor = audio_time / self.fade_in_duration
            effective_volume *= fade_in_factor

        if self.fade_out_duration > 0:
            fade_out_start = self.duration - self.fade_out_duration
            if audio_time > fade_out_start:
                remaining_time = self.duration - audio_time
                fade_out_factor = remaining_time / self.fade_out_duration
                effective_volume *= fade_out_factor

        return max(0.0, effective_volume)

    def _get_audio_at_time(self, audio_time: float) -> None:
        return None

    def render(self, time: float) -> None:
        if not self.is_visible_at(time):
            return

    def get_audio_data_at_time(self, time: float) -> Optional[Dict[str, Any]]:
        if not self.is_visible_at(time):
            return None

        audio_time = time - self.start_time
        effective_volume = self.get_effective_volume(audio_time)

        return {
            'audio_path': self.audio_path,
            'audio_time': audio_time,
            'volume': effective_volume,
            'original_volume': self.original_volume,
            'start_time': self.start_time,
            'duration': self.duration,
            'is_muted': self.is_muted,
            'fade_in_duration': self.fade_in_duration,
            'fade_out_duration': self.fade_out_duration
        }

    def calculate_size(self) -> None:
        self.width = 0
        self.height = 0

    def __del__(self) -> None:
        pass
