from typing import List, Union, TYPE_CHECKING, Literal, Optional
from .video_base import VideoBase

if TYPE_CHECKING:
    from typing import Self
    from .transition import Transition

class Scene(VideoBase):
    def __init__(self) -> None:
        super().__init__()
        self.elements: List[Union[VideoBase, 'Scene']] = []
        self.start_time: float = None
        self.duration: float = 0.0
        self._has_content_at_start: bool = False
        self.transition_in: Optional['Transition'] = None
        self.transition_out: Optional['Transition'] = None
        self._transition_alpha_multiplier: float = 1.0

    def add(self, element: Union[VideoBase, 'Scene'], layer: Literal["top", "bottom"] = "top") -> 'Scene':
        from .audio_element import AudioElement
        from .video_element import VideoElement
        from .image_element import ImageElement

        if layer == "bottom":
            self.elements.insert(0, element)
        else:
            self.elements.append(element)

        if isinstance(element, Scene):
            if element.start_time is None:
                child_has_content_at_start = self._scene_has_content_at_time(element, 0.0)

                if child_has_content_at_start and not self._has_content_at_start:
                    element.start_time = 0.0
                    self._has_content_at_start = True
                else:
                    last_scene_end_time = 0.0
                    for i, existing_element in enumerate(self.elements[:-1]):
                        if isinstance(existing_element, Scene):
                            existing_start = existing_element.start_time if existing_element.start_time is not None else 0.0
                            existing_end = existing_start + existing_element.duration
                            last_scene_end_time = max(last_scene_end_time, existing_end)
                    element.start_time = last_scene_end_time

            element_start = element.start_time if element.start_time is not None else 0.0
            scene_end_time = element_start + element.duration
            self.duration = max(self.duration, scene_end_time)
        else:
            is_bgm_audio = isinstance(element, AudioElement) and getattr(element, 'loop_until_scene_end', False)
            is_loop_video = isinstance(element, VideoElement) and (getattr(element, 'loop_until_scene_end', False) or getattr(element, '_wants_scene_duration', False))
            is_loop_image = isinstance(element, ImageElement) and (getattr(element, 'loop_until_scene_end', False) or getattr(element, '_wants_scene_duration', False))

            if not (is_bgm_audio or is_loop_video or is_loop_image):
                element_end_time = element.start_time + element.duration
                self.duration = max(self.duration, element_end_time)

        self._update_loop_element_durations()
        return self

    def _scene_has_content_at_time(self, scene: 'Scene', time: float) -> bool:
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

    def _update_loop_element_durations(self) -> None:
        from .audio_element import AudioElement
        from .video_element import VideoElement
        from .image_element import ImageElement

        for element in self.elements:
            if isinstance(element, Scene):
                element._update_loop_element_durations()
            elif isinstance(element, AudioElement) and element.loop_until_scene_end:
                element.update_duration_for_scene(self.duration)
            elif isinstance(element, VideoElement) and (element.loop_until_scene_end or getattr(element, '_wants_scene_duration', False)):
                element.update_duration_for_scene(self.duration)
            elif isinstance(element, ImageElement) and (element.loop_until_scene_end or getattr(element, '_wants_scene_duration', False)):
                element.update_duration_for_scene(self.duration)

    def start_at(self, time: float) -> 'Scene':
        self.start_time = time
        return self

    def set_transition_in(self, transition: 'Transition') -> 'Scene':
        self.transition_in = transition
        return self

    def set_transition_out(self, transition: 'Transition') -> 'Scene':
        self.transition_out = transition
        return self

    def is_visible_at(self, time: float) -> bool:
        start_time = self.start_time if self.start_time is not None else 0.0
        return start_time <= time < (start_time + self.duration)

    def calculate_size(self) -> None:
        self.width = 0
        self.height = 0

    def _calculate_transition_alpha(self, scene_time: float) -> float:
        alpha_multiplier = 1.0

        if self.transition_in is not None:
            if scene_time < self.transition_in.duration:
                progress = scene_time / self.transition_in.duration
                alpha_multiplier *= self.transition_in.get_alpha_multiplier(progress, 'in')

        if self.transition_out is not None:
            time_before_end = self.duration - scene_time
            if time_before_end < self.transition_out.duration:
                progress = (self.transition_out.duration - time_before_end) / self.transition_out.duration
                alpha_multiplier *= self.transition_out.get_alpha_multiplier(progress, 'out')

        return alpha_multiplier

    def _apply_transition_overlay(self, alpha: float) -> None:
        from OpenGL.GL import glDisable, glEnable, glColor4f, glBegin, glEnd, glVertex2f, GL_TEXTURE_2D, GL_QUADS

        fade_amount = 1.0 - alpha
        glDisable(GL_TEXTURE_2D)
        glColor4f(0.0, 0.0, 0.0, fade_amount)

        glBegin(GL_QUADS)
        glVertex2f(-10000, -10000)
        glVertex2f(30000, -10000)
        glVertex2f(30000, 30000)
        glVertex2f(-10000, 30000)
        glEnd()

        glColor4f(1.0, 1.0, 1.0, 1.0)

    def render(self, time: float) -> None:
        self.update_animated_properties(time)

        if not self.is_visible_at(time):
            return

        start_time = self.start_time if self.start_time is not None else 0.0

        if time >= start_time and self.start_time is not None:
            scene_time = time - start_time
        else:
            scene_time = time

        if scene_time < 0 or scene_time > self.duration:
            return

        transition_alpha = self._calculate_transition_alpha(scene_time)

        if transition_alpha <= 0.0:
            return

        for element in self.elements:
            element.render(scene_time)

        if transition_alpha < 1.0:
            self._apply_transition_overlay(transition_alpha)
