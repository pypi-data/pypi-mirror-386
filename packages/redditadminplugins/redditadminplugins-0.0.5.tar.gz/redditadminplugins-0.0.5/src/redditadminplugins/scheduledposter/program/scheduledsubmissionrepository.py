from abc import ABC, abstractmethod
from typing import List

from .scheduledsubmission import ScheduledSubmission


class ScheduledSubmissionRepository(ABC):

    @abstractmethod
    def get_due_submissions(self) -> List[ScheduledSubmission]:
        """Retrieve all due scheduled submissions"""

        raise NotImplementedError
