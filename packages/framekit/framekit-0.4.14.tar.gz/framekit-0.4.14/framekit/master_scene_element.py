import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import subprocess
import json
import copy
from typing import List, Literal, Optional
import platform as platform_module

import cv2
import numpy as np
import pygame
from tqdm import tqdm
from OpenGL.GL import *
from OpenGL.GLU import *

from .scene_element import Scene
from .audio_element import AudioElement
from .text_element import TextElement
from .audio_utils import has_audio_stream, HAS_FFMPEG


class MasterScene:
    def __init__(
        self,
        output_filename: str = "output_video.mp4",
        width: int = 1920,
        height: int = 1080,
        fps: int = 60,
        quality: Literal["low", "medium", "high"] = "medium"
    ) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self.quality = quality
        self.scenes: List[Scene] = []
        self.total_duration = 0.0
        self.output_filename = output_filename
        self.audio_elements = []
        self._has_content_at_start = False
        self._use_nvenc = self._check_nvenc_available()

        self.quality_multipliers = {"low": 1, "medium": 2, "high": 4}
        self.render_scale = self.quality_multipliers.get(quality, 2)
        self.render_width = width * self.render_scale
        self.render_height = height * self.render_scale

    def add(self, scene: Scene, layer: Literal["top", "bottom"] = "top") -> 'MasterScene':
        if scene.start_time is None:
            scene_has_content_at_start = self._scene_has_content_at_time(scene, 0.0)

            if scene_has_content_at_start and not self._has_content_at_start:
                scene.start_time = 0.0
                self._has_content_at_start = True
            elif self.scenes:
                last_scene = self.scenes[-1]
                last_scene_start = last_scene.start_time if last_scene.start_time is not None else 0.0
                scene.start_time = last_scene_start + last_scene.duration
            else:
                scene.start_time = 0.0

        if layer == "bottom":
            self.scenes.insert(0, scene)
        else:
            self.scenes.append(scene)

        self.total_duration = max(self.total_duration, scene.start_time + scene.duration)
        self._collect_audio_elements(scene)
        self._update_master_bgm_durations()
        return self

    def _check_nvenc_available(self) -> bool:
        if not HAS_FFMPEG:
            return False
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return 'h264_nvenc' in result.stdout
        except Exception:
            return False

    def _scene_has_content_at_time(self, scene: Scene, time: float) -> bool:
        for element in scene.elements:
            if isinstance(element, Scene):
                element_start = element.start_time if element.start_time is not None else 0.0
                if element_start <= time < element_start + element.duration:
                    if self._scene_has_content_at_time(element, time - element_start):
                        return True
            else:
                if element.start_time <= time < element.start_time + element.duration:
                    return True
        return False

    def _update_master_bgm_durations(self) -> None:
        for audio_element in self.audio_elements:
            if isinstance(audio_element, AudioElement) and audio_element.loop_until_scene_end:
                if self.total_duration > audio_element.duration:
                    audio_element.duration = self.total_duration

    def _collect_audio_elements(self, scene: Scene, time_offset: float = 0.0) -> None:
        from .video_element import VideoElement

        scene_start = scene.start_time if scene.start_time is not None else 0.0
        total_offset = time_offset + scene_start

        for element in scene.elements:
            if isinstance(element, Scene):
                self._collect_audio_elements(element, total_offset)
            elif isinstance(element, AudioElement):
                audio_copy = copy.deepcopy(element)
                audio_copy.start_time += total_offset
                self.audio_elements.append(audio_copy)
            elif isinstance(element, VideoElement):
                element._ensure_audio_element()
                audio_element = element.get_audio_element()
                if audio_element is not None:
                    audio_copy = copy.deepcopy(audio_element)
                    audio_copy.start_time += total_offset
                    self.audio_elements.append(audio_copy)

    def set_output(self, filename: str) -> 'MasterScene':
        self.output_filename = filename
        return self

    def set_quality(self, quality: str) -> 'MasterScene':
        if quality not in self.quality_multipliers:
            quality = "medium"

        self.quality = quality
        self.render_scale = self.quality_multipliers[quality]
        self.render_width = self.width * self.render_scale
        self.render_height = self.height * self.render_scale
        return self

    def _apply_quality_to_scene(self, scene: Scene) -> None:
        for element in scene.elements:
            if isinstance(element, Scene):
                self._apply_quality_to_scene(element)
            elif isinstance(element, TextElement):
                if not hasattr(element, 'quality_scale') or element.quality_scale != self.render_scale:
                    element.quality_scale = self.render_scale
                    element.texture_created = False
                    element.calculate_size()

    def _init_opengl(self) -> None:
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glViewport(0, 0, self.render_width, self.render_height)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def _setup_video_writer(self) -> tuple:
        if self.audio_elements:
            base_name = os.path.splitext(self.output_filename)[0]
            ext = os.path.splitext(self.output_filename)[1]
            full_path = f"{base_name}_temp_video_only{ext}"
        else:
            full_path = self.output_filename

        if self._use_nvenc and HAS_FFMPEG:
            cmd = [
                'ffmpeg', '-y',
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-s', f'{self.width}x{self.height}',
                '-pix_fmt', 'bgra',
                '-r', str(self.fps),
                '-i', '-',
                '-c:v', 'h264_nvenc',
                '-preset', 'fast',
                '-pix_fmt', 'yuv420p',
                full_path
            ]
            try:
                ffmpeg_process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                return ffmpeg_process, full_path
            except Exception:
                pass

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(full_path, fourcc, self.fps, (self.width, self.height))

        if not video_writer.isOpened():
            raise Exception(f"Failed to create video file: {full_path}")

        return video_writer, full_path

    def _capture_frame(self, use_bgra: bool = False) -> np.ndarray:
        pixels = glReadPixels(0, 0, self.render_width, self.render_height, GL_RGBA, GL_UNSIGNED_BYTE)
        image = np.frombuffer(pixels, dtype=np.uint8)
        image = image.reshape((self.render_height, self.render_width, 4))
        image = np.flipud(image)

        if self.render_scale > 1:
            image = cv2.resize(image, (self.width, self.height), interpolation=cv2.INTER_AREA)

        if use_bgra:
            return cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA)
        return cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)

    def _create_audio_mix(self, video_path: str) -> str:
        if not self.audio_elements:
            return video_path

        if not HAS_FFMPEG:
            return video_path

        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return video_path

        final_output = self.output_filename
        cmd = ['ffmpeg', '-y', '-i', video_path]

        valid_audio_files = []
        for audio_element in self.audio_elements:
            if not os.path.exists(audio_element.audio_path):
                continue

            if not has_audio_stream(audio_element.audio_path):
                continue

            if getattr(audio_element, 'loop_until_scene_end', False) and audio_element.duration > audio_element.original_duration:
                loop_count = int((audio_element.duration / audio_element.original_duration) + 0.99)
                for i in range(loop_count):
                    cmd.extend(['-i', audio_element.audio_path])
            else:
                cmd.extend(['-i', audio_element.audio_path])

            valid_audio_files.append(audio_element)

        if not valid_audio_files:
            return video_path

        if len(valid_audio_files) == 1:
            audio_element = valid_audio_files[0]
            volume = 0.0 if getattr(audio_element, 'is_muted', False) else getattr(audio_element, 'volume', 1.0)

            if getattr(audio_element, 'loop_until_scene_end', False) and audio_element.duration > audio_element.original_duration:
                loop_count = int((audio_element.duration / audio_element.original_duration) + 0.99)
                input_streams = [f"[{i}:a]" for i in range(1, loop_count + 1)]
                concat_filter = ''.join(input_streams) + f"concat=n={loop_count}:v=0:a=1[looped];"

                filter_chain = "[looped]"
                if audio_element.start_time > 0:
                    delay_ms = int(audio_element.start_time * 1000)
                    filter_chain += f"adelay={delay_ms}|{delay_ms},"

                filter_chain += f"volume={volume},atrim=end={self.total_duration}"
                full_filter = concat_filter + filter_chain
                cmd.extend(['-filter_complex', full_filter, '-c:v', 'copy', '-c:a', 'aac', '-t', str(self.total_duration), final_output])
            else:
                filter_chain = ""
                if audio_element.start_time > 0:
                    delay_ms = int(audio_element.start_time * 1000)
                    filter_chain += f"adelay={delay_ms}|{delay_ms},"

                filter_chain += f"volume={volume},atrim=end={self.total_duration}"
                cmd.extend(['-filter:a', filter_chain, '-c:v', 'copy', '-c:a', 'aac', '-t', str(self.total_duration), final_output])
        else:
            audio_inputs = []
            for i, audio_element in enumerate(valid_audio_files, 1):
                volume = 0.0 if getattr(audio_element, 'is_muted', False) else getattr(audio_element, 'volume', 1.0)
                delay_ms = int(audio_element.start_time * 1000)

                filter_chain = f"[{i}:a]"

                if getattr(audio_element, 'loop_until_scene_end', False) and audio_element.duration > audio_element.original_duration:
                    filter_chain += f"aloop=loop=-1:size={int(44100 * audio_element.original_duration)},atrim=end={audio_element.duration},"

                if delay_ms > 0:
                    filter_chain += f"adelay={delay_ms}|{delay_ms},"

                filter_chain += f"volume={volume}"

                if getattr(audio_element, 'loop_until_scene_end', False):
                    filter_chain += f",atrim=end={self.total_duration}"

                audio_inputs.append(f"{filter_chain}[a{i}]")

            mix_inputs = ''.join([f"[a{i}]" for i in range(1, len(valid_audio_files) + 1)])
            filter_complex = ';'.join(audio_inputs) + f";{mix_inputs}amix=inputs={len(valid_audio_files)}:normalize=0[aout]"
            cmd.extend(['-filter_complex', filter_complex, '-map', '0:v', '-map', '[aout]', '-c:v', 'copy', '-c:a', 'aac', '-t', str(self.total_duration), final_output])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                if os.path.exists(video_path) and "temp_video_only" in video_path:
                    os.remove(video_path)
                return final_output
            return video_path
        except Exception:
            return video_path

    def render(self) -> None:
        if 'SDL_VIDEODRIVER' not in os.environ:
            system = platform_module.system()
            is_container = os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv')

            if system == 'Darwin':
                os.environ['SDL_VIDEODRIVER'] = 'cocoa'
            elif system == 'Windows':
                os.environ['SDL_VIDEODRIVER'] = 'windows'

            if is_container or not os.environ.get('DISPLAY'):
                os.environ['SDL_AUDIODRIVER'] = 'dummy'

        os.environ['SDL_VIDEO_WINDOW_POS'] = '-1000,-1000'
        os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

        pygame.init()

        try:
            screen = pygame.display.set_mode(
                (self.render_width, self.render_height),
                pygame.DOUBLEBUF | pygame.OPENGL | pygame.HIDDEN
            )
        except pygame.error as e:
            raise NotImplementedError("OpenGL is required but failed to initialize")

        self._init_opengl()
        video_writer, video_path = self._setup_video_writer()
        is_ffmpeg_process = hasattr(video_writer, 'stdin')

        try:
            total_frames = int(self.total_duration * self.fps)

            for scene in self.scenes:
                self._apply_quality_to_scene(scene)

            with tqdm(total=total_frames, desc="Rendering", unit="frames") as pbar:
                for frame_num in range(total_frames):
                    current_time = frame_num / self.fps
                    glClear(GL_COLOR_BUFFER_BIT)

                    for scene in self.scenes:
                        scene.render(current_time)

                    if is_ffmpeg_process:
                        frame_bgra = self._capture_frame(use_bgra=True)
                        video_writer.stdin.write(frame_bgra.tobytes())
                    else:
                        frame_bgr = self._capture_frame()
                        video_writer.write(frame_bgr)

                    pygame.display.flip()
                    pbar.update(1)

        finally:
            if is_ffmpeg_process:
                video_writer.stdin.close()
                video_writer.wait()
            else:
                video_writer.release()
            pygame.quit()

            if self.audio_elements:
                final_output = self._create_audio_mix(video_path)
