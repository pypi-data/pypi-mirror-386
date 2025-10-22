from typing import Dict, Optional, Tuple, Any, Literal, Union, TypeVar
from PIL import Image, ImageDraw, ImageFilter
from .animation import Animation, AnimationManager, RepeatingAnimation

VideoBaseT = TypeVar('VideoBaseT', bound='VideoBase')


class VideoBase:
    def __init__(self) -> None:
        self.x: float = 0.0
        self.y: float = 0.0
        self.start_time: float = 0.0
        self.duration: float = 1.0
        self.visible: bool = True
        self.position_anchor: Literal['center', 'top-left', 'top-right', 'bottom-left', 'bottom-right'] = 'top-left'
        self.background_color: Optional[Tuple[int, int, int]] = None
        self.background_alpha: int = 255
        self.padding: Dict[str, int] = {'top': 0, 'right': 0, 'bottom': 0, 'left': 0}
        self.border_color: Optional[Tuple[int, int, int]] = None
        self.border_width: int = 0
        self.corner_radius: float = 0
        self.blur_strength: float = 0
        self.crop_width: Optional[int] = None
        self.crop_height: Optional[int] = None
        self.crop_mode: Literal['fill', 'fit'] = 'fill'
        self.width: int = 0
        self.height: int = 0
        self.texture_created: bool = False
        self.animation_manager: AnimationManager = AnimationManager()
        self.base_x: float = 0.0
        self.base_y: float = 0.0
        self.base_alpha: int = 255
        self.base_scale: float = 1.0
        self.rotation: float = 0.0
        self.scale: float = 1.0
        self.flip_horizontal: bool = False
        self.flip_vertical: bool = False

    def position(self: VideoBaseT, x: float, y: float, anchor: Optional[Literal['center', 'top-left', 'top-right', 'bottom-left', 'bottom-right']] = None) -> VideoBaseT:
        if anchor is not None:
            self.position_anchor = anchor
        self.x = x
        self.y = y
        self.base_x = x
        self.base_y = y
        return self

    def _calculate_anchor_offset(self, element_width: float, element_height: float) -> Tuple[float, float]:
        if self.position_anchor == 'center':
            return -element_width / 2, -element_height / 2
        elif self.position_anchor == 'top-right':
            return -element_width, 0
        elif self.position_anchor == 'bottom-left':
            return 0, -element_height
        elif self.position_anchor == 'bottom-right':
            return -element_width, -element_height
        return 0, 0

    def get_actual_render_position(self) -> Tuple[float, float, float, float]:
        element_width = getattr(self, 'width', 0)
        element_height = getattr(self, 'height', 0)
        scaled_width = element_width * self.scale
        scaled_height = element_height * self.scale
        offset_x, offset_y = self._calculate_anchor_offset(scaled_width, scaled_height)
        actual_x = self.x + offset_x
        actual_y = self.y + offset_y
        return actual_x, actual_y, scaled_width, scaled_height

    def set_duration(self: VideoBaseT, duration: float) -> VideoBaseT:
        self.duration = duration
        return self

    def start_at(self: VideoBaseT, time: float) -> VideoBaseT:
        self.start_time = time
        return self

    def is_visible_at(self, time: float) -> bool:
        return self.start_time <= time < (self.start_time + self.duration)

    def set_background(self: VideoBaseT, color: Tuple[int, int, int], alpha: int = 255, padding: Union[int, Dict[str, int]] = 5) -> VideoBaseT:
        self.background_color = color
        self.background_alpha = alpha
        if isinstance(padding, int):
            self.padding = {'top': padding, 'right': padding, 'bottom': padding, 'left': padding}
        elif isinstance(padding, dict):
            self.padding.update(padding)
        self.texture_created = False
        self.calculate_size()
        return self

    def set_border(self: VideoBaseT, color: Tuple[int, int, int], width: int = 1) -> VideoBaseT:
        self.border_color = color
        self.border_width = width
        self.texture_created = False
        self.calculate_size()
        return self

    def set_corner_radius(self: VideoBaseT, radius: float) -> VideoBaseT:
        self.corner_radius = max(0, radius)
        self.texture_created = False
        self.calculate_size()
        return self

    def set_crop(self: VideoBaseT, width: int, height: int, mode: Literal['fill', 'fit'] = 'fill') -> VideoBaseT:
        self.crop_width = width
        self.crop_height = height
        self.crop_mode = mode
        self.texture_created = False
        self.calculate_size()
        return self

    def set_blur(self: VideoBaseT, strength: float) -> VideoBaseT:
        self.blur_strength = max(0, strength)
        self.texture_created = False
        return self

    def set_rotate(self: VideoBaseT, angle: float) -> VideoBaseT:
        self.rotation = angle
        return self

    def set_flip(self: VideoBaseT, direction: Union[str, Literal['horizontal', 'vertical', 'both', 'none']] = 'horizontal') -> VideoBaseT:
        if direction == 'horizontal':
            self.flip_horizontal = True
            self.flip_vertical = False
        elif direction == 'vertical':
            self.flip_horizontal = False
            self.flip_vertical = True
        elif direction == 'both':
            self.flip_horizontal = True
            self.flip_vertical = True
        elif direction == 'none':
            self.flip_horizontal = False
            self.flip_vertical = False
        else:
            raise ValueError(f"Invalid flip direction: {direction}. Use 'horizontal', 'vertical', 'both', or 'none'")
        return self

    def _apply_border_and_background_to_image(self, img: Image.Image) -> Image.Image:
        original_width, original_height = img.size
        canvas_width = max(original_width + self.padding['left'] + self.padding['right'], 1)
        canvas_height = max(original_height + self.padding['top'] + self.padding['bottom'], 1)

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        canvas = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))

        if self.background_color is not None:
            draw = ImageDraw.Draw(canvas)
            bg_color = (*self.background_color, self.background_alpha)

            if self.corner_radius > 0:
                draw.rounded_rectangle([0, 0, canvas_width-1, canvas_height-1],
                                     radius=self.corner_radius, fill=bg_color)
            else:
                draw.rectangle([0, 0, canvas_width-1, canvas_height-1], fill=bg_color)

        canvas.paste(img, (self.padding['left'], self.padding['top']), img)

        if self.border_color is not None and self.border_width > 0:
            draw = ImageDraw.Draw(canvas)
            border_color = (*self.border_color, 255)

            if self.corner_radius > 0:
                for i in range(self.border_width):
                    current_radius = max(0, self.corner_radius - i)
                    draw.rounded_rectangle([i, i, canvas_width-1-i, canvas_height-1-i],
                                         radius=current_radius, outline=border_color, width=1)
            else:
                for i in range(self.border_width):
                    draw.rectangle([i, i, canvas_width-1-i, canvas_height-1-i],
                                 outline=border_color, width=1)

        return canvas

    def _apply_corner_radius_to_image(self, img: Image.Image) -> Image.Image:
        if self.corner_radius <= 0:
            return img

        width, height = img.size
        radius = min(self.corner_radius, width // 2, height // 2)
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, width, height], radius=radius, fill=255)

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        img.putalpha(mask)
        return img

    def _apply_blur_to_image(self, img: Image.Image) -> Image.Image:
        if self.blur_strength <= 0:
            return img
        return img.filter(ImageFilter.GaussianBlur(radius=self.blur_strength))

    def _calculate_crop_dimensions(self, original_width: int, original_height: int) -> Tuple[int, int, int, int]:
        if self.crop_width is None or self.crop_height is None:
            return original_width, original_height, 0, 0

        target_width = self.crop_width
        target_height = self.crop_height

        if self.crop_mode == 'fill':
            scale = max(target_width / original_width, target_height / original_height)
        else:
            scale = min(target_width / original_width, target_height / original_height)

        scaled_width = int(original_width * scale)
        scaled_height = int(original_height * scale)
        crop_x = max(0, (scaled_width - target_width) // 2)
        crop_y = max(0, (scaled_height - target_height) // 2)

        return scaled_width, scaled_height, crop_x, crop_y

    def _apply_crop_to_image(self, img: Image.Image) -> Image.Image:
        if self.crop_width is None or self.crop_height is None:
            return img

        original_width, original_height = img.size
        scaled_width, scaled_height, crop_x, crop_y = self._calculate_crop_dimensions(original_width, original_height)

        if scaled_width != original_width or scaled_height != original_height:
            img = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

        if self.crop_mode == 'fill':
            crop_box = (crop_x, crop_y, crop_x + self.crop_width, crop_y + self.crop_height)
            img = img.crop(crop_box)
        else:
            canvas = Image.new('RGBA', (self.crop_width, self.crop_height), (0, 0, 0, 0))
            paste_x = (self.crop_width - scaled_width) // 2
            paste_y = (self.crop_height - scaled_height) // 2
            canvas.paste(img, (paste_x, paste_y), img)
            img = canvas

        return img

    def animate(self: VideoBaseT, property_name: str, animation: Animation) -> VideoBaseT:
        animation.start_time += self.start_time
        self.animation_manager.add_animation(property_name, animation)
        return self

    def animate_position(self: VideoBaseT, animation: Animation, axis: Literal['x', 'y', 'both'] = 'both') -> VideoBaseT:
        if axis in ['x', 'both']:
            self.animate('x', animation)
        if axis in ['y', 'both']:
            self.animate('y', animation)
        return self

    def animate_fade(self: VideoBaseT, animation: Animation) -> VideoBaseT:
        self.animate('alpha', animation)
        return self

    def animate_scale(self: VideoBaseT, animation: Animation) -> VideoBaseT:
        self.animate('scale', animation)
        return self

    def animate_rotation(self: VideoBaseT, animation: Animation) -> VideoBaseT:
        self.animate('rotation', animation)
        return self

    def animate_repeating(self: VideoBaseT, property_name: str, animation: Animation,
                         repeat_count: int = -1, repeat_delay: float = 0.0,
                         repeat_mode: Literal['restart', 'reverse', 'continue'] = 'restart') -> VideoBaseT:
        repeating_animation = RepeatingAnimation(base_animation=animation, repeat_count=repeat_count,
                                                repeat_delay=repeat_delay, repeat_mode=repeat_mode)
        repeating_animation.start_time += self.start_time
        self.animation_manager.add_animation(property_name, repeating_animation)
        return self

    def animate_until_scene_end(self: VideoBaseT, property_name: str, animation: Animation,
                               repeat_delay: float = 0.0, repeat_mode: Literal['restart', 'reverse', 'continue'] = 'restart',
                               scene_duration: Optional[float] = None) -> VideoBaseT:
        if scene_duration is None:
            scene_duration = self.duration

        repeating_animation = RepeatingAnimation(base_animation=animation, repeat_count=-1, repeat_delay=repeat_delay,
                                                repeat_mode=repeat_mode, until_scene_end=True, scene_duration=scene_duration)
        repeating_animation.start_time += self.start_time
        self.animation_manager.add_animation(property_name, repeating_animation)
        return self

    def animate_repeating_scale(self: VideoBaseT, animation: Animation, repeat_count: int = -1,
                               repeat_delay: float = 0.0, repeat_mode: Literal['restart', 'reverse', 'continue'] = 'restart') -> VideoBaseT:
        return self.animate_repeating('scale', animation, repeat_count, repeat_delay, repeat_mode)

    def animate_repeating_position(self: VideoBaseT, animation: Animation, axis: Literal['x', 'y', 'both'] = 'both',
                                  repeat_count: int = -1, repeat_delay: float = 0.0,
                                  repeat_mode: Literal['restart', 'reverse', 'continue'] = 'restart') -> VideoBaseT:
        if axis in ['x', 'both']:
            self.animate_repeating('x', animation, repeat_count, repeat_delay, repeat_mode)
        if axis in ['y', 'both']:
            self.animate_repeating('y', animation, repeat_count, repeat_delay, repeat_mode)
        return self

    def animate_repeating_rotation(self: VideoBaseT, animation: Animation, repeat_count: int = -1,
                                  repeat_delay: float = 0.0, repeat_mode: Literal['restart', 'reverse', 'continue'] = 'restart') -> VideoBaseT:
        return self.animate_repeating('rotation', animation, repeat_count, repeat_delay, repeat_mode)

    def animate_pulse_until_end(self: VideoBaseT, from_scale: float = 1.0, to_scale: float = 1.2,
                               duration: float = 1.0, repeat_delay: float = 0.0,
                               scene_duration: Optional[float] = None) -> VideoBaseT:
        from animation import AnimationPresets
        pulse_animation = AnimationPresets.pulse(from_scale, to_scale, duration)
        return self.animate_until_scene_end('scale', pulse_animation, repeat_delay, 'restart', scene_duration)

    def animate_breathing_until_end(self: VideoBaseT, from_scale: float = 1.0, to_scale: float = 1.1,
                                   duration: float = 3.0, repeat_delay: float = 0.0,
                                   scene_duration: Optional[float] = None) -> VideoBaseT:
        from animation import AnimationPresets
        breathing_animation = AnimationPresets.breathing(from_scale, to_scale, duration)
        return self.animate_until_scene_end('scale', breathing_animation, repeat_delay, 'restart', scene_duration)

    def get_animated_properties(self, time: float) -> Dict[str, Any]:
        properties = {}

        animated_x = self.animation_manager.get_animated_value('x', time, self.base_x)
        animated_y = self.animation_manager.get_animated_value('y', time, self.base_y)
        if animated_x is not None:
            properties['x'] = animated_x
        if animated_y is not None:
            properties['y'] = animated_y

        animated_alpha = self.animation_manager.get_animated_value('alpha', time, self.background_alpha)
        if animated_alpha is not None:
            properties['alpha'] = max(0, min(255, int(animated_alpha)))

        animated_scale = self.animation_manager.get_animated_value('scale', time, self.base_scale)
        if animated_scale is not None:
            properties['scale'] = max(0.0, animated_scale)

        animated_rotation = self.animation_manager.get_animated_value('rotation', time, self.rotation)
        if animated_rotation is not None:
            properties['rotation'] = animated_rotation

        if hasattr(self, 'color') and self.animation_manager.get_animated_value('color', time) is not None:
            animated_color = self.animation_manager.get_animated_value('color', time, getattr(self, 'color', (255, 255, 255)))
            properties['color'] = animated_color

        animated_corner_radius = self.animation_manager.get_animated_value('corner_radius', time, self.corner_radius)
        if animated_corner_radius is not None:
            properties['corner_radius'] = max(0, animated_corner_radius)

        animated_blur_strength = self.animation_manager.get_animated_value('blur_strength', time, self.blur_strength)
        if animated_blur_strength is not None:
            properties['blur_strength'] = max(0, animated_blur_strength)

        return properties

    def update_animated_properties(self, time: float) -> None:
        animated_props = self.get_animated_properties(time)

        if 'x' in animated_props:
            self.x = animated_props['x']
        if 'y' in animated_props:
            self.y = animated_props['y']
        if 'alpha' in animated_props:
            self.background_alpha = animated_props['alpha']
        if 'scale' in animated_props:
            self.scale = animated_props['scale']
        if 'rotation' in animated_props:
            self.rotation = animated_props['rotation']
        if 'corner_radius' in animated_props:
            self.corner_radius = animated_props['corner_radius']
        if 'blur_strength' in animated_props:
            self.blur_strength = animated_props['blur_strength']

    def has_animations(self, time: Optional[float] = None) -> bool:
        if time is not None:
            return self.animation_manager.has_active_animations(time)
        return len(self.animation_manager.animations) > 0

    def calculate_size(self) -> None:
        pass

    def render(self, time: float) -> None:
        self.update_animated_properties(time)
