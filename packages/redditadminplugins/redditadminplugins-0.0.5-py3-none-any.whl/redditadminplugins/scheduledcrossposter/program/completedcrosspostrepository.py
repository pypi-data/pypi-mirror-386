from abc import ABC, abstractmethod

from .scheduledcrosspost import ScheduledCrosspost


class CompletedCrosspostRepository(ABC):
    @abstractmethod
    def add(self, completed_crosspost: ScheduledCrosspost):
        """Add (Acknowledge) completed crosspost"""
        raise NotImplementedError

    @abstractmethod
    def check_completed(self, scheduled_crosspost: ScheduledCrosspost) -> bool:
        """Check if provided scheduled crosspost has been completed"""
        raise NotImplementedError
