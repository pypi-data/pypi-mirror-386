import os
from typing import Tuple, Optional, List, Dict, Any, Literal, Union
import numpy as np
from OpenGL.GL import *
from PIL import Image, ImageDraw, ImageFont
from .video_base import VideoBase

_FONT_CACHE: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}


def _load_font_cached(font_path: Optional[str], size: int) -> ImageFont.FreeTypeFont:
    cache_key = (font_path or "", size)

    if cache_key in _FONT_CACHE:
        return _FONT_CACHE[cache_key]

    font = None
    if font_path and os.path.exists(font_path):
        try:
            font = ImageFont.truetype(font_path, size)
        except:
            pass

    if font is None:
        fallback_paths = [
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]
        for fallback_path in fallback_paths:
            try:
                font = ImageFont.truetype(fallback_path, size)
                break
            except:
                continue

    if font is None:
        font = ImageFont.load_default()

    _FONT_CACHE[cache_key] = font
    return font


class TextElement(VideoBase):
    def __init__(self, text: str, size: int = 50, color: Tuple[int, int, int] = (255, 255, 255),
                 font_path: Optional[str] = None, bold: bool = False, quality_scale: int = 1) -> None:
        super().__init__()
        self.text: str = text
        self.size: int = size
        self.color: Tuple[int, int, int] = color
        self.font_path: Optional[str] = font_path
        self.bold: bool = bold
        self.quality_scale: int = quality_scale
        self.texture_id: Optional[int] = None
        self.texture_width: int = 0
        self.texture_height: int = 0
        self.alignment: Literal['left', 'center', 'right'] = 'left'
        self.line_spacing: int = 0
        self.outline_color: Optional[Tuple[int, int, int]] = None
        self.outline_width: int = 0
        self._create_text_texture()
        self.calculate_size()

    def set_alignment(self, alignment: Literal['left', 'center', 'right']) -> 'TextElement':
        if alignment in ['left', 'center', 'right']:
            self.alignment = alignment
            self.texture_created = False
            self.calculate_size()
        return self

    def set_line_spacing(self, spacing: int) -> 'TextElement':
        self.line_spacing = spacing
        self.texture_created = False
        self.calculate_size()
        return self

    def set_outline(self, color: Tuple[int, int, int], width: int) -> 'TextElement':
        self.outline_color = color
        self.outline_width = width
        self.texture_created = False
        self.calculate_size()
        return self

    def _create_text_texture(self) -> None:
        self.texture_created = False

    def _create_texture_now(self) -> None:
        try:
            scaled_size = self.size * self.quality_scale
            font = _load_font_cached(self.font_path, scaled_size)
        except:
            font = ImageFont.load_default()

        lines = self.text.split('\n')
        dummy_img = Image.new('RGBA', (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)

        line_info = []
        max_width = 0
        total_height = 0

        for i, line in enumerate(lines):
            if line.strip():
                bbox = dummy_draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]
                y_offset = -bbox[1]
            else:
                line_width = 0
                line_height = font.getmetrics()[0]
                y_offset = 0

            line_info.append({
                'text': line,
                'width': line_width,
                'height': line_height,
                'y_offset': y_offset,
                'original_width': line_width,
                'original_height': line_height
            })

            if self.outline_width > 0:
                outline_scaled = self.outline_width * self.quality_scale
                line_width += outline_scaled * 2
                line_height += outline_scaled * 2

            max_width = max(max_width, line_width)
            total_height += line_height
            if i < len(lines) - 1:
                total_height += self.line_spacing

        content_width = max(max_width, 1)
        content_height = max(total_height, 1)

        img = Image.new('RGBA', (content_width, content_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        current_y = 0

        for line_data in line_info:
            if line_data['text'].strip():
                outline_offset = self.outline_width * self.quality_scale if self.outline_width > 0 else 0
                original_width = line_data['original_width']
                if self.alignment == 'left':
                    x_pos = outline_offset
                elif self.alignment == 'center':
                    x_pos = (content_width - original_width) // 2
                else:
                    x_pos = content_width - original_width - outline_offset

                stroke_width = 0
                stroke_fill = None

                if self.outline_color is not None and self.outline_width > 0:
                    stroke_width = self.outline_width * self.quality_scale
                    stroke_fill = (*self.outline_color, 255)
                elif self.bold:
                    stroke_width = 2 * self.quality_scale
                    stroke_fill = (*self.color, 255)

                y_pos = current_y + line_data['y_offset'] + outline_offset

                if stroke_width > 0 and stroke_fill is not None:
                    draw.text((x_pos, y_pos), line_data['text'], font=font, fill=(*self.color, 255),
                             stroke_width=stroke_width, stroke_fill=stroke_fill)
                else:
                    draw.text((x_pos, y_pos), line_data['text'], font=font, fill=(*self.color, 255))

            current_y += line_data['height'] + self.line_spacing

        # ---------------------------------------------------------
        # Apply quality scaling to padding and styles
        # ---------------------------------------------------------
        original_padding = self.padding.copy()
        original_corner_radius = self.corner_radius
        original_border_width = self.border_width

        if self.quality_scale > 1:
            self.padding = {k: v * self.quality_scale for k, v in self.padding.items()}
            self.corner_radius = self.corner_radius * self.quality_scale
            self.border_width = self.border_width * self.quality_scale

        img = self._apply_border_and_background_to_image(img)
        img = self._apply_blur_to_image(img)

        self.padding = original_padding
        self.corner_radius = original_corner_radius
        self.border_width = original_border_width

        self.texture_width = img.size[0]
        self.texture_height = img.size[1]
        self.width = self.texture_width
        self.height = self.texture_height

        img_data = np.array(img)

        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.texture_width, self.texture_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)

        glBindTexture(GL_TEXTURE_2D, 0)
        self.texture_created = True

    def calculate_size(self) -> None:
        try:
            font = _load_font_cached(self.font_path, self.size)
        except:
            font = ImageFont.load_default()

        lines = self.text.split('\n')
        dummy_img = Image.new('RGBA', (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)

        max_width = 0
        total_height = 0

        for i, line in enumerate(lines):
            if line.strip():
                bbox = dummy_draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]

                if self.outline_width > 0:
                    line_width += self.outline_width * 2
                    line_height += self.outline_width * 2
            else:
                line_width = 0
                line_height = font.getmetrics()[0]

            max_width = max(max_width, line_width)
            total_height += line_height
            if i < len(lines) - 1:
                total_height += self.line_spacing

        content_width = max(max_width, 1)
        content_height = max(total_height, 1)

        canvas_width = max(content_width + self.padding['left'] + self.padding['right'], 1)
        canvas_height = max(content_height + self.padding['top'] + self.padding['bottom'], 1)

        self.width = canvas_width
        self.height = canvas_height

    def render(self, time: float) -> None:
        if not self.is_visible_at(time):
            return

        self.update_animated_properties(time)

        if not self.texture_created:
            self._create_texture_now()

        if self.texture_id is None:
            return

        display_width = self.texture_width / self.quality_scale
        display_height = self.texture_height / self.quality_scale

        offset_x, offset_y = self._calculate_anchor_offset(display_width, display_height)

        render_x = self.x + offset_x
        render_y = self.y + offset_y

        glPushMatrix()

        center_x = render_x + display_width / 2
        center_y = render_y + display_height / 2

        glTranslatef(center_x, center_y, 0)

        if hasattr(self, 'rotation') and self.rotation != 0:
            glRotatef(self.rotation, 0, 0, 1)

        flip_x = -1.0 if getattr(self, 'flip_horizontal', False) else 1.0
        flip_y = -1.0 if getattr(self, 'flip_vertical', False) else 1.0
        if flip_x != 1.0 or flip_y != 1.0:
            glScalef(flip_x, flip_y, 1.0)

        if hasattr(self, 'scale') and self.scale != 1.0:
            glScalef(self.scale, self.scale, 1.0)

        glTranslatef(-center_x, -center_y, 0)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        alpha_value = 1.0
        glColor4f(1.0, 1.0, 1.0, alpha_value)

        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(render_x, render_y)

        glTexCoord2f(1.0, 0.0)
        glVertex2f(render_x + display_width, render_y)

        glTexCoord2f(1.0, 1.0)
        glVertex2f(render_x + display_width, render_y + display_height)

        glTexCoord2f(0.0, 1.0)
        glVertex2f(render_x, render_y + display_height)
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

        glPopMatrix()

    def __del__(self) -> None:
        if self.texture_id:
            try:
                glDeleteTextures(1, [self.texture_id])
            except:
                pass
