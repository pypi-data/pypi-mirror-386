from typing import Optional, Literal
from abc import ABC, abstractmethod


class Transition(ABC):
    def __init__(self, duration: float = 1.0) -> None:
        self.duration: float = duration

    @abstractmethod
    def get_alpha_multiplier(self, progress: float, direction: Literal['in', 'out']) -> float:
        pass

    def get_transform(self, progress: float, direction: Literal['in', 'out']) -> dict:
        return {}


class FadeTransition(Transition):
    def __init__(self, duration: float = 1.0, easing: Literal['linear', 'ease_in', 'ease_out', 'ease_in_out'] = 'linear') -> None:
        super().__init__(duration)
        self.easing = easing

    def get_alpha_multiplier(self, progress: float, direction: Literal['in', 'out']) -> float:
        eased_progress = self._apply_easing(progress)
        return eased_progress if direction == 'in' else 1.0 - eased_progress

    def _apply_easing(self, t: float) -> float:
        if self.easing == 'ease_in':
            return t * t
        elif self.easing == 'ease_out':
            return 1 - (1 - t) * (1 - t)
        elif self.easing == 'ease_in_out':
            return 2 * t * t if t < 0.5 else 1 - 2 * (1 - t) * (1 - t)
        return t
