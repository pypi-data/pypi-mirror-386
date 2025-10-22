import math
from typing import Any, Dict, List, Union, Optional, Literal, Tuple
from abc import ABC, abstractmethod


class Animation(ABC):
    def __init__(self, duration: float = 1.0, start_time: float = 0.0, delay: float = 0.0) -> None:
        self.duration: float = duration
        self.start_time: float = start_time
        self.delay: float = delay

    def is_active(self, time: float) -> bool:
        actual_start = self.start_time + self.delay
        return actual_start <= time < (actual_start + self.duration)

    def get_progress(self, time: float) -> float:
        if not self.is_active(time):
            return 0.0 if time < self.start_time + self.delay else 1.0

        actual_start = self.start_time + self.delay
        elapsed = time - actual_start
        return min(1.0, max(0.0, elapsed / self.duration))

    @abstractmethod
    def calculate_value(self, progress: float) -> Any:
        pass

    def get_value_at_time(self, time: float) -> Any:
        return self.calculate_value(self.get_progress(time))


class LinearAnimation(Animation):
    def __init__(self, from_value: Union[float, int], to_value: Union[float, int],
                 duration: float = 1.0, start_time: float = 0.0, delay: float = 0.0) -> None:
        super().__init__(duration, start_time, delay)
        self.from_value: Union[float, int] = from_value
        self.to_value: Union[float, int] = to_value

    def calculate_value(self, progress: float) -> float:
        return self.from_value + (self.to_value - self.from_value) * progress


class EaseInAnimation(Animation):
    def __init__(self, from_value: Union[float, int], to_value: Union[float, int],
                 duration: float = 1.0, start_time: float = 0.0, delay: float = 0.0, power: float = 2.0):
        super().__init__(duration, start_time, delay)
        self.from_value = from_value
        self.to_value = to_value
        self.power = power

    def calculate_value(self, progress: float) -> float:
        eased_progress = progress ** self.power
        return self.from_value + (self.to_value - self.from_value) * eased_progress


class EaseOutAnimation(Animation):
    def __init__(self, from_value: Union[float, int], to_value: Union[float, int],
                 duration: float = 1.0, start_time: float = 0.0, delay: float = 0.0, power: float = 2.0):
        super().__init__(duration, start_time, delay)
        self.from_value = from_value
        self.to_value = to_value
        self.power = power

    def calculate_value(self, progress: float) -> float:
        eased_progress = 1 - (1 - progress) ** self.power
        return self.from_value + (self.to_value - self.from_value) * eased_progress


class EaseInOutAnimation(Animation):
    def __init__(self, from_value: Union[float, int], to_value: Union[float, int],
                 duration: float = 1.0, start_time: float = 0.0, delay: float = 0.0, power: float = 2.0):
        super().__init__(duration, start_time, delay)
        self.from_value = from_value
        self.to_value = to_value
        self.power = power

    def calculate_value(self, progress: float) -> float:
        if progress < 0.5:
            eased_progress = (progress * 2) ** self.power / 2
        else:
            eased_progress = 1 - ((1 - progress) * 2) ** self.power / 2
        return self.from_value + (self.to_value - self.from_value) * eased_progress


class BounceAnimation(Animation):
    def __init__(self, from_value: Union[float, int], to_value: Union[float, int],
                 duration: float = 1.0, start_time: float = 0.0, delay: float = 0.0,
                 bounces: int = 3, bounce_height: float = 0.3):
        super().__init__(duration, start_time, delay)
        self.from_value = from_value
        self.to_value = to_value
        self.bounces = bounces
        self.bounce_height = bounce_height

    def calculate_value(self, progress: float) -> float:
        if progress >= 1.0:
            return self.to_value

        bounce_offset = 0
        if progress > 0.7:
            t = (progress - 0.7) / 0.3
            bounce_offset = self.bounce_height * (1 - t) * math.sin(t * math.pi * self.bounces)

        base_progress = 1 - (1 - progress) ** 3
        final_value = self.from_value + (self.to_value - self.from_value) * base_progress

        return final_value + bounce_offset * (self.to_value - self.from_value)


class SpringAnimation(Animation):
    def __init__(self, from_value: Union[float, int], to_value: Union[float, int],
                 duration: float = 1.0, start_time: float = 0.0, delay: float = 0.0,
                 stiffness: float = 0.5, damping: float = 0.8):
        super().__init__(duration, start_time, delay)
        self.from_value = from_value
        self.to_value = to_value
        self.stiffness = stiffness
        self.damping = damping

    def calculate_value(self, progress: float) -> float:
        if progress >= 1.0:
            return self.to_value

        omega = self.stiffness * 2 * math.pi
        decay = math.exp(-self.damping * progress)
        spring_progress = 1 - decay * math.cos(omega * progress)

        return self.from_value + (self.to_value - self.from_value) * spring_progress


