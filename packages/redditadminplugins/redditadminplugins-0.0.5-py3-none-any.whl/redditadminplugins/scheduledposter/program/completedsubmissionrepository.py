from abc import ABC, abstractmethod

from .scheduledsubmission import ScheduledSubmission


class CompletedSubmissionRepository(ABC):
    @abstractmethod
    def add(self, due_submission: ScheduledSubmission):
        """Add (Mark) completed submission"""

        raise NotImplementedError

    @abstractmethod
    def check_exists(self, scheduled_submission: ScheduledSubmission) -> bool:
        """
        Check if provided scheduled submission is completed
        """

        raise NotImplementedError

