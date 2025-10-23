from abc import ABC, abstractmethod
from typing import List

from .scheduledcrosspost import ScheduledCrosspost


class ScheduledCrosspostRepository(ABC):
    @abstractmethod
    def get_scheduled_crossposts(self) -> List[ScheduledCrosspost]:
        """Retrieve all scheduled crossposts"""
        raise NotImplementedError

    @abstractmethod
    def get_scheduled_crossposts_for_url(self, url: str) -> List[ScheduledCrosspost]:
        """Retrieve all scheduled crossposts for a particular url"""
        raise NotImplementedError

    @abstractmethod
    def check_exists(self, url: str) -> bool:
        """
        Check if scheduled crossposts exist for with
        the particular url
        """
        raise NotImplementedError

    @abstractmethod
    def delete_scheduled_crosspost(self, scheduled_crosspost: ScheduledCrosspost):
        """Delete the provided scheduled crosspost"""
        raise NotImplementedError
