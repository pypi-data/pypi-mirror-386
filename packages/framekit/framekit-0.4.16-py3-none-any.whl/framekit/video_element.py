import os
from typing import Optional, Tuple, Any
import cv2
import numpy as np
from OpenGL.GL import *
from PIL import Image
from .video_base import VideoBase
from .audio_element import AudioElement
from .audio_utils import has_audio_stream


class VideoElement(VideoBase):
    def __init__(self, video_path: str, scale: float = 1.0) -> None:
        super().__init__()
        self.video_path: str = video_path
        self.scale: float = scale
        self.texture_id: Optional[int] = None
        self.texture_width: int = 0
        self.texture_height: int = 0
        self.original_width: int = 0
        self.original_height: int = 0
        self.video_capture: Optional[cv2.VideoCapture] = None
        self.fps: float = 30.0
        self.total_frames: int = 0
        self.current_frame_data: Optional[np.ndarray] = None
        self.audio_element: Optional[AudioElement] = None
        self.loop_until_scene_end: bool = False
        self.original_duration: float = 0.0
        self._wants_scene_duration: bool = False
        self._create_video_texture()
        self.calculate_size()
        self.audio_element = None
        self._audio_element_created = False

    def _create_video_texture(self) -> None:
        self.texture_created = False
        self._load_video_info()

    def _load_video_info(self) -> None:
        if not os.path.exists(self.video_path):
            print(f"Warning: Video file not found: {self.video_path}")
            return

        try:
            self.video_capture = cv2.VideoCapture(self.video_path)

            if not self.video_capture.isOpened():
                print(f"Error: Cannot open video file: {self.video_path}")
                return

            self.original_width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.original_height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))

            base_width = int(self.original_width * self.scale)
            base_height = int(self.original_height * self.scale)

            self.texture_width = base_width + self.padding['left'] + self.padding['right']
            self.texture_height = base_height + self.padding['top'] + self.padding['bottom']

            if self.fps > 0 and self.total_frames > 0:
                video_duration = self.total_frames / self.fps
                self.duration = video_duration
                self.original_duration = video_duration

        except Exception as e:
            print(f"Error loading video info {self.video_path}: {e}")

    def _create_audio_element(self) -> None:
        if self._audio_element_created:
            return

        if not has_audio_stream(self.video_path):
            self.audio_element = None
            self._audio_element_created = True
            return

        try:
            self.audio_element = AudioElement(self.video_path, volume=1.0)
            self._sync_audio_timing()
            self._audio_element_created = True
        except Exception as e:
            print(f"Failed to create audio element for {self.video_path}: {e}")
            self.audio_element = None
            self._audio_element_created = True

    def _sync_audio_timing(self) -> None:
        if self.audio_element:
            self.audio_element.start_at(self.start_time)
            self.audio_element.set_duration(self.duration)

    def get_audio_element(self) -> Optional[AudioElement]:
        return self.audio_element

    def _create_texture_now(self) -> None:
        if self.texture_id is None:
            self.texture_id = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        glBindTexture(GL_TEXTURE_2D, 0)
        self.texture_created = True

    def _get_frame_at_time(self, video_time: float) -> Optional[np.ndarray]:
        if self.video_capture is None or not self.video_capture.isOpened():
            return None

        frame_number = int(video_time * self.fps)
        frame_number = max(0, min(frame_number, self.total_frames - 1))

        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        ret, frame = self.video_capture.read()
        if not ret:
            return None

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if self.scale != 1.0:
            new_width = int(self.original_width * self.scale)
            new_height = int(self.original_height * self.scale)
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

        alpha = np.full((frame.shape[0], frame.shape[1], 1), 255, dtype=np.uint8)
        frame = np.concatenate([frame, alpha], axis=2)

        pil_frame = Image.fromarray(frame, 'RGBA')

        pil_frame = self._apply_crop_to_image(pil_frame)
        pil_frame = self._apply_corner_radius_to_image(pil_frame)
        pil_frame = self._apply_border_and_background_to_image(pil_frame)
        pil_frame = self._apply_blur_to_image(pil_frame)

        self.width = pil_frame.size[0]
        self.height = pil_frame.size[1]

        frame = np.array(pil_frame)
        frame = np.flipud(frame)

        return frame

    def set_scale(self, scale: float) -> 'VideoElement':
        self.scale = scale
        if hasattr(self, 'original_width'):
            base_width = int(self.original_width * self.scale)
            base_height = int(self.original_height * self.scale)

            self.texture_width = base_width + self.padding['left'] + self.padding['right']
            self.texture_height = base_height + self.padding['top'] + self.padding['bottom']

            border_size = self.border_width * 2 if self.border_color else 0
            self.width = self.texture_width + border_size
            self.height = self.texture_height + border_size
        return self

    def start_at(self, start_time: float) -> 'VideoElement':
        super().start_at(start_time)
        self._ensure_audio_element()
        self._sync_audio_timing()
        return self

    def set_duration(self, duration: float) -> 'VideoElement':
        super().set_duration(duration)
        self._ensure_audio_element()
        self._sync_audio_timing()
        return self

    def _ensure_audio_element(self) -> None:
        if not self._audio_element_created:
            self._create_audio_element()

    def set_volume(self, volume: float) -> 'VideoElement':
        self._ensure_audio_element()
        if self.audio_element:
            self.audio_element.set_volume(volume)
        return self

    def set_audio_fade_in(self, duration: float) -> 'VideoElement':
        self._ensure_audio_element()
        if self.audio_element:
            self.audio_element.set_fade_in(duration)
        return self

    def set_audio_fade_out(self, duration: float) -> 'VideoElement':
        self._ensure_audio_element()
        if self.audio_element:
            self.audio_element.set_fade_out(duration)
        return self

    def mute_audio(self) -> 'VideoElement':
        self._ensure_audio_element()
        if self.audio_element:
            self.audio_element.mute()
        return self

    def unmute_audio(self) -> 'VideoElement':
        self._ensure_audio_element()
        if self.audio_element:
            self.audio_element.unmute()
        return self

    def get_audio_volume(self) -> float:
        self._ensure_audio_element()
        if self.audio_element:
            return self.audio_element.volume
        return 0.0

    def set_loop_until_scene_end(self, loop: bool = True) -> 'VideoElement':
        self.loop_until_scene_end = loop

        if loop and hasattr(self, 'original_duration') and self.original_duration > 0:
            self._wants_scene_duration = True

        return self

    def update_duration_for_scene(self, scene_duration: float) -> None:
        if (self.loop_until_scene_end or self._wants_scene_duration) and scene_duration > 0:
            self.duration = scene_duration

            self._ensure_audio_element()
            if self.audio_element and hasattr(self.audio_element, 'update_duration_for_scene'):
                self.audio_element.update_duration_for_scene(scene_duration)

    def render(self, time: float) -> None:
        if not self.is_visible_at(time):
            return

        if self.video_capture is None:
            return

        if not self.texture_created:
            self._create_texture_now()

        if self.texture_id is None:
            return

        video_time = time - self.start_time

        if self.loop_until_scene_end or self._wants_scene_duration:
            if self.original_duration > 0:
                if video_time >= self.original_duration:
                    video_time = video_time % self.original_duration
                elif video_time < 0:
                    video_time = 0

        frame_data = self._get_frame_at_time(video_time)
        if frame_data is None:
            return

        glPushAttrib(GL_ALL_ATTRIB_BITS)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        actual_height, actual_width = frame_data.shape[:2]
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, actual_width, actual_height,
                     0, GL_RGBA, GL_UNSIGNED_BYTE, frame_data)

        self.texture_width = actual_width
        self.texture_height = actual_height

        animated_props = self.get_animated_properties(time)

        original_width, original_height = self.width, self.height
        self.width, self.height = actual_width, actual_height

        render_x, render_y, _, _ = self.get_actual_render_position()

        if 'x' in animated_props:
            render_x = animated_props['x'] + self._calculate_anchor_offset(actual_width, actual_height)[0]
        if 'y' in animated_props:
            render_y = animated_props['y'] + self._calculate_anchor_offset(actual_width, actual_height)[1]

        self.width, self.height = original_width, original_height

        glPushMatrix()

        center_x = render_x + self.texture_width / 2
        center_y = render_y + self.texture_height / 2

        glTranslatef(center_x, center_y, 0)

        current_rotation = animated_props.get('rotation', getattr(self, 'rotation', 0.0))
        if current_rotation != 0:
            glRotatef(current_rotation, 0, 0, 1)

        flip_x = -1.0 if getattr(self, 'flip_horizontal', False) else 1.0
        flip_y = -1.0 if getattr(self, 'flip_vertical', False) else 1.0
        if flip_x != 1.0 or flip_y != 1.0:
            glScalef(flip_x, flip_y, 1.0)

        current_scale = animated_props.get('scale', getattr(self, 'scale', 1.0))
        if current_scale != 1.0:
            glScalef(current_scale, current_scale, 1.0)

        glTranslatef(-center_x, -center_y, 0)

        current_alpha = animated_props.get('alpha', 1.0)
        if current_alpha < 1.0:
            glColor4f(1.0, 1.0, 1.0, current_alpha / 255.0)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)

        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(render_x, render_y + self.texture_height)

        glTexCoord2f(1.0, 0.0)
        glVertex2f(render_x + self.texture_width, render_y + self.texture_height)

        glTexCoord2f(1.0, 1.0)
        glVertex2f(render_x + self.texture_width, render_y)

        glTexCoord2f(0.0, 1.0)
        glVertex2f(render_x, render_y)
        glEnd()

        glPopMatrix()

    def calculate_size(self) -> None:
        if not hasattr(self, 'original_width') or self.original_width == 0:
            self.width = 0
            self.height = 0
            return

        scaled_width = int(self.original_width * self.scale)
        scaled_height = int(self.original_height * self.scale)

        if self.crop_width is not None and self.crop_height is not None:
            content_width = self.crop_width
            content_height = self.crop_height
        else:
            content_width = scaled_width
            content_height = scaled_height

        canvas_width = max(content_width + self.padding['left'] + self.padding['right'], 1)
        canvas_height = max(content_height + self.padding['top'] + self.padding['bottom'], 1)

        self.width = canvas_width
        self.height = canvas_height

    def __del__(self) -> None:
        if self.video_capture:
            self.video_capture.release()

        if self.texture_id:
            try:
                glDeleteTextures(1, [self.texture_id])
            except:
                pass
