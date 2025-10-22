import os
from typing import Optional
import numpy as np
from OpenGL.GL import *
from PIL import Image
from .video_base import VideoBase


class ImageElement(VideoBase):
    def __init__(self, image_path: str, scale: float = 1.0) -> None:
        super().__init__()
        self.image_path: str = image_path
        self.scale: float = scale
        self.texture_id: Optional[int] = None
        self.texture_width: int = 0
        self.texture_height: int = 0
        self.original_width: int = 0
        self.original_height: int = 0
        self.loop_until_scene_end: bool = False
        self._wants_scene_duration: bool = False
        self._create_image_texture()
        self.calculate_size()

    def _create_image_texture(self) -> None:
        self.texture_created = False

    def _create_texture_now(self) -> None:
        if not os.path.exists(self.image_path):
            print(f"Warning: Image file not found: {self.image_path}")
            return

        try:
            img = Image.open(self.image_path)

            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            self.original_width, self.original_height = img.size

            if self.scale != 1.0:
                new_width = int(self.original_width * self.scale)
                new_height = int(self.original_height * self.scale)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            img = self._apply_crop_to_image(img)
            img = self._apply_corner_radius_to_image(img)
            img = self._apply_border_and_background_to_image(img)
            img = self._apply_blur_to_image(img)

            self.texture_width, self.texture_height = img.size
            self.width = self.texture_width
            self.height = self.texture_height

            img_data = np.array(img)
            img_data = np.flipud(img_data)

            self.texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)

            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.texture_width, self.texture_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)

            glBindTexture(GL_TEXTURE_2D, 0)
            self.texture_created = True

        except Exception as e:
            print(f"Error loading image {self.image_path}: {e}")
            self.texture_created = False

    def set_scale(self, scale: float) -> 'ImageElement':
        self.scale = scale
        if self.texture_created:
            self.texture_created = False
        self.calculate_size()
        return self

    def set_loop_until_scene_end(self, loop: bool = True) -> 'ImageElement':
        self.loop_until_scene_end = loop
        if loop:
            self._wants_scene_duration = True
        return self

    def update_duration_for_scene(self, scene_duration: float) -> None:
        if (self.loop_until_scene_end or self._wants_scene_duration) and scene_duration > 0:
            self.duration = scene_duration

    def start_at(self, start_time: float) -> 'ImageElement':
        super().start_at(start_time)
        return self

    def set_duration(self, duration: float) -> 'ImageElement':
        super().set_duration(duration)
        return self

    def render(self, time: float) -> None:
        if not self.is_visible_at(time):
            return

        if not self.texture_created:
            self._create_texture_now()

        if self.texture_id is None or not self.texture_created:
            return

        self.update_animated_properties(time)
        animated_props = self.get_animated_properties(time)
        current_alpha = animated_props.get('alpha', 1.0)
        render_x, render_y, scaled_width, scaled_height = self.get_actual_render_position()

        glPushMatrix()

        center_x = render_x + scaled_width / 2
        center_y = render_y + scaled_height / 2

        glTranslatef(center_x, center_y, 0)

        current_rotation = animated_props.get('rotation', getattr(self, 'rotation', 0.0))
        if current_rotation != 0:
            glRotatef(current_rotation, 0, 0, 1)

        flip_x = -1.0 if getattr(self, 'flip_horizontal', False) else 1.0
        flip_y = -1.0 if getattr(self, 'flip_vertical', False) else 1.0
        if flip_x != 1.0 or flip_y != 1.0:
            glScalef(flip_x, flip_y, 1.0)

        glTranslatef(-center_x, -center_y, 0)

        if current_alpha < 1.0:
            glColor4f(1.0, 1.0, 1.0, current_alpha)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(render_x, render_y + scaled_height)

        glTexCoord2f(1.0, 0.0)
        glVertex2f(render_x + scaled_width, render_y + scaled_height)

        glTexCoord2f(1.0, 1.0)
        glVertex2f(render_x + scaled_width, render_y)

        glTexCoord2f(0.0, 1.0)
        glVertex2f(render_x, render_y)
        glEnd()

        glPopMatrix()

    def calculate_size(self) -> None:
        if not os.path.exists(self.image_path):
            self.width = 0
            self.height = 0
            return

        try:
            from PIL import Image
            with Image.open(self.image_path) as img:
                original_width, original_height = img.size

            scaled_width = int(original_width * self.scale)
            scaled_height = int(original_height * self.scale)

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

        except Exception as e:
            print(f"Error calculating image size {self.image_path}: {e}")
            self.width = 0
            self.height = 0

    def __del__(self) -> None:
        if self.texture_id:
            try:
                glDeleteTextures(1, [self.texture_id])
            except:
                pass