class KeyframeAnimation(Animation):
    def __init__(self, keyframes: Dict[float, Union[float, int]],
                 duration: float = None, start_time: float = 0.0, delay: float = 0.0,
                 interpolation: str = 'linear'):
        if duration is None:
            duration = max(keyframes.keys()) if keyframes else 1.0
        super().__init__(duration, start_time, delay)

        self.keyframes = sorted(keyframes.items())
        self.interpolation = interpolation

    def calculate_value(self, progress: float) -> float:
        if not self.keyframes:
            return 0

        total_time = self.keyframes[-1][0] if self.keyframes[-1][0] > 0 else 1.0
        normalized_time = progress * total_time

        for i, (time, value) in enumerate(self.keyframes):
            if normalized_time <= time:
                if i == 0:
                    return value

                prev_time, prev_value = self.keyframes[i - 1]

                if time == prev_time:
                    return value

                segment_progress = (normalized_time - prev_time) / (time - prev_time)
                segment_progress = self._apply_interpolation(segment_progress)

                return prev_value + (value - prev_value) * segment_progress

        return self.keyframes[-1][1]

    def _apply_interpolation(self, t: float) -> float:
        if self.interpolation == 'ease_in':
            return t * t
        elif self.interpolation == 'ease_out':
            return 1 - (1 - t) * (1 - t)
        elif self.interpolation == 'ease_in_out':
            return 2 * t * t if t < 0.5 else 1 - 2 * (1 - t) * (1 - t)
        return t


class RepeatingAnimation(Animation):
    def __init__(self, base_animation: Animation, repeat_count: int = -1,
                 repeat_delay: float = 0.0, repeat_mode: str = 'restart',
                 until_scene_end: bool = False, scene_duration: float = None):
        self.base_animation = base_animation
        self.repeat_count = repeat_count
        self.repeat_delay = repeat_delay
        self.repeat_mode = repeat_mode
        self.until_scene_end = until_scene_end
        self.scene_duration = scene_duration

        self.cycle_duration = base_animation.duration + repeat_delay

        if until_scene_end and scene_duration is not None:
            total_duration = scene_duration
        elif repeat_count > 0:
            total_duration = self.cycle_duration * repeat_count - repeat_delay
        else:
            total_duration = float('inf')

        super().__init__(total_duration, base_animation.start_time, base_animation.delay)

    def calculate_value(self, progress: float) -> Any:
        if self.duration == float('inf'):
            return self._calculate_infinite_value(progress)

        current_time = progress * self.duration
        cycle_number = int(current_time // self.cycle_duration)
        time_in_cycle = current_time % self.cycle_duration

        if time_in_cycle > self.base_animation.duration:
            if self.repeat_mode == 'reverse' and cycle_number % 2 == 1:
                return self.base_animation.calculate_value(0.0)
            return self.base_animation.calculate_value(1.0)

        base_progress = time_in_cycle / self.base_animation.duration

        if self.repeat_mode == 'reverse' and cycle_number % 2 == 1:
            base_progress = 1.0 - base_progress

        return self.base_animation.calculate_value(base_progress)

    def _calculate_infinite_value(self, progress: float) -> Any:
        assumed_time = progress * 100
        cycle_number = int(assumed_time // self.cycle_duration)
        time_in_cycle = assumed_time % self.cycle_duration

        if time_in_cycle > self.base_animation.duration:
            if self.repeat_mode == 'reverse' and cycle_number % 2 == 1:
                return self.base_animation.calculate_value(0.0)
            return self.base_animation.calculate_value(1.0)

        base_progress = time_in_cycle / self.base_animation.duration

        if self.repeat_mode == 'reverse' and cycle_number % 2 == 1:
            base_progress = 1.0 - base_progress

        return self.base_animation.calculate_value(base_progress)

    def get_value_at_time(self, time: float) -> Any:
        if not self.is_active(time):
            actual_start = self.start_time + self.delay
            if time < actual_start:
                return self.base_animation.calculate_value(0.0)
            return self.base_animation.calculate_value(1.0)

        actual_start = self.start_time + self.delay
        elapsed = time - actual_start

        if self.until_scene_end and self.scene_duration is not None:
            if elapsed >= self.scene_duration:
                elapsed = self.scene_duration - 0.001

        cycle_number = int(elapsed // self.cycle_duration)
        time_in_cycle = elapsed % self.cycle_duration

        if self.repeat_count > 0 and cycle_number >= self.repeat_count:
            if self.repeat_mode == 'reverse' and (self.repeat_count - 1) % 2 == 1:
                return self.base_animation.calculate_value(0.0)
            return self.base_animation.calculate_value(1.0)

        if time_in_cycle > self.base_animation.duration:
            if self.repeat_mode == 'reverse' and cycle_number % 2 == 1:
                return self.base_animation.calculate_value(0.0)
            return self.base_animation.calculate_value(1.0)

        base_progress = time_in_cycle / self.base_animation.duration

        if self.repeat_mode == 'reverse' and cycle_number % 2 == 1:
            base_progress = 1.0 - base_progress

        return self.base_animation.calculate_value(base_progress)


class ColorAnimation(Animation):
    def __init__(self, from_color: tuple, to_color: tuple,
                 duration: float = 1.0, start_time: float = 0.0, delay: float = 0.0,
                 interpolation: str = 'linear'):
        super().__init__(duration, start_time, delay)
        self.from_color = from_color
        self.to_color = to_color
        self.interpolation = interpolation

    def calculate_value(self, progress: float) -> tuple:
        if self.interpolation == 'ease_in':
            progress = progress ** 2
        elif self.interpolation == 'ease_out':
            progress = 1 - (1 - progress) ** 2
        elif self.interpolation == 'ease_in_out':
            progress = 2 * progress ** 2 if progress < 0.5 else 1 - 2 * (1 - progress) ** 2

        r = int(self.from_color[0] + (self.to_color[0] - self.from_color[0]) * progress)
        g = int(self.from_color[1] + (self.to_color[1] - self.from_color[1]) * progress)
        b = int(self.from_color[2] + (self.to_color[2] - self.from_color[2]) * progress)

        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


class AnimationPresets:
    @staticmethod
    def fade_in(duration: float = 1.0, delay: float = 0.0) -> LinearAnimation:
        return LinearAnimation(0, 255, duration, delay=delay)

    @staticmethod
    def fade_out(duration: float = 1.0, delay: float = 0.0) -> LinearAnimation:
        return LinearAnimation(255, 0, duration, delay=delay)

    @staticmethod
    def slide_in_from_left(distance: float = 200, duration: float = 1.0, delay: float = 0.0) -> EaseOutAnimation:
        return EaseOutAnimation(-distance, 0, duration, delay=delay)

    @staticmethod
    def slide_in_from_right(distance: float = 200, duration: float = 1.0, delay: float = 0.0) -> EaseOutAnimation:
        return EaseOutAnimation(distance, 0, duration, delay=delay)

    @staticmethod
    def scale_up(from_scale: float = 0.0, to_scale: float = 1.0, duration: float = 1.0, delay: float = 0.0) -> EaseOutAnimation:
        return EaseOutAnimation(from_scale, to_scale, duration, delay=delay)

    @staticmethod
    def bounce_in(duration: float = 1.5, delay: float = 0.0) -> BounceAnimation:
        return BounceAnimation(0, 1, duration, delay=delay, bounces=3, bounce_height=0.3)

    @staticmethod
    def spring_in(duration: float = 2.0, delay: float = 0.0) -> SpringAnimation:
        return SpringAnimation(0, 1, duration, delay=delay, stiffness=0.6, damping=0.8)

    @staticmethod
    def pulse(from_scale: float = 1.0, to_scale: float = 1.3, duration: float = 1.0, delay: float = 0.0) -> KeyframeAnimation:
        keyframes = {0.0: from_scale, 0.5: to_scale, 1.0: from_scale}
        return KeyframeAnimation(keyframes, duration, delay=delay, interpolation='ease_in_out')

    @staticmethod
    def breathing(from_scale: float = 1.0, to_scale: float = 1.1, duration: float = 2.0, delay: float = 0.0) -> KeyframeAnimation:
        keyframes = {0.0: from_scale, 0.5: to_scale, 1.0: from_scale}
        return KeyframeAnimation(keyframes, duration, delay=delay, interpolation='ease_in_out')

    @staticmethod
    def wiggle(amplitude: float = 10.0, duration: float = 0.5, delay: float = 0.0) -> KeyframeAnimation:
        keyframes = {0.0: 0, 0.25: amplitude, 0.5: -amplitude, 0.75: amplitude, 1.0: 0}
        return KeyframeAnimation(keyframes, duration, delay=delay, interpolation='linear')


class AnimationManager:
    def __init__(self):
        self.animations: Dict[str, List[Animation]] = {}

    def add_animation(self, property_name: str, animation: Animation):
        if property_name not in self.animations:
            self.animations[property_name] = []
        self.animations[property_name].append(animation)

    def get_animated_value(self, property_name: str, time: float, base_value: Any = None):
        if property_name not in self.animations:
            return base_value

        current_value = base_value
        for animation in self.animations[property_name]:
            if isinstance(animation, RepeatingAnimation):
                if animation.is_active(time) or (animation.until_scene_end and animation.scene_duration is not None):
                    current_value = animation.get_value_at_time(time)
                    break
            else:
                if animation.is_active(time):
                    current_value = animation.get_value_at_time(time)
                    break

        return current_value

    def has_active_animations(self, time: float) -> bool:
        return any(animation.is_active(time) for animations in self.animations.values() for animation in animations)

    def clear_animations(self, property_name: str = None):
        if property_name:
            self.animations.pop(property_name, None)
        else:
            self.animations.clear()
